from pathlib import Path

from test_evaluator.ingest import load_records
from test_evaluator.orchestrator import EvaluationConfig, _select_records, evaluate


ROOT = Path(__file__).parents[1]


def test_basic_evaluation_writes_manifest_and_resumes(tmp_path: Path) -> None:
    output = tmp_path / "basic"
    config = EvaluationConfig(
        input_path=ROOT / "e2edev_sample.csv",
        output_dir=output,
        limit=1,
    )

    first = evaluate(config)
    resumed = evaluate(EvaluationConfig(**{**config.__dict__, "resume": True}))

    assert first.run_id == resumed.run_id
    assert resumed.mode == "basic"
    assert resumed.run_health is not None
    assert resumed.run_health.cache_hits >= 7
    assert (output / "run_manifest.json").is_file()
    assert (output / "config.json").is_file()
    assert (output / "inventory.json").is_file()
    assert (output / "checkpoints" / "02_load_records.json").is_file()


def test_full_mode_loads_source_inventory_and_degrades_cleanly(tmp_path: Path, monkeypatch) -> None:
    # Keep this recovery-path test independent of whether the developer machine
    # happens to have Chrome/Selenium installed.
    monkeypatch.setattr(
        "test_evaluator.runner.runtime_environment_issues",
        lambda: ["browser unavailable for recovery-path test"],
    )
    run = evaluate(
        EvaluationConfig(
            input_path=None,
            e2edev_root=ROOT / "E2EDev",
            projects=("E2ESD_Bench_01",),
            output_dir=tmp_path / "full",
            mode="full",
            limit=1,
        )
    )

    assert run.mode == "full"
    assert run.inventories[0].source_root is not None
    assert any("runtime environment was unavailable" in warning for warning in run.runtime_warnings)
    assert run.tests[0].runtime is not None
    assert run.tests[0].runtime.status == "env_error"
    assert run.tests[0].runtime_trace is not None
    assert run.tests[0].runtime_trace.likely_failure_cause == "environment_issue"
    assert any(review.agent == "selector_grounding" for review in run.tests[0].reviews)
    assert (tmp_path / "full" / "projects" / "E2ESD_Bench_01" / "source_model.json").is_file()
    assert (tmp_path / "full" / "projects" / "E2ESD_Bench_01" / "selector_grounding.json").is_file()
    assert (tmp_path / "full" / "projects" / "E2ESD_Bench_01" / "runtime_results.json").is_file()
    assert (tmp_path / "full" / "projects" / "E2ESD_Bench_01" / "runtime_traces.json").is_file()
    assert list((tmp_path / "full" / "workspaces" / run.run_id).glob("*/features/test.feature"))
    assert run.run_health is not None
    assert run.run_health.state_counts["degraded"] >= 1


def test_requirement_and_record_key_filters_are_composable() -> None:
    records = load_records(ROOT / "e2edev_sample.csv")
    target = records[0]
    selected = _select_records(
        records,
        EvaluationConfig(
            requirements=(target.suite_key,),
            tests=(target.record_key,),
        ),
    )

    assert [record.record_key for record in selected] == [target.record_key]
