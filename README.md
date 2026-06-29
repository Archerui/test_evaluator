# test_evaluator

An evidence-driven multi-agent evaluator for generated BDD/Selenium E2E tests.

- Research rationale: [proposal.md](proposal.md)
- Full implementation plan: [project.md](project.md)

## Implemented

- Basic CSV evaluation remains backward compatible.
- CSV, JSONL, and per-project `requirment_with_tests.json` ingestion.
- Discovery of cloned E2EDev projects, including the dataset's
  `source_projcet` directory spelling.
- Normalized Pydantic schemas for basic agents, source analysis, runtime,
  coverage, mutation, reports, and orchestrator state.
- Deterministic static verification of Gherkin, Behave decorators, Python AST,
  assertions, selectors, Selenium actions, waits, event construction, paths,
  and teardown.
- OpenAI-backed Requirement, BDD Traceability, Step-Code, Oracle Critic, and
  Suite Coverage agents with evidence validation.
- Checkpointed orchestrator states with input hashes, run manifests, cached
  resume, per-test/per-mutant recovery, per-call LLM caching, retry metadata,
  and degraded-stage reporting.
- Full-mode per-test workspaces that copy source, write Behave feature/step
  files, rewrite local entry paths, and leave the E2EDev clone unchanged.
- Deterministic HTML/JavaScript source models containing DOM anchors, event
  handlers, state effects, external APIs, and dynamically created IDs/classes.
- Selector grounding that checks Selenium locators and BDD `data-testid`
  anchors against the source model and records stability/purpose evidence.
- Baseline Behave/Selenium runner with headless Chrome hooks, timeout/process
  cleanup, retry, runtime artifact capture, and separate `fail`, `timeout`, and
  `env_error` outcomes.
- Runtime Trace classification with artifact-backed failure causes and flaky
  risk.
- Optional Chrome DevTools precise JavaScript coverage (`--coverage`).
- Real bounded mutation testing (`--mutation`) with event-name/handler, DOM
  update, external API, selector/storage string, comparison, boolean/numeric
  literal, and arithmetic operators. Mutants run in private disposable
  workspaces; invalid, timeout, and suspected-equivalent outcomes are excluded
  from the score.
- Behavior-grounded impacted-test selection with a conservative project-wide
  fallback, plus `--workers`-bounded parallel mutant execution.
- A checkpointed Dynamic Evidence stage that feeds runtime, oracle-target
  selector grounding, and killed/survived mutants back into test-level Dynamic
  Oracle and requirement-level Suite Coverage reviews. This evidence is shown
  explicitly and does not add a duplicate scoring weight.
- Coverage backend `auto`: Istanbul statement/branch/function coverage for
  external JavaScript, with automatic CDP precise-coverage fallback for inline
  scripts or unavailable instrumentation.
- Runtime observability artifacts for storage operations, fetch/XHR, selected
  browser APIs, and Chrome Network events; optional deterministic stubs for
  network, speech, clipboard, and notifications.
- Repeated unchanged baseline runs (`--stability-runs`) with flaky detection,
  soft runtime/mutation budgets, progress output, per-stage wall-clock costs,
  per-project test caps, and JSONL historical trend deltas.
- Proposal-weighted full test and requirement scoring with explicit hard gates
  and evidence-availability thresholds.
- JSON and Markdown reports at test, requirement-suite, and project level.

Full mode now executes the complete basic pipeline, source modeling/selector
grounding, baseline/runtime tracing, optional coverage, real mutation testing,
and full scoring. Unavailable values are reported as degraded or `N/A` rather
than invented.

## Install

```bash
python -m pip install -e '.[dev]'
```

For full-mode browser execution, install the runtime extra and make Chrome or
Chromium available on `PATH`:

```bash
python -m pip install -e '.[dev,full]'
```

Istanbul coverage additionally uses Node.js and `istanbul-lib-instrument`.
When either is unavailable, `--coverage-method auto` falls back to CDP.

```bash
npm install
```

## Basic mode

Run deterministic checks over the CSV sample:

```bash
python -m test_evaluator.cli \
  --mode basic \
  --input e2edev_sample.csv \
  --output reports/basic-offline
```

Run the semantic agents for a controlled sample:

```bash
python -m test_evaluator.cli \
  --mode basic \
  --input e2edev_sample.csv \
  --output reports/basic-live \
  --live \
  --limit 2
```

Read the cloned E2EDev project JSON directly:

```bash
python -m test_evaluator.cli \
  --mode basic \
  --e2edev-root E2EDev \
  --projects E2ESD_Bench_01 \
  --output reports/basic-e2edev
```

Optionally add the static Mutation Hypothesis Agent. This produces
`mutation_readiness`, not a real mutation score:

```bash
python -m test_evaluator.cli \
  --mode basic \
  --live \
  --limit 2 \
  --mutation-hypotheses
```

## Full mode

```bash
python -m test_evaluator.cli \
  --mode full \
  --e2edev-root E2EDev \
  --projects E2ESD_Bench_01 \
  --output reports/full-smoke \
  --max-tests 2 \
  --workers 2 \
  --runner-timeout 60 \
  --stability-runs 2 \
  --coverage \
  --coverage-method auto \
  --mutation \
  --max-mutants 30 \
  --max-mutants-per-project 30
```

Useful controls for larger runs:

```bash
  --max-tests-per-project 1 \
  --runtime-budget 300 \
  --mutation-budget 900 \
  --browser-stubs speech,clipboard \
  --history-file reports/history.jsonl
```

Each selected test gets an isolated workspace. The summary and
`projects/<project>/runtime_results.json` distinguish an assertion/test failure
from a missing package or browser (`env_error`). Headless mode is the default;
use `--no-headless` for local debugging.

Full mode also writes source models, selector grounding, runtime traces,
coverage, mutation plans/results, and a per-project summary. Use
`--requirements` and `--tests` for targeted runs; `--max-projects`,
`--max-tests`, and `--max-mutants` bound larger evaluations.

## Resume

Reuse state checkpoints when the configuration and input hashes are unchanged:

```bash
python -m test_evaluator.cli \
  --mode basic \
  --input e2edev_sample.csv \
  --output reports/basic-live \
  --live \
  --limit 2 \
  --resume
```

Every run writes:

```text
reports/<run>/
  summary.md
  evaluation.json
  config.json
  inventory.json
  run_manifest.json
  checkpoints/
  projects/<project>/runtime_results.json
  projects/<project>/stability_results.json
  projects/<project>/source_model.json
  projects/<project>/selector_grounding.json
  projects/<project>/runtime_traces.json
  projects/<project>/coverage.json
  projects/<project>/mutation_plan.json
  projects/<project>/mutation_results.json
  projects/<project>/dynamic_evidence.json
  history.jsonl
  projects/<project>/project_summary.md
  workspaces/<run-id>/<test>/
```

## Test

```bash
pytest -q
```
