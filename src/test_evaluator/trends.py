"""Append-only-compatible historical snapshots and run-to-run deltas."""

from __future__ import annotations

from datetime import UTC, datetime
import json
from pathlib import Path
from statistics import mean

from .schemas import EvaluationRun, TrendReport, TrendSnapshot


def _average(values) -> float | None:
    available = [float(value) for value in values if value is not None]
    return mean(available) if available else None


def _snapshot(run: EvaluationRun) -> TrendSnapshot:
    return TrendSnapshot(
        run_id=run.run_id,
        created_at=datetime.now(UTC).isoformat(),
        mode=run.mode,
        test_count=len(run.tests),
        metrics={
            "test_quality": _average(report.test_quality_score for report in run.tests),
            "requirement_adequacy": _average(
                report.requirement_adequacy_score for report in run.requirements
            ),
            "runtime_pass_rate": _average(project.runtime_pass_rate for project in run.projects),
            "mutation_score": _average(project.mutation_score for project in run.projects),
            "flaky_test_count": float(
                sum(bool(report.stability and report.stability.flaky) for report in run.tests)
            ),
            "runtime_seconds": (
                run.run_health.total_runtime_seconds if run.run_health else None
            ),
        },
    )


def update_history(run: EvaluationRun, history_path: str | Path) -> TrendReport:
    path = Path(history_path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    snapshots: list[TrendSnapshot] = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                snapshots.append(TrendSnapshot.model_validate_json(line))
            except Exception:
                continue
    current = _snapshot(run)
    previous = next(
        (
            snapshot
            for snapshot in reversed(snapshots)
            if snapshot.run_id != current.run_id and snapshot.mode == current.mode
        ),
        None,
    )
    snapshots = [snapshot for snapshot in snapshots if snapshot.run_id != current.run_id]
    snapshots.append(current)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        "\n".join(snapshot.model_dump_json() for snapshot in snapshots) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    deltas: dict[str, float | None] = {}
    for name, value in current.metrics.items():
        previous_value = previous.metrics.get(name) if previous else None
        deltas[name] = (
            float(value) - float(previous_value)
            if value is not None and previous_value is not None
            else None
        )
    return TrendReport(
        history_path=str(path),
        current=current,
        previous_run_id=previous.run_id if previous else None,
        deltas=deltas,
    )
