from test_evaluator.scoring import attach_runtime_results, coordinate_full_scores
from test_evaluator.schemas import (
    EvaluationRun,
    FailureAttribution,
    ProjectReport,
    RequirementReport,
    RuntimeResult,
    RuntimeTrace,
    StaticFacts,
    Status,
    TestReport as Report,
)


def _facts() -> StaticFacts:
    return StaticFacts(python_parseable=True, scenario_present=True)


def test_full_scoring_uses_proposal_weights_and_requirement_components() -> None:
    test = Report(
        record_key="Bench::1::1",
        project_id="Bench",
        requirement_id="1",
        test_id="1",
        scenario_type="Normal",
        confidence_coverage=1.0,
        risk="low",
        dimension_scores={
            "spec_alignment": 1.0,
            "step_traceability": 1.0,
            "oracle_strength": 1.0,
            "runtime_result": 1.0,
            "mutation_effectiveness": 0.5,
            "robustness": 1.0,
            "source_grounding": 1.0,
        },
        static_facts=_facts(),
    )
    requirement = RequirementReport(
        suite_key="Bench::1",
        project_id="Bench",
        requirement_id="1",
        test_count=1,
        scenario_distribution={"Normal": 1, "Edge": 1, "Error": 1},
        runtime_pass_rate=1.0,
        mutation_score=50.0,
        behavior_coverage={"b1": Status.PASS},
    )
    run = EvaluationRun(
        mode="full",
        tests=[test],
        requirements=[requirement],
        projects=[ProjectReport(project_id="Bench", test_count=1, requirement_count=1)],
    )

    coordinated = coordinate_full_scores(run)

    assert coordinated.tests[0].full_test_quality_score == 87.5
    assert coordinated.tests[0].test_quality_score == 87.5
    assert coordinated.tests[0].full_confidence_coverage == 1.0
    assert coordinated.requirements[0].full_requirement_adequacy_score == 90.0
    assert coordinated.requirements[0].full_confidence_coverage == 1.0
    assert coordinated.projects[0].average_full_test_quality_score == 87.5


def test_full_scoring_requires_half_the_weight_and_applies_hard_gate() -> None:
    insufficient = Report(
        record_key="Bench::1::1",
        project_id="Bench",
        requirement_id="1",
        test_id="1",
        confidence_coverage=0.0,
        risk="major",
        dimension_scores={"robustness": 1.0, "runtime_result": 1.0},
        static_facts=_facts(),
    )
    gated = insufficient.model_copy(
        update={
            "record_key": "Bench::1::2",
            "test_id": "2",
            "dimension_scores": {
                "spec_alignment": 1.0,
                "step_traceability": 1.0,
                "oracle_strength": 1.0,
                "runtime_result": 1.0,
                "mutation_effectiveness": 1.0,
                "robustness": 1.0,
            },
            "hard_gates": ["mutation_score_zero"],
        }
    )
    run = EvaluationRun(
        mode="full",
        tests=[insufficient, gated],
        requirements=[],
        projects=[ProjectReport(project_id="Bench", test_count=2, requirement_count=0)],
    )

    coordinate_full_scores(run)

    assert insufficient.full_test_quality_score is None
    assert insufficient.confidence_coverage == 0.25
    assert insufficient.full_confidence_coverage == 0.25
    assert gated.full_test_quality_score == 65.0


def test_runtime_score_penalizes_only_failures_attributed_to_the_test() -> None:
    def report(test_id: str, origin: str, effect: str) -> Report:
        runtime = RuntimeResult(
            record_key=f"Bench::1::{test_id}",
            status="fail",
            error_type="assertion_failure",
        )
        return Report(
            record_key=runtime.record_key,
            project_id="Bench",
            requirement_id="1",
            test_id=test_id,
            confidence_coverage=1.0,
            risk="low",
            dimension_scores={"robustness": 1.0},
            static_facts=_facts(),
            runtime_trace=RuntimeTrace(
                record_key=runtime.record_key,
                execution_status=runtime,
                failure_attribution=FailureAttribution(
                    origin=origin,
                    confidence=0.9,
                    test_quality_effect=effect,
                    reasoning="Attribution fixture.",
                ),
            ),
        )

    application = report("1", "application_defect", "neutral")
    test_defect = report("2", "test_defect", "penalize")
    requirement = RequirementReport(
        suite_key="Bench::1",
        project_id="Bench",
        requirement_id="1",
        test_count=2,
    )
    run = EvaluationRun(
        mode="full",
        tests=[application, test_defect],
        requirements=[requirement],
        projects=[ProjectReport(project_id="Bench", test_count=2, requirement_count=1)],
    )
    runtimes = {
        item.record_key: item.runtime_trace.execution_status for item in run.tests
    }

    attach_runtime_results(run, runtimes)

    assert application.dimension_scores["runtime_result"] is None
    assert "baseline_test_failed" not in application.hard_gates
    assert application.risk == "low"
    assert test_defect.dimension_scores["runtime_result"] == 0.0
    assert "baseline_test_failed" in test_defect.hard_gates
    assert test_defect.risk == "major"
    assert requirement.runtime_pass_rate == 0.0
