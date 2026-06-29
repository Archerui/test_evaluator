"""Deterministic facts and findings for Behave/Selenium step code."""

from __future__ import annotations

import ast
import re

from .ingest import TestRecord
from .schemas import AgentReview, Evidence, Finding, Severity, StaticFacts, Status


GHERKIN_STEP_RE = re.compile(r"^\s*(Given|When|Then|And|But)\s+(.+?)\s*$", re.MULTILINE)
TEST_ID_RE = re.compile(r"(?:data-testid|data-test-id)\s*[= ]\s*['\"]([^'\"`\r\n]+)['\"]")
SCENARIO_RE = re.compile(r"^\s*Scenario:\s*(?:\[([^\]]+)\]\s*)?(.+?)\s*$", re.MULTILINE)
SELECTOR_RE = re.compile(
    r"By\.(?:CSS_SELECTOR|ID|CLASS_NAME|NAME|TAG_NAME|XPATH)\s*,\s*f?['\"]([^'\"]+)['\"]"
)
FILE_URL_RE = re.compile(r"file://[^'\"\s)]+")


def _line_for_substring(text: str, needle: str) -> int | None:
    index = text.find(needle)
    return text[:index].count("\n") + 1 if index >= 0 else None


def _decorator_description(decorator: ast.expr) -> str | None:
    if not isinstance(decorator, ast.Call):
        return None
    if not isinstance(decorator.func, ast.Name):
        return None
    if decorator.func.id not in {"given", "when", "then", "step"}:
        return None
    if not decorator.args:
        return decorator.func.id
    first = decorator.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return f"{decorator.func.id}: {first.value}"
    return decorator.func.id


def _resolved_gherkin_steps(scenario: str) -> list[str]:
    resolved: list[str] = []
    previous = "given"
    for keyword, text in GHERKIN_STEP_RE.findall(scenario):
        kind = keyword.casefold()
        if kind in {"given", "when", "then"}:
            previous = kind
        else:
            kind = previous
        resolved.append(f"{kind}: {text}")
    return resolved


def _step_pattern_matches(pattern: str, value: str) -> bool:
    pattern = pattern.rstrip(":").replace("\\n", "\n")
    value = value.rstrip(":").replace("\\n", "\n")
    pieces: list[str] = []
    cursor = 0
    for match in re.finditer(r"\{[^{}]+\}", pattern):
        pieces.append(re.escape(pattern[cursor:match.start()]))
        pieces.append(".+")
        cursor = match.end()
    pieces.append(re.escape(pattern[cursor:]))
    return bool(re.fullmatch("".join(pieces), value, flags=re.IGNORECASE))


def _missing_step_definitions(gherkin_steps: list[str], decorators: list[str]) -> list[str]:
    parsed_decorators: list[tuple[str, str]] = []
    wildcard_patterns: list[str] = []
    for decorator in decorators:
        if ": " not in decorator:
            continue
        kind, pattern = decorator.split(": ", 1)
        if kind == "step":
            wildcard_patterns.append(pattern)
        else:
            parsed_decorators.append((kind, pattern))
    missing: list[str] = []
    for step in gherkin_steps:
        kind, value = step.split(": ", 1)
        patterns = [pattern for decorator_kind, pattern in parsed_decorators if decorator_kind == kind]
        patterns.extend(wildcard_patterns)
        if not any(_step_pattern_matches(pattern, value) for pattern in patterns):
            missing.append(step)
    return missing


def _attribute_actions(tree: ast.AST) -> list[str]:
    actions = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    interesting = {
        "click",
        "clear",
        "send_keys",
        "drag_and_drop",
        "execute_script",
        "get",
        "find_element",
        "find_elements",
        "quit",
    }
    return sorted(actions.intersection(interesting))


def extract_static_facts(record: TestRecord) -> StaticFacts:
    """Extract facts that can be checked without an LLM or browser execution."""

    scenario_match = SCENARIO_RE.search(record.scenario)
    scenario_type = scenario_match.group(1).strip() if scenario_match and scenario_match.group(1) else None
    gherkin_steps = _resolved_gherkin_steps(record.scenario)
    requirement_test_ids = sorted(set(TEST_ID_RE.findall(record.requirement)))
    gherkin_test_ids = sorted(set(TEST_ID_RE.findall(record.scenario)))
    code_test_ids = sorted(set(TEST_ID_RE.findall(record.step_code)))

    try:
        tree = ast.parse(record.step_code)
    except SyntaxError as error:
        return StaticFacts(
            python_parseable=False,
            syntax_error=f"{error.msg} (line {error.lineno})",
            scenario_present=scenario_match is not None,
            scenario_type=scenario_type,
            gherkin_steps=gherkin_steps,
            requirement_test_ids=requirement_test_ids,
            gherkin_test_ids=gherkin_test_ids,
            code_test_ids=code_test_ids,
            gherkin_ids_missing_from_code=sorted(set(gherkin_test_ids).difference(code_test_ids)),
        )

    decorators = sorted(
        description
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for decorator in node.decorator_list
        if (description := _decorator_description(decorator)) is not None
    )
    assertions = [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
    trivial_assertions = [
        node
        for node in assertions
        if isinstance(node.test, ast.Constant) and node.test.value is True
    ]
    decorator_counts: dict[str, int] = {}
    for decorator in decorators:
        decorator_counts[decorator] = decorator_counts.get(decorator, 0) + 1
    duplicate_step_definitions = sorted(
        decorator for decorator, count in decorator_counts.items() if count > 1
    )
    missing_step_definitions = _missing_step_definitions(gherkin_steps, decorators)
    print_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print"
    ]
    return StaticFacts(
        python_parseable=True,
        scenario_present=scenario_match is not None,
        scenario_type=scenario_type,
        gherkin_steps=gherkin_steps,
        decorators=decorators,
        missing_step_definitions=missing_step_definitions,
        duplicate_step_definitions=duplicate_step_definitions,
        assertion_count=len(assertions),
        trivial_assertion_count=len(trivial_assertions),
        print_only_oracle_count=len(print_calls) if not assertions else 0,
        requirement_test_ids=requirement_test_ids,
        gherkin_test_ids=gherkin_test_ids,
        code_test_ids=code_test_ids,
        gherkin_ids_missing_from_code=sorted(set(gherkin_test_ids).difference(code_test_ids)),
        selectors=sorted(set(SELECTOR_RE.findall(record.step_code))),
        actions=_attribute_actions(tree),
        webdriver_wait_count=record.step_code.count("WebDriverWait("),
        sleep_count=record.step_code.count("time.sleep("),
        has_driver_quit=".quit()" in record.step_code,
        hardcoded_file_paths=sorted(set(FILE_URL_RE.findall(record.step_code))),
        direct_event_construction=sorted(
            token
            for token in ("DataTransfer(", "DragEvent(", "new Event(", "dispatchEvent(")
            if token in record.step_code
        ),
    )


def static_review(record: TestRecord, facts: StaticFacts) -> AgentReview:
    """Turn deterministic facts into the static-verifier review contract."""

    findings: list[Finding] = []
    if not facts.python_parseable:
        findings.append(
            Finding(
                criterion="Python step code parses successfully",
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_step_code", quote=facts.syntax_error or "syntax error")],
                reasoning="The step implementation cannot be imported by Behave until the syntax error is fixed.",
                suggested_fix="Fix the Python syntax error and re-run the static verifier.",
            )
        )
    if not facts.scenario_present:
        findings.append(
            Finding(
                criterion="BDD scenario is present",
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_test_case", quote="No Scenario: declaration found")],
                reasoning="Behave requires a scenario to bind the test intent to step definitions.",
                suggested_fix="Add a Scenario with explicit Given/When/Then steps.",
            )
        )
    if not any(step.startswith("then:") for step in facts.gherkin_steps):
        findings.append(
            Finding(
                criterion="BDD scenario declares an expected result",
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_test_case", quote="No Then step found")],
                reasoning="A test without an expected result cannot express a test oracle.",
                suggested_fix="Add a Then step that describes the expected observable result.",
            )
        )
    if facts.assertion_count == 0 and facts.python_parseable:
        findings.append(
            Finding(
                criterion="Step code contains an automatic assertion",
                status=Status.WARNING,
                severity=Severity.MAJOR,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_step_code", quote="No Python assert statement found")],
                reasoning="This is a strong oracle-risk signal; the Oracle Critic decides whether another valid observation mechanism exists.",
                suggested_fix="Assert an observable state that corresponds to the Then outcome.",
            )
        )
    if facts.missing_step_definitions:
        findings.append(
            Finding(
                criterion="Every Gherkin step has a matching Behave implementation",
                status=Status.FAIL,
                severity=Severity.CRITICAL,
                confidence=0.95,
                evidence=[
                    Evidence(
                        field="derived.static_facts",
                        quote=", ".join(facts.missing_step_definitions[:5]),
                    )
                ],
                reasoning="At least one scenario step could not be matched to a given/when/then/step decorator in this test implementation.",
                suggested_fix="Add or correct the Behave decorator pattern for each missing Gherkin step.",
            )
        )
    if facts.trivial_assertion_count:
        findings.append(
            Finding(
                criterion="Assertions are non-trivial",
                status=Status.WARNING,
                severity=Severity.MAJOR,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_step_code", quote="assert True")],
                reasoning="A constant assertion cannot detect a behavioral regression.",
                suggested_fix="Replace constant assertions with checks of the requirement's expected observable.",
            )
        )
    if facts.sleep_count:
        findings.append(
            Finding(
                criterion="Synchronization uses deterministic waits",
                status=Status.WARNING,
                severity=Severity.MINOR,
                confidence=1.0,
                evidence=[Evidence(field="excutable_test_step_code", quote="time.sleep(", line_start=_line_for_substring(record.step_code, "time.sleep("))],
                reasoning="Fixed sleeps can make browser tests slow and flaky; they are not proof that the awaited state occurred.",
                suggested_fix="Prefer a targeted WebDriverWait condition for the state asserted by the test.",
            )
        )
    if facts.gherkin_ids_missing_from_code:
        missing = ", ".join(facts.gherkin_ids_missing_from_code)
        findings.append(
            Finding(
                criterion="Gherkin UI anchors are traceable in step code",
                status=Status.WARNING,
                severity=Severity.MINOR,
                confidence=0.75,
                evidence=[Evidence(field="derived.static_facts", quote=f"Gherkin test IDs absent as literal code selectors: {missing}")],
                reasoning="Literal selector mismatch is a candidate risk only; helpers or parent locators can be valid alternatives.",
                suggested_fix="Have the Step-Code Agent confirm that each important UI anchor is reached by an equivalent locator.",
            )
        )

    status = Status.PASS if not findings else max((finding.status for finding in findings), key=_status_rank)
    return AgentReview(
        agent="static_verifier",
        record_key=record.record_key,
        dimension="robustness",
        status=status,
        confidence=1.0,
        findings=findings,
    )


def _status_rank(status: Status) -> int:
    return {Status.PASS: 0, Status.UNKNOWN: 1, Status.WARNING: 2, Status.FAIL: 3}[status]
