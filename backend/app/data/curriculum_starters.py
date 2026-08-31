"""Generates per-language starter code from a problem's declarative I/O spec.

A curriculum problem describes how its stdin is shaped (``problem["io"]``) and
this module turns that description into starter code for every supported
language. Starters therefore stay consistent across ~75 problems without anyone
hand-writing five files per problem.

A starter always plumbs I/O and never contains the algorithm: the body of the
generated function is a ``TODO`` comment plus a placeholder return, which is the
property ``tests/test_judge_contract.py`` asserts.

The I/O spec
------------
``io = {``
    ``"mode":     "tokens" | "line",``
    ``"function": "snake_case_name",``  (camelCase is derived for JS/Java/C++)
    ``"todo":     "one line telling the learner what to return",``
    ``"reads":    [{"name": ..., "type": "int"|"long"|"string", "count": "n"}],``
    ``"args":     ["names", "passed", "to", "the", "function"],``
    ``"returns":  "int" | "long" | "void",``
``}``

``mode="tokens"`` reads whitespace-separated numbers; a read with ``count`` is an
array of that many values. ``mode="line"`` reads one raw line into a string.

A read may carry ``"value": "<expression>"`` instead of being read from stdin:
it is then *derived* from the reads declared before it. That is what lets a grid
problem put only ``r c`` on its first line and still know how many values
follow (``{"name": "k", "type": "int", "value": "r * c"}``). Without it, an
author's only way to express an element count was to demand a redundant token on
stdin, and a learner who computed the count themselves — as any competent
programmer would — had every value silently shifted by one.

``returns="void"`` is for problems whose answer is a sequence rather than a
single value: the function prints, and ``main`` merely calls it. Declaring such a
problem ``int`` hands the learner a signature promising a scalar answer that the
task does not have.
"""

from __future__ import annotations

import re
from typing import Any

LANGUAGES: tuple[str, ...] = ("python", "javascript", "java", "cpp", "c")

# ``LANGUAGES`` is the *expansion matrix*: every competitive-programming problem
# becomes one module per entry. TypeScript is deliberately NOT in it — see
# ``backend/docs/typescript.md`` — but a generator exists below, so a TypeScript
# starter can be produced from any ``io`` spec via :func:`build_starter`, and
# adding TypeScript to the matrix later is a one-line change rather than a
# rewrite.
GENERATED_LANGUAGES: tuple[str, ...] = (*LANGUAGES, "typescript")

# Sums over n <= 2e5 values of magnitude 1e9 reach 2e14, so every numeric
# quantity in a generated starter is 64-bit in C, C++ and Java. Getting this
# wrong is silent (wrap-around, not a crash), so it is not left to the learner.
_C_TYPES = {"int": "int", "long": "long long"}
_CPP_TYPES = {"int": "int", "long": "long long"}
_JAVA_TYPES = {"int": "int", "long": "long"}
_C_FORMATS = {"int": "%d", "long": "%lld"}
_C_SCANF = {"int": "%d", "long": "%lld"}

# A derived read's expression is arithmetic over other read names, which is
# spelled identically in all five languages; only the identifiers differ, and
# only for the camelCase languages.
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z_0-9]*")


def _camel(name: str) -> str:
    head, *rest = name.split("_")
    return head + "".join(part.capitalize() for part in rest)


def _reads(io: dict[str, Any]) -> list[dict[str, Any]]:
    return list(io["reads"])


def _is_array(read: dict[str, Any]) -> bool:
    return bool(read.get("count"))


def _is_derived(read: dict[str, Any]) -> bool:
    """True when the read is computed from earlier reads rather than from stdin."""
    return bool(read.get("value"))


def _expr(read: dict[str, Any], camel: bool) -> str:
    """The derived read's expression, with identifiers renamed if required."""
    value = read["value"]
    if not camel:
        return value
    return _IDENTIFIER.sub(lambda m: _camel(m.group(0)), value)


def _lookup(io: dict[str, Any], name: str) -> dict[str, Any]:
    for read in _reads(io):
        if read["name"] == name:
            return read
    raise KeyError(f"io.args references unknown read {name!r}")


def _validate(io: dict[str, Any]) -> None:
    mode = io.get("mode")
    if mode not in {"tokens", "line"}:
        raise ValueError(f"io.mode must be 'tokens' or 'line', got {mode!r}")
    for key in ("function", "todo", "reads", "args", "returns"):
        if not io.get(key):
            raise ValueError(f"io.{key} is required")
    if io["returns"] not in {"int", "long", "void"}:
        raise ValueError("io.returns must be 'int', 'long' or 'void'")
    seen: list[str] = []
    for read in _reads(io):
        if read.get("type") not in {"int", "long", "string"}:
            raise ValueError(f"unsupported read type {read.get('type')!r}")
        if mode == "line" and _is_array(read):
            raise ValueError("line mode cannot declare array reads")
        if mode == "tokens" and read["type"] == "string":
            raise ValueError("tokens mode cannot declare string reads")
        if _is_derived(read):
            if _is_array(read):
                raise ValueError(
                    f"read {read['name']!r} cannot be both derived and an array"
                )
            if read["type"] == "string":
                raise ValueError(f"derived read {read['name']!r} must be numeric")
            # A forward reference would generate code that uses a variable
            # before it is assigned, which in C is a silent garbage read.
            for name in _IDENTIFIER.findall(read["value"]):
                if name not in seen:
                    raise ValueError(
                        f"derived read {read['name']!r} references {name!r}, which is "
                        "not read before it"
                    )
        seen.append(read["name"])
    for name in io["args"]:
        _lookup(io, name)


# --------------------------------------------------------------------------- #
#  Python                                                                     #
# --------------------------------------------------------------------------- #


def _python(io: dict[str, Any]) -> str:
    fn = io["function"]
    void = io["returns"] == "void"
    call = f"{fn}({', '.join(io['args'])})"
    lines = ["import sys", "", "", f"def {fn}({', '.join(io['args'])}):"]
    lines += [f"    # TODO: {io['todo']}", "    pass" if void else "    return 0"]
    lines += ["", "", "def main():"]

    if io["mode"] == "line":
        name = _reads(io)[0]["name"]
        lines.append(f"    {name} = sys.stdin.readline().rstrip('\\n')")
    else:
        lines.append("    data = sys.stdin.read().split()")
        lines.append("    pos = 0")
        for read in _reads(io):
            name = read["name"]
            if _is_derived(read):
                lines.append(f"    {name} = {_expr(read, camel=False)}")
            elif _is_array(read):
                count = read["count"]
                lines.append(f"    {name} = [int(x) for x in data[pos:pos + {count}]]")
                lines.append(f"    pos += {count}")
            else:
                lines.append(f"    {name} = int(data[pos])")
                lines.append("    pos += 1")
    lines += [f"    {call}" if void else f"    print({call})"]
    lines += ["", "", 'if __name__ == "__main__":', "    main()", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  JavaScript                                                                 #
# --------------------------------------------------------------------------- #


def _javascript(io: dict[str, Any]) -> str:
    fn = _camel(io["function"])
    void = io["returns"] == "void"
    args = [_camel(a) for a in io["args"]]
    lines = [f"function {fn}({', '.join(args)}) {{", f"  // TODO: {io['todo']}"]
    if not void:
        lines.append("  return 0;")
    lines += ["}", ""]

    if io["mode"] == "line":
        name = _camel(_reads(io)[0]["name"])
        lines.append('const input = require("fs").readFileSync(0, "utf8");')
        lines.append(f'const {name} = input.split("\\n")[0] ?? "";')
    else:
        lines.append(
            'const data = require("fs").readFileSync(0, "utf8")'
            ".split(/\\s+/).filter(Boolean).map(Number);"
        )
        lines.append("let pos = 0;")
        for read in _reads(io):
            name = _camel(read["name"])
            if _is_derived(read):
                lines.append(f"const {name} = {_expr(read, camel=True)};")
            elif _is_array(read):
                count = _camel(read["count"])
                lines.append(f"const {name} = data.slice(pos, pos + {count});")
                lines.append(f"pos += {count};")
            else:
                lines.append(f"const {name} = data[pos];")
                lines.append("pos += 1;")
    call = f"{fn}({', '.join(args)})"
    lines += [f"{call};" if void else f"console.log({call});", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  TypeScript                                                                 #
# --------------------------------------------------------------------------- #

# The judge type-checks TypeScript under `--strict`, so a generated starter must
# already be *type-correct* even though it does not solve anything: an unannotated
# parameter is an error under `noImplicitAny`, and an unannotated
# `readFileSync(...).split(...)` chain would leave the learner fighting the
# compiler over plumbing they did not write. Every declaration below is therefore
# explicit — which is also the point of the language.
_TS_TYPES = {"int": "number", "long": "number", "string": "string"}


def _ts_param(read: dict[str, Any]) -> str:
    base = _TS_TYPES[read["type"]]
    return f"{base}[]" if _is_array(read) else base


def _typescript(io: dict[str, Any]) -> str:
    fn = _camel(io["function"])
    void = io["returns"] == "void"
    ret = "void" if void else "number"

    params = [
        f"{_camel(name)}: {_ts_param(_lookup(io, name))}" for name in io["args"]
    ]

    lines = [f"function {fn}({', '.join(params)}): {ret} {{", f"  // TODO: {io['todo']}"]
    if not void:
        lines.append("  return 0;")
    lines += ["}", ""]

    if io["mode"] == "line":
        name = _camel(_reads(io)[0]["name"])
        lines.append(
            'const input: string = require("fs").readFileSync(0, "utf8");'
        )
        lines.append(f'const {name}: string = input.split("\\n")[0] ?? "";')
    else:
        lines.append(
            'const data: number[] = require("fs").readFileSync(0, "utf8")'
            ".split(/\\s+/).filter(Boolean).map(Number);"
        )
        lines.append("let pos = 0;")
        for read in _reads(io):
            name = _camel(read["name"])
            if _is_derived(read):
                lines.append(f"const {name}: number = {_expr(read, camel=True)};")
            elif _is_array(read):
                count = _camel(read["count"])
                lines.append(f"const {name}: number[] = data.slice(pos, pos + {count});")
                lines.append(f"pos += {count};")
            else:
                lines.append(f"const {name}: number = data[pos];")
                lines.append("pos += 1;")
    call = f"{fn}({', '.join(_camel(a) for a in io['args'])})"
    lines += [f"{call};" if void else f"console.log({call});", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  C++                                                                        #
# --------------------------------------------------------------------------- #

# Explicit headers rather than <bits/stdc++.h>: that header does not exist on
# libc++ (macOS/clang), so a starter that used it would not compile here.
_CPP_HEADERS = (
    "#include <algorithm>\n"
    "#include <iostream>\n"
    "#include <string>\n"
    "#include <unordered_map>\n"
    "#include <unordered_set>\n"
    "#include <vector>\n"
)


def _cpp(io: dict[str, Any]) -> str:
    fn = _camel(io["function"])
    void = io["returns"] == "void"
    ret = "void" if void else _CPP_TYPES[io["returns"]]

    params = []
    for name in io["args"]:
        read = _lookup(io, name)
        if _is_array(read):
            params.append(f"const std::vector<{_CPP_TYPES[read['type']]}>& {_camel(name)}")
        elif read["type"] == "string":
            params.append(f"const std::string& {_camel(name)}")
        else:
            params.append(f"{_CPP_TYPES[read['type']]} {_camel(name)}")

    lines = [
        _CPP_HEADERS.rstrip("\n"),
        "",
        f"{ret} {fn}({', '.join(params)}) {{",
        f"    // TODO: {io['todo']}",
    ]
    if not void:
        lines.append("    return 0;")
    lines += [
        "}",
        "",
        "int main() {",
        "    std::ios::sync_with_stdio(false);",
        "    std::cin.tie(nullptr);",
    ]

    if io["mode"] == "line":
        name = _camel(_reads(io)[0]["name"])
        lines.append(f"    std::string {name};")
        lines.append(f"    std::getline(std::cin, {name});")
    else:
        for read in _reads(io):
            name = _camel(read["name"])
            ctype = _CPP_TYPES[read["type"]]
            if _is_derived(read):
                lines.append(f"    const {ctype} {name} = {_expr(read, camel=True)};")
            elif _is_array(read):
                count = _camel(read["count"])
                lines.append(f"    std::vector<{ctype}> {name}({count});")
                lines.append(f"    for (int i = 0; i < {count}; i++) std::cin >> {name}[i];")
            else:
                lines.append(f"    {ctype} {name};")
                lines.append(f"    if (!(std::cin >> {name})) return 0;")

    call_args = ", ".join(_camel(a) for a in io["args"])
    call = f"{fn}({call_args})"
    lines.append(f"    {call};" if void else f'    std::cout << {call} << "\\n";')
    lines += ["    return 0;", "}", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------- #
#  Java                                                                       #
# --------------------------------------------------------------------------- #

# Scanner is far too slow for n = 2e5 under the executor's time limit, so every
# Java starter ships this byte-level reader. Learners should not have to
# discover that the judge is timing out on I/O rather than on their algorithm.
_JAVA_READER = """
    /** Byte-level stdin reader: Scanner cannot keep up with n up to 200000. */
    private static final class FastReader {
        private final java.io.InputStream in;
        private final byte[] buf = new byte[1 << 16];
        private int len = 0;
        private int ptr = 0;

        FastReader(java.io.InputStream in) {
            this.in = in;
        }

        private int read() throws IOException {
            if (ptr == len) {
                len = in.read(buf, 0, buf.length);
                ptr = 0;
                if (len <= 0) {
                    return -1;
                }
            }
            return buf[ptr++];
        }

        long nextLong() throws IOException {
            int c = read();
            while (c == ' ' || c == '\\n' || c == '\\r' || c == '\\t') {
                c = read();
            }
            boolean negative = c == '-';
            if (negative) {
                c = read();
            }
            long value = 0;
            while (c >= '0' && c <= '9') {
                value = value * 10 + (c - '0');
                c = read();
            }
            return negative ? -value : value;
        }

        String nextLine() throws IOException {
            StringBuilder sb = new StringBuilder();
            int c = read();
            while (c != -1 && c != '\\n') {
                if (c != '\\r') {
                    sb.append((char) c);
                }
                c = read();
            }
            return sb.toString();
        }
    }
"""


def _java(io: dict[str, Any]) -> str:
    fn = _camel(io["function"])
    void = io["returns"] == "void"
    ret = "void" if void else _JAVA_TYPES[io["returns"]]

    params = []
    for name in io["args"]:
        read = _lookup(io, name)
        if _is_array(read):
            params.append(f"{_JAVA_TYPES[read['type']]}[] {_camel(name)}")
        elif read["type"] == "string":
            params.append(f"String {_camel(name)}")
        else:
            params.append(f"{_JAVA_TYPES[read['type']]} {_camel(name)}")

    body = [
        "import java.io.IOException;",
        "import java.util.*;",
        "",
        "public class Main {",
        "",
        f"    static {ret} {fn}({', '.join(params)}) {{",
        f"        // TODO: {io['todo']}",
    ]
    if not void:
        body.append("        return 0;")
    body += [
        "    }",
        "",
        "    public static void main(String[] args) throws IOException {",
        "        FastReader in = new FastReader(System.in);",
    ]

    if io["mode"] == "line":
        name = _camel(_reads(io)[0]["name"])
        body.append(f"        String {name} = in.nextLine();")
    else:
        for read in _reads(io):
            name = _camel(read["name"])
            jtype = _JAVA_TYPES[read["type"]]
            if _is_derived(read):
                body.append(f"        {jtype} {name} = {_expr(read, camel=True)};")
            elif _is_array(read):
                count = _camel(read["count"])
                body.append(f"        {jtype}[] {name} = new {jtype}[{count}];")
                body.append(
                    f"        for (int i = 0; i < {count}; i++) {name}[i] = "
                    + ("(int) in.nextLong();" if jtype == "int" else "in.nextLong();")
                )
            else:
                cast = "(int) " if jtype == "int" else ""
                body.append(f"        {jtype} {name} = {cast}in.nextLong();")

    call_args = ", ".join(_camel(a) for a in io["args"])
    call = f"{fn}({call_args})"
    body += [
        f"        {call};" if void else f"        System.out.println({call});",
        "    }",
        _JAVA_READER.rstrip("\n"),
        "}",
        "",
    ]
    return "\n".join(body)


# --------------------------------------------------------------------------- #
#  C                                                                          #
# --------------------------------------------------------------------------- #


def _c(io: dict[str, Any]) -> str:
    fn = io["function"]
    void = io["returns"] == "void"
    ret = "void" if void else _C_TYPES[io["returns"]]

    array_counts: list[str] = []
    params = []
    for name in io["args"]:
        read = _lookup(io, name)
        if _is_array(read):
            params.append(f"const {_C_TYPES[read['type']]}* {name}")
            if read["count"] not in array_counts:
                array_counts.append(read["count"])
        elif read["type"] == "string":
            params.append(f"const char* {name}")
        else:
            params.append(f"{_C_TYPES[read['type']]} {name}")
    # C arrays carry no length, so the count variable is appended to the
    # signature (once) whenever the function receives an array.
    params += [f"int {count}" for count in array_counts]

    lines = [
        "#include <stdio.h>",
        "#include <stdlib.h>",
        "#include <string.h>",
        "",
        f"{ret} {fn}({', '.join(params)}) {{",
        f"    /* TODO: {io['todo']} */",
    ]
    if not void:
        lines.append("    return 0;")
    lines += [
        "}",
        "",
        "int main(void) {",
    ]

    allocated: list[str] = []
    if io["mode"] == "line":
        name = _reads(io)[0]["name"]
        lines += [
            f"    char* {name} = NULL;",
            "    size_t cap = 0;",
            f"    ssize_t len = getline(&{name}, &cap, stdin);",
            "    if (len < 0) {",
            f"        {name} = (char*)calloc(1, 1);",
            "        len = 0;",
            "    }",
            f"    while (len > 0 && ({name}[len - 1] == '\\n' || {name}[len - 1] == '\\r')) {{",
            f"        {name}[--len] = '\\0';",
            "    }",
        ]
        allocated.append(name)
    else:
        for read in _reads(io):
            name = read["name"]
            ctype = _C_TYPES[read["type"]]
            fmt = _C_SCANF[read["type"]]
            if _is_derived(read):
                lines.append(f"    const {ctype} {name} = {_expr(read, camel=False)};")
            elif _is_array(read):
                count = read["count"]
                lines += [
                    f"    {ctype}* {name} = ({ctype}*)malloc((size_t)({count} > 0 ? {count} : 1)"
                    f" * sizeof({ctype}));",
                    f"    for (int i = 0; i < {count}; i++) {{",
                    f'        if (scanf("{fmt}", &{name}[i]) != 1) break;',
                    "    }",
                ]
                allocated.append(name)
            else:
                lines += [
                    f"    {ctype} {name} = 0;",
                    f'    if (scanf("{fmt}", &{name}) != 1) return 0;',
                ]

    call_args = list(io["args"]) + array_counts
    call = f'{fn}({", ".join(call_args)})'
    if void:
        lines.append(f"    {call};")
    else:
        lines.append(f'    printf("{_C_FORMATS[io["returns"]]}\\n", {call});')
    lines += [f"    free({name});" for name in allocated]
    lines += ["    return 0;", "}", ""]
    return "\n".join(lines)


_GENERATORS = {
    "python": _python,
    "javascript": _javascript,
    "typescript": _typescript,
    "java": _java,
    "cpp": _cpp,
    "c": _c,
}


def languages_for(problem: dict[str, Any]) -> tuple[str, ...]:
    """The languages a problem is offered in.

    An algorithmic problem is language-agnostic and is offered in all five. A
    problem that teaches a *language feature* is not: pointer arithmetic has no
    Python rendering, and `ArrayList` has no meaning in C. Such a problem
    declares ``"languages": ["c", "cpp"]`` and is expanded only there, rather
    than being restated as something it is not just to fill five slots.

    The returned order follows :data:`LANGUAGES`, so module ordering does not
    depend on how the author happened to spell the list.
    """
    declared = problem.get("languages")
    if not declared:
        return LANGUAGES
    unknown = [language for language in declared if language not in LANGUAGES]
    if unknown:
        raise ValueError(
            f"problem {problem.get('slug')!r} restricts itself to unsupported "
            f"language(s) {unknown}"
        )
    return tuple(language for language in LANGUAGES if language in declared)


def build_starters(problem: dict[str, Any]) -> dict[str, str]:
    """Return ``{language: starter source}`` for one curriculum problem.

    Only the problem's own languages are generated (see :func:`languages_for`).
    """
    io = problem.get("io")
    if not io:
        raise RuntimeError(
            f"Problem '{problem.get('slug')}' has no 'io' spec, so no starter can be "
            "generated. See backend/docs/curriculum_authoring.md."
        )
    _validate(io)
    return {language: _GENERATORS[language](io) for language in languages_for(problem)}


def build_starter(problem: dict[str, Any], language: str) -> str:
    """Return the starter for a single language, including ones outside ``LANGUAGES``.

    This is how a TypeScript starter is obtained: TypeScript has a generator but
    is not part of the expansion matrix, so :func:`build_starters` never emits one.
    """
    io = problem.get("io")
    if not io:
        raise RuntimeError(
            f"Problem '{problem.get('slug')}' has no 'io' spec, so no starter can be "
            "generated. See backend/docs/curriculum_authoring.md."
        )
    if language not in _GENERATORS:
        raise RuntimeError(f"no starter generator for language {language!r}")
    _validate(io)
    return _GENERATORS[language](io)
