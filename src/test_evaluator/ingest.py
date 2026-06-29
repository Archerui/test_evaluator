"""Dataset ingestion and requirement-suite grouping."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from .schemas import TestRecord


CSV_REQUIRED_COLUMNS = {
    "id",
    "req_id",
    "test_id",
    "requirement_summary",
    "fine_grained_reqs",
    "excutable_test_test_case",
    "excutable_test_step_code",
    "reference_answer",
}


def _required(row: dict[str, object], name: str, location: str) -> str:
    value = row.get(name)
    if value is None:
        raise ValueError(f"{location} is missing required field {name!r}")
    return str(value)


def _record_from_tabular_mapping(row: dict[str, object], location: str, origin: str) -> TestRecord:
    return TestRecord(
        project_id=_required(row, "id", location).strip(),
        requirement_id=_required(row, "req_id", location).strip(),
        test_id=_required(row, "test_id", location).strip(),
        requirement_summary=_required(row, "requirement_summary", location).strip(),
        requirement=_required(row, "fine_grained_reqs", location).strip(),
        scenario=_required(row, "excutable_test_test_case", location).strip(),
        step_code=_required(row, "excutable_test_step_code", location).strip(),
        reference_answer=_required(row, "reference_answer", location).strip(),
        input_origin=origin,  # type: ignore[arg-type]
    )


def load_csv_records(path: str | Path) -> list[TestRecord]:
    source = Path(path)
    with source.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = CSV_REQUIRED_COLUMNS.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

        return [
            _record_from_tabular_mapping(row, f"CSV row {row_number}", "csv")
            for row_number, row in enumerate(reader, start=2)
        ]


def load_jsonl_records(path: str | Path) -> list[TestRecord]:
    source = Path(path)
    records: list[TestRecord] = []
    for line_number, line in enumerate(source.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"JSONL line {line_number} must contain an object")
        records.append(_record_from_tabular_mapping(payload, f"JSONL line {line_number}", "jsonl"))
    return records


def _summary_text(payload: dict[str, object]) -> str:
    summary = payload.get("summary")
    if not isinstance(summary, dict):
        return ""
    values = [str(value).strip() for value in summary.values() if value and str(value).strip()]
    return " ".join(values)


def load_e2edev_project_records(
    project_dir: str | Path,
    *,
    source_root: str | Path | None = None,
) -> list[TestRecord]:
    """Load one E2EDev ``requirment_with_tests.json`` project."""

    project_path = Path(project_dir).resolve()
    tests_file = project_path / "requirment_with_tests.json"
    if not tests_file.is_file():
        raise FileNotFoundError(f"E2EDev tests file not found: {tests_file}")

    payload = json.loads(tests_file.read_text(encoding="utf-8"))
    suites = payload.get("finegrained_rewith_test")
    if not isinstance(suites, dict):
        raise ValueError(f"{tests_file} is missing object 'finegrained_rewith_test'")

    summary = _summary_text(payload)
    resolved_source = Path(source_root).resolve() if source_root else None
    records: list[TestRecord] = []
    for requirement_id, suite_payload in suites.items():
        if not isinstance(suite_payload, dict):
            continue
        requirement_payload = suite_payload.get("requirement")
        requirement = (
            str(requirement_payload.get("description", "")).strip()
            if isinstance(requirement_payload, dict)
            else str(requirement_payload or "").strip()
        )
        test_cases = suite_payload.get("test_cases")
        if not isinstance(test_cases, list):
            continue
        for index, test_payload in enumerate(test_cases, start=1):
            if not isinstance(test_payload, dict):
                continue
            raw_scenario = test_payload.get("test_case", "")
            if isinstance(raw_scenario, list):
                scenario = str(raw_scenario[0]).strip() if raw_scenario else ""
            else:
                scenario = str(raw_scenario).strip()
            step_code = str(test_payload.get("step_code", "")).strip()
            records.append(
                TestRecord(
                    project_id=project_path.name,
                    requirement_id=str(requirement_id),
                    test_id=str(index),
                    requirement_summary=summary,
                    requirement=requirement,
                    scenario=scenario,
                    step_code=step_code,
                    reference_answer=str(resolved_source or project_path),
                    input_origin="requirment_with_tests",
                    project_root=str(project_path),
                    source_root=str(resolved_source) if resolved_source else None,
                )
            )
    return records


def load_records(path: str | Path) -> list[TestRecord]:
    """Load CSV, JSONL, or one E2EDev project JSON without altering content."""

    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix == ".csv":
        return load_csv_records(source)
    if suffix == ".jsonl":
        return load_jsonl_records(source)
    if suffix == ".json" and source.name == "requirment_with_tests.json":
        return load_e2edev_project_records(source.parent)
    raise ValueError(f"Unsupported input format: {source}")


def group_by_suite(records: list[TestRecord]) -> dict[str, list[TestRecord]]:
    groups: dict[str, list[TestRecord]] = defaultdict(list)
    for record in records:
        groups[record.suite_key].append(record)
    return dict(groups)
