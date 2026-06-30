from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.schemas import Behavior, RequirementContract, Status
from test_evaluator.static_verifier import extract_static_facts
from test_evaluator.suite_analysis import (
    analyze_static_behavior_coverage,
    analyze_suite_duplicates,
)


DATASET = Path(__file__).parents[1] / "e2edev_sample.csv"


def test_req1_data_variants_form_one_semantic_duplicate_cluster() -> None:
    records = [
        record
        for record in load_records(DATASET)
        if record.project_id == "E2ESD_Bench_01" and record.requirement_id == "1"
    ]
    facts = {record.record_key: extract_static_facts(record) for record in records}

    analysis = analyze_suite_duplicates(records, facts)

    semantic = [
        group for group in analysis.duplicate_groups if group.kind == "semantic_scenario"
    ]
    assert len(semantic) == 1
    assert semantic[0].record_keys == [
        "E2ESD_Bench_01::1::1",
        "E2ESD_Bench_01::1::2",
        "E2ESD_Bench_01::1::3",
    ]
    assert analysis.unique_contribution_records == ["E2ESD_Bench_01::1::4"]
    assert analysis.semantic_duplicate_ratio == 0.5


def test_behavior_coverage_separates_strong_data_variants_from_negative_proxy() -> None:
    records = [
        record
        for record in load_records(DATASET)
        if record.project_id == "E2ESD_Bench_01" and record.requirement_id == "1"
    ]
    contract = RequirementContract(
        project_id="E2ESD_Bench_01",
        requirement_id="1",
        behaviors=[
            Behavior(
                behavior_id="B1",
                kind="normal",
                actor_actions=["Initiate a drag event on a product."],
                expected_observables=["The drag payload captures title and price."],
                observability="browser_api",
            )
        ],
    )

    coverage = analyze_static_behavior_coverage(records, contract)[0]

    assert coverage.status is Status.PASS
    assert coverage.strong_by_records == [
        "E2ESD_Bench_01::1::1",
        "E2ESD_Bench_01::1::2",
        "E2ESD_Bench_01::1::3",
    ]
    assert coverage.weak_by_records == ["E2ESD_Bench_01::1::4"]
