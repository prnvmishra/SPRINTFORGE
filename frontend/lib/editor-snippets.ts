/**
 * Snippet library for the workspace editor.
 *
 * Emmet covers HTML and CSS abbreviations (`!`, `div.card>ul>li*3`, `dfc`), so
 * nothing here duplicates it. What Emmet does not cover is the boilerplate a
 * learner retypes on every challenge: reading stdin in C++, a Java `main`, a
 * fetch with error handling. Those are the ones below.
 *
 * `$1`, `$2` are tab stops and `$0` is where the cursor lands last; `${1:name}`
 * gives a tab stop a pre-filled, selected default.
 */

export type Snippet = {
  /** What the learner types to summon it. */
  prefix: string;
  /** Shown to the right of the prefix in the suggestion list. */
  detail: string;
  body: string;
};

const JS_SNIPPETS: Snippet[] = [
  {
    prefix: "fetchjson",
    detail: "fetch + status check + try/catch",
    body: [
      "try {",
      "  const response = await fetch(${1:url});",
      "  if (!response.ok) throw new Error(`Request failed: ${response.status}`);",
      "  const ${2:data} = await response.json();",
      "  $0",
      "} catch (error) {",
      "  console.error(error);",
      "}",
    ].join("\n"),
  },
  {
    prefix: "afn",
    detail: "async function",
    body: "async function ${1:name}(${2:args}) {\n  $0\n}",
  },
  { prefix: "qs", detail: "querySelector", body: "document.querySelector(\"${1:selector}\")" },
  { prefix: "qsa", detail: "querySelectorAll (as array)", body: "[...document.querySelectorAll(\"${1:selector}\")]" },
  { prefix: "gid", detail: "getElementById", body: "document.getElementById(\"${1:id}\")" },
  { prefix: "cel", detail: "createElement + append", body: "const ${1:el} = document.createElement(\"${2:div}\");\n${1:el}.className = \"${3:class}\";\n${4:parent}.appendChild(${1:el});\n$0" },
  { prefix: "ael", detail: "addEventListener", body: "${1:element}.addEventListener(\"${2:click}\", (event) => {\n  $0\n});" },
  { prefix: "fore", detail: "forEach", body: "${1:items}.forEach((${2:item}) => {\n  $0\n});" },
  { prefix: "map", detail: "map", body: "const ${1:result} = ${2:items}.map((${3:item}) => $0);" },
  { prefix: "clg", detail: "console.log", body: "console.log($0);" },
  { prefix: "tryc", detail: "try / catch", body: "try {\n  $0\n} catch (error) {\n  console.error(error);\n}" },
];

const PYTHON_SNIPPETS: Snippet[] = [
  {
    prefix: "main",
    detail: "read stdin + main guard",
    body: [
      "import sys",
      "",
      "def main():",
      "    data = sys.stdin.read().split()",
      "    $0",
      "",
      "if __name__ == \"__main__\":",
      "    main()",
    ].join("\n"),
  },
  { prefix: "readints", detail: "read all ints from stdin", body: "nums = list(map(int, sys.stdin.read().split()))\n$0" },
  { prefix: "fori", detail: "for i in range", body: "for ${1:i} in range(${2:n}):\n    $0" },
  { prefix: "fore", detail: "for each", body: "for ${1:item} in ${2:items}:\n    $0" },
  { prefix: "def", detail: "function", body: "def ${1:name}(${2:args}):\n    $0" },
  { prefix: "cls", detail: "class", body: "class ${1:Name}:\n    def __init__(self${2:, args}):\n        $0" },
  { prefix: "dd", detail: "defaultdict", body: "from collections import defaultdict\n${1:counts} = defaultdict(${2:int})\n$0" },
  { prefix: "heap", detail: "heapq import", body: "import heapq\n$0" },
];

const CPP_SNIPPETS: Snippet[] = [
  {
    prefix: "main",
    detail: "competitive main + fast IO",
    body: [
      "#include <bits/stdc++.h>",
      "using namespace std;",
      "",
      "int main() {",
      "    ios::sync_with_stdio(false);",
      "    cin.tie(nullptr);",
      "    $0",
      "    return 0;",
      "}",
    ].join("\n"),
  },
  { prefix: "fastio", detail: "fast IO lines", body: "ios::sync_with_stdio(false);\ncin.tie(nullptr);\n$0" },
  { prefix: "fori", detail: "for loop", body: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ++${1:i}) {\n    $0\n}" },
  { prefix: "fore", detail: "range-for", body: "for (auto& ${1:item} : ${2:items}) {\n    $0\n}" },
  { prefix: "vec", detail: "vector", body: "vector<${1:int}> ${2:v}(${3:n});\n$0" },
  { prefix: "vec2", detail: "2D vector", body: "vector<vector<${1:int}>> ${2:grid}(${3:r}, vector<${1:int}>(${4:c}));\n$0" },
  { prefix: "readvec", detail: "read n then vector", body: "int n;\ncin >> n;\nvector<int> a(n);\nfor (int i = 0; i < n; ++i) cin >> a[i];\n$0" },
  { prefix: "sortv", detail: "sort", body: "sort(${1:v}.begin(), ${1:v}.end());\n$0" },
];

const C_SNIPPETS: Snippet[] = [
  {
    prefix: "main",
    detail: "main + stdio",
    body: "#include <stdio.h>\n#include <stdlib.h>\n\nint main(void) {\n    $0\n    return 0;\n}",
  },
  { prefix: "fori", detail: "for loop", body: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ++${1:i}) {\n    $0\n}" },
  { prefix: "scan", detail: "scanf int", body: "int ${1:n};\nscanf(\"%d\", &${1:n});\n$0" },
  { prefix: "printi", detail: "printf int", body: "printf(\"%d\\n\", ${1:value});\n$0" },
];

const JAVA_SNIPPETS: Snippet[] = [
  {
    prefix: "main",
    detail: "Main class + fast Scanner",
    body: [
      "import java.util.*;",
      "import java.io.*;",
      "",
      "public class Main {",
      "    public static void main(String[] args) throws IOException {",
      "        BufferedReader br = new BufferedReader(new InputStreamReader(System.in));",
      "        $0",
      "    }",
      "}",
    ].join("\n"),
  },
  { prefix: "fori", detail: "for loop", body: "for (int ${1:i} = 0; ${1:i} < ${2:n}; ${1:i}++) {\n    $0\n}" },
  { prefix: "fore", detail: "for each", body: "for (${1:int} ${2:item} : ${3:items}) {\n    $0\n}" },
  { prefix: "sout", detail: "println", body: "System.out.println($0);" },
  { prefix: "readints", detail: "read ints from a line", body: "StringTokenizer st = new StringTokenizer(br.readLine());\nint ${1:n} = Integer.parseInt(st.nextToken());\n$0" },
  { prefix: "sb", detail: "StringBuilder output", body: "StringBuilder sb = new StringBuilder();\n$0\nSystem.out.print(sb);" },
];

const SQL_SNIPPETS: Snippet[] = [
  { prefix: "sel", detail: "select where", body: "SELECT ${1:*}\nFROM ${2:table}\nWHERE ${3:condition};" },
  { prefix: "join", detail: "inner join", body: "SELECT ${1:*}\nFROM ${2:a}\nJOIN ${3:b} ON ${2:a}.${4:id} = ${3:b}.${5:a_id};" },
  { prefix: "grp", detail: "group by + having", body: "SELECT ${1:col}, COUNT(*) AS ${2:total}\nFROM ${3:table}\nGROUP BY ${1:col}\nHAVING COUNT(*) > ${4:1};" },
  { prefix: "cte", detail: "common table expression", body: "WITH ${1:name} AS (\n    SELECT $0\n)\nSELECT * FROM ${1:name};" },
];

/**
 * HTML and CSS lean on Emmet, so these are only the pieces Emmet cannot
 * produce — full documents and multi-line patterns.
 */
const HTML_SNIPPETS: Snippet[] = [
  {
    prefix: "html5",
    detail: "full document (same as Emmet `!`)",
    body: [
      "<!DOCTYPE html>",
      "<html lang=\"en\">",
      "<head>",
      "  <meta charset=\"UTF-8\">",
      "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">",
      "  <title>${1:Document}</title>",
      "  <link rel=\"stylesheet\" href=\"styles.css\">",
      "</head>",
      "<body>",
      "  $0",
      "  <script src=\"script.js\"></script>",
      "</body>",
      "</html>",
    ].join("\n"),
  },
];

const CSS_SNIPPETS: Snippet[] = [
  { prefix: "flexcenter", detail: "centre with flex", body: "display: flex;\nalign-items: center;\njustify-content: center;\n$0" },
  { prefix: "gridcols", detail: "responsive grid", body: "display: grid;\ngrid-template-columns: repeat(${1:auto-fit}, minmax(${2:220px}, 1fr));\ngap: ${3:1rem};\n$0" },
  { prefix: "reset", detail: "box-sizing reset", body: "*,\n*::before,\n*::after {\n  box-sizing: border-box;\n  margin: 0;\n  padding: 0;\n}\n$0" },
  { prefix: "media", detail: "media query", body: "@media (max-width: ${1:768px}) {\n  $0\n}" },
  { prefix: "vars", detail: ":root custom properties", body: ":root {\n  --${1:brand}: ${2:#c8fa4b};\n  $0\n}" },
];

/** Monaco language id → snippets. Keys must match the ids we pass to Editor. */
export const SNIPPETS_BY_LANGUAGE: Record<string, Snippet[]> = {
  javascript: JS_SNIPPETS,
  typescript: JS_SNIPPETS,
  python: PYTHON_SNIPPETS,
  cpp: CPP_SNIPPETS,
  c: C_SNIPPETS,
  java: JAVA_SNIPPETS,
  sql: SQL_SNIPPETS,
  html: HTML_SNIPPETS,
  css: CSS_SNIPPETS,
};

/** Rows for the in-app shortcut sheet. Keep in sync with the keybindings. */
export const KEYBOARD_SHORTCUTS: { keys: string; action: string }[] = [
  { keys: "Ctrl / ⌘ + Enter", action: "Run code" },
  { keys: "Ctrl / ⌘ + S", action: "Submit for checks" },
  { keys: "Ctrl / ⌘ + /", action: "Toggle comment" },
  { keys: "Shift + Alt + F", action: "Format document" },
  { keys: "Alt + ↑ / ↓", action: "Move line up / down" },
  { keys: "Shift + Alt + ↑ / ↓", action: "Duplicate line" },
  { keys: "Ctrl / ⌘ + D", action: "Select next occurrence" },
  { keys: "Ctrl / ⌘ + F", action: "Find" },
  { keys: "Ctrl / ⌘ + H", action: "Replace" },
  { keys: "Alt + Click", action: "Add extra cursor" },
  { keys: "Ctrl / ⌘ + Space", action: "Trigger suggestions" },
  { keys: "Tab", action: "Expand Emmet / snippet" },
  { keys: "!  then Tab", action: "Full HTML document" },
  { keys: "Ctrl / ⌘ + K", action: "Show this sheet" },
];
