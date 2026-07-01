from test_evaluator.scoring import attach_stability_results
from test_evaluator.stability import analyze_stability
from test_evaluator.schemas import (
    EvaluationRun,
    FailureAttribution,
    ProjectReport,
    RuntimeResult,
    RuntimeTrace,
    StaticFacts,
    Status,
    TestReport as Report,
)


def test_stability_detects_mixed_pass_and_failure() -> None:
    report = analyze_stability(
        "Bench::1::1",
        3,
        [
            RuntimeResult(record_key="Bench::1::1", status="pass"),
            RuntimeResult(
                record_key="Bench::1::1",
                status="fail",
                error_type="assertion_failure",
            ),
            RuntimeResult(record_key="Bench::1::1", status="pass"),
        ],
    )

    assert report.flaky is True
    assert report.status is Status.WARNING
    assert report.pass_rate == 2 / 3


def test_single_run_does_not_claim_stability() -> None:
    report = analyze_stability(
        "Bench::1::1",
        1,
        [RuntimeResult(record_key="Bench::1::1", status="pass")],
    )

    assert report.flaky is False
    assert report.status is Status.UNKNOWN


def test_flaky_gate_requires_a_test_owned_instability_signal() -> None:
    stability = analyze_stability(
        "Bench::1::1",
        2,
        [
            RuntimeResult(record_key="Bench::1::1", status="pass"),
            RuntimeResult(
                record_key="Bench::1::1",
                status="fail",
                error_type="assertion_failure",
            ),
        ],
    )

    def run(*, sleeps: int) -> EvaluationRun:
        runtime = RuntimeResult(record_key="Bench::1::1", status="pass")
        report = Report(
            record_key="Bench::1::1",
            project_id="Bench",
            requirement_id="1",
            test_id="1",
            confidence_coverage=1.0,
            risk="low",
            static_facts=StaticFacts(
                python_parseable=True,
                scenario_present=True,
                sleep_count=sleeps,
            ),
            runtime_trace=RuntimeTrace(
                record_key="Bench::1::1",
                execution_status=runtime,
                failure_attribution=FailureAttribution(
                    origin="no_failure",
                    confidence=1.0,
                    test_quality_effect="pass",
                    reasoning="Baseline passed.",
                ),
            ),
        )
        return EvaluationRun(
            mode="full",
            tests=[report],
            requirements=[],
            projects=[ProjectReport(project_id="Bench", test_count=1, requirement_count=0)],
        )

    unattributed = run(sleeps=0)
    attach_stability_results(unattributed, {"Bench::1::1": stability})
    assert "flaky_runtime" not in unattributed.tests[0].hard_gates
    assert unattributed.tests[0].risk == "low"
    assert next(
        review for review in unattributed.tests[0].reviews if review.agent == "stability_analyzer"
    ).status is Status.UNKNOWN

    test_owned = run(sleeps=1)
    attach_stability_results(test_owned, {"Bench::1::1": stability})
    assert "flaky_runtime" in test_owned.tests[0].hard_gates
    assert test_owned.tests[0].risk == "major"
