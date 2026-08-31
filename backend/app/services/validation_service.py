"""Deterministic (non-AI) validation layers for web submissions.

Layer 1: static structure checks (HTML elements/attributes, CSS declarations, JS tokens)
Layer 2: automated behaviour tests executed in the sandboxed runtime (Node)
Layer 3: expected output comparison (handled by the execution service)

AI evaluation (layer 4) only runs after these, and never replaces them.
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Any, Optional

from app.core.config import settings
from app.schemas.execution import TestCase
from app.services import js_ast, render_judge, spec_interpolation, sql_judge
from app.services.code_execution_service import get_code_execution_service

logger = logging.getLogger(__name__)


@dataclass
class CheckOutcome:
    id: str
    label: str
    passed: bool
    concept: Optional[str] = None
    hint: Optional[str] = None
    detail: Optional[str] = None
    #: Hidden checks are withheld from Run and only graded on Submit, so a
    #: solution cannot be tuned against the cases it is shown.
    hidden: bool = False
    #: Zero-based index of the requirement this check grades, declared by the
    #: spec. `None` means the check grades no single requirement, so the UI must
    #: not attribute it to one. `requirement_indexes` carries the full list when
    #: one check covers several requirements.
    requirement_index: Optional[int] = None
    requirement_indexes: Optional[list[int]] = None
    #: File-level precondition (e.g. "the file parses"). Never consumes a
    #: requirement slot and never counts toward the met/total ratio.
    precondition: bool = False
    #: True when the spec explicitly declared the mapping above. Without it a
    #: client cannot tell "declared as unmapped" from "not annotated at all".
    requirement_mapped: bool = False
    #: Set only by rendered checks that deliberately did not run (test
    #: environments without a browser). Always accompanied by `passed=False`, so
    #: a check that could not execute can never be mistaken for a pass.
    skipped: bool = False
    #: The check is broken (an unresolved `{placeholder}` in its selector, say),
    #: so the learner's work was never examined. Always accompanied by
    #: `passed=False` and `precondition=True`: it fails closed, it is presented
    #: as *our* fault, and it never owns or fails a requirement.
    config_error: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "passed": self.passed,
            "concept": self.concept,
            "hint": self.hint,
            "detail": self.detail,
            "hidden": self.hidden,
            "requirement_index": self.requirement_index,
            "requirement_indexes": self.requirement_indexes,
            "precondition": self.precondition,
            "requirement_mapped": self.requirement_mapped,
            "skipped": self.skipped,
            "config_error": self.config_error,
        }


def _requirement_mapping(spec: dict[str, Any]) -> dict[str, Any]:
    """Normalises the requirement pointers a check/assertion spec declares."""
    mapped = "requirement_index" in spec or "requirement_indexes" in spec
    indexes = spec.get("requirement_indexes")
    if indexes is None:
        single = spec.get("requirement_index")
        indexes = [single] if isinstance(single, int) else None
    elif isinstance(indexes, list):
        indexes = [i for i in indexes if isinstance(i, int)] or None
    return {
        "requirement_index": indexes[0] if indexes else None,
        "requirement_indexes": list(indexes) if indexes else None,
        "precondition": bool(spec.get("precondition")),
        "requirement_mapped": mapped,
    }


class _DomCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[dict[str, Any]] = []
        self._stack: list[str] = []
        self._text_by_index: dict[int, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        entry = {
            "tag": tag.lower(),
            "attrs": {k.lower(): (v or "") for k, v in attrs},
            "parents": list(self._stack),
            "text": "",
            "index": len(self.tags),
        }
        self.tags.append(entry)
        if tag.lower() not in {"img", "br", "hr", "input", "meta", "link", "source"}:
            self._stack.append(tag.lower())

    def handle_endtag(self, tag: str) -> None:
        if self._stack and self._stack[-1] == tag.lower():
            self._stack.pop()

    def handle_data(self, data: str) -> None:
        if not data.strip():
            return
        for entry in reversed(self.tags):
            if entry["tag"] in self._stack or (self._stack and entry["tag"] == self._stack[-1]):
                entry["text"] += data.strip() + " "
                break
        else:
            if self.tags:
                self.tags[-1]["text"] += data.strip() + " "


def parse_dom(html: str) -> list[dict[str, Any]]:
    collector = _DomCollector()
    collector.feed(html or "")
    collector.close()
    return collector.tags


def _matches_selector(entry: dict[str, Any], selector: str) -> bool:
    """Supports `tag`, `.class`, `#id`, `tag.class`, `tag#id`, `[attr]`."""
    selector = selector.strip()
    attr_match = re.fullmatch(r"\[([\w-]+)\]", selector)
    if attr_match:
        return attr_match.group(1).lower() in entry["attrs"]

    match = re.fullmatch(r"([a-zA-Z0-9]*)(?:\.([\w-]+))?(?:#([\w-]+))?", selector)
    if not match:
        return False
    tag, klass, ident = match.groups()
    if tag and entry["tag"] != tag.lower():
        return False
    if klass:
        classes = entry["attrs"].get("class", "").split()
        if klass not in classes:
            return False
    if ident and entry["attrs"].get("id") != ident:
        return False
    return bool(tag or klass or ident)


def query(dom: list[dict[str, Any]], selector: str) -> list[dict[str, Any]]:
    return [entry for entry in dom if _matches_selector(entry, selector)]


CSS_RULE_RE = re.compile(r"([^{}]+)\{([^{}]*)\}", re.DOTALL)


def parse_css(css: str) -> list[tuple[list[str], dict[str, str]]]:
    """Flat parse of top-level rules; at-rule bodies are also scanned."""
    rules: list[tuple[list[str], dict[str, str]]] = []
    text = re.sub(r"/\*.*?\*/", "", css or "", flags=re.DOTALL)
    for raw_selector, body in CSS_RULE_RE.findall(text):
        selector_text = raw_selector.strip()
        if selector_text.startswith("@"):
            continue
        selectors = [s.strip() for s in selector_text.split(",") if s.strip()]
        declarations: dict[str, str] = {}
        for declaration in body.split(";"):
            if ":" not in declaration:
                continue
            prop, value = declaration.split(":", 1)
            declarations[prop.strip().lower()] = value.strip().lower()
        if selectors:
            rules.append((selectors, declarations))
    return rules


def _selector_mentions(selector_text: str, needle: str) -> bool:
    """True when `needle` appears in `selector_text` as a whole token.

    Substring matching let `.plan-cardxyz` satisfy a check aimed at `.plan-card`,
    and let a `.card` class satisfy a check aimed at the `card` element, so both
    ends of the needle must fall on an identifier boundary.
    """
    needle = needle.strip().lower()
    if not needle:
        return False
    lead = r"(?<![\w.#-])" if needle[0] not in ".#" else r"(?<![\w-])"
    pattern = lead + re.escape(needle) + r"(?![\w-])"
    return bool(re.search(pattern, selector_text.lower()))


def _value_matches(
    value: str,
    value_pattern: Optional[str] = None,
    value_in: Optional[list[str]] = None,
) -> bool:
    """A declared value satisfies the (optional) constraints the check declares.

    With neither constraint the check asserts mere presence, which is still the
    right assertion when the requirement really is "declare this property".
    """
    normalised = " ".join((value or "").split()).lower()
    if value_in is not None:
        accepted = {" ".join(str(v).split()).lower() for v in value_in}
        if normalised not in accepted:
            return False
    if value_pattern is not None and not re.search(value_pattern, normalised, re.IGNORECASE):
        return False
    return True


def css_has_property(
    css: str,
    prop: str,
    selector: Optional[str] = None,
    value_pattern: Optional[str] = None,
    value_in: Optional[list[str]] = None,
) -> bool:
    prop = prop.lower()
    for selectors, declarations in parse_css(css):
        if prop not in declarations:
            continue
        if selector is not None and not any(_selector_mentions(s, selector) for s in selectors):
            continue
        if not _value_matches(declarations[prop], value_pattern, value_in):
            continue
        return True
    return False


JS_CHECK_TYPES = {
    "js_syntax",
    "js_calls",
    "js_async_function",
    "js_try_catch_await",
    "js_catch_handles",
    "js_ok_before_parse",
    "js_error_feedback",
    "js_loading_sequence",
    "js_not_trivial",
    "js_no_unreachable",
}


@dataclass
class _JsVerdict:
    passed: bool
    detail: Optional[str] = None
    hint: Optional[str] = None


def _named_functions(ast: dict[str, Any]) -> list[tuple[Optional[str], dict[str, Any]]]:
    """Function declarations plus functions bound to a variable/property name."""
    found: list[tuple[Optional[str], dict[str, Any]]] = []
    for node in js_ast.walk(ast):
        kind = node.get("type")
        if kind == "FunctionDeclaration":
            found.append(((node.get("id") or {}).get("name"), node))
        elif kind == "VariableDeclarator":
            init = node.get("init") or {}
            if init.get("type") in {"FunctionExpression", "ArrowFunctionExpression"}:
                found.append(((node.get("id") or {}).get("name"), init))
        elif kind == "AssignmentExpression":
            right = node.get("right") or {}
            if right.get("type") in {"FunctionExpression", "ArrowFunctionExpression"}:
                found.append((js_ast.dotted_name(node.get("left")).rsplit(".", 1)[-1], right))
    return found


def _request_awaits(scope: Any, parse_callee: str) -> list[dict[str, Any]]:
    """Awaited calls that are not the body-parsing call itself."""
    requests = []
    for node in js_ast.awaits(scope):
        argument = node.get("argument") or {}
        if argument.get("type") == "CallExpression" and js_ast.call_matches(argument, parse_callee):
            continue
        requests.append(node)
    return requests


def _tests_response_status(test: Any) -> bool:
    for member in js_ast.nodes_of_type(test, "MemberExpression"):
        if member.get("computed"):
            continue
        prop = (member.get("property") or {}).get("name")
        if prop in {"ok", "status", "statusText"}:
            return True
    return False


def _branch_handles_error(branch: Any) -> bool:
    if branch is None:
        return False
    if js_ast.nodes_of_type(branch, "ThrowStatement", "ReturnStatement"):
        return True
    return js_ast.has_dom_write(branch)


def _write_targets(root: Any) -> set[str]:
    """Dotted names of the DOM nodes/properties a subtree writes to."""
    targets: set[str] = set()
    for node in js_ast.walk(root):
        if not js_ast.is_dom_write(node):
            continue
        if node.get("type") == "AssignmentExpression":
            targets.add(js_ast.dotted_name(node.get("left")))
        else:
            targets.add(js_ast.dotted_name(node.get("callee")))
    return {t for t in targets if t}


def _dom_writes_by_function(ast: dict[str, Any]) -> dict[str, set[str]]:
    """For each named function, the DOM targets calling it eventually writes to.

    Source position alone cannot answer "did anything repaint after the request?"
    once the rendering lives in a helper: a `renderCards()` declared above the
    loader writes the DOM at an offset *before* the await, however late it is
    actually called. Resolving calls transitively lets a positional check follow
    the call instead of the text.
    """
    direct: dict[str, set[str]] = {}
    callees: dict[str, set[str]] = {}
    for name, fn in _named_functions(ast):
        if not name:
            continue
        body = fn.get("body")
        direct.setdefault(name, set()).update(_write_targets(body))
        callees.setdefault(name, set()).update(
            js_ast.dotted_name(call.get("callee")).rsplit(".", 1)[-1]
            for call in js_ast.nodes_of_type(body, "CallExpression")
        )

    resolved: dict[str, set[str]] = {}

    def resolve(name: str, seen: frozenset[str]) -> set[str]:
        if name in resolved:
            return resolved[name]
        if name in seen:  # recursion: stop rather than loop forever
            return set()
        writes = set(direct.get(name, ()))
        for callee in callees.get(name, ()):
            if callee in direct:
                writes |= resolve(callee, seen | {name})
        resolved[name] = writes
        return writes

    for name in list(direct):
        resolve(name, frozenset())
    return resolved


def _js_syntax_verdict(parse: js_ast.ParseResult, target: str) -> _JsVerdict:
    if parse.tooling_error:
        return _JsVerdict(False, "analysis unavailable", parse.message)
    location = f" ({parse.location})" if parse.location else ""
    return _JsVerdict(False, f"{target} does not parse", f"{parse.message}{location}")


def _run_js_check(check: dict[str, Any], content: str, target: str) -> _JsVerdict:
    """Every JS check is AST-driven and fails closed when parsing is impossible."""
    check_type = check.get("type")
    parse = js_ast.parse_js(content or "", target or "script.js")
    if not parse.valid or parse.ast is None:
        return _js_syntax_verdict(parse, target)

    ast = parse.ast

    if check_type == "js_syntax":
        return _JsVerdict(True, f"{target} parses as valid JavaScript")

    if check_type == "js_calls":
        callee = check.get("callee", "")
        minimum = int(check.get("min_count", 1))
        found = js_ast.calls_to(ast, callee)
        return _JsVerdict(
            len(found) >= minimum,
            f"{len(found)} call(s) to {callee}, need {minimum}",
        )

    if check_type == "js_async_function":
        name = check.get("name")
        for fn_name, fn in _named_functions(ast):
            if name and fn_name != name:
                continue
            if not fn.get("async"):
                continue
            if check.get("require_await", True) and not js_ast.awaits(fn.get("body")):
                continue
            return _JsVerdict(True, f"async function {fn_name or '(anonymous)'} awaits its work")
        return _JsVerdict(
            False,
            f"no async function{f' named {name}' if name else ''} that awaits was found",
        )

    if check_type == "js_try_catch_await":
        callee = check.get("callee")
        require_binding = bool(check.get("require_binding", True))
        reason = "no try/catch wraps the awaited call"
        for try_node in js_ast.nodes_of_type(ast, "TryStatement"):
            block = try_node.get("block")
            candidates = js_ast.awaits(block)
            if callee:
                candidates = [
                    a
                    for a in candidates
                    if js_ast.call_matches(a.get("argument") or {}, callee)
                ]
            if not candidates:
                continue
            handler = try_node.get("handler")
            if handler is None:
                reason = "the try block has no catch clause"
                continue
            if require_binding and handler.get("param") is None:
                reason = "catch does not bind the error (write `catch (error)`)"
                continue
            return _JsVerdict(True, "the awaited call runs inside try/catch")
        return _JsVerdict(False, reason)

    if check_type == "js_catch_handles":
        clauses = js_ast.nodes_of_type(ast, "CatchClause")
        if not clauses:
            return _JsVerdict(False, "no catch clause exists")
        reason = "the catch block does not handle the error"
        for clause in clauses:
            body = clause.get("body") or {}
            statements = body.get("body") or []
            if not statements:
                reason = "the catch block is empty"
                continue
            param_name = (clause.get("param") or {}).get("name")
            uses_binding = bool(param_name) and param_name in js_ast.identifier_names(body)
            rethrows = bool(js_ast.nodes_of_type(body, "ThrowStatement"))
            writes_dom = js_ast.has_dom_write(body)
            if check.get("require_dom_write") and not writes_dom:
                reason = "the catch block never writes the error to the page"
                continue
            if uses_binding or rethrows or writes_dom:
                return _JsVerdict(True, "the catch block acts on the error")
            reason = "the catch block ignores the caught error"
        return _JsVerdict(False, reason)

    if check_type == "js_ok_before_parse":
        parse_callee = check.get("parse_callee", ".json")
        parse_calls = js_ast.calls_to(ast, parse_callee)
        if not parse_calls:
            return _JsVerdict(False, f"the response body is never parsed with {parse_callee}")
        reason = "the response body is parsed before the status is checked"
        for call in parse_calls:
            scope = js_ast.scope_of(ast, call)
            requests = [
                a for a in _request_awaits(scope, parse_callee) if js_ast.span(a)[1] <= js_ast.span(call)[0]
            ]
            if not requests:
                reason = "the parsed body does not follow an awaited request"
                continue
            request_end = min(js_ast.span(r)[1] for r in requests)
            for branch in js_ast.nodes_of_type(scope, "IfStatement"):
                test = branch.get("test")
                if not _tests_response_status(test):
                    continue
                test_start, test_end = js_ast.span(test)
                if test_start < request_end or test_end > js_ast.span(call)[0]:
                    continue
                error_branch = (
                    branch.get("alternate")
                    if js_ast.contains(branch.get("consequent") or {}, call)
                    else branch.get("consequent")
                )
                if not _branch_handles_error(error_branch):
                    reason = "the non-ok branch does not throw or handle the failure"
                    continue
                return _JsVerdict(True, "status is checked and handled before the body is parsed")
            if reason.startswith("the response body is parsed"):
                reason = "no response.ok / status check runs between the request and the parse"
        return _JsVerdict(False, reason)

    if check_type == "js_error_feedback":
        for clause in js_ast.nodes_of_type(ast, "CatchClause"):
            if js_ast.has_dom_write(clause.get("body")):
                return _JsVerdict(True, "the catch block renders an error state")
        for branch in js_ast.nodes_of_type(ast, "IfStatement"):
            if not _tests_response_status(branch.get("test")):
                continue
            for side in ("consequent", "alternate"):
                if js_ast.has_dom_write(branch.get(side)):
                    return _JsVerdict(True, "the failure branch renders an error state")
        return _JsVerdict(
            False,
            "the failure path never writes to the DOM (logging to the console is not a UI)",
        )

    if check_type == "js_loading_sequence":
        parse_callee = check.get("parse_callee", ".json")
        requests = _request_awaits(ast, parse_callee)
        if not requests:
            return _JsVerdict(False, "no awaited request was found")
        request_start = min(js_ast.span(r)[0] for r in requests)
        request_end = max(js_ast.span(r)[1] for r in requests)
        before: set[str] = set()
        after: set[str] = set()
        writers = _dom_writes_by_function(ast)
        for node in js_ast.walk(ast):
            targets: set[str] = set()
            if js_ast.is_dom_write(node):
                target_name = (
                    js_ast.dotted_name(node.get("left"))
                    if node.get("type") == "AssignmentExpression"
                    else js_ast.dotted_name(node.get("callee"))
                )
                if target_name:
                    targets = {target_name}
            elif node.get("type") == "CallExpression":
                # A call to one of the learner's own render helpers counts as the
                # repaint it performs, at the position of the *call*. Without this
                # an extracted `renderCards()` — better code than an inline blob —
                # was reported as "the loading state is never cleared".
                callee = js_ast.dotted_name(node.get("callee")).rsplit(".", 1)[-1]
                targets = writers.get(callee, set())
            if not targets:
                continue
            start, _ = js_ast.span(node)
            if start < request_start:
                before |= targets
            elif start >= request_end:
                after |= targets
        shared = {b.rsplit(".", 1)[0] for b in before} & {a.rsplit(".", 1)[0] for a in after}
        if not before:
            return _JsVerdict(False, "nothing renders a loading state before the request starts")
        if not shared:
            return _JsVerdict(False, "the loading state is never cleared after the request settles")
        return _JsVerdict(True, "a loading state is rendered before the request and cleared after")

    if check_type == "js_not_trivial":
        name = check.get("name")
        candidates = [(n, fn) for n, fn in _named_functions(ast) if not name or n == name]
        if not candidates:
            return _JsVerdict(False, f"no function{f' named {name}' if name else ''} was found")
        for fn_name, fn in candidates:
            if js_ast.statement_is_trivial(fn.get("body")):
                return _JsVerdict(
                    False,
                    f"{fn_name or 'the function'} has no implementation "
                    "(empty body, comments only, or a constant return)",
                )
        return _JsVerdict(True, f"{len(candidates)} function(s) have real bodies")

    if check_type == "js_no_unreachable":
        dead = js_ast.unreachable_statements(ast)
        if dead:
            lines = sorted({js_ast.line_of(n) for n in dead if js_ast.line_of(n)})
            return _JsVerdict(
                False,
                "unreachable code after an unconditional return/throw"
                + (f" (line {lines[0]})" if lines else ""),
            )
        return _JsVerdict(True, "no unreachable statements")

    return _JsVerdict(False, f"unknown check type '{check_type}'")


def _strip_comments(source: str) -> str:
    """Removes HTML, block and line comments before a textual check reads the file.

    Commented-out markup renders nothing, so it must not satisfy a positive
    `regex` check — and, symmetrically, must not shield a `not_regex`
    prohibition. An unterminated `<!--` comments out the rest of the file in a
    real browser, so it is dropped here too.
    """
    text = re.sub(r"<!--.*?-->", "", source or "", flags=re.DOTALL)
    text = re.sub(r"<!--.*\Z", "", text, flags=re.DOTALL)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return re.sub(r"(?<!:)//[^\n]*", "", text)


# --------------------------------------------------------------------------
# Static check runner
# --------------------------------------------------------------------------


def _render_bundle(
    files: dict[str, str], render_files: Optional[dict[str, str]]
) -> dict[str, str]:
    """The page the render sandbox loads: provided files, submission on top.

    The learner's own files always win — the submission is what is being graded.
    One definition, shared by grading and by the debug report, so the report can
    never describe a bundle other than the one that was rendered.
    """
    if not render_files:
        return files
    return {**render_files, **files}


def render_assembly_debug(
    files: dict[str, str],
    checks: list[dict[str, Any]],
    render_files: Optional[dict[str, str]] = None,
) -> Optional[dict[str, Any]]:
    """Development-only description of the assembled page, else None.

    Returns None — so the caller omits the field entirely rather than shipping an
    empty one — unless `RENDER_ASSEMBLY_DEBUG` is set and the environment is not
    production, and unless the run actually had rendered checks to assemble for.
    """
    if not settings.render_assembly_debug_enabled:
        return None
    batch = [
        (index, check)
        for index, check in enumerate(checks)
        if check.get("type") in render_judge.RENDER_CHECK_TYPES
    ]
    if not batch:
        return None
    return render_judge.assembly_report(_render_bundle(files, render_files), batch)


#: Every check field whose value is handed to a selector engine — the browser's
#: `querySelectorAll`/`closest` or this module's own `query`/`css_has_property`.
#: An unresolved placeholder in any of them is a validator bug, so they are all
#: guarded in one place before a check runs.
_SELECTOR_FIELDS = ("selector", "parent", "within", "over")

#: What a learner is told when a check is broken. Deliberately does not describe
#: the fix in learner terms, because there is nothing for them to fix.
_CONFIG_ERROR_HINT = (
    "This is a fault in the ticket's checks, not in your code. It has been logged "
    "for the SprintForge team; nothing you write can satisfy this check until the "
    "spec is repaired."
)


def _configuration_error_outcome(
    index: int, check: dict[str, Any], label: str, reason: str
) -> CheckOutcome:
    """A broken check, reported as our bug rather than the learner's failure.

    Three things make that unmistakable rather than a matter of wording:

    * `config_error=True`, which the UI renders as a configuration fault in its
      own colour instead of a red cross;
    * `precondition=True` with no requirement pointers, so the check cannot mark
      any requirement unmet and is excluded from the met/total ratio;
    * an ERROR log line naming the check id, so it is visible server-side
      without a learner having to report it.

    It still does not pass. A check that never examined the submission must not
    be credited, exactly as an unavailable browser is not.
    """
    detail = reason if reason.startswith("validator configuration error") else (
        f"validator configuration error: {reason}"
    )
    logger.error(
        "validator configuration error on check %r (%s): %s",
        check.get("id", f"check_{index + 1}"),
        check.get("type"),
        reason,
    )
    return CheckOutcome(
        id=check.get("id", f"check_{index + 1}"),
        label=label,
        passed=False,
        concept=check.get("concept"),
        hint=_CONFIG_ERROR_HINT,
        detail=detail,
        hidden=bool(check.get("hidden")),
        config_error=True,
        precondition=True,
        requirement_mapped=True,
    )


def run_static_checks(
    files: dict[str, str],
    checks: list[dict[str, Any]],
    include_hidden: bool = True,
    render_files: Optional[dict[str, str]] = None,
) -> list[CheckOutcome]:
    """Runs structural checks. With `include_hidden=False` the hidden ones are
    skipped entirely, which is what the Run action uses.

    Two file maps, deliberately kept apart:

    * `files` is the submission being graded — the files the learner may edit in
      this task. Every textual and AST check reads its target out of this map and
      out of nothing else, so a check can only ever be satisfied by work that
      belongs to this task. Widening it would let a check scoped to a filename
      match a *different* task's file and hand out credit for work the learner
      did not do here.
    * `render_files` is the runnable page: the same submission plus the
      read-only documents the task provides (an `index.html` a CSS-only task is
      not allowed to edit, for instance). It exists because a stylesheet has no
      observable behaviour on its own — a rendered check has to load a document.
      It is passed to the render judge and to no other check.

    When `render_files` is omitted the submission is rendered as-is, which is the
    behaviour every caller had before assembly existed.
    """
    dom_cache: dict[str, list[dict[str, Any]]] = {}
    outcomes: list[CheckOutcome] = []

    # Rendered checks are graded first, and in one batch: everything sharing an
    # entry document and viewport costs a single page load rather than a browser
    # round trip per check.
    render_batch = [
        (index, check)
        for index, check in enumerate(checks)
        if check.get("type") in render_judge.RENDER_CHECK_TYPES
        and (include_hidden or not check.get("hidden"))
        # A check with a leaked placeholder is reported as a configuration error
        # below; there is no point loading a page to query a selector that cannot
        # be parsed.
        and not any(spec_interpolation.selector_leak(check.get(f)) for f in _SELECTOR_FIELDS)
    ]
    render_verdicts = render_judge.run_render_checks(
        _render_bundle(files, render_files), render_batch
    )

    for index, check in enumerate(checks):
        if check.get("hidden") and not include_hidden:
            continue
        check_type = check.get("type")
        target = check.get("file", "")
        content = files.get(target, "") if target else ""
        label = check.get("label", f"Check {index + 1}")
        passed = False
        detail: Optional[str] = None
        hint = check.get("hint")
        skipped = False
        config_error = False

        # Before anything reads a selector, refuse an uninterpolated one. Every
        # selector-bearing check type funnels through here, so this cannot be
        # bypassed by adding another one.
        leak = next(
            (
                spec_interpolation.selector_leak(check.get(field))
                for field in _SELECTOR_FIELDS
                if spec_interpolation.selector_leak(check.get(field))
            ),
            None,
        )
        if leak:
            outcomes.append(_configuration_error_outcome(index, check, label, leak))
            continue

        if check_type in render_judge.RENDER_CHECK_TYPES:
            verdict = render_verdicts.get(index)
            if verdict is None:
                passed = False
                detail = "this rendered check did not run"
            else:
                passed = verdict.passed
                detail = verdict.detail
                skipped = verdict.skipped
                if verdict.config_error:
                    outcomes.append(
                        _configuration_error_outcome(index, check, label, verdict.detail or "")
                    )
                    continue
                if not passed and verdict.hint:
                    hint = verdict.hint

        elif check_type in JS_CHECK_TYPES:
            verdict = _run_js_check(check, content, target)
            passed = verdict.passed
            detail = verdict.detail
            if not passed and verdict.hint:
                hint = verdict.hint

        elif check_type == "sql_query":
            # The learner's SQL is *executed* against the question's fixture
            # datasets and the result set compared against the reference query's.
            # A ticket graded this way cannot be satisfied by a query that
            # merely mentions the right keywords, and cannot fail a correct
            # query written in a different but equivalent style.
            spec = check.get("spec") or {}
            try:
                grade = sql_judge.grade(content, spec, include_hidden=include_hidden)
            except (sqlite3.Error, sql_judge.SqlSpecError) as exc:
                passed = False
                detail = f"this question's fixtures are broken: {exc}"
            else:
                passed = grade.passed
                if grade.rejection is not None:
                    detail = grade.rejection
                else:
                    failed = [o for o in grade.outcomes if not o.passed]
                    if failed:
                        first = failed[0]
                        detail = f"{first.dataset}: {first.detail}"
                        if len(failed) > 1:
                            detail += f" (and {len(failed) - 1} more dataset(s) disagree)"
                    else:
                        detail = (
                            f"correct on all {len(grade.outcomes)} fixture dataset(s)"
                        )

        elif check_type == "html_element":
            if target not in dom_cache:
                dom_cache[target] = parse_dom(content)
            found = query(dom_cache[target], check.get("selector", ""))
            min_count = int(check.get("min_count", 1))
            passed = len(found) >= min_count
            detail = f"found {len(found)}, need {min_count}"
            if passed and check.get("with_attributes"):
                required = {k.lower(): v for k, v in check["with_attributes"].items()}
                passed = any(
                    all(
                        (
                            entry["attrs"].get(attr, "") != ""
                            if expected in (None, "", "*")
                            else str(expected).lower() in entry["attrs"].get(attr, "").lower()
                        )
                        for attr, expected in required.items()
                    )
                    for entry in found
                )
                if not passed:
                    detail = f"required attributes missing: {', '.join(required)}"
            if passed and check.get("non_empty_text"):
                passed = any(entry["text"].strip() for entry in found)
                if not passed:
                    detail = "element exists but has no text content"

        elif check_type == "html_nested":
            if target not in dom_cache:
                dom_cache[target] = parse_dom(content)
            child = check.get("selector", "")
            parent = check.get("parent", "")
            found = query(dom_cache[target], child)
            passed = any(parent.strip().lower() in entry["parents"] for entry in found)
            detail = f"<{child}> inside <{parent}>"

        elif check_type == "css_property":
            passed = css_has_property(
                content,
                check.get("property", ""),
                check.get("selector"),
                check.get("value_pattern"),
                check.get("value_in"),
            )
            detail = f"{check.get('property')} on {check.get('selector') or 'any selector'}"
            constraint = check.get("value_pattern") or (
                " | ".join(str(v) for v in check["value_in"]) if check.get("value_in") else None
            )
            if constraint:
                detail += f" matching {constraint}"

        elif check_type == "css_at_rule":
            passed = bool(re.search(check.get("pattern", "@media"), content or "", re.IGNORECASE))
            detail = check.get("pattern")

        elif check_type == "regex":
            source = content if check.get("keep_comments") else _strip_comments(content)
            flags = re.IGNORECASE if check.get("ignore_case") else 0
            passed = bool(re.search(check.get("pattern", ""), source, flags | re.DOTALL))
            detail = check.get("pattern")

        elif check_type == "not_regex":
            source = content if check.get("keep_comments") else _strip_comments(content)
            passed = not re.search(check.get("pattern", ""), source, re.DOTALL)
            detail = f"must not contain {check.get('pattern')}"

        elif check_type == "non_empty":
            passed = bool((content or "").strip())
            detail = f"{target} must not be empty"

        elif check_type == "min_lines":
            passed = len([l for l in (content or "").splitlines() if l.strip()]) >= int(
                check.get("count", 1)
            )

        else:
            passed = False
            detail = f"unknown check type '{check_type}'"

        outcomes.append(
            CheckOutcome(
                id=check.get("id", f"check_{index + 1}"),
                label=label,
                passed=passed,
                concept=check.get("concept"),
                hint=hint,
                detail=detail,
                hidden=bool(check.get("hidden")),
                skipped=skipped,
                config_error=config_error,
                **_requirement_mapping(check),
            )
        )
    return outcomes


# --------------------------------------------------------------------------
# Layer 2: behaviour tests for JS/React executed through the sandbox
# --------------------------------------------------------------------------

#: Wall-clock budgets for the in-runtime harness. They are all comfortably
#: below the sandbox process timeout, so a hang inside the learner's async work
#: is reported as a graded failure rather than as a dead subprocess.
BEHAVIOUR_DRAIN_BUDGET_MS = 1500
BEHAVIOUR_ASSERTION_BUDGET_MS = 5000

#: Used when a spec author forgot a hint, so a failing row is never unexplained.
_DEFAULT_BEHAVIOUR_HINT = (
    "This scenario is run against your code with the network controlled by the "
    "grader. Read the detail line for what actually happened."
)

JS_HARNESS = """
// Assertion harness. The learner's file is wrapped (see `wrap_as`) and run once
// per scenario; the harness owns the clock, the pending-work bookkeeping and the
// error capture so that:
//   * unawaited async work is drained before an assertion is evaluated,
//   * a throw anywhere in the learner's code (including inside a catch block or
//     a timer callback) is recorded instead of silently killing the process,
//   * all waiting is bounded, so `while (true)`, `setInterval` and promises that
//     never settle end as failures rather than as a hung grader.
const __results = [];
const __runtimeErrors = [];
const __realSetTimeout = globalThis.setTimeout;
const __realClearTimeout = globalThis.clearTimeout;
const __DRAIN_BUDGET_MS = __DRAIN_BUDGET_MS_VALUE__;
const __ASSERTION_BUDGET_MS = __ASSERTION_BUDGET_MS_VALUE__;
const __DRAIN_MAX_ROUNDS = 200;
const __MICROTASK_FLUSHES = 25;
const __TIMER_CAP_MS = 25;
const __MAX_INTERVAL_TICKS = 5;

// Bumped by the prelude whenever harness-owned async work happens (a request is
// issued, a body is parsed, the DOM is written). Quiescence = no new activity
// and no pending tracked work across consecutive drain rounds.
let __activity = 0;
const __pending = new Set();

function __describeError(e) {
  if (e && e.message) return String(e.name ? e.name + ': ' + e.message : e.message);
  return String(e);
}

function __recordError(e) {
  const text = __describeError(e);
  if (text && __runtimeErrors.indexOf(text) === -1) __runtimeErrors.push(text);
}

function __resetErrors() {
  __runtimeErrors.length = 0;
}

function __note() {
  __activity++;
}

function __track(value) {
  if (value && typeof value.then === 'function') {
    __note();
    const settled = Promise.resolve(value).then(
      () => {},
      (e) => { __recordError(e); }
    );
    __pending.add(settled);
    settled.then(() => __pending.delete(settled));
  }
  return value;
}

// Learner delays are compressed and interval callbacks are capped, so a polling
// loop cannot outlast the drain budget.
globalThis.setTimeout = function (fn, delay) {
  const args = Array.prototype.slice.call(arguments, 2);
  const wait = Math.min(Math.max(Number(delay) || 0, 0), __TIMER_CAP_MS);
  let release;
  const done = new Promise((resolve) => { release = resolve; });
  __pending.add(done);
  done.then(() => __pending.delete(done));
  return __realSetTimeout(() => {
    __note();
    try {
      if (typeof fn === 'function') __track(fn.apply(null, args));
    } catch (e) {
      __recordError(e);
    }
    release();
  }, wait);
};
globalThis.clearTimeout = (id) => __realClearTimeout(id);
globalThis.setInterval = function (fn, delay) {
  const handle = { cancelled: false, ticks: 0 };
  const step = () => {
    if (handle.cancelled || handle.ticks >= __MAX_INTERVAL_TICKS) return;
    handle.ticks++;
    globalThis.setTimeout(() => {
      try {
        if (typeof fn === 'function') __track(fn());
      } catch (e) {
        __recordError(e);
      }
      step();
    }, delay);
  };
  step();
  return handle;
};
globalThis.clearInterval = (handle) => {
  if (handle && typeof handle === 'object') handle.cancelled = true;
};

if (typeof process !== 'undefined' && typeof process.on === 'function') {
  // A floating promise that rejects (the common `loadMovies();` at the end of a
  // file) must be visible to the grader, not fatal to it.
  process.on('unhandledRejection', (e) => __recordError(e));
  process.on('uncaughtException', (e) => __recordError(e));
}

// Drains the learner's pending asynchronous work. Returns null when the runtime
// went quiet, or a reason string when a bound was hit.
async function __drain() {
  const deadline = Date.now() + __DRAIN_BUDGET_MS;
  let stableRounds = 0;
  for (let round = 0; round < __DRAIN_MAX_ROUNDS; round++) {
    const activityBefore = __activity;
    for (let i = 0; i < __MICROTASK_FLUSHES; i++) await Promise.resolve();
    // One macrotask turn: lets timers fire and unhandled rejections surface.
    await new Promise((resolve) => __realSetTimeout(resolve, 0));
    if (__pending.size) {
      const remaining = Math.max(0, deadline - Date.now());
      await Promise.race([
        Promise.all(Array.from(__pending)),
        new Promise((resolve) => __realSetTimeout(resolve, remaining)),
      ]);
    }
    if (Date.now() >= deadline) return 'timeout';
    if (__activity === activityBefore && __pending.size === 0) {
      stableRounds++;
      if (stableRounds >= 2) return null;
    } else {
      stableRounds = 0;
    }
  }
  return 'rounds';
}

// Runs the learner's wrapped file, then waits for whatever it started. A throw
// is recorded and re-thrown so the assertion can report it.
async function __runUserMain(fn) {
  let result;
  let thrown = null;
  try {
    result = await fn();
  } catch (e) {
    __recordError(e);
    thrown = e;
  }
  const bound = await __drain();
  if (bound === 'timeout') {
    throw new Error(
      'your asynchronous work never settled — the grader stopped waiting after ' +
        __DRAIN_BUDGET_MS +
        'ms'
    );
  }
  if (bound === 'rounds') {
    throw new Error('your code kept scheduling asynchronous work and never settled');
  }
  if (thrown) throw thrown;
  return result;
}

// An assertion passes only on an explicitly truthy, non-string value. A string
// return is treated as a failure whose text explains what happened, and
// undefined/null never pass (fail closed).
async function __assert(name, fn) {
  let timer = null;
  try {
    const timeout = new Promise((resolve) => {
      timer = __realSetTimeout(() => resolve('__HARNESS_TIMEOUT__'), __ASSERTION_BUDGET_MS);
    });
    const value = await Promise.race([Promise.resolve().then(fn), timeout]);
    if (value === '__HARNESS_TIMEOUT__') {
      __results.push({
        name,
        passed: false,
        error:
          'this test hit the ' + __ASSERTION_BUDGET_MS + 'ms time limit — your code did not finish',
      });
      return;
    }
    if (typeof value === 'string') {
      __results.push({ name, passed: false, error: value });
      return;
    }
    const passed = value === true || (Boolean(value) && typeof value !== 'string');
    __results.push({
      name,
      passed,
      error: passed ? null : 'the expected behaviour was not observed',
    });
  } catch (e) {
    __results.push({ name, passed: false, error: __describeError(e) });
  } finally {
    if (timer !== null) __realClearTimeout(timer);
  }
}
"""


async def run_behaviour_tests(
    user_code: str,
    assertions: list[dict[str, Any]],
    prelude: str = "",
    wrap_as: Optional[str] = None,
    include_hidden: bool = True,
) -> list[CheckOutcome]:
    """Execute JS assertions against the learner's code in the sandbox runtime.

    `wrap_as` puts the learner's whole file inside an async function of that
    name so the harness can run it repeatedly, once per injected scenario.

    With `include_hidden=False` hidden assertions are dropped before the harness
    is built, so their expressions never reach the learner's runtime at all.
    """
    if not include_hidden:
        assertions = [a for a in assertions if not a.get("hidden")]
    if not assertions:
        return []

    # Never hand syntactically invalid code to the runtime: report the parse
    # error instead of a confusing crash, and never pass by accident.
    parsed = js_ast.parse_js(user_code or "", "script.js")
    if not parsed.valid:
        location = f" ({parsed.location})" if parsed.location else ""
        return [
            CheckOutcome(
                id="behaviour_syntax",
                label="Behaviour tests could not run: your code does not parse",
                passed=False,
                hint=f"{parsed.message}{location}",
                concept="syntax",
                precondition=True,
                requirement_mapped=True,
            )
        ]

    blocks = []
    for index, assertion in enumerate(assertions):
        name = json.dumps(assertion.get("label", f"behaviour_{index + 1}"))
        blocks.append(f"await __assert({name}, async () => {{ {assertion['expression']} }});")

    # The learner's code is placed directly in the IIFE body (not inside a block)
    # so its function declarations are visible to the assertions that follow.
    #
    # With `wrap_as`, the learner's file goes into `<name>__source` and the name
    # the spec calls is a thin shim that runs it and then drains the async work
    # it started. That way a spec written as `await __userMain(); return ...`
    # observes the finished DOM even when the file ends in a bare, unawaited
    # `loadMovies();` — which is idiomatic top-level code and must not be
    # penalised.
    body = (
        f"async function {wrap_as}__source() {{\n{user_code}\n}}\n"
        f"async function {wrap_as}() {{ return __runUserMain({wrap_as}__source); }}"
        if wrap_as
        else user_code
    )
    harness = JS_HARNESS.replace(
        "__DRAIN_BUDGET_MS_VALUE__", str(BEHAVIOUR_DRAIN_BUDGET_MS)
    ).replace("__ASSERTION_BUDGET_MS_VALUE__", str(BEHAVIOUR_ASSERTION_BUDGET_MS))
    program = "\n".join(
        [
            harness,
            prelude,
            "(async () => {",
            body,
            *blocks,
            "console.log('__SPRINTFORGE__' + JSON.stringify(__results));",
            "})().catch((e) => {",
            "  __results.push({ name: '__runtime__', passed: false, error: String((e && e.message) || e) });",
            "  console.log('__SPRINTFORGE__' + JSON.stringify(__results));",
            "});",
        ]
    )

    service = get_code_execution_service()
    execution = await service.run(
        "javascript", program, [TestCase(name="behaviour", stdin="", expected_stdout="")]
    )

    if not execution.supported:
        return [
            CheckOutcome(
                id="behaviour_runtime",
                label="Behaviour tests could not run",
                passed=False,
                hint=execution.compile_error,
                concept="tooling",
                precondition=True,
                requirement_mapped=True,
            )
        ]

    stdout = execution.results[0].stdout if execution.results else ""
    marker = stdout.find("__SPRINTFORGE__")
    if marker == -1:
        stderr = execution.combined_stderr() or "No test output produced."
        return [
            CheckOutcome(
                id="behaviour_runtime",
                label="Your code crashed before behaviour tests completed",
                passed=False,
                hint=stderr[:600],
                concept="debugging",
                precondition=True,
                requirement_mapped=True,
            )
        ]

    payload = stdout[marker + len("__SPRINTFORGE__") :].splitlines()[0]
    try:
        parsed = json.loads(payload)
    except json.JSONDecodeError:
        return [
            CheckOutcome(
                id="behaviour_runtime",
                label="Behaviour test output was unreadable",
                passed=False,
                concept="tooling",
                precondition=True,
                requirement_mapped=True,
            )
        ]

    by_label = {item.get("name"): item for item in parsed}
    outcomes: list[CheckOutcome] = []
    for index, assertion in enumerate(assertions):
        label = assertion.get("label", f"behaviour_{index + 1}")
        item = by_label.get(label)
        passed = bool(item and item.get("passed"))
        # A missing result means the harness never reached this assertion: fail
        # closed and say so rather than reporting an empty red row.
        detail = (item or {}).get("error")
        if not passed and not detail:
            detail = (
                "the expected behaviour was not observed"
                if item
                else "this test did not run to completion"
            )
        outcomes.append(
            CheckOutcome(
                id=assertion.get("id", f"behaviour_{index + 1}"),
                label=label,
                passed=passed,
                concept=assertion.get("concept"),
                hint=assertion.get("hint") or _DEFAULT_BEHAVIOUR_HINT,
                detail=detail,
                hidden=bool(assertion.get("hidden")),
                **_requirement_mapping(assertion),
            )
        )
    return outcomes
