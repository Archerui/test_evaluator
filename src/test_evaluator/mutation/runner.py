"""Apply one mutant to isolated test workspaces and execute impacted tests."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import shutil
from typing import Callable

from ..runner import run_baseline_test
from ..schemas import (
    ArtifactRef,
    MutationRunResult,
    MutationRunnerInput,
    MutationRunnerOutput,
    Status,
    TestRunnerInput,
    TestRunnerOutput,
    WorkspaceSpec,
)


MutationTestExecutor = Callable[[TestRunnerInput], TestRunnerOutput]


def _mutate_file(path: Path, line_start: int | None, original: str, mutated: str) -> str:
    if line_start is None or line_start <= 0:
        raise ValueError("Mutant has no valid line_start")
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if line_start > len(lines):
        raise ValueError(f"Mutation line {line_start} is outside {path}")
    existing = lines[line_start - 1].rstrip("\r\n")
    if existing != original:
        raise ValueError(
            f"Mutation source mismatch at {path}:{line_start}; expected {original!r}, found {existing!r}"
        )
    ending = lines[line_start - 1][len(existing):]
    lines[line_start - 1] = mutated + ending
    path.write_text("".join(lines), encoding="utf-8")
    return text


def _target(workspace: WorkspaceSpec, file_path: str, base_workspace_root: Path) -> Path:
    workspace_root = Path(workspace.workspace_root).resolve()
    try:
        workspace_root.relative_to(base_workspace_root)
    except ValueError as error:
        raise ValueError(f"Workspace escapes the mutation run root: {workspace_root}") from error
    app_root = Path(workspace.app_root).resolve()
    target = (app_root / file_path).resolve()
    try:
        target.relative_to(app_root)
    except ValueError as error:
        raise ValueError(f"Mutant target escapes application root: {file_path}") from error
    if not target.is_file():
        raise FileNotFoundError(f"Mutant target does not exist in workspace: {target}")
    return target


def _isolated_workspace(
    workspace: WorkspaceSpec,
    mutant_id: str,
    base_workspace_root: Path,
    artifacts_dir: Path,
) -> WorkspaceSpec:
    """Clone only app/features and repoint materialized entry paths to the clone."""

    original_root = Path(workspace.workspace_root).resolve()
    try:
        original_root.relative_to(base_workspace_root)
    except ValueError as error:
        raise ValueError(f"Workspace escapes the mutation run root: {original_root}") from error
    original_app = Path(workspace.app_root).resolve()
    original_features = Path(workspace.feature_file).resolve().parent
    entry_relative = Path(workspace.entry_html).resolve().relative_to(original_app)
    feature_relative = Path(workspace.feature_file).resolve().relative_to(original_features)
    steps_relative = Path(workspace.steps_file).resolve().relative_to(original_features)

    mutant_key = sha256(mutant_id.encode("utf-8")).hexdigest()[:16]
    record_key = sha256(workspace.record_key.encode("utf-8")).hexdigest()[:16]
    clone_root = base_workspace_root / ".mutation_workspaces" / mutant_key / record_key
    if clone_root.exists():
        shutil.rmtree(clone_root)
    clone_root.parent.mkdir(parents=True, exist_ok=True)
    clone_app = clone_root / "app"
    clone_features = clone_root / "features"
    try:
        shutil.copytree(original_app, clone_app)
        shutil.copytree(
            original_features,
            clone_features,
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
        clone_entry = clone_app / entry_relative
        clone_steps = clone_features / steps_relative
        step_code = clone_steps.read_text(encoding="utf-8")
        replacements = (
            (Path(workspace.entry_html).resolve().as_uri(), clone_entry.resolve().as_uri()),
            (str(Path(workspace.entry_html).resolve()), str(clone_entry.resolve())),
            (str(original_app), str(clone_app.resolve())),
        )
        for original, replacement in replacements:
            step_code = step_code.replace(original, replacement)
        clone_steps.write_text(step_code, encoding="utf-8")
    except Exception:
        shutil.rmtree(clone_root, ignore_errors=True)
        raise
    return workspace.model_copy(
        update={
            "workspace_root": str(clone_root),
            "app_root": str(clone_app),
            "feature_file": str(clone_features / feature_relative),
            "steps_file": str(clone_steps),
            "entry_html": str(clone_entry),
            "artifacts_dir": str(artifacts_dir),
        }
    )


def _cleanup_isolated_workspace(workspace_root: str, base_workspace_root: Path) -> None:
    root = Path(workspace_root)
    shutil.rmtree(root, ignore_errors=True)
    mutation_root = base_workspace_root / ".mutation_workspaces"
    for directory in (root.parent, mutation_root):
        try:
            directory.rmdir()
        except OSError:
            pass


def _runtime_artifacts(output: TestRunnerOutput) -> list[ArtifactRef]:
    return list(output.artifacts)


def run_mutant(
    request: MutationRunnerInput,
    *,
    workspaces: dict[str, WorkspaceSpec],
    executor: MutationTestExecutor = run_baseline_test,
) -> MutationRunnerOutput:
    """Run every selected test against a private, disposable workspace clone."""

    mutant = request.mutant
    if not request.tests_to_run:
        result = MutationRunResult(
            mutant_id=mutant.mutant_id,
            status="skipped",
            error_summary="No baseline-passing impacted tests were available",
        )
        return MutationRunnerOutput(
            agent="mutation_runner",
            run_id=request.run_id,
            mode="full",
            project_id=mutant.project_id,
            status=Status.SKIPPED,
            confidence=1.0,
            result=result,
        )

    base_root = Path(request.base_workspace_root).resolve()
    killed_by: list[str] = []
    survived: list[str] = []
    artifacts: list[ArtifactRef] = []
    timed_out = False
    errors: list[str] = []
    invalid = False
    for record in request.tests_to_run:
        workspace = workspaces.get(record.record_key)
        if workspace is None:
            invalid = True
            errors.append(f"Missing workspace for {record.record_key}")
            continue
        mutation_artifacts = Path(workspace.artifacts_dir) / "mutations" / mutant.mutant_id / record.test_id
        mutated_workspace: WorkspaceSpec | None = None
        try:
            mutated_workspace = _isolated_workspace(
                workspace,
                mutant.mutant_id,
                base_root,
                mutation_artifacts,
            )
            target = _target(mutated_workspace, mutant.file_path, base_root)
            _mutate_file(target, mutant.line_start, mutant.original, mutant.mutated)
        except Exception as error:
            invalid = True
            errors.append(f"{record.record_key}: {type(error).__name__}: {error}")
            if mutated_workspace is not None:
                _cleanup_isolated_workspace(mutated_workspace.workspace_root, base_root)
            continue
        try:
            output = executor(
                TestRunnerInput(
                    run_id=request.run_id,
                    workspace=mutated_workspace,
                    timeout_seconds=request.timeout_seconds,
                    headless=True,
                    retry_index=0,
                    browser_stubs=request.browser_stubs,
                )
            )
            artifacts.extend(_runtime_artifacts(output))
            runtime = output.runtime
            if runtime.status == "pass":
                survived.append(record.record_key)
            elif runtime.status == "fail":
                killed_by.append(record.record_key)
            elif runtime.status == "timeout":
                timed_out = True
            elif runtime.status == "env_error":
                invalid = True
                errors.append(f"{record.record_key}: runtime environment became unavailable")
            else:
                invalid = True
                errors.append(f"{record.record_key}: mutation execution was skipped")
        except Exception as error:
            invalid = True
            errors.append(f"{record.record_key}: {type(error).__name__}: {error}")
        finally:
            _cleanup_isolated_workspace(mutated_workspace.workspace_root, base_root)

    if killed_by:
        result_status = "killed"
    elif timed_out:
        result_status = "timeout"
    elif invalid:
        result_status = "invalid"
    elif survived:
        result_status = "survived"
    else:
        result_status = "skipped"
    result = MutationRunResult(
        mutant_id=mutant.mutant_id,
        status=result_status,  # type: ignore[arg-type]
        killed_by_record_keys=sorted(killed_by),
        survived_record_keys=sorted(survived),
        runtime_artifacts=artifacts,
        error_summary="; ".join(errors) or None,
    )
    envelope_status = {
        "killed": Status.PASS,
        "survived": Status.WARNING,
        "timeout": Status.WARNING,
        "invalid": Status.UNKNOWN,
        "skipped": Status.SKIPPED,
    }[result_status]
    return MutationRunnerOutput(
        agent="mutation_runner",
        run_id=request.run_id,
        mode="full",
        project_id=mutant.project_id,
        status=envelope_status,
        confidence=1.0 if result_status in {"killed", "survived"} else 0.5,
        artifacts=artifacts,
        warnings=errors,
        result=result,
    )
