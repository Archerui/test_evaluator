# Test Evaluator Report

- Run ID: `bf022d265aa3458b81af1598e2c1faf1`
- Mode: `basic`
- Semantic agents: `live`
- Model: `gpt-5-mini`
- Tests analysed: 25
- Requirement suites analysed: 8

## Project Summary

| Project | Tests | Requirements | Basic Test Quality | Basic Requirement Adequacy | Basic Test Unknown Rate | Risks |
|---|---:|---:|---:|---:|---:|---|
| E2ESD_Bench_01 | 12 | 3 | 66.7 | 67.9 | 0% | critical: 5, major: 2, medium: 5 |
| E2ESD_Bench_02 | 13 | 5 | 53.5 | 55.7 | 0% | critical: 10, major: 2, medium: 1 |

## Test Results

| Test | Scenario | Basic Score | Basic Evidence | Risk | Hard Gates |
|---|---|---:|---:|---|---|
| E2ESD_Bench_01::1::1 | Normal | 95.0 | 100% | medium | — |
| E2ESD_Bench_01::1::2 | Edge | 35.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_01::1::3 | Edge | 20.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_01::1::4 | Error | 20.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_01::3::1 | Normal | 95.0 | 100% | medium | — |
| E2ESD_Bench_01::3::2 | Normal | 67.5 | 100% | major | — |
| E2ESD_Bench_01::3::3 | Normal | 95.0 | 100% | medium | — |
| E2ESD_Bench_01::3::4 | Edge | 80.0 | 100% | major | — |
| E2ESD_Bench_01::5::1 | Normal | 77.5 | 100% | medium | — |
| E2ESD_Bench_01::5::2 | Normal | 95.0 | 100% | medium | — |
| E2ESD_Bench_01::5::3 | Normal | 60.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_01::5::4 | Edge | 60.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::1::1 | Normal | 60.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::1::2 | Edge | 35.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::2::1 | Normal | 45.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::2::2 | Edge | 95.0 | 100% | medium | — |
| E2ESD_Bench_02::2::3 | Error | 62.5 | 100% | major | — |
| E2ESD_Bench_02::3::1 | Normal | 35.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::3::2 | Normal | 80.0 | 100% | major | — |
| E2ESD_Bench_02::3::3 | Normal | 45.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::3::4 | Edge | 35.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::4::1 | Normal | 35.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::4::2 | Edge | 60.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::5::1 | Normal | 60.0 | 100% | critical | critical_oracle_gap |
| E2ESD_Bench_02::5::2 | Edge | 47.5 | 100% | critical | critical_oracle_gap |

## Run Health

- States: succeeded: 10
- Cache hits: 0
- Cache misses: 0
- Resume used: False
- Baseline runtime: none
- Mutation outcomes: none
- Flaky tests: 0
- Baseline runtime seconds: 0.00

## Basic Evaluation Details

Dimension cells show the normalized evidence status and its score out of 100. `UNKNOWN` is excluded from scoring.

| Test | Spec alignment | Step traceability | Oracle strength | Robustness | Basic Evidence | Basic Score | Unknown dimensions |
|---|---|---|---|---|---:|---:|---|
| E2ESD_Bench_01::1::1 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::1::2 | PASS (100) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 35.0 | — |
| E2ESD_Bench_01::1::3 | WARNING (50) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 20.0 | — |
| E2ESD_Bench_01::1::4 | WARNING (50) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 20.0 | — |
| E2ESD_Bench_01::3::1 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::3::2 | WARNING (50) | WARNING (50) | PASS (100) | WARNING (50) | 100% | 67.5 | — |
| E2ESD_Bench_01::3::3 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::3::4 | WARNING (50) | PASS (100) | PASS (100) | WARNING (50) | 100% | 80.0 | — |
| E2ESD_Bench_01::5::1 | PASS (100) | PASS (100) | WARNING (50) | WARNING (50) | 100% | 77.5 | — |
| E2ESD_Bench_01::5::2 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_01::5::3 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |
| E2ESD_Bench_01::5::4 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |
| E2ESD_Bench_02::1::1 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |
| E2ESD_Bench_02::1::2 | PASS (100) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 35.0 | — |
| E2ESD_Bench_02::2::1 | WARNING (50) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 45.0 | — |
| E2ESD_Bench_02::2::2 | PASS (100) | PASS (100) | PASS (100) | WARNING (50) | 100% | 95.0 | — |
| E2ESD_Bench_02::2::3 | WARNING (50) | PASS (100) | WARNING (50) | WARNING (50) | 100% | 62.5 | — |
| E2ESD_Bench_02::3::1 | PASS (100) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 35.0 | — |
| E2ESD_Bench_02::3::2 | WARNING (50) | PASS (100) | PASS (100) | WARNING (50) | 100% | 80.0 | — |
| E2ESD_Bench_02::3::3 | WARNING (50) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 45.0 | — |
| E2ESD_Bench_02::3::4 | PASS (100) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 35.0 | — |
| E2ESD_Bench_02::4::1 | PASS (100) | FAIL (0) | FAIL (0) | WARNING (50) | 100% | 35.0 | — |
| E2ESD_Bench_02::4::2 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |
| E2ESD_Bench_02::5::1 | PASS (100) | PASS (100) | FAIL (0) | WARNING (50) | 100% | 60.0 | — |
| E2ESD_Bench_02::5::2 | PASS (100) | WARNING (50) | FAIL (0) | WARNING (50) | 100% | 47.5 | — |

## Requirement Suites

| Suite | Tests | Scenario types | Basic Adequacy | Basic Evidence | Partial input |
|---|---:|---|---:|---:|---|
| E2ESD_Bench_01::1 | 4 | Edge: 2, Error: 1, Normal: 1 | 42.5 | 100% | False |
| E2ESD_Bench_01::3 | 4 | Edge: 1, Normal: 3 | 90.0 | 100% | False |
| E2ESD_Bench_01::5 | 4 | Edge: 1, Normal: 3 | 71.2 | 100% | False |
| E2ESD_Bench_02::1 | 2 | Edge: 1, Normal: 1 | 43.3 | 100% | False |
| E2ESD_Bench_02::2 | 3 | Edge: 1, Error: 1, Normal: 1 | 75.0 | 100% | False |
| E2ESD_Bench_02::3 | 4 | Edge: 1, Normal: 3 | 67.5 | 100% | False |
| E2ESD_Bench_02::4 | 2 | Edge: 1, Normal: 1 | 47.5 | 100% | False |
| E2ESD_Bench_02::5 | 2 | Edge: 1, Normal: 1 | 45.0 | 100% | False |

## Static Behavior Coverage

Coverage is requirement-level. Data variants do not count as independent behaviors.

| Suite | Behavior | Status | Strong tests | Weak tests | All declaring tests |
|---|---|---|---|---|---|
| E2ESD_Bench_01::1 | B1_capture_on_dragstart | WARNING | — | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 |
| E2ESD_Bench_01::1 | B2_product_item_structure_and_identifiers | WARNING | — | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3, E2ESD_Bench_01::1::4 |
| E2ESD_Bench_01::3 | 3.normal_add_item_on_drop | PASS | E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal_show_product_title_in_box2 | PASS | E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal_show_unit_price_in_box3 | PASS | E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal_increment_quantity_for_repeated_products | PASS | E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2 | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::3 | 3.normal_show_multiple_different_products | PASS | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 | — | E2ESD_Bench_01::3::1, E2ESD_Bench_01::3::2, E2ESD_Bench_01::3::3, E2ESD_Bench_01::3::4 |
| E2ESD_Bench_01::5 | 5.normal.total_sum_and_display | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |
| E2ESD_Bench_01::5 | 5.normal.trailing_zero_format | FAIL | — | — | — |
| E2ESD_Bench_01::5 | 5.edge.rounding_to_two_decimals | WARNING | — | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 | E2ESD_Bench_01::5::1, E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3, E2ESD_Bench_01::5::4 |
| E2ESD_Bench_02::1 | add_note_appends_div_note | WARNING | — | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 |
| E2ESD_Bench_02::1 | note_contains_visible_empty_textarea | WARNING | — | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 |
| E2ESD_Bench_02::1 | multiple_rapid_clicks_create_separate_notes | WARNING | — | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 | E2ESD_Bench_02::1::1, E2ESD_Bench_02::1::2 |
| E2ESD_Bench_02::2 | 2.1-realtime-render | PASS | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2 | E2ESD_Bench_02::2::3 | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2, E2ESD_Bench_02::2::3 |
| E2ESD_Bench_02::2 | 2.2-inline-formatting-html | PASS | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2 | E2ESD_Bench_02::2::3 | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2, E2ESD_Bench_02::2::3 |
| E2ESD_Bench_02::2 | 2.3-handle-invalid-markdown-on-exit | PASS | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2 | E2ESD_Bench_02::2::3 | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2, E2ESD_Bench_02::2::3 |
| E2ESD_Bench_02::2 | 2.4-immediate-localstorage-persistence | WARNING | — | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2, E2ESD_Bench_02::2::3 | E2ESD_Bench_02::2::1, E2ESD_Bench_02::2::2, E2ESD_Bench_02::2::3 |
| E2ESD_Bench_02::3 | 3.1-create-enters-edit | PASS | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 | — | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 |
| E2ESD_Bench_02::3 | 3.2-toggle-to-view-shows-main | PASS | E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3 | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::4 | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 |
| E2ESD_Bench_02::3 | 3.3-toggle-to-edit-shows-textarea | PASS | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 | — | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 |
| E2ESD_Bench_02::3 | 3.4-autosave-to-localstorage | WARNING | — | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::2, E2ESD_Bench_02::3::3, E2ESD_Bench_02::3::4 |
| E2ESD_Bench_02::4 | 4.dom_removal_on_delete | WARNING | — | E2ESD_Bench_02::4::1, E2ESD_Bench_02::4::2 | E2ESD_Bench_02::4::1, E2ESD_Bench_02::4::2 |
| E2ESD_Bench_02::4 | 4.localstorage_removal_on_delete | PASS | E2ESD_Bench_02::4::1, E2ESD_Bench_02::4::2 | — | E2ESD_Bench_02::4::1, E2ESD_Bench_02::4::2 |
| E2ESD_Bench_02::5 | 5.1-retrieve-and-display | WARNING | — | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 |
| E2ESD_Bench_02::5 | 5.2-note-element-structure | WARNING | — | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 |
| E2ESD_Bench_02::5 | 5.3-non-empty-note-displays-main | PASS | E2ESD_Bench_02::5::1 | E2ESD_Bench_02::5::2 | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 |
| E2ESD_Bench_02::5 | 5.4-empty-note-shows-textarea | WARNING | — | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 |
| E2ESD_Bench_02::5 | 5.5-no-notes-when-localStorage-empty | WARNING | — | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 | E2ESD_Bench_02::5::1, E2ESD_Bench_02::5::2 |

## Suite Duplicate Analysis

| Suite | Semantic duplicate ratio | Kind | Tests | Reason |
|---|---:|---|---|---|
| E2ESD_Bench_01::1 | 50% | semantic_scenario | E2ESD_Bench_01::1::1, E2ESD_Bench_01::1::2, E2ESD_Bench_01::1::3 | The scenarios exercise the same step structure after replacing concrete values, numbers, and test-id suffixes. |
| E2ESD_Bench_01::5 | 25% | semantic_scenario | E2ESD_Bench_01::5::2, E2ESD_Bench_01::5::3 | The scenarios exercise the same step structure after replacing concrete values, numbers, and test-id suffixes. |
| E2ESD_Bench_02::3 | 25% | exact_scenario | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::4 | The scenarios have the same normalized Given/When/Then text. |
| E2ESD_Bench_02::3 | 25% | oracle_shape | E2ESD_Bench_02::3::1, E2ESD_Bench_02::3::4 | Semantically similar scenarios use the same assertion-source shape. |

## Mutation Readiness (Static Estimate)

This is a requirement/oracle-based hypothesis, not a mutation score. No application code was mutated or executed.

| Test | Mutation readiness | Prediction coverage | Likely detected | Likely survives | Unknown |
|---|---:|---:|---:|---:|---:|
| E2ESD_Bench_01::1::1 | 100.0 | 100% | 3 | 0 | 0 |
| E2ESD_Bench_01::1::2 | 0.0 | 100% | 0 | 3 | 0 |
| E2ESD_Bench_01::1::3 | 0.0 | 100% | 0 | 3 | 0 |
| E2ESD_Bench_01::1::4 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_01::3::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::3 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::3::4 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::3 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_01::5::4 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::1::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::1::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::2::1 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::2::2 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::2::3 | 100.0 | 100% | 2 | 0 | 0 |
| E2ESD_Bench_02::3::1 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_02::3::2 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_02::3::3 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_02::3::4 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_02::4::1 | 0.0 | 100% | 0 | 2 | 0 |
| E2ESD_Bench_02::4::2 | N/A | 0% | 0 | 0 | 2 |
| E2ESD_Bench_02::5::1 | N/A | 0% | 0 | 0 | 2 |
| E2ESD_Bench_02::5::2 | 0.0 | 100% | 0 | 2 | 0 |

## Major and Critical Findings

### `E2ESD_Bench_01::1::2` — step_code

- **critical / FAIL**: Then steps claiming the drag event captured title/price do not observe the browser DataTransfer payload.
- Evidence: `And the product title "JavaScript: The Definitive Guide" should be captured`
- Reason: The test's verification steps only read DOM text from the product item (title and price) rather than reading the DataTransfer payload that the app's dragstart handler is expected to populate. static_facts shows no data_transfer read or event-payload assertion. Therefore the test does not actually confirm that the drag event populated the DataTransfer with title and price.
- Suggested fix: Have the test observe the application-populated drag payload. Options: (a) Add a short-lived page listener during the test that captures event.dataTransfer contents from the dispatched dragstart and stores them (e.g., window.__lastDragData) so the test can read them via execute_script; or (b) modify the app's dragstart handler (in test builds) to copy captured values into a test-visible location (DOM attribute or window variable) and assert those values in the Then step.

### `E2ESD_Bench_01::1::2` — step_code

- **major / FAIL**: The explicit 'drag event should be initiated' check is implemented only via DOM assertions and lacks an observation that the handler ran.
- Evidence: `Then the drag event should be initiated`
- Reason: While the test dispatches a DragEvent, there is no assertion that the page's dragstart handler executed or that it populated the DataTransfer. The code's subsequent assertions only check DOM text (which can prove content presence but not that the drag event was initiated/captured by the app).
- Suggested fix: Assert a side-effect of the dragstart handler (for example, a window flag, DOM attribute, or stored object that the handler writes) or capture event.dataTransfer directly via an attached listener in the test page context and then assert the captured payload.

### `E2ESD_Bench_01::1::2` — oracle_critic

- **critical / FAIL**: B1_capture_on_dragstart: The drag event's DataTransfer must be populated with the product's title and price
- Evidence: `The drag event should capture the title and price of the product being dragged.`
- Reason: The requirement demands that the browser DataTransfer payload be populated with title and price during dragstart. The test constructs and dispatches a DragEvent with a DataTransfer object (step_code), but there are no assertions that read the DataTransfer contents (static_facts shows data_transfer_read_keys: []). Instead the test only reads DOM text for title/price. Reading DOM proves the values exist in the element but does not verify they were populated into the drag event's DataTransfer. Because the core observable (DataTransfer payload) is not asserted, the oracle cannot detect regressions where the payload is not set.
- Suggested fix: Add a concrete assertion that inspects the DataTransfer used during dragstart. Options: (a) instrument the page handler to call dataTransfer.setData('text/plain', JSON.stringify({title,price})) and assert that via execute_script after dispatch, or (b) dispatch the DragEvent from script and immediately read event.dataTransfer in an injected handler/spied function, returning the payload to the test for assertion. Ensure the test reads exact keys (e.g. getData) rather than only checking DOM.

### `E2ESD_Bench_01::1::3` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: is_drag_event_initiated(context.driver, product_item), True`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_01::1::3` — bdd_traceability

- **major / WARNING**: The requirement requires that the product title and price be made available via the browser DataTransfer during the drag (e.g., populated on dragstart), but the scenario does not assert DataTransfer population or explicitly tie the capture to dragstart.
- Evidence: `The drag event should capture the title and price of the product being dragged.`
- Reason: The behaviour contract explicitly requires the DataTransfer to be populated during the drag (observable via browser API). The scenario asserts that the drag is initiated and that title/price are captured, but it does not state that these values are placed into the DataTransfer or that capture occurs on dragstart. Static analysis also shows no creation of a DataTransfer in the test artifacts ("data_transfer_creation_count": 0), so the scenario leaves out the required observable mechanism.
- Suggested fix: Add an explicit Then that the product title and price are present in the drag event's DataTransfer (or that capture occurs on dragstart), for example: "Then the dragstart event's DataTransfer should contain key 'title' with value 'Mastering JavaScript' and key 'price' with value '$35'."

### `E2ESD_Bench_01::1::3` — step_code

- **critical / FAIL**: The When/Then steps must perform a real drag action or observe the browser DataTransfer populated during dragstart rather than relying on constant placeholders.
- Evidence: `assert is_drag_event_initiated(context.driver, product_item), "Drag event was not initiated"`
- Reason: The helper is_drag_event_initiated unconditionally returns True and the When step asserts that result. The Then step 'the drag event should be initiated' also contains a constant True assertion (placeholder). These are constant/trivial assertions (static_facts: "constant_assertion_count": 2) and do not exercise or observe a browser dragstart event or the DataTransfer API, so the core interaction required by the scenario is not implemented.
- Suggested fix: Replace the placeholder with an explicit dragstart interaction and a real observation: either synthesize a dragstart on the target element via JavaScript (creating a DataTransfer and dispatching a DragEvent) and/or install a page-side listener that records the DataTransfer contents during dragstart. Then assert that the recorded DataTransfer was populated rather than returning a constant True.

### `E2ESD_Bench_01::1::3` — oracle_critic

- **critical / FAIL**: The test must assert that the drag event's DataTransfer is populated with the product's title and price during dragstart.
- Evidence: `The drag event should capture the title and price of the product being dragged.`
- Reason: The behaviour contract requires observing the browser DataTransfer contents populated during dragstart. The test contains no creation or dispatch of a DragEvent and no reads of event.dataTransfer (static_facts shows data_transfer_creation_count = 0 and drag_event_dispatch_count = 0). Without a concrete observation of DataTransfer (a mock/spy or direct inspection after dispatch), the test cannot demonstrate that title and price were put into the drag payload. The placeholder is_drag_event_initiated() returns a constant and does not inspect DataTransfer, so it cannot serve as an oracle for the required transfer.
- Suggested fix: Construct and dispatch a synthetic dragstart event or trigger the app's dragstart handler via injected JavaScript, and then read event.dataTransfer (e.g., setData/getData or inspect dataTransfer properties) to assert the title and price keys/values. Alternatively, add a spy/mocked handler that records the dataTransfer.setData calls and assert on those recorded values.

### `E2ESD_Bench_01::1::3` — oracle_critic

- **major / FAIL**: The test's checks that a drag event was initiated are implemented as constants/placeholders rather than concrete observations of a dragstart event or its payload.
- Evidence: `return True`
- Reason: The helper is_drag_event_initiated() is a placeholder that returns a constant True (static_facts classifies it as 'constant'). This does not observe browser behavior (no DragEvent construction/dispatch or dataTransfer inspection). As a result, the test would pass even if no drag event occurred or if the handler did not populate the DataTransfer.
- Suggested fix: Implement is_drag_event_initiated to synthesize a dragstart (or attach a spy to the application's dragstart handler) and verify the handler is invoked and the dataTransfer is populated. Do not rely on constant return values.

### `E2ESD_Bench_01::1::4` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: True, True`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_01::1::4` — bdd_traceability

- **major / WARNING**: Scenario does not exercise the contract's positive behaviour: dragging an li[draggable="true"] product item and capturing its title and price.
- Evidence: `The drag event should capture the title and price of the product being dragged.`
- Reason: The supplied requirement contract requires that dragging a product item (li with draggable="true") should capture product title and price. The scenario is an error-case that targets a non-draggable element ('drop-area') and therefore does not validate the required positive capture behavior. Because this is an extra negative/edge scenario that neither contradicts nor fully covers the stated contract, a warning is appropriate to signal missing positive coverage.
- Suggested fix: Add a complementary scenario that drags a product item (an li element with draggable="true" and a data-testid like 'product-item-1') and asserts that the drag payload captures the product title and price (verify the values from 'product-title-1' and 'product-price-1').

### `E2ESD_Bench_01::1::4` — step_code

- **critical / FAIL**: Then steps that assert 'no product title should be captured' and 'no product price should be captured' must verify absence of captured drag payload or related DOM changes, not use constant placeholders.
- Evidence: `assert True, "No product title should be captured."`
- Reason: Both Then steps that are intended to verify that no product title or price was captured contain only constant assertions (always-True). They do not observe any drag data, DOM nodes, or application state that would substantiate the claimed absence of captured product information. The test therefore lacks the core verification mechanism required by the scenario.
- Suggested fix: Replace the placeholder assertions with real checks. Options: (1) execute a small script to read whatever application-side variable stores the last drag payload (e.g. window.lastDragData) and assert it is empty or undefined; (2) if the app writes captured values into DOM nodes, locate those nodes (e.g. [data-testid^='product-title-'] / product-price-) and assert they were not updated; or (3) dispatch a synthetic dragstart and then read the DataTransfer or app-visible effect that would contain title/price. Avoid leaving asserts as constants.

### `E2ESD_Bench_01::1::4` — step_code

- **major / WARNING**: Then step 'no drag event should be initiated' is implemented only via checking the element's draggable attribute (element attribute proxy) rather than observing drag event dispatch or payload.
- Evidence: `return element.get_attribute("draggable") == "true"`
- Reason: The test determines whether a drag was initiated by reading the element's draggable attribute (element.get_attribute('draggable') == 'true') and then negating that. The draggable attribute is a capability proxy and does not prove that a drag event was or wasn't dispatched or that any drag payload was established. This leaves a gap between the Gherkin step ('no drag event should be initiated') and the observable the test actually inspects.
- Suggested fix: To more directly verify that no drag event occurred, instrument the page or use execute_script to attach a temporary listener that records dragstart events (e.g. increment a counter or set window.__drag_seen=true) before attempting the user action, then assert that no event was observed. Alternatively, after attempting the action, query any application-visible artifact that would have been set by a drag handler.

### `E2ESD_Bench_01::1::4` — oracle_critic

- **critical / FAIL**: Then 'no drag event should be initiated' is automatically observed by the test code
- Evidence: `return element.get_attribute("draggable") == "true"`
- Reason: The test decides whether a drag occurred solely by reading the element's draggable attribute (element.get_attribute("draggable")). The static data_flow classifies this assertion as an element_attribute_proxy, and there are no drag event creation/dispatch or DataTransfer payload reads (drag_event_dispatch_count = 0, data_transfer_read_keys = []). An attribute value does not prove that a drag event was or was not initiated by the browser or app handlers, so this oracle cannot reliably detect the event's occurrence or its absence.
- Suggested fix: Replace the attribute check with a concrete observation of drag event behavior: dispatch or listen for a real DragEvent and/or inspect the DataTransfer object after the application's dragstart handler runs (or install a spy/mocking hook) and assert that no dragstart handler fired or that DataTransfer does not contain product data.

### `E2ESD_Bench_01::1::4` — oracle_critic

- **critical / FAIL**: Then 'no product title should be captured' and 'no product price should be captured' are automatically observed by the test code
- Evidence: `assert True, "No product title should be captured."`
- Reason: Both Then steps that claim 'no title' and 'no price' are implemented as unconditional constants (assert True). The static facts show no DataTransfer creation/reads or event payload assertions (event_payload_assertion_count = 0, data_transfer_read_keys = []). Therefore the test contains no automatic oracle that would detect whether title or price were actually captured by a drag event; the assertions cannot fail and do not validate the required behavior.
- Suggested fix: Replace the placeholder assertions with concrete checks that inspect the drag payload: trigger the drag (or listen to dragstart), read the DataTransfer keys/values that the app sets (title and price), and assert they are absent for the non-draggable element or present/absent appropriately.

### `E2ESD_Bench_01::3::2` — bdd_traceability

- **major / WARNING**: Scenario does not explicitly assert the UI mapping to .box1/.box2/.box3 as required by the behaviour contract
- Evidence: `#div1 .box1`
- Reason: The behaviour contract explicitly requires that each cart entry map title->.box2, price->.box3, quantity->.box1. The scenario verifies that titles/prices/quantities appear in the cart display but does not assert they appear in those specific selectors/classes. Because the contract explicitly names those UI anchors, the scenario is missing an assertion that the fields are rendered in .box1/.box2/.box3.
- Suggested fix: Add Then steps that assert the product title appears in the cart entry's .box2, the price in .box3, and the quantity in .box1 (e.g. "Then the cart entry for 'The Essence of JavaScript' shows its title in .box2, price in .box3, and quantity in .box1").

### `E2ESD_Bench_01::3::2` — step_code

- **major / FAIL**: Then steps that assert product prices use a Boolean expression that is effectively always true
- Evidence: `assert "$40" in prices or "$40.00", "Price '$40' not found in cart"`
- Reason: Each price assertion uses 'or' with a non-empty string literal on the right-hand side (e.g. or "$40.00"). In Python that string is truthy, so the assert will pass regardless of whether the membership check succeeds, making the price checks unable to falsify the expectation.
- Suggested fix: Change to explicit membership checks for both formats, e.g. assert ("$40" in prices) or ("$40.00" in prices), and similarly for $120.

### `E2ESD_Bench_01::3::4` — bdd_traceability

- **major / WARNING**: Scenario must assert that the unit price is specifically presented in elements matching selector .box3 as required by the behaviour contract.
- Evidence: `the product title appears in .box2, the unit price in .box3, and the quantity in .box1.`
- Reason: The behaviour contract constrains the unit price to be presented specifically in .box3. The scenario asserts the price value but does not state it must appear in selector .box3, so it omits a required location constraint from the contract.
- Suggested fix: Add or adapt a Then step to assert the unit price appears in the cart UI at selector .box3 (for example: "Then the unit price "$120" is visible in .box3").

### `E2ESD_Bench_01::5::3` — oracle_critic

- **major / WARNING**: The test must assert that the <div id="allMoney"> text equals the arithmetic sum of cart product prices formatted with the currency symbol and two decimal places (e.g. "$70.00").
- Evidence: `The system calculates the total price by summing the prices of all products in the cart`
- Reason: The test performs a direct DOM observation of the displayed total (it asserts the expected formatted string appears in the #allMoney element). This verifies the displayed text but does not verify that the displayed total was computed by summing the actual product prices in the cart: the test uses a hard-coded expected value ("$70.00") rather than reading product prices and computing the arithmetic sum to compare exactly. Using substring membership (expected_price in actual_price) also allows additional surrounding text and is weaker than an exact equality check.
- Suggested fix: Compute the expected total by reading each dropped product's price from the page, summing them, formatting to two decimals with the currency symbol, then assert exact equality with the #allMoney element text (use equality, not substring).

### `E2ESD_Bench_01::5::3` — oracle_critic

- **critical / FAIL**: The drag-and-drop action must be observed in a way that proves the application received product identity/price (DataTransfer payload) so regressions in drag payload handling are detectable.
- Evidence: `var dataTransfer = new DataTransfer();
product.dispatchEvent(new DragEvent('dragstart', {dataTransfer: dataTransfer}));
dropArea.dispatchEvent(new DragEvent('drop', {dataTransfer: dataTransfer}));`
- Reason: Although the test script synthesizes DragEvent and DataTransfer objects and dispatches them, there is no assertion that the DataTransfer payload carried product identity or price keys, nor is there any read of the DataTransfer after application handlers run. static_facts shows zero event-payload assertions and no data_transfer_read_keys. Without observing the payload (or verifying the cart DOM reflects the exact dropped product details), the test cannot detect regressions where the app fails to read/populate the drag payload.
- Suggested fix: After dispatching the synthetic drop, inspect either (a) the DataTransfer contents as handled by the app (if accessible) or (b) assert the cart DOM contains the expected dropped product entries (IDs/prices). Alternatively, add assertions that read specific DataTransfer keys or use an app-side spy to confirm the payload keys/values were consumed.

### `E2ESD_Bench_01::5::4` — oracle_critic

- **critical / FAIL**: The test must assert that <div id="allMoney"> shows the arithmetic sum of dropped product prices formatted with a currency symbol and two decimals (behavior 5.normal.total_sum_and_display).
- Evidence: `assert expected_total in actual_total, f"Expected total '{expected_total}', but got '{actual_total}'"`
- Reason: The test only performs a DOM observation and a substring containment check ("expected_total in actual_total") against the displayed text. That does not verify that the total was computed by summing the actual product prices; it merely checks that the displayed string contains the expected value. The oracle is therefore weak: it can produce false positives (e.g. incorrect internal sum that by coincidence matches the expected string, additional surrounding text, or formatting differences) and does not assert strict equality or validate numeric computation or exact formatting to two decimals and currency symbol. The test also does not compute the expected sum from the product price elements in the DOM nor verify cart contents, so the arithmetic contract is unobserved by the implementation.
- Suggested fix: Read the price values of each dropped product from the DOM, parse them to numbers, compute the arithmetic sum, format it with the currency symbol and two decimals, then assert strict equality between that computed string and the text of #allMoney. Additionally, assert the cart contains the expected products (e.g. count or testids) to ensure drops succeeded. If drag-and-drop relies on DataTransfer payloads, make the test observe the DataTransfer or verify resulting cart DOM entries rather than only dispatching events.

### `E2ESD_Bench_02::1::1` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) > 0`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::1::1` — oracle_critic

- **critical / FAIL**: A new .note element is created and appended to the document body after clicking the Add note button
- Evidence: `notes = context.driver.find_elements(By.CSS_SELECTOR, ".note")`
- Reason: The test attempts to assert that a .note exists via len(notes) > 0, but static_facts classifies that assertion as a constant rather than a concrete DOM observation. That means the implementation does not reliably prove a new .note was appended after the click (and the test does not compare before/after counts or otherwise identify the newly created element). The contract requires a new note element be created and appended; the current check is insufficient.
- Suggested fix: Make the existence check concrete: capture notes before the click, click, then re-query and assert the count increased; or locate the newly added note (e.g. container.lastElementChild) and assert it has class "note" and is attached to document.body.

### `E2ESD_Bench_02::1::1` — oracle_critic

- **critical / FAIL**: The textarea is visible to the user
- Evidence: `assert textarea.is_displayed(), "The textarea is not visible"`
- Reason: static_facts marks the visibility check as an element_attribute_proxy rather than a stronger DOM observation. An attribute/proxy check like is_displayed() can be insufficient to guarantee user-visible rendering in some failure modes (e.g., zero-size, clipped, transparent, off-screen). The contract requires the textarea to be visible to the user; this test's oracle is weak for that core observable and therefore does not reliably prevent regressions.
- Suggested fix: Strengthen visibility assertions: scope to the newly created note, then assert computed style visibility/opacity, and check boundingClientRect dimensions are non-zero and within the viewport (or use explicit CSS visibility/opacity checks) in addition to is_displayed().

### `E2ESD_Bench_02::1::2` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) > 1`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::1::2` — step_code

- **critical / FAIL**: Assertion that 'multiple new notes are displayed' is implemented as an observable increase caused by the rapid clicks
- Evidence: `notes = context.driver.find_elements(By.CSS_SELECTOR, "[data-testid='note-textarea']")
assert len(notes) > 1, f"Expected multiple notes, but found {len(notes)}"`
- Reason: The scenario's core Then step promises that multiple new notes are displayed as a result of rapid clicks. The implementation asserts only that the current number of elements matching the note-textarea selector is > 1, but does not record the pre-click count or otherwise verify that the rapid clicks caused the increase. The static analysis classifies this assertion as a 'constant' source, indicating the test does not establish a before/after or causation. According to the review rules, a missing or constant implementation of a core When/Then is a critical failure because it does not implement the scenario mechanism.
- Suggested fix: Capture the initial count of note textareas before performing the rapid clicks (e.g. initial = len(find_elements(...))), then after the clicks assert new_count >= initial + expected_new_notes (or new_count > initial). This proves the clicks produced additional notes rather than relying on a pre-existing condition.

### `E2ESD_Bench_02::1::2` — oracle_critic

- **critical / FAIL**: Multiple new notes are asserted to exist after rapid clicks
- Evidence: `assert len(notes) > 1, f"Expected multiple notes, but found {len(notes)}"`
- Reason: The test's assertion that multiple notes exist is classified as coming from a 'constant' source in the static data flow. A constant-style assertion does not prove the test actually observed DOM changes caused by the UI interaction and would not reliably detect regressions where notes are not appended.
- Suggested fix: Query and count the actual note container elements (e.g., div.note) before and after the rapid clicks, and wait/assert that the count increases. Avoid relying on an assertion that the analyzer classifies as a constant.

### `E2ESD_Bench_02::2::1` — bdd_traceability

- **major / WARNING**: Missing coverage for the edge contract: invalid/unmatched Markdown should display raw input on exit without crashing.
- Evidence: `invalid Markdown (e.g., unmatched **) does not cause crashes or errors, and instead displays the raw input when the user exits the edit mode by clicking the "Edit" button (data-testid="edit-note-button").`
- Reason: The provided behaviour contract requires an explicit edge-case: when the textarea contains invalid/unmatched Markdown (e.g., unmatched **), exiting edit mode must show the raw input and not crash. The current scenario only exercises a valid Markdown input ("# Heading") and its rendered HTML outcome; it does not exercise or claim the invalid-markdown-on-exit behaviour, so the contract is not covered by this scenario.
- Suggested fix: Add a separate scenario for the invalid-markdown edge case. Example: Given a note in edit mode; When the user enters "unmatched **bold" into data-testid "note-textarea" and clicks the "Edit" button (data-testid "edit-note-button"); Then the main display area (data-testid "note-main") should display the raw text "unmatched **bold" and the app remains responsive (no crash).

### `E2ESD_Bench_02::2::1` — oracle_critic

- **critical / FAIL**: Behavior 2.3 - When exiting edit mode with invalid/unmatched Markdown (e.g., unmatched **), the main display (data-testid="note-main") must show the raw input verbatim and the app must remain responsive (no crash or unhandled error visible).
- Evidence: `invalid Markdown (e.g., unmatched **) does not cause crashes or errors, and instead displays the raw input when the user exits the edit mode by clicking the "Edit" button (data-testid="edit-note-button").`
- Reason: The provided test code only inputs valid Markdown (# Heading) and asserts the rendered <h1> text via a DOM observation. There is no scenario or assertion that inputs invalid/unmatched Markdown (e.g., unmatched **) nor any check that the note-main contains the raw verbatim textarea value on exiting edit mode. There is also no assertion that verifies the app remains responsive or that no unhandled error UI is shown. Because the required observables for this edge behavior (verbatim DOM content for invalid input and absence of visible crash/error) are not asserted, the oracle is insufficient to catch regressions for this behavior.
- Suggested fix: Add an explicit scenario that inputs an invalid Markdown string (e.g., "unmatched **" or "**bold") into [data-testid='note-textarea'], clicks the edit button, then assert that [data-testid='note-main'] displays the exact raw text (e.g., compare note-main.textContent or innerText to the original textarea value). Also assert the absence of error UI after exit (e.g., no visible error banner) and/or capture console logs or an error element to ensure no unhandled exception was surfaced to the user.

### `E2ESD_Bench_02::2::3` — bdd_traceability

- **major / WARNING**: Scenario does not assert the required constraint that the app remains responsive / shows no crash or unhandled error when exiting edit mode with invalid Markdown.
- Evidence: `invalid Markdown (e.g., unmatched **) does not cause crashes or errors, and instead displays the raw input when the user exits the edit mode by clicking the "Edit" button (data-testid="edit-note-button").`
- Reason: The behaviour contract explicitly requires that invalid Markdown must not cause crashes or unhandled errors and that the app remains responsive as a user-observable outcome. The scenario asserts only that the main display shows the raw text; it does not include any step or assertion that verifies the app did not crash or that no unhandled error is visible to the user.
- Suggested fix: Add an explicit Then step that verifies the app remains responsive or that no error/crash indicator is visible after exiting edit mode (for example: check that the page is still interactive, no error banner/text is present, or a visible 'edit' control remains enabled).

### `E2ESD_Bench_02::2::3` — oracle_critic

- **major / WARNING**: App remains responsive (no crash or unhandled error visible) when exiting edit mode with invalid Markdown
- Evidence: `main_display_area = WebDriverWait(context.driver, 10).until( EC.visibility_of_element_located((By.CSS_SELECTOR, "[data-testid='note-main']")) )`
- Reason: The scenario requirement includes a resilience observable (no crash/unhandled error). The test does not explicitly assert absence of errors or check for crash indicators (e.g., no console errors, no visible error message, or that application code did not throw). The only related runtime check is locating the main display element (WebDriverWait for visibility) and reading its text; this is an indirect/partial constraint — it will detect a complete failure to render the element but does not prove there were no unhandled errors or that the app remained responsive in all ways. Therefore the oracle for "no crash/unhandled error visible" is partial, not strong.
- Suggested fix: Add explicit assertions for absence of error UI or console errors after exiting edit mode (for example, check for no visible error banner and inspect browser console logs for uncaught exceptions), or assert application-specific healthy state indicators immediately after clicking the Edit button.

### `E2ESD_Bench_02::3::1` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) > 0`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::3::1` — step_code

- **critical / FAIL**: The 'Then a new note should be created' step uses a constant-style assertion (len(notes) > 0) and is classified as 'constant' in static_facts, so it does not reliably prove that clicking the Add button created a new note.
- Evidence: `assert len(notes) > 0, "No new note was created"`
- Reason: The implementation checks notes = context.driver.find_elements(By.CSS_SELECTOR, ".note") and asserts len(notes) > 0. static_facts marks this assertion as 'constant', indicating the test does not observe a change attributable to the When action (for example, it doesn't compare before/after counts or wait for a newly-created note). Per the review rules, a core Then step with a constant implementation is a critical failure because it doesn't implement the scenario's observable.
- Suggested fix: Capture the note count (or marker) before clicking, then after clicking wait for the count to increase or for a specifically-created note element (e.g., by an id, newest-item selector, or presence of an 'editing' class). Use WebDriverWait to assert the new element appears rather than asserting len(notes) > 0 as a standalone constant check.

### `E2ESD_Bench_02::3::1` — step_code

- **major / WARNING**: The main content area hidden check is implemented as an element attribute proxy without an explicit wait, which may be flaky and cannot prove the transition timing requirement.
- Evidence: `main_content = context.driver.find_element(By.CSS_SELECTOR, "[data-testid='note-main']")
    assert not main_content.is_displayed(), "Main content area is not hidden"`
- Reason: The test directly finds the main content element and checks .is_displayed() without waiting. static_facts classifies this as an element-attribute-proxy assertion: it can detect whether the DOM reports the element as hidden but does not guard against timing/race conditions (the Gherkin requires the transition to edit mode occur immediately upon creation).
- Suggested fix: Use an explicit wait for invisibility, e.g. WebDriverWait(..., EC.invisibility_of_element_located((By.CSS_SELECTOR, "[data-testid='note-main']"))) or wait for a specific 'editing' state on the newly-created note to make the timing requirement explicit.

### `E2ESD_Bench_02::3::1` — oracle_critic

- **critical / FAIL**: New note creation is asserted by the test (Then: a new note should be created).
- Evidence: `assert len(notes) > 0, "No new note was created"`
- Reason: The test's assertion that 'len(notes) > 0' is classified as a constant-based check by the static analysis. A constant-style assertion does not reliably prove the application created a note as a result of the user action (it does not tie the observed change to the triggered behavior or guard against false positives).
- Suggested fix: Replace the constant-style existence check with a DOM-stable assertion that ties the new note to the action, e.g. locate a newly inserted .note element that has an edit-mode marker (class or data attribute) added after the click, or assert an increase in a note list length calculated before and after the click within the test.

### `E2ESD_Bench_02::3::1` — oracle_critic

- **critical / FAIL**: Textarea visibility after creation (Then: note's textarea should be visible).
- Evidence: `assert textarea.is_displayed(), "Textarea is not visible"`
- Reason: The test only reads the textarea's DOM display attribute (element.is_displayed()), which the static analysis classifies as an element_attribute_proxy. This is a weak oracle for the required behavior because it only observes a DOM attribute and does not prove the application performed the correct immediate transition to edit mode (race conditions, timing, or incorrect element reuse could mask regressions).
- Suggested fix: Make the assertion stronger and tied to the creation event: assert that the specific newly created note contains the visible textarea (e.g. locate the textarea within the note element returned immediately after click), or assert a deterministic edit-mode marker (class/data attribute) set on the note at creation time. Consider asserting both visibility and the presence of an 'editing' state attribute.

### `E2ESD_Bench_02::3::1` — oracle_critic

- **critical / FAIL**: Main content area is hidden after creation (Then: note's note-main should be hidden).
- Evidence: `assert not main_content.is_displayed(), "Main content area is not hidden"`
- Reason: As with the textarea visibility, the test only inspects the DOM display attribute of note-main (element_attribute_proxy). This is a weak oracle for the required immediate transition to edit mode: it does not ensure the hide/show behavior is a direct result of the creation action or that the correct note instance was asserted.
- Suggested fix: Assert the hidden state on the specific newly-created note element (e.g. find the note created by the click and check its .note-main child is hidden). Additionally, assert any explicit "editing" state attribute or class on the note to ensure the UI transitioned to edit mode deterministically.

### `E2ESD_Bench_02::3::2` — bdd_traceability

- **major / WARNING**: The behaviour contract '3.1-create-enters-edit' (click Add note -> immediately enter edit mode) is not exercised by this scenario
- Evidence: `Upon creation, the note should immediately enter edit mode: the textarea (data-testid="note-textarea") is visible for user input, while the main content area (data-testid="note-main") remains hidden.`
- Reason: The requirement contract explicitly requires that clicking the Add note button causes the new note to immediately enter edit mode. The scenario instead uses a Given that a note already exists ('a note is created with text "Sample Note"') and does not perform the user action of clicking the Add note button, so it does not verify the creation -> immediate edit-mode transition.
- Suggested fix: Add a Normal scenario that performs the user action: 'When the user clicks the "Add note" button with data-testid "add-note-button"' and then asserts the textarea (data-testid="note-textarea") is visible and the main content area (data-testid="note-main") is hidden immediately after creation.

### `E2ESD_Bench_02::3::3` — bdd_traceability

- **major / WARNING**: Behavior contract '3.1-create-enters-edit' requires clicking the Add note button to create a note that immediately enters edit mode.
- Evidence: `Upon creation, the note should immediately enter edit mode: the textarea (data-testid="note-textarea") is visible for user input, while the main content area (data-testid="note-main") remains hidden.`
- Reason: The contract's actor action is an explicit click of the Add note button (data-testid="add-note-button") and requires the transition to edit mode to occur immediately upon creation. The scenario instead uses a precondition that 'a note is created' and exercises the Edit button toggle; it does not perform or assert the Add note click nor the immediate transition on creation, so it does not validate this contract.
- Suggested fix: Add a step that explicitly clicks the Add note button (e.g. "When the user clicks the \"Add note\" button with data-testid \"add-note-button\"") and then assert the textarea is visible and note-main is hidden immediately after creation.

### `E2ESD_Bench_02::3::3` — oracle_critic

- **critical / FAIL**: Behaviour 3.1-create-enters-edit — The textarea (data-testid="note-textarea") should be visible immediately upon note creation
- Evidence: `Upon creation, the note should immediately enter edit mode: the textarea (data-testid="note-textarea") is visible for user input, while the main content area (data-testid="note-main") remains hidden.`
- Reason: The test's check for the textarea uses textarea.is_displayed(), which static_facts classifies as an element_attribute_proxy (a DOM attribute observation). That assertion only inspects the element's visible state in the DOM and does not prove the application has entered the required 'edit mode' state (for example, an internal edit-mode flag or persistence behavior). Because the core observable (entering edit mode immediately) is only validated via a DOM attribute proxy, regressions that break the actual edit-mode semantics could still pass the test.
- Suggested fix: Strengthen the oracle: assert a concrete application state change in addition to DOM visibility (for example, check a dedicated edit-mode attribute/class on the note element, or verify the note's persisted state in localStorage immediately after creation). If the app exposes an internal flag or data-* attribute when edit mode is active, assert its exact value rather than relying solely on is_displayed().

### `E2ESD_Bench_02::3::3` — oracle_critic

- **critical / FAIL**: Behaviour 3.1-create-enters-edit — The main content area (data-testid="note-main") should be hidden immediately upon note creation
- Evidence: `Upon creation, the note should immediately enter edit mode: the textarea (data-testid="note-textarea") is visible for user input, while the main content area (data-testid="note-main") remains hidden.`
- Reason: The test asserts the main content is hidden by checking main_content.is_displayed() and negating it; static_facts marks this as an element_attribute_proxy. This only verifies DOM visibility, not that the application correctly switched to edit mode at the state or persistence level. Thus the observable required by the behaviour contract is not strongly asserted and a UI-only or timing regression could let broken behaviour slip through.
- Suggested fix: Make the negative assertion stronger: check for an explicit edit-mode indicator (class, attribute, or JS-exposed property) or validate that the non-edit representation is removed/empty in the DOM and that the note's edit state is reflected in persisted storage (e.g., localStorage) immediately after creation.

### `E2ESD_Bench_02::3::4` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) > 0`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::3::4` — step_code

- **critical / FAIL**: Implementation verifies 'a new note should be created' by asserting that len(notes) > 0, but the test does not detect creation relative to prior state (constant-style assertion).
- Evidence: `Then a new note should be created`
- Reason: The Gherkin requires a newly created note; the step implementation only asserts that at least one element with class ".note" exists (a constant-style check). This does not prove a note was created by the click action (no before/after comparison, no selection of the newly created element, and static_facts classifies this assertion as constant). According to the review rules, a core Then implemented only with a constant assertion is a critical failure.
- Suggested fix: Record the count of notes before clicking and assert the count increases after the click, or locate the newly created note (e.g. the last .note element or an element with a creation/edit-mode marker) and assert its presence. Alternatively, assert a specific creation indicator (timestamp, data attribute, or newly-added element under a parent) rather than only len(notes) > 0.

### `E2ESD_Bench_02::3::4` — oracle_critic

- **critical / FAIL**: The test's visibility checks for edit mode rely only on element display attributes and do not strongly observe an edit-mode transition.
- Evidence: `assert textarea.is_displayed()`
- Reason: Both visibility assertions are classified as element_attribute_proxy in the static data flow. Reading is_displayed() only inspects DOM presentation and does not prove that the application performed the intended 'enter edit mode' transition (handlers, state flags, or focus). A visual/display property could be set or faked without the app-side edit-mode behavior occurring, so this oracle is weak and would allow regressions to pass.
- Suggested fix: Use stronger, application-level observables: (a) assert a deterministic state change (e.g. note element has data-mode or CSS class like 'editing'), (b) check document.activeElement === textarea to verify focus, or (c) expose and assert application state or a localStorage entry indicating the note is in edit mode immediately after creation.

### `E2ESD_Bench_02::3::4` — oracle_critic

- **critical / FAIL**: The test's check that a new note was created is a weak/constant-style assertion and doesn't robustly verify the creation event.
- Evidence: `assert len(notes) > 0`
- Reason: The only creation check is `len(notes) > 0`, classified as a constant-style assertion. This does not verify that the click produced a new note (could pass if notes existed beforehand) nor that the new element is the one entering edit mode. Without a before/after comparison or an assertion tied to the specific new element returned by the add action, the creation observable is under-specified and allows false positives.
- Suggested fix: Record the note count before clicking and assert count increased by one, or capture the element returned/created by the action (for example, query for a newly inserted .note element or an element with a generated id) and assert its state (editing class, textarea visibility, or localStorage entry) immediately after creation.

### `E2ESD_Bench_02::4::1` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) == 0, 'Sample Note' not in notes`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::4::1` — step_code

- **critical / FAIL**: The scenario's Then steps that verify the note was removed from the page and from localStorage are implemented as constant/unreliable assertions and do not provide plausible observable verification of the required behavior.
- Evidence: `assert len(notes) == 0, "Expected no notes on the page"`
- Reason: Both Then assertions are flagged as constant by the static facts and the code does a simple membership/length check without robust parsing or checks tied to the created item's identity. The page-removal assertion asserts len(notes) == 0 (a constant expectation) rather than verifying that the specific note "Sample Note" is absent. The localStorage assertion reads localStorage.getItem('notes') but performs a substring check against the raw returned value; static analysis marks these as constant assertions, indicating they do not reliably observe the contract that the note's stored entry was removed as a consequence of the same delete click.
- Suggested fix: Parse the stored notes (e.g. JSON.parse returned value) and assert that no stored object has text === 'Sample Note'. For page removal, locate the specific note element by its text/content or data-testid and assert it is absent rather than asserting the list length is zero.

### `E2ESD_Bench_02::4::1` — step_code

- **major / FAIL**: The Given step that creates the note does not clearly ensure the note is persisted to localStorage before the delete action, so the precondition required by the contract is not established.
- Evidence: `textarea.send_keys("Sample Note")`
- Reason: The creation step clicks an add button and sends keys into a textarea but does not perform an explicit save/confirm action or verify that localStorage contains the new note before proceeding to deletion. The behaviour contract requires that the note exists as an entry in the application's stored notes array in localStorage before deletion; the current implementation does not establish or assert that persistence.
- Suggested fix: After entering text, perform the UI action that finalizes creation (click Save/Add if required) and then assert persistence: execute_script to return localStorage.getItem('notes') and parse it to confirm an entry for 'Sample Note' exists before proceeding to click delete.

### `E2ESD_Bench_02::4::1` — oracle_critic

- **critical / FAIL**: 4.localstorage_removal_on_delete — localStorage entry removed as consequence of clicking delete
- Evidence: `notes = context.driver.execute_script("return localStorage.getItem('notes');")`
- Reason: The test does call execute_script to read localStorage (evidence: "return localStorage.getItem('notes');") and then asserts the string absence. However, the static analysis classifies the related assertions as constant ("constant_assertion_count": 2) and the assertion is a simple containment check of a literal string. As written the check does not robustly assert the exact stored structure (for example parsing JSON and checking array membership) nor does it prove the removal was caused by the same click action (no before/after comparison or observation of the storage mutation call). Per the oracle rules, a constant string containment check without a precise parsed assertion or a mutation/spied call is a weak oracle and leaves the regression undetected in some failure modes.
- Suggested fix: Read and parse the notes JSON from localStorage (e.g. execute_script("return JSON.parse(localStorage.getItem('notes'))")) and assert the parsed array does not contain an entry with text exactly equal to "Sample Note". Prefer an explicit before/after assertion (capture stored array before clicking delete, click, then re-read and assert the specific entry was removed) or spy/mock the storage write (setItem) to verify the deletion persisted as a direct consequence of the click.

### `E2ESD_Bench_02::4::1` — oracle_critic

- **critical / FAIL**: 4.localstorage_removal_on_delete — note removed from DOM after clicking delete
- Evidence: `notes = context.driver.find_elements(By.CSS_SELECTOR, ".note")`
- Reason: The test asserts the page contains zero elements matching ".note" after clicking delete, but the static facts mark no DOM-backed assertions ("dom_assertion_count": 0) and the assertion used is a plain length equality against a constant. The code does not assert that the specific created note with text "Sample Note" is gone (it only checks count==0), nor does it use a robust wait-for-absence (e.g. WebDriverWait until staleness or until element with that text is absent). Because the oracle is only a raw element-count equality and is classified as a constant-style assertion, it is insufficiently strong to guarantee the intended UI effect across race conditions or partial removals.
- Suggested fix: Assert the absence of the specific note node containing the exact text (e.g. locate an element by its text and wait for staleness) and/or use WebDriverWait to explicitly wait until the element containing "Sample Note" is not present. Prefer checking that the particular note element is removed (staleness_of) instead of relying only on len(notes) == 0.

### `E2ESD_Bench_02::4::2` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: 'Note 1' in local_storage_notes, 'Note 3' in local_storage_notes, 'Note 2' not in local_storage_notes`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::4::2` — oracle_critic

- **critical / FAIL**: The test must verify the deleted note's entry is removed from localStorage as a consequence of the same delete click action.
- Evidence: `the corresponding entry must also be removed from localStorage`
- Reason: Although the test calls execute_script to read localStorage, the static analysis classifies the subsequent membership assertions against local_storage_notes as 'constant' (not a concrete observable). Per the oracle-strength rules, a 'constant' classification is not a reliable oracle for verifying that the delete click caused removal from localStorage. There is no concrete observable (e.g., a precise array equality check on the returned storage value, a spy/mock of localStorage.setItem/removeItem, or other strong evidence) that ties the deletion click to removal in storage. Therefore the persistence contract (removal from localStorage) is not strongly asserted and could be a false positive.
- Suggested fix: Replace the weak/constant-style checks with a strong, concrete assertion and/or instrumentation: (1) assert exact returned stored notes array equality after delete, e.g. assert local_storage_notes == ['Note 1', 'Note 3'] (returned via execute_script), or assert JSON.stringify(local_storage_notes) equals expected string; and/or (2) instrument or spy localStorage APIs in the page (wrap/spy localStorage.setItem/removeItem) and assert the spy was called with the expected updated notes array immediately after the delete click. Ensure the read/assert happens immediately after the click so the removal is observed as a consequence of that same action.

### `E2ESD_Bench_02::5::1` — oracle_critic

- **major / WARNING**: Application creates one rendered note element per stored entry (count equality)
- Evidence: `note_elements = context.driver.find_elements(By.CSS_SELECTOR, "[data-testid='note-main']")`
- Reason: The test verifies that the texts for both notes appear in elements with data-testid='note-main', but it does not assert that the number of rendered note elements equals the number of stored entries (no assertion checking len(note_elements) == 2). This leaves open regressions where extra or missing DOM nodes could still satisfy the text-presence checks.
- Suggested fix: Add an assertion that the count of rendered note containers equals the length of the stored notes array (e.g. assert len(note_elements) == expected_count).

### `E2ESD_Bench_02::5::1` — oracle_critic

- **major / UNKNOWN**: Notes retrieved from localStorage result from parsing localStorage via JSON.parse(localStorage.getItem('notes')) and populating internal notes variable
- Evidence: `Internally, the notes variable is used to store the array of note content, retrieved using JSON.parse(localStorage.getItem('notes')).`
- Reason: The requirement specifies an internal read/parse of localStorage into a notes variable, but the test only injects localStorage and observes DOM output. There is no instrumentation, spy, or direct inspection proving the application called localStorage.getItem or used JSON.parse to populate an internal notes variable. DOM observation alone does not prove the internal retrieval/parsing mechanism.
- Suggested fix: Instrument the app or add a spy/mocked wrapper around localStorage.getItem/JSON.parse, or expose the internal notes variable (for test hooks) so the test can assert that JSON.parse(localStorage.getItem('notes')) was invoked and its result assigned.

### `E2ESD_Bench_02::5::1` — oracle_critic

- **critical / FAIL**: Textarea visibility rules: for populated notes the textarea (data-testid='note-textarea') is hidden by default; for empty notes the textarea is shown and main is hidden
- Evidence: `Each note must also include a div with the class main (data-testid="note-main") to show the note content, and a textarea (data-testid="note-textarea") for editing. Notes retrieved from localStorage should be rendered with their content displayed in the main div, with the textarea hidden by default.`
- Reason: The scenario only asserts that note-main contains the expected text; it does not check for the presence or visibility state of data-testid='note-textarea'. Because the required visibility behavior (textarea hidden for non-empty notes, shown for empty notes) is not observed by the test, regressions (e.g. textareas accidentally visible for populated notes or main div left hidden) would not be detected. This is a core UI observable from the requirement and is currently unverified by the automated steps.
- Suggested fix: Add assertions that verify presence and visibility state of [data-testid='note-textarea'] and [data-testid='note-main'] for each rendered note (for example, check element.is_displayed() or CSS classes), and include a case for empty-note content to assert textarea is shown while main is hidden.

### `E2ESD_Bench_02::5::2` — static_verifier

- **major / WARNING**: Assertions avoid constant placeholders
- Evidence: `Constant-derived assertions: len(notes) == 0`
- Reason: A constant assertion cannot detect a behavioral regression.
- Suggested fix: Replace constant assertions with checks of the requirement's expected observable.

### `E2ESD_Bench_02::5::2` — step_code

- **major / FAIL**: The 'Given the localStorage is empty' precondition must be established before the page is loaded so the app reads an empty storage on open.
- Evidence: `Given the localStorage is empty`
- Reason: The test opens the page (context.driver.get(...)) and then clears localStorage via execute_script. The Gherkin intent is that the page is opened while localStorage is empty. Because the implementation clears storage after the initial get(), the application may already have read and rendered notes during its initial load, so the test does not reliably establish the required precondition. This ordering mismatch prevents the test from observing the promised behavior.
- Suggested fix: Clear localStorage before loading the page or reload the page after clearing. For example, call execute_script("window.localStorage.clear();") before context.driver.get(...) or call context.driver.refresh() after clearing so the app loads with empty storage.

### `E2ESD_Bench_02::5::2` — oracle_critic

- **critical / FAIL**: 5.5-no-notes-when-localStorage-empty — test must detect that no .note elements are present when localStorage is empty
- Evidence: `If localStorage is empty, no notes should be shown.`
- Reason: The behaviour contract requires asserting that no elements with the .note class are present in the DOM. The test instead queries only elements with data-testid 'note-main' and asserts their count is zero ("notes = ... [data-testid='note-main']" and "assert len(notes) == 0..."). Static facts classify the assertion as coming from a constant rather than a concrete DOM-observed oracle ("classification": "constant"). Because the test does not check for .note elements, it can miss placeholder .note containers that lack a note-main child (so a regression that renders empty .note elements would still pass). The assertion therefore is not a strong DOM oracle for the required observable and cannot reliably detect the specified regression.
- Suggested fix: Change the assertion to directly inspect the DOM for the required UI anchor. For example, find elements by the .note selector (By.CSS_SELECTOR, ".note") and assert their length is 0. Alternatively, assert both that no '.note' elements exist and that no '[data-testid="note-main"]' elements exist. Ensure the assertion is based on the runtime DOM read (find_elements) rather than a constant classification and remove reliance on unrelated selectors.

## Interpretation

Test quality scores: 25 available, 0 unavailable.
`N/A` means the applicable evidence threshold was not met; it is not a passing result. Basic test scores require 70% of weighted dimensions, basic requirement scores require 60%, and full scores require 50%.


## Stage Cost

| Stage | Seconds |
|---|---:|
| BASIC_PARALLEL_REVIEWS | 1162.97 |
| BASIC_SUITE_REVIEW | 405.14 |
| BUILD_REQUIREMENT_CONTRACTS | 304.87 |
| STATIC_VERIFY | 0.09 |
| BASIC_COORDINATE | 0.02 |
| LOAD_RECORDS | 0.01 |
| WRITE_REPORTS | 0.01 |
| DISCOVER_INPUTS | 0.00 |
| CREATED | 0.00 |
| COMPLETED | 0.00 |