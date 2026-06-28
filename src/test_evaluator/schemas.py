"""Pydantic contracts shared by deterministic checks and LLM agents."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class Status(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    INFO = "info"
    MINOR = "minor"
    MAJOR = "major"
    CRITICAL = "critical"


class Evidence(BaseModel):
    field: str = Field(description="CSV field or derived static artifact containing the evidence")
    quote: str = Field(description="Short verbatim excerpt from the input")
    line_start: int | None = Field(default=None, ge=1)
    line_end: int | None = Field(default=None, ge=1)


class Finding(BaseModel):
    criterion: str
    status: Status
    severity: Severity
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[Evidence] = Field(default_factory=list)
    reasoning: str
    suggested_fix: str | None = None


class Behavior(BaseModel):
    behavior_id: str
    kind: Literal["normal", "edge", "error", "persistence", "external_integration", "other"]
    preconditions: list[str] = Field(default_factory=list)
    actor_actions: list[str] = Field(default_factory=list)
    expected_observables: list[str] = Field(default_factory=list)
    state_effects: list[str] = Field(default_factory=list)
    ui_anchors: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    observability: Literal["dom", "storage", "mocked_api", "browser_api", "unknown"]
    source_evidence: list[Evidence] = Field(default_factory=list)


class RequirementContract(BaseModel):
    project_id: str
    requirement_id: str
    behaviors: list[Behavior]


class AgentReview(BaseModel):
    agent: Literal[
        "bdd_traceability",
        "step_code",
        "oracle_critic",
        "mutation_hypothesis",
        "suite_coverage",
        "static_verifier",
    ]
    record_key: str | None = None
    suite_key: str | None = None
    dimension: Literal[
        "spec_alignment",
        "step_traceability",
        "oracle_strength",
        "mutation_readiness",
        "robustness",
        "suite_adequacy",
    ]
    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding] = Field(default_factory=list)


class StaticFacts(BaseModel):
    python_parseable: bool
    syntax_error: str | None = None
    scenario_present: bool
    scenario_type: str | None = None
    gherkin_steps: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    assertion_count: int = 0
    trivial_assertion_count: int = 0
    requirement_test_ids: list[str] = Field(default_factory=list)
    gherkin_test_ids: list[str] = Field(default_factory=list)
    code_test_ids: list[str] = Field(default_factory=list)
    gherkin_ids_missing_from_code: list[str] = Field(default_factory=list)
    actions: list[str] = Field(default_factory=list)
    webdriver_wait_count: int = 0
    sleep_count: int = 0
    has_driver_quit: bool = False


class TestReport(BaseModel):
    record_key: str
    project_id: str
    requirement_id: str
    test_id: str
    scenario_type: str | None = None
    test_quality_score: float | None = Field(default=None, ge=0.0, le=100.0)
    mutation_readiness: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Static hypothesis only; never a real mutation score.",
    )
    confidence_coverage: float = Field(ge=0.0, le=1.0)
    risk: Literal["low", "medium", "major", "critical", "unknown"]
    hard_gates: list[str] = Field(default_factory=list)
    dimension_scores: dict[str, float | None] = Field(default_factory=dict)
    static_facts: StaticFacts
    reviews: list[AgentReview] = Field(default_factory=list)


class RequirementReport(BaseModel):
    suite_key: str
    project_id: str
    requirement_id: str
    partial_suite: bool = False
    test_count: int
    scenario_distribution: dict[str, int] = Field(default_factory=dict)
    requirement_adequacy_score: float | None = Field(default=None, ge=0.0, le=100.0)
    review: AgentReview | None = None
    behavior_coverage: dict[str, Status] = Field(default_factory=dict)


class SuiteAssessment(BaseModel):
    review: AgentReview
    behavior_coverage: dict[str, Status] = Field(default_factory=dict)


class BehaviorCoverageItem(BaseModel):
    behavior_id: str
    status: Status


class SuiteAgentOutput(BaseModel):
    """Compact LLM response used to construct a SuiteAssessment deterministically."""

    status: Status
    confidence: float = Field(ge=0.0, le=1.0)
    findings: list[Finding]
    behavior_coverage: list[BehaviorCoverageItem]


class ProjectReport(BaseModel):
    project_id: str
    test_count: int
    requirement_count: int
    average_test_quality_score: float | None = None
    average_requirement_adequacy_score: float | None = None
    risk_counts: dict[str, int] = Field(default_factory=dict)
    unknown_rate: float = 0.0


class EvaluationRun(BaseModel):
    mode: Literal["offline", "live"]
    model: str | None = None
    tests: list[TestReport]
    requirements: list[RequirementReport]
    projects: list[ProjectReport]
    runtime_warnings: list[str] = Field(default_factory=list)
