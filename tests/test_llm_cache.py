from pathlib import Path
from types import SimpleNamespace

from pydantic import BaseModel

from test_evaluator.llm import OpenAIJsonAgent


class CachedOutput(BaseModel):
    value: str


def test_structured_agent_reuses_valid_disk_cache(tmp_path: Path) -> None:
    calls = 0

    class Responses:
        def parse(self, **kwargs):
            nonlocal calls
            calls += 1
            return SimpleNamespace(output_parsed=CachedOutput(value="cached"))

    agent = OpenAIJsonAgent.__new__(OpenAIJsonAgent)
    agent.model = "unit-model"
    agent.max_output_tokens = 100
    agent.cache_dir = tmp_path
    agent.client = SimpleNamespace(responses=Responses())

    first = agent.run(instructions="unit", payload={"id": 1}, response_model=CachedOutput)
    second = agent.run(instructions="unit", payload={"id": 1}, response_model=CachedOutput)

    assert first == second == CachedOutput(value="cached")
    assert calls == 1
    assert len(list(tmp_path.glob("*.json"))) == 1
