"""Repeated-run stability and flaky classification."""

from __future__ import annotations

from .schemas import RuntimeResult, StabilityAttempt, StabilityReport, Status


def analyze_stability(
    record_key: str,
    requested_runs: int,
    results: list[RuntimeResult],
) -> StabilityReport:
    if requested_runs <= 0:
        raise ValueError("requested_runs must be positive")
    attempts = [
        StabilityAttempt(
            run_index=index,
            status=result.status,
            duration_seconds=result.duration_seconds,
            error_type=result.error_type,
        )
        for index, result in enumerate(results)
    ]
    behavioral = [result for result in results if result.status in {"pass", "fail", "timeout"}]
    statuses = {result.status for result in behavioral}
    flaky = "pass" in statuses and bool(statuses.intersection({"fail", "timeout"}))
    pass_rate = (
        sum(result.status == "pass" for result in behavioral) / len(behavioral)
        if behavioral
        else None
    )
    if flaky:
        status = Status.WARNING
    elif behavioral and statuses == {"pass"} and len(results) >= requested_runs:
        status = Status.PASS if requested_runs >= 2 else Status.UNKNOWN
    elif behavioral and statuses == {"fail"}:
        status = Status.FAIL
    elif behavioral:
        status = Status.WARNING
    else:
        status = Status.UNKNOWN
    return StabilityReport(
        record_key=record_key,
        requested_runs=requested_runs,
        completed_runs=len(results),
        pass_rate=pass_rate,
        flaky=flaky,
        status=status,
        attempts=attempts,
    )
