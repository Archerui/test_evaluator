"""Deterministic coordination and score calculation."""

from __future__ import annotations

from collections import Counter
from statistics import mean

from .ingest import TestRecord
from .schemas import (
    AgentReview,
    EvaluationRun,
    ProjectReport,
    RequirementReport,
    Severity,
    StaticFacts,
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

STATUS_SCORE: dict[Status, float | None] = {
    Status.PASS: 1.0,
    Status.WARNING: 0.5,
    Status.FAIL: 0.0,
    Status.UNKNOWN: None,
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


def coordinate_test(record: TestRecord, facts: StaticFacts, reviews: list[AgentReview]) -> TestReport:
    """Produce a score without allowing the coordinator to invent new evidence."""

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

    # A score based only on static robustness is not a credible overall quality
    # score. Keep it unavailable until at least half of the rubric is evidenced.
    test_score = (weighted_total / known_weight * 100.0) if known_weight >= 0.50 else None
    hard_gates: list[str] = []
    static = by_dimension.get("robustness")
    oracle = by_dimension.get("oracle_strength")
    if not facts.python_parseable:
        hard_gates.append("step_code_not_parseable")
    if not facts.scenario_present:
        hard_gates.append("scenario_missing")
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
        test_quality_score=test_score,
        mutation_readiness=(
            STATUS_SCORE[by_dimension["mutation_readiness"].status] * 100.0
            if "mutation_readiness" in by_dimension
            and STATUS_SCORE[by_dimension["mutation_readiness"].status] is not None
            else None
        ),
        confidence_coverage=known_weight,
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
) -> RequirementReport:
    """Combine suite evidence, test oracle scores, and diversity into a transparent score."""

    behavior_coverage = assessment.behavior_coverage if assessment else {}
    behavior_scores = [STATUS_SCORE[status] for status in behavior_coverage.values() if STATUS_SCORE[status] is not None]
    oracle_scores = [report.dimension_scores.get("oracle_strength") for report in test_reports]
    oracle_scores = [score for score in oracle_scores if score is not None]
    suite_score = STATUS_SCORE[assessment.review.status] if assessment else None

    components: list[tuple[float, float | None]] = [
        (0.50, mean(behavior_scores) if behavior_scores else None),
        (0.30, mean(oracle_scores) if oracle_scores else None),
        (0.20, suite_score),
    ]
    known_weight = sum(weight for weight, score in components if score is not None)
    adequacy = (
        sum(weight * score for weight, score in components if score is not None) / known_weight * 100.0
        if known_weight
        else None
    )
    distribution = Counter(record.scenario_type or "Unlabelled" for record in records)
    return RequirementReport(
        suite_key=suite_key,
        project_id=records[0].project_id,
        requirement_id=records[0].requirement_id,
        partial_suite=partial_suite,
        test_count=len(records),
        scenario_distribution=dict(sorted(distribution.items())),
        requirement_adequacy_score=adequacy,
        review=assessment.review if assessment else None,
        behavior_coverage=behavior_coverage,
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
        unknown_weight = sum(1.0 - report.confidence_coverage for report in tests)
        projects.append(
            ProjectReport(
                project_id=project_id,
                test_count=len(tests),
                requirement_count=len(requirements),
                average_test_quality_score=mean(quality_scores) if quality_scores else None,
                average_requirement_adequacy_score=mean(adequacy_scores) if adequacy_scores else None,
                risk_counts=dict(sorted(risk_counts.items())),
                unknown_rate=unknown_weight / len(tests) if tests else 0.0,
            )
        )
    return projects


def build_run(
    mode: str,
    model: str | None,
    tests: list[TestReport],
    requirements: list[RequirementReport],
    runtime_warnings: list[str] | None = None,
) -> EvaluationRun:
    return EvaluationRun(
        mode=mode,  # type: ignore[arg-type]
        model=model,
        tests=tests,
        requirements=requirements,
        projects=coordinate_projects(tests, requirements),
        runtime_warnings=runtime_warnings or [],
    )
