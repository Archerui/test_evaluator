"""Ground Selenium selectors and requirement UI anchors in a SourceModel."""

from __future__ import annotations

import re

from .schemas import (
    Evidence,
    Finding,
    SelectorGroundingInput,
    SelectorGroundingItem,
    SelectorGroundingOutput,
    Severity,
    Status,
)


_LOCATOR = re.compile(
    r"By\.(?P<kind>CSS_SELECTOR|ID|CLASS_NAME|NAME|TAG_NAME|XPATH)\s*,\s*f?"
    r"(?P<quote>['\"])(?P<value>.*?)(?P=quote)"
)
_SIMPLE_CSS = re.compile(
    r"#[A-Za-z_][\w-]*|\.[A-Za-z_][\w-]*|"
    r"\[(?:data-testid|data-test-id|name|role)\s*=\s*['\"][^'\"]+['\"]\]|"
    r"(?<![-\w])[A-Za-z][\w-]*(?![-\w])"
)
_DYNAMIC = re.compile(r"\{[^{}]+\}")


def _canonical(selector: str) -> str:
    return re.sub(r"\s+", " ", selector.strip().replace("'", '"'))


def _normalize_locator(kind: str, value: str) -> str:
    if kind == "ID":
        return f"#{value}"
    if kind == "CLASS_NAME":
        return f".{value}"
    if kind == "NAME":
        return f'[name="{value}"]'
    if kind == "TAG_NAME":
        return value.casefold()
    if kind == "XPATH":
        id_match = re.search(r"@id\s*=\s*['\"]([^'\"]+)", value)
        test_id_match = re.search(r"@data-testid\s*=\s*['\"]([^'\"]+)", value)
        if id_match:
            return f"#{id_match.group(1)}"
        if test_id_match:
            return f'[data-testid="{test_id_match.group(1)}"]'
        tag_match = re.fullmatch(r"//([A-Za-z][\w-]*)", value.strip())
        return tag_match.group(1).casefold() if tag_match else value
    return _canonical(value)


def _purpose(code: str, offset: int) -> str:
    decorators = list(re.finditer(r"(?m)^\s*@(given|when|then|step)\s*\(", code[:offset]))
    if not decorators:
        return "unknown"
    kind = decorators[-1].group(1)
    return {
        "given": "precondition",
        "when": "action_target",
        "then": "oracle_target",
        "step": "unknown",
    }[kind]


def _line(text: str, offset: int) -> int:
    return text[:offset].count("\n") + 1


def _contract_selector(anchor: str) -> str | None:
    candidate = _canonical(anchor)
    test_id = re.search(r"data-test(?:id|-id)\s*[=: ]\s*['\"]?([\w${}.-]+)", candidate)
    if test_id:
        return f'[data-testid="{test_id.group(1)}"]'
    if candidate.startswith(("#", ".", "[", "//")):
        return candidate
    return None


def _matches(selector: str, anchors) -> list:
    canonical = _canonical(selector)
    by_selector: dict[str, list] = {}
    for anchor in anchors:
        by_selector.setdefault(_canonical(anchor.selector), []).append(anchor)

    if canonical in by_selector:
        return by_selector[canonical]

    for anchor_selector, candidates in by_selector.items():
        if _DYNAMIC.search(anchor_selector) and _dynamic_regex(anchor_selector).match(canonical):
            return candidates

    if _DYNAMIC.search(canonical):
        regex = _dynamic_regex(canonical)
        return [anchor for anchor in anchors if regex.match(_canonical(anchor.selector))]

    without_state = re.sub(r":(?:checked|selected|enabled|disabled|first-child|last-child)$", "", canonical)
    if without_state in by_selector:
        return by_selector[without_state]

    xpath_text = re.search(
        r"//(?P<tag>[A-Za-z][\w-]*).*?text\(\).*?['\"](?P<text>[^'\"]+)['\"]",
        canonical,
    )
    if xpath_text:
        return [
            anchor
            for anchor in anchors
            if anchor.tag == xpath_text.group("tag").casefold()
            and anchor.text
            and xpath_text.group("text") in anchor.text
        ]

    tokens = [_canonical(token) for token in _SIMPLE_CSS.findall(canonical)]
    meaningful = [token for token in tokens if token.startswith(("#", ".", "["))]
    if not meaningful and canonical.casefold() in by_selector:
        meaningful = [canonical.casefold()]
    if meaningful and all(token in by_selector for token in meaningful):
        result = []
        for token in meaningful:
            result.extend(by_selector[token])
        return list({(item.file_path, item.line_start, item.selector): item for item in result}.values())
    return []


def _dynamic_regex(selector: str) -> re.Pattern[str]:
    parts: list[str] = []
    cursor = 0
    for match in _DYNAMIC.finditer(selector):
        parts.append(re.escape(selector[cursor:match.start()]))
        parts.append(".+")
        cursor = match.end()
    parts.append(re.escape(selector[cursor:]))
    return re.compile("^" + "".join(parts) + "$")


def _stability(selector: str) -> str:
    if _DYNAMIC.search(selector):
        return "medium"
    if "data-testid" in selector or selector.startswith("#") or selector.startswith("[name="):
        return "stable"
    if selector.startswith(".") or selector.startswith("[role="):
        return "medium"
    if selector.startswith("/") or any(token in selector for token in (":nth-", ">", "[1]")):
        return "brittle"
    if re.fullmatch(r"[A-Za-z][\w-]*", selector):
        return "medium"
    return "unknown"


def ground_selectors(request: SelectorGroundingInput) -> SelectorGroundingOutput:
    code = request.record.step_code
    items: list[SelectorGroundingItem] = []
    findings: list[Finding] = []
    unresolved_dynamic = 0
    locator_matches = list(_LOCATOR.finditer(code))
    for match in locator_matches:
        selector = _normalize_locator(match.group("kind"), match.group("value"))
        matched = _matches(selector, request.source_model.dom_anchors)
        dynamic = bool(_DYNAMIC.search(selector))
        raw_value = match.group("value").strip()
        xpath_tag = re.search(r"//([A-Za-z][\w-]*)", raw_value)
        xpath_text_is_runtime_dependent = (
            match.group("kind") == "XPATH"
            and "text()" in raw_value
            and xpath_tag is not None
            and any(anchor.tag == xpath_tag.group(1).casefold() for anchor in request.source_model.dom_anchors)
        )
        context_dependent = (
            match.group("kind") == "XPATH" and raw_value.startswith(".")
        ) or xpath_text_is_runtime_dependent
        evidence = [
            Evidence(
                field="source_model.dom_anchors",
                quote=anchor.selector,
                file_path=anchor.file_path,
                line_start=anchor.line_start,
            )
            for anchor in matched[:10]
        ]
        items.append(
            SelectorGroundingItem(
                selector=selector,
                source_exists=bool(matched),
                matched_anchors=matched[:25],
                stability=_stability(selector),  # type: ignore[arg-type]
                purpose=_purpose(code, match.start()),  # type: ignore[arg-type]
                evidence=evidence,
            )
        )
        if not matched and (dynamic or context_dependent):
            unresolved_dynamic += 1
        elif not matched:
            findings.append(
                Finding(
                    criterion=f"Selector exists in application source: {selector}",
                    status=Status.FAIL,
                    severity=Severity.MAJOR,
                    confidence=0.95,
                    evidence=[
                        Evidence(
                            field="step_code",
                            quote=match.group(0),
                            line_start=_line(code, match.start()),
                        )
                    ],
                    reasoning="The literal Selenium locator did not match a DOM anchor in the discovered HTML source.",
                    suggested_fix="Correct the locator or confirm that the element is created dynamically before this step runs.",
                )
            )

    anchor_test_ids = {
        anchor.attributes.get("data-testid")
        for anchor in request.source_model.dom_anchors
        if anchor.attributes.get("data-testid")
    }
    expected_test_ids = set(request.static_facts.requirement_test_ids + request.static_facts.gherkin_test_ids)
    missing_source_anchors = {
        f'[data-testid="{test_id}"]'
        for test_id in sorted(expected_test_ids.difference(anchor_test_ids))
    }
    contract_selectors: set[str] = set()
    for behavior in request.contract.behaviors:
        for raw_anchor in behavior.ui_anchors:
            selector = _contract_selector(raw_anchor)
            if selector:
                contract_selectors.add(selector)
            if selector and not _matches(selector, request.source_model.dom_anchors):
                missing_source_anchors.add(selector)
    sorted_missing_source_anchors = sorted(missing_source_anchors)
    for selector in sorted_missing_source_anchors:
        findings.append(
            Finding(
                criterion=f"BDD/requirement UI anchor exists in source: {selector}",
                status=Status.FAIL,
                severity=Severity.MAJOR,
                confidence=0.95,
                evidence=[Evidence(field="scenario_or_requirement", quote=selector)],
                reasoning="A UI anchor named by the requirement or scenario was not found in the application source model.",
                suggested_fix="Align the BDD anchor with the application source or add the intended stable test identifier.",
            )
        )

    warnings: list[str] = []
    if unresolved_dynamic:
        warnings.append(
            f"{unresolved_dynamic} dynamic or context-dependent selectors could not be proven from static source and require runtime confirmation."
        )
    if findings:
        status = Status.FAIL
        confidence = 0.95
    elif unresolved_dynamic:
        status = Status.WARNING
        confidence = 0.6
    elif not items and not expected_test_ids and not contract_selectors:
        status = Status.SKIPPED
        confidence = 1.0
        warnings.append("No Selenium DOM selectors or explicit test IDs were present in this test")
    else:
        status = Status.PASS
        confidence = 0.95
    return SelectorGroundingOutput(
        agent="selector_grounding",
        run_id=request.run_id,
        mode="full",
        project_id=request.record.project_id,
        suite_key=request.record.suite_key,
        record_key=request.record.record_key,
        dimension="source_grounding",
        status=status,
        confidence=confidence,
        findings=findings,
        warnings=warnings,
        selectors=items,
        missing_source_anchors=sorted_missing_source_anchors,
    )
