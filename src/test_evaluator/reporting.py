"""Persist machine-readable and presentation-friendly evaluation reports."""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path

from .schemas import EvaluationRun, Finding


def write_reports(run: EvaluationRun, output_dir: str | Path) -> Path:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "evaluation.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    (destination / "summary.md").write_text(render_markdown(run), encoding="utf-8")
    (destination / "config.json").write_text(
        json.dumps(run.config, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    (destination / "inventory.json").write_text(
        json.dumps([item.model_dump(mode="json") for item in run.inventories], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for project in run.projects:
        project_dir = destination / "projects" / project.project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        (project_dir / "project_summary.md").write_text(
            render_project_markdown(run, project.project_id),
            encoding="utf-8",
        )
    return destination


def _format_score(score: float | None) -> str:
    return "N/A" if score is None else f"{score:.1f}"


def _high_risk_findings(run: EvaluationRun) -> list[tuple[str, str, Finding]]:
    selected: list[tuple[str, str, Finding]] = []
    for report in run.tests:
        for review in report.reviews:
            for finding in review.findings:
                if finding.severity.value in {"critical", "major"} and finding.status.value != "PASS":
                    selected.append((report.record_key, review.agent, finding))
    return selected


def _review_status(report, agent: str) -> str:
    review = next((item for item in report.reviews if item.agent == agent), None)
    return review.status.value if review else "N/A"


def _dynamic_behavior_summary(requirement) -> str:
    if not requirement.dynamic_behavior_coverage:
        return "N/A"
    counts = Counter(item.status.value for item in requirement.dynamic_behavior_coverage)
    return ", ".join(f"{status}: {count}" for status, count in sorted(counts.items()))


def _stability_summary(report) -> str:
    if report.stability is None:
        return "N/A"
    rate = f"{report.stability.pass_rate:.0%}" if report.stability.pass_rate is not None else "N/A"
    return f"{report.stability.status.value} ({rate})"


def render_project_markdown(run: EvaluationRun, project_id: str) -> str:
    project = next(item for item in run.projects if item.project_id == project_id)
    tests = [item for item in run.tests if item.project_id == project_id]
    requirements = [item for item in run.requirements if item.project_id == project_id]
    lines = [
        f"# {project_id}",
        "",
        f"- Tests: {len(tests)}",
        f"- Requirement suites: {len(requirements)}",
        f"- Basic test quality: {_format_score(project.average_basic_test_quality_score)}",
        f"- Full test quality: {_format_score(project.average_full_test_quality_score)}",
        f"- Requirement adequacy: {_format_score(project.average_requirement_adequacy_score)}",
        f"- Runtime pass rate: {f'{project.runtime_pass_rate:.0%}' if project.runtime_pass_rate is not None else 'N/A'}",
        f"- Mutation score: {_format_score(project.mutation_score)}",
        "",
        "## Tests",
        "",
        "| Test | Basic | Full | Runtime | Stability | Dynamic Oracle | Mutation | Risk |",
        "|---|---:|---:|---|---|---|---:|---|",
    ]
    for report in tests:
        lines.append(
            f"| {report.record_key} | {_format_score(report.basic_test_quality_score)} | "
            f"{_format_score(report.full_test_quality_score)} | "
            f"{report.runtime.status if report.runtime else 'N/A'} | "
            f"{_stability_summary(report)} | "
            f"{_review_status(report, 'dynamic_oracle')} | "
            f"{_format_score(report.mutation_score)} | {report.risk} |"
        )

    lines.append("")
    return "\n".join(lines)


def render_markdown(run: EvaluationRun) -> str:
    lines = [
        "# Test Evaluator Report",
        "",
        f"- Run ID: `{run.run_id or 'not recorded'}`",
        f"- Mode: `{run.mode}`",
        f"- Semantic agents: `{run.semantic_mode}`",
        f"- Model: `{run.model or 'not used'}`",
        f"- Tests analysed: {len(run.tests)}",
        f"- Requirement suites analysed: {len(run.requirements)}",
        "",
        "## Project Summary",
        "",
        "| Project | Tests | Requirements | Basic Test Quality | Full Test Quality | Requirement Adequacy | Runtime Pass | Mutation | Unknown Rate | Risks |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for project in run.projects:
        risks = ", ".join(f"{kind}: {count}" for kind, count in project.risk_counts.items()) or "none"
        runtime_pass = f"{project.runtime_pass_rate:.0%}" if project.runtime_pass_rate is not None else "N/A"
        lines.append(
            "| "
            f"{project.project_id} | {project.test_count} | {project.requirement_count} | "
            f"{_format_score(project.average_basic_test_quality_score)} | "
            f"{_format_score(project.average_full_test_quality_score)} | "
            f"{_format_score(project.average_requirement_adequacy_score)} | "
            f"{runtime_pass} | "
            f"{_format_score(project.mutation_score)} | "
            f"{project.unknown_rate:.0%} | {risks} |"
        )

    if run.trend:
        lines.extend(["", "## Historical Trend", ""])
        if run.trend.previous_run_id:
            lines.append(f"Compared with run `{run.trend.previous_run_id}`.")
            lines.extend(["", "| Metric | Current | Delta |", "|---|---:|---:|"])
            for name, value in run.trend.current.metrics.items():
                delta = run.trend.deltas.get(name)
                current_text = "N/A" if value is None else f"{value:.2f}"
                delta_text = "N/A" if delta is None else f"{delta:+.2f}"
                lines.append(f"| {name} | {current_text} | {delta_text} |")
        else:
            lines.append("No previous compatible run exists yet; this run is the trend baseline.")

    if run.runtime_warnings:
        lines.extend(["", "## Runtime Warnings", ""])
        lines.extend(f"- {warning}" for warning in run.runtime_warnings)

    if run.run_health:
        state_counts = ", ".join(
            f"{status}: {count}" for status, count in run.run_health.state_counts.items()
        ) or "none"
        lines.extend(
            [
                "",
                "## Run Health",
                "",
                f"- States: {state_counts}",
                f"- Cache hits: {run.run_health.cache_hits}",
                f"- Cache misses: {run.run_health.cache_misses}",
                f"- Resume used: {run.run_health.resume_used}",
                f"- Baseline runtime: {run.run_health.runtime_counts or 'none'}",
                f"- Mutation outcomes: {run.run_health.mutation_counts or 'none'}",
                f"- Flaky tests: {run.run_health.flaky_test_count}",
                f"- Baseline runtime seconds: {run.run_health.total_runtime_seconds:.2f}",
            ]
        )
        if run.run_health.degraded_reasons:
            lines.append("- Degraded stages:")
            lines.extend(f"  - {reason}" for reason in run.run_health.degraded_reasons)
        if run.run_health.failed_reasons:
            lines.append("- Failed stages:")
            lines.extend(f"  - {reason}" for reason in run.run_health.failed_reasons)
        measured = [
            (state, seconds)
            for state, seconds in run.run_health.stage_durations_seconds.items()
            if seconds > 0
        ]
        if measured:
            lines.extend(["", "### Stage Cost", "", "| Stage | Seconds |", "|---|---:|"])
            lines.extend(
                f"| {state} | {seconds:.2f} |"
                for state, seconds in sorted(measured, key=lambda item: item[1], reverse=True)
            )

    lines.extend(
        [
            "",
            "## Test Results",
            "",
            "| Test | Scenario | Basic Score | Full Score | Source Grounding | Runtime | Stability | Dynamic Oracle | Mutation | Evidence Coverage | Risk | Hard Gates |",
            "|---|---|---:|---:|---|---|---|---|---:|---:|---|---|",
        ]
    )
    for report in run.tests:
        hard_gates = ", ".join(report.hard_gates) or "—"
        lines.append(
            f"| {report.record_key} | {report.scenario_type or 'Unlabelled'} | "
            f"{_format_score(report.basic_test_quality_score)} | "
            f"{_format_score(report.full_test_quality_score)} | "
            f"{_review_status(report, 'selector_grounding')} | "
            f"{report.runtime.status if report.runtime else 'N/A'} | "
            f"{_stability_summary(report)} | "
            f"{_review_status(report, 'dynamic_oracle')} | {_format_score(report.mutation_score)} | "
            f"{report.confidence_coverage:.0%} | "
            f"{report.risk} | {hard_gates} |"
        )

    runtime_reports = [report for report in run.tests if report.runtime is not None]
    if runtime_reports:
        lines.extend(
            [
                "",
                "## Baseline Runtime Details",
                "",
                "`env_error` means the runtime dependency/browser setup was unavailable; it is not a failed test assertion.",
                "",
                "| Test | Status | Error type | Failed step | Duration (s) |",
                "|---|---|---|---|---:|",
            ]
        )
        for report in runtime_reports:
            runtime = report.runtime
            lines.append(
                f"| {report.record_key} | {runtime.status} | {runtime.error_type or '—'} | "
                f"{runtime.failed_step or '—'} | "
                f"{runtime.duration_seconds:.2f} |" if runtime.duration_seconds is not None else
                f"| {report.record_key} | {runtime.status} | {runtime.error_type or '—'} | "
                f"{runtime.failed_step or '—'} | N/A |"
            )

    lines.extend(
        [
            "",
            "## Requirement Suites",
            "",
            "| Suite | Tests | Scenario types | Basic Adequacy | Full Adequacy | Runtime Pass | Flaky | Dynamic Behaviors | Mutation | Partial input |",
            "|---|---:|---|---:|---:|---:|---:|---|---:|---|",
        ]
    )
    for requirement in run.requirements:
        distribution = ", ".join(f"{kind}: {count}" for kind, count in requirement.scenario_distribution.items())
        runtime_pass = (
            f"{requirement.runtime_pass_rate:.0%}"
            if requirement.runtime_pass_rate is not None
            else "N/A"
        )
        lines.append(
            f"| {requirement.suite_key} | {requirement.test_count} | {distribution} | "
            f"{_format_score(requirement.basic_requirement_adequacy_score)} | "
            f"{_format_score(requirement.full_requirement_adequacy_score)} | {runtime_pass} | "
            f"{requirement.flaky_test_count} | "
            f"{_dynamic_behavior_summary(requirement)} | "
            f"{_format_score(requirement.mutation_score)} | "
            f"{requirement.partial_suite} |"
        )

    repeated = [
        report for report in run.tests if report.stability and report.stability.requested_runs > 1
    ]
    if repeated:
        lines.extend(
            [
                "",
                "## Stability Runs",
                "",
                "| Test | Runs completed/requested | Pass rate | Flaky | Outcomes |",
                "|---|---:|---:|---|---|",
            ]
        )
        for report in repeated:
            stability = report.stability
            outcomes = ", ".join(attempt.status for attempt in stability.attempts)
            rate = f"{stability.pass_rate:.0%}" if stability.pass_rate is not None else "N/A"
            lines.append(
                f"| {report.record_key} | {stability.completed_runs}/{stability.requested_runs} | "
                f"{rate} | {stability.flaky} | {outcomes} |"
            )

    dynamic_requirements = [
        requirement for requirement in run.requirements if requirement.dynamic_behavior_coverage
    ]
    if dynamic_requirements:
        lines.extend(
            [
                "",
                "## Dynamic Evidence Feedback",
                "",
                "This layer feeds runtime, selector grounding, and mutation outcomes back into Oracle/Suite reviews. It is explanatory evidence and is not added as another score weight.",
                "",
                "| Suite | Behavior | Status | Runtime-confirmed tests | Killed mutants | Survived mutants |",
                "|---|---|---|---:|---:|---:|",
            ]
        )
        for requirement in dynamic_requirements:
            for behavior in requirement.dynamic_behavior_coverage:
                lines.append(
                    f"| {requirement.suite_key} | {behavior.behavior_id} | {behavior.status.value} | "
                    f"{len(behavior.runtime_confirmed_by_records)} | "
                    f"{len(behavior.killed_by_mutants)} | {len(behavior.survived_mutants)} |"
                )

    if run.mutation_analyses:
        lines.extend(["", "## Real Mutation Testing", ""])
        for project_id, analysis in sorted(run.mutation_analyses.items()):
            lines.extend(
                [
                    f"### `{project_id}`",
                    "",
                    f"- Mutation score: {_format_score(analysis.mutation_score)}",
                    f"- Top survived mutants: {len(analysis.top_survived_mutants)}",
                ]
            )
            for mutant in analysis.top_survived_mutants:
                lines.append(
                    f"  - `{mutant.mutant_id}` — {mutant.operator} at `{mutant.file_path}:{mutant.line_start or '?'}`"
                )

    mutation_readiness = [report for report in run.tests if report.mutation_readiness is not None]
    if mutation_readiness:
        lines.extend(
            [
                "",
                "## Mutation Readiness (Static Estimate)",
                "",
                "This is a requirement/oracle-based hypothesis, not a mutation score. No application code was mutated or executed.",
                "",
                "| Test | Mutation readiness |",
                "|---|---:|",
            ]
        )
        for report in mutation_readiness:
            lines.append(f"| {report.record_key} | {_format_score(report.mutation_readiness)} |")

    high_risk = _high_risk_findings(run)
    lines.extend(["", "## Major and Critical Findings", ""])
    if not high_risk:
        lines.append("No major or critical evidence-backed findings were produced.")
    else:
        for record_key, agent, finding in high_risk:
            quote = finding.evidence[0].quote if finding.evidence else "No source evidence was returned."
            lines.extend(
                [
                    f"### `{record_key}` — {agent}",
                    "",
                    f"- **{finding.severity.value} / {finding.status.value}**: {finding.criterion}",
                    f"- Evidence: `{quote}`",
                    f"- Reason: {finding.reasoning}",
                    f"- Suggested fix: {finding.suggested_fix or 'Manual review required.'}",
                    "",
                ]
            )

    score_count = Counter("available" if report.test_quality_score is not None else "unavailable" for report in run.tests)
    lines.extend(
        [
            "## Interpretation",
            "",
            f"Test quality scores: {score_count['available']} available, {score_count['unavailable']} unavailable.",
            "`N/A` means fewer than half of the weighted rubric had evidence; it is not a passing result.",
            (
                "Full scores use the proposal's BDD, step, oracle, runtime, mutation, and robustness weights. "
                "Source grounding, optional CDP coverage, and dynamic evidence feedback remain explicit supporting evidence rather than hidden score inputs."
            ),
            "",
        ]
    )
    return "\n".join(lines)
