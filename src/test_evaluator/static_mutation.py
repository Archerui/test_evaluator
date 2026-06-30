"""General, source-free mutation-readiness hypotheses for basic evaluation."""

from __future__ import annotations

import hashlib
import re

from .schemas import (
    Behavior,
    RequirementContract,
    StaticFacts,
    StaticMutationAssessment,
    StaticMutationHypothesis,
    TestRecord,
)


_TOKEN_RE = re.compile(r"[A-Za-z0-9_-]{3,}")
_STOP_WORDS = {
    "and",
    "are",
    "but",
    "for",
    "given",
    "should",
    "system",
    "then",
    "the",
    "user",
    "when",
    "with",
}


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_RE.findall(value)
        if token.casefold() not in _STOP_WORDS
    }


def _behavior_text(behavior: Behavior) -> str:
    return " ".join(
        [
            *behavior.preconditions,
            *behavior.actor_actions,
            *behavior.expected_observables,
            *behavior.state_effects,
            *behavior.constraints,
        ]
    )


def target_behaviors(record: TestRecord, contract: RequirementContract) -> list[Behavior]:
    if not contract.behaviors:
        combined = f"{record.requirement}\n{record.scenario}\n{record.step_code}".casefold()
        scenario_tokens = _tokens(record.scenario)
        if (
            scenario_tokens.intersection({"browser", "datatransfer", "drag", "dragstart", "event"})
            or record.step_code.find("DataTransfer") >= 0
            or record.step_code.find("DragEvent") >= 0
        ):
            observability = "browser_api"
        elif "localstorage" in combined or "sessionstorage" in combined:
            observability = "storage"
        elif any(token in combined for token in ("fetch(", "http", " api ")):
            observability = "network"
        elif record.step_code and _has_dom_signal(record.step_code):
            observability = "dom"
        else:
            observability = "unknown"
        return [
            Behavior(
                behavior_id="__scenario__",
                kind="other",
                actor_actions=[record.scenario],
                expected_observables=[record.requirement],
                observability=observability,  # type: ignore[arg-type]
            )
        ]
    scenario_tokens = _tokens(record.scenario)
    ranked: list[tuple[float, Behavior]] = []
    for behavior in contract.behaviors:
        behavior_tokens = _tokens(_behavior_text(behavior))
        score = (
            len(scenario_tokens.intersection(behavior_tokens)) / len(behavior_tokens)
            if behavior_tokens
            else 0.0
        )
        ranked.append((score, behavior))
    ranked.sort(key=lambda item: (-item[0], item[1].behavior_id))
    positive = [behavior for score, behavior in ranked if score > 0.0]
    # A test-level readiness estimate is anchored to the single closest
    # behavior. Suite coverage handles multi-behavior declarations separately;
    # selecting more here makes unrelated contract details inflate hypotheses.
    return positive[:1] or [behavior for _, behavior in ranked[:1]]


def _has_dom_signal(step_code: str) -> bool:
    """Return whether code contains a generic browser DOM observation signal."""

    return any(
        token in step_code
        for token in (
            "find_element",
            "find_elements",
            "querySelector",
            ".text",
            "get_attribute",
        )
    )


def _has_exact_assertion(facts: StaticFacts, classification: str) -> bool:
    comparison_markers = (" == ", " != ", " in ", "<", ">")
    return any(
        assertion.classification == classification
        and any(marker in f" {assertion.expression} " for marker in comparison_markers)
        for assertion in facts.data_flow.assertions
    )


def _prediction(
    behavior: Behavior,
    fault_class: str,
    facts: StaticFacts,
) -> tuple[str, float, str]:
    data_flow = facts.data_flow
    assertions = data_flow.assertions
    if behavior.observability == "browser_api" and data_flow.event_payload_assertion_count:
        exact = _has_exact_assertion(facts, "event_payload_observation")
        if fault_class != "string_literal" or exact:
            return (
                "likely_detected",
                0.90,
                "The asserted path directly observes application-produced browser-event payload data.",
            )
    if behavior.observability == "browser_api" and not data_flow.event_payload_assertion_count:
        return (
            "likely_survives",
            0.85 if assertions else 0.90,
            "No asserted path directly observes the required browser API or event payload.",
        )
    if behavior.observability == "dom" and data_flow.dom_assertion_count:
        exact = _has_exact_assertion(facts, "dom_observation")
        if fault_class == "dom_update" or exact:
            return (
                "likely_detected",
                0.80,
                "The asserted path observes the required DOM result after the action.",
            )
        return (
            "unknown",
            0.55,
            "The DOM is observed, but the static analysis cannot prove the asserted value is specific enough.",
        )
    if data_flow.self_fulfilled_event_payload_assertion_count:
        return (
            "likely_survives",
            0.90,
            "The test injects and re-reads its own event payload, so application faults can remain invisible.",
        )
    if assertions and all(
        assertion.classification in {"constant", "element_attribute_proxy"}
        for assertion in assertions
    ):
        return (
            "likely_survives",
            0.85,
            "Only constants or capability proxies reach assertions; the required result is not observed.",
        )
    if not assertions:
        return (
            "likely_survives",
            0.80,
            "No automatic assertion is available to distinguish the hypothesized fault.",
        )
    return (
        "unknown",
        0.45,
        "The available static assertion flow does not establish whether this fault would be detected.",
    )


def _fault_classes(behavior: Behavior, facts: StaticFacts) -> list[tuple[str, str]]:
    if behavior.observability == "dom":
        return [
            ("dom_update", "Required DOM state update is omitted or applied to the wrong target."),
            ("string_literal", "A required user-observable value is replaced by an incorrect literal."),
        ]
    if behavior.observability == "browser_api":
        return [
            ("event_handler", "A required browser event handler is omitted or does not produce its observable effect."),
            ("api_call", "A required browser API interaction is omitted or invoked incorrectly."),
            ("string_literal", "A required browser-API argument, payload value, or key is incorrect."),
        ]
    if behavior.observability in {"mocked_api", "network", "storage"}:
        return [
            ("api_call", "The required API or storage interaction is omitted or invoked incorrectly."),
            ("string_literal", "A required request, argument, key, or result value is incorrect."),
        ]
    return [
        ("comparison", "A condition controlling the required behavior uses the wrong comparison."),
        ("boolean_literal", "A boolean decision controlling the required behavior is inverted."),
    ]


def assess_static_mutation(
    record: TestRecord,
    contract: RequirementContract,
    facts: StaticFacts,
) -> StaticMutationAssessment:
    """Predict fault detection without source code, mutation, or execution."""

    hypotheses: list[StaticMutationHypothesis] = []
    for behavior in target_behaviors(record, contract):
        for fault_class, description in _fault_classes(behavior, facts):
            prediction, confidence, rationale = _prediction(behavior, fault_class, facts)
            digest = hashlib.sha256(
                f"{record.record_key}:{behavior.behavior_id}:{fault_class}".encode("utf-8")
            ).hexdigest()[:10]
            hypotheses.append(
                StaticMutationHypothesis(
                    hypothesis_id=f"static-{digest}",
                    fault_class=fault_class,  # type: ignore[arg-type]
                    behavior_ids=[behavior.behavior_id],
                    description=description,
                    prediction=prediction,  # type: ignore[arg-type]
                    confidence=confidence,
                    rationale=rationale,
                )
            )
    known = [item for item in hypotheses if item.prediction != "unknown"]
    detected = sum(item.prediction == "likely_detected" for item in known)
    readiness = detected / len(known) * 100.0 if known else None
    coverage = len(known) / len(hypotheses) if hypotheses else 0.0
    return StaticMutationAssessment(
        record_key=record.record_key,
        hypotheses=hypotheses,
        readiness_score=readiness,
        prediction_coverage=coverage,
    )
