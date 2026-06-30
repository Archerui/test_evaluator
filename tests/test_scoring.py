from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.scoring import (
    coordinate_requirement,
    coordinate_test,
    normalize_review_status,
    unknown_review,
)
from test_evaluator.schemas import (
    AgentReview,
    Evidence,
    Finding,
    Severity,
    Status,
    SuiteAssessment,
)
from test_evaluator.static_verifier import extract_static_facts, static_review


DATASET = Path(__file__).parents[1] / "e2edev_sample.csv"


def test_static_only_run_has_no_overconfident_global_score() -> None:
    record = load_records(DATASET)[0]
    facts = extract_static_facts(record)
    report = coordinate_test(
        record,
        facts,
        [
            static_review(record, facts),
            unknown_review("bdd_traceability", record.record_key, "spec_alignment"),
            unknown_review("step_code", record.record_key, "step_traceability"),
            unknown_review("oracle_critic", record.record_key, "oracle_strength"),
        ],
    )

    assert report.test_quality_score is None
    assert report.confidence_coverage == 0.10
    assert report.basic_confidence_coverage == 0.10
    assert report.dimension_scores["oracle_strength"] is None


def _finding(status: Status, severity: Severity, criterion: str = "criterion") -> Finding:
    return Finding(
        criterion=criterion,
        status=status,
        severity=severity,
        confidence=0.9,
        evidence=[Evidence(field="scenario", quote="Scenario evidence")],
        reasoning="Evidence-backed result.",
    )


def _review(
    agent: str,
    record_key: str,
    dimension: str,
    findings: list[Finding],
) -> AgentReview:
    return AgentReview(
        agent=agent,  # type: ignore[arg-type]
        record_key=record_key,
        dimension=dimension,  # type: ignore[arg-type]
        status=Status.PASS,
        confidence=0.9,
        findings=findings,
    )


def test_review_status_is_derived_from_finding_severity() -> None:
    record_key = "Bench::1::1"
    critical = _review(
        "oracle_critic",
        record_key,
        "oracle_strength",
        [_finding(Status.FAIL, Severity.CRITICAL)],
    )
    one_major = critical.model_copy(
        update={"findings": [_finding(Status.FAIL, Severity.MAJOR)]}
    )
    two_major = critical.model_copy(
        update={
            "findings": [
                _finding(Status.FAIL, Severity.MAJOR, "first"),
                _finding(Status.FAIL, Severity.MAJOR, "second"),
            ]
        }
    )

    assert normalize_review_status(critical).status is Status.FAIL
    assert normalize_review_status(one_major).status is Status.WARNING
    assert normalize_review_status(two_major).status is Status.FAIL


def test_minor_suggestion_does_not_lower_evidenced_semantic_dimension() -> None:
    review = _review(
        "bdd_traceability",
        "Bench::1::1",
        "spec_alignment",
        [
            _finding(Status.PASS, Severity.INFO, "core behavior aligns"),
            _finding(Status.WARNING, Severity.MINOR, "optional detail"),
        ],
    )

    assert normalize_review_status(review).status is Status.PASS


def test_basic_score_requires_seventy_percent_of_weighted_evidence() -> None:
    record = load_records(DATASET)[0]
    facts = extract_static_facts(record)
    report = coordinate_test(
        record,
        facts,
        [
            _review(
                "bdd_traceability",
                record.record_key,
                "spec_alignment",
                [_finding(Status.PASS, Severity.INFO)],
            ),
            _review(
                "step_code",
                record.record_key,
                "step_traceability",
                [_finding(Status.PASS, Severity.INFO)],
            ),
            unknown_review("oracle_critic", record.record_key, "oracle_strength"),
            static_review(record, facts),
        ],
    )

    assert report.basic_confidence_coverage == 0.65
    assert report.basic_test_quality_score is None


def test_requirement_score_requires_sixty_percent_of_weighted_evidence() -> None:
    record = load_records(DATASET)[0]
    facts = extract_static_facts(record)
    test_report = coordinate_test(
        record,
        facts,
        [
            unknown_review("bdd_traceability", record.record_key, "spec_alignment"),
            unknown_review("step_code", record.record_key, "step_traceability"),
            _review(
                "oracle_critic",
                record.record_key,
                "oracle_strength",
                [_finding(Status.PASS, Severity.INFO)],
            ),
            static_review(record, facts),
        ],
    )
    assessment = SuiteAssessment(
        review=AgentReview(
            agent="suite_coverage",
            suite_key=record.suite_key,
            dimension="suite_adequacy",
            status=Status.WARNING,
            confidence=0.8,
            findings=[],
        )
    )

    requirement = coordinate_requirement(
        record.suite_key,
        [record],
        [test_report],
        assessment,
        partial_suite=False,
    )

    assert requirement.basic_confidence_coverage == 0.30
    assert requirement.basic_requirement_adequacy_score is None
    assert requirement.review is not None
    assert requirement.review.status is Status.UNKNOWN
