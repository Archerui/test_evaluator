"""Checkpointed orchestration state and resume support."""

from __future__ import annotations

import hashlib
import json
import os
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from pydantic import BaseModel

from .schemas import (
    ArtifactRef,
    Mode,
    OrchestratorState,
    RunHealth,
    RunManifest,
    SemanticMode,
    StateCheckpoint,
    StateStatus,
)


STATE_ORDER: tuple[OrchestratorState, ...] = (
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
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


def _jsonable(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item) for item in value]
    return value


def stable_hash(value: Any) -> str:
    encoded = json.dumps(_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class OrchestratorStateStore:
    """Persist state transitions and JSON payloads for restartable runs."""

    def __init__(
        self,
        output_dir: str | Path,
        *,
        mode: Mode,
        semantic_mode: SemanticMode,
        config: dict[str, object],
        resume: bool = False,
    ) -> None:
        self.output_dir = Path(output_dir).resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir = self.output_dir / "checkpoints"
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.item_checkpoint_dir = self.checkpoint_dir / "items"
        self.item_checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_path = self.output_dir / "run_manifest.json"
        self.config_hash = stable_hash(config)
        self.resume_used = resume
        self.cache_hits = 0
        self.cache_misses = 0

        if resume and self.manifest_path.is_file():
            self.manifest = RunManifest.model_validate_json(self.manifest_path.read_text(encoding="utf-8"))
            if self.manifest.config_hash != self.config_hash:
                raise ValueError(
                    "Cannot resume: configuration changed. Use a new output directory or run without --resume."
                )
        else:
            self.manifest = RunManifest(
                run_id=uuid4().hex,
                mode=mode,
                semantic_mode=semantic_mode,
                output_dir=str(self.output_dir),
                config_hash=self.config_hash,
                current_state="CREATED",
                checkpoints=[
                    StateCheckpoint(
                        run_id="",
                        state="CREATED",
                        status="succeeded",
                        started_at=_now(),
                        finished_at=_now(),
                        attempts=1,
                    )
                ],
            )
            self.manifest.checkpoints[0].run_id = self.manifest.run_id
            self._write_manifest()

    @property
    def run_id(self) -> str:
        return self.manifest.run_id

    def _write_json_atomic(self, path: Path, payload: Any) -> None:
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(_jsonable(payload), ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temporary, path)

    def _write_manifest(self) -> None:
        self._write_json_atomic(self.manifest_path, self.manifest)

    def _payload_path(self, state: OrchestratorState) -> Path:
        index = STATE_ORDER.index(state)
        return self.checkpoint_dir / f"{index:02d}_{state.casefold()}.json"

    def _latest(self, state: OrchestratorState) -> StateCheckpoint | None:
        for checkpoint in reversed(self.manifest.checkpoints):
            if checkpoint.state == state:
                return checkpoint
        return None

    def cached_payload(self, state: OrchestratorState, input_hash: str) -> dict[str, Any] | None:
        if not self.resume_used:
            return None
        checkpoint = self._latest(state)
        path = self._payload_path(state)
        if (
            checkpoint is not None
            and checkpoint.status in {"succeeded", "degraded", "cached"}
            and checkpoint.input_hash == input_hash
            and path.is_file()
        ):
            self.cache_hits += 1
            if checkpoint.status != "degraded":
                checkpoint.status = "cached"
            self.manifest.current_state = state
            self._write_manifest()
            payload = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(payload, dict):
                raise ValueError(f"Checkpoint payload for {state} is not an object")
            return payload
        self.cache_misses += 1
        return None

    def start(self, state: OrchestratorState, input_hash: str) -> StateCheckpoint:
        previous = self._latest(state)
        checkpoint = StateCheckpoint(
            run_id=self.run_id,
            state=state,
            status="running",
            started_at=_now(),
            attempts=(previous.attempts if previous else 0) + 1,
            input_hash=input_hash,
        )
        self.manifest.current_state = state
        self.manifest.checkpoints.append(checkpoint)
        self._write_manifest()
        return checkpoint

    def _item_payload_path(self, state: OrchestratorState, item_key: str) -> Path:
        digest = hashlib.sha256(item_key.encode("utf-8")).hexdigest()[:20]
        directory = self.item_checkpoint_dir / state.casefold()
        directory.mkdir(parents=True, exist_ok=True)
        return directory / f"{digest}.json"

    def cached_item_payload(
        self,
        state: OrchestratorState,
        item_key: str,
        input_hash: str,
    ) -> dict[str, Any] | None:
        if not self.resume_used:
            return None
        path = self._item_payload_path(state, item_key)
        if not path.is_file():
            self.cache_misses += 1
            return None
        payload = json.loads(path.read_text(encoding="utf-8"))
        if (
            isinstance(payload, dict)
            and payload.get("item_key") == item_key
            and payload.get("input_hash") == input_hash
            and isinstance(payload.get("payload"), dict)
        ):
            self.cache_hits += 1
            return payload["payload"]
        self.cache_misses += 1
        return None

    def save_item_payload(
        self,
        state: OrchestratorState,
        item_key: str,
        input_hash: str,
        payload: dict[str, Any],
    ) -> Path:
        path = self._item_payload_path(state, item_key)
        self._write_json_atomic(
            path,
            {
                "state": state,
                "item_key": item_key,
                "input_hash": input_hash,
                "payload": payload,
            },
        )
        status_map = self.manifest.mutant_status if state == "MUTATION_RUN" else self.manifest.record_status
        status_map[item_key] = "succeeded"
        self._write_manifest()
        return path

    def succeed(
        self,
        state: OrchestratorState,
        payload: dict[str, Any],
        *,
        status: Literal["succeeded", "degraded"] = "succeeded",
        warning: str | None = None,
    ) -> Path:
        checkpoint = self._latest(state)
        if checkpoint is None or checkpoint.status != "running":
            raise RuntimeError(f"State {state} was not started")
        path = self._payload_path(state)
        self._write_json_atomic(path, payload)
        checkpoint.status = status
        checkpoint.finished_at = _now()
        checkpoint.error_summary = warning
        checkpoint.output_artifacts = [
            ArtifactRef(
                kind="checkpoint",
                path=str(path.relative_to(self.output_dir)),
                description=f"{state} checkpoint",
                sha256=file_hash(path),
            )
        ]
        self._write_manifest()
        return path

    def fail(self, state: OrchestratorState, error: Exception, *, recoverable: bool) -> None:
        checkpoint = self._latest(state)
        if checkpoint is None:
            checkpoint = self.start(state, input_hash="")
        checkpoint.status = "failed"
        checkpoint.finished_at = _now()
        checkpoint.error_summary = f"{type(error).__name__}: {error}"
        checkpoint.recoverable = recoverable
        self.manifest.current_state = state if recoverable else "FAILED"
        self._write_manifest()

    def skip(self, state: OrchestratorState, reason: str, *, degraded: bool = False) -> None:
        checkpoint = StateCheckpoint(
            run_id=self.run_id,
            state=state,
            status="degraded" if degraded else "skipped",
            started_at=_now(),
            finished_at=_now(),
            attempts=0,
            error_summary=reason,
            recoverable=True,
        )
        self.manifest.current_state = state
        self.manifest.checkpoints.append(checkpoint)
        self._write_manifest()

    def complete(self) -> None:
        checkpoint = StateCheckpoint(
            run_id=self.run_id,
            state="COMPLETED",
            status="succeeded",
            started_at=_now(),
            finished_at=_now(),
            attempts=1,
        )
        self.manifest.current_state = "COMPLETED"
        self.manifest.checkpoints.append(checkpoint)
        self._write_manifest()

    def health(self) -> RunHealth:
        latest_by_state: dict[str, StateCheckpoint] = {}
        for checkpoint in self.manifest.checkpoints:
            latest_by_state[checkpoint.state] = checkpoint
        counts = Counter(checkpoint.status for checkpoint in latest_by_state.values())
        degraded_reasons = [
            checkpoint.error_summary
            for checkpoint in latest_by_state.values()
            if checkpoint.status == "degraded" and checkpoint.error_summary
        ]
        failed_reasons = [
            checkpoint.error_summary
            for checkpoint in latest_by_state.values()
            if checkpoint.status == "failed" and checkpoint.error_summary
        ]
        failed_attempts = Counter(
            checkpoint.state
            for checkpoint in self.manifest.checkpoints
            if checkpoint.status == "failed"
        )
        retry_counts = dict(sorted(failed_attempts.items()))
        stage_durations: dict[str, float] = {}
        for state, checkpoint in latest_by_state.items():
            if not checkpoint.started_at or not checkpoint.finished_at:
                continue
            try:
                started = datetime.fromisoformat(checkpoint.started_at)
                finished = datetime.fromisoformat(checkpoint.finished_at)
            except ValueError:
                continue
            stage_durations[state] = max(0.0, (finished - started).total_seconds())
        return RunHealth(
            state_counts=dict(sorted(counts.items())),
            degraded_reasons=degraded_reasons,
            failed_reasons=failed_reasons,
            retry_counts=retry_counts,
            cache_hits=self.cache_hits,
            cache_misses=self.cache_misses,
            resume_used=self.resume_used,
            stage_durations_seconds=dict(sorted(stage_durations.items())),
        )
