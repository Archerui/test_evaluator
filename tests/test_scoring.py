from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.scoring import coordinate_test, unknown_review
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
    assert report.dimension_scores["oracle_strength"] is None
