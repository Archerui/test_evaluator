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
from .schemas import AgentReview, RequirementContract, StaticFacts, SuiteAgentOutput, SuiteAssessment


COMMON_GUARDRAILS = """
You are an evidence-grounded software-test reviewer. Use only the provided
CSV-derived content and static facts. Never assume access to the application,
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
state. Every source_evidence.field must be `fine_grained_reqs` or
`requirement_summary`.
""".strip()


BDD_INSTRUCTIONS = f"""
{COMMON_GUARDRAILS}

Act as the BDD Traceability Agent. Compare the requirement behaviour contracts
with the supplied Gherkin scenario. Assess only whether the scenario expresses
the right preconditions, action, expected outcome, constraints, and scenario
type. Do not inspect implementation quality and do not infer browser behavior.
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
wait patterns, and driver lifecycle. A literal data-testid mismatch is only a
candidate risk, not proof of failure. Do not claim the page itself works. Use
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
For a browser/external API behaviour, require a mock, spy, or another concrete
observable that demonstrates the required call and arguments. Use a minimal
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
error condition. Call unproven omissions 'candidate gaps'. Use
dimension='suite_adequacy', agent='suite_coverage', and set suite_key exactly as
provided. Return a compact object with `status`, `confidence`, `findings`, and
a `behavior_coverage` list containing `{{behavior_id, status}}` for every supplied
behaviour ID; return at most 5 concise findings.
Evidence fields must be `fine_grained_reqs` or `scenario_corpus`.
""".strip()


def build_requirement_contract(agent: OpenAIJsonAgent, record: TestRecord) -> RequirementContract:
    contract = agent.run(
        instructions=REQUIREMENT_INSTRUCTIONS,
        payload={
            "project_id": record.project_id,
            "requirement_id": record.requirement_id,
            "requirement_summary": record.requirement_summary,
            "fine_grained_reqs": record.requirement,
        },
        response_model=RequirementContract,
    )
    # Model-provided identity is not authoritative; preserve the CSV identity.
    contract = contract.model_copy(update={"project_id": record.project_id, "requirement_id": record.requirement_id})
    return validate_contract_evidence(
        contract,
        {
            "fine_grained_reqs": record.requirement,
            "requirement_summary": record.requirement_summary,
        },
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
            "behaviour_contracts": [behavior.model_dump(mode="json") for behavior in contract.behaviors],
            "gherkin_scenario": record.scenario,
            "static_facts": facts.model_dump(mode="json"),
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
            "behaviour_contracts": [behavior.model_dump(mode="json") for behavior in contract.behaviors],
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump(mode="json"),
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
            "behaviour_contracts": [behavior.model_dump(mode="json") for behavior in contract.behaviors],
            "gherkin_scenario": record.scenario,
            "step_code": record.step_code,
            "static_facts": facts.model_dump(mode="json"),
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
            "behaviour_contracts": [behavior.model_dump(mode="json") for behavior in contract.behaviors],
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
