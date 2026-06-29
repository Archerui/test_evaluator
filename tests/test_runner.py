import json
import subprocess
from pathlib import Path

from test_evaluator.runner import run_baseline_test
from test_evaluator.schemas import TestRunnerInput as RunnerInput, WorkspaceSpec


def _workspace(tmp_path: Path) -> WorkspaceSpec:
    features = tmp_path / "features"
    steps = features / "steps"
    artifacts = tmp_path / "artifacts"
    steps.mkdir(parents=True)
    artifacts.mkdir()
    feature_file = features / "test.feature"
    steps_file = steps / "steps.py"
    entry = tmp_path / "index.html"
    feature_file.write_text("Feature: Unit\n  Scenario: Unit\n    Given unit\n", encoding="utf-8")
    steps_file.write_text("# unit\n", encoding="utf-8")
    entry.write_text("<html></html>", encoding="utf-8")
    return WorkspaceSpec(
        record_key="Bench::1::1",
        workspace_root=str(tmp_path),
        app_root=str(tmp_path),
        feature_file=str(feature_file),
        steps_file=str(steps_file),
        entry_html=str(entry),
        artifacts_dir=str(artifacts),
    )


def test_runner_returns_environment_error_without_execution(tmp_path: Path) -> None:
    invoked = False

    def executor(*args, **kwargs):
        nonlocal invoked
        invoked = True
        raise AssertionError("executor should not run")

    result = run_baseline_test(
        RunnerInput(run_id="run", workspace=_workspace(tmp_path), timeout_seconds=1),
        executor=executor,
        environment_issues=["behave missing"],
    ).runtime

    assert result.status == "env_error"
    assert result.error_type == "env_error"
    assert result.stderr is not None
    assert invoked is False


def test_runner_parses_pass_and_assertion_failure(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)

    def passing(command, **kwargs):
        assert kwargs["env"]["TEST_EVALUATOR_COVERAGE_METHOD"] == "istanbul"
        assert kwargs["env"]["TEST_EVALUATOR_BROWSER_STUBS"] == "speech,clipboard"
        outfile = Path(command[command.index("--outfile") + 1])
        outfile.write_text("[]", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="1 passed", stderr="")

    passed = run_baseline_test(
        RunnerInput(
            run_id="run",
            workspace=workspace,
            timeout_seconds=1,
            collect_coverage=True,
            coverage_method="istanbul",
            browser_stubs=["speech", "clipboard"],
        ),
        executor=passing,
        environment_issues=[],
    ).runtime
    assert passed.status == "pass"
    assert passed.behave_json is not None

    def failing(command, **kwargs):
        outfile = Path(command[command.index("--outfile") + 1])
        outfile.write_text(
            json.dumps(
                [
                    {
                        "elements": [
                            {
                                "steps": [
                                    {
                                        "keyword": "Then",
                                        "name": "unit",
                                        "result": {
                                            "status": "failed",
                                            "error_message": "AssertionError: expected true",
                                        },
                                    }
                                ]
                            }
                        ]
                    }
                ]
            ),
            encoding="utf-8",
        )
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="AssertionError: expected true")

    failed = run_baseline_test(
        RunnerInput(run_id="run", workspace=workspace, timeout_seconds=1, retry_index=1),
        executor=failing,
        environment_issues=[],
    ).runtime
    assert failed.status == "fail"
    assert failed.error_type == "assertion_failure"
    assert failed.failed_step == "Then unit"
