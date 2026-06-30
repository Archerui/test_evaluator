"""Deterministic requirement-suite duplicate analysis."""

from __future__ import annotations

from collections import Counter, defaultdict
import hashlib
import math
import re

from .schemas import (
    Behavior,
    BehaviorCoverageItem,
    RequirementContract,
    StaticFacts,
    Status,
    SuiteDuplicateGroup,
    SuiteStaticAnalysis,
    TestRecord,
)


_STEP_RE = re.compile(r"^\s*(?:Given|When|Then|And|But)\s+(.+?)\s*$", re.MULTILINE | re.IGNORECASE)
_QUOTED_RE = re.compile(r"(['\"])(?:\\.|(?!\1).)*\1")
_NUMBER_RE = re.compile(r"(?<![A-Za-z])[-+]?\$?\d+(?:\.\d+)?")
_TEST_ID_SUFFIX_RE = re.compile(r"(?<=-)[0-9]+\b")
_WORD_RE = re.compile(r"[A-Za-z0-9_-]{3,}")
_STOP_WORDS = {
    "and", "are", "displayed", "each", "element", "elements", "exists", "for", "from",
    "item", "list", "none", "operation", "product", "rendered", "required", "should",
    "state", "that", "the", "then", "user", "verification", "visible", "when", "with"
}


def _scenario_steps(scenario: str) -> list[str]:
    return [re.sub(r"\s+", " ", step).strip().casefold() for step in _STEP_RE.findall(scenario)]


def _signature(parts: list[str]) -> str:
    return " | ".join(parts)


def _semantic_step(step: str) -> str:
    value = _QUOTED_RE.sub("<value>", step)
    value = _TEST_ID_SUFFIX_RE.sub("<n>", value)
    value = _NUMBER_RE.sub("<number>", value)
    return re.sub(r"\s+", " ", value).strip()


def _group_id(kind: str, signature: str) -> str:
    digest = hashlib.sha256(f"{kind}:{signature}".encode("utf-8")).hexdigest()[:10]
    return f"{kind}-{digest}"


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _WORD_RE.findall(value)
        if token.casefold() not in _STOP_WORDS
    }


def _behavior_parts(behavior: Behavior) -> tuple[str, str]:
    action = " ".join([*behavior.preconditions, *behavior.actor_actions])
    outcome = " ".join(behavior.expected_observables)
    return action, outcome


def _negative(value: str) -> bool:
    normalized = f" {value.casefold()} "
    return any(marker in normalized for marker in (" no ", " not ", " cannot ", " without "))


def analyze_static_behavior_coverage(
    records: list[TestRecord],
    contract: RequirementContract,
) -> list[BehaviorCoverageItem]:
    """Map scenarios to behaviors without using source code or runtime results."""

    details: list[BehaviorCoverageItem] = []
    for behavior in contract.behaviors:
        action_text, outcome_text = _behavior_parts(behavior)
        action_tokens = _tokens(action_text)
        outcome_tokens = _tokens(outcome_text)
        behavior_is_negative = _negative(outcome_text)
        strong: list[str] = []
        weak: list[str] = []
        for record in records:
            steps = _scenario_steps(record.scenario)
            then_text = " ".join(steps[1:])
            scenario_tokens = _tokens(" ".join(steps))
            action_overlap = len(action_tokens.intersection(scenario_tokens))
            outcome_overlap = len(outcome_tokens.intersection(scenario_tokens))
            action_threshold = max(2, math.ceil(len(action_tokens) * 0.30))
            outcome_threshold = max(2, math.ceil(len(outcome_tokens) * 0.30))
            action_supported = not action_tokens or action_overlap >= action_threshold
            outcome_supported = not outcome_tokens or outcome_overlap >= outcome_threshold
            polarity_matches = behavior_is_negative == _negative(then_text)
            if action_supported and outcome_supported and polarity_matches:
                strong.append(record.record_key)
            elif action_overlap + outcome_overlap >= 2:
                weak.append(record.record_key)
        weak = sorted(set(weak).difference(strong))
        strong = sorted(set(strong))
        status = Status.PASS if strong else Status.WARNING if weak else Status.FAIL
        details.append(
            BehaviorCoverageItem(
                behavior_id=behavior.behavior_id,
                status=status,
                covered_by_records=sorted([*strong, *weak]),
                strong_by_records=strong,
                weak_by_records=weak,
            )
        )
    return details


def analyze_suite_duplicates(
    records: list[TestRecord],
    facts_by_record: dict[str, StaticFacts],
) -> SuiteStaticAnalysis:
    if not records:
        return SuiteStaticAnalysis()

    exact_by_signature: dict[str, list[str]] = defaultdict(list)
    semantic_by_signature: dict[str, list[str]] = defaultdict(list)
    oracle_by_signature: dict[str, list[str]] = defaultdict(list)
    semantic_for_record: dict[str, str] = {}
    for record in records:
        steps = _scenario_steps(record.scenario)
        exact = _signature(steps)
        semantic = _signature([_semantic_step(step) for step in steps])
        semantic_for_record[record.record_key] = semantic
        exact_by_signature[exact].append(record.record_key)
        semantic_by_signature[semantic].append(record.record_key)
        facts = facts_by_record.get(record.record_key)
        if facts and facts.data_flow.assertions:
            oracle = ",".join(
                assertion.classification for assertion in facts.data_flow.assertions
            )
            oracle_by_signature[oracle].append(record.record_key)

    groups: list[SuiteDuplicateGroup] = []
    exact_members: set[frozenset[str]] = set()
    for signature, record_keys in sorted(exact_by_signature.items()):
        if len(record_keys) < 2:
            continue
        members = frozenset(record_keys)
        exact_members.add(members)
        groups.append(
            SuiteDuplicateGroup(
                group_id=_group_id("exact", signature),
                kind="exact_scenario",
                record_keys=sorted(record_keys),
                signature=signature,
                rationale="The scenarios have the same normalized Given/When/Then text.",
            )
        )
    for signature, record_keys in sorted(semantic_by_signature.items()):
        if len(record_keys) < 2 or frozenset(record_keys) in exact_members:
            continue
        groups.append(
            SuiteDuplicateGroup(
                group_id=_group_id("semantic", signature),
                kind="semantic_scenario",
                record_keys=sorted(record_keys),
                signature=signature,
                rationale=(
                    "The scenarios exercise the same step structure after replacing concrete "
                    "values, numbers, and test-id suffixes."
                ),
            )
        )
    for signature, record_keys in sorted(oracle_by_signature.items()):
        if len(record_keys) < 2:
            continue
        # An oracle-shape duplicate is most actionable when the tests also claim
        # the same semantic scenario; otherwise equal assertion types can be valid.
        semantic_groups = {semantic_for_record[key] for key in record_keys}
        if len(semantic_groups) != 1:
            continue
        groups.append(
            SuiteDuplicateGroup(
                group_id=_group_id("oracle", signature),
                kind="oracle_shape",
                record_keys=sorted(record_keys),
                signature=signature,
                rationale="Semantically similar scenarios use the same assertion-source shape.",
            )
        )

    semantic_counts = Counter(semantic_for_record.values())
    unique_records = sorted(
        key for key, signature in semantic_for_record.items() if semantic_counts[signature] == 1
    )
    duplicate_ratio = 1.0 - len(semantic_counts) / len(records)
    return SuiteStaticAnalysis(
        duplicate_groups=groups,
        unique_contribution_records=unique_records,
        semantic_duplicate_ratio=duplicate_ratio,
    )
