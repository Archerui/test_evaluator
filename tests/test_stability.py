from test_evaluator.stability import analyze_stability
from test_evaluator.schemas import RuntimeResult, Status


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
