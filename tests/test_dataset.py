from pathlib import Path

from test_evaluator.dataset import (
    discover_project_inventories,
    load_inventory_records,
    load_inventory_semantic_context,
)
from test_evaluator.ingest import load_records


ROOT = Path(__file__).parents[1]
E2EDEV = ROOT / "E2EDev"


def test_discovers_full_e2edev_repository() -> None:
    inventories = discover_project_inventories(E2EDEV)

    assert len(inventories) == 46
    assert {item.project_id for item in inventories} >= {"E2ESD_Bench_01", "E2ESD_Bench_59"}


def test_loads_project_json_into_normalized_records() -> None:
    inventories = discover_project_inventories(E2EDEV, ["E2ESD_Bench_01"])
    records = load_inventory_records(inventories)

    assert len(records) == 12
    assert len({record.suite_key for record in records}) == 3
    assert records[0].record_key == "E2ESD_Bench_01::1::1"
    assert records[0].input_origin == "requirment_with_tests"
    assert records[0].source_root is not None


def test_load_records_dispatches_project_json() -> None:
    path = E2EDEV / "E2EDev_data" / "E2ESD_Bench_01" / "requirment_with_tests.json"

    records = load_records(path)

    assert len(records) == 12
    assert records[0].project_id == "E2ESD_Bench_01"


def test_loads_source_semantic_context_including_fenced_json() -> None:
    inventory = discover_project_inventories(E2EDEV, ["E2ESD_Bench_01"])[0]

    requirements, analysis, warnings = load_inventory_semantic_context(inventory)

    assert len(requirements) == 7
    assert analysis["LogicComplexityLevel"] == "state management"
    assert warnings == []
