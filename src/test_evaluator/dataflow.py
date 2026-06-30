"""Conservative static data-flow extraction for browser test assertions.

This is intentionally a small interprocedural approximation, not a general
Python/JavaScript analyser. It identifies the high-value distinction needed by
the basic evaluator: whether an assertion observes a dispatched drag event's
DataTransfer payload, merely reads DOM text/attributes, or checks a constant.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass, field
import re

from .schemas import AssertionDataFlow, DataFlowFacts


_DT_CREATE_RE = re.compile(r"\bnew\s+DataTransfer\s*\(")
_DRAG_CREATE_RE = re.compile(r"\bnew\s+DragEvent\s*\(")
_DISPATCH_RE = re.compile(r"\.dispatchEvent\s*\(")
_DT_GET_RE = re.compile(r"\.getData\s*\(\s*['\"]([^'\"]+)['\"]")
_DT_SET_RE = re.compile(r"\.setData\s*\(\s*['\"]([^'\"]+)['\"]")
_DT_TYPE_RE = re.compile(r"\.types(?:\.includes\s*\(\s*['\"]([^'\"]+)['\"])?")
_DOM_TEXT_RE = re.compile(r"(?:\.innerText\b|\.textContent\b|\.value\b|\.text\b)")
_DOM_ATTRIBUTE_RE = re.compile(r"(?:\.getAttribute\s*\(|\.get_attribute\s*\()")


@dataclass
class _Flow:
    sources: set[str] = field(default_factory=set)
    data_transfer_read_keys: set[str] = field(default_factory=set)
    data_transfer_set_keys: set[str] = field(default_factory=set)
    drag_event_dispatched: bool = False

    def merge(self, other: "_Flow") -> "_Flow":
        return _Flow(
            sources=self.sources | other.sources,
            data_transfer_read_keys=(
                self.data_transfer_read_keys | other.data_transfer_read_keys
            ),
            data_transfer_set_keys=(
                self.data_transfer_set_keys | other.data_transfer_set_keys
            ),
            drag_event_dispatched=self.drag_event_dispatched or other.drag_event_dispatched,
        )


def _node_key(node: ast.AST) -> str:
    try:
        return ast.unparse(node)
    except Exception:
        return ""


def _script_text(call: ast.Call) -> str | None:
    if not call.args:
        return None
    first = call.args[0]
    if isinstance(first, ast.Constant) and isinstance(first.value, str):
        return first.value
    return None


def _script_flow(script: str) -> _Flow:
    read_keys = set(_DT_GET_RE.findall(script))
    read_keys.update(key for key in _DT_TYPE_RE.findall(script) if key)
    set_keys = set(_DT_SET_RE.findall(script))
    sources: set[str] = set()
    if read_keys or ".types" in script:
        sources.add("data_transfer")
    if _DRAG_CREATE_RE.search(script) or _DISPATCH_RE.search(script):
        sources.add("drag_event")
    if "document.querySelector" in script or "querySelector(" in script:
        if _DOM_ATTRIBUTE_RE.search(script):
            sources.add("dom_attribute")
        elif _DOM_TEXT_RE.search(script):
            sources.add("dom_text")
    return _Flow(
        sources=sources,
        data_transfer_read_keys=read_keys,
        data_transfer_set_keys=set_keys,
        drag_event_dispatched=bool(_DISPATCH_RE.search(script)),
    )


def _call_name(call: ast.Call) -> str:
    if isinstance(call.func, ast.Name):
        return call.func.id
    if isinstance(call.func, ast.Attribute):
        return call.func.attr
    return ""


def _expression_flow(
    node: ast.AST,
    assignments: dict[str, _Flow],
    function_returns: dict[str, _Flow],
) -> _Flow:
    key = _node_key(node)
    if key in assignments:
        return assignments[key]

    if isinstance(node, ast.Constant):
        return _Flow(sources={"constant"})
    if isinstance(node, (ast.Name, ast.Attribute)):
        if isinstance(node, ast.Attribute) and node.attr == "text":
            return _Flow(sources={"dom_text"})
        return assignments.get(key, _Flow())
    if isinstance(node, ast.Call):
        name = _call_name(node)
        if name == "execute_script":
            script = _script_text(node)
            return _script_flow(script) if script is not None else _Flow()
        if name == "get_attribute":
            attribute_name = (
                node.args[0].value
                if node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                else ""
            )
            source = (
                "dom_text"
                if attribute_name.casefold() in {"innerhtml", "innertext", "textcontent", "value"}
                else "dom_attribute"
            )
            return _Flow(sources={source})
        if name in {"is_displayed", "is_enabled", "is_selected"}:
            return _Flow(sources={"dom_attribute"})
        if name in function_returns:
            return function_returns[name]
        flow = _Flow()
        if isinstance(node.func, ast.Attribute):
            flow = flow.merge(
                _expression_flow(node.func.value, assignments, function_returns)
            )
        for argument in [*node.args, *(keyword.value for keyword in node.keywords)]:
            flow = flow.merge(_expression_flow(argument, assignments, function_returns))
        return flow

    flow = _Flow()
    for child in ast.iter_child_nodes(node):
        flow = flow.merge(_expression_flow(child, assignments, function_returns))
    if len(flow.sources) > 1 and "constant" in flow.sources:
        flow.sources.remove("constant")
    return flow


def _function_return_flows(tree: ast.AST) -> dict[str, _Flow]:
    result: dict[str, _Flow] = {}
    for function in (
        node
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    ):
        local_assignments: dict[str, _Flow] = {}
        for _ in range(3):
            for node in ast.walk(function):
                if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                    continue
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                flow = _expression_flow(value, local_assignments, result)
                for target in targets:
                    local_assignments[_node_key(target)] = flow
        return_flow = _Flow()
        for node in ast.walk(function):
            if isinstance(node, ast.Return) and node.value is not None:
                return_flow = return_flow.merge(
                    _expression_flow(node.value, local_assignments, result)
                )
        result[function.name] = return_flow
    return result


def _assignment_flows(tree: ast.AST, function_returns: dict[str, _Flow]) -> dict[str, _Flow]:
    assignments: dict[str, _Flow] = {}
    for _ in range(4):
        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            value = node.value
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            flow = _expression_flow(value, assignments, function_returns)
            for target in targets:
                assignments[_node_key(target)] = flow
    return assignments


def _classification(flow: _Flow) -> str:
    sources = flow.sources - {"constant"} if len(flow.sources) > 1 else flow.sources
    if "data_transfer" in sources:
        if flow.data_transfer_set_keys.intersection(flow.data_transfer_read_keys):
            return "self_fulfilled_event_payload"
        if flow.drag_event_dispatched and flow.data_transfer_read_keys:
            return "event_payload_observation"
        return "data_transfer_observation"
    if sources == {"dom_text"}:
        return "dom_observation"
    if sources == {"dom_attribute"}:
        return "element_attribute_proxy"
    if sources == {"constant"}:
        return "constant"
    if len(sources) > 1:
        return "mixed"
    return "unknown"


def extract_data_flow(tree: ast.AST) -> DataFlowFacts:
    """Extract assertion sources and drag-event payload flow from parsed Python."""

    function_returns = _function_return_flows(tree)
    assignments = _assignment_flows(tree, function_returns)
    script_calls = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and _call_name(node) == "execute_script"
    ]
    scripts = [script for call in script_calls if (script := _script_text(call)) is not None]

    assertions: list[AssertionDataFlow] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assert):
            continue
        flow = _expression_flow(node.test, assignments, function_returns)
        if not flow.sources:
            flow.sources.add("unknown")
        classification = _classification(flow)
        assertions.append(
            AssertionDataFlow(
                expression=_node_key(node.test),
                sources=sorted(flow.sources),  # type: ignore[arg-type]
                classification=classification,  # type: ignore[arg-type]
                data_transfer_read_keys=sorted(flow.data_transfer_read_keys),
                data_transfer_set_keys=sorted(flow.data_transfer_set_keys),
                drag_event_dispatched=flow.drag_event_dispatched,
            )
        )

    classifications = [assertion.classification for assertion in assertions]
    return DataFlowFacts(
        execute_script_count=len(script_calls),
        data_transfer_creation_count=sum(len(_DT_CREATE_RE.findall(script)) for script in scripts),
        drag_event_creation_count=sum(len(_DRAG_CREATE_RE.findall(script)) for script in scripts),
        drag_event_dispatch_count=sum(len(_DISPATCH_RE.findall(script)) for script in scripts),
        data_transfer_read_keys=sorted(
            {
                *[key for script in scripts for key in _DT_GET_RE.findall(script)],
                *[
                    key
                    for script in scripts
                    for key in _DT_TYPE_RE.findall(script)
                    if key
                ],
            }
        ),
        data_transfer_set_keys=sorted(
            {key for script in scripts for key in _DT_SET_RE.findall(script)}
        ),
        assertions=assertions,
        event_payload_assertion_count=classifications.count("event_payload_observation"),
        self_fulfilled_event_payload_assertion_count=classifications.count(
            "self_fulfilled_event_payload"
        ),
        dom_assertion_count=classifications.count("dom_observation"),
        element_attribute_proxy_assertion_count=classifications.count(
            "element_attribute_proxy"
        ),
        constant_assertion_count=classifications.count("constant"),
        unknown_assertion_count=classifications.count("unknown"),
    )
