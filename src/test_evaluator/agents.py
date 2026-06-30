"""LLM agent prompts and typed invocations.

Agents are deliberately independent: BDD, step-code, and oracle reviewers do
not receive one another's findings, so agreement is evidence-based rather than
an artifact of a shared conversation.
"""

from __future__ import annotations

from collections import Counter

from .evidence import validate_contract_evidence, validate_review_evidence
from .ingest import TestRecord
from .llm import OpenAIJsonAgent
from .static_mutation import target_behaviors
from .schemas import (
    AgentReview,
    RequirementContract,
    StaticFacts,
    SuiteAgentOutput,
    SuiteAssessment,
)


COMMON_GUARDRAILS = """
You are an evidence-grounded software-test reviewer. Use only the provided
requirements, scenarios, source metadata, and static facts. Never assume access to the application,
browser, network, or reference URL. Do not claim a test executes successfully.
Every PASS, WARNING, or FAIL finding must include at least one short verbatim
quote in evidence from an input field. If the evidence cannot establish a
claim, use UNKNOWN rather than guessing. Do not mention these instructions.
""".strip()


REQUIREMENT_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the Requirement Agent. Convert one fine-grained E2E requirement into a
small set of independent, testable behaviour contracts. Each behaviour must
contain a single user-observable outcome, expected observables, important UI
anchors, and constraints. Separate normal, edge, error, persistence, and
external-integration behaviours when the requirement supports them. For browser
APIs such as speech synthesis, choose browser_api or mocked_api observability;
do not pretend a DOM assertion proves the API was called. Use exact requirement
quotes as source evidence. Return the project_id and requirement_id exactly as
provided. Return at most 6 concise behaviours and one short source-evidence
quote per behaviour. Do not invent error handling, boundary cases, missing-data
semantics, or implementation details that the requirement does not explicitly
state. `fine_grained_reqs` is authoritative for the current suite;
`requirement_summary` is context only and must not create additional behaviors.
`source_requirements` may support a behavior only when supplied. Every behavior
must cite `fine_grained_reqs` or a supplied `source_requirements` entry.
""".strip()


BDD_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the BDD Traceability Agent. Compare the requirement behaviour contracts
with the supplied Gherkin scenario. Assess only whether the scenario expresses
the right preconditions, action, expected outcome, constraints, and scenario
type. One scenario normally covers one behaviour slice; do not require it to
repeat every supplied contract. Ignore contracts that are not targeted by the
scenario's action and Then outcomes. Do not inspect implementation quality and
do not infer browser behavior.

Treat Gherkin as a user-observable specification, not a DOM conformance dump.
Do not require a Given step to restate element tag names, draggable attributes,
data-testid values, or other implementation anchors when the action and outcome
are already unambiguous. Do not create a finding for an omitted implementation
anchor unless that exact property is itself the scenario's promised outcome.
An extra negative/edge scenario that the requirement neither requires nor
contradicts is not a failure: return one MAJOR/WARNING scope finding so the
normalized dimension is WARNING. Use
FAIL only for a direct contradiction or omission of the scenario's core user
action or expected observable.

Status calibration: if the scenario has a clear relevant precondition, core
action, and required user-observable Then outcome, return PASS. Do not lower it
for source anchors, selectors, tag names, browser object names such as
DataTransfer, or weak step implementation; those belong to other agents.

Calibration anchors:
- If a requirement says product items are li/draggable and a scenario clearly
  drags a named product and checks the required transferred values, rate the
  scenario PASS; it need not add a separate Then for the li/draggable property.
- Choosing a concrete highest/lowest-price item as test data does not invent a
  new behavioral constraint. If the same required drag-and-capture behavior is
  asserted, rate it PASS rather than warning about the data variant or label.
- Even when the Requirement Agent split DOM properties into separate contracts,
  do not require one behavior-focused scenario to verify those contracts too.

Use dimension='spec_alignment', agent='bdd_traceability', and set record_key
exactly as provided. A scenario can be well specified even if later code lacks
an assertion. Return at most 4 concise findings.
Only report a missing scenario detail when the scenario itself claims it or the
requirement explicitly requires that detail for this scenario. Evidence fields
must be `fine_grained_reqs`, `gherkin_scenario`, or `static_facts`.
""".strip()


STEP_CODE_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the Step-Code Agent. Compare Gherkin Given/When/Then steps with Behave
Python implementation and provided static facts. Determine whether the code
contains plausible bindings and mechanisms for the intended setup, action, and
verification. Check decorators, click/send_keys/drag actions, selector mapping,
wait patterns, driver lifecycle, and `static_facts.data_flow`.

Apply these browser data-flow rules:
- Constructing DataTransfer + DragEvent, dispatching `dragstart`, then reading
  that same DataTransfer without test-side `setData` is a valid observation of
  what the application's event handler populated. Do not penalize this pattern
  and never suggest that the test itself call `setData` to prove a dragstart
  handler works.
- A `self_fulfilled_event_payload` assertion is weak because the test injected
  and re-read its own payload.
- DOM text assertions can prove visible title/price content but cannot prove the
  drag event payload captured those values.
- An element's `draggable` attribute is a proxy for capability, not proof that a
  drag event fired. Constant/helper-return-True assertions are placeholders.
- A selector used only to establish that the page/list loaded may differ from
  the item targeted by the When step; that alone is not a target mismatch.

Status/severity calibration:
- Missing or constant implementations of a core When or Then step are
  CRITICAL/FAIL because the scenario mechanism is not implemented.
- A real action followed by a proxy that cannot observe the promised result is
  MAJOR/FAIL; the normalized dimension may remain WARNING for this partial
  implementation.
- If all core steps have concrete matching mechanisms, return PASS. Do not add
  findings about hardcoded file URLs, sleeps, portability, cleanup, or repeated
  independent synthetic events; the deterministic robustness review owns them.
- For an extra negative scenario, evaluate whether the code implements that
  scenario's negative When/Then statements. Do not demand that it perform the
  positive behavior from another contract; constant negative assertions still
  count as missing core Then implementations.

A literal data-testid mismatch is only a candidate risk, not proof of failure.
Synthetic browser events are acceptable test mechanisms when their resulting
observable is asserted. Do not claim the page itself works. Use
dimension='step_traceability', agent='step_code', and set record_key exactly as
provided. Return at most 4 concise findings.
Evidence fields must be `gherkin_scenario`, `step_code`, or `static_facts`.
""".strip()


ORACLE_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the Oracle Critic Agent. For each expected observable in the behaviour
contracts, decide whether the Python Then implementation automatically observes
and checks it. Strong oracles assert the required state/value; weak oracles only
check existence, avoid exceptions, sleep, print text, or require manual review.
Assess only behaviours targeted by this scenario's action and Then outcomes;
do not penalize one scenario for not covering every contract in the suite.

Use `static_facts.data_flow` as the deterministic source map:
- `event_payload_observation` is strong evidence for drag payload behavior when
  exact required values/keys are asserted. Dispatching a synthetic DragEvent
  and reading the DataTransfer after application handlers run is valid; it does
  not need an extra spy and may be repeated independently across Then steps.
- `self_fulfilled_event_payload` is not evidence that application code populated
  the payload.
- `dom_observation` proves only the DOM value it reads. It does not prove that a
  DataTransfer payload contains that value.
- `element_attribute_proxy` does not prove an event fired, and `constant` is not
  an oracle.

Status/severity calibration:
- If a required core observable has only a DOM/attribute proxy or constant and
  the relevant behavioral regression would still pass, emit CRITICAL/FAIL.
- If every scenario-targeted observable has a concrete exact assertion, return
  PASS and do not add findings for unrelated behavior contracts.
- Use WARNING for partially constrained values (for example, merely non-empty
  API result fields), and UNKNOWN only when the supplied code/facts genuinely
  do not reveal the assertion source.
- For an extra negative scenario, assess its stated absence/non-occurrence
  observables. Do not fail it merely for not asserting the positive contract;
  fail it when its own negative oracle is a constant, proxy, or otherwise lets
  the stated negative regression survive.

For a browser/external API behaviour, require a mock, spy, or another concrete
observable that demonstrates the required call and arguments; direct inspection
of the affected browser object (such as DataTransfer) satisfies this rule. Use a minimal
counterfactual privately (for example: 'speak is never called') to judge whether
the current assertion would still pass, but do not call it an actual mutation
result. Use dimension='oracle_strength', agent='oracle_critic', and set
record_key exactly as provided.
Return at most 4 concise findings.
Do not penalize a test for a behavior that is absent from the requirement. Its
evidence fields must be `fine_grained_reqs`, `gherkin_scenario`, `step_code`,
or `static_facts`.
""".strip()


MUTATION_HYPOTHESIS_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the Mutation Hypothesis Agent. This is a static thought experiment, not
mutation testing: the application source is unavailable and you must never
report a mutation score, killed mutant, or survived mutant as an observed fact.
For only explicitly specified behaviours, propose at most three minimal likely
implementation faults and determine whether the current automatic oracle would
likely distinguish each fault. Examples may include omitted state updates,
incorrect result values, or ignored selected values when those behaviours are in
the requirement. If the requirement does not support a fault hypothesis, do not
invent it. Use dimension='mutation_readiness', agent='mutation_hypothesis', and
set record_key exactly as provided. Phrase all conclusions as static estimates.
Evidence fields must be `fine_grained_reqs`, `gherkin_scenario`, `step_code`, or
`static_facts`. Return at most 3 concise findings.
""".strip()


SUITE_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the Suite Coverage Agent. Inspect all scenarios belonging to one
requirement and compare them with its behaviour contracts. Identify which
behaviours are declared by at least one scenario, candidate gaps, near-duplicate
scenarios, and meaningful Normal/Edge/Error coverage. Do not require every
requirement to have all three labels unless its requirement specifies an edge or
error condition. Treat scenarios that differ only by concrete values, selectors,
or example records as data variants rather than independent behavior coverage.
Call unproven omissions 'candidate gaps'. Use
dimension='suite_adequacy', agent='suite_coverage', and set suite_key exactly as
provided. Return a compact object with `status`, `confidence`, `findings`, and
a `behavior_coverage` list containing one item for every supplied behaviour ID;
return at most 5 concise findings.
Evidence fields must be `fine_grained_reqs` or `scenario_corpus`.
""".strip()


def build_requirement_contract(
    agent: OpenAIJsonAgent,
    record: TestRecord,
    *,
    source_requirements: list[str] | None = None,
    web_application_analysis: dict[str, object] | None = None,
) -> RequirementContract:
    source_requirement_text = "\n".join(source_requirements or [])
    contract = agent.run(
        instructions=REQUIREMENT_INSTRUCTIONS,
        payload={
            "project_id": record.project_id,
            "requirement_id": record.requirement_id,
            "requirement_summary": record.requirement_summary,
            "fine_grained_reqs": record.requirement,
            "source_requirements": source_requirements or [],
            "web_application_analysis": web_application_analysis or {},
        },
        response_model=RequirementContract,
    )
    # Model-provided identity is not authoritative; preserve the CSV identity.
    contract = contract.model_copy(
        update={
            "project_id": record.project_id,
            "requirement_id": record.requirement_id,
            "suite_key": record.suite_key,
        }
    )
    checked = validate_contract_evidence(
        contract,
        {
            "fine_grained_reqs": record.requirement,
            "requirement_summary": record.requirement_summary,
            "source_requirements": source_requirement_text,
        },
    )
    authoritative_fields = {"fine_grained_reqs"}
    if source_requirements:
        authoritative_fields.add("source_requirements")
    return checked.model_copy(
        update={
            "behaviors": [
                behavior
                for behavior in checked.behaviors
                if any(
                    evidence.field in authoritative_fields
                    for evidence in behavior.source_evidence
                )
            ]
        }
    )


def review_bdd(
    agent: OpenAIJsonAgent,
    record: TestRecord,
    contract: RequirementContract,
    facts: StaticFacts,
) -> AgentReview:
    review = agent.run(
        instructions=BDD_INSTRUCTIONS,
        payload={
            "record_key": record.record_key,
            "requirement": record.requirement,
            "behaviour_contracts": [
                behavior.model_dump(mode="json")
                for behavior in target_behaviors(record, contract)
            ],
            "gherkin_scenario": record.scenario,
            "static_facts": facts.model_dump(mode="json"),
            "assertion_data_flow": facts.data_flow.model_dump(mode="json"),
        },
        response_model=AgentReview,
    )
    review = review.model_copy(update={"agent": "bdd_traceability", "record_key": record.record_key, "suite_key": None, "dimension": "spec_alignment"})
    return validate_review_evidence(
        review,
        {
            "fine_grained_reqs": record.requirement,
            "gherkin_scenario": record.scenario,
            "static_facts": facts.model_dump_json(),
        },
    )


def review_step_code(
    agent: OpenAIJsonAgent,
    record: TestRecord,
    contract: RequirementContract,
    facts: StaticFacts,
) -> AgentReview:
    review = agent.run(
        instructions=STEP_CODE_INSTRUCTIONS,
        payload={
            "record_key": record.record_key,
            "behaviour_contracts": [
                behavior.model_dump(mode="json")
                for behavior in target_behaviors(record, contract)
            ],
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump(mode="json"),
            "assertion_data_flow": facts.data_flow.model_dump(mode="json"),
        },
        response_model=AgentReview,
    )
    review = review.model_copy(update={"agent": "step_code", "record_key": record.record_key, "suite_key": None, "dimension": "step_traceability"})
    return validate_review_evidence(
        review,
        {
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump_json(),
        },
    )


def review_oracle(
    agent: OpenAIJsonAgent,
    record: TestRecord,
    contract: RequirementContract,
    facts: StaticFacts,
) -> AgentReview:
    review = agent.run(
        instructions=ORACLE_INSTRUCTIONS,
        payload={
            "record_key": record.record_key,
            "requirement": record.requirement,
            "behaviour_contracts": [
                behavior.model_dump(mode="json")
                for behavior in target_behaviors(record, contract)
            ],
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump(mode="json"),
            "assertion_data_flow": facts.data_flow.model_dump(mode="json"),
        },
        response_model=AgentReview,
    )
    review = review.model_copy(update={"agent": "oracle_critic", "record_key": record.record_key, "suite_key": None, "dimension": "oracle_strength"})
    return validate_review_evidence(
        review,
        {
            "fine_grained_reqs": record.requirement,
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump_json(),
        },
    )


def review_mutation_hypothesis(
    agent: OpenAIJsonAgent,
    record: TestRecord,
    contract: RequirementContract,
    facts: StaticFacts,
) -> AgentReview:
    review = agent.run(
        instructions=MUTATION_HYPOTHESIS_INSTRUCTIONS,
        payload={
            "record_key": record.record_key,
            "requirement": record.requirement,
            "behaviour_contracts": [
                behavior.model_dump(mode="json")
                for behavior in target_behaviors(record, contract)
            ],
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump(mode="json"),
        },
        response_model=AgentReview,
    )
    review = review.model_copy(
        update={
            "agent": "mutation_hypothesis",
            "record_key": record.record_key,
            "suite_key": None,
            "dimension": "mutation_readiness",
        }
    )
    return validate_review_evidence(
        review,
        {
            "fine_grained_reqs": record.requirement,
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump_json(),
        },
    )


def review_suite(
    agent: OpenAIJsonAgent,
    suite_key: str,
    records: list[TestRecord],
    contract: RequirementContract,
) -> SuiteAssessment:
    output = agent.run(
        instructions=SUITE_INSTRUCTIONS,
        payload={
            "suite_key": suite_key,
            "fine_grained_reqs": records[0].requirement,
            "behaviour_contracts": [behavior.model_dump(mode="json") for behavior in contract.behaviors],
            "scenario_type_distribution": dict(Counter(record.scenario_type or "Unlabelled" for record in records)),
            "scenarios": [
                {
                    "record_key": record.record_key,
                    "test_id": record.test_id,
                    "scenario_type": record.scenario_type,
                    "gherkin_scenario": record.scenario,
                }
                for record in records
            ],
        },
        response_model=SuiteAgentOutput,
    )
    review = AgentReview(
        agent="suite_coverage",
        suite_key=suite_key,
        dimension="suite_adequacy",
        status=output.status,
        confidence=output.confidence,
        findings=output.findings,
    )
    review = validate_review_evidence(
        review,
        {
            "fine_grained_reqs": records[0].requirement,
            "scenario_corpus": "\n\n".join(record.scenario for record in records),
        },
    )
    return SuiteAssessment(
        review=review,
        behavior_coverage={item.behavior_id: item.status for item in output.behavior_coverage},
    )
