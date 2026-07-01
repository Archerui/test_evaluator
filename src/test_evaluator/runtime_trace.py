"""Deterministic interpretation of baseline runtime artifacts."""

from __future__ import annotations

from pathlib import Path
import json

from .schemas import (
    Evidence,
    FailureAttribution,
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


def _runtime_evidence(request: RuntimeTraceInput) -> list[Evidence]:
    runtime = request.runtime
    summary = f"status={runtime.status}"
    if runtime.error_type:
        summary += f", error_type={runtime.error_type}"
    if runtime.failed_step:
        summary += f", failed_step={runtime.failed_step}"
    evidence = [Evidence(field="runtime.result", quote=summary)]
    if runtime.stderr:
        evidence.append(
            Evidence(
                field="runtime.stderr",
                quote=_excerpt(runtime.stderr.path),
                artifact=runtime.stderr,
            )
        )
    return evidence


def _dimension_status(request: RuntimeTraceInput, dimension: str) -> Status | None:
    review = next((item for item in request.reviews if item.dimension == dimension), None)
    return review.status if review else None


def _review_evidence(request: RuntimeTraceInput, dimensions: set[str]) -> list[Evidence]:
    evidence: list[Evidence] = []
    for review in request.reviews:
        if review.dimension not in dimensions:
            continue
        for finding in review.findings:
            evidence.extend(finding.evidence[:1])
    return evidence[:4]


def _console_application_error(request: RuntimeTraceInput) -> tuple[bool, str | None]:
    runtime = request.runtime
    excerpt = _excerpt(runtime.console_log.path if runtime.console_log else None)
    if not excerpt:
        return False, None
    lowered = excerpt.casefold()
    markers = (
        "uncaught",
        "unhandledrejection",
        "referenceerror",
        "typeerror",
        "rangeerror",
    )
    return any(marker in lowered for marker in markers), excerpt


def _failed_step_purpose(failed_step: str | None) -> str | None:
    normalized = (failed_step or "").strip().casefold()
    if normalized.startswith("given"):
        return "precondition"
    if normalized.startswith("when"):
        return "action_target"
    if normalized.startswith(("then", "and", "but")):
        return "oracle_target"
    return None


def _attribution(
    request: RuntimeTraceInput,
    *,
    origin: str,
    confidence: float,
    effect: str,
    reasoning: str,
    signals: list[str],
    evidence: list[Evidence] | None = None,
) -> FailureAttribution:
    merged_evidence = [*_runtime_evidence(request), *(evidence or [])]
    return FailureAttribution(
        origin=origin,  # type: ignore[arg-type]
        confidence=confidence,
        test_quality_effect=effect,  # type: ignore[arg-type]
        reasoning=reasoning,
        signals=signals,
        evidence=merged_evidence[:8],
    )


def attribute_runtime_failure(request: RuntimeTraceInput) -> FailureAttribution:
    """Attribute a raw execution result without blaming the test by default."""

    runtime = request.runtime
    facts = request.static_facts
    if runtime.status == "pass":
        return _attribution(
            request,
            origin="no_failure",
            confidence=1.0,
            effect="pass",
            reasoning="The unchanged baseline test completed successfully.",
            signals=["baseline_passed"],
        )
    if runtime.status == "env_error" or runtime.error_type in {"env_error", "browser_error"}:
        return _attribution(
            request,
            origin="environment_issue",
            confidence=0.99,
            effect="neutral",
            reasoning="The browser or runtime environment was unavailable; this is not evidence of a defective test.",
            signals=["runtime_environment_unavailable"],
        )
    if runtime.status == "skipped":
        return _attribution(
            request,
            origin="indeterminate",
            confidence=1.0,
            effect="unknown",
            reasoning="The baseline was not executed, so test runtime quality cannot be judged.",
            signals=["baseline_skipped"],
        )
    if runtime.error_type == "syntax_error" or not facts.python_parseable:
        return _attribution(
            request,
            origin="test_defect",
            confidence=0.99,
            effect="penalize",
            reasoning="The evaluated Python step implementation is syntactically invalid.",
            signals=["test_code_syntax_error"],
        )
    if facts.missing_step_definitions:
        return _attribution(
            request,
            origin="test_defect",
            confidence=0.98,
            effect="penalize",
            reasoning="The scenario contains steps without matching Behave implementations.",
            signals=["missing_step_implementation"],
        )

    semantic_dimensions = {"spec_alignment", "step_traceability", "oracle_strength"}
    statuses = {
        dimension: _dimension_status(request, dimension)
        for dimension in semantic_dimensions
    }
    failed_dimensions = sorted(
        dimension for dimension, status in statuses.items() if status is Status.FAIL
    )
    all_semantic_pass = all(statuses[dimension] is Status.PASS for dimension in semantic_dimensions)
    review_evidence = _review_evidence(request, set(failed_dimensions))
    console_error, console_excerpt = _console_application_error(request)
    console_evidence = (
        [
            Evidence(
                field="runtime.console_log",
                quote=console_excerpt,
                artifact=runtime.console_log,
            )
        ]
        if console_error and runtime.console_log
        else []
    )

    if runtime.error_type == "selector_not_found":
        grounding = request.selector_grounding
        if grounding and grounding.missing_source_anchors:
            return _attribution(
                request,
                origin="contract_or_dataset_mismatch",
                confidence=0.85,
                effect="neutral",
                reasoning=(
                    "A selector named by the requirement or scenario is absent from the application source. "
                    "The source/contract mismatch must not be charged to the evaluated test without further evidence."
                ),
                signals=["required_anchor_missing_from_source"],
                evidence=[
                    Evidence(
                        field="source_grounding.missing_source_anchors",
                        quote=", ".join(grounding.missing_source_anchors[:5]),
                    )
                ],
            )
        purpose = _failed_step_purpose(runtime.failed_step)
        missing_test_selectors = [
            item.selector
            for item in (grounding.selectors if grounding else [])
            if not item.source_exists and (purpose is None or item.purpose == purpose)
        ]
        if missing_test_selectors:
            return _attribution(
                request,
                origin="test_defect",
                confidence=0.90,
                effect="penalize",
                reasoning="The failed test step uses a literal selector that is not present in the application source model.",
                signals=["test_selector_absent_from_source"],
                evidence=[
                    Evidence(
                        field="source_grounding.selectors",
                        quote=", ".join(missing_test_selectors[:5]),
                    )
                ],
            )
        if failed_dimensions:
            return _attribution(
                request,
                origin="test_defect",
                confidence=0.82,
                effect="penalize",
                reasoning="The selector failure coincides with an evidence-backed failure in the test specification or implementation.",
                signals=[f"failed_basic_dimension:{item}" for item in failed_dimensions],
                evidence=review_evidence,
            )
        return _attribution(
            request,
            origin="indeterminate",
            confidence=0.55,
            effect="unknown",
            reasoning="The element was not found at runtime, but the available evidence cannot distinguish test timing/action defects from missing application state.",
            signals=["runtime_selector_not_found"],
        )

    if runtime.error_type == "assertion_failure":
        if failed_dimensions:
            return _attribution(
                request,
                origin="test_defect",
                confidence=0.88,
                effect="penalize",
                reasoning="The runtime assertion failure coincides with an evidence-backed defect in the test specification, step implementation, or oracle.",
                signals=[f"failed_basic_dimension:{item}" for item in failed_dimensions],
                evidence=review_evidence,
            )
        grounding_status = request.selector_grounding.status if request.selector_grounding else None
        grounding_supports_test = grounding_status in {Status.PASS, Status.SKIPPED}
        if all_semantic_pass and grounding_supports_test:
            return _attribution(
                request,
                origin="application_defect",
                confidence=0.78,
                effect="neutral",
                reasoning=(
                    "The scenario, step implementation, oracle, and source selectors are independently supported, "
                    "so the observed assertion mismatch is more consistent with application behavior than a defective test."
                ),
                signals=["basic_semantics_pass", "source_grounding_supported", "assertion_observed_mismatch"],
            )
        return _attribution(
            request,
            origin="indeterminate",
            confidence=0.50,
            effect="unknown",
            reasoning="An assertion failed, but the available static and source evidence is insufficient to assign the mismatch to the test or application.",
            signals=["assertion_failure_without_decisive_attribution"],
        )

    if runtime.error_type == "path_error":
        if facts.hardcoded_file_paths:
            return _attribution(
                request,
                origin="test_defect",
                confidence=0.82,
                effect="penalize",
                reasoning="The evaluated test contains a hard-coded local path and failed with a path error.",
                signals=["hardcoded_test_path", "runtime_path_error"],
                evidence=[
                    Evidence(
                        field="derived.static_facts",
                        quote=", ".join(facts.hardcoded_file_paths[:5]),
                    )
                ],
            )
        return _attribution(
            request,
            origin="indeterminate",
            confidence=0.50,
            effect="unknown",
            reasoning="A file path failed, but the evidence does not establish whether it originated in the test, application resources, or workspace materialization.",
            signals=["runtime_path_error"],
        )

    if runtime.status == "timeout" or runtime.error_type == "timeout":
        return _attribution(
            request,
            origin="indeterminate",
            confidence=0.45,
            effect="unknown",
            reasoning="A timeout alone cannot distinguish a defective wait/action from slow or blocked application behavior.",
            signals=["runtime_timeout"],
        )

    if console_error and all_semantic_pass:
        return _attribution(
            request,
            origin="application_defect",
            confidence=0.80,
            effect="neutral",
            reasoning="The test's semantic dimensions passed and the browser console captured an uncaught application-side exception.",
            signals=["basic_semantics_pass", "application_console_exception"],
            evidence=console_evidence,
        )
    if failed_dimensions:
        return _attribution(
            request,
            origin="test_defect",
            confidence=0.80,
            effect="penalize",
            reasoning="The runtime failure coincides with an evidence-backed defect in the evaluated test.",
            signals=[f"failed_basic_dimension:{item}" for item in failed_dimensions],
            evidence=review_evidence,
        )
    return _attribution(
        request,
        origin="indeterminate",
        confidence=0.40,
        effect="unknown",
        reasoning="The runtime artifacts do not provide enough evidence to assign this failure to the test or application.",
        signals=["unclassified_runtime_failure"],
        evidence=console_evidence,
    )


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

    attribution = attribute_runtime_failure(request)
    likely_cause = {
        "no_failure": "no_failure",
        "test_defect": "test_bug",
        "application_defect": "app_bug",
        "environment_issue": "environment_issue",
        "evaluator_issue": "evaluator_issue",
        "contract_or_dataset_mismatch": "contract_or_dataset_mismatch",
        "indeterminate": "indeterminate",
    }[attribution.origin]
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
        failure_attribution=attribution,
    )

    findings: list[Finding] = []
    if runtime.status in {"fail", "timeout"}:
        penalize = attribution.test_quality_effect == "penalize"
        findings.append(
            Finding(
                criterion="Runtime failure is attributable to the evaluated test",
                status=Status.FAIL if penalize else Status.UNKNOWN,
                severity=Severity.MAJOR if penalize else Severity.INFO,
                confidence=attribution.confidence,
                evidence=attribution.evidence,
                reasoning=attribution.reasoning,
                suggested_fix=(
                    "Correct the test defect identified by the attribution signals and rerun the unchanged baseline."
                    if penalize
                    else "Inspect the attribution evidence; do not lower test quality until responsibility is established."
                ),
            )
        )
    envelope_status = (
        Status.PASS
        if attribution.test_quality_effect == "pass"
        else Status.FAIL
        if attribution.test_quality_effect == "penalize"
        else Status.SKIPPED
        if runtime.status == "skipped"
        else Status.UNKNOWN
    )
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
