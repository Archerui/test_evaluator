"""Thin, typed wrapper around the OpenAI Responses API.

The OpenAI SDK obtains OPENAI_API_KEY itself. This module never reads,
prints, serializes, or otherwise inspects the credential.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from threading import get_ident
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)


class OpenAIJsonAgent:
    """Run an evidence-grounded agent and require a Pydantic-shaped response."""

    def __init__(
        self,
        model: str,
        max_output_tokens: int = 4_000,
        timeout_seconds: float = 45.0,
        cache_dir: str | Path | None = None,
    ) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        self.cache_dir = Path(cache_dir).resolve() if cache_dir else None
        if self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        # Do not pass an API key here. The SDK resolves OPENAI_API_KEY internally.
        self.client = OpenAI(timeout=timeout_seconds, max_retries=1)

    def run(self, *, instructions: str, payload: dict[str, object], response_model: type[T]) -> T:
        cache_path: Path | None = None
        if self.cache_dir:
            cache_input = json.dumps(
                {
                    "model": self.model,
                    "max_output_tokens": self.max_output_tokens,
                    "instructions": instructions,
                    "payload": payload,
                    "response_model": f"{response_model.__module__}.{response_model.__qualname__}",
                },
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
            cache_key = hashlib.sha256(cache_input.encode("utf-8")).hexdigest()
            cache_path = self.cache_dir / f"{cache_key}.json"
            if cache_path.is_file():
                try:
                    return response_model.model_validate_json(cache_path.read_text(encoding="utf-8"))
                except (OSError, ValidationError):
                    pass

        # A schema-valid response can still be truncated when an agent is overly
        # verbose. Retry once with an explicit compactness constraint rather than
        # returning partial JSON to the coordinator.
        for attempt in range(2):
            try:
                response = self.client.responses.parse(
                    model=self.model,
                    instructions=(
                        instructions
                        if attempt == 0
                        else instructions
                        + "\nRetry requirement: return compact valid JSON only. Keep all strings short and return fewer findings if necessary."
                    ),
                    input=json.dumps(payload, ensure_ascii=False),
                    text_format=response_model,
                    max_output_tokens=self.max_output_tokens,
                    store=False,
                )
                if response.output_parsed is None:
                    raise RuntimeError("The model returned no structured output.")
                parsed = response.output_parsed
                if cache_path:
                    temporary = cache_path.with_suffix(f".tmp-{os.getpid()}-{get_ident()}")
                    temporary.write_text(parsed.model_dump_json(indent=2), encoding="utf-8")
                    os.replace(temporary, cache_path)
                return parsed
            except ValidationError:
                if attempt == 1:
                    raise
        raise RuntimeError("The structured response retry loop ended unexpectedly.")
