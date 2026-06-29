from test_evaluator.dynamic_evidence import analyze_dynamic_oracle, analyze_dynamic_suite_coverage
from test_evaluator.schemas import (
    ArtifactRef,
    Behavior,
    DynamicOracleInput,
    DynamicSuiteCoverageInput,
    Evidence,
    MutationPlan,
    MutationRunResult,
    MutantSpec,
    RequirementContract,
    RuntimeResult,
    RuntimeTrace,
    SelectorGroundingItem,
    SelectorGroundingOutput,
    Status,
    TestRecord as Record,
)


def _record() -> Record:
    return Record(
        project_id="Bench_Dynamic",
        requirement_id="1",
        test_id="1",
        requirement="Click submit and show ready in #output",
        scenario="Feature: Dynamic\n  Scenario: [Normal] submit\n    Then ready is shown",
        step_code="assert output.text == 'ready'",
    )


def _runtime(record: Record) -> RuntimeResult:
    return RuntimeResult(
        record_key=record.record_key,
        status="pass",
        behave_json=ArtifactRef(kind="behave_json", path="behave.json"),
    )


def _grounding(record: Record) -> SelectorGroundingOutput:
    return SelectorGroundingOutput(
        agent="selector_grounding",
        run_id="run",
        mode="full",
        project_id=record.project_id,
        suite_key=record.suite_key,
        record_key=record.record_key,
        dimension="source_grounding",
        status=Status.PASS,
        confidence=1.0,
        selectors=[
            SelectorGroundingItem(
                selector="#output",
                source_exists=True,
                stability="stable",
                purpose="oracle_target",
                evidence=[Evidence(field="source", quote="#output")],
            )
        ],
    )


def _mutation_data(record: Record):
    mutants = [
        MutantSpec(
            mutant_id="killed",
            project_id=record.project_id,
            operator="dom_update",
            file_path="index.html",
            line_start=10,
            original="output.textContent = 'ready';",
            mutated='output.textContent = "";',
            behavior_candidates=["B1"],
            impacted_record_keys=[record.record_key],
        ),
        MutantSpec(
            mutant_id="survived",
            project_id=record.project_id,
            operator="comparison",
            file_path="index.html",
            line_start=11,
            original="count >= 1",
            mutated="count < 1",
            behavior_candidates=["B1"],
            impacted_record_keys=[record.record_key],
        ),
    ]
    results = [
        MutationRunResult(
            mutant_id="killed",
            status="killed",
            killed_by_record_keys=[record.record_key],
        ),
        MutationRunResult(
            mutant_id="survived",
            status="survived",
            survived_record_keys=[record.record_key],
        ),
    ]
    return MutationPlan(project_id=record.project_id, mutants=mutants), results


def test_dynamic_oracle_reports_observed_survivor() -> None:
    record = _record()
    runtime = _runtime(record)
    plan, results = _mutation_data(record)
    output = analyze_dynamic_oracle(
        DynamicOracleInput(
            run_id="run",
            record=record,
            runtime_trace=RuntimeTrace(record_key=record.record_key, execution_status=runtime),
            selector_grounding=_grounding(record),
            mutation_plan=plan,
            mutation_results=results,
        )
    )

    assert output.status is Status.WARNING
    assert output.runtime_confirmed is True
    assert output.oracle_selectors == ["#output"]
    assert output.mutation_score == 50.0
    assert output.killed_mutants == ["killed"]
    assert output.survived_mutants == ["survived"]
    assert output.findings[0].evidence[0].file_path == "index.html"


def test_dynamic_suite_builds_behavior_level_evidence() -> None:
    record = _record()
    runtime = _runtime(record)
    plan, results = _mutation_data(record)
    contract = RequirementContract(
        project_id=record.project_id,
        requirement_id=record.requirement_id,
        suite_key=record.suite_key,
        behaviors=[
            Behavior(
                behavior_id="B1",
                kind="normal",
                expected_observables=["ready is shown"],
                ui_anchors=["#output"],
                observability="dom",
            )
        ],
    )
    output = analyze_dynamic_suite_coverage(
        DynamicSuiteCoverageInput(
            run_id="run",
            suite_key=record.suite_key,
            contract=contract,
            records=[record],
            base_behavior_coverage={"B1": Status.PASS},
            runtime_results={record.record_key: runtime},
            selector_grounding={record.record_key: _grounding(record)},
            mutation_plan=plan,
            mutation_results=results,
        )
    )

    behavior = output.behavior_coverage[0]
    assert output.status is Status.WARNING
    assert behavior.status is Status.WARNING
    assert behavior.runtime_confirmed_by_records == [record.record_key]
    assert behavior.killed_by_mutants == ["killed"]
    assert behavior.survived_mutants == ["survived"]
    assert output.findings[0].status is Status.WARNING


def test_dynamic_oracle_skips_nonpassing_baseline() -> None:
    record = _record()
    runtime = RuntimeResult(record_key=record.record_key, status="env_error", error_type="env_error")
    output = analyze_dynamic_oracle(
        DynamicOracleInput(
            run_id="run",
            record=record,
            runtime_trace=RuntimeTrace(record_key=record.record_key, execution_status=runtime),
        )
    )

    assert output.status is Status.SKIPPED
    assert output.mutation_score is None
