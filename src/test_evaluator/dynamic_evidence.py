"""Post-runtime evidence feedback for oracle and suite-level behavior reviews."""

from __future__ import annotations

import re

from .schemas import (
    AgentReview,
    BehaviorCoverage,
    DynamicOracleInput,
    DynamicOracleOutput,
    DynamicSuiteCoverageInput,
    DynamicSuiteCoverageOutput,
    Evidence,
    Finding,
    MutationPlan,
    Severity,
    Status,
)


def _mutants_by_id(plan: MutationPlan | None):
    return {mutant.mutant_id: mutant for mutant in plan.mutants} if plan else {}


def _oracle_mutation_outcomes(request: DynamicOracleInput):
    mutant_by_id = _mutants_by_id(request.mutation_plan)
    killed = []
    survived = []
    for result in request.mutation_results:
        mutant = mutant_by_id.get(result.mutant_id)
        if request.record.record_key in result.killed_by_record_keys:
            killed.append(result)
        elif request.record.record_key in result.survived_record_keys:
            if mutant is None or not mutant.suspected_equivalent:
                survived.append(result)
    return mutant_by_id, killed, survived


def analyze_dynamic_oracle(request: DynamicOracleInput) -> DynamicOracleOutput:
    """Describe observed fault detection without changing the oracle score weight."""

    runtime = request.runtime_trace.execution_status
    runtime_confirmed = runtime.status == "pass"
    oracle_selectors = sorted(
        {
            item.selector
            for item in (request.selector_grounding.selectors if request.selector_grounding else [])
            if item.purpose == "oracle_target" and (item.source_exists or runtime_confirmed)
        }
    )
    mutant_by_id, killed, survived = _oracle_mutation_outcomes(request)
    denominator = len(killed) + len(survived)
    mutation_score = len(killed) / denominator * 100.0 if denominator else None
    findings: list[Finding] = []
    for result in survived[:5]:
        mutant = mutant_by_id.get(result.mutant_id)
        evidence = [Evidence(field="mutation_result", quote=result.mutant_id)]
        operator = "application"
        if mutant is not None:
            operator = mutant.operator
            evidence = [
                Evidence(
                    field="application_source",
                    quote=mutant.original,
                    file_path=mutant.file_path,
                    line_start=mutant.line_start,
                )
            ]
        findings.append(
            Finding(
                criterion=f"Dynamic oracle fails to distinguish mutant {result.mutant_id}",
                status=Status.FAIL,
                severity=Severity.MAJOR,
                confidence=1.0,
                evidence=evidence,
                reasoning=(
                    f"The baseline test passed and also passed after the {operator} mutation; "
                    "the observed oracle did not distinguish this injected fault."
                ),
                suggested_fix="Assert the exact observable state that this source mutation changes.",
            )
        )

    warnings: list[str] = []
    if not runtime_confirmed:
        status = Status.SKIPPED
        warnings.append(
            f"Dynamic oracle evidence requires a passing baseline; baseline status was {runtime.status}."
        )
    elif mutation_score is None:
        status = Status.UNKNOWN
        warnings.append("No valid killed/survived mutant exercised this test.")
    elif mutation_score >= 80.0:
        status = Status.PASS
    elif mutation_score > 0.0:
        status = Status.WARNING
    else:
        status = Status.FAIL
    return DynamicOracleOutput(
        agent="dynamic_oracle",
        run_id=request.run_id,
        mode="full",
        project_id=request.record.project_id,
        suite_key=request.record.suite_key,
        record_key=request.record.record_key,
        dimension="dynamic_oracle_evidence",
        status=status,
        confidence=1.0 if mutation_score is not None else 0.5 if runtime_confirmed else 0.0,
        findings=findings,
        warnings=warnings,
        runtime_confirmed=runtime_confirmed,
        oracle_selectors=oracle_selectors,
        mutation_score=mutation_score,
        killed_mutants=sorted(result.mutant_id for result in killed),
        survived_mutants=sorted(result.mutant_id for result in survived),
    )


def _anchor_tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in re.findall(r"[A-Za-z0-9_-]{3,}", value)
        if token.casefold() not in {"data-testid", "data-test-id"}
    }


def _selector_supports_behavior(selector: str, anchors: list[str]) -> bool:
    selector_tokens = _anchor_tokens(selector)
    return any(selector_tokens.intersection(_anchor_tokens(anchor)) for anchor in anchors)


def _dynamic_status(
    *,
    base_status: Status | None,
    killed: list[str],
    survived: list[str],
    runtime_confirmed: list[str],
) -> Status:
    if survived and not killed:
        return Status.FAIL
    if survived:
        return Status.WARNING
    if killed:
        return Status.WARNING if base_status is Status.FAIL else Status.PASS
    if runtime_confirmed and base_status is Status.PASS:
        # A passing runtime confirms executability, but without a counterfactual
        # it is not strong enough to claim dynamic fault-detection coverage.
        return Status.WARNING
    return Status.UNKNOWN


def analyze_dynamic_suite_coverage(
    request: DynamicSuiteCoverageInput,
) -> DynamicSuiteCoverageOutput:
    """Build behavior-level runtime/source/mutation evidence as a non-scoring layer."""

    mutant_by_id = _mutants_by_id(request.mutation_plan)
    suite_record_keys = {record.record_key for record in request.records}
    coverage: list[BehaviorCoverage] = []
    findings: list[Finding] = []
    for behavior in request.contract.behaviors:
        relevant_mutants = {
            mutant.mutant_id: mutant
            for mutant in mutant_by_id.values()
            if behavior.behavior_id in mutant.behavior_candidates
        }
        killed: list[str] = []
        survived: list[str] = []
        for result in request.mutation_results:
            mutant = relevant_mutants.get(result.mutant_id)
            if mutant is None:
                continue
            if suite_record_keys.intersection(result.killed_by_record_keys):
                killed.append(result.mutant_id)
            elif (
                suite_record_keys.intersection(result.survived_record_keys)
                and not mutant.suspected_equivalent
            ):
                survived.append(result.mutant_id)

        runtime_confirmed: list[str] = []
        evidence: list[Evidence] = []
        for record in request.records:
            runtime = request.runtime_results.get(record.record_key)
            if runtime is None or runtime.status != "pass":
                continue
            grounding = request.selector_grounding.get(record.record_key)
            selector_matches = []
            if grounding and behavior.ui_anchors:
                selector_matches = [
                    item
                    for item in grounding.selectors
                    if item.source_exists
                    and _selector_supports_behavior(item.selector, behavior.ui_anchors)
                ]
            if not behavior.ui_anchors or selector_matches:
                runtime_confirmed.append(record.record_key)
                if runtime.behave_json:
                    evidence.append(
                        Evidence(field="runtime.behave_json", artifact=runtime.behave_json)
                    )
                for item in selector_matches[:2]:
                    evidence.extend(item.evidence[:1])

        for mutant_id in (killed + survived)[:5]:
            mutant = relevant_mutants[mutant_id]
            evidence.append(
                Evidence(
                    field="application_source",
                    quote=mutant.original,
                    file_path=mutant.file_path,
                    line_start=mutant.line_start,
                )
            )
        base_status = request.base_behavior_coverage.get(behavior.behavior_id)
        status = _dynamic_status(
            base_status=base_status,
            killed=killed,
            survived=survived,
            runtime_confirmed=runtime_confirmed,
        )
        covered_by = (
            sorted(suite_record_keys)
            if base_status in {Status.PASS, Status.WARNING}
            else []
        )
        coverage.append(
            BehaviorCoverage(
                behavior_id=behavior.behavior_id,
                status=status,
                covered_by_records=covered_by,
                runtime_confirmed_by_records=sorted(runtime_confirmed),
                killed_by_mutants=sorted(killed),
                survived_mutants=sorted(survived),
                evidence=evidence[:10],
            )
        )
        if survived:
            all_survived = not killed
            first = relevant_mutants[survived[0]]
            findings.append(
                Finding(
                    criterion=f"Dynamic coverage for behavior {behavior.behavior_id}",
                    status=Status.FAIL if all_survived else Status.WARNING,
                    severity=Severity.MAJOR if all_survived else Severity.MINOR,
                    confidence=1.0,
                    evidence=[
                        Evidence(
                            field="application_source",
                            quote=first.original,
                            file_path=first.file_path,
                            line_start=first.line_start,
                        )
                    ],
                    reasoning=(
                        f"{len(survived)} behavior-related mutant(s) survived the suite"
                        + (" and none were killed." if all_survived else ".")
                    ),
                    suggested_fix="Add a scenario and exact oracle that fails for the survived behavior mutation.",
                )
            )

    if not coverage:
        status = Status.SKIPPED
        confidence = 0.0
        warnings = ["The requirement contract contains no behaviors to confirm dynamically."]
    else:
        rank = {
            Status.FAIL: 4,
            Status.WARNING: 3,
            Status.UNKNOWN: 2,
            Status.PASS: 1,
            Status.SKIPPED: 0,
        }
        status = max((item.status for item in coverage), key=rank.__getitem__)
        confidence = sum(item.status not in {Status.UNKNOWN, Status.SKIPPED} for item in coverage) / len(coverage)
        warnings = []
        if confidence < 1.0:
            warnings.append("Some behaviors had no behavior-specific runtime or mutation evidence.")
    return DynamicSuiteCoverageOutput(
        agent="dynamic_suite_coverage",
        run_id=request.run_id,
        mode="full",
        project_id=request.contract.project_id,
        suite_key=request.suite_key,
        dimension="dynamic_behavior_coverage",
        status=status,
        confidence=confidence,
        findings=findings,
        warnings=warnings,
        behavior_coverage=coverage,
    )


def as_review(output: DynamicOracleOutput | DynamicSuiteCoverageOutput) -> AgentReview:
    return AgentReview(
        agent=output.agent,
        project_id=output.project_id,
        suite_key=output.suite_key,
        record_key=output.record_key,
        dimension=output.dimension,
        status=output.status,
        confidence=output.confidence,
        findings=output.findings,
    )
