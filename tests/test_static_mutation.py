from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.scoring import DIMENSION_WEIGHTS, FULL_TEST_WEIGHTS
from test_evaluator.schemas import Behavior, RequirementContract
from test_evaluator.static_mutation import assess_static_mutation
from test_evaluator.static_verifier import extract_static_facts


DATASET = Path(__file__).parents[1] / "e2edev_sample.csv"


def test_static_mutation_readiness_is_not_a_score_dimension() -> None:
    assert "mutation_readiness" not in DIMENSION_WEIGHTS
    assert "mutation_readiness" not in FULL_TEST_WEIGHTS


def test_static_mutation_distinguishes_event_payload_from_dom_and_constant_proxies() -> None:
    records = [
        record
        for record in load_records(DATASET)
        if record.project_id == "E2ESD_Bench_01" and record.requirement_id == "1"
    ]
    contract = RequirementContract(
        project_id="E2ESD_Bench_01",
        requirement_id="1",
        suite_key="E2ESD_Bench_01::1",
        behaviors=[
            Behavior(
                behavior_id="B-event-payload",
                kind="normal",
                actor_actions=["The user initiates a browser event on an item."],
                expected_observables=["The browser event payload contains required values."],
                observability="browser_api",
            )
        ],
    )

    assessments = {
        record.test_id: assess_static_mutation(
            record,
            contract,
            extract_static_facts(record),
        )
        for record in records
    }

    assert assessments["1"].readiness_score == 100.0
    assert {item.prediction for item in assessments["1"].hypotheses} == {
        "likely_detected"
    }
    for test_id in ("2", "3", "4"):
        assert assessments[test_id].readiness_score == 0.0
        assert {item.prediction for item in assessments[test_id].hypotheses} == {
            "likely_survives"
        }
