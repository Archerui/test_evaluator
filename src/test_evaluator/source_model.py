"""Deterministic HTML/JavaScript source modeling for full-mode evaluation."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from html.parser import HTMLParser
from pathlib import Path

from .schemas import (
    DomAnchor,
    EventHandler,
    SourceModel,
    SourceModelInput,
    SourceModelOutput,
    StateEffect,
    Status,
)


_JS_EXTENSIONS = {".js", ".mjs", ".cjs"}
_HTML_EXTENSIONS = {".html", ".htm"}


@dataclass
class _Element:
    tag: str
    attributes: dict[str, str]
    file_path: str
    line: int
    text: list[str] = field(default_factory=list)


class _SourceHTMLParser(HTMLParser):
    def __init__(self, file_path: str) -> None:
        super().__init__(convert_charrefs=True)
        self.file_path = file_path
        self.stack: list[_Element] = []
        self.anchors: list[DomAnchor] = []
        self.inline_scripts: list[tuple[str, int]] = []
        self.external_scripts: list[tuple[str, int]] = []
        self.inline_handlers: list[EventHandler] = []
        self._script: _Element | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = {name.casefold(): value or "" for name, value in attrs}
        line = self.getpos()[0]
        element = _Element(tag.casefold(), attributes, self.file_path, line)
        self.stack.append(element)
        if tag.casefold() == "script":
            source = attributes.get("src")
            if source:
                self.external_scripts.append((source, line))
            else:
                self._script = element
        for name, value in attributes.items():
            if name.startswith("on") and len(name) > 2:
                self.inline_handlers.append(
                    EventHandler(
                        event=name[2:],
                        selector=_preferred_selector(tag, attributes),
                        function_name=value.strip() or None,
                        file_path=self.file_path,
                        line_start=line,
                    )
                )

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for element in self.stack:
            element.text.append(data)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.casefold()
        match_index = next(
            (index for index in range(len(self.stack) - 1, -1, -1) if self.stack[index].tag == tag),
            None,
        )
        if match_index is None:
            return
        closing = self.stack[match_index:]
        del self.stack[match_index:]
        for element in reversed(closing):
            self._finish(element)

    def close(self) -> None:
        super().close()
        for element in reversed(self.stack):
            self._finish(element)
        self.stack.clear()

    def _finish(self, element: _Element) -> None:
        text = re.sub(r"\s+", " ", " ".join(element.text)).strip()[:240] or None
        for selector in _element_selectors(element.tag, element.attributes):
            self.anchors.append(
                DomAnchor(
                    selector=selector,
                    tag=element.tag,
                    text=text,
                    attributes=element.attributes,
                    file_path=element.file_path,
                    line_start=element.line,
                )
            )
        if element is self._script:
            self.inline_scripts.append(("\n".join(element.text), element.line))
            self._script = None


def _quote_attribute(name: str, value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'[{name}="{escaped}"]'


def _element_selectors(tag: str, attributes: dict[str, str]) -> list[str]:
    selectors = [tag]
    for name, value in attributes.items():
        if value and (name.startswith("data-") or name in {"value", "type", "aria-label"}):
            selectors.append(_quote_attribute(name, value))
    if value := attributes.get("id"):
        selectors.append(f"#{value}")
    if value := attributes.get("name"):
        selectors.append(_quote_attribute("name", value))
    if value := attributes.get("role"):
        selectors.append(_quote_attribute("role", value))
    for class_name in attributes.get("class", "").split():
        if re.fullmatch(r"[A-Za-z_][\w-]*", class_name):
            selectors.append(f".{class_name}")
    return list(dict.fromkeys(selectors))


def _preferred_selector(tag: str, attributes: dict[str, str]) -> str:
    selectors = _element_selectors(tag, attributes)
    return next((selector for selector in selectors if selector.startswith("[data-test")), selectors[-1])


_VARIABLE_BINDING = re.compile(
    r"\b(?:const|let|var)\s+(?P<name>[A-Za-z_$][\w$]*)\s*=\s*document\."
    r"(?P<method>getElementById|getElementsByClassName|getElementsByTagName|getElementsByName|querySelector|querySelectorAll)"
    r"\(\s*['\"](?P<value>[^'\"]+)['\"]\s*\)"
)
_DIRECT_EVENT = re.compile(
    r"document\.(?P<method>getElementById|querySelector)\(\s*['\"](?P<value>[^'\"]+)['\"]\s*\)"
    r"\.addEventListener\(\s*['\"](?P<event>[\w:-]+)['\"]"
)
_VARIABLE_EVENT = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)(?:\s*\[[^\]]+\])?\.addEventListener"
    r"\(\s*['\"](?P<event>[\w:-]+)['\"]\s*,\s*(?P<handler>[A-Za-z_$][\w$]*|function)?"
)
_PROPERTY_EVENT = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)(?:\s*\[[^\]]+\])?\.on(?P<event>[a-z][\w]*)\s*=\s*"
    r"(?P<handler>[A-Za-z_$][\w$]*|function)?"
)
_DOM_EFFECT = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)(?:\s*\[[^\]]+\])?\."
    r"(?P<operation>innerHTML|textContent|innerText|value|appendChild|removeChild|replaceChildren|classList|style)"
)
_STORAGE_EFFECT = re.compile(r"(?P<storage>localStorage|sessionStorage)\.(?P<operation>setItem|getItem|removeItem|clear)\s*\(")
_FETCH = re.compile(r"\bfetch\(\s*(['\"])(?P<url>.+?)\1")
_CALCULATION = re.compile(r"(?m)\b(?P<name>[A-Za-z_$][\w$]*)\s*(?P<operation>\+=|-=|\*=|/=|\+\+|--)")
_NAVIGATION = re.compile(r"(?:window\.)?location\.(?P<operation>href|assign|replace)\b")
_CREATED_ELEMENT = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)\s*=\s*document\.createElement\(\s*['\"](?P<tag>[\w-]+)['\"]\s*\)"
)
_PROPERTY_ANCHOR = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)\.(?P<attribute>id|className)\s*=\s*['\"](?P<value>[^'\"]+)['\"]"
)
_SET_ATTRIBUTE = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)\.setAttribute\(\s*['\"]"
    r"(?P<attribute>id|class|data-testid|data-test-id|name|role)['\"]\s*,\s*['\"](?P<value>[^'\"]+)['\"]\s*\)"
)
_CLASS_LIST_ADD = re.compile(
    r"(?P<name>[A-Za-z_$][\w$]*)\.classList\.add\(\s*['\"](?P<value>[^'\"]+)['\"]\s*\)"
)
_HTML_FRAGMENT_TAG = re.compile(r"<(?P<tag>[A-Za-z][\w-]*)(?P<attributes>[^<>]*)>")
_HTML_FRAGMENT_ATTRIBUTE = re.compile(
    r"(?P<name>[A-Za-z_:][\w:.-]*)\s*=\s*(?P<quote>['\"])(?P<value>.*?)(?P=quote)"
)


def _selector_for_method(method: str, value: str) -> str:
    return {
        "getElementById": f"#{value}",
        "getElementsByClassName": f".{value}",
        "getElementsByTagName": value.casefold(),
        "getElementsByName": _quote_attribute("name", value),
        "querySelector": value,
        "querySelectorAll": value,
    }[method]


def _line(text: str, offset: int, base_line: int = 1) -> int:
    return base_line + text[:offset].count("\n")


def _analyze_javascript(
    text: str,
    file_path: str,
    *,
    base_line: int = 1,
) -> tuple[list[DomAnchor], list[EventHandler], list[StateEffect], list[str]]:
    variables = {
        match.group("name"): _selector_for_method(match.group("method"), match.group("value"))
        for match in _VARIABLE_BINDING.finditer(text)
    }
    created_matches = list(_CREATED_ELEMENT.finditer(text))
    created_tags = {match.group("name"): match.group("tag").casefold() for match in created_matches}
    dynamic_anchors: list[DomAnchor] = []
    for match in created_matches:
        tag = match.group("tag").casefold()
        dynamic_anchors.append(
            DomAnchor(
                selector=tag,
                tag=tag,
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for fragment in _HTML_FRAGMENT_TAG.finditer(text):
        attributes = {
            item.group("name").casefold(): item.group("value")
            for item in _HTML_FRAGMENT_ATTRIBUTE.finditer(fragment.group("attributes"))
        }
        for selector in _element_selectors(fragment.group("tag").casefold(), attributes):
            dynamic_anchors.append(
                DomAnchor(
                    selector=selector,
                    tag=fragment.group("tag").casefold(),
                    attributes=attributes,
                    file_path=file_path,
                    line_start=_line(text, fragment.start(), base_line),
                )
            )
    for pattern in (_PROPERTY_ANCHOR, _SET_ATTRIBUTE, _CLASS_LIST_ADD):
        for match in pattern.finditer(text):
            attribute = match.groupdict().get("attribute", "class")
            attribute = "class" if attribute == "className" else attribute
            value = match.group("value")
            attributes = {attribute: value}
            selectors = _element_selectors(created_tags.get(match.group("name"), "unknown"), attributes)
            for selector in selectors:
                if selector == "unknown":
                    continue
                dynamic_anchors.append(
                    DomAnchor(
                        selector=selector,
                        tag=created_tags.get(match.group("name"), "unknown"),
                        attributes=attributes,
                        file_path=file_path,
                        line_start=_line(text, match.start(), base_line),
                    )
                )
            preferred = next(
                (item for item in selectors if item != created_tags.get(match.group("name"), "unknown")),
                None,
            )
            if preferred:
                variables[match.group("name")] = preferred
    handlers: list[EventHandler] = []
    for match in _DIRECT_EVENT.finditer(text):
        handlers.append(
            EventHandler(
                event=match.group("event"),
                selector=_selector_for_method(match.group("method"), match.group("value")),
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for pattern in (_VARIABLE_EVENT, _PROPERTY_EVENT):
        for match in pattern.finditer(text):
            handlers.append(
                EventHandler(
                    event=match.group("event"),
                    selector=variables.get(match.group("name")),
                    function_name=(match.groupdict().get("handler") or None),
                    file_path=file_path,
                    line_start=_line(text, match.start(), base_line),
                )
            )

    effects: list[StateEffect] = []
    for match in _DOM_EFFECT.finditer(text):
        effects.append(
            StateEffect(
                kind="dom_update",
                target=variables.get(match.group("name"), match.group("name")),
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for match in _STORAGE_EFFECT.finditer(text):
        operation = match.group("operation")
        effects.append(
            StateEffect(
                kind="storage_write" if operation in {"setItem", "removeItem", "clear"} else "storage_read",
                target=match.group("storage"),
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    external_apis: list[str] = []
    for match in _FETCH.finditer(text):
        external_apis.append(match.group("url"))
        effects.append(
            StateEffect(
                kind="api_call",
                target=match.group("url"),
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for match in _CALCULATION.finditer(text):
        effects.append(
            StateEffect(
                kind="calculation",
                target=match.group("name"),
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for match in _NAVIGATION.finditer(text):
        effects.append(
            StateEffect(
                kind="navigation",
                target=f"location.{match.group('operation')}",
                file_path=file_path,
                line_start=_line(text, match.start(), base_line),
            )
        )
    for api in ("XMLHttpRequest", "navigator.clipboard", "speechSynthesis", "Notification", "Audio("):
        if api in text:
            external_apis.append(api.rstrip("("))
    return dynamic_anchors, _dedupe_handlers(handlers), _dedupe_effects(effects), sorted(set(external_apis))


def _dedupe_handlers(items: list[EventHandler]) -> list[EventHandler]:
    seen: set[tuple[object, ...]] = set()
    result: list[EventHandler] = []
    for item in items:
        key = (item.event, item.selector, item.function_name, item.file_path, item.line_start)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def _dedupe_effects(items: list[StateEffect]) -> list[StateEffect]:
    seen: set[tuple[object, ...]] = set()
    result: list[StateEffect] = []
    for item in items:
        key = (item.kind, item.target, item.file_path, item.line_start)
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result


def build_source_model(request: SourceModelInput) -> SourceModelOutput:
    """Build a conservative source model from discovered HTML and JavaScript files."""

    inventory = request.inventory
    if not inventory.source_root:
        raise ValueError(f"Project {inventory.project_id} has no source root")
    root = Path(inventory.source_root).resolve()
    if not root.is_dir():
        raise FileNotFoundError(f"Source root does not exist: {root}")

    anchors: list[DomAnchor] = []
    handlers: list[EventHandler] = []
    effects: list[StateEffect] = []
    external_apis: list[str] = []
    warnings: list[str] = []
    analyzed_files: list[str] = []
    source_files = sorted(
        relative
        for relative in inventory.source_files
        if Path(relative).suffix.casefold() in _HTML_EXTENSIONS | _JS_EXTENSIONS
    )
    for relative in source_files:
        path = root / relative
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            warnings.append(f"Could not read {relative}: {error}")
            continue
        analyzed_files.append(relative)
        suffix = path.suffix.casefold()
        if suffix in _HTML_EXTENSIONS:
            parser = _SourceHTMLParser(relative)
            try:
                parser.feed(text)
                parser.close()
            except Exception as error:
                warnings.append(f"Partial HTML parse for {relative}: {type(error).__name__}: {error}")
            anchors.extend(parser.anchors)
            handlers.extend(parser.inline_handlers)
            for script_text, start_line in parser.inline_scripts:
                js_anchors, js_handlers, js_effects, js_apis = _analyze_javascript(
                    script_text,
                    relative,
                    base_line=start_line,
                )
                anchors.extend(js_anchors)
                handlers.extend(js_handlers)
                effects.extend(js_effects)
                external_apis.extend(js_apis)
            for script_source, line in parser.external_scripts:
                clean_source = script_source.split("?", 1)[0].split("#", 1)[0]
                if not (path.parent / clean_source).is_file() and not re.match(r"https?://", script_source):
                    warnings.append(f"Referenced script not found at {relative}:{line}: {script_source}")
        elif suffix in _JS_EXTENSIONS:
            js_anchors, js_handlers, js_effects, js_apis = _analyze_javascript(text, relative)
            anchors.extend(js_anchors)
            handlers.extend(js_handlers)
            effects.extend(js_effects)
            external_apis.extend(js_apis)

    unique_anchors: list[DomAnchor] = []
    seen_anchors: set[tuple[object, ...]] = set()
    for anchor in anchors:
        key = (anchor.selector, anchor.file_path, anchor.line_start)
        if key not in seen_anchors:
            seen_anchors.add(key)
            unique_anchors.append(anchor)

    model = SourceModel(
        project_id=inventory.project_id,
        source_root=str(root),
        entry_html=inventory.entry_html,
        dom_anchors=unique_anchors,
        event_handlers=_dedupe_handlers(handlers),
        state_effects=_dedupe_effects(effects),
        external_apis=sorted(set(external_apis)),
        source_files=analyzed_files,
        parse_warnings=warnings,
    )
    status = Status.WARNING if warnings else Status.PASS
    if not analyzed_files:
        status = Status.UNKNOWN
        warnings.append("No HTML or JavaScript source files were available for analysis")
    return SourceModelOutput(
        agent="source_model",
        run_id=request.run_id,
        mode="full",
        project_id=inventory.project_id,
        status=status,
        confidence=0.9 if analyzed_files else 0.0,
        warnings=warnings,
        source_model=model,
    )
