"""JavaScript AST bridge.

Node (with a vendored `acorn`) is used only as a *parser*: it turns learner
source into a JSON ESTree document. Every semantic rule is expressed in Python
over that document, so the rules stay unit-testable without spawning a runtime.

Fail-closed contract: if Node or the parser is missing, times out, or produces
unreadable output, `parse_js` returns a result with `tooling_error` set and
`valid` False. Callers must treat that as a failing check, never a pass.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Optional

TOOL_DIR = Path(__file__).resolve().parents[1] / "tools" / "js_ast"
PARSE_SCRIPT = TOOL_DIR / "parse.js"
PARSE_TIMEOUT_SECONDS = 10

JSX_SUFFIXES = (".jsx", ".tsx")

_FUNCTION_TYPES = {"FunctionDeclaration", "FunctionExpression", "ArrowFunctionExpression"}

DOM_WRITE_PROPERTIES = {
    "innerHTML",
    "outerHTML",
    "textContent",
    "innerText",
    "className",
    "hidden",
    "src",
    "value",
}

DOM_WRITE_METHODS = {
    "insertAdjacentHTML",
    "insertAdjacentElement",
    "insertAdjacentText",
    "appendChild",
    "append",
    "prepend",
    "replaceChildren",
    "replaceChild",
    "removeChild",
    "remove",
    "setAttribute",
    "removeAttribute",
    "createElement",
    "classList.add",
    "classList.remove",
    "classList.toggle",
    "classList.replace",
}


@dataclass
class ParseResult:
    valid: bool
    ast: Optional[dict[str, Any]] = None
    source_type: Optional[str] = None
    message: Optional[str] = None
    line: Optional[int] = None
    column: Optional[int] = None
    tooling_error: bool = False

    @property
    def location(self) -> str:
        if self.line is None:
            return ""
        if self.column is None:
            return f"line {self.line}"
        return f"line {self.line}, column {self.column + 1}"


_CACHE: dict[tuple[str, bool], ParseResult] = {}
_CACHE_LIMIT = 256


def clear_parse_cache() -> None:
    _CACHE.clear()


def _tooling_failure(message: str) -> ParseResult:
    return ParseResult(valid=False, message=message, tooling_error=True)


def parse_js(source: str, filename: str = "script.js") -> ParseResult:
    """Parse JS/JSX source into an ESTree dict. Cached per (source, jsx flag)."""
    jsx = filename.lower().endswith(JSX_SUFFIXES)
    key = (source or "", jsx)
    cached = _CACHE.get(key)
    if cached is not None:
        return cached

    result = _parse_uncached(source or "", jsx)
    if len(_CACHE) >= _CACHE_LIMIT:
        _CACHE.clear()
    _CACHE[key] = result
    return result


def _parse_uncached(source: str, jsx: bool) -> ParseResult:
    node = shutil.which("node")
    if node is None:
        return _tooling_failure(
            "JavaScript analysis is unavailable: Node.js was not found on PATH."
        )
    if not PARSE_SCRIPT.exists() or not (TOOL_DIR / "node_modules" / "acorn").exists():
        return _tooling_failure(
            "JavaScript analysis is unavailable: run `npm install` in "
            "backend/app/tools/js_ast."
        )

    command = [node, str(PARSE_SCRIPT)]
    if jsx:
        command.append("--jsx")
    try:
        proc = subprocess.run(
            command,
            input=source,
            capture_output=True,
            text=True,
            timeout=PARSE_TIMEOUT_SECONDS,
            cwd=str(TOOL_DIR),
        )
    except subprocess.TimeoutExpired:
        return _tooling_failure("JavaScript analysis timed out while parsing your code.")
    except OSError as exc:  # pragma: no cover - depends on host
        return _tooling_failure(f"JavaScript analysis could not start: {exc}")

    if proc.returncode != 0:
        return _tooling_failure(
            "JavaScript analysis failed: " + (proc.stderr or "parser exited non-zero")[:400]
        )

    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return _tooling_failure("JavaScript analysis produced unreadable output.")

    if payload.get("valid"):
        return ParseResult(valid=True, ast=payload.get("ast"), source_type=payload.get("sourceType"))

    error = payload.get("error") or {}
    return ParseResult(
        valid=False,
        message=str(error.get("message") or "Syntax error"),
        line=error.get("line"),
        column=error.get("column"),
    )


# --------------------------------------------------------------------------
# Generic ESTree walking helpers
# --------------------------------------------------------------------------


def walk(node: Any) -> Iterator[dict[str, Any]]:
    """Yield every AST node dict, depth-first.

    Comments are never present (acorn drops them unless asked for) and string
    literals are `Literal` nodes whose *value* is data, never code, so evidence
    gathered here can not come from a comment or a string.
    """
    if isinstance(node, dict):
        if "type" in node:
            yield node
        for key, value in node.items():
            if key in {"loc", "type", "start", "end"}:
                continue
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def nodes_of_type(root: Any, *types: str) -> list[dict[str, Any]]:
    wanted = set(types)
    return [n for n in walk(root) if n.get("type") in wanted]


def span(node: dict[str, Any]) -> tuple[int, int]:
    return int(node.get("start", -1)), int(node.get("end", -1))


def contains(outer: dict[str, Any], inner: dict[str, Any]) -> bool:
    o_start, o_end = span(outer)
    i_start, i_end = span(inner)
    return o_start <= i_start and i_end <= o_end


def line_of(node: dict[str, Any]) -> Optional[int]:
    loc = node.get("loc") or {}
    start = loc.get("start") or {}
    return start.get("line")


def dotted_name(node: Optional[dict[str, Any]]) -> str:
    """Render a callee/member expression as a dotted string.

    `response.json` -> "response.json"; `items[0].run` -> "items[].run";
    `this.x` -> "this.x". Unknown shapes render as "".
    """
    if not isinstance(node, dict):
        return ""
    kind = node.get("type")
    if kind == "Identifier":
        return str(node.get("name") or "")
    if kind == "ThisExpression":
        return "this"
    if kind == "MemberExpression":
        obj = dotted_name(node.get("object"))
        if node.get("computed"):
            return f"{obj}[]" if obj else "[]"
        prop = dotted_name(node.get("property"))
        return f"{obj}.{prop}" if obj else prop
    if kind == "CallExpression":
        return dotted_name(node.get("callee"))
    return ""


def call_matches(call: dict[str, Any], name: str) -> bool:
    """Match a CallExpression against `fetch`, `response.json` or `.json`."""
    rendered = dotted_name(call.get("callee"))
    if not rendered:
        return False
    if name.startswith("."):
        return rendered.endswith(name)
    return rendered == name or rendered.endswith("." + name)


def calls_to(root: Any, name: str) -> list[dict[str, Any]]:
    return [c for c in nodes_of_type(root, "CallExpression") if call_matches(c, name)]


def functions(root: Any) -> list[dict[str, Any]]:
    return nodes_of_type(root, *_FUNCTION_TYPES)


def enclosing_function(root: Any, node: dict[str, Any]) -> Optional[dict[str, Any]]:
    """Innermost function whose span contains `node`."""
    candidates = [fn for fn in functions(root) if contains(fn, node)]
    if not candidates:
        return None
    return min(candidates, key=lambda fn: span(fn)[1] - span(fn)[0])


def scope_of(root: Any, node: dict[str, Any]) -> Any:
    """The function body containing `node`, falling back to the whole program."""
    fn = enclosing_function(root, node)
    return fn.get("body") if fn else root


def identifier_names(root: Any) -> set[str]:
    return {str(n.get("name")) for n in nodes_of_type(root, "Identifier") if n.get("name")}


def is_dom_write(node: dict[str, Any]) -> bool:
    """True for AST nodes that mutate the document."""
    kind = node.get("type")
    if kind == "AssignmentExpression":
        left = node.get("left") or {}
        if left.get("type") == "MemberExpression" and not left.get("computed"):
            prop = (left.get("property") or {}).get("name")
            return prop in DOM_WRITE_PROPERTIES
        return False
    if kind == "CallExpression":
        rendered = dotted_name(node.get("callee"))
        if not rendered:
            return False
        tail_one = rendered.rsplit(".", 1)[-1]
        tail_two = ".".join(rendered.split(".")[-2:])
        return tail_one in DOM_WRITE_METHODS or tail_two in DOM_WRITE_METHODS
    return False


def has_dom_write(root: Any) -> bool:
    return any(is_dom_write(node) for node in walk(root))


def awaits(root: Any) -> list[dict[str, Any]]:
    return nodes_of_type(root, "AwaitExpression")


def statement_is_trivial(body: Any) -> bool:
    """A function body that does nothing observable."""
    if not isinstance(body, dict):
        return True
    if body.get("type") != "BlockStatement":
        # Concise arrow body: only a bare literal counts as trivial.
        return body.get("type") == "Literal"
    statements = body.get("body") or []
    if not statements:
        return True
    if len(statements) == 1:
        only = statements[0]
        if only.get("type") == "ReturnStatement":
            argument = only.get("argument")
            if argument is None or argument.get("type") in {"Literal", "Identifier"}:
                return argument is None or argument.get("type") == "Literal"
        if only.get("type") == "EmptyStatement":
            return True
    return False


TERMINATING_STATEMENTS = {"ReturnStatement", "ThrowStatement", "BreakStatement", "ContinueStatement"}


def unreachable_statements(root: Any) -> list[dict[str, Any]]:
    """Statements that follow an unconditional return/throw in the same block."""
    dead: list[dict[str, Any]] = []
    for block in nodes_of_type(root, "BlockStatement", "Program"):
        statements = block.get("body") or []
        for index, statement in enumerate(statements):
            if statement.get("type") in TERMINATING_STATEMENTS:
                for later in statements[index + 1 :]:
                    # Function declarations hoist, so they are still reachable.
                    if later.get("type") != "FunctionDeclaration":
                        dead.append(later)
                break
    return dead
