"""Generate bounded, reproducible mutation plans from discovered source."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re

from ..schemas import (
    MutationGeneratorInput,
    MutationGeneratorOutput,
    MutationPlan,
    MutantSpec,
    Status,
)
from .operators import DEFAULT_OPERATORS, generate_candidates


_BEHAVIOR_STOPWORDS = {
    "add",
    "attribute",
    "element",
    "event",
    "function",
    "handler",
    "item",
    "list",
    "return",
    "should",
    "system",
    "true",
    "false",
    "user",
    "value",
    "when",
}


def _semantic_tokens(text: str) -> set[str]:
    tokens: set[str] = set()
    for raw in re.findall(r"[A-Za-z][A-Za-z0-9_-]{2,}", text.casefold()):
        pieces = [item for item in re.split(r"[-_]", raw) if item]
        for token in pieces:
            if token in _BEHAVIOR_STOPWORDS:
                continue
            tokens.add(token)
            if "drag" in token:
                tokens.add("drag")
            if "drop" in token:
                tokens.add("drop")
            if "load" in token:
                tokens.add("load")
            if token.endswith("s") and len(token) > 4:
                tokens.add(token[:-1])
    return tokens


def _behavior_candidates(line: str, request: MutationGeneratorInput) -> list[str]:
    lowered = line.casefold()
    line_tokens = _semantic_tokens(line)
    matched: list[str] = []
    for contract in request.contracts:
        for behavior in contract.behaviors:
            anchors = [anchor.casefold() for anchor in behavior.ui_anchors if len(anchor) >= 3]
            behavior_text = " ".join(
                [behavior.behavior_id]
                + behavior.ui_anchors
                + behavior.actor_actions
                + behavior.expected_observables
                + behavior.state_effects
                + behavior.constraints
            )
            behavior_tokens = _semantic_tokens(behavior_text)
            if any(anchor in lowered for anchor in anchors) or line_tokens.intersection(behavior_tokens):
                matched.append(behavior.behavior_id)
    return sorted(set(matched))


def generate_mutation_plan(request: MutationGeneratorInput) -> MutationGeneratorOutput:
    if request.max_mutants <= 0:
        raise ValueError("max_mutants must be positive")
    if not request.inventory.source_root:
        raise ValueError(f"Project {request.inventory.project_id} has no source root")
    root = Path(request.inventory.source_root).resolve()
    enabled = tuple(request.operators or DEFAULT_OPERATORS)
    unknown = sorted(set(enabled).difference(DEFAULT_OPERATORS))
    if unknown:
        raise ValueError(f"Unknown mutation operators: {', '.join(unknown)}")

    mutants: list[MutantSpec] = []
    skipped: list[dict[str, object]] = []
    supported_files = [
        relative
        for relative in request.source_model.source_files
        if Path(relative).suffix.casefold() in {".js", ".mjs", ".cjs", ".html", ".htm"}
    ]
    for relative in sorted(supported_files):
        path = (root / relative).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            skipped.append({"file_path": relative, "reason": "path escapes source root"})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            skipped.append({"file_path": relative, "reason": str(error)})
            continue
        candidates = generate_candidates(relative, text, enabled)
        if not candidates:
            skipped.append({"file_path": relative, "reason": "no supported mutation sites"})
        for candidate in candidates:
            identity = "|".join(
                (
                    request.inventory.project_id,
                    relative,
                    str(candidate.line_start),
                    candidate.operator,
                    candidate.mutated,
                )
            )
            mutant_id = f"{request.inventory.project_id}-m{sha256(identity.encode()).hexdigest()[:12]}"
            mutants.append(
                MutantSpec(
                    mutant_id=mutant_id,
                    project_id=request.inventory.project_id,
                    operator=candidate.operator,
                    file_path=relative,
                    line_start=candidate.line_start,
                    original=candidate.original,
                    mutated=candidate.mutated,
                    behavior_candidates=_behavior_candidates(candidate.original, request),
                )
            )
            if len(mutants) >= request.max_mutants:
                break
        if len(mutants) >= request.max_mutants:
            break

    plan = MutationPlan(
        project_id=request.inventory.project_id,
        mutants=mutants,
        skipped_candidates=skipped,
    )
    return MutationGeneratorOutput(
        agent="mutation_generator",
        run_id=request.run_id,
        mode="full",
        project_id=request.inventory.project_id,
        status=Status.PASS if mutants else Status.UNKNOWN,
        confidence=1.0,
        warnings=[] if mutants else ["No supported mutation sites were found"],
        plan=plan,
    )
