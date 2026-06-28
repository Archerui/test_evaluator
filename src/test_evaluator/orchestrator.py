"""Fixed multi-agent orchestration for the proposal's v0 pipeline."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path

from .agents import (
    build_requirement_contract,
    review_bdd,
    review_mutation_hypothesis,
    review_oracle,
    review_step_code,
    review_suite,
)
from .ingest import TestRecord, group_by_suite, load_records
from .llm import OpenAIJsonAgent
from .reporting import write_reports
from .schemas import (
    AgentReview,
    EvaluationRun,
    RequirementContract,
    Severity,
    Status,
    SuiteAssessment,
)
from .scoring import build_run, coordinate_requirement, coordinate_test, unknown_review
from .static_verifier import extract_static_facts, static_review


@dataclass(frozen=True)
class EvaluationConfig:
    input_path: Path
    output_dir: Path
    live: bool = False
    model: str = "gpt-5-mini"
    limit: int | None = None
    max_output_tokens: int = 4_000
    timeout_seconds: float = 45.0
    mutation_hypotheses: bool = False


def _fallback_contract(record: TestRecord) -> RequirementContract:
    return RequirementContract(
        project_id=record.project_id,
        requirement_id=record.requirement_id,
        behaviors=[],
    )


def _agent_failure_review(agent: str, record_key: str, dimension: str, error: Exception) -> AgentReview:
    review = unknown_review(agent, record_key, dimension)
    # The exception is intentionally not copied to reports: provider errors can
    # contain operational details that are not evidence about the candidate test.
    return review.model_copy(update={"confidence": 0.0})


def _suite_failure_assessment(suite_key: str) -> SuiteAssessment:
    return SuiteAssessment(
        review=AgentReview(
            agent="suite_coverage",
            suite_key=suite_key,
            dimension="suite_adequacy",
            status=Status.UNKNOWN,
            confidence=0.0,
            findings=[],
        ),
        behavior_coverage={},
    )


def _offline_reviews(record: TestRecord) -> list[AgentReview]:
    return [
        unknown_review("bdd_traceability", record.record_key, "spec_alignment"),
        unknown_review("step_code", record.record_key, "step_traceability"),
        unknown_review("oracle_critic", record.record_key, "oracle_strength"),
    ]


def evaluate_csv(config: EvaluationConfig) -> EvaluationRun:
    """Evaluate CSV records and write JSON plus Markdown reports.

    In offline mode only deterministic checks run. In live mode an OpenAI client
    is created without reading the credential itself; the client resolves
    OPENAI_API_KEY internally.
    """

    all_records = load_records(config.input_path)
    records = all_records[: config.limit] if config.limit is not None else all_records
    if not records:
        raise ValueError("No records selected for evaluation.")

    all_suites = group_by_suite(all_records)
    selected_suites = group_by_suite(records)
    llm = OpenAIJsonAgent(config.model, config.max_output_tokens, config.timeout_seconds) if config.live else None
    contracts: dict[str, RequirementContract] = {}
    runtime_warnings: list[str] = []

    if llm:
        for suite_key, suite_records in selected_suites.items():
            try:
                contracts[suite_key] = build_requirement_contract(llm, suite_records[0])
            except Exception:
                contracts[suite_key] = _fallback_contract(suite_records[0])
                runtime_warnings.append(
                    f"Requirement Agent returned no valid structured contract for {suite_key}; dependent semantic reviews were skipped."
                )
    else:
        contracts = {suite_key: _fallback_contract(suite_records[0]) for suite_key, suite_records in selected_suites.items()}

    test_reports = []
    for record in records:
        facts = extract_static_facts(record)
        reviews = [static_review(record, facts)]
        if llm and contracts[record.suite_key].behaviors:
            tasks = (
                ("bdd_traceability", "spec_alignment", review_bdd),
                ("step_code", "step_traceability", review_step_code),
                ("oracle_critic", "oracle_strength", review_oracle),
            )
            concurrent_reviews: dict[str, AgentReview] = {}
            with ThreadPoolExecutor(max_workers=len(tasks), thread_name_prefix="test-evaluator") as pool:
                futures = {
                    pool.submit(invoke, llm, record, contracts[record.suite_key], facts): (agent_name, dimension)
                    for agent_name, dimension, invoke in tasks
                }
                for future in as_completed(futures):
                    agent_name, dimension = futures[future]
                    try:
                        concurrent_reviews[agent_name] = future.result()
                    except Exception as error:
                        concurrent_reviews[agent_name] = _agent_failure_review(agent_name, record.record_key, dimension, error)
                        runtime_warnings.append(
                            f"{agent_name} returned no valid structured review for {record.record_key}; the dimension is UNKNOWN."
                        )
            # Preserve a stable report order irrespective of API completion time.
            reviews.extend(concurrent_reviews[agent_name] for agent_name, _, _ in tasks)
            if config.mutation_hypotheses:
                try:
                    reviews.append(review_mutation_hypothesis(llm, record, contracts[record.suite_key], facts))
                except Exception as error:
                    reviews.append(_agent_failure_review("mutation_hypothesis", record.record_key, "mutation_readiness", error))
                    runtime_warnings.append(
                        f"mutation_hypothesis returned no valid structured review for {record.record_key}; mutation readiness is UNKNOWN."
                    )
        else:
            reviews.extend(_offline_reviews(record))
        test_reports.append(coordinate_test(record, facts, reviews))

    requirement_reports = []
    for suite_key, suite_records in selected_suites.items():
        partial_suite = len(suite_records) != len(all_suites[suite_key])
        assessment: SuiteAssessment | None = None
        if llm and contracts[suite_key].behaviors:
            try:
                assessment = review_suite(llm, suite_key, suite_records, contracts[suite_key])
            except Exception:
                assessment = _suite_failure_assessment(suite_key)
                runtime_warnings.append(
                    f"Suite Coverage Agent returned no valid structured review for {suite_key}; requirement adequacy has reduced confidence."
                )
        suite_tests = [report for report in test_reports if report.record_key in {record.record_key for record in suite_records}]
        requirement_reports.append(
            coordinate_requirement(suite_key, suite_records, suite_tests, assessment, partial_suite)
        )

    run = build_run(
        mode="live" if config.live else "offline",
        model=config.model if config.live else None,
        tests=test_reports,
        requirements=requirement_reports,
        runtime_warnings=runtime_warnings,
    )
    write_reports(run, config.output_dir)
    return run
