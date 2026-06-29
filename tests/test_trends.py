from pathlib import Path

from test_evaluator.schemas import EvaluationRun, RunHealth
from test_evaluator.trends import update_history


def test_history_upserts_runs_and_computes_deltas(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"
    first = EvaluationRun(
        run_id="first",
        mode="full",
        semantic_mode="offline",
        tests=[],
        requirements=[],
        projects=[],
        run_health=RunHealth(total_runtime_seconds=10.0),
    )
    baseline = update_history(first, path)
    assert baseline.previous_run_id is None

    second = first.model_copy(
        update={
            "run_id": "second",
            "run_health": RunHealth(total_runtime_seconds=7.5),
        }
    )
    trend = update_history(second, path)

    assert trend.previous_run_id == "first"
    assert trend.deltas["runtime_seconds"] == -2.5
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2

    update_history(second, path)
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2
