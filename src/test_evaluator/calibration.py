"""Load and validate the human-labelled basic-evaluator golden set."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .ingest import load_records
from .schemas import EvaluationRun, Status
from .static_verifier import extract_static_facts


DEFAULT_GOLDEN_PATH = Path("calibration/golden_basic_v1.json")
DEFAULT_DATASET_PATH = Path("e2edev_sample.csv")


class GoldenCalibrationCase(BaseModel):
    case_id: str
    source_record_key: str
    focus: Literal["bdd_traceability", "step_code", "oracle_critic"]
    expected_status: Status
    expected_assertion_classifications: list[str] | None = None
    tags: list[str] = Field(default_factory=list)
    rationale: str


class CalibrationComparison(BaseModel):
    matched: int
    compared: int
    skipped: int
    accuracy: float | None
    by_agent: dict[str, dict[str, int | float | None]] = Field(default_factory=dict)
    mismatches: list[str] = Field(default_factory=list)


def load_golden_cases(path: str | Path = DEFAULT_GOLDEN_PATH) -> list[GoldenCalibrationCase]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return [GoldenCalibrationCase.model_validate(item) for item in payload]


def validate_golden_cases(
    cases: list[GoldenCalibrationCase],
    dataset_path: str | Path = DEFAULT_DATASET_PATH,
) -> list[str]:
    """Return deterministic set/data-flow validation errors."""

    errors: list[str] = []
    if not 20 <= len(cases) <= 30:
        errors.append(f"Golden set must contain 20-30 cases; found {len(cases)}.")
    identifiers = [case.case_id for case in cases]
    duplicates = sorted(key for key, count in Counter(identifiers).items() if count > 1)
    if duplicates:
        errors.append(f"Duplicate case IDs: {', '.join(duplicates)}")

    focus_counts = Counter(case.focus for case in cases)
    for focus in ("bdd_traceability", "step_code", "oracle_critic"):
        if focus_counts[focus] < 6:
            errors.append(f"Golden set needs at least 6 {focus} cases; found {focus_counts[focus]}.")

    records = {record.record_key: record for record in load_records(dataset_path)}
    for case in cases:
        record = records.get(case.source_record_key)
        if record is None:
            errors.append(f"{case.case_id}: unknown source record {case.source_record_key}.")
            continue
        if case.expected_assertion_classifications is None:
            continue
        actual = [
            assertion.classification
            for assertion in extract_static_facts(record).data_flow.assertions
        ]
        if actual != case.expected_assertion_classifications:
            errors.append(
                f"{case.case_id}: assertion flow changed; expected "
                f"{case.expected_assertion_classifications}, got {actual}."
            )
    return errors


def compare_evaluation(
    cases: list[GoldenCalibrationCase],
    run: EvaluationRun,
) -> CalibrationComparison:
    """Compare normalized report statuses with labels for records present in a run."""

    actual = {
        (test.record_key, review.agent): review.status
        for test in run.tests
        for review in test.reviews
    }
    matched = 0
    compared = 0
    mismatches: list[str] = []
    per_agent: dict[str, Counter[str]] = {}
    for case in cases:
        status = actual.get((case.source_record_key, case.focus))
        if status is None:
            continue
        compared += 1
        per_agent.setdefault(case.focus, Counter())["compared"] += 1
        if status is case.expected_status:
            matched += 1
            per_agent[case.focus]["matched"] += 1
        else:
            mismatches.append(
                f"{case.case_id}: expected {case.expected_status.value}, got {status.value}"
            )

    by_agent: dict[str, dict[str, int | float | None]] = {}
    for agent, counts in sorted(per_agent.items()):
        agent_compared = counts["compared"]
        agent_matched = counts["matched"]
        by_agent[agent] = {
            "matched": agent_matched,
            "compared": agent_compared,
            "accuracy": agent_matched / agent_compared if agent_compared else None,
        }
    return CalibrationComparison(
        matched=matched,
        compared=compared,
        skipped=len(cases) - compared,
        accuracy=matched / compared if compared else None,
        by_agent=by_agent,
        mismatches=mismatches,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate or score the basic golden set.")
    parser.add_argument("--golden", type=Path, default=DEFAULT_GOLDEN_PATH)
    parser.add_argument("--dataset", type=Path, default=DEFAULT_DATASET_PATH)
    parser.add_argument(
        "--evaluation",
        type=Path,
        help="Optional evaluation.json to compare with available golden labels.",
    )
    args = parser.parse_args()
    cases = load_golden_cases(args.golden)
    errors = validate_golden_cases(cases, args.dataset)
    if errors:
        raise SystemExit("\n".join(errors))
    focus_counts = Counter(case.focus for case in cases)
    print(f"Golden set valid: {len(cases)} labelled decisions; {dict(sorted(focus_counts.items()))}")
    if args.evaluation:
        run = EvaluationRun.model_validate_json(args.evaluation.read_text(encoding="utf-8"))
        comparison = compare_evaluation(cases, run)
        print(comparison.model_dump_json(indent=2))


if __name__ == "__main__":
    main()
