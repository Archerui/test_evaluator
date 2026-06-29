from pathlib import Path

import pytest

from test_evaluator.state_machine import OrchestratorStateStore, stable_hash


def test_state_store_resumes_matching_checkpoint(tmp_path: Path) -> None:
    config = {"mode": "basic", "input": "sample.csv"}
    first = OrchestratorStateStore(
        tmp_path,
        mode="basic",
        semantic_mode="offline",
        config=config,
    )
    input_hash = stable_hash({"records": 2})
    first.start("LOAD_RECORDS", input_hash)
    first.succeed("LOAD_RECORDS", {"records": [{"id": 1}]})

    resumed = OrchestratorStateStore(
        tmp_path,
        mode="basic",
        semantic_mode="offline",
        config=config,
        resume=True,
    )
    payload = resumed.cached_payload("LOAD_RECORDS", input_hash)

    assert resumed.run_id == first.run_id
    assert payload == {"records": [{"id": 1}]}
    assert resumed.health().cache_hits == 1


def test_state_store_rejects_changed_resume_config(tmp_path: Path) -> None:
    OrchestratorStateStore(
        tmp_path,
        mode="basic",
        semantic_mode="offline",
        config={"limit": 1},
    )

    with pytest.raises(ValueError, match="configuration changed"):
        OrchestratorStateStore(
            tmp_path,
            mode="basic",
            semantic_mode="offline",
            config={"limit": 2},
            resume=True,
        )


def test_item_checkpoint_reuses_matching_mutant_payload(tmp_path: Path) -> None:
    output = tmp_path / "run"
    store = OrchestratorStateStore(
        output,
        mode="full",
        semantic_mode="offline",
        config={"mode": "full"},
    )
    store.save_item_payload(
        "MUTATION_RUN",
        "mutant-1",
        "input-hash",
        {"result": {"mutant_id": "mutant-1", "status": "killed"}},
    )

    resumed = OrchestratorStateStore(
        output,
        mode="full",
        semantic_mode="offline",
        config={"mode": "full"},
        resume=True,
    )

    assert resumed.cached_item_payload("MUTATION_RUN", "mutant-1", "input-hash") == {
        "result": {"mutant_id": "mutant-1", "status": "killed"}
    }
    assert resumed.cached_item_payload("MUTATION_RUN", "mutant-1", "changed") is None
