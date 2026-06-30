"""Checkpointed multi-agent orchestration for basic and full evaluation modes."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import time
from typing import Callable

from .agents import (
    build_requirement_contract,
    review_bdd,
    review_mutation_hypothesis,
    review_oracle,
    review_step_code,
    review_suite,
)
from .dataset import discover_project_inventories, load_inventory_records, load_inventory_semantic_context
from .dynamic_evidence import analyze_dynamic_oracle, analyze_dynamic_suite_coverage
from .coverage import collect_coverage
from .grounding import ground_selectors
from .ingest import TestRecord, group_by_suite, load_records
from .llm import OpenAIJsonAgent
from .materializer import materialize_test
from .mutation import analyze_mutations, generate_mutation_plan, run_mutant
from .mutation_calibration import calibrate_static_mutation
from .reporting import write_reports
from .runner import run_baseline_test
from .schemas import (
    AgentReview,
    ArtifactRef,
    CoverageInput,
    CoverageOutput,
    CoverageReport,
    DynamicOracleInput,
    DynamicOracleOutput,
    DynamicSuiteCoverageInput,
    DynamicSuiteCoverageOutput,
    EvaluationRun,
    MutationAnalysis,
    MutationAnalystInput,
    MutationGeneratorInput,
    MutationPlan,
    MutationRunResult,
    MutationRunnerInput,
    MutantSpec,
    ProjectInventory,
    RequirementContract,
    RuntimeResult,
    RuntimeTrace,
    RuntimeTraceInput,
    RuntimeTraceOutput,
    SelectorGroundingInput,
    SelectorGroundingOutput,
    SourceModel,
    SourceModelInput,
    StabilityReport,
    StaticFacts,
    Status,
    SuiteAssessment,
    TestMaterializerInput,
    TestRunnerInput,
    WorkspaceSpec,
)
from .scoring import (
    attach_coverage_results,
    attach_dynamic_evidence,
    attach_mutation_results,
    attach_runtime_results,
    attach_runtime_traces,
    attach_source_grounding,
    attach_stability_results,
    build_run,
    coordinate_full_scores,
    coordinate_requirement,
    coordinate_test,
    unknown_review,
)
from .source_model import build_source_model
from .stability import analyze_stability
from .runtime_trace import trace_runtime
from .state_machine import OrchestratorStateStore, file_hash, stable_hash
from .static_verifier import extract_static_facts, static_review
from .static_mutation import assess_static_mutation
from .suite_analysis import analyze_static_behavior_coverage, analyze_suite_duplicates


PIPELINE_VERSION = "1.3.0"


def _progress(config: "EvaluationConfig", state: str, completed: int, total: int) -> None:
    if config.progress:
        print(f"... [{state}] {completed}/{total}", flush=True)


def _impacted_record_keys(
    mutant: MutantSpec,
    records: list[TestRecord],
    contracts: dict[str, RequirementContract],
) -> list[str]:
    """Select requirement-local tests when a mutant has behavior grounding.

    Grounding is deliberately conservative: an unmapped mutant, or a behavior
    ID that cannot be resolved to a suite, falls back to every selected test in
    the project so mutation effectiveness is never overstated by under-testing.
    """

    project_records = [record for record in records if record.project_id == mutant.project_id]
    if not mutant.behavior_candidates:
        return [record.record_key for record in project_records]
    behavior_ids = set(mutant.behavior_candidates)
    suites = {
        suite_key
        for suite_key, contract in contracts.items()
        if contract.project_id == mutant.project_id
        and behavior_ids.intersection(behavior.behavior_id for behavior in contract.behaviors)
    }
    if not suites:
        return [record.record_key for record in project_records]
    return [record.record_key for record in project_records if record.suite_key in suites]


@dataclass(frozen=True)
class EvaluationConfig:
    input_path: Path | None = Path("e2edev_sample.csv")
    output_dir: Path = Path("reports/latest")
    mode: str = "basic"
    e2edev_root: Path | None = None
    projects: tuple[str, ...] = ()
    requirements: tuple[str, ...] = ()
    tests: tuple[str, ...] = ()
    max_projects: int | None = None
    workers: int = 2
    live: bool = False
    model: str = "gpt-5-mini"
    limit: int | None = None
    max_tests_per_project: int | None = None
    max_output_tokens: int = 4_000
    timeout_seconds: float = 45.0
    llm_cache: bool = True
    runner_timeout_seconds: float = 60.0
    headless: bool = True
    runtime_retries: int = 1
    stability_runs: int = 1
    runtime_budget_seconds: float | None = None
    mutation: bool = False
    max_mutants: int = 30
    max_mutants_per_project: int = 30
    mutation_budget_seconds: float | None = None
    mutation_operators: tuple[str, ...] = ()
    coverage: bool = False
    coverage_method: str = "auto"
    browser_stubs: tuple[str, ...] = ()
    mutation_hypotheses: bool = False
    resume: bool = False
    progress: bool = False

    def manifest_config(self) -> dict[str, object]:
        payload = asdict(self)
        payload["input_path"] = str(self.input_path) if self.input_path else None
        payload["output_dir"] = str(self.output_dir)
        payload["e2edev_root"] = str(self.e2edev_root) if self.e2edev_root else None
        payload["projects"] = list(self.projects)
        payload["requirements"] = list(self.requirements)
        payload["tests"] = list(self.tests)
        payload["mutation_operators"] = list(self.mutation_operators)
        payload["browser_stubs"] = list(self.browser_stubs)
        payload["pipeline_version"] = PIPELINE_VERSION
        payload.pop("resume", None)
        payload.pop("progress", None)
        return payload


def _fallback_contract(record: TestRecord) -> RequirementContract:
    return RequirementContract(
        project_id=record.project_id,
        requirement_id=record.requirement_id,
        suite_key=record.suite_key,
        behaviors=[],
    )


def _agent_failure_review(agent: str, record_key: str, dimension: str) -> AgentReview:
    review = unknown_review(agent, record_key, dimension)
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


def _state_payload(
    store: OrchestratorStateStore,
    state: str,
    input_hash: str,
    operation: Callable[[], dict[str, object]],
    *,
    recoverable: bool = False,
    retries: int = 0,
    degraded_reason: Callable[[dict[str, object]], str | None] | None = None,
    cached_validator: Callable[[dict[str, object]], bool] | None = None,
) -> dict[str, object]:
    cached = store.cached_payload(state, input_hash)  # type: ignore[arg-type]
    if cached is not None and (cached_validator is None or cached_validator(cached)):
        return cached
    if cached is not None:
        store.cache_hits -= 1
        store.cache_misses += 1

    last_error: Exception | None = None
    for attempt in range(retries + 1):
        store.start(state, input_hash)  # type: ignore[arg-type]
        try:
            payload = operation()
            warning = degraded_reason(payload) if degraded_reason else None
            store.succeed(  # type: ignore[arg-type]
                state,
                payload,
                status="degraded" if warning else "succeeded",
                warning=warning,
            )
            return payload
        except Exception as error:
            last_error = error
            store.fail(state, error, recoverable=recoverable or attempt < retries)  # type: ignore[arg-type]
            if attempt >= retries:
                raise
    raise RuntimeError(f"State {state} failed unexpectedly") from last_error


def _input_signature(config: EvaluationConfig) -> str:
    if config.e2edev_root:
        root = config.e2edev_root.resolve()
        candidates = sorted(root.rglob("requirment_with_tests.json"))
        if config.projects:
            selected = set(config.projects)
            candidates = [path for path in candidates if path.parent.name in selected]
        return stable_hash(
            [
                {
                    "path": str(path),
                    "size": path.stat().st_size,
                    "sha256": file_hash(path),
                }
                for path in candidates
            ]
        )
    if config.input_path is None:
        return stable_hash({"input": None})
    return file_hash(config.input_path)


def _csv_inventories(records: list[TestRecord], input_path: Path | None) -> list[ProjectInventory]:
    inventories: list[ProjectInventory] = []
    for project_id in sorted({record.project_id for record in records}):
        project_records = [record for record in records if record.project_id == project_id]
        inventories.append(
            ProjectInventory(
                project_id=project_id,
                tests_file=str(input_path.resolve()) if input_path else None,
                test_count=len(project_records),
                requirement_count=len({record.requirement_id for record in project_records}),
                discovery_status=Status.PASS,
                warnings=["CSV-only input: application source was not discovered."],
            )
        )
    return inventories


def _select_records(records: list[TestRecord], config: EvaluationConfig) -> list[TestRecord]:
    selected = records
    if config.requirements:
        requested = set(config.requirements)
        selected = [
            record
            for record in selected
            if record.requirement_id in requested or record.suite_key in requested
        ]
        matched = {value for value in requested if any(
            record.requirement_id == value or record.suite_key == value for record in records
        )}
        missing = requested.difference(matched)
        if missing:
            raise ValueError(f"Requested requirements were not found: {', '.join(sorted(missing))}")
    if config.tests:
        requested = set(config.tests)
        before_test_filter = selected
        selected = [
            record
            for record in selected
            if record.test_id in requested or record.record_key in requested
        ]
        matched = {value for value in requested if any(
            record.test_id == value or record.record_key == value for record in before_test_filter
        )}
        missing = requested.difference(matched)
        if missing:
            raise ValueError(f"Requested tests were not found in the selected requirements: {', '.join(sorted(missing))}")
    return selected


def _source_signature(inventories: list[ProjectInventory]) -> str:
    files: list[dict[str, object]] = []
    for inventory in inventories:
        if not inventory.source_root:
            files.append({"project_id": inventory.project_id, "source_root": None})
            continue
        root = Path(inventory.source_root)
        for relative in sorted(set(inventory.source_files + inventory.asset_files)):
            path = root / relative
            if path.is_file():
                stat = path.stat()
                files.append(
                    {
                        "project_id": inventory.project_id,
                        "path": relative,
                        "size": stat.st_size,
                        "sha256": file_hash(path),
                    }
                )
    return stable_hash(files)


def _write_runtime_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    runtime_by_record: dict[str, RuntimeResult],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        project_dir = output_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        destination = project_dir / "runtime_results.json"
        project_keys = {record.record_key for record in records if record.project_id == project_id}
        payload = {
            record_key: runtime.model_dump(mode="json")
            for record_key, runtime in runtime_by_record.items()
            if record_key in project_keys
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="runtime_result",
                path=str(destination),
                description=f"Baseline runtime results for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_stability_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    reports: dict[str, StabilityReport],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        destination = output_dir / "projects" / project_id / "stability_results.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        keys = {record.record_key for record in records if record.project_id == project_id}
        payload = {
            record_key: report.model_dump(mode="json")
            for record_key, report in reports.items()
            if record_key in keys
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="stability_report",
                path=str(destination),
                description=f"Repeated-run stability results for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_source_model_artifacts(
    output_dir: Path,
    models: dict[str, SourceModel],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id, model in sorted(models.items()):
        project_dir = output_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        destination = project_dir / "source_model.json"
        destination.write_text(model.model_dump_json(indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="source_model",
                path=str(destination),
                description=f"Static source model for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_grounding_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    outputs: dict[str, SelectorGroundingOutput],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        project_dir = output_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        destination = project_dir / "selector_grounding.json"
        project_keys = {record.record_key for record in records if record.project_id == project_id}
        payload = {
            record_key: output.model_dump(mode="json")
            for record_key, output in outputs.items()
            if record_key in project_keys
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="selector_grounding",
                path=str(destination),
                description=f"Selector grounding results for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_mutation_artifacts(
    output_dir: Path,
    plans: dict[str, MutationPlan],
    results: dict[str, list[MutationRunResult]],
    analyses: dict[str, MutationAnalysis],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    project_ids = sorted(set(plans) | set(results) | set(analyses))
    for project_id in project_ids:
        project_dir = output_dir / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        plan_path = project_dir / "mutation_plan.json"
        results_path = project_dir / "mutation_results.json"
        plan = plans.get(project_id, MutationPlan(project_id=project_id))
        plan_path.write_text(plan.model_dump_json(indent=2), encoding="utf-8")
        payload = {
            "project_id": project_id,
            "results": [item.model_dump(mode="json") for item in results.get(project_id, [])],
            "analysis": analyses[project_id].model_dump(mode="json") if project_id in analyses else None,
        }
        results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.extend(
            [
                ArtifactRef(
                    kind="mutation_result",
                    path=str(plan_path),
                    description=f"Mutation plan for {project_id}",
                    sha256=file_hash(plan_path),
                ),
                ArtifactRef(
                    kind="mutation_result",
                    path=str(results_path),
                    description=f"Mutation outcomes and analysis for {project_id}",
                    sha256=file_hash(results_path),
                ),
            ]
        )
    return artifacts


def _write_runtime_trace_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    traces: dict[str, RuntimeTrace],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        destination = output_dir / "projects" / project_id / "runtime_traces.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        keys = {record.record_key for record in records if record.project_id == project_id}
        payload = {
            record_key: trace.model_dump(mode="json")
            for record_key, trace in traces.items()
            if record_key in keys
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="runtime_trace",
                path=str(destination),
                description=f"Runtime trace analysis for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_coverage_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    reports: dict[str, CoverageReport],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        destination = output_dir / "projects" / project_id / "coverage.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        keys = {record.record_key for record in records if record.project_id == project_id}
        payload = {
            record_key: report.model_dump(mode="json")
            for record_key, report in reports.items()
            if record_key in keys
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="coverage",
                path=str(destination),
                description=f"Normalized CDP coverage for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def _write_dynamic_evidence_artifacts(
    output_dir: Path,
    records: list[TestRecord],
    test_outputs: dict[str, DynamicOracleOutput],
    suite_outputs: dict[str, DynamicSuiteCoverageOutput],
) -> list[ArtifactRef]:
    artifacts: list[ArtifactRef] = []
    for project_id in sorted({record.project_id for record in records}):
        destination = output_dir / "projects" / project_id / "dynamic_evidence.json"
        destination.parent.mkdir(parents=True, exist_ok=True)
        record_keys = {record.record_key for record in records if record.project_id == project_id}
        suite_keys = {record.suite_key for record in records if record.project_id == project_id}
        payload = {
            "project_id": project_id,
            "tests": {
                record_key: output.model_dump(mode="json")
                for record_key, output in test_outputs.items()
                if record_key in record_keys
            },
            "requirements": {
                suite_key: output.model_dump(mode="json")
                for suite_key, output in suite_outputs.items()
                if suite_key in suite_keys
            },
        }
        destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        artifacts.append(
            ArtifactRef(
                kind="dynamic_evidence",
                path=str(destination),
                description=f"Dynamic oracle and behavior evidence for {project_id}",
                sha256=file_hash(destination),
            )
        )
    return artifacts


def evaluate(config: EvaluationConfig) -> EvaluationRun:
    """Evaluate selected records with checkpointing and resumable state."""

    if config.mode not in {"basic", "full"}:
        raise ValueError("mode must be 'basic' or 'full'")
    if config.mode == "full" and config.e2edev_root is None:
        raise ValueError("full mode requires --e2edev-root")
    if config.input_path is None and config.e2edev_root is None:
        raise ValueError("Either input_path or e2edev_root is required")
    if config.runner_timeout_seconds <= 0:
        raise ValueError("runner_timeout_seconds must be positive")
    if config.runtime_retries < 0:
        raise ValueError("runtime_retries cannot be negative")
    if config.stability_runs <= 0:
        raise ValueError("stability_runs must be positive")
    if config.runtime_budget_seconds is not None and config.runtime_budget_seconds <= 0:
        raise ValueError("runtime_budget_seconds must be positive")
    if config.mutation and config.mode != "full":
        raise ValueError("real mutation testing requires full mode")
    if config.max_mutants <= 0:
        raise ValueError("max_mutants must be positive")
    if config.max_mutants_per_project <= 0:
        raise ValueError("max_mutants_per_project must be positive")
    if config.mutation_budget_seconds is not None and config.mutation_budget_seconds <= 0:
        raise ValueError("mutation_budget_seconds must be positive")
    if config.max_projects is not None and config.max_projects <= 0:
        raise ValueError("max_projects must be positive")
    if config.workers <= 0:
        raise ValueError("workers must be positive")
    if config.max_tests_per_project is not None and config.max_tests_per_project <= 0:
        raise ValueError("max_tests_per_project must be positive")
    if config.coverage_method not in {"auto", "cdp_precise_coverage", "istanbul"}:
        raise ValueError("coverage_method must be auto, cdp_precise_coverage, or istanbul")
    unknown_stubs = set(config.browser_stubs).difference({"network", "speech", "clipboard", "notification"})
    if unknown_stubs:
        raise ValueError(f"Unknown browser stubs: {', '.join(sorted(unknown_stubs))}")

    semantic_mode = "live" if config.live else "offline"
    manifest_config = config.manifest_config()
    store = OrchestratorStateStore(
        config.output_dir,
        mode=config.mode,  # type: ignore[arg-type]
        semantic_mode=semantic_mode,
        config=manifest_config,
        resume=config.resume,
    )
    input_signature = _input_signature(config)

    def discover() -> dict[str, object]:
        if config.e2edev_root:
            inventories = discover_project_inventories(config.e2edev_root, config.projects)
            if config.max_projects is not None:
                inventories = inventories[: config.max_projects]
        else:
            if config.input_path is None or not config.input_path.is_file():
                raise FileNotFoundError(f"Input file not found: {config.input_path}")
            inventories = []
        return {"inventories": [item.model_dump(mode="json") for item in inventories]}

    discovery_payload = _state_payload(
        store,
        "DISCOVER_INPUTS",
        stable_hash({"input": input_signature, "projects": config.projects, "mode": config.mode}),
        discover,
    )
    inventories = [ProjectInventory.model_validate(item) for item in discovery_payload["inventories"]]  # type: ignore[index]

    def load() -> dict[str, object]:
        if config.e2edev_root:
            loaded = load_inventory_records(inventories)
        else:
            loaded = load_records(config.input_path)  # type: ignore[arg-type]
            if config.projects:
                selected = set(config.projects)
                loaded = [record for record in loaded if record.project_id in selected]
                missing = selected.difference({record.project_id for record in loaded})
                if missing:
                    raise ValueError(f"Requested projects were not found in input: {', '.join(sorted(missing))}")
        if not loaded:
            raise ValueError("No records selected for evaluation")
        loaded_inventories = inventories or _csv_inventories(loaded, config.input_path)
        return {
            "records": [record.model_dump(mode="json") for record in loaded],
            "inventories": [item.model_dump(mode="json") for item in loaded_inventories],
        }

    load_payload = _state_payload(
        store,
        "LOAD_RECORDS",
        stable_hash({"input": input_signature, "projects": config.projects}),
        load,
    )
    dataset_records = [TestRecord.model_validate(item) for item in load_payload["records"]]  # type: ignore[index]
    inventories = [ProjectInventory.model_validate(item) for item in load_payload["inventories"]]  # type: ignore[index]
    if config.max_projects is not None and not config.e2edev_root:
        project_ids = sorted({record.project_id for record in dataset_records})[: config.max_projects]
        dataset_records = [record for record in dataset_records if record.project_id in set(project_ids)]
        inventories = [inventory for inventory in inventories if inventory.project_id in set(project_ids)]
    all_records = _select_records(dataset_records, config)
    if config.max_tests_per_project is not None:
        counts: Counter[str] = Counter()
        capped_records: list[TestRecord] = []
        for record in all_records:
            if counts[record.project_id] >= config.max_tests_per_project:
                continue
            counts[record.project_id] += 1
            capped_records.append(record)
        all_records = capped_records
    records = all_records[: config.limit] if config.limit is not None else all_records
    if not records:
        raise ValueError("No records selected for evaluation")

    all_suites = group_by_suite(dataset_records)
    selected_suites = group_by_suite(records)
    records_hash = stable_hash([record.model_dump(mode="json") for record in records])

    static_payload = _state_payload(
        store,
        "STATIC_VERIFY",
        records_hash,
        lambda: {
            "facts": {
                record.record_key: extract_static_facts(record).model_dump(mode="json")
                for record in records
            }
        },
    )
    facts_by_record = {
        record_key: StaticFacts.model_validate(payload)
        for record_key, payload in static_payload["facts"].items()  # type: ignore[union-attr]
    }

    semantic_context_by_project: dict[str, tuple[list[str], dict[str, object]]] = {}
    semantic_context_warnings: list[str] = []
    if config.mode == "full":
        for inventory in inventories:
            source_requirements, web_analysis, warnings = load_inventory_semantic_context(inventory)
            semantic_context_by_project[inventory.project_id] = (source_requirements, web_analysis)
            semantic_context_warnings.extend(warnings)

    llm: OpenAIJsonAgent | None = None

    def get_llm() -> OpenAIJsonAgent:
        nonlocal llm
        if llm is None:
            llm = OpenAIJsonAgent(
                config.model,
                config.max_output_tokens,
                config.timeout_seconds,
                cache_dir=config.output_dir / "llm_cache" if config.llm_cache else None,
            )
        return llm

    def build_contracts() -> dict[str, object]:
        contracts: dict[str, RequirementContract] = {}
        warnings: list[str] = list(semantic_context_warnings)
        for suite_key, suite_records in selected_suites.items():
            if config.live:
                try:
                    source_requirements, web_analysis = semantic_context_by_project.get(
                        suite_records[0].project_id,
                        ([], {}),
                    )
                    contracts[suite_key] = build_requirement_contract(
                        get_llm(),
                        suite_records[0],
                        source_requirements=source_requirements,
                        web_application_analysis=web_analysis,
                    )
                except Exception:
                    contracts[suite_key] = _fallback_contract(suite_records[0])
                    warnings.append(
                        f"Requirement Agent returned no valid structured contract for {suite_key}; dependent semantic reviews were skipped."
                    )
            else:
                contracts[suite_key] = _fallback_contract(suite_records[0])
        return {
            "contracts": {
                suite_key: contract.model_dump(mode="json")
                for suite_key, contract in contracts.items()
            },
            "warnings": warnings,
        }

    contracts_payload = _state_payload(
        store,
        "BUILD_REQUIREMENT_CONTRACTS",
        stable_hash(
            {
                "requirements": {
                    key: suite[0].requirement
                    for key, suite in selected_suites.items()
                },
                "live": config.live,
                "model": config.model if config.live else None,
                "source_context": semantic_context_by_project if config.live else None,
            }
        ),
        build_contracts,
        recoverable=True,
    )
    contracts = {
        suite_key: RequirementContract.model_validate(payload)
        for suite_key, payload in contracts_payload["contracts"].items()  # type: ignore[union-attr]
    }
    runtime_warnings = list(contracts_payload.get("warnings", []))

    def build_test_reviews() -> dict[str, object]:
        test_reviews: dict[str, list[AgentReview]] = {}
        warnings: list[str] = []
        for record in records:
            facts = facts_by_record[record.record_key]
            reviews = [static_review(record, facts)]
            contract = contracts[record.suite_key]
            if config.live and contract.behaviors:
                tasks = (
                    ("bdd_traceability", "spec_alignment", review_bdd),
                    ("step_code", "step_traceability", review_step_code),
                    ("oracle_critic", "oracle_strength", review_oracle),
                )
                concurrent_reviews: dict[str, AgentReview] = {}
                with ThreadPoolExecutor(max_workers=len(tasks), thread_name_prefix="test-evaluator") as pool:
                    futures = {
                        pool.submit(invoke, get_llm(), record, contract, facts): (agent_name, dimension)
                        for agent_name, dimension, invoke in tasks
                    }
                    for future in as_completed(futures):
                        agent_name, dimension = futures[future]
                        try:
                            concurrent_reviews[agent_name] = future.result()
                        except Exception:
                            concurrent_reviews[agent_name] = _agent_failure_review(
                                agent_name,
                                record.record_key,
                                dimension,
                            )
                            warnings.append(
                                f"{agent_name} returned no valid structured review for {record.record_key}; the dimension is UNKNOWN."
                            )
                reviews.extend(concurrent_reviews[agent_name] for agent_name, _, _ in tasks)
                if config.mutation_hypotheses:
                    try:
                        reviews.append(review_mutation_hypothesis(get_llm(), record, contract, facts))
                    except Exception:
                        reviews.append(
                            _agent_failure_review(
                                "mutation_hypothesis",
                                record.record_key,
                                "mutation_readiness",
                            )
                        )
                        warnings.append(
                            f"mutation_hypothesis returned no valid structured review for {record.record_key}; mutation readiness is UNKNOWN."
                        )
            else:
                reviews.extend(_offline_reviews(record))
            test_reviews[record.record_key] = reviews
        return {
            "reviews": {
                record_key: [review.model_dump(mode="json") for review in reviews]
                for record_key, reviews in test_reviews.items()
            },
            "warnings": warnings,
        }

    reviews_payload = _state_payload(
        store,
        "BASIC_PARALLEL_REVIEWS",
        stable_hash(
            {
                "records": records_hash,
                "contracts": contracts_payload["contracts"],
                "facts": static_payload["facts"],
                "live": config.live,
                "model": config.model if config.live else None,
                "mutation_hypotheses": config.mutation_hypotheses,
            }
        ),
        build_test_reviews,
        recoverable=True,
    )
    reviews_by_record = {
        record_key: [AgentReview.model_validate(item) for item in items]
        for record_key, items in reviews_payload["reviews"].items()  # type: ignore[union-attr]
    }
    runtime_warnings.extend(reviews_payload.get("warnings", []))

    def build_suite_reviews() -> dict[str, object]:
        assessments: dict[str, SuiteAssessment | None] = {}
        warnings: list[str] = []
        for suite_key, suite_records in selected_suites.items():
            contract = contracts[suite_key]
            assessment: SuiteAssessment | None = None
            if config.live and contract.behaviors:
                try:
                    assessment = review_suite(get_llm(), suite_key, suite_records, contract)
                except Exception:
                    assessment = _suite_failure_assessment(suite_key)
                    warnings.append(
                        f"Suite Coverage Agent returned no valid structured review for {suite_key}; requirement adequacy has reduced confidence."
                    )
            assessments[suite_key] = assessment
        return {
            "assessments": {
                suite_key: assessment.model_dump(mode="json") if assessment else None
                for suite_key, assessment in assessments.items()
            },
            "warnings": warnings,
        }

    suite_payload = _state_payload(
        store,
        "BASIC_SUITE_REVIEW",
        stable_hash(
            {
                "contracts": contracts_payload["contracts"],
                "reviews": reviews_payload["reviews"],
                "live": config.live,
                "model": config.model if config.live else None,
            }
        ),
        build_suite_reviews,
        recoverable=True,
    )
    assessments = {
        suite_key: SuiteAssessment.model_validate(payload) if payload else None
        for suite_key, payload in suite_payload["assessments"].items()  # type: ignore[union-attr]
    }
    runtime_warnings.extend(suite_payload.get("warnings", []))

    def coordinate() -> dict[str, object]:
        test_reports = []
        for record in records:
            report = coordinate_test(
                record,
                facts_by_record[record.record_key],
                reviews_by_record[record.record_key],
            )
            static_mutation = assess_static_mutation(
                record,
                contracts[record.suite_key],
                facts_by_record[record.record_key],
            )
            report.static_mutation = static_mutation
            report.mutation_readiness = static_mutation.readiness_score
            test_reports.append(report)
        requirement_reports = []
        for suite_key, suite_records in selected_suites.items():
            partial_suite = len(suite_records) != len(all_suites[suite_key])
            record_keys = {record.record_key for record in suite_records}
            suite_tests = [report for report in test_reports if report.record_key in record_keys]
            requirement_reports.append(
                coordinate_requirement(
                    suite_key,
                    suite_records,
                    suite_tests,
                    assessments[suite_key],
                    partial_suite,
                    analyze_suite_duplicates(suite_records, facts_by_record),
                    analyze_static_behavior_coverage(suite_records, contracts[suite_key]),
                )
            )
        run = build_run(
            mode=config.mode,
            semantic_mode=semantic_mode,
            model=config.model if config.live else None,
            tests=test_reports,
            requirements=requirement_reports,
            runtime_warnings=runtime_warnings,
            run_id=store.run_id,
            config=manifest_config,
            inventories=inventories,
        )
        return {"run": run.model_dump(mode="json")}

    coordinate_payload = _state_payload(
        store,
        "BASIC_COORDINATE",
        stable_hash(
            {
                "reviews": reviews_payload["reviews"],
                "suite": suite_payload["assessments"],
                "mode": config.mode,
            }
        ),
        coordinate,
    )
    run = EvaluationRun.model_validate(coordinate_payload["run"])

    if config.mode == "full":
        inventory_by_project = {inventory.project_id: inventory for inventory in inventories}

        def model_sources() -> dict[str, object]:
            outputs: dict[str, object] = {}
            errors: dict[str, str] = {}
            warnings: list[str] = []
            selected_project_ids = {record.project_id for record in records}
            for project_id in sorted(selected_project_ids):
                inventory = inventory_by_project.get(project_id)
                if inventory is None:
                    errors[project_id] = "No project inventory was discovered"
                    continue
                try:
                    output = build_source_model(
                        SourceModelInput(
                            run_id=store.run_id,
                            inventory=inventory,
                            contract_by_suite={
                                suite_key: contract
                                for suite_key, contract in contracts.items()
                                if contract.project_id == project_id
                            },
                        )
                    )
                    outputs[project_id] = output.source_model.model_dump(mode="json")
                    warnings.extend(f"{project_id}: {warning}" for warning in output.warnings)
                except Exception as error:
                    errors[project_id] = f"{type(error).__name__}: {error}"
            models = {
                project_id: SourceModel.model_validate(payload)
                for project_id, payload in outputs.items()
            }
            artifacts = _write_source_model_artifacts(config.output_dir, models)
            return {
                "models": outputs,
                "errors": errors,
                "warnings": warnings,
                "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
            }

        source_payload = _state_payload(
            store,
            "SOURCE_MODEL",
            stable_hash(
                {
                    "sources": _source_signature(inventories),
                    "projects": sorted({record.project_id for record in records}),
                }
            ),
            model_sources,
            recoverable=True,
            degraded_reason=lambda payload: (
                "; ".join(
                    [
                        *[f"Source modeling failed for {project}: {error}" for project, error in payload.get("errors", {}).items()],  # type: ignore[union-attr]
                        *[str(item) for item in payload.get("warnings", [])],
                    ]
                )
                or None
            ),
        )
        source_models = {
            project_id: SourceModel.model_validate(payload)
            for project_id, payload in source_payload["models"].items()  # type: ignore[union-attr]
        }
        source_payload["artifacts"] = [
            artifact.model_dump(mode="json")
            for artifact in _write_source_model_artifacts(config.output_dir, source_models)
        ]
        run.runtime_warnings.extend(str(item) for item in source_payload.get("warnings", []))
        if source_payload.get("errors"):
            run.runtime_warnings.append(
                f"Source modeling failed for {len(source_payload['errors'])} selected projects."
            )

        def ground_source_selectors() -> dict[str, object]:
            outputs: dict[str, object] = {}
            errors: dict[str, str] = {}
            warnings: list[str] = []
            for record in records:
                model = source_models.get(record.project_id)
                if model is None:
                    errors[record.record_key] = "No source model is available for this project"
                    continue
                try:
                    output = ground_selectors(
                        SelectorGroundingInput(
                            run_id=store.run_id,
                            record=record,
                            contract=contracts[record.suite_key],
                            static_facts=facts_by_record[record.record_key],
                            source_model=model,
                        )
                    )
                    outputs[record.record_key] = output.model_dump(mode="json")
                    warnings.extend(
                        f"{record.record_key}: {warning}"
                        for warning in output.warnings
                        if output.status in {Status.UNKNOWN, Status.SKIPPED}
                    )
                except Exception as error:
                    errors[record.record_key] = f"{type(error).__name__}: {error}"
            validated = {
                record_key: SelectorGroundingOutput.model_validate(payload)
                for record_key, payload in outputs.items()
            }
            artifacts = _write_grounding_artifacts(config.output_dir, records, validated)
            return {
                "outputs": outputs,
                "errors": errors,
                "warnings": warnings,
                "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
            }

        grounding_payload = _state_payload(
            store,
            "SOURCE_GROUNDING",
            stable_hash(
                {
                    "records": records_hash,
                    "facts": static_payload["facts"],
                    "models": source_payload["models"],
                    "contracts": contracts_payload["contracts"],
                }
            ),
            ground_source_selectors,
            recoverable=True,
            degraded_reason=lambda payload: (
                f"Selector grounding failed for {len(payload.get('errors', {}))} of {len(records)} selected tests."
                if payload.get("errors")
                else None
            ),
        )
        grounding_by_record = {
            record_key: SelectorGroundingOutput.model_validate(payload)
            for record_key, payload in grounding_payload["outputs"].items()  # type: ignore[union-attr]
        }
        grounding_payload["artifacts"] = [
            artifact.model_dump(mode="json")
            for artifact in _write_grounding_artifacts(config.output_dir, records, grounding_by_record)
        ]
        run.runtime_warnings.extend(str(item) for item in grounding_payload.get("warnings", []))
        if grounding_payload.get("errors"):
            run.runtime_warnings.append(
                f"Selector grounding failed for {len(grounding_payload['errors'])} of {len(records)} selected tests."
            )

        def materialize() -> dict[str, object]:
            workspaces: dict[str, object] = {}
            errors: dict[str, str] = {}
            workspace_root = config.output_dir / "workspaces" / store.run_id
            for record in records:
                inventory = inventory_by_project.get(record.project_id)
                if inventory is None:
                    errors[record.record_key] = f"No project inventory found for {record.project_id}"
                    continue
                try:
                    output = materialize_test(
                        TestMaterializerInput(
                            run_id=store.run_id,
                            inventory=inventory,
                            record=record,
                            output_dir=str(workspace_root),
                            instrumentation={"headless": config.headless},
                        )
                    )
                    workspaces[record.record_key] = output.workspace.model_dump(mode="json")
                except Exception as error:
                    errors[record.record_key] = f"{type(error).__name__}: {error}"
            return {"workspaces": workspaces, "errors": errors}

        materialization_payload = _state_payload(
            store,
            "MATERIALIZE_TESTS",
            stable_hash(
                {
                    "records": records_hash,
                    "sources": _source_signature(inventories),
                    "headless": config.headless,
                }
            ),
            materialize,
            recoverable=True,
            degraded_reason=lambda payload: (
                f"Materialization failed for {len(payload.get('errors', {}))} of {len(records)} selected tests."
                if payload.get("errors")
                else None
            ),
            cached_validator=lambda payload: all(
                Path(str(workspace.get("feature_file", ""))).is_file()
                and Path(str(workspace.get("steps_file", ""))).is_file()
                and Path(str(workspace.get("entry_html", ""))).is_file()
                for workspace in payload.get("workspaces", {}).values()  # type: ignore[union-attr]
                if isinstance(workspace, dict)
            ),
        )
        workspaces = {
            record_key: WorkspaceSpec.model_validate(payload)
            for record_key, payload in materialization_payload["workspaces"].items()  # type: ignore[union-attr]
        }
        materialization_errors = dict(materialization_payload.get("errors", {}))
        if materialization_errors:
            run.runtime_warnings.append(
                f"Materialization failed for {len(materialization_errors)} of {len(records)} selected tests."
            )

        def run_baselines() -> dict[str, object]:
            results: dict[str, RuntimeResult] = {}
            warnings: list[str] = []
            deadline = (
                time.monotonic() + config.runtime_budget_seconds
                if config.runtime_budget_seconds is not None
                else None
            )

            def run_one(record: TestRecord) -> tuple[RuntimeResult, list[str]]:
                local_warnings: list[str] = []
                if deadline is not None and time.monotonic() >= deadline:
                    local_warnings.append(
                        f"Runtime budget exhausted before {record.record_key}; baseline was skipped."
                    )
                    return RuntimeResult(record_key=record.record_key, status="skipped"), local_warnings
                workspace = workspaces.get(record.record_key)
                if workspace is None:
                    return (
                        RuntimeResult(
                            record_key=record.record_key,
                            status="skipped",
                            error_type="unknown",
                        ),
                        local_warnings,
                    )
                final_result: RuntimeResult | None = None
                for retry_index in range(config.runtime_retries + 1):
                    try:
                        output = run_baseline_test(
                            TestRunnerInput(
                                run_id=store.run_id,
                                workspace=workspace,
                                timeout_seconds=config.runner_timeout_seconds,
                                headless=config.headless,
                                retry_index=retry_index,
                                browser_stubs=list(config.browser_stubs),
                            )
                        )
                        final_result = output.runtime
                    except Exception as error:
                        final_result = RuntimeResult(
                            record_key=record.record_key,
                            status="env_error",
                            error_type="env_error",
                        )
                        local_warnings.append(
                            f"Runner raised {type(error).__name__} for {record.record_key}: {error}"
                        )
                    if final_result.status not in {"env_error", "timeout"}:
                        break
                if final_result is None:
                    final_result = RuntimeResult(
                        record_key=record.record_key,
                        status="env_error",
                        error_type="env_error",
                    )
                return final_result, local_warnings

            pending_records: list[TestRecord] = []
            item_hashes: dict[str, str] = {}
            for record in records:
                item_hash = stable_hash(
                    {
                        "record": record.model_dump(mode="json"),
                        "workspace": (
                            workspaces[record.record_key].model_dump(mode="json")
                            if record.record_key in workspaces
                            else None
                        ),
                        "timeout": config.runner_timeout_seconds,
                        "headless": config.headless,
                        "retries": config.runtime_retries,
                        "browser_stubs": config.browser_stubs,
                    }
                )
                item_hashes[record.record_key] = item_hash
                cached = store.cached_item_payload(
                    "RUN_BASELINE_TESTS",
                    record.record_key,
                    item_hash,
                )
                if cached is None:
                    pending_records.append(record)
                    continue
                results[record.record_key] = RuntimeResult.model_validate(cached["runtime"])
                warnings.extend(str(item) for item in cached.get("warnings", []))

            if pending_records:
                with ThreadPoolExecutor(
                    max_workers=min(config.workers, len(pending_records)),
                    thread_name_prefix="test-evaluator-runtime",
                ) as pool:
                    futures = {pool.submit(run_one, record): record for record in pending_records}
                    completed_count = 0
                    for future in as_completed(futures):
                        record = futures[future]
                        result, local_warnings = future.result()
                        results[record.record_key] = result
                        warnings.extend(local_warnings)
                        store.save_item_payload(
                            "RUN_BASELINE_TESTS",
                            record.record_key,
                            item_hashes[record.record_key],
                            {
                                "runtime": result.model_dump(mode="json"),
                                "warnings": local_warnings,
                            },
                        )
                        completed_count += 1
                        _progress(config, "RUN_BASELINE_TESTS", completed_count, len(pending_records))
            results = {record.record_key: results[record.record_key] for record in records}
            environment_errors = sum(result.status == "env_error" for result in results.values())
            skipped = sum(result.status == "skipped" for result in results.values())
            if environment_errors:
                warnings.append(
                    f"Baseline runtime environment was unavailable for {environment_errors} selected tests."
                )
            if skipped:
                warnings.append(f"Baseline execution was skipped for {skipped} tests that were not materialized.")
            artifacts = _write_runtime_artifacts(config.output_dir, records, results)
            return {
                "results": {
                    record_key: result.model_dump(mode="json")
                    for record_key, result in results.items()
                },
                "warnings": warnings,
                "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
            }

        baseline_payload = _state_payload(
            store,
            "RUN_BASELINE_TESTS",
            stable_hash(
                {
                    "workspaces": materialization_payload["workspaces"],
                    "timeout": config.runner_timeout_seconds,
                    "headless": config.headless,
                    "retries": config.runtime_retries,
                    "browser_stubs": config.browser_stubs,
                    "runtime_budget_seconds": config.runtime_budget_seconds,
                }
            ),
            run_baselines,
            recoverable=True,
            degraded_reason=lambda payload: (
                "; ".join(str(item) for item in payload.get("warnings", [])) or None
            ),
        )
        runtime_by_record = {
            record_key: RuntimeResult.model_validate(payload)
            for record_key, payload in baseline_payload["results"].items()  # type: ignore[union-attr]
        }
        # Recreate stable project-level artifacts even when the runner state was
        # loaded from a checkpoint and a derived report file was removed.
        baseline_payload["artifacts"] = [
            artifact.model_dump(mode="json")
            for artifact in _write_runtime_artifacts(config.output_dir, records, runtime_by_record)
        ]
        run.runtime_warnings.extend(str(item) for item in baseline_payload.get("warnings", []))

        def build_stability_reports() -> dict[str, object]:
            results_by_record: dict[str, list[RuntimeResult]] = {
                record.record_key: [runtime_by_record[record.record_key]] for record in records
            }
            warnings: list[str] = []
            deadline = (
                time.monotonic() + config.runtime_budget_seconds
                if config.runtime_budget_seconds is not None
                else None
            )

            def repeat(record: TestRecord, run_index: int) -> RuntimeResult:
                if deadline is not None and time.monotonic() >= deadline:
                    return RuntimeResult(record_key=record.record_key, status="skipped")
                workspace = workspaces.get(record.record_key)
                if workspace is None:
                    return RuntimeResult(record_key=record.record_key, status="skipped")
                try:
                    return run_baseline_test(
                        TestRunnerInput(
                            run_id=store.run_id,
                            workspace=workspace,
                            timeout_seconds=config.runner_timeout_seconds,
                            headless=config.headless,
                            retry_index=1000 + run_index,
                            browser_stubs=list(config.browser_stubs),
                        )
                    ).runtime
                except Exception:
                    return RuntimeResult(
                        record_key=record.record_key,
                        status="env_error",
                        error_type="env_error",
                    )

            tasks = [
                (record, run_index)
                for record in records
                if runtime_by_record[record.record_key].status not in {"env_error", "skipped"}
                for run_index in range(1, config.stability_runs)
            ]
            if tasks:
                with ThreadPoolExecutor(
                    max_workers=min(config.workers, len(tasks)),
                    thread_name_prefix="test-evaluator-stability",
                ) as pool:
                    futures = {
                        pool.submit(repeat, record, run_index): (record, run_index)
                        for record, run_index in tasks
                    }
                    ordered: dict[str, dict[int, RuntimeResult]] = {}
                    completed_count = 0
                    for future in as_completed(futures):
                        record, run_index = futures[future]
                        ordered.setdefault(record.record_key, {})[run_index] = future.result()
                        completed_count += 1
                        _progress(config, "STABILITY_ANALYZE", completed_count, len(tasks))
                    for record_key, indexed in ordered.items():
                        results_by_record[record_key].extend(
                            indexed[index] for index in sorted(indexed)
                        )
            reports = {
                record.record_key: analyze_stability(
                    record.record_key,
                    config.stability_runs,
                    results_by_record[record.record_key],
                )
                for record in records
            }
            incomplete = sum(
                report.completed_runs < report.requested_runs for report in reports.values()
            )
            if incomplete:
                warnings.append(f"Stability runs were incomplete for {incomplete} selected tests.")
            artifacts = _write_stability_artifacts(config.output_dir, records, reports)
            return {
                "reports": {
                    record_key: report.model_dump(mode="json")
                    for record_key, report in reports.items()
                },
                "warnings": warnings,
                "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
            }

        stability_payload = _state_payload(
            store,
            "STABILITY_ANALYZE",
            stable_hash(
                {
                    "baseline": baseline_payload["results"],
                    "workspaces": materialization_payload["workspaces"],
                    "runs": config.stability_runs,
                    "timeout": config.runner_timeout_seconds,
                    "headless": config.headless,
                    "browser_stubs": config.browser_stubs,
                    "runtime_budget_seconds": config.runtime_budget_seconds,
                }
            ),
            build_stability_reports,
            recoverable=True,
            degraded_reason=lambda payload: (
                "; ".join(str(item) for item in payload.get("warnings", [])) or None
            ),
        )
        stability_by_record = {
            record_key: StabilityReport.model_validate(payload)
            for record_key, payload in stability_payload["reports"].items()  # type: ignore[union-attr]
        }
        stability_payload["artifacts"] = [
            artifact.model_dump(mode="json")
            for artifact in _write_stability_artifacts(config.output_dir, records, stability_by_record)
        ]
        run.runtime_warnings.extend(str(item) for item in stability_payload.get("warnings", []))

        def build_runtime_traces() -> dict[str, object]:
            outputs: dict[str, object] = {}
            errors: dict[str, str] = {}
            for record in records:
                try:
                    output = trace_runtime(
                        RuntimeTraceInput(
                            run_id=store.run_id,
                            record=record,
                            runtime=runtime_by_record[record.record_key],
                            static_facts=facts_by_record[record.record_key],
                            source_model=source_models.get(record.project_id),
                        )
                    )
                    outputs[record.record_key] = output.model_dump(mode="json")
                except Exception as error:
                    errors[record.record_key] = f"{type(error).__name__}: {error}"
            validated = {
                record_key: RuntimeTraceOutput.model_validate(payload)
                for record_key, payload in outputs.items()
            }
            artifacts = _write_runtime_trace_artifacts(
                config.output_dir,
                records,
                {record_key: output.runtime_trace for record_key, output in validated.items()},
            )
            return {
                "outputs": outputs,
                "errors": errors,
                "artifacts": [artifact.model_dump(mode="json") for artifact in artifacts],
            }

        runtime_trace_payload = _state_payload(
            store,
            "RUNTIME_TRACE",
            stable_hash(
                {
                    "runtime": baseline_payload["results"],
                    "facts": static_payload["facts"],
                }
            ),
            build_runtime_traces,
            recoverable=True,
            degraded_reason=lambda payload: (
                f"Runtime tracing failed for {len(payload.get('errors', {}))} of {len(records)} selected tests."
                if payload.get("errors")
                else None
            ),
        )
        runtime_trace_outputs = {
            record_key: RuntimeTraceOutput.model_validate(payload)
            for record_key, payload in runtime_trace_payload["outputs"].items()  # type: ignore[union-attr]
        }
        runtime_trace_payload["artifacts"] = [
            artifact.model_dump(mode="json")
            for artifact in _write_runtime_trace_artifacts(
                config.output_dir,
                records,
                {
                    record_key: output.runtime_trace
                    for record_key, output in runtime_trace_outputs.items()
                },
            )
        ]

        coverage_outputs: dict[str, CoverageOutput] = {}
        coverage_reports: dict[str, CoverageReport] = {}
        coverage_artifacts: list[ArtifactRef] = []
        if config.coverage:
            def collect_test_coverage() -> dict[str, object]:
                outputs: dict[str, object] = {}
                errors: dict[str, str] = {}

                def collect_one(record: TestRecord) -> CoverageOutput:
                    workspace = workspaces.get(record.record_key)
                    inventory = inventory_by_project.get(record.project_id)
                    if workspace is None or inventory is None:
                        raise ValueError("Workspace or inventory is unavailable")
                    return collect_coverage(
                        CoverageInput(
                            run_id=store.run_id,
                            inventory=inventory,
                                workspace=workspace,
                                runtime=runtime_by_record[record.record_key],
                                method=config.coverage_method,  # type: ignore[arg-type]
                                browser_stubs=list(config.browser_stubs),
                        ),
                        timeout_seconds=config.runner_timeout_seconds,
                        headless=config.headless,
                    )

                with ThreadPoolExecutor(
                    max_workers=min(config.workers, len(records)),
                    thread_name_prefix="test-evaluator-coverage",
                ) as pool:
                    futures = {pool.submit(collect_one, record): record for record in records}
                    for future in as_completed(futures):
                        record = futures[future]
                        try:
                            output = future.result()
                            outputs[record.record_key] = output.model_dump(mode="json")
                        except Exception as error:
                            errors[record.record_key] = f"{type(error).__name__}: {error}"
                unavailable = sum(
                    CoverageOutput.model_validate(payload).coverage.status in {Status.UNKNOWN, Status.SKIPPED}
                    for payload in outputs.values()
                )
                warnings = (
                    [f"Coverage was unavailable for {unavailable} of {len(records)} selected tests."]
                    if unavailable
                    else []
                )
                return {"outputs": outputs, "errors": errors, "warnings": warnings}

            coverage_payload = _state_payload(
                store,
                "COVERAGE",
                stable_hash(
                    {
                        "runtime": baseline_payload["results"],
                        "workspaces": materialization_payload["workspaces"],
                        "method": config.coverage_method,
                        "browser_stubs": config.browser_stubs,
                    }
                ),
                collect_test_coverage,
                recoverable=True,
                degraded_reason=lambda payload: (
                    "; ".join(
                        [
                            *[f"{record}: {error}" for record, error in payload.get("errors", {}).items()],  # type: ignore[union-attr]
                            *[str(item) for item in payload.get("warnings", [])],
                        ]
                    )
                    or None
                ),
            )
            coverage_outputs = {
                record_key: CoverageOutput.model_validate(payload)
                for record_key, payload in coverage_payload["outputs"].items()  # type: ignore[union-attr]
            }
            coverage_reports = {
                record_key: output.coverage for record_key, output in coverage_outputs.items()
            }
            coverage_artifacts = _write_coverage_artifacts(config.output_dir, records, coverage_reports)
            run.runtime_warnings.extend(str(item) for item in coverage_payload.get("warnings", []))
        else:
            store.skip("COVERAGE", "Coverage collection was not requested; use --coverage to enable it.")

        mutation_plans: dict[str, MutationPlan] = {}
        mutation_results: dict[str, list[MutationRunResult]] = {}
        mutation_analyses: dict[str, MutationAnalysis] = {}
        mutation_artifacts: list[ArtifactRef] = []
        if config.mutation:
            def generate_mutants() -> dict[str, object]:
                plans: dict[str, object] = {}
                errors: dict[str, str] = {}
                warnings: list[str] = []
                remaining = config.max_mutants
                selected_projects = sorted({record.project_id for record in records})
                for project_id in selected_projects:
                    inventory = inventory_by_project.get(project_id)
                    model = source_models.get(project_id)
                    if inventory is None or model is None:
                        errors[project_id] = "Source inventory/model is unavailable"
                        continue
                    if remaining <= 0:
                        plans[project_id] = MutationPlan(project_id=project_id).model_dump(mode="json")
                        warnings.append(f"{project_id}: global mutation limit was already reached")
                        continue
                    try:
                        output = generate_mutation_plan(
                            MutationGeneratorInput(
                                run_id=store.run_id,
                                inventory=inventory,
                                source_model=model,
                                contracts=[
                                    contract
                                    for contract in contracts.values()
                                    if contract.project_id == project_id
                                ],
                                max_mutants=min(remaining, config.max_mutants_per_project),
                                operators=list(config.mutation_operators),
                            )
                        )
                        plan = output.plan.model_copy(
                            update={
                                "mutants": [
                                    mutant.model_copy(
                                        update={
                                            "impacted_record_keys": _impacted_record_keys(
                                                mutant,
                                                records,
                                                contracts,
                                            )
                                        }
                                    )
                                    for mutant in output.plan.mutants
                                ]
                            }
                        )
                        plans[project_id] = plan.model_dump(mode="json")
                        remaining -= len(plan.mutants)
                        warnings.extend(f"{project_id}: {warning}" for warning in output.warnings)
                    except Exception as error:
                        errors[project_id] = f"{type(error).__name__}: {error}"
                return {"plans": plans, "errors": errors, "warnings": warnings}

            mutation_generate_payload = _state_payload(
                store,
                "MUTATION_GENERATE",
                stable_hash(
                    {
                        "models": source_payload["models"],
                        "contracts": contracts_payload["contracts"],
                        "max_mutants": config.max_mutants,
                        "max_mutants_per_project": config.max_mutants_per_project,
                        "operators": config.mutation_operators,
                        "records": records_hash,
                    }
                ),
                generate_mutants,
                recoverable=True,
                degraded_reason=lambda payload: (
                    "; ".join(
                        [
                            *[f"{project}: {error}" for project, error in payload.get("errors", {}).items()],  # type: ignore[union-attr]
                            *[str(item) for item in payload.get("warnings", [])],
                        ]
                    )
                    or None
                ),
            )
            mutation_plans = {
                project_id: MutationPlan.model_validate(payload)
                for project_id, payload in mutation_generate_payload["plans"].items()  # type: ignore[union-attr]
            }
            run.runtime_warnings.extend(str(item) for item in mutation_generate_payload.get("warnings", []))
            if mutation_generate_payload.get("errors"):
                run.runtime_warnings.append(
                    f"Mutation generation failed for {len(mutation_generate_payload['errors'])} selected projects."
                )

            def execute_mutants() -> dict[str, object]:
                outputs_by_id: dict[str, dict[str, MutationRunResult]] = {
                    project_id: {} for project_id in mutation_plans
                }
                errors: dict[str, str] = {}
                warnings: list[str] = []
                deadline = (
                    time.monotonic() + config.mutation_budget_seconds
                    if config.mutation_budget_seconds is not None
                    else None
                )
                workspace_root = config.output_dir / "workspaces" / store.run_id
                records_by_key = {record.record_key: record for record in records}
                pending: list[tuple[str, MutantSpec, list[TestRecord], str]] = []
                for project_id, plan in mutation_plans.items():
                    for mutant in plan.mutants:
                        eligible = [
                            records_by_key[record_key]
                            for record_key in mutant.impacted_record_keys
                            if record_key in records_by_key
                            and runtime_by_record.get(record_key)
                            and runtime_by_record[record_key].status == "pass"
                            and not (
                                stability_by_record.get(record_key)
                                and stability_by_record[record_key].flaky
                            )
                        ]
                        item_hash = stable_hash(
                            {
                                "mutant": mutant.model_dump(mode="json"),
                                "eligible": [record.record_key for record in eligible],
                                "workspaces": {
                                    record.record_key: workspaces[record.record_key].model_dump(mode="json")
                                    for record in eligible
                                    if record.record_key in workspaces
                                },
                                "timeout": config.runner_timeout_seconds,
                                "browser_stubs": config.browser_stubs,
                            }
                        )
                        cached = store.cached_item_payload(
                            "MUTATION_RUN",
                            mutant.mutant_id,
                            item_hash,
                        )
                        if cached is not None:
                            outputs_by_id[project_id][mutant.mutant_id] = MutationRunResult.model_validate(
                                cached["result"]
                            )
                            continue
                        pending.append((project_id, mutant, eligible, item_hash))

                def run_one(
                    project_id: str,
                    mutant: MutantSpec,
                    eligible: list[TestRecord],
                ) -> tuple[str, str, MutationRunResult, str | None]:
                    if deadline is not None and time.monotonic() >= deadline:
                        return (
                            project_id,
                            mutant.mutant_id,
                            MutationRunResult(
                                mutant_id=mutant.mutant_id,
                                status="skipped",
                                error_summary="Mutation budget exhausted before execution",
                            ),
                            None,
                        )
                    try:
                        output = run_mutant(
                            MutationRunnerInput(
                                run_id=store.run_id,
                                mutant=mutant,
                                base_workspace_root=str(workspace_root),
                                tests_to_run=eligible,
                                timeout_seconds=config.runner_timeout_seconds,
                                browser_stubs=list(config.browser_stubs),
                            ),
                            workspaces=workspaces,
                        )
                        return project_id, mutant.mutant_id, output.result, None
                    except Exception as error:
                        message = f"{type(error).__name__}: {error}"
                        return (
                            project_id,
                            mutant.mutant_id,
                            MutationRunResult(
                                mutant_id=mutant.mutant_id,
                                status="invalid",
                                error_summary=message,
                            ),
                            message,
                        )

                if pending:
                    with ThreadPoolExecutor(
                        max_workers=min(config.workers, len(pending)),
                        thread_name_prefix="test-evaluator-mutation",
                    ) as pool:
                        futures = {
                            pool.submit(run_one, project_id, mutant, eligible): (
                                project_id,
                                mutant,
                                item_hash,
                            )
                            for project_id, mutant, eligible, item_hash in pending
                        }
                        completed_count = 0
                        for future in as_completed(futures):
                            _, submitted_mutant, item_hash = futures[future]
                            project_id, mutant_id, result, error = future.result()
                            outputs_by_id[project_id][mutant_id] = result
                            store.save_item_payload(
                                "MUTATION_RUN",
                                mutant_id,
                                item_hash,
                                {"result": result.model_dump(mode="json")},
                            )
                            if error:
                                errors[submitted_mutant.mutant_id] = error
                            completed_count += 1
                            _progress(config, "MUTATION_RUN", completed_count, len(pending))

                outputs: dict[str, list[object]] = {}
                for project_id, plan in mutation_plans.items():
                    project_results = [
                        outputs_by_id[project_id][mutant.mutant_id]
                        for mutant in plan.mutants
                        if mutant.mutant_id in outputs_by_id[project_id]
                    ]
                    outputs[project_id] = [result.model_dump(mode="json") for result in project_results]
                    if plan.mutants and project_results and all(
                        result.status == "skipped" for result in project_results
                    ):
                        warnings.append(
                            f"{project_id}: mutation execution skipped because no selected baseline test passed"
                        )
                budget_skips = sum(
                    result.status == "skipped"
                    and result.error_summary == "Mutation budget exhausted before execution"
                    for project_results in outputs_by_id.values()
                    for result in project_results.values()
                )
                if budget_skips:
                    warnings.append(
                        f"Mutation budget exhausted; {budget_skips} mutant(s) were skipped."
                    )
                return {"results": outputs, "errors": errors, "warnings": warnings}

            mutation_run_payload = _state_payload(
                store,
                "MUTATION_RUN",
                stable_hash(
                    {
                        "plans": mutation_generate_payload["plans"],
                        "baseline": baseline_payload["results"],
                        "stability": stability_payload["reports"],
                        "workspaces": materialization_payload["workspaces"],
                        "timeout": config.runner_timeout_seconds,
                        "browser_stubs": config.browser_stubs,
                        "mutation_budget_seconds": config.mutation_budget_seconds,
                    }
                ),
                execute_mutants,
                recoverable=True,
                degraded_reason=lambda payload: (
                    "; ".join(
                        [
                            *[f"{mutant}: {error}" for mutant, error in payload.get("errors", {}).items()],  # type: ignore[union-attr]
                            *[str(item) for item in payload.get("warnings", [])],
                        ]
                    )
                    or None
                ),
            )
            mutation_results = {
                project_id: [MutationRunResult.model_validate(item) for item in payload]
                for project_id, payload in mutation_run_payload["results"].items()  # type: ignore[union-attr]
            }
            run.runtime_warnings.extend(str(item) for item in mutation_run_payload.get("warnings", []))

            def analyze_mutation_results() -> dict[str, object]:
                analyses: dict[str, object] = {}
                errors: dict[str, str] = {}
                warnings: list[str] = []
                for project_id, plan in mutation_plans.items():
                    model = source_models.get(project_id)
                    if model is None:
                        errors[project_id] = "Source model is unavailable"
                        continue
                    try:
                        output = analyze_mutations(
                            MutationAnalystInput(
                                run_id=store.run_id,
                                project_id=project_id,
                                contract_by_suite={
                                    suite_key: contract
                                    for suite_key, contract in contracts.items()
                                    if contract.project_id == project_id
                                },
                                source_model=model,
                                mutation_plan=plan,
                                mutation_results=mutation_results.get(project_id, []),
                                test_reviews=[
                                    review
                                    for record_key, reviews in reviews_by_record.items()
                                    if records_by_key_for_analysis[record_key].project_id == project_id
                                    for review in reviews
                                ],
                            )
                        )
                        analyses[project_id] = output.analysis.model_dump(mode="json")
                        warnings.extend(f"{project_id}: {warning}" for warning in output.warnings)
                    except Exception as error:
                        errors[project_id] = f"{type(error).__name__}: {error}"
                return {"analyses": analyses, "errors": errors, "warnings": warnings}

            records_by_key_for_analysis = {record.record_key: record for record in records}
            mutation_analysis_payload = _state_payload(
                store,
                "MUTATION_ANALYZE",
                stable_hash(
                    {
                        "plans": mutation_generate_payload["plans"],
                        "results": mutation_run_payload["results"],
                    }
                ),
                analyze_mutation_results,
                recoverable=True,
                degraded_reason=lambda payload: (
                    "; ".join(
                        [
                            *[f"{project}: {error}" for project, error in payload.get("errors", {}).items()],  # type: ignore[union-attr]
                            *[str(item) for item in payload.get("warnings", [])],
                        ]
                    )
                    or None
                ),
            )
            mutation_analyses = {
                project_id: MutationAnalysis.model_validate(payload)
                for project_id, payload in mutation_analysis_payload["analyses"].items()  # type: ignore[union-attr]
            }
            run.runtime_warnings.extend(str(item) for item in mutation_analysis_payload.get("warnings", []))
            mutation_artifacts = _write_mutation_artifacts(
                config.output_dir,
                mutation_plans,
                mutation_results,
                mutation_analyses,
            )
        else:
            mutation_reason = "Real mutation testing was not requested; use --mutation to enable it."
            store.skip("MUTATION_GENERATE", mutation_reason)
            store.skip("MUTATION_RUN", mutation_reason)
            store.skip("MUTATION_ANALYZE", mutation_reason)

        def build_dynamic_evidence() -> dict[str, object]:
            test_outputs: dict[str, object] = {}
            suite_outputs: dict[str, object] = {}
            errors: dict[str, str] = {}
            for record in records:
                trace_output = runtime_trace_outputs.get(record.record_key)
                if trace_output is None:
                    errors[record.record_key] = "Runtime trace is unavailable"
                    continue
                try:
                    output = analyze_dynamic_oracle(
                        DynamicOracleInput(
                            run_id=store.run_id,
                            record=record,
                            runtime_trace=trace_output.runtime_trace,
                            selector_grounding=grounding_by_record.get(record.record_key),
                            mutation_plan=mutation_plans.get(record.project_id),
                            mutation_results=mutation_results.get(record.project_id, []),
                        )
                    )
                    test_outputs[record.record_key] = output.model_dump(mode="json")
                except Exception as error:
                    errors[record.record_key] = f"{type(error).__name__}: {error}"

            requirements_by_suite = {item.suite_key: item for item in run.requirements}
            for suite_key, suite_records in selected_suites.items():
                contract = contracts.get(suite_key)
                if contract is None:
                    errors[suite_key] = "Requirement contract is unavailable"
                    continue
                project_id = suite_records[0].project_id
                try:
                    output = analyze_dynamic_suite_coverage(
                        DynamicSuiteCoverageInput(
                            run_id=store.run_id,
                            suite_key=suite_key,
                            contract=contract,
                            records=suite_records,
                            base_behavior_coverage=(
                                requirements_by_suite[suite_key].behavior_coverage
                                if suite_key in requirements_by_suite
                                else {}
                            ),
                            runtime_results={
                                record.record_key: runtime_by_record[record.record_key]
                                for record in suite_records
                                if record.record_key in runtime_by_record
                            },
                            selector_grounding={
                                record.record_key: grounding_by_record[record.record_key]
                                for record in suite_records
                                if record.record_key in grounding_by_record
                            },
                            mutation_plan=mutation_plans.get(project_id),
                            mutation_results=mutation_results.get(project_id, []),
                        )
                    )
                    suite_outputs[suite_key] = output.model_dump(mode="json")
                except Exception as error:
                    errors[suite_key] = f"{type(error).__name__}: {error}"
            return {"tests": test_outputs, "suites": suite_outputs, "errors": errors}

        dynamic_evidence_payload = _state_payload(
            store,
            "DYNAMIC_EVIDENCE",
            stable_hash(
                {
                    "contracts": contracts_payload["contracts"],
                    "basic_requirements": [
                        requirement.model_dump(mode="json") for requirement in run.requirements
                    ],
                    "grounding": grounding_payload["outputs"],
                    "runtime_traces": runtime_trace_payload["outputs"],
                    "mutation_plans": {
                        project_id: plan.model_dump(mode="json")
                        for project_id, plan in mutation_plans.items()
                    },
                    "mutation_results": {
                        project_id: [result.model_dump(mode="json") for result in results]
                        for project_id, results in mutation_results.items()
                    },
                }
            ),
            build_dynamic_evidence,
            recoverable=True,
            degraded_reason=lambda payload: (
                "; ".join(
                    f"{key}: {error}" for key, error in payload.get("errors", {}).items()  # type: ignore[union-attr]
                )
                or None
            ),
        )
        dynamic_test_outputs = {
            record_key: DynamicOracleOutput.model_validate(payload)
            for record_key, payload in dynamic_evidence_payload["tests"].items()  # type: ignore[union-attr]
        }
        dynamic_suite_outputs = {
            suite_key: DynamicSuiteCoverageOutput.model_validate(payload)
            for suite_key, payload in dynamic_evidence_payload["suites"].items()  # type: ignore[union-attr]
        }
        dynamic_evidence_artifacts = _write_dynamic_evidence_artifacts(
            config.output_dir,
            records,
            dynamic_test_outputs,
            dynamic_suite_outputs,
        )
        if dynamic_evidence_payload.get("errors"):
            run.runtime_warnings.append(
                f"Dynamic evidence failed for {len(dynamic_evidence_payload['errors'])} test/suite items."
            )

        def coordinate_full() -> dict[str, object]:
            coordinated = attach_source_grounding(run, grounding_by_record)
            coordinated = attach_runtime_results(coordinated, runtime_by_record)
            coordinated = attach_stability_results(coordinated, stability_by_record)
            coordinated = attach_runtime_traces(coordinated, runtime_trace_outputs)
            coordinated = attach_coverage_results(coordinated, coverage_reports)
            coordinated = attach_mutation_results(
                coordinated,
                mutation_plans,
                mutation_results,
                mutation_analyses,
            )
            if mutation_plans or mutation_results:
                coordinated.mutation_calibration = calibrate_static_mutation(
                    coordinated.tests,
                    mutation_plans,
                    mutation_results,
                )
            coordinated = attach_dynamic_evidence(
                coordinated,
                dynamic_test_outputs,
                dynamic_suite_outputs,
            )
            coordinated = coordinate_full_scores(coordinated)
            coordinated.mutation_analyses = mutation_analyses
            coordinated.mutation_results = mutation_results
            coordinated.artifacts.extend(
                ArtifactRef.model_validate(item)
                for item in (
                    list(source_payload.get("artifacts", []))
                    + list(grounding_payload.get("artifacts", []))
                    + list(baseline_payload.get("artifacts", []))
                    + list(stability_payload.get("artifacts", []))
                    + list(runtime_trace_payload.get("artifacts", []))
                    + [artifact.model_dump(mode="json") for artifact in coverage_artifacts]
                    + [artifact.model_dump(mode="json") for artifact in mutation_artifacts]
                    + [artifact.model_dump(mode="json") for artifact in dynamic_evidence_artifacts]
                )
            )
            return {"run": coordinated.model_dump(mode="json")}

        full_payload = _state_payload(
            store,
            "FULL_COORDINATE",
            stable_hash(
                {
                    "basic": coordinate_payload["run"],
                    "source_grounding": grounding_payload["outputs"],
                    "runtime": baseline_payload["results"],
                    "stability": stability_payload["reports"],
                    "runtime_traces": runtime_trace_payload["outputs"],
                    "coverage": {
                        record_key: report.model_dump(mode="json")
                        for record_key, report in coverage_reports.items()
                    },
                    "mutation_plans": {
                        project_id: plan.model_dump(mode="json")
                        for project_id, plan in mutation_plans.items()
                    },
                    "mutation_results": {
                        project_id: [result.model_dump(mode="json") for result in results]
                        for project_id, results in mutation_results.items()
                    },
                    "mutation_analyses": {
                        project_id: analysis.model_dump(mode="json")
                        for project_id, analysis in mutation_analyses.items()
                    },
                    "dynamic_evidence": {
                        "tests": dynamic_evidence_payload["tests"],
                        "suites": dynamic_evidence_payload["suites"],
                    },
                }
            ),
            coordinate_full,
        )
        run = EvaluationRun.model_validate(full_payload["run"])

    def execution_health():
        health = store.health()
        health.runtime_counts = dict(
            sorted(Counter(report.runtime.status for report in run.tests if report.runtime).items())
        )
        health.mutation_counts = dict(
            sorted(
                Counter(
                    result.status
                    for project_results in run.mutation_results.values()
                    for result in project_results
                ).items()
            )
        )
        health.total_runtime_seconds = sum(
            report.runtime.duration_seconds or 0.0
            for report in run.tests
            if report.runtime
        )
        health.flaky_test_count = sum(report.flaky for report in run.stability_reports.values())
        return health

    store.start("WRITE_REPORTS", stable_hash(run.model_dump(mode="json")))
    try:
        run.run_health = execution_health()
        destination = write_reports(run, config.output_dir)
        store.succeed(
            "WRITE_REPORTS",
            {
                "summary": str(destination / "summary.md"),
                "evaluation": str(destination / "evaluation.json"),
            },
        )
        store.complete()
        run.run_health = execution_health()
        write_reports(run, config.output_dir)
    except Exception as error:
        store.fail("WRITE_REPORTS", error, recoverable=False)
        raise
    return run


def evaluate_csv(config: EvaluationConfig) -> EvaluationRun:
    """Backward-compatible wrapper for the original CSV entry point."""

    return evaluate(config)
