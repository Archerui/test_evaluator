"""Optional Chrome DevTools precise-coverage collection and normalization."""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path
import shutil
import subprocess
from typing import Callable
from urllib.parse import unquote, urlparse

from .runner import run_baseline_test
from .schemas import (
    CoverageInput,
    CoverageOutput,
    CoverageReport,
    FileCoverage,
    Status,
    TestRunnerInput,
    TestRunnerOutput,
)


CoverageExecutor = Callable[[TestRunnerInput], TestRunnerOutput]


def _merged_length(ranges: list[tuple[int, int]]) -> int:
    merged: list[list[int]] = []
    for start, end in sorted(ranges):
        if end <= start:
            continue
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    return sum(end - start for start, end in merged)


def _file_path(url: str, app_root: Path) -> str:
    parsed = urlparse(url)
    if parsed.scheme == "file":
        path = Path(unquote(parsed.path)).resolve()
        try:
            return str(path.relative_to(app_root.resolve()))
        except ValueError:
            return str(path)
    return url or "<anonymous-script>"


def _is_application_url(url: str, app_root: Path) -> bool:
    parsed = urlparse(url)
    if parsed.scheme != "file":
        return False
    try:
        Path(unquote(parsed.path)).resolve().relative_to(app_root.resolve())
        return True
    except ValueError:
        return False


def _parse_coverage(path: Path, app_root: Path) -> list[FileCoverage]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    scripts = payload.get("result", []) if isinstance(payload, dict) else []
    files: list[FileCoverage] = []
    for script in scripts:
        if not isinstance(script, dict):
            continue
        script_url = str(script.get("url", ""))
        if not _is_application_url(script_url, app_root):
            continue
        functions = [item for item in script.get("functions", []) if isinstance(item, dict)]
        normalized_ranges: list[dict[str, object]] = []
        covered_functions = 0
        total_bytes = 0
        covered_bytes = 0
        for function in functions:
            ranges = [item for item in function.get("ranges", []) if isinstance(item, dict)]
            if ranges:
                root = ranges[0]
                root_start = int(root.get("startOffset", 0))
                root_end = int(root.get("endOffset", 0))
                root_length = max(0, root_end - root_start)
                uncovered = _merged_length(
                    [
                        (int(item.get("startOffset", 0)), int(item.get("endOffset", 0)))
                        for item in ranges
                        if int(item.get("count", 0)) == 0
                    ]
                )
                function_covered = max(0, root_length - min(root_length, uncovered))
                total_bytes += root_length
                covered_bytes += function_covered
                if function_covered > 0:
                    covered_functions += 1
            for item in ranges:
                start = int(item.get("startOffset", 0))
                end = int(item.get("endOffset", 0))
                count = int(item.get("count", 0))
                normalized_ranges.append({"start": start, "end": end, "count": count})
        files.append(
            FileCoverage(
                file_path=_file_path(script_url, app_root),
                statement_coverage=(covered_bytes / total_bytes * 100.0) if total_bytes else None,
                function_coverage=(covered_functions / len(functions) * 100.0) if functions else None,
                executed_ranges=normalized_ranges,
            )
        )
    return files


def _parse_istanbul(path: Path, app_root: Path) -> list[FileCoverage]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    files: list[FileCoverage] = []
    for raw_path, item in payload.items():
        if not isinstance(item, dict):
            continue
        file_path = Path(str(item.get("path") or raw_path))
        try:
            normalized = str(file_path.resolve().relative_to(app_root.resolve()))
        except ValueError:
            normalized = str(file_path)
        statements = item.get("s", {}) if isinstance(item.get("s"), dict) else {}
        functions = item.get("f", {}) if isinstance(item.get("f"), dict) else {}
        branches = item.get("b", {}) if isinstance(item.get("b"), dict) else {}
        branch_counts = [
            int(count)
            for counts in branches.values()
            if isinstance(counts, list)
            for count in counts
        ]
        statement_map = item.get("statementMap", {}) if isinstance(item.get("statementMap"), dict) else {}
        executed_ranges = []
        for statement_id, location in statement_map.items():
            if not isinstance(location, dict):
                continue
            executed_ranges.append(
                {
                    "statement_id": statement_id,
                    "start": location.get("start"),
                    "end": location.get("end"),
                    "count": int(statements.get(statement_id, 0)),
                }
            )
        files.append(
            FileCoverage(
                file_path=normalized,
                statement_coverage=(
                    sum(int(count) > 0 for count in statements.values()) / len(statements) * 100.0
                    if statements
                    else None
                ),
                branch_coverage=(
                    sum(count > 0 for count in branch_counts) / len(branch_counts) * 100.0
                    if branch_counts
                    else None
                ),
                function_coverage=(
                    sum(int(count) > 0 for count in functions.values()) / len(functions) * 100.0
                    if functions
                    else None
                ),
                executed_ranges=executed_ranges,
            )
        )
    return files


def _istanbul_available() -> bool:
    if shutil.which("node") is None:
        return False
    try:
        completed = subprocess.run(
            ["node", "-e", "require.resolve('istanbul-lib-instrument')"],
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def _instrumented_workspace(request: CoverageInput) -> tuple[object, Path]:
    workspace = request.workspace
    original_root = Path(workspace.workspace_root).resolve()
    original_app = Path(workspace.app_root).resolve()
    original_features = Path(workspace.feature_file).resolve().parent
    entry_relative = Path(workspace.entry_html).resolve().relative_to(original_app)
    feature_relative = Path(workspace.feature_file).resolve().relative_to(original_features)
    steps_relative = Path(workspace.steps_file).resolve().relative_to(original_features)
    clone_parent = original_root.parent / ".coverage_workspaces"
    clone_root = clone_parent / sha256(workspace.record_key.encode()).hexdigest()[:16]
    if clone_root.exists():
        shutil.rmtree(clone_root)
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
        for original, replacement in (
            (Path(workspace.entry_html).resolve().as_uri(), clone_entry.resolve().as_uri()),
            (str(Path(workspace.entry_html).resolve()), str(clone_entry.resolve())),
            (str(original_app), str(clone_app.resolve())),
        ):
            step_code = step_code.replace(original, replacement)
        clone_steps.write_text(step_code, encoding="utf-8")
        js_files = [
            clone_app / relative
            for relative in request.inventory.source_files
            if Path(relative).suffix.casefold() in {".js", ".mjs", ".cjs"}
            and (clone_app / relative).is_file()
        ]
        if not js_files:
            raise RuntimeError("No external JavaScript files are available for Istanbul instrumentation")
        script = Path(__file__).with_name("instrument_js.cjs")
        completed = subprocess.run(
            ["node", str(script), *[str(path) for path in js_files]],
            cwd=clone_root,
            text=True,
            capture_output=True,
            timeout=30,
            check=False,
        )
        if completed.returncode:
            raise RuntimeError((completed.stderr or completed.stdout or "Istanbul instrumentation failed").strip())
        instrumented = workspace.model_copy(
            update={
                "workspace_root": str(clone_root),
                "app_root": str(clone_app),
                "feature_file": str(clone_features / feature_relative),
                "steps_file": str(clone_steps),
                "entry_html": str(clone_entry),
                "artifacts_dir": str(Path(workspace.artifacts_dir) / "coverage_run"),
            }
        )
        return instrumented, clone_parent
    except Exception:
        shutil.rmtree(clone_root, ignore_errors=True)
        try:
            clone_parent.rmdir()
        except OSError:
            pass
        raise


def collect_coverage(
    request: CoverageInput,
    *,
    timeout_seconds: float,
    headless: bool = True,
    executor: CoverageExecutor = run_baseline_test,
) -> CoverageOutput:
    if request.method == "none" or request.runtime.status != "pass":
        report = CoverageReport(
            project_id=request.inventory.project_id,
            record_key=request.workspace.record_key,
            method=request.method,
            status=Status.SKIPPED,
        )
        return CoverageOutput(
            agent="coverage",
            run_id=request.run_id,
            mode="full",
            project_id=request.inventory.project_id,
            record_key=request.workspace.record_key,
            status=Status.SKIPPED,
            confidence=1.0,
            warnings=["Coverage requires a passing baseline runtime"],
            coverage=report,
        )

    warnings: list[str] = []
    effective_method = request.method
    coverage_workspace = request.workspace.model_copy(
        update={"artifacts_dir": str(Path(request.workspace.artifacts_dir) / "coverage_run")}
    )
    cleanup_root: Path | None = None
    if effective_method in {"auto", "istanbul"}:
        try:
            if not _istanbul_available():
                raise RuntimeError("istanbul-lib-instrument is unavailable to Node.js")
            coverage_workspace, cleanup_parent = _instrumented_workspace(request)
            cleanup_root = Path(coverage_workspace.workspace_root)
            effective_method = "istanbul"
        except Exception as error:
            warnings.append(f"Istanbul unavailable; used CDP fallback: {error}")
            effective_method = "cdp_precise_coverage"
    try:
        output = executor(
            TestRunnerInput(
                run_id=request.run_id,
                workspace=coverage_workspace,
                timeout_seconds=timeout_seconds,
                headless=headless,
                collect_coverage=True,
                coverage_method=effective_method,  # type: ignore[arg-type]
                browser_stubs=request.browser_stubs,
            )
        )
    finally:
        if cleanup_root is not None:
            cleanup_parent = cleanup_root.parent
            shutil.rmtree(cleanup_root, ignore_errors=True)
            try:
                cleanup_parent.rmdir()
            except OSError:
                pass
    expected_name = "istanbul_coverage.json" if effective_method == "istanbul" else "coverage.json"
    coverage_artifact = next(
        (item for item in output.artifacts if item.kind == "coverage" and Path(item.path).name == expected_name),
        None,
    )
    files: list[FileCoverage] = []
    status = Status.UNKNOWN
    if coverage_artifact:
        try:
            files = (
                _parse_istanbul(Path(coverage_artifact.path), Path(coverage_workspace.app_root))
                if effective_method == "istanbul"
                else _parse_coverage(Path(coverage_artifact.path), Path(request.workspace.app_root))
            )
            status = Status.PASS if output.runtime.status == "pass" and files else Status.WARNING
        except (OSError, ValueError, json.JSONDecodeError) as error:
            warnings.append(f"Could not parse CDP coverage: {error}")
    else:
        warnings.append("Chrome produced no precise-coverage artifact")
    if output.runtime.status != "pass":
        warnings.append(f"Coverage rerun ended with {output.runtime.status}")
    report = CoverageReport(
        project_id=request.inventory.project_id,
        record_key=request.workspace.record_key,
        method=effective_method,
        status=status,
        files=files,
        artifacts=[coverage_artifact] if coverage_artifact else [],
    )
    return CoverageOutput(
        agent="coverage",
        run_id=request.run_id,
        mode="full",
        project_id=request.inventory.project_id,
        record_key=request.workspace.record_key,
        status=status,
        confidence=1.0 if status in {Status.PASS, Status.WARNING} else 0.0,
        artifacts=output.artifacts,
        warnings=warnings,
        coverage=report,
    )
