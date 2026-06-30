from test_evaluator.agents import build_requirement_contract
from test_evaluator.evidence import validate_contract_evidence, validate_review_evidence
from test_evaluator.schemas import (
    AgentReview,
    Behavior,
    Evidence,
    Finding,
    RequirementContract,
    Severity,
    Status,
    SuiteAgentOutput,
    TestRecord as Record,
)


def test_unsupported_llm_finding_becomes_unknown() -> None:
    review = AgentReview(
        agent="oracle_critic",
        record_key="p::r::t",
        dimension="oracle_strength",
        status=Status.FAIL,
        confidence=0.9,
        findings=[
            Finding(
                criterion="invented claim",
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                confidence=0.9,
                evidence=[Evidence(field="step_code", quote="this quote is not in the source")],
                reasoning="unsupported",
            )
        ],
    )

    checked = validate_review_evidence(review, {"step_code": "assert actual == expected"})

    assert checked.status is Status.UNKNOWN
    assert checked.findings[0].status is Status.UNKNOWN
    assert checked.findings[0].evidence == []


def test_requirement_contract_drops_behavior_without_requirement_quote() -> None:
    contract = RequirementContract(
        project_id="p",
        requirement_id="r",
        behaviors=[
            Behavior(
                behavior_id="B1",
                kind="error",
                expected_observables=["invented behavior"],
                observability="dom",
                source_evidence=[Evidence(field="fine_grained_reqs", quote="not present")],
            )
        ],
    )

    checked = validate_contract_evidence(contract, {"fine_grained_reqs": "The user clicks Save."})

    assert checked.behaviors == []


def test_suite_agent_schema_uses_required_array_items() -> None:
    schema = SuiteAgentOutput.model_json_schema()

    assert set(schema["required"]) == {"status", "confidence", "findings", "behavior_coverage"}
    assert schema["properties"]["behavior_coverage"]["type"] == "array"


def test_requirement_agent_cannot_promote_summary_context_to_suite_behavior() -> None:
    record = Record(
        project_id="p",
        requirement_id="r",
        test_id="t",
        requirement_summary="The broader app also exports reports.",
        requirement="The user can save the current form.",
        scenario="Scenario: Save\nWhen the user saves\nThen the form is saved",
        step_code="assert True",
    )
    contract = RequirementContract(
        project_id="p",
        requirement_id="r",
        behaviors=[
            Behavior(
                behavior_id="save",
                kind="normal",
                expected_observables=["The form is saved."],
                observability="dom",
                source_evidence=[
                    Evidence(
                        field="fine_grained_reqs",
                        quote="The user can save the current form.",
                    )
                ],
            ),
            Behavior(
                behavior_id="export",
                kind="other",
                expected_observables=["A report is exported."],
                observability="dom",
                source_evidence=[
                    Evidence(
                        field="requirement_summary",
                        quote="The broader app also exports reports.",
                    )
                ],
            ),
        ],
    )

    class FakeAgent:
        def run(self, **_kwargs):
            return contract

    checked = build_requirement_contract(FakeAgent(), record)  # type: ignore[arg-type]

    assert [behavior.behavior_id for behavior in checked.behaviors] == ["save"]
