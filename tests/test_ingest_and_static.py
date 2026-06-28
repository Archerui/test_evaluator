from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.static_verifier import extract_static_facts, static_review


DATASET = Path(__file__).parents[1] / "e2edev_sample.csv"


def test_loads_expected_sample_shape() -> None:
    records = load_records(DATASET)

    assert len(records) == 70
    assert len({record.project_id for record in records}) == 5
    assert len({record.suite_key for record in records}) == 24


def test_static_verifier_flags_speech_test_without_assertion() -> None:
    record = next(
        record
        for record in load_records(DATASET)
        if (record.project_id, record.requirement_id, record.test_id) == ("E2ESD_Bench_04", "5", "1")
    )

    facts = extract_static_facts(record)
    review = static_review(record, facts)

    assert facts.python_parseable is True
    assert facts.assertion_count == 0
    assert any(finding.criterion == "Step code contains an automatic assertion" for finding in review.findings)


def test_static_verifier_extracts_drag_test_actions() -> None:
    record = load_records(DATASET)[0]
    facts = extract_static_facts(record)

    assert facts.scenario_type == "Normal"
    assert "execute_script" in facts.actions
    assert facts.webdriver_wait_count > 0
