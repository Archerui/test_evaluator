# test_evaluator

An evidence-driven, multi-agent evaluator for generated BDD/Selenium E2E tests.
The design and research rationale are in [proposal.md](proposal.md).

## What is implemented

- CSV ingestion and requirement-suite grouping.
- Deterministic static verification of Gherkin, Behave decorators, Python AST,
  assertions, selectors, Selenium actions, waits, and teardown.
- OpenAI-backed Requirement, BDD Traceability, Step-Code, Oracle Critic, and
  Suite Coverage agents with structured Pydantic outputs.
- A deterministic coordinator that scores only evidence-backed results and
  reports `UNKNOWN` rather than inventing execution results.
- JSON and Markdown reports at test, requirement-suite, and project level.

The first version deliberately does **not** claim browser pass rate, code
coverage, or mutation score: the CSV does not include the applications or a
runtime. Mutation readiness is documented in the proposal as a follow-up.

## Run

The installed environment already includes the required Python packages. For a
fresh environment, install this project with:

```bash
python -m pip install -e '.[dev]'
```

Run deterministic checks over the full sample without calling an LLM:

```bash
python -m test_evaluator.cli --input e2edev_sample.csv --output reports/offline
```

Run the full semantic pipeline for a small, cost-controlled sample. The OpenAI
SDK reads `OPENAI_API_KEY` directly; the program never prints or stores it.

```bash
python -m test_evaluator.cli \
  --input e2edev_sample.csv \
  --output reports/live-smoke \
  --live \
  --limit 2
```

Optionally add the static Mutation Hypothesis Agent. Its result is labelled
`mutation_readiness`; it is not a real mutation score because no application
source is available in the CSV.

```bash
python -m test_evaluator.cli --live --limit 2 --mutation-hypotheses
```

`--model` defaults to `gpt-5-mini`; set it explicitly if a different model is
available in the account:

```bash
python -m test_evaluator.cli --live --limit 2 --model YOUR_AVAILABLE_MODEL
```

Each run writes `summary.md` for review and `evaluation.json` for downstream
analysis. Live full-dataset evaluation can make roughly three calls per test,
plus one requirement-contract and one suite-coverage call per requirement.

## Test

```bash
pytest -q
```
