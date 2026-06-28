"""Thin, typed wrapper around the OpenAI Responses API.

The OpenAI SDK obtains OPENAI_API_KEY itself. This module never reads,
prints, serializes, or otherwise inspects the credential.
"""

from __future__ import annotations

import json
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError


T = TypeVar("T", bound=BaseModel)


class OpenAIJsonAgent:
    """Run an evidence-grounded agent and require a Pydantic-shaped response."""

    def __init__(self, model: str, max_output_tokens: int = 4_000, timeout_seconds: float = 45.0) -> None:
        self.model = model
        self.max_output_tokens = max_output_tokens
        # Do not pass an API key here. The SDK resolves OPENAI_API_KEY internally.
        self.client = OpenAI(timeout=timeout_seconds, max_retries=1)

    def run(self, *, instructions: str, payload: dict[str, object], response_model: type[T]) -> T:
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
                return response.output_parsed
            except ValidationError:
                if attempt == 1:
                    raise
        raise RuntimeError("The structured response retry loop ended unexpectedly.")
