"""Adaptive assessment item bank.

Items are indexed by skill and difficulty (1-10). The engine selects the next
item based on live performance, so no learner sees a fixed static quiz.

Item types: mcq, output_prediction, code_debug, code_completion, scenario.
Non-MCQ items carry `answer_checks` (deterministic regex signals) and are also
passed to the AI evaluator, which returns validated structured output.
"""

from __future__ import annotations

from typing import Any

from app.data.assessment_bank_backend import BACKEND_ITEMS
from app.data.assessment_bank_data import DATA_ITEMS

ASSESSMENT_ITEMS: list[dict[str, Any]] = [
    # ----------------------------------------------------------- js_basics
    {
        "id": "js_basics_e1",
        "skill_id": "js_basics",
        "difficulty": 1,
        "type": "mcq",
        "concept": "types",
        "prompt": "What is the result of `typeof null` in JavaScript?",
        "options": ["\"null\"", "\"object\"", "\"undefined\"", "\"number\""],
        "correct_option": 1,
        "explanation": "typeof null returns \"object\" — a long-standing quirk of the language.",
    },
    {
        "id": "js_basics_e2",
        "skill_id": "js_basics",
        "difficulty": 2,
        "type": "output_prediction",
        "concept": "operators",
        "prompt": "What does this print?",
        "code": "console.log(1 + '2' - 1);",
        "expected_answer": "11",
        "answer_checks": [r"^\s*11\s*$"],
        "explanation": "1 + '2' coerces to the string '12', then '12' - 1 coerces back to the number 11.",
    },
    {
        "id": "js_basics_m1",
        "skill_id": "js_basics",
        "difficulty": 4,
        "type": "mcq",
        "concept": "control flow",
        "prompt": "Which comparison evaluates to `false`?",
        "options": ["0 == '0'", "0 === '0'", "'' == false", "null == undefined"],
        "correct_option": 1,
        "explanation": "=== compares without coercion, so 0 === '0' is false.",
    },
    # -------------------------------------------------------- js_functions
    {
        "id": "js_functions_e1",
        "skill_id": "js_functions",
        "difficulty": 2,
        "type": "mcq",
        "concept": "hoisting",
        "prompt": "Which declaration is hoisted and callable before its definition line?",
        "options": [
            "const fn = () => {}",
            "function fn() {}",
            "let fn = function () {}",
            "class Fn {}",
        ],
        "correct_option": 1,
        "explanation": "Function declarations are fully hoisted; const/let bindings are not initialised.",
    },
    {
        "id": "js_functions_m1",
        "skill_id": "js_functions",
        "difficulty": 5,
        "type": "output_prediction",
        "concept": "closures",
        "prompt": "What does this print?",
        "code": "function counter() {\n  let n = 0;\n  return () => ++n;\n}\nconst c = counter();\nc();\nconsole.log(c());",
        "expected_answer": "2",
        "answer_checks": [r"^\s*2\s*$"],
        "explanation": "The returned arrow function closes over `n`, so the second call yields 2.",
    },
    {
        "id": "js_functions_h1",
        "skill_id": "js_functions",
        "difficulty": 7,
        "type": "output_prediction",
        "concept": "closures",
        "prompt": "What is logged?",
        "code": "const fns = [];\nfor (var i = 0; i < 3; i++) { fns.push(() => i); }\nconsole.log(fns.map((f) => f()).join(','));",
        "expected_answer": "3,3,3",
        "answer_checks": [r"3\s*,\s*3\s*,\s*3"],
        "explanation": "`var` is function-scoped, so all closures share the final value of i.",
    },
    # ------------------------------------------------------------- js_dom
    {
        "id": "js_dom_e1",
        "skill_id": "js_dom",
        "difficulty": 2,
        "type": "mcq",
        "concept": "querySelector",
        "prompt": "Which call returns the first element with class `card`?",
        "options": [
            "document.querySelector('.card')",
            "document.getElementById('card')",
            "document.querySelectorAll('.card')",
            "document.getElementsByClassName('card')",
        ],
        "correct_option": 0,
        "explanation": "querySelector takes a CSS selector and returns the first match.",
    },
    {
        "id": "js_dom_m1",
        "skill_id": "js_dom",
        "difficulty": 4,
        "type": "code_completion",
        "concept": "event listeners",
        "prompt": "Complete the code so clicking the button sets the status text to \"Saved\".",
        "code": "const btn = document.getElementById('saveBtn');\nconst status = document.getElementById('status');\n// your code here",
        "expected_answer": "btn.addEventListener('click', () => { status.textContent = 'Saved'; });",
        "answer_checks": [r"addEventListener\(\s*['\"]click['\"]", r"(textContent|innerText)\s*="],
        "explanation": "Register a click listener and write to textContent.",
    },
    # ------------------------------------------------------------ js_async
    {
        "id": "js_async_e1",
        "skill_id": "js_async",
        "difficulty": 3,
        "type": "mcq",
        "concept": "promises",
        "prompt": "What does an `async` function always return?",
        "options": ["The resolved value", "A Promise", "undefined", "A generator"],
        "correct_option": 1,
        "explanation": "An async function always returns a Promise, even for a plain return value.",
    },
    {
        "id": "js_async_m1",
        "skill_id": "js_async",
        "difficulty": 5,
        "type": "output_prediction",
        "concept": "event loop",
        "prompt": "In what order are the numbers logged?",
        "code": "console.log(1);\nsetTimeout(() => console.log(2), 0);\nPromise.resolve().then(() => console.log(3));\nconsole.log(4);",
        "expected_answer": "1 4 3 2",
        "answer_checks": [r"1\D+4\D+3\D+2"],
        "explanation": "Sync code first, then microtasks (promises), then macrotasks (timers).",
    },
    {
        "id": "js_async_h1",
        "skill_id": "js_async",
        "difficulty": 7,
        "type": "scenario",
        "concept": "promise rejection",
        "prompt": (
            "A page calls three independent APIs with `Promise.all`. One endpoint is down, "
            "and the whole page renders blank. Explain the root cause and how you would change "
            "the code so partial data still renders."
        ),
        "expected_answer": (
            "Promise.all rejects as soon as any promise rejects, discarding the fulfilled results. "
            "Use Promise.allSettled (or attach a .catch to each promise) so each result is inspected "
            "independently and the successful responses can still be rendered."
        ),
        "answer_checks": [r"allSettled|catch|reject"],
        "explanation": "Promise.all is all-or-nothing; allSettled reports each outcome separately.",
    },
    # ------------------------------------------- js_async_error_handling
    {
        "id": "js_aeh_e1",
        "skill_id": "js_async_error_handling",
        "difficulty": 4,
        "type": "mcq",
        "concept": "try/catch",
        "prompt": "What happens when you `await` a promise that rejects, with no try/catch?",
        "options": [
            "await returns undefined",
            "The rejection is silently ignored",
            "The error is thrown inside the async function",
            "The function retries automatically",
        ],
        "correct_option": 2,
        "explanation": "A rejected awaited promise throws at the await site and propagates to the caller.",
    },
    {
        "id": "js_aeh_e0",
        "skill_id": "js_async_error_handling",
        "difficulty": 2,
        "type": "mcq",
        "concept": "try/catch",
        "prompt": "Which block runs whether or not an exception was thrown?",
        "options": ["try", "catch", "finally", "throw"],
        "correct_option": 2,
        "explanation": "finally always runs, which makes it the place for cleanup.",
    },
    {
        "id": "js_aeh_e2",
        "skill_id": "js_async_error_handling",
        "difficulty": 3,
        "type": "mcq",
        "concept": "promise rejection",
        "prompt": "Which of these correctly handles a rejection from `doWork()`?",
        "options": [
            "doWork().then(handle)",
            "doWork().catch(handle)",
            "try { doWork(); } catch (e) { handle(e); }",
            "await doWork()",
        ],
        "correct_option": 1,
        "explanation": "Without await, a synchronous try/catch cannot see the rejection; .catch can.",
    },
    {
        "id": "js_aeh_m1",
        "skill_id": "js_async_error_handling",
        "difficulty": 6,
        "type": "code_debug",
        "concept": "promise rejection",
        "prompt": "This function crashes the page whenever the network fails. Fix it so it returns an error result instead of throwing.",
        "code": "async function getUser(id) {\n  const res = await fetch(`/api/users/${id}`);\n  return res.json();\n}",
        "expected_answer": (
            "async function getUser(id) {\n"
            "  try {\n"
            "    const res = await fetch(`/api/users/${id}`);\n"
            "    if (!res.ok) return { error: `HTTP ${res.status}` };\n"
            "    return { data: await res.json() };\n"
            "  } catch (e) {\n"
            "    return { error: e.message };\n"
            "  }\n"
            "}"
        ),
        "answer_checks": [r"try\s*\{[\s\S]*catch", r"await"],
        "explanation": "Wrap the await in try/catch and check res.ok before parsing JSON.",
    },
    {
        "id": "js_aeh_h1",
        "skill_id": "js_async_error_handling",
        "difficulty": 8,
        "type": "scenario",
        "concept": "async error handling",
        "prompt": (
            "Your fetch wrapper has try/catch around `await fetch(...)`, yet users still see "
            "\"Unhandled promise rejection\" in production. Give two concrete reasons this can "
            "still happen and how you would fix each."
        ),
        "expected_answer": (
            "1) A rejection happens outside the try block — for example the promise is created, "
            "then awaited later, or a .then chain is started without a .catch; move creation inside "
            "the try or attach .catch at creation. 2) fetch resolves for HTTP 4xx/5xx, so a later "
            "res.json() on an error body throws outside the guarded region; check res.ok and parse "
            "inside the try. Also, errors thrown inside event handlers or floating async calls are "
            "never awaited, so add a top-level catch on the call site."
        ),
        "answer_checks": [r"res\.ok|status|catch|await"],
        "explanation": "Rejections escape when they are created outside guarded regions or never awaited.",
    },
    # ------------------------------------------------------- api_integration
    {
        "id": "api_e1",
        "skill_id": "api_integration",
        "difficulty": 4,
        "type": "mcq",
        "concept": "HTTP status codes",
        "prompt": "Does `fetch()` reject its promise for an HTTP 404 response?",
        "options": [
            "Yes, any non-2xx rejects",
            "No — you must check response.ok",
            "Only for 5xx responses",
            "Only when using async/await",
        ],
        "correct_option": 1,
        "explanation": "fetch only rejects on network failures; HTTP errors resolve normally.",
    },
    {
        "id": "api_m1",
        "skill_id": "api_integration",
        "difficulty": 6,
        "type": "code_completion",
        "concept": "fetch",
        "prompt": "Write a function `getMovies()` that fetches /api/movies, throws on non-ok responses and returns parsed JSON.",
        "expected_answer": (
            "async function getMovies() {\n"
            "  const res = await fetch('/api/movies');\n"
            "  if (!res.ok) throw new Error(`HTTP ${res.status}`);\n"
            "  return res.json();\n"
            "}"
        ),
        "answer_checks": [r"fetch\(", r"res(ponse)?\.ok|status"],
        "explanation": "Always branch on response.ok before parsing.",
    },
    # -------------------------------------------------------------- react
    {
        "id": "react_e1",
        "skill_id": "react_fundamentals",
        "difficulty": 3,
        "type": "mcq",
        "concept": "props",
        "prompt": "Which statement about props is correct?",
        "options": [
            "Props are mutable inside the child component",
            "Props are read-only inputs to a component",
            "Props re-render only when state changes",
            "Props must always be strings",
        ],
        "correct_option": 1,
        "explanation": "Props are read-only; a component must not modify them.",
    },
    {
        "id": "react_state_m1",
        "skill_id": "react_state",
        "difficulty": 5,
        "type": "mcq",
        "concept": "useState",
        "prompt": "Calling `setCount(count + 1)` twice in the same handler increments by how much?",
        "options": ["2", "1", "0", "It throws"],
        "correct_option": 1,
        "explanation": "Both calls read the same stale `count`; use the updater form setCount(c => c + 1).",
    },
    {
        "id": "react_state_h1",
        "skill_id": "react_state",
        "difficulty": 7,
        "type": "code_debug",
        "concept": "useEffect",
        "prompt": "This component fetches on every render and floods the API. Fix it.",
        "code": "function Movies() {\n  const [movies, setMovies] = useState([]);\n  useEffect(() => {\n    fetch('/api/movies').then((r) => r.json()).then(setMovies);\n  });\n  return <List items={movies} />;\n}",
        "expected_answer": "Add an empty dependency array: useEffect(() => { ... }, []); and handle errors with .catch.",
        "answer_checks": [r"\[\s*\]|dependency|deps"],
        "explanation": "Without a dependency array the effect runs after every render.",
    },
    {
        "id": "react_fetch_h1",
        "skill_id": "react_data_fetching",
        "difficulty": 8,
        "type": "scenario",
        "concept": "loading states",
        "prompt": (
            "A dashboard shows a blank panel for several seconds and sometimes renders stale data "
            "after the user switches tabs quickly. Describe the two bugs and the fix."
        ),
        "expected_answer": (
            "There is no loading state, so nothing renders while the request is in flight; add explicit "
            "loading and error states. And the effect does not cancel the previous request, so an older "
            "response can resolve last and overwrite newer data; use an AbortController or an ignore flag "
            "in the effect cleanup."
        ),
        "answer_checks": [r"loading|abort|cleanup|ignore|cancel"],
        "explanation": "Race conditions require cleanup; UX requires explicit loading/error states.",
    },
    # ---------------------------------------------------------------- html
    {
        "id": "html_e1",
        "skill_id": "html_basics",
        "difficulty": 1,
        "type": "mcq",
        "concept": "elements",
        "prompt": "Which attribute is required on an `<img>` for accessibility?",
        "options": ["title", "alt", "aria-img", "caption"],
        "correct_option": 1,
        "explanation": "alt provides the text alternative used by screen readers.",
    },
    {
        "id": "html_sem_m1",
        "skill_id": "html_semantics",
        "difficulty": 4,
        "type": "mcq",
        "concept": "landmarks",
        "prompt": "Which element correctly wraps the primary content of a page?",
        "options": ["<div id=\"main\">", "<main>", "<section id=\"content\">", "<article>"],
        "correct_option": 1,
        "explanation": "<main> is the landmark for a document's primary content.",
    },
    {
        "id": "html_sem_h1",
        "skill_id": "html_semantics",
        "difficulty": 6,
        "type": "code_debug",
        "concept": "headings hierarchy",
        "prompt": "Explain what is wrong accessibility-wise:\n<div onclick=\"submit()\">Submit</div>",
        "expected_answer": "A div is not focusable or announced as a control; use a <button type=\"button\"> so it is keyboard accessible.",
        "answer_checks": [r"button|focus|keyboard|role"],
        "explanation": "Interactive controls must be real buttons (or have role + tabindex + key handlers).",
    },
    # ----------------------------------------------------------------- css
    {
        "id": "css_e1",
        "skill_id": "css_basics",
        "difficulty": 2,
        "type": "mcq",
        "concept": "box model",
        "prompt": "With `box-sizing: border-box`, what does `width` include?",
        "options": [
            "Content only",
            "Content, padding and border",
            "Content and margin",
            "Everything including margin",
        ],
        "correct_option": 1,
        "explanation": "border-box makes width include padding and border, but never margin.",
    },
    {
        "id": "css_layout_m1",
        "skill_id": "css_layout",
        "difficulty": 5,
        "type": "code_completion",
        "concept": "flexbox",
        "prompt": "Write the CSS for `.page` that centres a single child both horizontally and vertically in the viewport.",
        "expected_answer": ".page { display: flex; align-items: center; justify-content: center; min-height: 100vh; }",
        "answer_checks": [r"display\s*:\s*(flex|grid)", r"align-items\s*:\s*center", r"justify-content\s*:\s*center"],
        "explanation": "Flexbox centring needs both axes plus a height for the container.",
    },
    {
        "id": "css_resp_m1",
        "skill_id": "css_responsive",
        "difficulty": 6,
        "type": "mcq",
        "concept": "mobile first",
        "prompt": "In a mobile-first stylesheet, which media query direction do you write?",
        "options": ["max-width", "min-width", "orientation", "prefers-color-scheme"],
        "correct_option": 1,
        "explanation": "Mobile-first defines base styles for small screens, then enhances with min-width.",
    },
    # ------------------------------------------------------------- python
    {
        "id": "python_e1",
        "skill_id": "python_basics",
        "difficulty": 2,
        "type": "output_prediction",
        "concept": "lists",
        "prompt": "What does this print?",
        "code": "a = [1, 2, 3]\nb = a\nb.append(4)\nprint(len(a))",
        "expected_answer": "4",
        "answer_checks": [r"^\s*4\s*$"],
        "explanation": "Lists are references; b and a point at the same object.",
    },
    {
        "id": "dsa_m1",
        "skill_id": "dsa_arrays",
        "difficulty": 5,
        "type": "mcq",
        "concept": "complexity",
        "prompt": "What is the time complexity of rotating an array of n elements by k using slicing?",
        "options": ["O(n*k)", "O(n)", "O(log n)", "O(k^2)"],
        "correct_option": 1,
        "explanation": "Slice-and-concat touches each element a constant number of times.",
    },
    {
        "id": "dsa_h1",
        "skill_id": "dsa_arrays",
        "difficulty": 7,
        "type": "scenario",
        "concept": "edge cases",
        "prompt": "Rotating by k crashes when k > n. What single change fixes it, and what other edge case must you handle?",
        "expected_answer": "Normalise with k = k % n, and guard against n == 0 (or an empty array) before taking the modulus.",
        "answer_checks": [r"%|mod", r"empty|zero|0|n\s*==\s*0"],
        "explanation": "Modulo normalises k; an empty array would make the modulus a division by zero.",
    },
    # -------------------------------------------------------- other languages
    {
        "id": "java_e1",
        "skill_id": "java_basics",
        "difficulty": 3,
        "type": "mcq",
        "concept": "types",
        "prompt": "What is the default value of an `int` field in a Java class?",
        "options": ["null", "0", "undefined", "It must be initialised"],
        "correct_option": 1,
        "explanation": "Numeric instance fields default to 0.",
    },
    {
        "id": "c_e1",
        "skill_id": "c_basics",
        "difficulty": 4,
        "type": "mcq",
        "concept": "pointers",
        "prompt": "What does `sizeof(arr)` yield inside a function that received `int arr[]` as a parameter?",
        "options": [
            "The full array size in bytes",
            "The size of a pointer",
            "The number of elements",
            "A compile error",
        ],
        "correct_option": 1,
        "explanation": "Array parameters decay to pointers, so sizeof gives the pointer size.",
    },
    {
        "id": "cpp_e1",
        "skill_id": "cpp_basics",
        "difficulty": 4,
        "type": "mcq",
        "concept": "vectors",
        "prompt": "Why pass a large `std::vector<int>` as `const std::vector<int>&`?",
        "options": [
            "It allows modification",
            "It avoids copying the whole vector",
            "It makes the vector thread-safe",
            "It is required by the STL",
        ],
        "correct_option": 1,
        "explanation": "A const reference avoids an O(n) copy while preventing mutation.",
    },
]


# Backend and application-architecture items live in their own module to keep
# this file navigable; they are part of the same bank.
ASSESSMENT_ITEMS.extend(BACKEND_ITEMS)

# Data-analysis items, for the skills the Data Analyst path is built on.
ASSESSMENT_ITEMS.extend(DATA_ITEMS)

_seen_ids = {i["id"] for i in ASSESSMENT_ITEMS}
if len(_seen_ids) != len(ASSESSMENT_ITEMS):
    raise RuntimeError("duplicate assessment item id detected")

ITEMS_BY_SKILL: dict[str, list[dict[str, Any]]] = {}
for _item in ASSESSMENT_ITEMS:
    ITEMS_BY_SKILL.setdefault(_item["skill_id"], []).append(_item)
for _items in ITEMS_BY_SKILL.values():
    _items.sort(key=lambda i: i["difficulty"])

ITEM_INDEX: dict[str, dict[str, Any]] = {i["id"]: i for i in ASSESSMENT_ITEMS}
