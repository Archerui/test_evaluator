"""Offline calibration of static predictions against full mutation outcomes."""

from __future__ import annotations

from collections import Counter, defaultdict

from .schemas import (
    MutationCalibrationObservation,
    MutationCalibrationRecommendation,
    MutationCalibrationReport,
    MutationPlan,
    MutationRunResult,
    TestReport,
)


def calibrate_static_mutation(
    tests: list[TestReport],
    plans_by_project: dict[str, MutationPlan],
    results_by_project: dict[str, list[MutationRunResult]],
) -> MutationCalibrationReport:
    """Compare generic fault-class predictions; never modify test scores."""

    observations: list[MutationCalibrationObservation] = []
    for test in tests:
        assessment = test.static_mutation
        if assessment is None:
            continue
        plan = plans_by_project.get(test.project_id)
        if plan is None:
            continue
        results = {
            result.mutant_id: result
            for result in results_by_project.get(test.project_id, [])
        }
        for hypothesis in assessment.hypotheses:
            if hypothesis.prediction == "unknown":
                continue
            for mutant in plan.mutants:
                if mutant.operator != hypothesis.fault_class or mutant.suspected_equivalent:
                    continue
                if mutant.impacted_record_keys and test.record_key not in mutant.impacted_record_keys:
                    continue
                if (
                    hypothesis.behavior_ids
                    and mutant.behavior_candidates
                    and not set(hypothesis.behavior_ids).intersection(mutant.behavior_candidates)
                ):
                    continue
                result = results.get(mutant.mutant_id)
                if result is None:
                    continue
                if test.record_key in result.killed_by_record_keys:
                    actual = "killed"
                elif test.record_key in result.survived_record_keys:
                    actual = "survived"
                else:
                    continue
                expected_actual = (
                    "killed" if hypothesis.prediction == "likely_detected" else "survived"
                )
                observations.append(
                    MutationCalibrationObservation(
                        record_key=test.record_key,
                        hypothesis_id=hypothesis.hypothesis_id,
                        mutant_id=mutant.mutant_id,
                        fault_class=hypothesis.fault_class,
                        prediction=hypothesis.prediction,
                        actual=actual,
                        matched=actual == expected_actual,
                    )
                )

    confusion = Counter(
        f"{item.prediction}__{item.actual}" for item in observations
    )
    grouped: dict[str, list[MutationCalibrationObservation]] = defaultdict(list)
    for item in observations:
        grouped[item.fault_class].append(item)
    by_fault_class: dict[str, dict[str, float | int | None]] = {}
    recommendations: list[MutationCalibrationRecommendation] = []
    for fault_class, items in sorted(grouped.items()):
        matched = sum(item.matched for item in items)
        overconfident = sum(
            item.prediction == "likely_detected" and item.actual == "survived"
            for item in items
        )
        underconfident = sum(
            item.prediction == "likely_survives" and item.actual == "killed"
            for item in items
        )
        by_fault_class[fault_class] = {
            "observations": len(items),
            "matched": matched,
            "accuracy": matched / len(items) if items else None,
        }
        if overconfident:
            recommendations.append(
                MutationCalibrationRecommendation(
                    fault_class=fault_class,  # type: ignore[arg-type]
                    issue="static_overconfidence",
                    observation_count=overconfident,
                    action=(
                        "Require a more direct or more specific assertion path before predicting "
                        "likely_detected for this generic fault class."
                    ),
                )
            )
        if underconfident:
            recommendations.append(
                MutationCalibrationRecommendation(
                    fault_class=fault_class,  # type: ignore[arg-type]
                    issue="static_underconfidence",
                    observation_count=underconfident,
                    action=(
                        "Recognize additional evidence-backed assertion paths before predicting "
                        "likely_survives for this generic fault class."
                    ),
                )
            )
    matched_count = sum(item.matched for item in observations)
    return MutationCalibrationReport(
        observation_count=len(observations),
        matched_count=matched_count,
        accuracy=matched_count / len(observations) if observations else None,
        confusion=dict(sorted(confusion.items())),
        by_fault_class=by_fault_class,
        observations=observations,
        recommendations=recommendations,
    )
