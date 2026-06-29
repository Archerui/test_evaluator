"""Deterministic interpretation of baseline runtime artifacts."""

from __future__ import annotations

from pathlib import Path
import json

from .schemas import (
    Evidence,
    Finding,
    RuntimeObservation,
    RuntimeTrace,
    RuntimeTraceInput,
    RuntimeTraceOutput,
    Severity,
    Status,
)


def _excerpt(path: str | None, limit: int = 800) -> str | None:
    if not path:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8", errors="replace").strip()
    except OSError:
        return None
    return text[-limit:] if text else None


def _json_payload(path: str | None):
    if not path:
        return None
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _cause(error_type: str | None, status: str) -> str:
    if status == "env_error" or error_type in {"env_error", "browser_error"}:
        return "environment_issue"
    if status == "timeout" or error_type == "timeout":
        return "timeout_or_flaky"
    if error_type == "selector_not_found":
        return "selector_issue"
    if error_type == "path_error":
        return "path_issue"
    if error_type == "syntax_error":
        return "test_bug"
    return "unknown"


def trace_runtime(request: RuntimeTraceInput) -> RuntimeTraceOutput:
    runtime = request.runtime
    observations = [
        RuntimeObservation(
            kind="step_result",
            summary=(
                f"Baseline status={runtime.status}"
                + (f", failed_step={runtime.failed_step}" if runtime.failed_step else "")
                + (f", error_type={runtime.error_type}" if runtime.error_type else "")
            ),
        )
    ]
    stderr_excerpt = _excerpt(runtime.stderr.path if runtime.stderr else None)
    if stderr_excerpt:
        observations.append(
            RuntimeObservation(
                kind="exception",
                summary=stderr_excerpt,
                evidence=[Evidence(field="runtime.stderr", artifact=runtime.stderr)],
            )
        )
    if runtime.dom_snapshot:
        observations.append(
            RuntimeObservation(
                kind="dom_state",
                summary="A DOM snapshot was captured at the failed step.",
                evidence=[Evidence(field="runtime.dom_snapshot", artifact=runtime.dom_snapshot)],
            )
        )
    if runtime.screenshot:
        observations.append(
            RuntimeObservation(
                kind="screenshot",
                summary="A browser screenshot was captured at the failed step.",
                evidence=[Evidence(field="runtime.screenshot", artifact=runtime.screenshot)],
            )
        )
    if runtime.console_log:
        observations.append(
            RuntimeObservation(
                kind="console",
                summary=_excerpt(runtime.console_log.path) or "A browser console log was captured.",
                evidence=[Evidence(field="runtime.console_log", artifact=runtime.console_log)],
            )
        )
    browser_trace = _json_payload(runtime.browser_trace.path if runtime.browser_trace else None)
    if isinstance(browser_trace, dict):
        for key, kind in (
            ("storage", "storage"),
            ("network", "network"),
            ("browser_api", "browser_api"),
        ):
            events = browser_trace.get(key, [])
            if isinstance(events, list) and events:
                operations = sorted(
                    {str(item.get("operation", "unknown")) for item in events if isinstance(item, dict)}
                )
                observations.append(
                    RuntimeObservation(
                        kind=kind,  # type: ignore[arg-type]
                        summary=f"Observed {len(events)} {key} event(s): {', '.join(operations[:8])}.",
                        evidence=[Evidence(field=f"runtime.{key}", artifact=runtime.browser_trace)],
                    )
                )
    network_events = _json_payload(runtime.network_log.path if runtime.network_log else None)
    if isinstance(network_events, list) and network_events:
        observations.append(
            RuntimeObservation(
                kind="network",
                summary=f"Chrome DevTools captured {len(network_events)} Network domain event(s).",
                evidence=[Evidence(field="runtime.network_log", artifact=runtime.network_log)],
            )
        )

    likely_cause = _cause(runtime.error_type, runtime.status)
    if runtime.status == "timeout":
        flaky_risk = "high"
    elif request.static_facts.sleep_count or runtime.status == "fail":
        flaky_risk = "medium"
    elif runtime.status == "pass":
        flaky_risk = "low"
    else:
        flaky_risk = "unknown"
    trace = RuntimeTrace(
        record_key=request.record.record_key,
        execution_status=runtime,
        observations=observations,
        likely_failure_cause=likely_cause,  # type: ignore[arg-type]
        flaky_risk=flaky_risk,  # type: ignore[arg-type]
    )

    findings: list[Finding] = []
    if runtime.status in {"fail", "timeout"}:
        evidence = []
        if runtime.stderr:
            evidence.append(Evidence(field="runtime.stderr", artifact=runtime.stderr, quote=stderr_excerpt))
        findings.append(
            Finding(
                criterion="Baseline test executes successfully",
                status=Status.FAIL if runtime.status == "fail" else Status.WARNING,
                severity=Severity.MAJOR,
                confidence=1.0,
                evidence=evidence,
                reasoning=f"The baseline run ended with {runtime.status}; likely cause category: {likely_cause}.",
                suggested_fix="Inspect the failed step and captured runtime artifacts before interpreting mutation results.",
            )
        )
    envelope_status = {
        "pass": Status.PASS,
        "fail": Status.FAIL,
        "timeout": Status.WARNING,
        "env_error": Status.UNKNOWN,
        "skipped": Status.SKIPPED,
    }[runtime.status]
    return RuntimeTraceOutput(
        agent="runtime_trace",
        run_id=request.run_id,
        mode="full",
        project_id=request.record.project_id,
        suite_key=request.record.suite_key,
        record_key=request.record.record_key,
        status=envelope_status,
        confidence=1.0 if runtime.status in {"pass", "fail", "timeout"} else 0.5,
        findings=findings,
        runtime_trace=trace,
    )
