from test_evaluator.reporting import render_markdown, render_project_markdown
from test_evaluator.schemas import (
    AgentReview,
    EvaluationRun,
    ProjectReport,
    RequirementReport,
    RunHealth,
    StaticFacts,
    Status,
    TestReport as Report,
)


def test_basic_report_exposes_dimension_and_evidence_unknowns() -> None:
    report = Report(
        record_key="Bench::1::1",
        project_id="Bench",
        requirement_id="1",
        test_id="1",
        scenario_type="Normal",
        confidence_coverage=0.65,
        basic_confidence_coverage=0.65,
        risk="medium",
        dimension_scores={
            "spec_alignment": 1.0,
            "step_traceability": 0.5,
            "oracle_strength": None,
            "robustness": 1.0,
        },
        static_facts=StaticFacts(python_parseable=True, scenario_present=True),
        reviews=[
            AgentReview(
                agent="bdd_traceability",
                record_key="Bench::1::1",
                dimension="spec_alignment",
                status=Status.PASS,
                confidence=0.9,
            ),
            AgentReview(
                agent="step_code",
                record_key="Bench::1::1",
                dimension="step_traceability",
                status=Status.WARNING,
                confidence=0.8,
            ),
            AgentReview(
                agent="oracle_critic",
                record_key="Bench::1::1",
                dimension="oracle_strength",
                status=Status.UNKNOWN,
                confidence=0.0,
            ),
            AgentReview(
                agent="static_verifier",
                record_key="Bench::1::1",
                dimension="robustness",
                status=Status.PASS,
                confidence=1.0,
            ),
        ],
    )
    requirement = RequirementReport(
        suite_key="Bench::1",
        project_id="Bench",
        requirement_id="1",
        test_count=1,
        basic_confidence_coverage=0.30,
    )
    run = EvaluationRun(
        mode="basic",
        tests=[report],
        requirements=[requirement],
        projects=[
            ProjectReport(
                project_id="Bench",
                test_count=1,
                requirement_count=1,
                unknown_rate=0.35,
                risk_counts={"medium": 1},
            )
        ],
        run_health=RunHealth(
            state_counts={"succeeded": 1},
            stage_durations_seconds={"BASIC_PARALLEL_REVIEWS": 1.25},
        ),
    )

    markdown = render_markdown(run)

    assert "## Basic Evaluation Details" in markdown
    assert "PASS (100)" in markdown
    assert "WARNING (50)" in markdown
    assert "Oracle strength" in markdown
    assert "| Bench::1::1 | Normal | N/A | 65% |" in markdown
    assert "| Bench::1 | 1 |  | N/A | 30% | False |" in markdown
    assert "Basic test scores require 70%" in markdown
    assert "Historical Trend" not in markdown
    assert markdown.index("## Test Results") < markdown.index("## Run Health")
    assert markdown.index("## Run Health") < markdown.index("## Basic Evaluation Details")
    assert markdown.index("## Interpretation") < markdown.index("## Stage Cost")
    assert markdown.rstrip().endswith("| BASIC_PARALLEL_REVIEWS | 1.25 |")

    project_markdown = render_project_markdown(run, "Bench")
    assert "| Test | Basic | Basic Evidence | Unknown dimensions | Risk |" in project_markdown
    assert "Full test quality" not in project_markdown
