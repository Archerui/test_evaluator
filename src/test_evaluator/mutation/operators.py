"""Conservative, line-addressable mutation operators for browser applications."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


DEFAULT_OPERATORS = (
    "event_name",
    "event_handler",
    "dom_update",
    "api_call",
    "string_literal",
    "comparison",
    "boolean_literal",
    "numeric_literal",
    "arithmetic",
)


@dataclass(frozen=True)
class MutationCandidate:
    operator: str
    line_start: int
    original: str
    mutated: str


_SCRIPT_BLOCK = re.compile(r"<script\b(?![^>]*\bsrc\s*=)[^>]*>(?P<code>.*?)</script\s*>", re.I | re.S)
_COMPARISON = re.compile(r"===|!==|==|!=|>=|<=")
_BOOLEAN = re.compile(r"\b(?:true|false)\b")
_NUMERIC_BOUNDARY = re.compile(r"(?<![\w$.])(?:0|1)(?![\w.])")
_ARITHMETIC = re.compile(r"(?P<left>[\w)\]])(?P<space1>\s*)(?P<op>[+\-*])(?P<space2>\s*)(?=[\w(\[])")
_ADD_EVENT = re.compile(
    r"\.addEventListener\(\s*(?P<quote>['\"])(?P<event>[A-Za-z][\w:-]*)(?P=quote)"
)
_PROPERTY_EVENT = re.compile(r"\.on(?P<event>click|change|input|submit|drop|dragstart|dragover|load|keydown|keyup)\b")
_EVENT_HANDLER_OPEN = re.compile(
    r"\.addEventListener\(\s*['\"][A-Za-z][\w:-]*['\"]\s*,\s*"
    r"(?:(?:async\s+)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>|"
    r"(?:async\s+)?function(?:\s+[A-Za-z_$][\w$]*)?\s*\([^)]*\))\s*(?P<open>\{)"
)
_DOM_CALL = re.compile(r"\b[A-Za-z_$][\w$]*(?:\[[^\]\r\n]+\])?\.(?:appendChild|removeChild|replaceChildren)\([^;\r\n]*\)\s*;")
_DOM_ASSIGNMENT = re.compile(
    r"(?P<target>\b[A-Za-z_$][\w$]*(?:\[[^\]\r\n]+\])?\.(?:innerHTML|textContent|innerText))"
    r"\s*=\s*[^;\r\n]+;"
)
_API_CALL_LINE = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?:await[ \t]+)?(?:"
    r"fetch|speechSynthesis\.speak|navigator\.clipboard\.(?:writeText|readText)|"
    r"Notification\.requestPermission|[A-Za-z_$][\w$]*\.play"
    r")\s*\([^;\r\n]*\)(?:\.[^;\r\n]+)?\s*;[ \t]*$"
)
_HIGH_VALUE_STRING = re.compile(
    r"(?:"
    r"(?:localStorage|sessionStorage)\.(?:getItem|setItem|removeItem)|"
    r"document\.(?:querySelector|querySelectorAll|getElementById|getElementsByClassName|getElementsByName)"
    r")\(\s*(?P<quote>['\"])(?P<value>[^'\"\r\n]+)(?P=quote)"
)


def _mask_non_code(text: str) -> str:
    """Mask JS comments/strings while preserving offsets and newlines."""

    chars = list(text)
    index = 0
    state = "code"
    quote = ""
    while index < len(chars):
        char = chars[index]
        following = chars[index + 1] if index + 1 < len(chars) else ""
        if state == "code":
            if char == "/" and following == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if char == "/" and following == "*":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if char in {"'", '"', "`"}:
                quote = char
                chars[index] = " "
                index += 1
                state = "string"
                continue
        elif state == "line_comment":
            if char == "\n":
                state = "code"
            else:
                chars[index] = " "
            index += 1
            continue
        elif state == "block_comment":
            if char == "*" and following == "/":
                chars[index] = chars[index + 1] = " "
                index += 2
                state = "code"
                continue
            if char != "\n":
                chars[index] = " "
            index += 1
            continue
        elif state == "string":
            if char == "\\":
                chars[index] = " "
                if index + 1 < len(chars) and chars[index + 1] != "\n":
                    chars[index + 1] = " "
                index += 2
                continue
            if char == quote:
                chars[index] = " "
                state = "code"
            elif char != "\n":
                chars[index] = " "
            index += 1
            continue
        index += 1
    return "".join(chars)


def _segments(file_path: str, text: str) -> list[tuple[int, str]]:
    if Path(file_path).suffix.casefold() not in {".html", ".htm"}:
        return [(0, text)]
    return [(match.start("code"), match.group("code")) for match in _SCRIPT_BLOCK.finditer(text)]


def _line_candidate(
    text: str,
    start: int,
    end: int,
    replacement: str,
    operator: str,
) -> MutationCandidate | None:
    line_start_offset = text.rfind("\n", 0, start) + 1
    line_end_offset = text.find("\n", end)
    if line_end_offset < 0:
        line_end_offset = len(text)
    if "\n" in text[start:end] or "\r" in text[start:end]:
        return None
    original_line = text[line_start_offset:line_end_offset].rstrip("\r")
    relative_start = start - line_start_offset
    relative_end = end - line_start_offset
    mutated_line = original_line[:relative_start] + replacement + original_line[relative_end:]
    if original_line == mutated_line:
        return None
    return MutationCandidate(
        operator=operator,
        line_start=text[:line_start_offset].count("\n") + 1,
        original=original_line,
        mutated=mutated_line,
    )


def generate_candidates(
    file_path: str,
    text: str,
    operators: tuple[str, ...] | list[str] = DEFAULT_OPERATORS,
) -> list[MutationCandidate]:
    enabled = set(operators)
    candidates: list[MutationCandidate] = []
    comparison_replacements = {"===": "!==", "!==": "===", "==": "!=", "!=": "==", ">=": "<", "<=": ">"}
    arithmetic_replacements = {"+": "-", "-": "+", "*": "+"}

    for segment_offset, segment in _segments(file_path, text):
        masked = _mask_non_code(segment)
        if "event_name" in enabled:
            for match in _ADD_EVENT.finditer(segment):
                start = segment_offset + match.start("event")
                end = segment_offset + match.end("event")
                candidate = _line_candidate(
                    text,
                    start,
                    end,
                    f"__mutated_{match.group('event')}__",
                    "event_name",
                )
                if candidate:
                    candidates.append(candidate)
            for match in _PROPERTY_EVENT.finditer(masked):
                start = segment_offset + match.start("event")
                end = segment_offset + match.end("event")
                candidate = _line_candidate(text, start, end, f"__mutated_{match.group('event')}__", "event_name")
                if candidate:
                    candidates.append(candidate)

        if "event_handler" in enabled:
            for match in _EVENT_HANDLER_OPEN.finditer(segment):
                insertion = segment_offset + match.end("open")
                candidate = _line_candidate(
                    text,
                    insertion,
                    insertion,
                    " return;",
                    "event_handler",
                )
                if candidate:
                    candidates.append(candidate)

        if "api_call" in enabled:
            for match in _API_CALL_LINE.finditer(segment):
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    f'{match.group("indent")}/* mutation: external API call removed */',
                    "api_call",
                )
                if candidate:
                    candidates.append(candidate)

        if "string_literal" in enabled:
            for match in _HIGH_VALUE_STRING.finditer(segment):
                start = segment_offset + match.start("value")
                end = segment_offset + match.end("value")
                candidate = _line_candidate(
                    text,
                    start,
                    end,
                    f"__mutated_{match.group('value')}__",
                    "string_literal",
                )
                if candidate:
                    candidates.append(candidate)

        if "dom_update" in enabled:
            for match in _DOM_CALL.finditer(masked):
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    "/* mutation: DOM update removed */",
                    "dom_update",
                )
                if candidate:
                    candidates.append(candidate)
            for match in _DOM_ASSIGNMENT.finditer(masked):
                replacement = f'{segment[match.start("target"):match.end("target")]} = "";'
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    replacement,
                    "dom_update",
                )
                if candidate:
                    candidates.append(candidate)

        if "comparison" in enabled:
            for match in _COMPARISON.finditer(masked):
                token = match.group(0)
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    comparison_replacements[token],
                    "comparison",
                )
                if candidate:
                    candidates.append(candidate)

        if "boolean_literal" in enabled:
            for match in _BOOLEAN.finditer(masked):
                replacement = "false" if match.group(0) == "true" else "true"
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    replacement,
                    "boolean_literal",
                )
                if candidate:
                    candidates.append(candidate)

        if "numeric_literal" in enabled:
            for match in _NUMERIC_BOUNDARY.finditer(masked):
                before = masked[:match.start()]
                after = masked[match.end():]
                if before.rfind("[") > before.rfind("]") and "]" in after:
                    continue
                replacement = "1" if match.group(0) == "0" else "0"
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start(),
                    segment_offset + match.end(),
                    replacement,
                    "numeric_literal",
                )
                if candidate:
                    candidates.append(candidate)

        if "arithmetic" in enabled:
            for match in _ARITHMETIC.finditer(masked):
                operator = match.group("op")
                operator_offset = match.start("op")
                if operator == "-":
                    before = masked[:operator_offset]
                    after = masked[match.end("op"):]
                    inside_brackets = before.rfind("[") > before.rfind("]") and "]" in after
                    if inside_brackets:
                        continue
                candidate = _line_candidate(
                    text,
                    segment_offset + match.start("op"),
                    segment_offset + match.end("op"),
                    arithmetic_replacements[operator],
                    "arithmetic",
                )
                if candidate:
                    candidates.append(candidate)

    unique: dict[tuple[object, ...], MutationCandidate] = {}
    for candidate in candidates:
        key = (candidate.operator, candidate.line_start, candidate.original, candidate.mutated)
        unique.setdefault(key, candidate)
    priority = {name: index for index, name in enumerate(DEFAULT_OPERATORS)}
    return sorted(
        unique.values(),
        key=lambda item: (priority.get(item.operator, 99), item.line_start, item.mutated),
    )
