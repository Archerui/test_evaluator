"""Pydantic contracts shared by deterministic checks, agents, and orchestration."""

from __future__ import annotations

import re
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


Mode = Literal["basic", "full"]
SemanticMode = Literal["offline", "live"]
StateStatus = Literal["pending", "running", "succeeded", "failed", "skipped", "degraded", "retrying", "cached"]
OrchestratorState = Literal[
    "CREATED",
    "DISCOVER_INPUTS",
    "LOAD_RECORDS",
    "STATIC_VERIFY",
    "BUILD_REQUIREMENT_CONTRACTS",
    "BASIC_PARALLEL_REVIEWS",
    "BASIC_SUITE_REVIEW",
    "BASIC_COORDINATE",
    "SOURCE_MODEL",
    "SOURCE_GROUNDING",
    "MATERIALIZE_TESTS",
    "RUN_BASELINE_TESTS",
    "STABILITY_ANALYZE",
    "RUNTIME_TRACE",
    "COVERAGE",
    "MUTATION_GENERATE",
    "MUTATION_RUN",
    "MUTATION_ANALYZE",
    "DYNAMIC_EVIDENCE",
    "FULL_COORDINATE",
    "WRITE_REPORTS",
    "COMPLETED",
    "FAILED",
]
ArtifactKind = Literal[
    "stdout",
    "stderr",
    "behave_json",
    "screenshot",
    "dom_snapshot",
    "console_log",
    "browser_trace",
    "network_log",
    "source_model",
    "coverage",
    "mutation_result",
    "workspace",
    "checkpoint",
    "report",
    "inventory",
    "runtime_result",
    "selector_grounding",
    "runtime_trace",
    "dynamic_evidence",
    "stability_report",
]


class Status(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"
    SKIPPED = "SKIPPED"


class Severity(str, Enum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class ArtifactRef(BaseModel):
    kind: ArtifactKind
    path: str
    description: str | None = None
    sha256: str | None = None


class Evidence(BaseModel):
    field: str = Field(description="Input field, source file, runtime artifact, or derived fact containing the evidence")
    quote: str | None = Field(default=None, description="Short verbatim excerpt when textual evidence exists")
    file_path: str | None = None
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)
    artifact: ArtifactRef | None = None


class Finding(BaseModel):
    criterion: str
    status: Status
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning: str
    suggested_fix: str | None = None


class TestRecord(BaseModel):
    """Normalized test record accepted from CSV, JSONL, or E2EDev project JSON."""

    project_id: str
    requirement_id: str
    test_id: str
    requirement_summary: str = ""
    requirement: str
    scenario: str
    step_code: str
    reference_answer: str = ""
    input_origin: Literal["csv", "jsonl", "requirment_with_tests"] = "csv"
    project_root: str | None = None
    source_root: str | None = None

    @property
    def record_key(self) -> str:
        return f"{self.project_id}::{self.requirement_id}::{self.test_id}"

    @property
    def suite_key(self) -> str:
        return f"{self.project_id}::{self.requirement_id}"

    @property
    def scenario_type(self) -> str | None:
        match = re.search(r"Scenario:\s*\[([^\]]+)\]", self.scenario)
        return match.group(1).strip() if match else None


class ProjectInventoryInput(BaseModel):
    run_id: str
    mode: Mode
    input_path: str | None = None
    e2edev_root: str | None = None
    selected_projects: list[str] | None = None
    selected_requirements: list[str] | None = None
    selected_tests: list[str] | None = None


class ProjectInventory(BaseModel):
    project_id: str
    project_root: str | None = None
    source_root: str | None = None
    entry_html: str | None = None
    tests_file: str | None = None
    requirements_file: str | None = None
    web_application_analysis_file: str | None = None
    source_files: list[str] = Field(default_factory=list)
    asset_files: list[str] = Field(default_factory=list)
    test_count: int = 0
    requirement_count: int = 0
    discovery_status: Status = Status.PASS
    warnings: list[str] = Field(default_factory=list)


class ProjectDiscoveryOutput(BaseModel):
    run_id: str
    mode: Mode
    projects: list[ProjectInventory]
    records: list[TestRecord] = Field(default_factory=list)


class Behavior(BaseModel):
    behavior_id: str
    kind: Literal["normal", "edge", "error", "persistence", "external_integration", "other"]
    preconditions: list[str] = Field(default_factory=list)
    actor_actions: list[str] = Field(default_factory=list)
    expected_observables: list[str] = Field(default_factory=list)
    state_effects: list[str] = Field(default_factory=list)
    ui_anchors: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    observability: Literal[
        "dom",
        "storage",
        "mocked_api",
        "browser_api",
        "network",
        "canvas",
        "audio",
        "unknown",
    ]
    source_evidence: list[Evidence] = Field(default_factory=list)


class RequirementContract(BaseModel):
    project_id: str
    requirement_id: str
    suite_key: str | None = None
    behaviors: list[Behavior]


class AgentReview(BaseModel):
    """Compact review currently used by the basic coordinator and LLM agents."""

    agent: Literal[
        "requirement_agent",
        "bdd_traceability",
        "step_code",
        "oracle_critic",
        "mutation_hypothesis",
        "suite_coverage",
        "static_verifier",
        "source_model",
        "selector_grounding",
        "test_materializer",
        "test_runner",
        "runtime_trace",
        "failure_attribution",
        "coverage",
        "mutation_generator",
        "mutation_runner",
        "mutation_analyst",
        "dynamic_oracle",
        "dynamic_suite_coverage",
        "stability_analyzer",
        "basic_coordinator",
        "full_coordinator",
    ]
    record_key: str | None = None
    suite_key: str | None = None
    project_id: str | None = None
    dimension: Literal[
        "spec_alignment",
        "step_traceability",
        "oracle_strength",
        "mutation_readiness",
        "robustness",
        "suite_adequacy",
        "source_grounding",
        "runtime_result",
        "runtime_attribution",
        "coverage",
        "mutation_effectiveness",
        "dynamic_oracle_evidence",
        "dynamic_behavior_coverage",
        "stability",
    ]
    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding] = Field(default_factory=list)


class AssertionDataFlow(BaseModel):
    """Deterministic approximation of what an assertion actually observes."""

    expression: str
    sources: list[
        Literal[
            "data_transfer",
            "drag_event",
            "dom_text",
            "dom_attribute",
            "constant",
            "unknown",
        ]
    ] = Field(default_factory=list)
    classification: Literal[
        "event_payload_observation",
        "self_fulfilled_event_payload",
        "data_transfer_observation",
        "dom_observation",
        "element_attribute_proxy",
        "constant",
        "mixed",
        "unknown",
    ]
    data_transfer_read_keys: list[str] = Field(default_factory=list)
    data_transfer_set_keys: list[str] = Field(default_factory=list)
    drag_event_dispatched: bool = False


class DataFlowFacts(BaseModel):
    """Static DataTransfer/DragEvent/DOM-to-assert flow summary."""

    execute_script_count: int = 0
    data_transfer_creation_count: int = 0
    drag_event_creation_count: int = 0
    drag_event_dispatch_count: int = 0
    data_transfer_read_keys: list[str] = Field(default_factory=list)
    data_transfer_set_keys: list[str] = Field(default_factory=list)
    assertions: list[AssertionDataFlow] = Field(default_factory=list)
    event_payload_assertion_count: int = 0
    self_fulfilled_event_payload_assertion_count: int = 0
    dom_assertion_count: int = 0
    element_attribute_proxy_assertion_count: int = 0
    constant_assertion_count: int = 0
    unknown_assertion_count: int = 0


class StaticFacts(BaseModel):
    python_parseable: bool
    syntax_error: str | None = None
    scenario_present: bool
    scenario_type: str | None = None
    gherkin_steps: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    missing_step_definitions: list[str] = Field(default_factory=list)
    duplicate_step_definitions: list[str] = Field(default_factory=list)
    assertion_count: int = 0
    trivial_assertion_count: int = 0
    print_only_oracle_count: int = 0
    requirement_test_ids: list[str] = Field(default_factory=list)
    gherkin_test_ids: list[str] = Field(default_factory=list)
    code_test_ids: list[str] = Field(default_factory=list)
    gherkin_ids_missing_from_code: list[str] = Field(default_factory=list)
    selectors: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    webdriver_wait_count: int = 0
    sleep_count: int = 0
    has_driver_quit: bool = False
    hardcoded_file_paths: list[str] = Field(default_factory=list)
    direct_event_construction: list[str] = Field(default_factory=list)
    data_flow: DataFlowFacts = Field(default_factory=DataFlowFacts)


class AgentEnvelope(BaseModel):
    """General full-mode envelope for non-basic artifacts and diagnostics."""

    agent: str
    run_id: str
    mode: Mode
    project_id: str | None = None
    suite_key: str | None = None
    record_key: str | None = None
    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class DomAnchor(BaseModel):
    selector: str
    tag: str
    text: str | None = None
    attributes: dict[str, str] = Field(default_factory=dict)
    file_path: str
    line_start: int | None = None


class EventHandler(BaseModel):
    event: str
    selector: str | None = None
    function_name: str | None = None
    file_path: str
    line_start: int | None = None
    behavior_candidates: list[str] = Field(default_factory=list)


class StateEffect(BaseModel):
    kind: Literal["dom_update", "storage_write", "storage_read", "calculation", "api_call", "navigation", "unknown"]
    target: str
    file_path: str
    line_start: int | None = None
    behavior_candidates: list[str] = Field(default_factory=list)


class SourceModel(BaseModel):
    project_id: str
    source_root: str
    entry_html: str | None = None
    dom_anchors: list[DomAnchor] = Field(default_factory=list)
    event_handlers: list[EventHandler] = Field(default_factory=list)
    state_effects: list[StateEffect] = Field(default_factory=list)
    external_apis: list[str] = Field(default_factory=list)
    source_files: list[str] = Field(default_factory=list)
    parse_warnings: list[str] = Field(default_factory=list)


class SelectorGroundingItem(BaseModel):
    selector: str
    source_exists: bool
    matched_anchors: list[DomAnchor] = Field(default_factory=list)
    stability: Literal["stable", "medium", "brittle", "unknown"]
    purpose: Literal["precondition", "action_target", "oracle_target", "unknown"]
    evidence: list[Evidence] = Field(default_factory=list)


class WorkspaceSpec(BaseModel):
    record_key: str
    workspace_root: str
    app_root: str
    feature_file: str
    steps_file: str
    entry_html: str
    artifacts_dir: str
    rewritten_paths: list[dict[str, str]] = Field(default_factory=list)


class RuntimeResult(BaseModel):
    record_key: str
    status: Literal["pass", "fail", "timeout", "env_error", "skipped"]
    duration_seconds: float | None = None
    failed_step: str | None = None
    error_type: Literal[
        "assertion_failure",
        "selector_not_found",
        "syntax_error",
        "browser_error",
        "path_error",
        "timeout",
        "env_error",
        "unknown",
    ] | None = None
    stdout: ArtifactRef | None = None
    stderr: ArtifactRef | None = None
    behave_json: ArtifactRef | None = None
    screenshot: ArtifactRef | None = None
    dom_snapshot: ArtifactRef | None = None
    console_log: ArtifactRef | None = None
    browser_trace: ArtifactRef | None = None
    network_log: ArtifactRef | None = None


class RuntimeObservation(BaseModel):
    kind: Literal[
        "step_result",
        "dom_state",
        "console",
        "screenshot",
        "exception",
        "timing",
        "storage",
        "network",
        "browser_api",
    ]
    summary: str
    evidence: list[Evidence] = Field(default_factory=list)


class FailureAttribution(BaseModel):
    """Conservative ownership decision for a raw runtime failure.

    The attribution is explicitly about the quality of the evaluated test. A
    failed application, environment, or evaluator does not automatically make
    the test defective.
    """

    origin: Literal[
        "no_failure",
        "test_defect",
        "application_defect",
        "environment_issue",
        "evaluator_issue",
        "contract_or_dataset_mismatch",
        "indeterminate",
    ]
    confidence: float = Field(ge=0.0, le=1.0)
    test_quality_effect: Literal["pass", "penalize", "neutral", "unknown"]
    reasoning: str
    signals: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class RuntimeTrace(BaseModel):
    record_key: str
    execution_status: RuntimeResult
    observations: list[RuntimeObservation] = Field(default_factory=list)
    likely_failure_cause: Literal[
        "test_bug",
        "app_bug",
        "oracle_mismatch",
        "selector_issue",
        "path_issue",
        "environment_issue",
        "timeout_or_flaky",
        "contract_or_dataset_mismatch",
        "evaluator_issue",
        "indeterminate",
        "no_failure",
        "unknown",
    ] = "unknown"
    flaky_risk: Literal["low", "medium", "high", "unknown"] = "unknown"
    failure_attribution: FailureAttribution | None = None


class StabilityAttempt(BaseModel):
    run_index: int
    status: Literal["pass", "fail", "timeout", "env_error", "skipped"]
    duration_seconds: float | None = None
    error_type: str | None = None


class StabilityReport(BaseModel):
    record_key: str
    requested_runs: int
    completed_runs: int
    pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    flaky: bool = False
    status: Status = Status.UNKNOWN
    attempts: list[StabilityAttempt] = Field(default_factory=list)


class FileCoverage(BaseModel):
    file_path: str
    statement_coverage: float | None = None
    branch_coverage: float | None = None
    function_coverage: float | None = None
    executed_ranges: list[dict[str, object]] = Field(default_factory=list)


class CoverageReport(BaseModel):
    project_id: str
    record_key: str
    method: str
    status: Status
    files: list[FileCoverage] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)


class MutantSpec(BaseModel):
    mutant_id: str
    project_id: str
    operator: str
    file_path: str
    line_start: int | None = None
    original: str
    mutated: str
    behavior_candidates: list[str] = Field(default_factory=list)
    impacted_record_keys: list[str] = Field(default_factory=list)
    suspected_equivalent: bool = False


class MutationPlan(BaseModel):
    project_id: str
    mutants: list[MutantSpec] = Field(default_factory=list)
    skipped_candidates: list[dict[str, object]] = Field(default_factory=list)


class MutationRunResult(BaseModel):
    mutant_id: str
    status: Literal["killed", "survived", "timeout", "invalid", "skipped"]
    killed_by_record_keys: list[str] = Field(default_factory=list)
    survived_record_keys: list[str] = Field(default_factory=list)
    runtime_artifacts: list[ArtifactRef] = Field(default_factory=list)
    error_summary: str | None = None


class MutationBehaviorSummary(BaseModel):
    behavior_id: str
    total_mutants: int
    killed: int
    survived: int
    timeout: int
    invalid: int
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    survived_mutants: list[str] = Field(default_factory=list)
    suspected_equivalent_mutants: list[str] = Field(default_factory=list)
    interpretation: str = ""


class MutationAnalysis(BaseModel):
    project_id: str
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    behavior_summaries: list[MutationBehaviorSummary] = Field(default_factory=list)
    top_survived_mutants: list[MutantSpec] = Field(default_factory=list)


MutationFaultClass = Literal[
    "event_name",
    "event_handler",
    "dom_update",
    "api_call",
    "string_literal",
    "comparison",
    "boolean_literal",
    "numeric_literal",
    "arithmetic",
]


class StaticMutationHypothesis(BaseModel):
    hypothesis_id: str
    fault_class: MutationFaultClass
    behavior_ids: list[str] = Field(default_factory=list)
    description: str
    prediction: Literal["likely_detected", "likely_survives", "unknown"]
    confidence: float = Field(ge=0.0, le=1.0)
    rationale: str


class StaticMutationAssessment(BaseModel):
    record_key: str
    hypotheses: list[StaticMutationHypothesis] = Field(default_factory=list)
    readiness_score: float | None = Field(default=None, ge=0.0, le=100.0)
    prediction_coverage: float = Field(default=0.0, ge=0.0, le=1.0)


class MutationCalibrationObservation(BaseModel):
    record_key: str
    hypothesis_id: str
    mutant_id: str
    fault_class: MutationFaultClass
    prediction: Literal["likely_detected", "likely_survives"]
    actual: Literal["killed", "survived"]
    matched: bool


class MutationCalibrationRecommendation(BaseModel):
    fault_class: MutationFaultClass
    issue: Literal["static_overconfidence", "static_underconfidence"]
    observation_count: int
    action: str


class MutationCalibrationReport(BaseModel):
    source: Literal["full_mutation_outcomes"] = "full_mutation_outcomes"
    scoring_effect: Literal["none"] = "none"
    observation_count: int = 0
    matched_count: int = 0
    accuracy: float | None = Field(default=None, ge=0.0, le=1.0)
    confusion: dict[str, int] = Field(default_factory=dict)
    by_fault_class: dict[str, dict[str, float | int | None]] = Field(default_factory=dict)
    observations: list[MutationCalibrationObservation] = Field(default_factory=list)
    recommendations: list[MutationCalibrationRecommendation] = Field(default_factory=list)


class BehaviorCoverage(BaseModel):
    behavior_id: str
    status: Status
    covered_by_records: list[str] = Field(default_factory=list)
    runtime_confirmed_by_records: list[str] = Field(default_factory=list)
    killed_by_mutants: list[str] = Field(default_factory=list)
    survived_mutants: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class BehaviorCoverageItem(BaseModel):
    behavior_id: str
    status: Status
    covered_by_records: list[str] = Field(default_factory=list)
    strong_by_records: list[str] = Field(default_factory=list)
    weak_by_records: list[str] = Field(default_factory=list)


class SuiteBehaviorStatusItem(BaseModel):
    behavior_id: str
    status: Status


class SuiteDuplicateGroup(BaseModel):
    group_id: str
    kind: Literal["exact_scenario", "semantic_scenario", "oracle_shape"]
    record_keys: list[str]
    signature: str
    rationale: str


class SuiteStaticAnalysis(BaseModel):
    duplicate_groups: list[SuiteDuplicateGroup] = Field(default_factory=list)
    unique_contribution_records: list[str] = Field(default_factory=list)
    semantic_duplicate_ratio: float = Field(default=0.0, ge=0.0, le=1.0)


class SuiteAgentOutput(BaseModel):
    """Compact LLM response used to construct a SuiteAssessment deterministically."""

    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding]
    behavior_coverage: list[SuiteBehaviorStatusItem]


class SuiteAssessment(BaseModel):
    review: AgentReview
    behavior_coverage: dict[str, Status] = Field(default_factory=dict)
    behavior_coverage_details: list[BehaviorCoverageItem] = Field(default_factory=list)


class DimensionScores(BaseModel):
    spec_alignment: float | None = None
    step_traceability: float | None = None
    oracle_strength: float | None = None
    robustness: float | None = None
    source_grounding: float | None = None
    runtime_result: float | None = None
    coverage: float | None = None
    mutation_effectiveness: float | None = None


class TestReport(BaseModel):
    record_key: str
    project_id: str
    requirement_id: str
    test_id: str
    scenario_type: str | None = None
    evaluation_mode: Mode = "basic"
    test_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    basic_test_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    full_test_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    mutation_readiness: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Static hypothesis only; never a real mutation score.",
    )
    static_mutation: "StaticMutationAssessment | None" = None
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    confidence_coverage: float = Field(ge=0.0, le=1.0)
    basic_confidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    full_confidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    risk: Literal["low", "medium", "major", "critical", "unknown"]
    hard_gates: list[str] = Field(default_factory=list)
    dimension_scores: dict[str, float | None] = Field(default_factory=dict)
    static_facts: StaticFacts
    runtime: RuntimeResult | None = None
    runtime_trace: RuntimeTrace | None = None
    stability: StabilityReport | None = None
    coverage: CoverageReport | None = None
    reviews: list[AgentReview] = Field(default_factory=list)


class RequirementReport(BaseModel):
    suite_key: str
    project_id: str
    requirement_id: str
    evaluation_mode: Mode = "basic"
    partial_suite: bool = False
    test_count: int
    scenario_distribution: dict[str, int] = Field(default_factory=dict)
    requirement_adequacy_score: float | None = Field(default=None, ge=0.0, le=100.0)
    basic_requirement_adequacy_score: float | None = Field(default=None, ge=0.0, le=100.0)
    full_requirement_adequacy_score: float | None = Field(default=None, ge=0.0, le=100.0)
    runtime_pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    basic_confidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    full_confidence_coverage: float = Field(default=0.0, ge=0.0, le=1.0)
    review: AgentReview | None = None
    behavior_coverage: dict[str, Status] = Field(default_factory=dict)
    behavior_coverage_details: list[BehaviorCoverageItem] = Field(default_factory=list)
    suite_static_analysis: SuiteStaticAnalysis = Field(default_factory=SuiteStaticAnalysis)
    dynamic_review: AgentReview | None = None
    dynamic_behavior_coverage: list[BehaviorCoverage] = Field(default_factory=list)
    flaky_test_count: int = 0


class ProjectReport(BaseModel):
    project_id: str
    evaluation_mode: Mode = "basic"
    test_count: int
    requirement_count: int
    average_test_quality_score: float | None = None
    average_basic_test_quality_score: float | None = None
    average_full_test_quality_score: float | None = None
    average_requirement_adequacy_score: float | None = None
    runtime_pass_rate: float | None = Field(default=None, ge=0.0, le=1.0)
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    risk_counts: dict[str, int] = Field(default_factory=dict)
    unknown_rate: float = 0.0
    flaky_test_count: int = 0


class StateCheckpoint(BaseModel):
    run_id: str
    state: OrchestratorState
    status: StateStatus
    started_at: str | None = None
    finished_at: str | None = None
    attempts: int = 0
    input_hash: str | None = None
    output_artifacts: list[ArtifactRef] = Field(default_factory=list)
    error_summary: str | None = None
    recoverable: bool = True


class RunManifest(BaseModel):
    run_id: str
    mode: Mode
    semantic_mode: SemanticMode
    output_dir: str
    config_hash: str
    current_state: OrchestratorState
    checkpoints: list[StateCheckpoint] = Field(default_factory=list)
    project_status: dict[str, StateStatus] = Field(default_factory=dict)
    record_status: dict[str, StateStatus] = Field(default_factory=dict)
    mutant_status: dict[str, StateStatus] = Field(default_factory=dict)


class RunHealth(BaseModel):
    state_counts: dict[str, int] = Field(default_factory=dict)
    degraded_reasons: list[str] = Field(default_factory=list)
    failed_reasons: list[str] = Field(default_factory=list)
    retry_counts: dict[str, int] = Field(default_factory=dict)
    cache_hits: int = 0
    cache_misses: int = 0
    resume_used: bool = False
    runtime_counts: dict[str, int] = Field(default_factory=dict)
    mutation_counts: dict[str, int] = Field(default_factory=dict)
    total_runtime_seconds: float = 0.0
    flaky_test_count: int = 0
    stage_durations_seconds: dict[str, float] = Field(default_factory=dict)


class EvaluationRun(BaseModel):
    run_id: str = ""
    mode: Mode = "basic"
    semantic_mode: SemanticMode = "offline"
    model: str | None = None
    config: dict[str, object] = Field(default_factory=dict)
    tests: list[TestReport]
    requirements: list[RequirementReport]
    projects: list[ProjectReport]
    inventories: list[ProjectInventory] = Field(default_factory=list)
    run_health: RunHealth | None = None
    runtime_warnings: list[str] = Field(default_factory=list)
    artifacts: list[ArtifactRef] = Field(default_factory=list)
    mutation_analyses: dict[str, MutationAnalysis] = Field(default_factory=dict)
    mutation_results: dict[str, list[MutationRunResult]] = Field(default_factory=dict)
    mutation_calibration: "MutationCalibrationReport | None" = None
    runtime_traces: dict[str, RuntimeTrace] = Field(default_factory=dict)
    coverage_reports: dict[str, CoverageReport] = Field(default_factory=dict)
    stability_reports: dict[str, StabilityReport] = Field(default_factory=dict)


# Agent-specific input/output contracts. The current basic pipeline still uses
# AgentReview internally; these models define the stable boundary for the full
# pipeline as it is implemented in later phases.


class StaticVerifierInput(BaseModel):
    run_id: str
    record: TestRecord


class StaticVerifierOutput(AgentEnvelope):
    agent: Literal["static_verifier"]
    dimension: Literal["robustness"]
    facts: StaticFacts


class RequirementAgentInput(BaseModel):
    run_id: str
    project_id: str
    requirement_id: str
    suite_key: str
    requirement_summary: str | None = None
    fine_grained_requirement: str
    source_requirements: list[str] = Field(default_factory=list)
    web_application_analysis: dict[str, object] = Field(default_factory=dict)


class RequirementAgentOutput(AgentEnvelope):
    agent: Literal["requirement_agent"]
    contract: RequirementContract


class BehaviorScenarioMapping(BaseModel):
    behavior_id: str
    gherkin_steps: list[str] = Field(default_factory=list)
    coverage_status: Status
    evidence: list[Evidence] = Field(default_factory=list)


class BDDTraceabilityInput(BaseModel):
    run_id: str
    record: TestRecord
    contract: RequirementContract
    static_facts: StaticFacts


class BDDTraceabilityOutput(AgentEnvelope):
    agent: Literal["bdd_traceability"]
    dimension: Literal["spec_alignment"]
    behavior_mappings: list[BehaviorScenarioMapping] = Field(default_factory=list)
    missing_behaviors: list[str] = Field(default_factory=list)
    unsupported_scenario_claims: list[str] = Field(default_factory=list)


class StepImplementationMapping(BaseModel):
    gherkin_step: str
    decorator: str | None = None
    function_name: str | None = None
    implementation_status: Status
    action_observed: bool | None = None
    selectors_used: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)


class StepCodeInput(BaseModel):
    run_id: str
    record: TestRecord
    contract: RequirementContract
    static_facts: StaticFacts
    source_model: SourceModel | None = None
    runtime_result: RuntimeResult | None = None


class StepCodeOutput(AgentEnvelope):
    agent: Literal["step_code"]
    dimension: Literal["step_traceability"]
    step_mappings: list[StepImplementationMapping] = Field(default_factory=list)
    missing_steps: list[str] = Field(default_factory=list)
    misleading_steps: list[str] = Field(default_factory=list)


class OracleCheck(BaseModel):
    behavior_id: str
    expected_observable: str
    observed_by_test: bool
    oracle_type: Literal[
        "assert_dom",
        "assert_storage",
        "assert_browser_api",
        "assert_network",
        "assert_calculation",
        "assert_exception",
        "print_only",
        "placeholder",
        "none",
        "unknown",
    ]
    strength: Literal["strong", "medium", "weak", "none", "unknown"]
    evidence: list[Evidence] = Field(default_factory=list)


class OracleCriticInput(BaseModel):
    run_id: str
    record: TestRecord
    contract: RequirementContract
    static_facts: StaticFacts
    source_model: SourceModel | None = None
    runtime_trace: RuntimeTrace | None = None
    mutation_analysis: MutationAnalysis | None = None


class OracleCriticOutput(AgentEnvelope):
    agent: Literal["oracle_critic"]
    dimension: Literal["oracle_strength"]
    oracle_checks: list[OracleCheck] = Field(default_factory=list)
    critical_oracle_gaps: list[str] = Field(default_factory=list)


class SuiteCoverageInput(BaseModel):
    run_id: str
    suite_key: str
    project_id: str
    requirement_id: str
    contract: RequirementContract
    records: list[TestRecord]
    test_reviews: list[AgentReview]
    runtime_results: list[RuntimeResult] = Field(default_factory=list)
    mutation_analysis: list[MutationAnalysis] = Field(default_factory=list)


class SuiteCoverageOutput(AgentEnvelope):
    agent: Literal["suite_coverage"]
    dimension: Literal["suite_adequacy"]
    behavior_coverage: list[BehaviorCoverage] = Field(default_factory=list)
    scenario_distribution: dict[str, int] = Field(default_factory=dict)
    duplicate_scenarios: list[list[str]] = Field(default_factory=list)
    missing_behavior_ids: list[str] = Field(default_factory=list)


class SourceModelInput(BaseModel):
    run_id: str
    inventory: ProjectInventory
    contract_by_suite: dict[str, RequirementContract] = Field(default_factory=dict)


class SourceModelOutput(AgentEnvelope):
    agent: Literal["source_model"]
    source_model: SourceModel


class SelectorGroundingInput(BaseModel):
    run_id: str
    record: TestRecord
    contract: RequirementContract
    static_facts: StaticFacts
    source_model: SourceModel


class SelectorGroundingOutput(AgentEnvelope):
    agent: Literal["selector_grounding"]
    dimension: Literal["source_grounding"]
    selectors: list[SelectorGroundingItem] = Field(default_factory=list)
    missing_source_anchors: list[str] = Field(default_factory=list)


class TestMaterializerInput(BaseModel):
    run_id: str
    inventory: ProjectInventory
    record: TestRecord
    output_dir: str
    instrumentation: dict[str, object] = Field(default_factory=dict)


class TestMaterializerOutput(AgentEnvelope):
    agent: Literal["test_materializer"]
    workspace: WorkspaceSpec


class TestRunnerInput(BaseModel):
    run_id: str
    workspace: WorkspaceSpec
    timeout_seconds: float
    headless: bool = True
    retry_index: int = 0
    collect_coverage: bool = False
    coverage_method: Literal["cdp_precise_coverage", "istanbul", "none"] = "none"
    browser_stubs: list[str] = Field(default_factory=list)


class TestRunnerOutput(AgentEnvelope):
    agent: Literal["test_runner"]
    runtime: RuntimeResult


class RuntimeTraceInput(BaseModel):
    run_id: str
    record: TestRecord
    runtime: RuntimeResult
    static_facts: StaticFacts
    source_model: SourceModel | None = None
    contract: RequirementContract | None = None
    reviews: list[AgentReview] = Field(default_factory=list)
    selector_grounding: SelectorGroundingOutput | None = None
    stability: StabilityReport | None = None


class RuntimeTraceOutput(AgentEnvelope):
    agent: Literal["runtime_trace"]
    runtime_trace: RuntimeTrace


class CoverageInput(BaseModel):
    run_id: str
    inventory: ProjectInventory
    workspace: WorkspaceSpec
    runtime: RuntimeResult
    method: Literal["auto", "cdp_precise_coverage", "istanbul", "none"]
    browser_stubs: list[str] = Field(default_factory=list)


class CoverageOutput(AgentEnvelope):
    agent: Literal["coverage"]
    coverage: CoverageReport


class MutationGeneratorInput(BaseModel):
    run_id: str
    inventory: ProjectInventory
    source_model: SourceModel
    contracts: list[RequirementContract]
    max_mutants: int
    operators: list[str] = Field(default_factory=list)


class MutationGeneratorOutput(AgentEnvelope):
    agent: Literal["mutation_generator"]
    plan: MutationPlan


class MutationRunnerInput(BaseModel):
    run_id: str
    mutant: MutantSpec
    base_workspace_root: str
    tests_to_run: list[TestRecord]
    timeout_seconds: float
    browser_stubs: list[str] = Field(default_factory=list)


class MutationRunnerOutput(AgentEnvelope):
    agent: Literal["mutation_runner"]
    result: MutationRunResult


class MutationAnalystInput(BaseModel):
    run_id: str
    project_id: str
    contract_by_suite: dict[str, RequirementContract]
    source_model: SourceModel
    mutation_plan: MutationPlan
    mutation_results: list[MutationRunResult]
    test_reviews: list[AgentReview]


class MutationAnalystOutput(AgentEnvelope):
    agent: Literal["mutation_analyst"]
    analysis: MutationAnalysis


class DynamicOracleInput(BaseModel):
    run_id: str
    record: TestRecord
    runtime_trace: RuntimeTrace
    selector_grounding: SelectorGroundingOutput | None = None
    mutation_plan: MutationPlan | None = None
    mutation_results: list[MutationRunResult] = Field(default_factory=list)


class DynamicOracleOutput(AgentEnvelope):
    agent: Literal["dynamic_oracle"]
    dimension: Literal["dynamic_oracle_evidence"]
    runtime_confirmed: bool = False
    oracle_selectors: list[str] = Field(default_factory=list)
    mutation_score: float | None = Field(default=None, ge=0.0, le=100.0)
    killed_mutants: list[str] = Field(default_factory=list)
    survived_mutants: list[str] = Field(default_factory=list)


class DynamicSuiteCoverageInput(BaseModel):
    run_id: str
    suite_key: str
    contract: RequirementContract
    records: list[TestRecord]
    base_behavior_coverage: dict[str, Status] = Field(default_factory=dict)
    runtime_results: dict[str, RuntimeResult] = Field(default_factory=dict)
    selector_grounding: dict[str, SelectorGroundingOutput] = Field(default_factory=dict)
    mutation_plan: MutationPlan | None = None
    mutation_results: list[MutationRunResult] = Field(default_factory=list)


class DynamicSuiteCoverageOutput(AgentEnvelope):
    agent: Literal["dynamic_suite_coverage"]
    dimension: Literal["dynamic_behavior_coverage"]
    behavior_coverage: list[BehaviorCoverage] = Field(default_factory=list)
