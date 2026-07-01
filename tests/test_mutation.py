from pathlib import Path

from test_evaluator.mutation.analyzer import analyze_mutations
from test_evaluator.mutation.generator import generate_mutation_plan
from test_evaluator.mutation.operators import generate_candidates
from test_evaluator.mutation.runner import run_mutant
from test_evaluator.orchestrator import _impacted_record_keys
from test_evaluator.scoring import attach_mutation_results
from test_evaluator.schemas import (
    Behavior,
    EvaluationRun,
    MutationAnalystInput,
    MutationGeneratorInput,
    MutationPlan,
    MutationRunResult,
    MutationRunnerInput,
    MutantSpec,
    ProjectInventory,
    ProjectReport,
    RequirementContract,
    RequirementReport,
    RuntimeResult,
    SourceModel,
    StaticFacts,
    Status,
    TestRecord as Record,
    TestReport as Report,
    TestRunnerOutput as RunnerOutput,
    WorkspaceSpec,
)


SOURCE = """const enabled = true;
button.addEventListener('dragstart', () => {
  if (enabled === true) {
    output.textContent = 'ready';
    localStorage.setItem('state', 'ready');
    speechSynthesis.speak(message);
  }
});
const digits = value.replace(/[^0-9.]/g, '');
"""


def test_operators_and_generator_are_bounded_and_avoid_regex_ranges(tmp_path: Path) -> None:
    candidates = generate_candidates("script.js", SOURCE)
    assert {item.operator for item in candidates} >= {
        "event_name",
        "event_handler",
        "dom_update",
        "api_call",
        "string_literal",
        "comparison",
        "boolean_literal",
    }
    assert not any("0+9" in item.mutated for item in candidates)
    assert any(
        item.operator == "numeric_literal"
        for item in generate_candidates("script.js", "let count = 0;\n")
    )

    source = tmp_path / "source"
    source.mkdir()
    (source / "script.js").write_text(SOURCE, encoding="utf-8")
    inventory = ProjectInventory(
        project_id="Bench_Mutation",
        source_root=str(source),
        source_files=["script.js"],
    )
    output = generate_mutation_plan(
        MutationGeneratorInput(
            run_id="run",
            inventory=inventory,
            source_model=SourceModel(
                project_id="Bench_Mutation",
                source_root=str(source),
                source_files=["script.js"],
            ),
            contracts=[
                RequirementContract(
                    project_id="Bench_Mutation",
                    requirement_id="1",
                    suite_key="Bench_Mutation::1",
                    behaviors=[
                        Behavior(
                            behavior_id="B-drag",
                            kind="normal",
                            actor_actions=["Drag the product"],
                            observability="dom",
                        )
                    ],
                )
            ],
            max_mutants=3,
        )
    )
    assert output.status is Status.PASS
    assert len(output.plan.mutants) == 3
    assert len({item.mutant_id for item in output.plan.mutants}) == 3
    assert any("B-drag" in item.behavior_candidates for item in output.plan.mutants)


def _record() -> Record:
    return Record(
        project_id="Bench_Mutation",
        requirement_id="1",
        test_id="1",
        requirement="Show ready state",
        scenario="Feature: Unit\n  Scenario: Unit\n    Then ready",
        step_code="from behave import then\n@then('ready')\ndef ready(context):\n    assert True\n",
    )


def test_mutation_runner_restores_workspace_and_classifies_kill(tmp_path: Path) -> None:
    workspace_root = tmp_path / "workspaces" / "record"
    app = workspace_root / "app"
    features = workspace_root / "features"
    artifacts = workspace_root / "artifacts"
    app.mkdir(parents=True)
    features.mkdir()
    artifacts.mkdir()
    source_file = app / "script.js"
    original = "if (enabled === true) {\n  output.textContent = 'ready';\n}\n"
    source_file.write_text(original, encoding="utf-8")
    feature = features / "test.feature"
    steps = features / "steps.py"
    entry = app / "index.html"
    feature.write_text("Feature: Unit\n", encoding="utf-8")
    entry.write_text("<html></html>", encoding="utf-8")
    steps.write_text(f'ENTRY = "{entry}"\nURI = "{entry.as_uri()}"\n', encoding="utf-8")
    workspace = WorkspaceSpec(
        record_key=_record().record_key,
        workspace_root=str(workspace_root),
        app_root=str(app),
        feature_file=str(feature),
        steps_file=str(steps),
        entry_html=str(entry),
        artifacts_dir=str(artifacts),
    )
    mutant = MutantSpec(
        mutant_id="m1",
        project_id="Bench_Mutation",
        operator="comparison",
        file_path="script.js",
        line_start=1,
        original="if (enabled === true) {",
        mutated="if (enabled !== true) {",
        impacted_record_keys=[_record().record_key],
    )

    def executor(request):
        isolated_source = Path(request.workspace.app_root) / "script.js"
        assert isolated_source != source_file
        mutated = "!==" in isolated_source.read_text(encoding="utf-8")
        isolated_steps = Path(request.workspace.steps_file).read_text(encoding="utf-8")
        assert str(Path(request.workspace.entry_html)) in isolated_steps
        assert Path(request.workspace.entry_html).as_uri() in isolated_steps
        runtime = RuntimeResult(
            record_key=request.workspace.record_key,
            status="fail" if mutated else "pass",
            error_type="assertion_failure" if mutated else None,
        )
        return RunnerOutput(
            agent="test_runner",
            run_id=request.run_id,
            mode="full",
            record_key=request.workspace.record_key,
            status=Status.FAIL if mutated else Status.PASS,
            confidence=1.0,
            runtime=runtime,
        )

    output = run_mutant(
        MutationRunnerInput(
            run_id="run",
            mutant=mutant,
            base_workspace_root=str(tmp_path / "workspaces"),
            tests_to_run=[_record()],
            timeout_seconds=1,
        ),
        workspaces={_record().record_key: workspace},
        executor=executor,
    )
    assert output.result.status == "killed"
    assert output.result.killed_by_record_keys == [_record().record_key]
    assert source_file.read_text(encoding="utf-8") == original
    assert not list((tmp_path / "workspaces" / ".mutation_workspaces").glob("*/*"))


def test_behavior_grounding_limits_impacted_tests_with_conservative_fallback() -> None:
    first = _record()
    second = first.model_copy(update={"requirement_id": "2", "test_id": "2"})
    contract = RequirementContract(
        project_id=first.project_id,
        requirement_id="1",
        suite_key=first.suite_key,
        behaviors=[
            Behavior(
                behavior_id="B1",
                kind="normal",
                observability="dom",
            )
        ],
    )
    grounded = MutantSpec(
        mutant_id="grounded",
        project_id=first.project_id,
        operator="dom_update",
        file_path="script.js",
        original="old",
        mutated="new",
        behavior_candidates=["B1"],
    )
    unmapped = grounded.model_copy(update={"mutant_id": "unmapped", "behavior_candidates": []})

    assert _impacted_record_keys(grounded, [first, second], {first.suite_key: contract}) == [
        first.record_key
    ]
    assert _impacted_record_keys(unmapped, [first, second], {first.suite_key: contract}) == [
        first.record_key,
        second.record_key,
    ]


def test_attached_surviving_mutant_finding_does_not_claim_it_was_killed() -> None:
    record = _record()
    mutant = MutantSpec(
        mutant_id="m-survivor",
        project_id=record.project_id,
        operator="dom_update",
        file_path="index.html",
        original="output.textContent = 'ready'",
        mutated="output.textContent = ''",
    )
    result = MutationRunResult(
        mutant_id=mutant.mutant_id,
        status="survived",
        survived_record_keys=[record.record_key],
    )
    run = EvaluationRun(
        mode="full",
        tests=[
            Report(
                record_key=record.record_key,
                project_id=record.project_id,
                requirement_id=record.requirement_id,
                test_id=record.test_id,
                confidence_coverage=1.0,
                risk="low",
                static_facts=StaticFacts(python_parseable=True, scenario_present=True),
            )
        ],
        requirements=[
            RequirementReport(
                suite_key=record.suite_key,
                project_id=record.project_id,
                requirement_id=record.requirement_id,
                test_count=1,
            )
        ],
        projects=[ProjectReport(project_id=record.project_id, test_count=1, requirement_count=1)],
    )

    attach_mutation_results(
        run,
        {record.project_id: MutationPlan(project_id=record.project_id, mutants=[mutant])},
        {record.project_id: [result]},
        {},
    )

    review = next(item for item in run.tests[0].reviews if item.agent == "mutation_runner")
    assert review.findings[0].criterion == "Mutant m-survivor survives this test"


def test_mutation_analyzer_excludes_invalid_results() -> None:
    mutants = [
        MutantSpec(
            mutant_id=mutant_id,
            project_id="Bench_Mutation",
            operator="comparison",
            file_path="script.js",
            line_start=index,
            original="old",
            mutated="new",
        )
        for index, mutant_id in enumerate(("killed", "survived", "invalid", "equivalent"), start=1)
    ]
    mutants[-1] = mutants[-1].model_copy(update={"suspected_equivalent": True})
    output = analyze_mutations(
        MutationAnalystInput(
            run_id="run",
            project_id="Bench_Mutation",
            contract_by_suite={},
            source_model=SourceModel(project_id="Bench_Mutation", source_root="/tmp"),
            mutation_plan=MutationPlan(project_id="Bench_Mutation", mutants=mutants),
            mutation_results=[
                MutationRunResult(mutant_id="killed", status="killed"),
                MutationRunResult(mutant_id="survived", status="survived"),
                MutationRunResult(mutant_id="invalid", status="invalid"),
                MutationRunResult(mutant_id="equivalent", status="survived"),
            ],
            test_reviews=[],
        )
    )
    assert output.analysis.mutation_score == 50.0
    assert [item.mutant_id for item in output.analysis.top_survived_mutants] == ["survived"]
    assert output.analysis.behavior_summaries[0].suspected_equivalent_mutants == ["equivalent"]
