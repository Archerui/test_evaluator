"""Discovery helpers for a cloned E2EDev repository."""

from __future__ import annotations

import json
from pathlib import Path

from .ingest import load_e2edev_project_records
from .schemas import ProjectInventory, Status, TestRecord


SOURCE_DIR_CANDIDATES = ("source_projcet", "source_project", "source_code")
CODE_EXTENSIONS = {".html", ".htm", ".js", ".mjs", ".cjs", ".css", ".json"}


def resolve_data_root(e2edev_root: str | Path) -> Path:
    root = Path(e2edev_root).resolve()
    if not root.exists():
        raise FileNotFoundError(f"E2EDev root does not exist: {root}")
    nested = root / "E2EDev_data"
    if nested.is_dir():
        return nested
    if root.name == "E2EDev_data":
        return root
    if any(child.is_dir() and child.name.startswith("E2ESD_Bench_") for child in root.iterdir()):
        return root
    raise ValueError(f"Could not locate E2EDev_data under {root}")


def _source_root(project_dir: Path) -> Path | None:
    for name in SOURCE_DIR_CANDIDATES:
        candidate = project_dir / name
        if candidate.is_dir():
            return candidate.resolve()
    return None


def _entry_html(source_root: Path | None) -> str | None:
    if source_root is None:
        return None
    candidates = sorted(
        source_root.rglob("*.html"),
        key=lambda path: (path.name != "index.html", len(path.relative_to(source_root).parts), str(path)),
    )
    return str(candidates[0].relative_to(source_root)) if candidates else None


def _project_counts(tests_file: Path) -> tuple[int, int, list[str]]:
    warnings: list[str] = []
    if not tests_file.is_file():
        return 0, 0, [f"Missing tests file: {tests_file.name}"]
    try:
        payload = json.loads(tests_file.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return 0, 0, [f"Could not parse {tests_file.name}: {error}"]
    suites = payload.get("finegrained_rewith_test")
    if not isinstance(suites, dict):
        return 0, 0, ["Missing object 'finegrained_rewith_test'"]
    test_count = 0
    for suite in suites.values():
        if isinstance(suite, dict) and isinstance(suite.get("test_cases"), list):
            test_count += len(suite["test_cases"])
    return test_count, len(suites), warnings


def discover_project_inventories(
    e2edev_root: str | Path,
    selected_projects: list[str] | tuple[str, ...] | None = None,
) -> list[ProjectInventory]:
    data_root = resolve_data_root(e2edev_root)
    requested = set(selected_projects or [])
    project_dirs = sorted(
        child for child in data_root.iterdir() if child.is_dir() and child.name.startswith("E2ESD_Bench_")
    )
    available = {path.name for path in project_dirs}
    missing = sorted(requested.difference(available))
    if missing:
        raise ValueError(f"Requested E2EDev projects were not found: {', '.join(missing)}")
    if requested:
        project_dirs = [path for path in project_dirs if path.name in requested]

    inventories: list[ProjectInventory] = []
    for project_dir in project_dirs:
        source_root = _source_root(project_dir)
        tests_file = project_dir / "requirment_with_tests.json"
        test_count, requirement_count, warnings = _project_counts(tests_file)
        if source_root is None:
            warnings.append("No source_projcet/source_project/source_code directory found")
        entry_html = _entry_html(source_root)
        if source_root is not None and entry_html is None:
            warnings.append("No HTML entry point found under source directory")

        source_files: list[str] = []
        asset_files: list[str] = []
        if source_root is not None:
            for path in sorted(source_root.rglob("*")):
                if not path.is_file() or path.name == ".DS_Store":
                    continue
                relative = str(path.relative_to(source_root))
                (source_files if path.suffix.casefold() in CODE_EXTENSIONS else asset_files).append(relative)

        requirements_file = source_root / "requirements.json" if source_root else None
        analysis_file = source_root / "web_application_analysis.json" if source_root else None
        status = Status.PASS if not warnings else Status.WARNING
        if not tests_file.is_file():
            status = Status.FAIL
        inventories.append(
            ProjectInventory(
                project_id=project_dir.name,
                project_root=str(project_dir.resolve()),
                source_root=str(source_root) if source_root else None,
                entry_html=entry_html,
                tests_file=str(tests_file.resolve()) if tests_file.exists() else None,
                requirements_file=str(requirements_file.resolve()) if requirements_file and requirements_file.is_file() else None,
                web_application_analysis_file=(
                    str(analysis_file.resolve()) if analysis_file and analysis_file.is_file() else None
                ),
                source_files=source_files,
                asset_files=asset_files,
                test_count=test_count,
                requirement_count=requirement_count,
                discovery_status=status,
                warnings=warnings,
            )
        )
    if not inventories:
        raise ValueError(f"No E2EDev projects found under {data_root}")
    return inventories


def load_inventory_records(inventories: list[ProjectInventory]) -> list[TestRecord]:
    records: list[TestRecord] = []
    for inventory in inventories:
        if not inventory.project_root or not inventory.tests_file:
            continue
        records.extend(
            load_e2edev_project_records(
                inventory.project_root,
                source_root=inventory.source_root,
            )
        )
    return records


def _read_json_document(path: Path) -> object:
    text = path.read_text(encoding="utf-8", errors="replace").strip()
    if text.startswith("```"):
        lines = text.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)
    return json.loads(text)


def load_inventory_semantic_context(
    inventory: ProjectInventory,
) -> tuple[list[str], dict[str, object], list[str]]:
    """Load optional source-side requirements and application analysis for live agents."""

    requirements: list[str] = []
    analysis: dict[str, object] = {}
    warnings: list[str] = []
    if inventory.requirements_file:
        try:
            payload = _read_json_document(Path(inventory.requirements_file))
            if isinstance(payload, dict) and isinstance(payload.get("requirements"), list):
                for item in payload["requirements"]:
                    if isinstance(item, dict) and item.get("description"):
                        requirements.append(str(item["description"]).strip())
                    elif isinstance(item, str):
                        requirements.append(item.strip())
        except (OSError, json.JSONDecodeError) as error:
            warnings.append(f"Could not parse source requirements for {inventory.project_id}: {error}")
    if inventory.web_application_analysis_file:
        try:
            payload = _read_json_document(Path(inventory.web_application_analysis_file))
            if isinstance(payload, dict):
                analysis = payload
        except (OSError, json.JSONDecodeError) as error:
            warnings.append(f"Could not parse web application analysis for {inventory.project_id}: {error}")
    return requirements, analysis, warnings
