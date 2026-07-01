# Test Evaluator Report

- Run ID: `489cd8af8a954658a23aa181be9577de`
- Mode: `full`
- Semantic agents: `live`
- Model: `gpt-5-mini`
- Tests analysed: 12
- Requirement suites analysed: 3

## Project Summary

| Project | Tests | Requirements | Basic Test Quality | Full Test Quality | Requirement Adequacy | Runtime Pass | Mutation | Unknown Rate | Risks |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| E2ESD_Bench_01 | 12 | 3 | 64.6 | 62.2 | 78.6 | 100% | 88.9 | 0% | critical: 4, major: 3, medium: 5 |

## Test Results

| Test | Scenario | Basic Score | Full Score | Source Grounding | Runtime | Failure origin | Stability | Dynamic Oracle | Mutation | Basic Evidence | Full Evidence | Risk | Hard Gates |
|---|---|---:|---:|---|---|---|---|---|---:|---:|---:|---|---|
| E2ESD_Bench_01::1::1 | Normal | 95.0 | 76.7 | PASS | pass | no_failure | PASS (100%) | WARNING | 16.7 | 100% | 100% | medium | — |
| E2ESD_Bench_01::1::2 | Edge | 20.0 | 30.0 | PASS | pass | no_failure | PASS (100%) | FAIL | 0.0 | 100% | 100% | critical | critical_oracle_gap, mutation_score_zero |
| E2ESD_Bench_01::1::3 | Edge | 20.0 | 30.0 | PASS | pass | no_failure | PASS (100%) | FAIL | 0.0 | 100% | 100% | critical | critical_oracle_gap, mutation_score_zero |
| E2ESD_Bench_01::1::4 | Error | 20.0 | 30.0 | PASS | pass | no_failure | PASS (100%) | FAIL | 0.0 | 100% | 100% | critical | critical_oracle_gap, mutation_score_zero |
| E2ESD_Bench_01::3::1 | Normal | 95.0 | 85.5 | PASS | pass | no_failure | PASS (100%) | WARNING | 52.0 | 100% | 100% | medium | — |
| E2ESD_Bench_01::3::2 | Normal | 52.5 | 58.5 | PASS | pass | no_failure | PASS (100%) | WARNING | 44.0 | 100% | 100% | major | — |
| E2ESD_Bench_01::3::3 | Normal | 82.5 | 85.0 | PASS | pass | no_failure | PASS (100%) | PASS | 80.0 | 100% | 100% | major | — |
| E2ESD_Bench_01::3::4 | Edge | 95.0 | 84.5 | PASS | pass | no_failure | PASS (100%) | WARNING | 48.0 | 100% | 100% | medium | — |
| E2ESD_Bench_01::5::1 | Normal | 62.5 | 63.7 | PASS | pass | no_failure | PASS (100%) | WARNING | 35.0 | 100% | 100% | major | — |
| E2ESD_Bench_01::5::2 | Normal | 77.5 | 71.2 | PASS | pass | no_failure | PASS (100%) | WARNING | 35.0 | 100% | 100% | medium | — |
| E2ESD_Bench_01::5::3 | Normal | 95.0 | 81.2 | PASS | pass | no_failure | PASS (100%) | WARNING | 35.0 | 100% | 100% | medium | — |
| E2ESD_Bench_01::5::4 | Edge | 60.0 | 50.0 | PASS | pass | no_failure | PASS (100%) | WARNING | 35.0 | 100% | 100% | critical | critical_oracle_gap |

## Run Health

- States: cached: 8, succeeded: 14
- Cache hits: 27
- Cache misses: 19
- Resume used: True
- Baseline runtime: {'pass': 12}
- Mutation outcomes: {'killed': 24, 'survived': 3}
- Flaky tests: 0
- Baseline runtime seconds: 72.01

## Basic Evaluation Details

Dimension cells show the normalized evidence status and its score out of 100. `UNKNOWN` is excluded from scoring.

| Test | Spec alignment | Step traceability | Oracle strength | Robustness | Basic Evidence | Basic Score | Unknown dimensions |
|---|---|---|---|---|---:|---:|---|
| E2ESD_Bench_01::1::1 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::1::2 | WARNING (50) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 20.0 | — |
| E2ESD_Bench_01::1::3 | WARNING (50) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 20.0 | — |
| E2ESD_Bench_01::1::4 | WARNING (50) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 20.0 | — |
| E2ESD_Bench_01::3::1 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::3::2 | PASS (100) | FAIL (0) | WARNING (50) | WARNING (50) | 100% | 52.5 | — |
| E2ESD_Bench_01::3::3 | PASS (100) | WARNING (50) | PASS (100) | WARNING (50) | 100% | 82.5 | — |
| E2ESD_Bench_01::3::4 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::5::1 | WARNING (50) | PASS (100) | WARNING (50) | WARNING (50) | 100% | 62.5 | — |
| E2ESD_Bench_01::5::2 | PASS (100) | PASS (100) | WARNING (50) | WARNING (50) | 100% | 77.5 | — |
| E2ESD_Bench_01::5::3 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::5::4 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |

## Baseline Runtime Details

Raw execution status is separated from failure ownership. Only `test_defect` with effect `penalize` lowers the test runtime score; application, environment, evaluator, contract, and indeterminate failures remain neutral or `UNKNOWN`.

| Test | Status | Error type | Failure origin | Test-quality effect | Attribution confidence | Failed step | Duration (s) |
|---|---|---|---|---|---:|---|---:|
| E2ESD_Bench_01::1::1 | pass | — | no_failure | pass | 100% | — | 5.03 |
| E2ESD_Bench_01::1::2 | pass | — | no_failure | pass | 100% | — | 7.11 |
| E2ESD_Bench_01::1::3 | pass | — | no_failure | pass | 100% | — | 5.01 |
| E2ESD_Bench_01::1::4 | pass | — | no_failure | pass | 100% | — | 2.86 |
| E2ESD_Bench_01::3::1 | pass | — | no_failure | pass | 100% | — | 7.45 |
| E2ESD_Bench_01::3::2 | pass | — | no_failure | pass | 100% | — | 11.64 |
| E2ESD_Bench_01::3::3 | pass | — | no_failure | pass | 100% | — | 7.92 |
| E2ESD_Bench_01::3::4 | pass | — | no_failure | pass | 100% | — | 7.19 |
| E2ESD_Bench_01::5::1 | pass | — | no_failure | pass | 100% | — | 2.86 |
| E2ESD_Bench_01::5::2 | pass | — | no_failure | pass | 100% | — | 4.02 |
| E2ESD_Bench_01::5::3 | pass | — | no_failure | pass | 100% | — | 5.02 |
| E2ESD_Bench_01::5::4 | pass | — | no_failure | pass | 100% | — | 5.90 |

## Requirement Suites

| Suite | Tests | Scenario types | Basic Adequacy | Basic Evidence | Full Adequacy | Full Evidence | Runtime Pass | Flaky | Dynamic Behaviors | Mutation | Partial input |
|---|---:|---|---:|---:|---:|---:|---:|---:|---|---:|---|
| E2ESD_Bench_01::1 | 4 | Edge: 2, Error: 1, Normal: 1 | 50.8 | 100% | 63.7 | 100% | 100% | 0 | WARNING: 6 | 16.7 | False |
| E2ESD_Bench_01::3 | 4 | Edge: 1, Normal: 3 | 86.2 | 100% | 93.3 | 100% | 100% | 0 | PASS: 1, WARNING: 4 | 84.0 | False |
| E2ESD_Bench_01::5 | 4 | Edge: 1, Normal: 3 | 75.0 | 100% | 78.8 | 100% | 100% | 0 | WARNING: 4 | 40.0 | False |

## Static Behavior Coverage

Coverage is requirement-level. Data variants do not count as independent behaviors.

| Suite | Behavior | Status | Strong tests | Weak tests | All declaring tests |
|---|---|---|---|---|---|
| E2ESD_Bench_01::1 | 1.1 | WARNING | — | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 |
| E2ESD_Bench_01::1 | 1.2 | FAIL | — | — | — |
| E2ESD_Bench_01::1 | 1.3 | WARNING | — | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 |
| E2ESD_Bench_01::1 | 1.4 | WARNING | — | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 |
| E2ESD_Bench_01::1 | 1.5 | FAIL | — | — | — |
| E2ESD_Bench_01::1 | 1.6 | FAIL | — | — | — |
| E2ESD_Bench_01::3 | 3.normal.product_list_visible_on_load | WARNING | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal.add_single_product_via_drag_and_drop | WARNING | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal.add_same_product_multiple_times_increments_quantity | WARNING | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal.add_multiple_distinct_products_create_separate_entries | WARNING | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal.cart_total_updates_and_formats_currency | WARNING | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::5 | B-5-1-add-single-product-updates-total | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |
| E2ESD_Bench_01::5 | B-5-2-sum-multiple-products-updates-total | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |
| E2ESD_Bench_01::5 | B-5-3-repeated-drops-increment-quantity-and-affect-total | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |
| E2ESD_Bench_01::5 | B-5-4-real-time-total-update-on-add | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |

## Suite Duplicate Analysis

| Suite | Semantic duplicate ratio | Kind | Tests | Reason |
|---|---:|---|---|---|
| E2ESD_Bench_01::1 | 50% | semantic_scenario | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3 | The scenarios exercise the same step structure after replacing concrete values, numbers, and test-id suffixes. |
| E2ESD_Bench_01::5 | 25% | semantic_scenario | E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3 | The scenarios exercise the same step structure after replacing concrete values, numbers, and test-id suffixes. |

## Stability Runs

| Test | Runs completed/requested | Pass rate | Flaky | Outcomes |
|---|---:|---:|---|---|
| E2ESD_Bench_01::1::1 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::1::2 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::1::3 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::1::4 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::3::1 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::3::2 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::3::3 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::3::4 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::5::1 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::5::2 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::5::3 | 2/2 | 100% | False | pass, pass |
| E2ESD_Bench_01::5::4 | 2/2 | 100% | False | pass, pass |

## Dynamic Evidence Feedback

This layer feeds runtime, selector grounding, and mutation outcomes back into Oracle/Suite reviews. It is explanatory evidence and is not added as another score weight.

| Suite | Behavior | Status | Runtime-confirmed tests | Killed mutants | Survived mutants |
|---|---|---|---:|---:|---:|
| E2ESD_Bench_01::1 | 1.1 | WARNING | 2 | 2 | 3 |
| E2ESD_Bench_01::1 | 1.2 | WARNING | 2 | 1 | 3 |
| E2ESD_Bench_01::1 | 1.3 | WARNING | 2 | 3 | 4 |
| E2ESD_Bench_01::1 | 1.4 | WARNING | 0 | 1 | 4 |
| E2ESD_Bench_01::1 | 1.5 | WARNING | 0 | 1 | 2 |
| E2ESD_Bench_01::1 | 1.6 | WARNING | 0 | 1 | 2 |
| E2ESD_Bench_01::3 | 3.normal.product_list_visible_on_load | PASS | 2 | 1 | 0 |
| E2ESD_Bench_01::3 | 3.normal.add_single_product_via_drag_and_drop | WARNING | 4 | 11 | 3 |
| E2ESD_Bench_01::3 | 3.normal.add_same_product_multiple_times_increments_quantity | WARNING | 4 | 10 | 3 |
| E2ESD_Bench_01::3 | 3.normal.add_multiple_distinct_products_create_separate_entries | WARNING | 4 | 10 | 3 |
| E2ESD_Bench_01::3 | 3.normal.cart_total_updates_and_formats_currency | WARNING | 0 | 4 | 3 |
| E2ESD_Bench_01::5 | B-5-1-add-single-product-updates-total | WARNING | 2 | 6 | 4 |
| E2ESD_Bench_01::5 | B-5-2-sum-multiple-products-updates-total | WARNING | 2 | 5 | 4 |
| E2ESD_Bench_01::5 | B-5-3-repeated-drops-increment-quantity-and-affect-total | WARNING | 2 | 5 | 4 |
| E2ESD_Bench_01::5 | B-5-4-real-time-total-update-on-add | WARNING | 2 | 4 | 3 |

## Real Mutation Testing

### `E2ESD_Bench_01`

- Mutation score: 88.9
- Top survived mutants: 3
  - `E2ESD_Bench_01-m1a7468a55232` — event_name at `index.html:41`
  - `E2ESD_Bench_01-m60f1ff8eb429` — numeric_literal at `index.html:37`
  - `E2ESD_Bench_01-m4f3d9524fe2a` — numeric_literal at `index.html:37`

## Mutation Readiness (Static Estimate)

This is a requirement/oracle-based hypothesis, not a mutation score. No application code was mutated or executed.

| Test | Mutation readiness | Prediction coverage | Likely detected | Likely survives | Unknown |
|---|---:|---:|---:|---:|---:|
| E2ESD_Bench_01::1::1 | 100.0 | 100% | 3 | 0 | 0 |
| E2ESD_Bench_01::1::2 | 0.0 | 100% | 0 | 3 | 0 |
| E2ESD_Bench_01::1::3 | 0.0 | 100% | 0 | 3 | 0 |
| E2ESD_Bench_01::1::4 | 0.0 | 100% | 0 | 3 | 0 |
| E2ESD_Bench_01::3::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::3 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::4 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::3 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::4 | 100.0 | 100% | 2 | 0 | 0 |

## Static-to-Real Mutation Calibration

This offline diagnostic compares generic static fault-class predictions with full-mode mutation outcomes. It has no scoring effect on basic or full quality scores.

- Comparable observations: 80
- Prediction accuracy: 52%
- Scoring effect: `none`

| Generic fault class | Observations | Matched | Accuracy |
|---|---:|---:|---:|
| dom_update | 68 | 36 | 53% |
| string_literal | 12 | 6 | 50% |

### General Calibration Actions

- `dom_update` / static_overconfidence (32): Require a more direct or more specific assertion path before predicting likely_detected for this generic fault class.
- `string_literal` / static_overconfidence (6): Require a more direct or more specific assertion path before predicting likely_detected for this generic fault class.

## Major and Critical Findings

### `E2ESD_Bench_01::1::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m137c2855bb5b survives this test
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mc5efa4ace1b0 survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m385c97ea419c survives this test
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m137c2855bb5b
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mc5efa4ace1b0
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m385c97ea419c
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::2` — bdd_traceability

- **major / WARNING**: Test implementation coverage for DataTransfer payload verification
- Evidence: `Then the drag event should be initiated`
- Reason: Although the scenario expresses the expected observable (the drag event and captured title/price), the provided static_facts show no assertions that check the event payload (event_payload_assertion_count = 0) and indicate drag event dispatch was not observed in the recorded assertions (drag_event_dispatched = false). This suggests the scenario's claim to capture DataTransfer payload may not be verified by the test implementation.
- Suggested fix: Add explicit assertions that read the drag event's DataTransfer payload (or its test double) and verify the title and price keys/values are set when the item is dragged. Ensure the test dispatches a dragstart with a DataTransfer containing the title and price, or that the test reads those keys from the actual drag event.

### `E2ESD_Bench_01::1::2` — step_code

- **critical / FAIL**: Then steps must prove the drag event's transfer data contains the product title and price
- Evidence: `And the product title "JavaScript: The Definitive Guide" should be captured`
- Reason: The Gherkin expectation is that the drag event's transfer data contains title and price. The implemented Then steps only read DOM text (asserting title and price strings from product-item-2's children) and do not read or assert any DataTransfer payload. static_facts shows no data_transfer read assertions ("data_transfer_read_keys": []). Therefore the test cannot establish that the drag event's transfer data actually captured the title and price.
- Suggested fix: Add assertions that read the event's DataTransfer payload populated by the application's dragstart handler. Options: (a) attach a test listener or use execute_script to observe the application's dragstart handler storing payload (e.g. on a global variable or DOM node) and assert that contains the title/price, or (b) after dispatch, read the relevant DataTransfer keys (e.g. event.dataTransfer.getData(...)) if the application sets them. Ensure the test asserts on the DataTransfer content rather than only DOM text.

### `E2ESD_Bench_01::1::2` — oracle_critic

- **critical / FAIL**: The test must assert the DragEvent.dataTransfer payload contains the dragged product's title and price (e.g. via reading event.dataTransfer.getData or inspecting the dispatched DataTransfer).
- Evidence: `assert title == "JavaScript: The Definitive Guide", f"Expected title 'JavaScript: The Definitive Guide', but got '{title}'"`
- Reason: The test constructs and dispatches a DragEvent with a new DataTransfer, but it never reads or asserts any values from the event.dataTransfer object. All assertions are DOM observations of the product title/price text. According to the static facts, there are zero event-payload assertions and four DOM assertions, so the test cannot detect regressions where the application fails to put title/price into the DataTransfer payload.
- Suggested fix: Make the oracle read the DataTransfer content produced by the dragstart handler and assert the title and price are present. For example, add a temporary dragstart listener (via execute_script) that captures event.dataTransfer.getData('text/plain') or event.dataTransfer.getData('application/json') into window.__lastDragPayload, then dispatch the synthetic DragEvent and assert window.__lastDragPayload contains the expected title and price. Alternatively, after dispatching, run execute_script to inspect the dispatched event's DataTransfer (or set and later read a known key via dataTransfer.setData/getData) and assert exactly the expected payload.

### `E2ESD_Bench_01::1::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m33557c7e5dc6 survives this test
- Evidence: `window.onload = function () {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mca5115e03cb8 survives this test
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m137c2855bb5b survives this test
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m33557c7e5dc6
- Evidence: `window.onload = function () {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mca5115e03cb8
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m137c2855bb5b
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::3` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: is_drag_event_initiated(context.driver, product_item), True`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_01::1::3` — bdd_traceability

- **major / WARNING**: Scenario does not explicitly assert that the captured title and price are present in the drag event's transfer (DataTransfer) payload as required by the behaviour contract.
- Evidence: `When the user drags a product item (li element) from the product list, the system should initiate a drag event, capturing the product's title and price for transfer.`
- Reason: The requirement explicitly targets the drag event's transfer data (DataTransfer payload) as the observable that must contain title and price. The scenario asserts that the title and price are "captured" but does not explicitly state they are placed into the drag event's transfer payload, leaving the exact observable unspecified.
- Suggested fix: Make the Then steps explicit about the transfer payload, e.g. "Then the drag event's transfer data should contain the product title 'Mastering JavaScript' and price '$35'".

### `E2ESD_Bench_01::1::3` — step_code

- **critical / FAIL**: The When/Then steps that assert the drag event was initiated are implemented as placeholders/constants rather than observing a real dragstart or DataTransfer payload.
- Evidence: `def is_drag_event_initiated(driver, product_item):
    # This function checks if the drag event is initiated by checking the dataTransfer object
    # Since Selenium does not support drag and drop natively, this is a placeholder for actual implementation
    # In a real-world scenario, you might need to use JavaScript to simulate drag and drop
    return True`
- Reason: Both the When step and the Then step that claim the drag event was initiated rely on a constant-return placeholder (is_drag_event_initiated returns True) and an unconditional assertion (assert True). There is no creation or dispatch of a drag event, nor any reading of event.dataTransfer in the test code, so the test cannot actually verify that a dragstart occurred or that the application populated a DataTransfer payload.
- Suggested fix: Replace the placeholder with a concrete mechanism: simulate a user drag (e.g., dispatch a real dragstart on the target element via execute_script or use a library that triggers drag events) and capture/return the page-side event.dataTransfer contents (attach a temporary dragstart listener in the page that records dataTransfer keys/values so the test can assert them). Remove constant True returns and assert actual observed payloads.

### `E2ESD_Bench_01::1::3` — step_code

- **major / FAIL**: The assertions that the product title and price were "captured" observe DOM text only and do not read the drag event's DataTransfer payload required by the behavior contract.
- Evidence: `Then the drag event should be initiated
    And the product title "Mastering JavaScript" should be captured
    And the product price "$35" should be captured`
- Reason: The behaviour contract requires that the drag event's transfer data contains title and price. The test only reads the page DOM (innerText of product-title-3 and product-price-3). DOM text presence proves the page shows those values but does not prove that a dragstart handler populated the DataTransfer with them. The test contains no code that reads event.dataTransfer or any page-side record of the drag payload.
- Suggested fix: Assert the transfer payload directly: install a page-side dragstart listener (via execute_script) that captures event.dataTransfer contents when the dragstart occurs and exposes them (e.g., by returning the captured payload or writing it to a known DOM element). Then assert that the captured payload includes "Mastering JavaScript" and "$35". Alternatively, if the app persists the drag payload somewhere observable, read that persisted value instead of only checking DOM labels.

### `E2ESD_Bench_01::1::3` — oracle_critic

- **critical / FAIL**: The test must assert that the drag event's DataTransfer payload contains the product title and price.
- Evidence: `When the user drags a product item (li element) from the product list, the system should initiate a drag event, capturing the product's title and price for transfer.`
- Reason: The requirement expects the test to observe the browser drag event payload (DataTransfer) containing title and price. The test only reads DOM text nodes for title and price (dom_observation) and has no creation/reading of a DataTransfer or assertions against event payload (static_facts shows event_payload_assertion_count = 0). A DOM read does not prove that the drag event transfer data captured those values, so the oracle is too weak to detect a regression in the drag payload behavior.
- Suggested fix: Replace or augment the DOM assertions with a concrete browser-API observation: simulate/dispatch a dragstart in-page and read the DataTransfer keys/values (via execute_script), or install an in-page dragstart listener that records event.dataTransfer.getData(...) for assertion. Ensure test asserts exact DataTransfer keys/values for title and price.

### `E2ESD_Bench_01::1::3` — oracle_critic

- **critical / FAIL**: The test must verify that a real dragstart event was initiated (not by returning a constant).
- Evidence: `assert is_drag_event_initiated(context.driver, product_item), "Drag event was not initiated"`
- Reason: The helper is_drag_event_initiated is a placeholder that returns True unconditionally (constant). Static analysis classifies the assertion as coming from a constant. Thus the test would pass even if no dragstart event occurred in the browser, making the oracle ineffective at catching regressions that break dragstart dispatch or handling.
- Suggested fix: Implement a real check: either trigger a synthetic dragstart and observe the event (e.g. install a one-time dragstart listener that records event existence and payload on the page and read it via execute_script), or use browser APIs to inspect DataTransfer after dispatch. Avoid returning fixed constants for event verification.

### `E2ESD_Bench_01::1::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m33557c7e5dc6 survives this test
- Evidence: `window.onload = function () {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mca5115e03cb8 survives this test
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m137c2855bb5b survives this test
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m33557c7e5dc6
- Evidence: `window.onload = function () {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mca5115e03cb8
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m137c2855bb5b
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::4` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: True, True`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_01::1::4` — bdd_traceability

- **major / WARNING**: Scenario does not exercise the requirement's core positive behavior: initiating a drag on a draggable product li and capturing title and price.
- Evidence: `When the user drags a product item (li element) from the product list, the system should initiate a drag event, capturing the product's title and price for transfer.`
- Reason: The behaviour contract requires a scenario where the actor initiates a drag on a draggable product 'li' and the drag transfer contains the product title and price. The provided scenario is an error/negative case that attempts to drag a non-draggable element ('drop-area') and asserts no drag or capture occurs. That negative case neither verifies nor contradicts the required positive behaviour, so it does not satisfy the contract's core observable outcome.
- Suggested fix: Add a complementary positive scenario that performs: Given a product list with a draggable product item, When the user initiates a drag on the product li (e.g. data-testid 'product-item-1'), Then the drag event transfer data contains the product title and price (e.g. values from 'product-title-1' and 'product-price-1').

### `E2ESD_Bench_01::1::4` — step_code

- **critical / FAIL**: The Then steps that claim no product title/price are captured are implemented as constant assertions and do not observe application state or DataTransfer payload.
- Evidence: `And no product title should be captured`
- Reason: Both Then steps for title and price return constant True assertions rather than reading DOM text, executing JS to inspect DataTransfer, or otherwise observing application state. Constant assertions cannot establish that the drag payload did or did not contain title/price.
- Suggested fix: Replace the placeholder asserts with concrete checks: either execute page JS to read any recorded drag payload (e.g. inspection of an application-visible store or event-captured element), or assert absence/presence of DOM changes that the app uses to record a drag. Avoid assert True placeholders.

### `E2ESD_Bench_01::1::4` — step_code

- **major / FAIL**: The When step does not perform or simulate a dragstart; it only inspects the element's 'draggable' attribute (an attribute proxy) to decide whether a drag was initiated.
- Evidence: `When the user attempts to drag the non-draggable element with data-testid "drop-area"`
- Reason: The step claims to 'attempt to drag' but the implementation merely reads the element's 'draggable' attribute. Per the review rules, 'draggable' is a proxy for capability and does not prove a dragstart event was initiated or that the application's dragstart handler ran. There is no synthetic dragstart dispatch, no DataTransfer creation/read, and no execute_script usage to observe event payload.
- Suggested fix: Either simulate the dragstart (construct DataTransfer and dispatch a dragstart event) and then inspect application-observable effects, or instrument the page (via execute_script) to confirm whether a real dragstart handler ran and what it populated in DataTransfer. Do not rely solely on the 'draggable' attribute to prove a drag occurred.

### `E2ESD_Bench_01::1::4` — oracle_critic

- **critical / FAIL**: Then 'no drag event should be initiated' is automatically observed by the test.
- Evidence: `return element.get_attribute("draggable") == "true"`
- Reason: The test infers whether a drag event was initiated solely by reading the element's draggable attribute (element_attribute_proxy). This does not observe browser dragstart events or the DataTransfer API; an application could still dispatch a dragstart/DataTransfer programmatically or set payloads even if the attribute differs, so the oracle is not strong enough to rule out a drag event.
- Suggested fix: Replace the attribute-only check with a concrete browser-API observation: attach a JS listener for 'dragstart' and record the event, or synthesize the drag and read the DataTransfer contents (via execute_script) to confirm no event was dispatched.

### `E2ESD_Bench_01::1::4` — oracle_critic

- **critical / FAIL**: Then 'no product title should be captured' is automatically observed by the test.
- Evidence: `assert True, "No product title should be captured."`
- Reason: The step uses a constant assertion (assert True) as a placeholder rather than inspecting any DataTransfer payload or application state. A constant cannot prove that no title was captured, so this oracle is absent/too weak to detect the regression targeted by the requirement.
- Suggested fix: Assert the absence of title in the drag payload by reading the DataTransfer data during/after dragstart (e.g. via a JS listener that records event.dataTransfer.getData('text/plain') or specific keys), or verify handlers did not set a title key.

### `E2ESD_Bench_01::1::4` — oracle_critic

- **critical / FAIL**: Then 'no product price should be captured' is automatically observed by the test.
- Evidence: `assert True, "No product price should be captured."`
- Reason: Like the title check, the price check is a placeholder constant and does not inspect the browser's DataTransfer payload or any event-recording mechanism. The test therefore cannot prove that no price was captured during a drag.
- Suggested fix: Capture and assert the contents (or absence) of the price key on the DataTransfer object during dragstart (e.g. via a JS dragstart listener that stores event.dataTransfer.getData for the test to read).

### `E2ESD_Bench_01::1::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m33557c7e5dc6 survives this test
- Evidence: `window.onload = function () {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mca5115e03cb8 survives this test
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m137c2855bb5b survives this test
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::1::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m33557c7e5dc6
- Evidence: `window.onload = function () {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mca5115e03cb8
- Evidence: `        aLi[i].ondragstart = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m137c2855bb5b
- Evidence: `    oDiv.ondrop = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::1::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1da5859e33ed survives this test
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m976254f1b78e survives this test
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The test passed after the string_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mca040c016b3e survives this test
- Evidence: `            var box2 = document.getElementsByClassName('box2');`
- Reason: The test passed after the string_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c6926cf32e9 survives this test
- Evidence: `                if (box2[i].innerHTML == sTitle) {`
- Reason: The test passed after the comparison mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1da5859e33ed
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m976254f1b78e
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The baseline test passed and also passed after the string_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mca040c016b3e
- Evidence: `            var box2 = document.getElementsByClassName('box2');`
- Reason: The baseline test passed and also passed after the string_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c6926cf32e9
- Evidence: `                if (box2[i].innerHTML == sTitle) {`
- Reason: The baseline test passed and also passed after the comparison mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::2` — step_code

- **critical / FAIL**: Then steps asserting product prices use correct boolean logic to fail when price is missing
- Evidence: `assert "$40" in prices or "$40.00", "Price '$40' not found in cart"`
- Reason: Both price assertions use the expression `assert A or "literal", "msg"`. In Python this yields a truthy value even when A is False (the right-hand string is truthy), causing the assertion to always pass and therefore not actually verify the expected prices. Because price checks are core Then expectations for this scenario, this is a critical verification bug.
- Suggested fix: Change to explicit boolean assertions, e.g. `assert "$40" in prices or "$40.00" in prices, "Price '$40' not found in cart"` or `assert any(p in ("$40","$40.00") for p in prices), ...`.

### `E2ESD_Bench_01::3::2` — oracle_critic

- **major / WARNING**: Cart unit price checks use a partially constrained assertion and can pass without matching DOM text
- Evidence: `assert "$40" in prices or "$40.00", "Price '$40' not found in cart"`
- Reason: The price assertions are written as e.g. '"$40" in prices or "$40.00"' which, due to Python operator semantics, does not reliably assert that either '$40' or '$40.00' is present in the collected prices list. Static facts mark these as dom_observation, but the logical expression is weak/incorrect and could pass even when the DOM lacks the expected price text.
- Suggested fix: Change the assertions to actually check membership in the DOM-derived list, e.g. 'any(p in prices for p in ["$40","$40.00"])' or '"$40" in prices or "$40.00" in prices' so the test fails when the expected price text is absent.

### `E2ESD_Bench_01::3::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mbb6fadc93d33 survives this test
- Evidence: `            oSpan.innerHTML = sMoney;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mc59b50551451 survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1da5859e33ed survives this test
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m976254f1b78e survives this test
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The test passed after the string_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mbb6fadc93d33
- Evidence: `            oSpan.innerHTML = sMoney;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mc59b50551451
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1da5859e33ed
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m976254f1b78e
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The baseline test passed and also passed after the string_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::3` — step_code

- **major / WARNING**: Risk: the action locates the drop target by data-testid while the Then assertions inspect #div1; if the drop-area element does not also have id="div1" the test may not observe the cart update.
- Evidence: `When the user drags the product item with data-testid "product-item-3" and drops it into the drop area with data-testid "drop-area"`
- Reason: The When implementation dispatches drag/drop to the element found by [data-testid='{cart_id}'] (the action target uses the data-testid value), but the Then assertions query children of #div1. If the element identified by data-testid="drop-area" is not the same DOM element with id="div1", the test's DOM assertions will not observe the cart changes even though the drag/drop events were dispatched to a different element.
- Suggested fix: Use the same selector family for action and verification (e.g., locate the drop area by data-testid everywhere, or ensure the element with data-testid="drop-area" also has id="div1"). Update Then steps to assert relative to the same element used in the When step (e.g., find the drop-area element and then query its .box2/.box3/.box1 children).

### `E2ESD_Bench_01::3::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m3a3759d24959 survives this test
- Evidence: `    var iNum = 0; // 总金额`
- Reason: The test passed after the numeric_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-md72a1bf9a3c3 survives this test
- Evidence: `    for (var i = 0; i < aLi.length; i++) {`
- Reason: The test passed after the numeric_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m60f1ff8eb429 survives this test
- Evidence: `            ev.dataTransfer.setDragImage(this, 0, 0);`
- Reason: The test passed after the numeric_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m4f3d9524fe2a survives this test
- Evidence: `            ev.dataTransfer.setDragImage(this, 0, 0);`
- Reason: The test passed after the numeric_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m3a3759d24959
- Evidence: `    var iNum = 0; // 总金额`
- Reason: The baseline test passed and also passed after the numeric_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-md72a1bf9a3c3
- Evidence: `    for (var i = 0; i < aLi.length; i++) {`
- Reason: The baseline test passed and also passed after the numeric_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m60f1ff8eb429
- Evidence: `            ev.dataTransfer.setDragImage(this, 0, 0);`
- Reason: The baseline test passed and also passed after the numeric_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m4f3d9524fe2a
- Evidence: `            ev.dataTransfer.setDragImage(this, 0, 0);`
- Reason: The baseline test passed and also passed after the numeric_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1da5859e33ed survives this test
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m976254f1b78e survives this test
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The test passed after the string_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mca040c016b3e survives this test
- Evidence: `            var box2 = document.getElementsByClassName('box2');`
- Reason: The test passed after the string_literal mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c6926cf32e9 survives this test
- Evidence: `                if (box2[i].innerHTML == sTitle) {`
- Reason: The test passed after the comparison mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::3::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1da5859e33ed
- Evidence: `                    box1[i].innerHTML = parseInt(box1[i].innerHTML) + 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m976254f1b78e
- Evidence: `            var box1 = document.getElementsByClassName('box1');`
- Reason: The baseline test passed and also passed after the string_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mca040c016b3e
- Evidence: `            var box2 = document.getElementsByClassName('box2');`
- Reason: The baseline test passed and also passed after the string_literal mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::3::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c6926cf32e9
- Evidence: `                if (box2[i].innerHTML == sTitle) {`
- Reason: The baseline test passed and also passed after the comparison mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::1` — bdd_traceability

- **major / WARNING**: Scenario does not exercise the multi-product summation behaviour required by the contract B-5-2.
- Evidence: `The system calculates the total price by summing the prices of all products in the cart`
- Reason: The behaviour contract B-5-2 specifically requires adding multiple products (e.g., product A and product B) and verifying that #allMoney displays the arithmetic sum. The provided scenario only adds a single product and asserts a single-item total, so it does not validate the multi-product summation or the cart listing of multiple items.
- Suggested fix: Add a complementary scenario that drags at least two distinct products into the cart (e.g., product-item-1 and product-item-2) and asserts that the element with id "allMoney" displays the correctly formatted sum (currency symbol + two decimal places) of their prices.

### `E2ESD_Bench_01::5::1` — oracle_critic

- **major / WARNING**: Drag-and-drop payload and cart contents are not strongly asserted (no DataTransfer inspection or cart item checks)
- Evidence: `Then the total price displayed in the element with id "allMoney" should be "$40.00"`
- Reason: The test simulates a drag/drop via injected JS but static analysis shows no DataTransfer creation/inspection. The only verification is the #allMoney DOM text. This means the test would not detect regressions where the drag payload is malformed or the app fails to record individual cart entries (e.g., product list and quantities), even though the displayed total might still be (accidentally) correct or incorrect in ways the test can't distinguish.
- Suggested fix: Add a concrete assertion that inspects the DataTransfer payload or instrument the application handler (spy/mock) to confirm the dragged product id/price was delivered; also assert cart DOM entries (product names/prices/quantities) after the drop to strengthen the oracle.

### `E2ESD_Bench_01::5::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mc5efa4ace1b0 survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m385c97ea419c survives this test
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::1` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a63cbe1144f survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mc5efa4ace1b0
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m385c97ea419c
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::1` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a63cbe1144f
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::2` — oracle_critic

- **major / UNKNOWN**: B-5-2-sum-multiple-products-updates-total — The cart lists both product A and product B with their prices and quantities
- Evidence: `The system calculates the total price by summing the prices of all products in the cart, formatting the total to two decimal places with the appropriate currency symbol (e.g., '$80.00'), and displays the total in the <div id="allMoney"> element.`
- Reason: Although the scenario exercises drag/drop and then checks the displayed total, there is no automated assertion in the provided step code that verifies the cart lists both products with their prices/quantities. The only assertion present targets the #allMoney DOM text. Therefore the test cannot be said to automatically observe or verify the cart contents.
- Suggested fix: Add explicit assertions that check the cart DOM after drops — for example, locate the cart entries (by data-testid or selector) and assert both product-item-1 and product-item-2 appear with expected price text and expected quantity values.

### `E2ESD_Bench_01::5::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mc5efa4ace1b0 survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m385c97ea419c survives this test
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::2` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a63cbe1144f survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mc5efa4ace1b0
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m385c97ea419c
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::2` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a63cbe1144f
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m385c97ea419c survives this test
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a63cbe1144f survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::3` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mbb6fadc93d33 survives this test
- Evidence: `            oSpan.innerHTML = sMoney;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m385c97ea419c
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a63cbe1144f
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::3` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mbb6fadc93d33
- Evidence: `            oSpan.innerHTML = sMoney;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::4` — oracle_critic

- **critical / FAIL**: The cart lists both added products with their prices and quantities (the UI shows entries for each added product).
- Evidence: `Then the total price displayed in the element with id "allMoney" should be "$240.00"`
- Reason: The behaviour contract expects the cart to list both products with their prices/quantities, but the test contains no assertions that inspect the cart contents. The only assertion present targets #allMoney text. Because there is no DOM assertion verifying product entries, prices, or quantities in the cart, the test does not observe this required behaviour and a regression affecting cart listing would not be caught.
- Suggested fix: Add explicit assertions after the drops to verify cart item elements (e.g., select cart rows/elements and assert presence of product titles, per-item price text, and quantity values) so the cart contents and per-item prices/quantities are concretely observed.

### `E2ESD_Bench_01::5::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a7468a55232 survives this test
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The test passed after the event_name mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m6c3c5fe4be37 survives this test
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-mc5efa4ace1b0 survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m385c97ea419c survives this test
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::4` — mutation_runner

- **major / FAIL**: Mutant E2ESD_Bench_01-m1a63cbe1144f survives this test
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The test passed after the dom_update mutation, so this fault was not detected.
- Suggested fix: Strengthen the observable assertion that should distinguish the original behavior from this mutant.

### `E2ESD_Bench_01::5::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a7468a55232
- Evidence: `    oDiv.ondragover = function (ev) {`
- Reason: The baseline test passed and also passed after the event_name mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m6c3c5fe4be37
- Evidence: `            oSpan.innerHTML = 1;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-mc5efa4ace1b0
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m385c97ea419c
- Evidence: `            oSpan.innerHTML = sTitle;`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

### `E2ESD_Bench_01::5::4` — dynamic_oracle

- **major / FAIL**: Dynamic oracle fails to distinguish mutant E2ESD_Bench_01-m1a63cbe1144f
- Evidence: `            oP.appendChild(oSpan);`
- Reason: The baseline test passed and also passed after the dom_update mutation; the observed oracle did not distinguish this injected fault.
- Suggested fix: Assert the exact observable state that this source mutation changes.

## Interpretation

Test quality scores: 12 available, 0 unavailable.
`N/A` means the applicable evidence threshold was not met; it is not a passing result. Basic test scores require 70% of weighted dimensions, basic requirement scores require 60%, and full scores require 50%.
Full scores use BDD, step, oracle, runtime, mutation, and robustness weights. Source grounding, optional CDP coverage, and dynamic evidence feedback remain explicit supporting evidence rather than hidden score inputs.


## Stage Cost

| Stage | Seconds |
|---|---:|
| MUTATION_RUN | 332.37 |
| BASIC_PARALLEL_REVIEWS | 146.21 |
| BASIC_SUITE_REVIEW | 68.18 |
| COVERAGE | 38.40 |
| RUN_BASELINE_TESTS | 38.16 |
| STABILITY_ANALYZE | 37.64 |
| BUILD_REQUIREMENT_CONTRACTS | 36.30 |
| STATIC_VERIFY | 0.05 |
| FULL_COORDINATE | 0.05 |
| MUTATION_GENERATE | 0.02 |
| DYNAMIC_EVIDENCE | 0.02 |
| BASIC_COORDINATE | 0.01 |
| WRITE_REPORTS | 0.01 |
| MATERIALIZE_TESTS | 0.01 |
| SOURCE_GROUNDING | 0.01 |
| MUTATION_ANALYZE | 0.01 |
| SOURCE_MODEL | 0.00 |
| RUNTIME_TRACE | 0.00 |
| DISCOVER_INPUTS | 0.00 |
| LOAD_RECORDS | 0.00 |
| CREATED | 0.00 |
| COMPLETED | 0.00 |