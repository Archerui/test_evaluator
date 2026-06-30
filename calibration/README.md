# Basic Evaluator Golden Calibration Set

`golden_basic_v1.json` contains 24 human-labelled agent decisions over eight
representative records from `e2edev_sample.csv`:

- 8 BDD Traceability decisions
- 8 Step-Code decisions
- 8 Oracle Critic decisions

The set deliberately includes strong event-payload flow, DOM-only proxies,
constant/helper placeholders, an unspecified negative scenario, persistence,
Markdown DOM semantics, a browser speech API, and network-backed result UI.

`expected_status` is the expected normalized status after evidence validation
and coordinator status normalization. These labels are calibration targets, not
automatically inferred ground truth. Changes require human review and a short
rationale in the case.

Validate record references and deterministic assertion-flow expectations:

```bash
python -m test_evaluator.calibration
```

Compare any evaluation containing some or all golden records:

```bash
python -m test_evaluator.calibration \
  --evaluation reports/<run>/evaluation.json
```

The comparison reports matched, compared, skipped, per-agent accuracy, and
individual mismatches. A partial run is valid; absent golden records are
reported as skipped rather than incorrect.

## Mutation calibration

Full runs with real mutation testing additionally write
`mutation_calibration.json`. Matching is intentionally general:

- static and real cases are joined by generic mutation operator/fault class;
- behavior IDs are used only when both sides provide them;
- invalid, timed-out, and suspected-equivalent mutants are excluded;
- results are aggregated as a confusion matrix and per-fault-class accuracy;
- no benchmark-specific title, selector, value, or requirement text is added to
  prompts or calibration rules.

The artifact always contains `scoring_effect: none`. It is offline feedback for
future prompt/rule calibration and never modifies the run's basic or full score.
