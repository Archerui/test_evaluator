from pathlib import Path

from test_evaluator.grounding import ground_selectors
from test_evaluator.schemas import (
    ProjectInventory,
    RequirementContract,
    SelectorGroundingInput,
    SourceModelInput,
    TestRecord as Record,
)
from test_evaluator.source_model import build_source_model
from test_evaluator.static_verifier import extract_static_facts


def _source_fixture(tmp_path: Path):
    source = tmp_path / "source"
    source.mkdir()
    (source / "index.html").write_text(
        """<!doctype html>
<html><body>
<button id="save" data-testid="save-button">Save</button>
<script src="script.js"></script>
<script>
const save = document.getElementById('save');
save.onclick = function () {
  const status = document.createElement('div');
  status.id = 'status';
  status.textContent = 'Saved';
  document.body.appendChild(status);
};
</script>
</body></html>
""",
        encoding="utf-8",
    )
    (source / "script.js").write_text(
        "localStorage.setItem('ready', 'yes');\nfetch('/api/items');\n",
        encoding="utf-8",
    )
    inventory = ProjectInventory(
        project_id="Bench_Source",
        source_root=str(source),
        entry_html="index.html",
        source_files=["index.html", "script.js"],
    )
    output = build_source_model(SourceModelInput(run_id="run", inventory=inventory))
    return source, inventory, output


def _record(selector: str) -> Record:
    return Record(
        project_id="Bench_Source",
        requirement_id="1",
        test_id="1",
        requirement='The save control uses data-testid="save-button".',
        scenario=(
            "Feature: Save\n  Scenario: [Normal] Save\n"
            "    When the user saves\n"
            "    Then the status is visible"
        ),
        step_code=(
            "from behave import when, then\n"
            "from selenium.webdriver.common.by import By\n"
            "@when('the user saves')\n"
            "def save(context):\n"
            "    context.driver.find_element(By.CSS_SELECTOR, '[data-testid=\"save-button\"]').click()\n"
            "@then('the status is visible')\n"
            "def status(context):\n"
            f"    assert context.driver.find_element(By.ID, '{selector}').is_displayed()\n"
        ),
    )


def test_source_model_extracts_static_and_dynamic_behavior(tmp_path: Path) -> None:
    _, _, output = _source_fixture(tmp_path)
    model = output.source_model

    selectors = {anchor.selector for anchor in model.dom_anchors}
    assert '[data-testid="save-button"]' in selectors
    assert "#save" in selectors
    assert "#status" in selectors
    assert any(handler.event == "click" and handler.selector == "#save" for handler in model.event_handlers)
    assert any(effect.kind == "storage_write" for effect in model.state_effects)
    assert any(effect.kind == "api_call" and effect.target == "/api/items" for effect in model.state_effects)
    assert "/api/items" in model.external_apis
    assert output.status.value == "PASS"


def test_grounding_matches_dynamic_id_and_reports_missing_literal(tmp_path: Path) -> None:
    _, _, source_output = _source_fixture(tmp_path)
    record = _record("status")
    contract = RequirementContract(
        project_id=record.project_id,
        requirement_id=record.requirement_id,
        behaviors=[],
    )
    grounded = ground_selectors(
        SelectorGroundingInput(
            run_id="run",
            record=record,
            contract=contract,
            static_facts=extract_static_facts(record),
            source_model=source_output.source_model,
        )
    )
    assert grounded.status.value == "PASS"
    assert all(item.source_exists for item in grounded.selectors)
    assert {item.purpose for item in grounded.selectors} == {"action_target", "oracle_target"}

    missing_record = _record("does-not-exist")
    missing = ground_selectors(
        SelectorGroundingInput(
            run_id="run",
            record=missing_record,
            contract=contract,
            static_facts=extract_static_facts(missing_record),
            source_model=source_output.source_model,
        )
    )
    assert missing.status.value == "FAIL"
    assert any(item.selector == "#does-not-exist" and not item.source_exists for item in missing.selectors)
    assert missing.findings[0].evidence[0].line_start is not None
