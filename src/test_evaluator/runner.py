"""Execute materialized Behave tests and classify their outcomes."""

from __future__ import annotations

import importlib.util
import json
import os
import signal
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

from .schemas import ArtifactRef, Status, TestRunnerInput, TestRunnerOutput
from .state_machine import file_hash


CommandExecutor = Callable[..., subprocess.CompletedProcess[str]]


def _execute_command(command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    """Run Behave in its own process group so timeout cleanup also reaches Chrome."""

    timeout = kwargs.pop("timeout")
    check = kwargs.pop("check", False)
    capture_output = kwargs.pop("capture_output", False)
    if capture_output:
        kwargs["stdout"] = subprocess.PIPE
        kwargs["stderr"] = subprocess.PIPE
    process = subprocess.Popen(command, start_new_session=(os.name == "posix"), **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        if os.name == "posix":
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
        else:
            process.terminate()
        try:
            stdout, stderr = process.communicate(timeout=2)
        except subprocess.TimeoutExpired:
            if os.name == "posix":
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                process.kill()
            stdout, stderr = process.communicate()
        raise subprocess.TimeoutExpired(command, timeout, output=stdout, stderr=stderr) from error
    completed = subprocess.CompletedProcess(command, process.returncode, stdout=stdout, stderr=stderr)
    if check and process.returncode:
        raise subprocess.CalledProcessError(process.returncode, command, output=stdout, stderr=stderr)
    return completed


def runtime_environment_issues() -> list[str]:
    """Return missing baseline runtime dependencies without starting a browser."""

    issues: list[str] = []
    for module in ("behave", "selenium"):
        if importlib.util.find_spec(module) is None:
            issues.append(f"Python package {module!r} is not installed")
    browser = next(
        (
            executable
            for executable in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser")
            if shutil.which(executable)
        ),
        None,
    )
    if browser is None:
        issues.append("No Chrome/Chromium browser executable was found on PATH")
    return issues


def _artifact(kind: str, path: Path, description: str) -> ArtifactRef | None:
    if not path.is_file():
        return None
    return ArtifactRef(
        kind=kind,  # type: ignore[arg-type]
        path=str(path),
        description=description,
        sha256=file_hash(path),
    )


def _failed_step(behave_json: Path) -> tuple[str | None, str]:
    if not behave_json.is_file():
        return None, ""
    try:
        payload = json.loads(behave_json.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, ""
    features = payload if isinstance(payload, list) else [payload]
    messages: list[str] = []
    for feature in features:
        if not isinstance(feature, dict):
            continue
        for element in feature.get("elements", []):
            if not isinstance(element, dict):
                continue
            for step in element.get("steps", []):
                if not isinstance(step, dict):
                    continue
                result = step.get("result")
                if not isinstance(result, dict):
                    continue
                error_message = str(result.get("error_message", ""))
                if error_message:
                    messages.append(error_message)
                if str(result.get("status", "")).casefold() == "failed":
                    keyword = str(step.get("keyword", "")).strip()
                    name = str(step.get("name", "")).strip()
                    return " ".join(part for part in (keyword, name) if part), "\n".join(messages)
    return None, "\n".join(messages)


def _classify_error(output: str) -> tuple[str, bool]:
    lowered = output.casefold()
    if any(token in lowered for token in ("assertionerror", "assert ", "assertion failed")):
        return "assertion_failure", False
    if any(token in lowered for token in ("nosuchelementexception", "no such element", "unable to locate element")):
        return "selector_not_found", False
    if any(token in lowered for token in ("syntaxerror", "indentationerror", "taberror")):
        return "syntax_error", False
    if any(token in lowered for token in ("err_file_not_found", "file not found", "no such file or directory")):
        return "path_error", False
    if any(
        token in lowered
        for token in (
            "sessionnotcreatedexception",
            "webdriverexception",
            "cannot find chrome binary",
            "chrome failed to start",
            "unable to obtain driver",
            "modulenotfounderror",
        )
    ):
        return "browser_error", True
    return "unknown", False


def _runtime_output(
    request: TestRunnerInput,
    *,
    status: str,
    duration: float,
    error_type: str | None,
    failed_step: str | None,
    attempt_dir: Path,
) -> TestRunnerOutput:
    stdout = _artifact("stdout", attempt_dir / "stdout.txt", "Behave standard output")
    stderr = _artifact("stderr", attempt_dir / "stderr.txt", "Behave standard error")
    behave_json = _artifact("behave_json", attempt_dir / "behave.json", "Behave JSON result")
    screenshot = _artifact("screenshot", attempt_dir / "failure.png", "Browser screenshot at failed step")
    dom_snapshot = _artifact("dom_snapshot", attempt_dir / "dom_snapshot.html", "DOM at failed step")
    console_log = _artifact("console_log", attempt_dir / "console_log.json", "Browser console at failed step")
    coverage = _artifact("coverage", attempt_dir / "coverage.json", "Chrome precise JavaScript coverage")
    istanbul_coverage = _artifact(
        "coverage", attempt_dir / "istanbul_coverage.json", "Istanbul JavaScript coverage"
    )
    browser_trace = _artifact(
        "browser_trace", attempt_dir / "browser_trace.json", "Storage/network/browser API trace"
    )
    network_log = _artifact(
        "network_log", attempt_dir / "network_log.json", "Chrome DevTools Network events"
    )
    runtime = {
        "record_key": request.workspace.record_key,
        "status": status,
        "duration_seconds": duration,
        "failed_step": failed_step,
        "error_type": error_type,
        "stdout": stdout,
        "stderr": stderr,
        "behave_json": behave_json,
        "screenshot": screenshot,
        "dom_snapshot": dom_snapshot,
        "console_log": console_log,
        "browser_trace": browser_trace,
        "network_log": network_log,
    }
    envelope_status = {
        "pass": Status.PASS,
        "fail": Status.FAIL,
        "timeout": Status.WARNING,
        "env_error": Status.UNKNOWN,
        "skipped": Status.SKIPPED,
    }[status]
    artifacts = [
        item
        for item in (
            stdout,
            stderr,
            behave_json,
            screenshot,
            dom_snapshot,
            console_log,
            coverage,
            istanbul_coverage,
            browser_trace,
            network_log,
        )
        if item
    ]
    return TestRunnerOutput(
        agent="test_runner",
        run_id=request.run_id,
        mode="full",
        record_key=request.workspace.record_key,
        status=envelope_status,
        confidence=1.0 if status in {"pass", "fail"} else 0.5,
        artifacts=artifacts,
        runtime=runtime,  # type: ignore[arg-type]
    )


def run_baseline_test(
    request: TestRunnerInput,
    *,
    executor: CommandExecutor | None = None,
    environment_issues: list[str] | None = None,
) -> TestRunnerOutput:
    """Run one workspace, returning env_error instead of conflating setup failures with test failures."""

    workspace = request.workspace
    feature_file = Path(workspace.feature_file)
    if not feature_file.is_file():
        raise FileNotFoundError(f"Materialized feature file is missing: {feature_file}")

    attempt_dir = Path(workspace.artifacts_dir) / f"baseline_attempt_{request.retry_index}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    stdout_path = attempt_dir / "stdout.txt"
    stderr_path = attempt_dir / "stderr.txt"
    behave_json = attempt_dir / "behave.json"
    issues = runtime_environment_issues() if environment_issues is None else environment_issues
    if issues:
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text("Runtime environment unavailable:\n- " + "\n- ".join(issues) + "\n", encoding="utf-8")
        return _runtime_output(
            request,
            status="env_error",
            duration=0.0,
            error_type="env_error",
            failed_step=None,
            attempt_dir=attempt_dir,
        )

    command = [
        sys.executable,
        "-m",
        "behave",
        str(feature_file),
        "--format",
        "json.pretty",
        "--outfile",
        str(behave_json),
        "--no-capture",
        "--no-capture-stderr",
        "--no-color",
    ]
    environment = os.environ.copy()
    # Chrome for Testing can use shared libraries installed in the active Conda
    # environment. Propagate that library directory to Chrome/ChromeDriver child
    # processes as well as to the Python Behave process.
    conda_prefix = environment.get("CONDA_PREFIX")
    if conda_prefix:
        conda_lib = str(Path(conda_prefix) / "lib")
        existing_library_path = environment.get("LD_LIBRARY_PATH")
        environment["LD_LIBRARY_PATH"] = (
            f"{conda_lib}:{existing_library_path}" if existing_library_path else conda_lib
        )
    environment["TEST_EVALUATOR_HEADLESS"] = "1" if request.headless else "0"
    environment["TEST_EVALUATOR_ARTIFACTS"] = str(attempt_dir)
    coverage_method = request.coverage_method
    if request.collect_coverage and coverage_method == "none":
        coverage_method = "cdp_precise_coverage"
    environment["TEST_EVALUATOR_COVERAGE_METHOD"] = coverage_method
    environment["TEST_EVALUATOR_OBSERVABILITY"] = "1"
    environment["TEST_EVALUATOR_BROWSER_STUBS"] = ",".join(request.browser_stubs)
    invoke = executor or _execute_command
    started = time.monotonic()
    try:
        completed = invoke(
            command,
            cwd=workspace.workspace_root,
            env=environment,
            text=True,
            capture_output=True,
            timeout=request.timeout_seconds,
            check=False,
        )
        duration = time.monotonic() - started
        stdout_path.write_text(completed.stdout or "", encoding="utf-8")
        stderr_path.write_text(completed.stderr or "", encoding="utf-8")
    except subprocess.TimeoutExpired as error:
        duration = time.monotonic() - started
        stdout = error.stdout.decode(errors="replace") if isinstance(error.stdout, bytes) else (error.stdout or "")
        stderr = error.stderr.decode(errors="replace") if isinstance(error.stderr, bytes) else (error.stderr or "")
        stdout_path.write_text(stdout, encoding="utf-8")
        stderr_path.write_text(stderr + f"\nTimed out after {request.timeout_seconds:.1f} seconds.\n", encoding="utf-8")
        return _runtime_output(
            request,
            status="timeout",
            duration=duration,
            error_type="timeout",
            failed_step=None,
            attempt_dir=attempt_dir,
        )
    except OSError as error:
        duration = time.monotonic() - started
        stdout_path.write_text("", encoding="utf-8")
        stderr_path.write_text(f"{type(error).__name__}: {error}\n", encoding="utf-8")
        return _runtime_output(
            request,
            status="env_error",
            duration=duration,
            error_type="env_error",
            failed_step=None,
            attempt_dir=attempt_dir,
        )

    if completed.returncode == 0:
        return _runtime_output(
            request,
            status="pass",
            duration=duration,
            error_type=None,
            failed_step=None,
            attempt_dir=attempt_dir,
        )

    failed_step, behave_error = _failed_step(behave_json)
    error_type, environment_failure = _classify_error(
        "\n".join((completed.stdout or "", completed.stderr or "", behave_error))
    )
    return _runtime_output(
        request,
        status="env_error" if environment_failure else "fail",
        duration=duration,
        error_type="env_error" if environment_failure else error_type,
        failed_step=failed_step,
        attempt_dir=attempt_dir,
    )
