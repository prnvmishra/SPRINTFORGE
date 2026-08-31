"""Curated *external* references, one small set per knowledge-graph skill.

Philosophy: "learn only what you need, when you need it". This file therefore
holds no curricula, no courses and no invented content — only canonical
documentation that is stable enough to link to for years (MDN, react.dev,
nodejs.org, postgresql.org, docs.python.org, Oracle's Java tutorial,
cppreference, pandas, SciPy, Matplotlib, Vega-Lite, and the Microsoft/Google
spreadsheet function references). Anything internal (practice modules, adaptive assessments, the
course that teaches the skill) is *not* listed here: it is resolved at read time
from ``PRACTICE_MODULE_INDEX``, ``ITEMS_BY_SKILL`` and
``paths.course_ids_for_skill`` so this file can never drift from the catalog.

Each entry:
  kind    - concept_guide | documentation | challenge
  title   - what the page actually is
  minutes - honest reading estimate for the linked page, not a course length
  url     - canonical documentation URL
"""

from __future__ import annotations

from typing import Any

MDN = "https://developer.mozilla.org/en-US/docs"
PANDAS = "https://pandas.pydata.org/docs"
MATPLOTLIB = "https://matplotlib.org/stable"
VEGA_LITE = "https://vega.github.io/vega-lite/docs"

EXTERNAL_RESOURCES: dict[str, list[dict[str, Any]]] = {
    "html_basics": [
        {"kind": "concept_guide", "title": "MDN: HTML basics", "minutes": 20, "url": f"{MDN}/Web/HTML"},
        {"kind": "documentation", "title": "MDN: HTML element reference", "minutes": 10, "url": f"{MDN}/Web/HTML/Element"},
    ],
    "html_semantics": [
        {"kind": "concept_guide", "title": "MDN: ARIA and accessible markup", "minutes": 25, "url": f"{MDN}/Web/Accessibility/ARIA"},
        {"kind": "documentation", "title": "MDN: HTML element reference (sectioning elements)", "minutes": 10, "url": f"{MDN}/Web/HTML/Element"},
        {"kind": "documentation", "title": "WAI-ARIA Authoring Practices", "minutes": 20, "url": "https://www.w3.org/WAI/ARIA/apg/"},
    ],
    "css_basics": [
        {"kind": "concept_guide", "title": "MDN: CSS", "minutes": 20, "url": f"{MDN}/Web/CSS"},
        {"kind": "documentation", "title": "MDN: The box model", "minutes": 15, "url": f"{MDN}/Web/CSS/CSS_box_model"},
    ],
    "css_layout": [
        {"kind": "concept_guide", "title": "MDN: Flexbox layout", "minutes": 25, "url": f"{MDN}/Web/CSS/CSS_flexible_box_layout"},
        {"kind": "concept_guide", "title": "MDN: Grid layout", "minutes": 25, "url": f"{MDN}/Web/CSS/CSS_grid_layout"},
    ],
    "css_responsive": [
        {"kind": "concept_guide", "title": "MDN: Media queries", "minutes": 20, "url": f"{MDN}/Web/CSS/CSS_media_queries"},
        {"kind": "documentation", "title": "MDN: Viewport meta tag", "minutes": 8, "url": f"{MDN}/Web/HTML/Viewport_meta_tag"},
    ],
    "js_basics": [
        {"kind": "concept_guide", "title": "MDN: JavaScript guide", "minutes": 30, "url": f"{MDN}/Web/JavaScript/Guide"},
        {"kind": "documentation", "title": "MDN: JavaScript reference", "minutes": 10, "url": f"{MDN}/Web/JavaScript/Reference"},
    ],
    "js_functions": [
        {"kind": "concept_guide", "title": "MDN: Functions", "minutes": 25, "url": f"{MDN}/Web/JavaScript/Guide/Functions"},
        {"kind": "documentation", "title": "MDN: Closures", "minutes": 20, "url": f"{MDN}/Web/JavaScript/Guide/Closures"},
    ],
    "js_dom": [
        {"kind": "concept_guide", "title": "MDN: Document Object Model", "minutes": 25, "url": f"{MDN}/Web/API/Document_Object_Model"},
        {"kind": "documentation", "title": "MDN: addEventListener", "minutes": 10, "url": f"{MDN}/Web/API/EventTarget/addEventListener"},
    ],
    "js_async": [
        {"kind": "concept_guide", "title": "MDN: Using promises", "minutes": 25, "url": f"{MDN}/Web/JavaScript/Guide/Using_promises"},
        {"kind": "documentation", "title": "MDN: async function", "minutes": 12, "url": f"{MDN}/Web/JavaScript/Reference/Statements/async_function"},
    ],
    "js_async_error_handling": [
        {"kind": "documentation", "title": "MDN: try...catch", "minutes": 12, "url": f"{MDN}/Web/JavaScript/Reference/Statements/try...catch"},
        {"kind": "documentation", "title": "MDN: Response.ok (why fetch does not throw on 404)", "minutes": 8, "url": f"{MDN}/Web/API/Response/ok"},
        {"kind": "concept_guide", "title": "MDN: Using the Fetch API", "minutes": 20, "url": f"{MDN}/Web/API/Fetch_API/Using_Fetch"},
    ],
    "api_integration": [
        {"kind": "concept_guide", "title": "MDN: Using the Fetch API", "minutes": 20, "url": f"{MDN}/Web/API/Fetch_API/Using_Fetch"},
        {"kind": "documentation", "title": "MDN: CORS", "minutes": 20, "url": f"{MDN}/Web/HTTP/CORS"},
        {"kind": "documentation", "title": "MDN: AbortController (cancelling requests)", "minutes": 10, "url": f"{MDN}/Web/API/AbortController"},
    ],
    "react_fundamentals": [
        {"kind": "concept_guide", "title": "react.dev: Learn React", "minutes": 30, "url": "https://react.dev/learn"},
        {"kind": "concept_guide", "title": "react.dev: Thinking in React", "minutes": 20, "url": "https://react.dev/learn/thinking-in-react"},
    ],
    "react_state": [
        {"kind": "documentation", "title": "react.dev: useState", "minutes": 15, "url": "https://react.dev/reference/react/useState"},
        {"kind": "concept_guide", "title": "react.dev: Managing state", "minutes": 25, "url": "https://react.dev/learn/managing-state"},
    ],
    "react_data_fetching": [
        {"kind": "documentation", "title": "react.dev: useEffect", "minutes": 20, "url": "https://react.dev/reference/react/useEffect"},
        {"kind": "concept_guide", "title": "react.dev: You might not need an Effect", "minutes": 20, "url": "https://react.dev/learn/you-might-not-need-an-effect"},
    ],
    "react_dashboard": [
        {"kind": "concept_guide", "title": "react.dev: Scaling up with Reducer and Context", "minutes": 25, "url": "https://react.dev/learn/scaling-up-with-reducer-and-context"},
        {"kind": "concept_guide", "title": "react.dev: Choosing the state structure", "minutes": 20, "url": "https://react.dev/learn/choosing-the-state-structure"},
    ],
    "node_basics": [
        {"kind": "concept_guide", "title": "nodejs.org: Introduction to Node.js", "minutes": 20, "url": "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs"},
        {"kind": "documentation", "title": "nodejs.org: API reference", "minutes": 10, "url": "https://nodejs.org/docs/latest/api/"},
    ],
    "rest_api": [
        {"kind": "documentation", "title": "MDN: HTTP request methods", "minutes": 12, "url": f"{MDN}/Web/HTTP/Methods"},
        {"kind": "documentation", "title": "MDN: HTTP response status codes", "minutes": 15, "url": f"{MDN}/Web/HTTP/Status"},
        {"kind": "documentation", "title": "Express: routing guide", "minutes": 15, "url": "https://expressjs.com/en/guide/routing.html"},
    ],
    "database_modeling": [
        {"kind": "concept_guide", "title": "PostgreSQL: Data definition (tables, keys)", "minutes": 30, "url": "https://www.postgresql.org/docs/current/ddl.html"},
        {"kind": "documentation", "title": "PostgreSQL: Constraints", "minutes": 20, "url": "https://www.postgresql.org/docs/current/ddl-constraints.html"},
        {"kind": "concept_guide", "title": "PostgreSQL: SQL tutorial", "minutes": 25, "url": "https://www.postgresql.org/docs/current/tutorial-sql.html"},
    ],
    "python_basics": [
        {"kind": "concept_guide", "title": "docs.python.org: The Python tutorial", "minutes": 30, "url": "https://docs.python.org/3/tutorial/"},
        {"kind": "documentation", "title": "docs.python.org: Built-in types", "minutes": 15, "url": "https://docs.python.org/3/library/stdtypes.html"},
    ],
    "dsa_arrays": [
        {"kind": "documentation", "title": "MDN: Array methods reference", "minutes": 15, "url": f"{MDN}/Web/JavaScript/Reference/Global_Objects/Array"},
        {"kind": "documentation", "title": "docs.python.org: Data structures (lists)", "minutes": 20, "url": "https://docs.python.org/3/tutorial/datastructures.html"},
    ],
    "java_basics": [
        {"kind": "concept_guide", "title": "Oracle: Java tutorial — Learning the Java language", "minutes": 30, "url": "https://docs.oracle.com/javase/tutorial/java/index.html"},
        {"kind": "documentation", "title": "Oracle: Java SE API documentation", "minutes": 10, "url": "https://docs.oracle.com/en/java/javase/21/docs/api/index.html"},
    ],
    "c_basics": [
        {"kind": "documentation", "title": "cppreference: C language reference", "minutes": 25, "url": "https://en.cppreference.com/w/c/language"},
        {"kind": "documentation", "title": "cppreference: C standard library", "minutes": 15, "url": "https://en.cppreference.com/w/c/header"},
    ],
    "cpp_basics": [
        {"kind": "documentation", "title": "cppreference: C++ language reference", "minutes": 25, "url": "https://en.cppreference.com/w/cpp/language"},
        {"kind": "documentation", "title": "cppreference: Containers library", "minutes": 20, "url": "https://en.cppreference.com/w/cpp/container"},
    ],
    "data_cleaning": [
        {"kind": "concept_guide", "title": "pandas: Working with missing data", "minutes": 25, "url": f"{PANDAS}/user_guide/missing_data.html"},
        {"kind": "documentation", "title": "pandas: drop_duplicates", "minutes": 8, "url": f"{PANDAS}/reference/api/pandas.DataFrame.drop_duplicates.html"},
        {"kind": "documentation", "title": "pandas: dtypes and type conversion", "minutes": 15, "url": f"{PANDAS}/user_guide/basics.html#dtypes"},
    ],
    "exploratory_analysis": [
        {"kind": "concept_guide", "title": "pandas: Group by — split-apply-combine", "minutes": 30, "url": f"{PANDAS}/user_guide/groupby.html"},
        {"kind": "concept_guide", "title": "pandas: Reshaping and pivot tables", "minutes": 25, "url": f"{PANDAS}/user_guide/reshaping.html"},
        {"kind": "documentation", "title": "pandas: DataFrame.describe", "minutes": 8, "url": f"{PANDAS}/reference/api/pandas.DataFrame.describe.html"},
    ],
    "statistics_business": [
        {"kind": "documentation", "title": "docs.python.org: statistics module (mean, median, variance)", "minutes": 15, "url": "https://docs.python.org/3/library/statistics.html"},
        {"kind": "concept_guide", "title": "SciPy: Statistics tutorial", "minutes": 30, "url": "https://docs.scipy.org/doc/scipy/tutorial/stats.html"},
        {"kind": "documentation", "title": "SciPy: ttest_ind (comparing two groups)", "minutes": 12, "url": "https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html"},
    ],
    "data_visualization": [
        {"kind": "concept_guide", "title": "Matplotlib: Quick start guide", "minutes": 25, "url": f"{MATPLOTLIB}/users/explain/quick_start.html"},
        {"kind": "documentation", "title": "Matplotlib: Plot types (choosing a chart)", "minutes": 12, "url": f"{MATPLOTLIB}/plot_types/index.html"},
        {"kind": "documentation", "title": "Vega-Lite: Encoding (mapping data to visual channels)", "minutes": 20, "url": f"{VEGA_LITE}/encoding.html"},
    ],
    "dashboard_design": [
        {"kind": "concept_guide", "title": "Matplotlib: Arranging multiple axes in a figure", "minutes": 20, "url": f"{MATPLOTLIB}/users/explain/axes/arranging_axes.html"},
        {"kind": "documentation", "title": "Vega-Lite: Concatenating views into one dashboard", "minutes": 15, "url": f"{VEGA_LITE}/concat.html"},
        {"kind": "documentation", "title": "Vega-Lite: Selections and drill-down interaction", "minutes": 20, "url": f"{VEGA_LITE}/selection.html"},
    ],
    "spreadsheet_modeling": [
        {"kind": "documentation", "title": "Microsoft: Create a PivotTable to analyse worksheet data", "minutes": 15, "url": "https://support.microsoft.com/en-us/office/create-a-pivottable-to-analyze-worksheet-data-a9a84538-bfe9-40a9-a8e9-f99134456576"},
        {"kind": "documentation", "title": "Microsoft: XLOOKUP function", "minutes": 12, "url": "https://support.microsoft.com/en-us/office/xlookup-function-b7fd680e-6d10-43e6-84f9-88eae8bf5929"},
        {"kind": "documentation", "title": "Google Sheets: Function list", "minutes": 10, "url": "https://support.google.com/docs/table/25273"},
    ],
}
