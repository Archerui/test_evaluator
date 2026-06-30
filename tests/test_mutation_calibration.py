from test_evaluator.mutation_calibration import calibrate_static_mutation
from test_evaluator.reporting import write_reports
from test_evaluator.schemas import (
    EvaluationRun,
    MutantSpec,
    MutationPlan,
    MutationRunResult,
    ProjectReport,
    StaticFacts,
    StaticMutationAssessment,
    StaticMutationHypothesis,
    TestReport as Report,
)


def _report(record_key: str, prediction: str) -> Report:
    project_id, requirement_id, test_id = record_key.split("::")
    return Report(
        record_key=record_key,
        project_id=project_id,
        requirement_id=requirement_id,
        test_id=test_id,
        confidence_coverage=1.0,
        risk="low",
        static_facts=StaticFacts(python_parseable=True, scenario_present=True),
        static_mutation=StaticMutationAssessment(
            record_key=record_key,
            readiness_score=100.0 if prediction == "likely_detected" else 0.0,
            prediction_coverage=1.0,
            hypotheses=[
                StaticMutationHypothesis(
                    hypothesis_id=f"hypothesis-{test_id}",
                    fault_class="event_handler",
                    behavior_ids=["B1"],
                    description="A required event handler is omitted.",
                    prediction=prediction,  # type: ignore[arg-type]
                    confidence=0.9,
                    rationale="Generic assertion-flow prediction.",
                )
            ],
        ),
    )


def test_full_mutation_calibration_is_generic_and_non_scoring() -> None:
    strong = _report("Bench::1::strong", "likely_detected")
    weak = _report("Bench::1::weak", "likely_survives")
    original_scores = [strong.test_quality_score, weak.test_quality_score]
    plan = MutationPlan(
        project_id="Bench",
        mutants=[
            MutantSpec(
                mutant_id="generic-event-handler-mutant",
                project_id="Bench",
                operator="event_handler",
                file_path="app.js",
                original="handler",
                mutated="",
                behavior_candidates=["B1"],
                impacted_record_keys=[strong.record_key, weak.record_key],
            )
        ],
    )
    results = [
        MutationRunResult(
            mutant_id="generic-event-handler-mutant",
            status="killed",
            killed_by_record_keys=[strong.record_key],
            survived_record_keys=[weak.record_key],
        )
    ]

    calibration = calibrate_static_mutation(
        [strong, weak],
        {"Bench": plan},
        {"Bench": results},
    )

    assert calibration.observation_count == 2
    assert calibration.matched_count == 2
    assert calibration.accuracy == 1.0
    assert calibration.scoring_effect == "none"
    assert calibration.recommendations == []
    assert [strong.test_quality_score, weak.test_quality_score] == original_scores


def test_calibration_emits_general_fault_class_action_for_mismatch() -> None:
    report = _report("Bench::1::strong", "likely_detected")
    plan = MutationPlan(
        project_id="Bench",
        mutants=[
            MutantSpec(
                mutant_id="generic-event-handler-mutant",
                project_id="Bench",
                operator="event_handler",
                file_path="app.js",
                original="handler",
                mutated="",
                behavior_candidates=["B1"],
                impacted_record_keys=[report.record_key],
            )
        ],
    )
    result = MutationRunResult(
        mutant_id="generic-event-handler-mutant",
        status="survived",
        survived_record_keys=[report.record_key],
    )

    calibration = calibrate_static_mutation(
        [report],
        {"Bench": plan},
        {"Bench": [result]},
    )

    assert calibration.accuracy == 0.0
    assert calibration.recommendations[0].fault_class == "event_handler"
    assert calibration.recommendations[0].issue == "static_overconfidence"


def test_calibration_is_written_as_a_separate_non_scoring_artifact(tmp_path) -> None:
    report = _report("Bench::1::strong", "likely_detected")
    run = EvaluationRun(
        mode="full",
        tests=[report],
        requirements=[],
        projects=[ProjectReport(project_id="Bench", test_count=1, requirement_count=0)],
    )
    run.mutation_calibration = calibrate_static_mutation([report], {}, {})

    write_reports(run, tmp_path)

    artifact = (tmp_path / "mutation_calibration.json").read_text(encoding="utf-8")
    summary = (tmp_path / "summary.md").read_text(encoding="utf-8")
    assert '"scoring_effect": "none"' in artifact
    assert "## Static-to-Real Mutation Calibration" in summary
