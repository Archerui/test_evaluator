"""CSV ingestion and grouping."""

from __future__ import annotations

import csv
import re
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TestRecord:
    project_id: str
    requirement_id: str
    test_id: str
    requirement_summary: str
    requirement: str
    scenario: str
    step_code: str
    reference_answer: str

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


def _required(row: dict[str, str], name: str, row_number: int) -> str:
    value = row.get(name)
    if value is None:
        raise ValueError(f"CSV row {row_number} is missing required column {name!r}")
    return value


def load_records(path: str | Path) -> list[TestRecord]:
    """Load the E2EDev CSV without changing its original content."""

    with Path(path).open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        required_columns = {
            "id",
            "req_id",
            "test_id",
            "requirement_summary",
            "fine_grained_reqs",
            "excutable_test_test_case",
            "excutable_test_step_code",
            "reference_answer",
        }
        missing = required_columns.difference(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV is missing columns: {', '.join(sorted(missing))}")

        records: list[TestRecord] = []
        for row_number, row in enumerate(reader, start=2):
            records.append(
                TestRecord(
                    project_id=_required(row, "id", row_number).strip(),
                    requirement_id=_required(row, "req_id", row_number).strip(),
                    test_id=_required(row, "test_id", row_number).strip(),
                    requirement_summary=_required(row, "requirement_summary", row_number).strip(),
                    requirement=_required(row, "fine_grained_reqs", row_number).strip(),
                    scenario=_required(row, "excutable_test_test_case", row_number).strip(),
                    step_code=_required(row, "excutable_test_step_code", row_number).strip(),
                    reference_answer=_required(row, "reference_answer", row_number).strip(),
                )
            )
    return records


def group_by_suite(records: list[TestRecord]) -> dict[str, list[TestRecord]]:
    groups: dict[str, list[TestRecord]] = defaultdict(list)
    for record in records:
        groups[record.suite_key].append(record)
    return dict(groups)
