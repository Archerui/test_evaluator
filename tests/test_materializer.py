from pathlib import Path

from test_evaluator.materializer import materialize_test
from test_evaluator.schemas import (
    ProjectInventory,
    TestMaterializerInput as MaterializerInput,
    TestRecord as Record,
)


def _record(source_root: Path) -> Record:
    return Record(
        project_id="Bench_Unit",
        requirement_id="1",
        test_id="1",
        requirement="Open the page",
        scenario=(
            "Feature: Open page\n\n"
            "  Scenario: [Normal] Open the entry page\n"
            "    Given the page is open\n"
            "    Then it should be visible"
        ),
        step_code=(
            "from behave import given, then\n"
            "from selenium import webdriver\n"
            "file_path = \"index.html\"\n"
            "@given('the page is open')\n"
            "def open_page(context):\n"
            "    context.driver = webdriver.Chrome()\n"
            "    context.driver.get(f\"file://index.html\")\n"
            "@then('it should be visible')\n"
            "def visible(context):\n"
            "    assert context.driver.title == 'Unit'\n"
        ),
        source_root=str(source_root),
    )


def test_materializer_copies_source_and_rewrites_paths(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    original = "<html><title>Unit</title></html>"
    (source / "index.html").write_text(original, encoding="utf-8")
    inventory = ProjectInventory(
        project_id="Bench_Unit",
        source_root=str(source),
        entry_html="index.html",
        source_files=["index.html"],
    )

    output = materialize_test(
        MaterializerInput(
            run_id="run-unit",
            inventory=inventory,
            record=_record(source),
            output_dir=str(tmp_path / "workspaces"),
        )
    )

    workspace = output.workspace
    entry = Path(workspace.entry_html)
    steps = Path(workspace.steps_file).read_text(encoding="utf-8")
    assert entry.read_text(encoding="utf-8") == original
    assert entry.as_uri() in steps
    assert f'file_path = "{entry}"' in steps
    assert Path(workspace.feature_file).is_file()
    assert (Path(workspace.workspace_root) / "features" / "environment.py").is_file()
    assert Path(workspace.workspace_root).is_relative_to(tmp_path / "workspaces")
    assert (source / "index.html").read_text(encoding="utf-8") == original
    assert len(workspace.rewritten_paths) == 2


def test_materializer_rejects_missing_source(tmp_path: Path) -> None:
    inventory = ProjectInventory(project_id="Bench_Unit", entry_html="index.html")
    record = _record(tmp_path / "missing")

    try:
        materialize_test(
            MaterializerInput(
                run_id="run-unit",
                inventory=inventory,
                record=record,
                output_dir=str(tmp_path / "workspaces"),
            )
        )
    except RuntimeError as error:
        assert "source root" in str(error).casefold()
    else:
        raise AssertionError("missing source root should not materialize")
