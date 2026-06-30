from pathlib import Path

from test_evaluator.calibration import load_golden_cases, validate_golden_cases


ROOT = Path(__file__).parents[1]


def test_basic_golden_set_is_balanced_and_static_expectations_are_current() -> None:
    cases = load_golden_cases(ROOT / "calibration" / "golden_basic_v1.json")

    errors = validate_golden_cases(cases, ROOT / "e2edev_sample.csv")

    assert errors == []
    assert len(cases) == 24
    assert {focus: sum(case.focus == focus for case in cases) for focus in {
        "bdd_traceability",
        "step_code",
        "oracle_critic",
    }} == {
        "bdd_traceability": 8,
        "step_code": 8,
        "oracle_critic": 8,
    }
