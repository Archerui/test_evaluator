"""Aggregate mutation outcomes without counting invalid/timeout mutants as survivors."""

from __future__ import annotations

from collections import Counter

from ..schemas import (
    MutationAnalysis,
    MutationAnalystInput,
    MutationAnalystOutput,
    MutationBehaviorSummary,
    Status,
)


def _score(results, excluded_ids: set[str] | None = None) -> float | None:
    excluded = excluded_ids or set()
    eligible = [result for result in results if result.mutant_id not in excluded]
    killed = sum(result.status == "killed" for result in eligible)
    survived = sum(result.status == "survived" for result in eligible)
    denominator = killed + survived
    return killed / denominator * 100.0 if denominator else None


def analyze_mutations(request: MutationAnalystInput) -> MutationAnalystOutput:
    results_by_id = {result.mutant_id: result for result in request.mutation_results}
    mutant_by_id = {mutant.mutant_id: mutant for mutant in request.mutation_plan.mutants}
    behavior_ids = [
        behavior.behavior_id
        for contract in request.contract_by_suite.values()
        for behavior in contract.behaviors
    ]
    if any(not mutant.behavior_candidates for mutant in request.mutation_plan.mutants):
        behavior_ids.append("__unmapped__")

    summaries: list[MutationBehaviorSummary] = []
    for behavior_id in dict.fromkeys(behavior_ids):
        mutants = [
            mutant
            for mutant in request.mutation_plan.mutants
            if behavior_id in mutant.behavior_candidates
            or (behavior_id == "__unmapped__" and not mutant.behavior_candidates)
        ]
        results = [results_by_id[item.mutant_id] for item in mutants if item.mutant_id in results_by_id]
        counts = Counter(result.status for result in results)
        survived_ids = [result.mutant_id for result in results if result.status == "survived"]
        suspected_equivalent = [
            mutant.mutant_id
            for mutant in mutants
            if mutant.suspected_equivalent and mutant.mutant_id in survived_ids
        ]
        score = _score(results, set(suspected_equivalent))
        valid_count = sum(
            result.status in {"killed", "survived"}
            and result.mutant_id not in suspected_equivalent
            for result in results
        )
        killed_for_score = sum(
            result.status == "killed" and result.mutant_id not in suspected_equivalent
            for result in results
        )
        summaries.append(
            MutationBehaviorSummary(
                behavior_id=behavior_id,
                total_mutants=len(mutants),
                killed=counts["killed"],
                survived=counts["survived"],
                timeout=counts["timeout"],
                invalid=counts["invalid"],
                mutation_score=score,
                survived_mutants=survived_ids,
                suspected_equivalent_mutants=suspected_equivalent,
                interpretation=(
                    "No valid mutant outcomes were available."
                    if score is None
                    else f"{killed_for_score} of {valid_count} non-equivalent valid mutants were killed."
                ),
            )
        )

    equivalent_ids = {
        mutant.mutant_id
        for mutant in request.mutation_plan.mutants
        if mutant.suspected_equivalent
        and results_by_id.get(mutant.mutant_id) is not None
        and results_by_id[mutant.mutant_id].status == "survived"
    }
    analysis_score = _score(request.mutation_results, equivalent_ids)
    survived_specs = [
        mutant_by_id[result.mutant_id]
        for result in request.mutation_results
        if result.status == "survived"
        and result.mutant_id in mutant_by_id
        and result.mutant_id not in equivalent_ids
    ][:10]
    analysis = MutationAnalysis(
        project_id=request.project_id,
        mutation_score=analysis_score,
        behavior_summaries=summaries,
        top_survived_mutants=survived_specs,
    )
    status = Status.PASS if analysis_score == 100.0 else Status.WARNING if analysis_score is not None else Status.UNKNOWN
    return MutationAnalystOutput(
        agent="mutation_analyst",
        run_id=request.run_id,
        mode="full",
        project_id=request.project_id,
        status=status,
        confidence=1.0 if analysis_score is not None else 0.0,
        warnings=[] if analysis_score is not None else ["No valid killed/survived mutation outcomes were available"],
        analysis=analysis,
    )
