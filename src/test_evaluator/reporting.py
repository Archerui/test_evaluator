"""Persist machine-readable and presentation-friendly evaluation reports."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

from .schemas import EvaluationRun, Finding


def write_reports(run: EvaluationRun, output_dir: str | Path) -> Path:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "evaluation.json").write_text(run.model_dump_json(indent=2), encoding="utf-8")
    (destination / "summary.md").write_text(render_markdown(run), encoding="utf-8")
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


def render_markdown(run: EvaluationRun) -> str:
    lines = [
        "# Test Evaluator Report",
        "",
        f"- Mode: `{run.mode}`",
        f"- Model: `{run.model or 'not used'}`",
        f"- Tests analysed: {len(run.tests)}",
        f"- Requirement suites analysed: {len(run.requirements)}",
        "",
        "## Project Summary",
        "",
            "| Project | Tests | Requirements | Test Quality | Requirement Adequacy | Unknown Rate | Risks |",
            "|---|---:|---:|---:|---:|---:|---|",
    ]
    for project in run.projects:
        risks = ", ".join(f"{kind}: {count}" for kind, count in project.risk_counts.items()) or "none"
        lines.append(
            "| "
            f"{project.project_id} | {project.test_count} | {project.requirement_count} | "
            f"{_format_score(project.average_test_quality_score)} | "
            f"{_format_score(project.average_requirement_adequacy_score)} | "
            f"{project.unknown_rate:.0%} | {risks} |"
        )

    if run.runtime_warnings:
        lines.extend(["", "## Runtime Warnings", ""])
        lines.extend(f"- {warning}" for warning in run.runtime_warnings)

    lines.extend(
        [
            "",
            "## Test Results",
            "",
            "| Test | Scenario | Test Quality | Evidence Coverage | Risk | Hard Gates |",
            "|---|---|---:|---:|---|---|",
        ]
    )
    for report in run.tests:
        hard_gates = ", ".join(report.hard_gates) or "—"
        lines.append(
            f"| {report.record_key} | {report.scenario_type or 'Unlabelled'} | "
            f"{_format_score(report.test_quality_score)} | {report.confidence_coverage:.0%} | "
            f"{report.risk} | {hard_gates} |"
        )

    lines.extend(
        [
            "",
            "## Requirement Suites",
            "",
            "| Suite | Tests | Scenario types | Adequacy | Partial input |",
            "|---|---:|---|---:|---|",
        ]
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
    for requirement in run.requirements:
        distribution = ", ".join(f"{kind}: {count}" for kind, count in requirement.scenario_distribution.items())
        lines.append(
            f"| {requirement.suite_key} | {requirement.test_count} | {distribution} | "
            f"{_format_score(requirement.requirement_adequacy_score)} | {requirement.partial_suite} |"
        )

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
            "This static/LLM report is not an execution pass rate, coverage result, or mutation score.",
            "",
        ]
    )
    return "\n".join(lines)
