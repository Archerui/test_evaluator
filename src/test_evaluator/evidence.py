"""Evidence validation for LLM outputs.

Structured output alone does not guarantee that a model's quoted evidence is
actually present in the CSV. These helpers enforce the proposal's grounding
rule before a finding can influence a score.
"""

from __future__ import annotations

import re

from .schemas import AgentReview, Behavior, Evidence, Finding, RequirementContract, Severity, Status


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip().casefold()


def _is_supported(evidence: Evidence, sources: dict[str, str]) -> bool:
    source = sources.get(evidence.field)
    quote = _normalize(evidence.quote)
    return bool(source and quote and quote in _normalize(source))


def validate_review_evidence(review: AgentReview, sources: dict[str, str]) -> AgentReview:
    """Downgrade unsupported claims to UNKNOWN before coordination."""

    checked_findings: list[Finding] = []
    for finding in review.findings:
        evidence = [item for item in finding.evidence if _is_supported(item, sources)]
        if finding.status is not Status.UNKNOWN and not evidence:
            checked_findings.append(
                finding.model_copy(
                    update={
                        "status": Status.UNKNOWN,
                        "severity": Severity.INFO,
                        "confidence": 0.0,
                        "evidence": [],
                        "reasoning": "The agent's claim was not retained because its quoted evidence could not be verified in the supplied CSV fields.",
                        "suggested_fix": None,
                    }
                )
            )
        else:
            checked_findings.append(finding.model_copy(update={"evidence": evidence}))

    non_unknown = [finding for finding in checked_findings if finding.status is not Status.UNKNOWN]
    status = review.status if non_unknown else Status.UNKNOWN
    confidence = review.confidence if non_unknown else 0.0
    return review.model_copy(update={"findings": checked_findings, "status": status, "confidence": confidence})


def validate_contract_evidence(contract: RequirementContract, sources: dict[str, str]) -> RequirementContract:
    """Keep only behaviours with at least one verified requirement citation."""

    behaviors: list[Behavior] = []
    for behavior in contract.behaviors:
        evidence = [item for item in behavior.source_evidence if _is_supported(item, sources)]
        if evidence:
            behaviors.append(behavior.model_copy(update={"source_evidence": evidence}))
    return contract.model_copy(update={"behaviors": behaviors})
