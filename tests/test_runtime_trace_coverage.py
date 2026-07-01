import json
from pathlib import Path

from test_evaluator.coverage import collect_coverage
from test_evaluator.runtime_trace import trace_runtime
from test_evaluator.schemas import (
    AgentReview,
    ArtifactRef,
    CoverageInput,
    ProjectInventory,
    RuntimeResult,
    RuntimeTraceInput,
    SelectorGroundingOutput,
    StaticFacts,
    Status,
    TestRecord as Record,
    TestRunnerOutput as RunnerOutput,
    WorkspaceSpec,
)


def _record() -> Record:
    return Record(
        project_id="Bench_Runtime",
        requirement_id="1",
        test_id="1",
        requirement="Unit",
        scenario="Feature: Unit\n  Scenario: Unit\n    Then unit",
        step_code="from behave import then\n@then('unit')\ndef unit(context):\n    assert True\n",
    )


def _facts() -> StaticFacts:
    return StaticFacts(python_parseable=True, scenario_present=True, sleep_count=1)


def _semantic_reviews(*, step: Status = Status.PASS) -> list[AgentReview]:
    return [
        AgentReview(
            agent="bdd_traceability",
            record_key=_record().record_key,
            dimension="spec_alignment",
            status=Status.PASS,
            confidence=0.9,
        ),
        AgentReview(
            agent="step_code",
            record_key=_record().record_key,
            dimension="step_traceability",
            status=step,
            confidence=0.9,
        ),
        AgentReview(
            agent="oracle_critic",
            record_key=_record().record_key,
            dimension="oracle_strength",
            status=Status.PASS,
            confidence=0.9,
        ),
    ]


def _grounding(status: Status = Status.PASS, *, missing: list[str] | None = None):
    return SelectorGroundingOutput(
        agent="selector_grounding",
        run_id="run",
        mode="full",
        record_key=_record().record_key,
        dimension="source_grounding",
        status=status,
        confidence=0.9,
        missing_source_anchors=missing or [],
    )


def _workspace(tmp_path: Path) -> WorkspaceSpec:
    app = tmp_path / "app"
    app.mkdir()
    entry = app / "index.html"
    entry.write_text("<html></html>", encoding="utf-8")
    feature = tmp_path / "test.feature"
    steps = tmp_path / "steps.py"
    feature.write_text("Feature: Unit\n", encoding="utf-8")
    steps.write_text("# unit\n", encoding="utf-8")
    return WorkspaceSpec(
        record_key=_record().record_key,
        workspace_root=str(tmp_path),
        app_root=str(app),
        feature_file=str(feature),
        steps_file=str(steps),
        entry_html=str(entry),
        artifacts_dir=str(tmp_path / "artifacts"),
    )


def test_runtime_trace_distinguishes_environment_and_test_failures(tmp_path: Path) -> None:
    stderr = tmp_path / "stderr.txt"
    stderr.write_text("No Chrome binary", encoding="utf-8")
    environment = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="env_error",
                error_type="env_error",
                stderr=ArtifactRef(kind="stderr", path=str(stderr)),
            ),
            static_facts=_facts(),
        )
    )
    assert environment.runtime_trace.likely_failure_cause == "environment_issue"
    assert environment.status is Status.UNKNOWN

    selector = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="fail",
                error_type="selector_not_found",
                failed_step="Then unit",
            ),
            static_facts=_facts(),
        )
    )
    assert selector.runtime_trace.likely_failure_cause == "indeterminate"
    assert selector.runtime_trace.failure_attribution.origin == "indeterminate"
    assert selector.runtime_trace.failure_attribution.test_quality_effect == "unknown"
    assert selector.runtime_trace.flaky_risk == "medium"
    assert selector.findings

    browser_trace = tmp_path / "browser_trace.json"
    browser_trace.write_text(
        json.dumps(
            {
                "storage": [{"operation": "setItem", "key": "cart"}],
                "network": [{"operation": "fetch", "url": "https://example.test"}],
                "browser_api": [{"operation": "speechSynthesis.speak"}],
            }
        ),
        encoding="utf-8",
    )
    observed = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="pass",
                browser_trace=ArtifactRef(kind="browser_trace", path=str(browser_trace)),
            ),
            static_facts=_facts(),
        )
    )
    assert {item.kind for item in observed.runtime_trace.observations} >= {
        "storage",
        "network",
        "browser_api",
    }


def test_runtime_failure_attribution_protects_test_quality_from_application_failures() -> None:
    application = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="fail",
                error_type="assertion_failure",
                failed_step="Then unit",
            ),
            static_facts=_facts(),
            reviews=_semantic_reviews(),
            selector_grounding=_grounding(),
        )
    )

    attribution = application.runtime_trace.failure_attribution
    assert attribution.origin == "application_defect"
    assert attribution.test_quality_effect == "neutral"
    assert application.status is Status.UNKNOWN


def test_runtime_failure_attribution_penalizes_evidence_backed_test_defects() -> None:
    test_defect = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="fail",
                error_type="assertion_failure",
                failed_step="Then unit",
            ),
            static_facts=_facts(),
            reviews=_semantic_reviews(step=Status.FAIL),
            selector_grounding=_grounding(),
        )
    )

    attribution = test_defect.runtime_trace.failure_attribution
    assert attribution.origin == "test_defect"
    assert attribution.test_quality_effect == "penalize"
    assert test_defect.status is Status.FAIL


def test_runtime_failure_attribution_keeps_required_source_mismatch_neutral() -> None:
    mismatch = trace_runtime(
        RuntimeTraceInput(
            run_id="run",
            record=_record(),
            runtime=RuntimeResult(
                record_key=_record().record_key,
                status="fail",
                error_type="selector_not_found",
                failed_step="Then unit",
            ),
            static_facts=_facts(),
            reviews=_semantic_reviews(),
            selector_grounding=_grounding(
                Status.FAIL,
                missing=['[data-testid="required-result"]'],
            ),
        )
    )

    attribution = mismatch.runtime_trace.failure_attribution
    assert attribution.origin == "contract_or_dataset_mismatch"
    assert attribution.test_quality_effect == "neutral"
    assert mismatch.status is Status.UNKNOWN


def test_coverage_normalizes_cdp_ranges(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)

    def executor(request):
        coverage_path = Path(request.workspace.artifacts_dir) / "baseline_attempt_0" / "coverage.json"
        coverage_path.parent.mkdir(parents=True)
        coverage_path.write_text(
            json.dumps(
                {
                    "result": [
                        {
                            "url": Path(workspace.entry_html).as_uri(),
                            "functions": [
                                {
                                    "functionName": "unit",
                                    "ranges": [
                                        {"startOffset": 0, "endOffset": 100, "count": 1},
                                        {"startOffset": 20, "endOffset": 40, "count": 0},
                                    ],
                                }
                            ],
                        }
                    ]
                }
            ),
            encoding="utf-8",
        )
        artifact = ArtifactRef(kind="coverage", path=str(coverage_path))
        return RunnerOutput(
            agent="test_runner",
            run_id=request.run_id,
            mode="full",
            record_key=request.workspace.record_key,
            status=Status.PASS,
            confidence=1.0,
            artifacts=[artifact],
            runtime=RuntimeResult(record_key=request.workspace.record_key, status="pass"),
        )

    output = collect_coverage(
        CoverageInput(
            run_id="run",
            inventory=ProjectInventory(project_id="Bench_Runtime"),
            workspace=workspace,
            runtime=RuntimeResult(record_key=workspace.record_key, status="pass"),
            method="cdp_precise_coverage",
        ),
        timeout_seconds=1,
        executor=executor,
    )
    assert output.status is Status.PASS
    assert output.coverage.files[0].file_path == "index.html"
    assert output.coverage.files[0].statement_coverage == 80.0


def test_coverage_instruments_external_javascript_with_istanbul(tmp_path: Path) -> None:
    workspace = _workspace(tmp_path)
    source = Path(workspace.app_root) / "script.js"
    source.write_text(
        "function classify(value) { return value > 0 ? 'yes' : 'no'; }\nclassify(1);\n",
        encoding="utf-8",
    )

    def executor(request):
        instrumented = Path(request.workspace.app_root) / "script.js"
        assert "__coverage__" in instrumented.read_text(encoding="utf-8")
        coverage_path = Path(request.workspace.artifacts_dir) / "baseline_attempt_0" / "istanbul_coverage.json"
        coverage_path.parent.mkdir(parents=True, exist_ok=True)
        coverage_path.write_text(
            json.dumps(
                {
                    str(instrumented): {
                        "path": str(instrumented),
                        "statementMap": {
                            "0": {"start": {"line": 1, "column": 0}, "end": {"line": 1, "column": 10}},
                            "1": {"start": {"line": 2, "column": 0}, "end": {"line": 2, "column": 10}},
                        },
                        "s": {"0": 1, "1": 0},
                        "fnMap": {"0": {}},
                        "f": {"0": 1},
                        "branchMap": {"0": {}},
                        "b": {"0": [1, 0]},
                    }
                }
            ),
            encoding="utf-8",
        )
        return RunnerOutput(
            agent="test_runner",
            run_id=request.run_id,
            mode="full",
            record_key=request.workspace.record_key,
            status=Status.PASS,
            confidence=1.0,
            artifacts=[ArtifactRef(kind="coverage", path=str(coverage_path))],
            runtime=RuntimeResult(record_key=request.workspace.record_key, status="pass"),
        )

    output = collect_coverage(
        CoverageInput(
            run_id="run",
            inventory=ProjectInventory(
                project_id="Bench_Runtime",
                source_root=workspace.app_root,
                source_files=["script.js"],
            ),
            workspace=workspace,
            runtime=RuntimeResult(record_key=workspace.record_key, status="pass"),
            method="istanbul",
        ),
        timeout_seconds=1,
        executor=executor,
    )
    file_coverage = output.coverage.files[0]
    assert output.coverage.method == "istanbul"
    assert file_coverage.file_path == "script.js"
    assert file_coverage.statement_coverage == 50.0
    assert file_coverage.branch_coverage == 50.0
    assert file_coverage.function_coverage == 100.0
    assert source.read_text(encoding="utf-8").startswith("function classify")
