"""Deterministic coordination and score calculation."""

from __future__ import annotations

from collections import Counter
from statistics import mean

from .ingest import TestRecord
from .schemas import (
    AgentReview,
    BehaviorCoverageItem,
    Evidence,
    EvaluationRun,
    Finding,
    MutationAnalysis,
    MutationPlan,
    MutationRunResult,
    ProjectReport,
    RequirementReport,
    RuntimeResult,
    RuntimeTraceOutput,
    CoverageReport,
    DynamicOracleOutput,
    DynamicSuiteCoverageOutput,
    SelectorGroundingOutput,
    Severity,
    StaticFacts,
    SuiteStaticAnalysis,
    StabilityReport,
    Status,
    SuiteAssessment,
    TestReport,
)


DIMENSION_WEIGHTS = {
    "spec_alignment": 0.30,
    "step_traceability": 0.25,
    "oracle_strength": 0.35,
    "robustness": 0.10,
}

BASIC_TEST_MIN_KNOWN_WEIGHT = 0.70
BASIC_REQUIREMENT_MIN_KNOWN_WEIGHT = 0.60

FULL_TEST_WEIGHTS = {
    "spec_alignment": 0.15,
    "step_traceability": 0.15,
    "oracle_strength": 0.20,
    "runtime_result": 0.20,
    "mutation_effectiveness": 0.25,
    "robustness": 0.05,
}

FULL_REQUIREMENT_WEIGHTS = {
    "behavior_coverage": 0.25,
    "source_grounding": 0.15,
    "runtime_pass_rate": 0.20,
    "oracle_adequacy": 0.15,
    "mutation_score": 0.20,
    "scenario_diversity": 0.05,
}

STATUS_SCORE: dict[Status, float | None] = {
    Status.PASS: 1.0,
    Status.WARNING: 0.5,
    Status.FAIL: 0.0,
    Status.UNKNOWN: None,
    Status.SKIPPED: None,
}

RUNTIME_SCORE: dict[str, float | None] = {
    "pass": 1.0,
    "fail": 0.0,
    "timeout": 0.0,
    "env_error": None,
    "skipped": None,
}


def unknown_review(agent: str, record_key: str, dimension: str) -> AgentReview:
    return AgentReview(
        agent=agent,  # type: ignore[arg-type]
        record_key=record_key,
        dimension=dimension,  # type: ignore[arg-type]
        status=Status.UNKNOWN,
        confidence=0.0,
        findings=[],
    )


def normalize_review_status(review: AgentReview) -> AgentReview:
    """Derive a consistent envelope status from evidence-validated findings."""

    if not review.findings:
        if review.agent == "static_verifier" and review.status is Status.PASS:
            return review
        if review.status in {Status.UNKNOWN, Status.SKIPPED}:
            return review.model_copy(update={"confidence": 0.0})
        return review.model_copy(update={"status": Status.UNKNOWN, "confidence": 0.0})

    critical_failures = [
        finding
        for finding in review.findings
        if finding.status is Status.FAIL and finding.severity is Severity.CRITICAL
    ]
    major_failures = [
        finding
        for finding in review.findings
        if finding.status is Status.FAIL and finding.severity is Severity.MAJOR
    ]
    non_unknown = [finding for finding in review.findings if finding.status is not Status.UNKNOWN]
    unknown = [finding for finding in review.findings if finding.status is Status.UNKNOWN]
    high_severity_warnings = [
        finding
        for finding in non_unknown
        if finding.status is Status.WARNING
        and finding.severity in {Severity.MAJOR, Severity.CRITICAL}
    ]
    high_severity_unknowns = [
        finding
        for finding in unknown
        if finding.severity in {Severity.MAJOR, Severity.CRITICAL}
    ]
    minor_failures = [
        finding
        for finding in non_unknown
        if finding.status is Status.FAIL and finding.severity is Severity.MINOR
    ]
    pass_findings = [finding for finding in non_unknown if finding.status is Status.PASS]
    if critical_failures or len(major_failures) >= 2:
        status = Status.FAIL
    elif major_failures or minor_failures or high_severity_warnings or high_severity_unknowns:
        status = Status.WARNING
    elif pass_findings:
        # INFO/MINOR suggestions do not halve an otherwise evidenced semantic
        # dimension. They remain visible findings and still contribute to risk.
        status = Status.PASS
    elif non_unknown:
        status = Status.WARNING
    else:
        status = Status.UNKNOWN
    confidence = review.confidence if status is not Status.UNKNOWN else 0.0
    return review.model_copy(update={"status": status, "confidence": confidence})


def coordinate_test(record: TestRecord, facts: StaticFacts, reviews: list[AgentReview]) -> TestReport:
    """Produce a score without allowing the coordinator to invent new evidence."""

    reviews = [normalize_review_status(review) for review in reviews]
    by_dimension = {review.dimension: review for review in reviews}
    dimension_scores: dict[str, float | None] = {}
    known_weight = 0.0
    weighted_total = 0.0
    for dimension, weight in DIMENSION_WEIGHTS.items():
        score = STATUS_SCORE[by_dimension[dimension].status] if dimension in by_dimension else None
        dimension_scores[dimension] = score
        if score is not None:
            known_weight += weight
            weighted_total += score * weight

    test_score = (
        weighted_total / known_weight * 100.0
        if known_weight >= BASIC_TEST_MIN_KNOWN_WEIGHT
        else None
    )
    hard_gates: list[str] = []
    static = by_dimension.get("robustness")
    oracle = by_dimension.get("oracle_strength")
    if not facts.python_parseable:
        hard_gates.append("step_code_not_parseable")
    if not facts.scenario_present:
        hard_gates.append("scenario_missing")
    if facts.missing_step_definitions:
        hard_gates.append("missing_step_implementation")
    if oracle and any(
        finding.status is Status.FAIL and finding.severity is Severity.CRITICAL
        for finding in oracle.findings
    ):
        hard_gates.append("critical_oracle_gap")

    severity_counts = Counter(
        finding.severity.value
        for review in reviews
        if review.agent != "mutation_hypothesis"
        for finding in review.findings
        if finding.status in {Status.FAIL, Status.WARNING}
    )
    if hard_gates:
        risk = "critical"
    elif severity_counts[Severity.MAJOR.value] or any(review.status is Status.FAIL for review in reviews):
        risk = "major"
    elif severity_counts[Severity.MINOR.value] or any(review.status is Status.WARNING for review in reviews):
        risk = "medium"
    elif all(review.status is Status.UNKNOWN for review in reviews):
        risk = "unknown"
    else:
        risk = "low"

    return TestReport(
        record_key=record.record_key,
        project_id=record.project_id,
        requirement_id=record.requirement_id,
        test_id=record.test_id,
        scenario_type=record.scenario_type,
        evaluation_mode="basic",
        test_quality_score=test_score,
        basic_test_quality_score=test_score,
        mutation_readiness=(
            STATUS_SCORE[by_dimension["mutation_readiness"].status] * 100.0
            if "mutation_readiness" in by_dimension
            and STATUS_SCORE[by_dimension["mutation_readiness"].status] is not None
            else None
        ),
        confidence_coverage=known_weight,
        basic_confidence_coverage=known_weight,
        risk=risk,
        hard_gates=hard_gates,
        dimension_scores=dimension_scores,
        static_facts=facts,
        reviews=reviews,
    )


def coordinate_requirement(
    suite_key: str,
    records: list[TestRecord],
    test_reports: list[TestReport],
    assessment: SuiteAssessment | None,
    partial_suite: bool,
    suite_static_analysis: SuiteStaticAnalysis | None = None,
    static_behavior_coverage: list[BehaviorCoverageItem] | None = None,
) -> RequirementReport:
    """Combine suite evidence, test oracle scores, and diversity into a transparent score."""

    normalized_assessment = None
    if assessment:
        normalized_assessment = assessment.model_copy(
            update={"review": normalize_review_status(assessment.review)}
        )
    behavior_coverage = normalized_assessment.behavior_coverage if normalized_assessment else {}
    behavior_scores = [STATUS_SCORE[status] for status in behavior_coverage.values() if STATUS_SCORE[status] is not None]
    oracle_scores = [report.dimension_scores.get("oracle_strength") for report in test_reports]
    oracle_scores = [score for score in oracle_scores if score is not None]
    suite_score = STATUS_SCORE[normalized_assessment.review.status] if normalized_assessment else None

    components: list[tuple[float, float | None]] = [
        (0.50, mean(behavior_scores) if behavior_scores else None),
        (0.30, mean(oracle_scores) if oracle_scores else None),
        (0.20, suite_score),
    ]
    known_weight = sum(weight for weight, score in components if score is not None)
    adequacy = (
        sum(weight * score for weight, score in components if score is not None) / known_weight * 100.0
        if known_weight >= BASIC_REQUIREMENT_MIN_KNOWN_WEIGHT
        else None
    )
    distribution = Counter(record.scenario_type or "Unlabelled" for record in records)
    return RequirementReport(
        suite_key=suite_key,
        project_id=records[0].project_id,
        requirement_id=records[0].requirement_id,
        evaluation_mode="basic",
        partial_suite=partial_suite,
        test_count=len(records),
        scenario_distribution=dict(sorted(distribution.items())),
        requirement_adequacy_score=adequacy,
        basic_requirement_adequacy_score=adequacy,
        basic_confidence_coverage=known_weight,
        review=normalized_assessment.review if normalized_assessment else None,
        behavior_coverage=behavior_coverage,
        behavior_coverage_details=static_behavior_coverage or [],
        suite_static_analysis=suite_static_analysis or SuiteStaticAnalysis(),
    )


def coordinate_projects(test_reports: list[TestReport], requirement_reports: list[RequirementReport]) -> list[ProjectReport]:
    project_ids = sorted({report.project_id for report in test_reports})
    projects: list[ProjectReport] = []
    for project_id in project_ids:
        tests = [report for report in test_reports if report.project_id == project_id]
        requirements = [report for report in requirement_reports if report.project_id == project_id]
        quality_scores = [report.test_quality_score for report in tests if report.test_quality_score is not None]
        adequacy_scores = [
            report.requirement_adequacy_score
            for report in requirements
            if report.requirement_adequacy_score is not None
        ]
        risk_counts = Counter(report.risk for report in tests)
        unknown_weight = sum(1.0 - report.basic_confidence_coverage for report in tests)
        projects.append(
            ProjectReport(
                project_id=project_id,
                evaluation_mode=tests[0].evaluation_mode if tests else "basic",
                test_count=len(tests),
                requirement_count=len(requirements),
                average_test_quality_score=mean(quality_scores) if quality_scores else None,
                average_basic_test_quality_score=mean(quality_scores) if quality_scores else None,
                average_requirement_adequacy_score=mean(adequacy_scores) if adequacy_scores else None,
                risk_counts=dict(sorted(risk_counts.items())),
                unknown_rate=unknown_weight / len(tests) if tests else 0.0,
            )
        )
    return projects


def attach_runtime_results(run: EvaluationRun, runtime_by_record: dict[str, RuntimeResult]) -> EvaluationRun:
    """Attach baseline evidence without pretending partial full-mode evidence is a final full score."""

    for report in run.tests:
        runtime = runtime_by_record.get(report.record_key)
        if runtime is None:
            continue
        report.runtime = runtime
        report.dimension_scores["runtime_result"] = RUNTIME_SCORE[runtime.status]
        if runtime.status == "fail":
            if "baseline_test_failed" not in report.hard_gates:
                report.hard_gates.append("baseline_test_failed")
            if report.risk not in {"critical"}:
                report.risk = "major"
        elif runtime.status == "timeout":
            if "baseline_test_timeout" not in report.hard_gates:
                report.hard_gates.append("baseline_test_timeout")
            if report.risk not in {"critical"}:
                report.risk = "major"

    tests_by_suite: dict[str, list[TestReport]] = {}
    for report in run.tests:
        suite_key = f"{report.project_id}::{report.requirement_id}"
        tests_by_suite.setdefault(suite_key, []).append(report)
    for requirement in run.requirements:
        executed = [
            report.runtime
            for report in tests_by_suite.get(requirement.suite_key, [])
            if report.runtime and report.runtime.status in {"pass", "fail", "timeout"}
        ]
        requirement.runtime_pass_rate = (
            sum(result.status == "pass" for result in executed) / len(executed)
            if executed
            else None
        )

    for project in run.projects:
        executed = [
            report.runtime
            for report in run.tests
            if report.project_id == project.project_id
            and report.runtime
            and report.runtime.status in {"pass", "fail", "timeout"}
        ]
        project.runtime_pass_rate = (
            sum(result.status == "pass" for result in executed) / len(executed)
            if executed
            else None
        )
        project.risk_counts = dict(
            sorted(Counter(report.risk for report in run.tests if report.project_id == project.project_id).items())
        )
    return run


def attach_stability_results(
    run: EvaluationRun,
    stability_by_record: dict[str, StabilityReport],
) -> EvaluationRun:
    for report in run.tests:
        stability = stability_by_record.get(report.record_key)
        if stability is None:
            continue
        report.stability = stability
        findings: list[Finding] = []
        if stability.flaky:
            outcomes = ", ".join(
                f"run {attempt.run_index + 1}={attempt.status}" for attempt in stability.attempts
            )
            findings.append(
                Finding(
                    criterion="Repeated baseline runs are stable",
                    status=Status.FAIL,
                    severity=Severity.MAJOR,
                    confidence=1.0,
                    evidence=[Evidence(field="runtime.stability", quote=outcomes)],
                    reasoning="The same unchanged test produced both passing and non-passing behavioral outcomes.",
                    suggested_fix="Remove nondeterministic waits, external dependencies, or shared state and repeat the stability run.",
                )
            )
            if "flaky_runtime" not in report.hard_gates:
                report.hard_gates.append("flaky_runtime")
            if report.risk != "critical":
                report.risk = "major"
        report.reviews = [item for item in report.reviews if item.agent != "stability_analyzer"]
        report.reviews.append(
            AgentReview(
                agent="stability_analyzer",
                project_id=report.project_id,
                record_key=report.record_key,
                dimension="stability",
                status=stability.status,
                confidence=1.0 if stability.completed_runs >= 2 else 0.5,
                findings=findings,
            )
        )
    for requirement in run.requirements:
        requirement.flaky_test_count = sum(
            bool(report.stability and report.stability.flaky)
            for report in run.tests
            if report.project_id == requirement.project_id
            and report.requirement_id == requirement.requirement_id
        )
    for project in run.projects:
        project.flaky_test_count = sum(
            bool(report.stability and report.stability.flaky)
            for report in run.tests
            if report.project_id == project.project_id
        )
    run.stability_reports = stability_by_record
    return run


def attach_source_grounding(
    run: EvaluationRun,
    grounding_by_record: dict[str, SelectorGroundingOutput],
) -> EvaluationRun:
    """Attach source-grounding reviews while preserving the basic score boundary."""

    for report in run.tests:
        output = grounding_by_record.get(report.record_key)
        if output is None:
            continue
        review = AgentReview(
            agent="selector_grounding",
            record_key=report.record_key,
            project_id=report.project_id,
            dimension="source_grounding",
            status=output.status,
            confidence=output.confidence,
            findings=output.findings,
        )
        report.reviews = [item for item in report.reviews if item.agent != "selector_grounding"]
        report.reviews.append(review)
        report.dimension_scores["source_grounding"] = STATUS_SCORE[output.status]
        if output.status is Status.FAIL and report.risk != "critical":
            report.risk = "major"
        elif output.status is Status.WARNING and report.risk in {"low", "unknown"}:
            report.risk = "medium"

    for project in run.projects:
        project.risk_counts = dict(
            sorted(Counter(report.risk for report in run.tests if report.project_id == project.project_id).items())
        )
    return run


def attach_mutation_results(
    run: EvaluationRun,
    plans_by_project: dict[str, MutationPlan],
    results_by_project: dict[str, list[MutationRunResult]],
    analyses_by_project: dict[str, MutationAnalysis],
) -> EvaluationRun:
    """Attach valid mutation outcomes at test, requirement, and project levels."""

    for report in run.tests:
        results = results_by_project.get(report.project_id, [])
        exercised = [
            result
            for result in results
            if report.record_key in result.killed_by_record_keys
            or report.record_key in result.survived_record_keys
        ]
        if not exercised:
            report.dimension_scores["mutation_effectiveness"] = None
            continue
        killed = sum(report.record_key in result.killed_by_record_keys for result in exercised)
        score = killed / len(exercised) * 100.0
        report.mutation_score = score
        report.dimension_scores["mutation_effectiveness"] = score / 100.0
        status = Status.PASS if score >= 80.0 else Status.WARNING if score > 0 else Status.FAIL
        mutant_by_id = {
            mutant.mutant_id: mutant
            for mutant in plans_by_project.get(report.project_id, MutationPlan(project_id=report.project_id)).mutants
        }
        survived = [
            mutant_by_id[result.mutant_id]
            for result in exercised
            if report.record_key in result.survived_record_keys and result.mutant_id in mutant_by_id
        ]
        findings = [
            Finding(
                criterion=f"Test kills mutant {mutant.mutant_id}",
                status=Status.FAIL,
                severity=Severity.MAJOR,
                confidence=1.0,
                evidence=[
                    Evidence(
                        field="application_source",
                        quote=mutant.original,
                        file_path=mutant.file_path,
                        line_start=mutant.line_start,
                    )
                ],
                reasoning=f"The test passed after the {mutant.operator} mutation, so this fault was not detected.",
                suggested_fix="Strengthen the observable assertion that should distinguish the original behavior from this mutant.",
            )
            for mutant in survived[:5]
        ]
        report.reviews = [item for item in report.reviews if item.agent != "mutation_runner"]
        report.reviews.append(
            AgentReview(
                agent="mutation_runner",
                record_key=report.record_key,
                project_id=report.project_id,
                dimension="mutation_effectiveness",
                status=status,
                confidence=1.0,
                findings=findings,
            )
        )
        if score == 0.0:
            if "mutation_score_zero" not in report.hard_gates:
                report.hard_gates.append("mutation_score_zero")
            if report.risk != "critical":
                report.risk = "major"
        elif status is Status.WARNING and report.risk in {"low", "unknown"}:
            report.risk = "medium"

    for requirement in run.requirements:
        record_keys = {
            report.record_key
            for report in run.tests
            if report.project_id == requirement.project_id
            and report.requirement_id == requirement.requirement_id
        }
        results = results_by_project.get(requirement.project_id, [])
        exercised = [
            result
            for result in results
            if record_keys.intersection(result.killed_by_record_keys + result.survived_record_keys)
        ]
        if exercised:
            killed = sum(bool(record_keys.intersection(result.killed_by_record_keys)) for result in exercised)
            requirement.mutation_score = killed / len(exercised) * 100.0

    for project in run.projects:
        analysis = analyses_by_project.get(project.project_id)
        project.mutation_score = analysis.mutation_score if analysis else None
        project.risk_counts = dict(
            sorted(Counter(report.risk for report in run.tests if report.project_id == project.project_id).items())
        )
    return run


def attach_runtime_traces(
    run: EvaluationRun,
    outputs_by_record: dict[str, RuntimeTraceOutput],
) -> EvaluationRun:
    for report in run.tests:
        output = outputs_by_record.get(report.record_key)
        if output is None:
            continue
        report.runtime_trace = output.runtime_trace
        report.reviews = [item for item in report.reviews if item.agent != "runtime_trace"]
        report.reviews.append(
            AgentReview(
                agent="runtime_trace",
                record_key=report.record_key,
                project_id=report.project_id,
                dimension="runtime_result",
                status=output.status,
                confidence=output.confidence,
                findings=output.findings,
            )
        )
    run.runtime_traces = {
        record_key: output.runtime_trace for record_key, output in outputs_by_record.items()
    }
    return run


def attach_coverage_results(
    run: EvaluationRun,
    reports_by_record: dict[str, CoverageReport],
) -> EvaluationRun:
    for report in run.tests:
        coverage = reports_by_record.get(report.record_key)
        if coverage is None:
            continue
        report.coverage = coverage
        values = [item.statement_coverage for item in coverage.files if item.statement_coverage is not None]
        report.dimension_scores["coverage"] = mean(values) / 100.0 if values else None
        report.reviews = [item for item in report.reviews if item.agent != "coverage"]
        report.reviews.append(
            AgentReview(
                agent="coverage",
                record_key=report.record_key,
                project_id=report.project_id,
                dimension="coverage",
                status=coverage.status,
                confidence=1.0 if values else 0.0,
                findings=[],
            )
        )
    run.coverage_reports = reports_by_record
    return run


def attach_dynamic_evidence(
    run: EvaluationRun,
    test_outputs: dict[str, DynamicOracleOutput],
    suite_outputs: dict[str, DynamicSuiteCoverageOutput],
) -> EvaluationRun:
    """Attach post-runtime reviews without adding a second scoring weight."""

    for report in run.tests:
        output = test_outputs.get(report.record_key)
        if output is None:
            continue
        report.reviews = [item for item in report.reviews if item.agent != "dynamic_oracle"]
        report.reviews.append(
            AgentReview(
                agent="dynamic_oracle",
                project_id=report.project_id,
                suite_key=output.suite_key,
                record_key=report.record_key,
                dimension="dynamic_oracle_evidence",
                status=output.status,
                confidence=output.confidence,
                findings=output.findings,
            )
        )

    for requirement in run.requirements:
        output = suite_outputs.get(requirement.suite_key)
        if output is None:
            continue
        requirement.dynamic_behavior_coverage = output.behavior_coverage
        requirement.dynamic_review = AgentReview(
            agent="dynamic_suite_coverage",
            project_id=requirement.project_id,
            suite_key=requirement.suite_key,
            dimension="dynamic_behavior_coverage",
            status=output.status,
            confidence=output.confidence,
            findings=output.findings,
        )
    return run


def _weighted_score(
    values: dict[str, float | None],
    weights: dict[str, float],
    *,
    minimum_known_weight: float = 0.50,
) -> tuple[float | None, float]:
    known_weight = sum(weights[name] for name, value in values.items() if value is not None)
    if known_weight < minimum_known_weight:
        return None, known_weight
    total = sum(weights[name] * value for name, value in values.items() if value is not None)
    return total / known_weight * 100.0, known_weight


def coordinate_full_scores(run: EvaluationRun) -> EvaluationRun:
    """Calculate proposal-defined full scores after all available evidence is attached."""

    cap_by_gate = {
        "step_code_not_parseable": 20.0,
        "scenario_missing": 20.0,
        "missing_step_implementation": 40.0,
        "critical_oracle_gap": 50.0,
        "baseline_test_failed": 60.0,
        "baseline_test_timeout": 60.0,
        "mutation_score_zero": 65.0,
        "flaky_runtime": 75.0,
    }
    for report in run.tests:
        values = {
            name: report.dimension_scores.get(name)
            for name in FULL_TEST_WEIGHTS
        }
        score, known_weight = _weighted_score(values, FULL_TEST_WEIGHTS)
        if score is not None:
            caps = [cap_by_gate[gate] for gate in report.hard_gates if gate in cap_by_gate]
            if caps:
                score = min(score, min(caps))
        report.full_test_quality_score = score
        report.test_quality_score = score
        report.confidence_coverage = known_weight
        report.full_confidence_coverage = known_weight

    tests_by_suite: dict[str, list[TestReport]] = {}
    for report in run.tests:
        tests_by_suite.setdefault(f"{report.project_id}::{report.requirement_id}", []).append(report)
    for requirement in run.requirements:
        tests = tests_by_suite.get(requirement.suite_key, [])
        behavior_values = [
            STATUS_SCORE[status]
            for status in requirement.behavior_coverage.values()
            if STATUS_SCORE[status] is not None
        ]
        source_values = [
            report.dimension_scores.get("source_grounding")
            for report in tests
            if report.dimension_scores.get("source_grounding") is not None
        ]
        oracle_values = [
            report.dimension_scores.get("oracle_strength")
            for report in tests
            if report.dimension_scores.get("oracle_strength") is not None
        ]
        scenario_kinds = {
            kind.casefold()
            for kind, count in requirement.scenario_distribution.items()
            if count > 0 and kind != "Unlabelled"
        }
        diversity = min(len(scenario_kinds) / 3.0, 1.0) if scenario_kinds else None
        values = {
            "behavior_coverage": mean(behavior_values) if behavior_values else None,
            "source_grounding": mean(source_values) if source_values else None,
            "runtime_pass_rate": requirement.runtime_pass_rate,
            "oracle_adequacy": mean(oracle_values) if oracle_values else None,
            "mutation_score": requirement.mutation_score / 100.0 if requirement.mutation_score is not None else None,
            "scenario_diversity": diversity,
        }
        score, known_weight = _weighted_score(values, FULL_REQUIREMENT_WEIGHTS)
        requirement.full_requirement_adequacy_score = score
        requirement.requirement_adequacy_score = score
        requirement.full_confidence_coverage = known_weight

    for project in run.projects:
        tests = [report for report in run.tests if report.project_id == project.project_id]
        requirements = [
            report for report in run.requirements if report.project_id == project.project_id
        ]
        full_scores = [
            report.full_test_quality_score
            for report in tests
            if report.full_test_quality_score is not None
        ]
        basic_scores = [
            report.basic_test_quality_score
            for report in tests
            if report.basic_test_quality_score is not None
        ]
        requirement_scores = [
            report.full_requirement_adequacy_score
            for report in requirements
            if report.full_requirement_adequacy_score is not None
        ]
        project.average_full_test_quality_score = mean(full_scores) if full_scores else None
        project.average_basic_test_quality_score = mean(basic_scores) if basic_scores else None
        project.average_test_quality_score = project.average_full_test_quality_score
        project.average_requirement_adequacy_score = (
            mean(requirement_scores) if requirement_scores else None
        )
        project.unknown_rate = (
            sum(1.0 - report.confidence_coverage for report in tests) / len(tests)
            if tests
            else 0.0
        )
    return run


def build_run(
    mode: str,
    semantic_mode: str,
    model: str | None,
    tests: list[TestReport],
    requirements: list[RequirementReport],
    runtime_warnings: list[str] | None = None,
    *,
    run_id: str = "",
    config: dict[str, object] | None = None,
    inventories: list | None = None,
    run_health=None,
) -> EvaluationRun:
    for report in tests:
        report.evaluation_mode = mode  # type: ignore[assignment]
    for report in requirements:
        report.evaluation_mode = mode  # type: ignore[assignment]
    projects = coordinate_projects(tests, requirements)
    for project in projects:
        project.evaluation_mode = mode  # type: ignore[assignment]
    return EvaluationRun(
        run_id=run_id,
        mode=mode,  # type: ignore[arg-type]
        semantic_mode=semantic_mode,  # type: ignore[arg-type]
        model=model,
        config=config or {},
        tests=tests,
        requirements=requirements,
        projects=projects,
        inventories=inventories or [],
        run_health=run_health,
        runtime_warnings=runtime_warnings or [],
    )
