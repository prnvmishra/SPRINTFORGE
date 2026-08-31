"""Career path registry: Path -> Course -> {knowledge, test, project}.

This is the top-level information architecture. A learner picks a career path,
works through its courses in order, and each course carries three things:

* **knowledge** — the ordered skills it teaches, plus the practice modules that
  make the learner implement them immediately.
* **test**      — an adaptive assessment over the course's skills.
* **project**   — a pre-filled brief that seeds the existing project generator,
  so the course ends in something shipped rather than a certificate.

Design notes
------------
Courses do **not** hardcode their practice modules. A course declares its
skills, and modules are matched by ``skill_id`` at read time, so authoring a new
problem automatically files it under the right course.

Ordering inside a course is likewise not hardcoded: the path service asks
``KnowledgeGraph.learning_path()`` so prerequisites always come first and stay
consistent with the graph if the graph changes.

Paths marked ``available: False`` are registered but have no curriculum behind
them yet. They are surfaced honestly rather than hidden, and never pretend to
contain content — the knowledge graph currently holds only software-engineering
skills, so data and operations paths need their own skill nodes, assessment
items and practice problems before they can be turned on.
"""

from __future__ import annotations

from typing import Any, Optional


def _project(
    title: str,
    idea: str,
    tech_stack: list[str],
    outcome: str,
    complexity: str = "intermediate",
) -> dict[str, Any]:
    """A course capstone, shaped to seed ProjectCreateRequest directly."""
    return {
        "title": title,
        "idea": idea,
        "tech_stack": tech_stack,
        "complexity": complexity,
        "desired_outcome": outcome,
    }


# --------------------------------------------------------------------------- #
#  SDE path — the only path with a full curriculum behind it today            #
# --------------------------------------------------------------------------- #

SDE_COURSES: list[dict[str, Any]] = [
    {
        "id": "web-foundations",
        "title": "Web Foundations: HTML & CSS",
        "blurb": (
            "Structure a page with semantic markup, then lay it out and make it "
            "respond to any screen. Everything else on this path sits on top of this."
        ),
        "skills": [
            "html_basics",
            "html_semantics",
            "css_basics",
            "css_layout",
            "css_responsive",
        ],
        "project": _project(
            title="Responsive Profile Card",
            idea=(
                "Build a profile card page with semantic HTML and a responsive "
                "layout that works from 320px to desktop, using flexbox or grid "
                "and no layout libraries."
            ),
            tech_stack=["HTML", "CSS"],
            outcome="A hand-built, accessible, responsive page with no framework.",
            complexity="beginner",
        ),
    },
    {
        "id": "javascript-programming",
        "title": "JavaScript Programming",
        "blurb": (
            "Values, scope and functions first, then driving the DOM. This is "
            "where a static page starts responding to a user."
        ),
        "skills": ["js_basics", "js_functions", "js_dom"],
        "project": _project(
            title="Interactive Task Tracker",
            idea=(
                "Build a task tracker where a user can add, complete and remove "
                "tasks. Render the list from an array in memory and update the "
                "DOM on every change. No framework."
            ),
            tech_stack=["HTML", "CSS", "JavaScript"],
            outcome="A working DOM-driven app built without a framework.",
            complexity="beginner",
        ),
    },
    {
        "id": "async-and-apis",
        "title": "Async JavaScript & API Integration",
        "blurb": (
            "Promises, async/await, and the part most people skip: handling the "
            "request that fails. Real data arrives late and sometimes not at all."
        ),
        "skills": ["js_async", "js_async_error_handling", "api_integration"],
        "project": _project(
            title="Movie Browser with Live Data",
            idea=(
                "Build a movie browser that fetches from a REST API, shows loading "
                "and error states, and never leaves the user staring at a blank "
                "screen when the network fails."
            ),
            tech_stack=["HTML", "CSS", "JavaScript", "API"],
            outcome="An app that behaves correctly when the network misbehaves.",
        ),
    },
    {
        "id": "react-development",
        "title": "React Development",
        "blurb": (
            "Components, state and data fetching, up to structuring an application "
            "that stays readable once it grows past one screen."
        ),
        "skills": [
            "react_fundamentals",
            "react_state",
            "react_data_fetching",
            "react_dashboard",
        ],
        "project": _project(
            title="React Movie Ticket Booking System",
            idea=(
                "Build a seat-selection and booking flow in React: list showings "
                "from an API, select seats with derived state, and show a booking "
                "summary. Keep state colocated and derive what you can."
            ),
            tech_stack=["React", "JavaScript", "API"],
            outcome="A multi-screen React app with real data and derived state.",
            complexity="advanced",
        ),
    },
    {
        "id": "backend-and-data",
        "title": "Backend & Databases",
        "blurb": (
            "Serve the data instead of consuming someone else's: a Node server, "
            "REST endpoints that behave, and a schema that will not fight you later."
        ),
        "skills": ["node_basics", "rest_api", "database_modeling"],
        "project": _project(
            title="Task Tracker REST API",
            idea=(
                "Build a REST API for tasks with proper status codes, validation, "
                "and a relational schema with the right keys and constraints."
            ),
            tech_stack=["Node.js", "Database", "REST"],
            outcome="A running API backed by a schema you designed.",
        ),
    },
    {
        "id": "dsa-problem-solving",
        "title": "DSA & Problem Solving",
        "blurb": (
            "Judged algorithmic problems with hidden tests and complexity limits. "
            "This is the course that prepares you for interview rounds."
        ),
        "skills": ["python_basics", "dsa_arrays"],
        "project": None,  # Judged problems are the deliverable here, not an app.
    },
]


DATA_ANALYST_COURSES: list[dict[str, Any]] = [
    {
        "id": "sql-for-analysis",
        "title": "SQL for Analysis",
        "blurb": (
            "Read a schema you did not design, then filter, join and aggregate it "
            "until it answers a question. Every later course assumes you can get "
            "the numbers out yourself."
        ),
        "skills": ["sql_basics", "sql_joins", "sql_aggregation", "sql_analytics"],
        "project": _project(
            title="Retail Revenue Report",
            idea=(
                "Given an orders, customers and products schema, write the queries "
                "behind a monthly revenue report: revenue by category, repeat-customer "
                "rate, and month-over-month change using window functions."
            ),
            tech_stack=["SQL"],
            outcome=(
                "A set of queries that answer stated business questions and survive "
                "being run against a different month of data."
            ),
            complexity="beginner",
        ),
    },
    {
        "id": "cleaning-and-exploration",
        "title": "Data Cleaning & Exploration",
        "blurb": (
            "Real extracts arrive with duplicates, inconsistent labels and missing "
            "values. Clean them defensibly, then explore before you conclude."
        ),
        "skills": ["data_cleaning", "exploratory_analysis"],
        "project": _project(
            title="Messy Extract Cleanup",
            idea=(
                "Take a deliberately dirty sales extract — duplicate rows, mixed date "
                "formats, inconsistent city spellings, missing amounts — and produce a "
                "cleaned dataset plus a written note on every rule you applied and why."
            ),
            tech_stack=["Python", "pandas"],
            outcome=(
                "A reproducible cleaning script whose decisions are documented rather "
                "than silent."
            ),
            complexity="beginner",
        ),
    },
    {
        "id": "statistics-for-business",
        "title": "Statistics for Business Questions",
        "blurb": (
            "Enough statistics to avoid confident nonsense: distributions, variation, "
            "and whether a difference you are looking at means anything."
        ),
        "skills": ["statistics_business"],
        "project": _project(
            title="Did the Promotion Work?",
            idea=(
                "Compare sales before and after a promotion, quantify the difference, "
                "and state plainly whether the data supports the claim — including what "
                "would have to be true for the conclusion to be wrong."
            ),
            tech_stack=["Python", "pandas"],
            outcome=(
                "A conclusion with its uncertainty stated, not a single number presented "
                "as fact."
            ),
        ),
    },
    {
        "id": "visualisation-and-dashboards",
        "title": "Visualisation & Dashboards",
        "blurb": (
            "Charts that answer a question instead of decorating a screen, assembled "
            "into a dashboard someone can actually act on."
        ),
        "skills": ["data_visualization", "dashboard_design"],
        "project": _project(
            title="Operations Dashboard",
            idea=(
                "Design a one-screen dashboard for a store manager: pick the few metrics "
                "that drive a decision, choose chart types that suit each one, and justify "
                "everything you left out."
            ),
            tech_stack=["Python", "pandas", "matplotlib"],
            outcome=(
                "A dashboard defensible metric by metric, with the omissions argued for."
            ),
        ),
    },
    {
        "id": "spreadsheet-modelling",
        "title": "Spreadsheet Modelling",
        "blurb": (
            "The tool most business decisions are still made in: build a model that is "
            "auditable, not a grid of magic numbers."
        ),
        "skills": ["spreadsheet_modeling"],
        "project": _project(
            title="Hiring Budget Model",
            idea=(
                "Model a year of hiring cost with assumptions held in named, separated "
                "inputs, so a reviewer can change salary or headcount and watch every "
                "dependent figure update correctly."
            ),
            tech_stack=["Spreadsheets"],
            outcome=(
                "A model where assumptions live in one place and no result is hardcoded."
            ),
        ),
    },
]


# --------------------------------------------------------------------------- #
#  Path registry                                                              #
# --------------------------------------------------------------------------- #

PATHS: list[dict[str, Any]] = [
    {
        "id": "sde",
        "label": "SDE — Software Development Engineer",
        "tagline": "Build and ship software, then prove it under a judge.",
        "blurb": (
            "The full engineering track: markup and layout, JavaScript, async and "
            "APIs, React, backend and databases, plus judged DSA problems. Every "
            "course ends in something you built and something that graded you."
        ),
        "roles": ["Frontend Engineer", "Backend Engineer", "Full-stack Engineer"],
        "available": True,
        "courses": SDE_COURSES,
    },
    {
        "id": "data-analyst",
        "label": "Data Analyst",
        "tagline": "Turn raw tables into decisions someone can act on.",
        "blurb": (
            "SQL, spreadsheet modelling, statistics for business questions, and "
            "dashboards that answer something instead of decorating a screen."
        ),
        "roles": ["Data Analyst", "Business Analyst", "BI Analyst"],
        "available": True,
        "courses": DATA_ANALYST_COURSES,
    },
    {
        "id": "data-scientist",
        "label": "Data Scientist",
        "tagline": "Model the problem, then defend the model.",
        "blurb": (
            "Python for data, statistics and inference, feature work, and machine "
            "learning judged on held-out data rather than on a notebook that ran."
        ),
        "roles": ["Data Scientist", "ML Engineer", "Research Analyst"],
        "available": False,
        "planned_courses": [
            "Python for Data",
            "Statistics & Inference",
            "Feature Engineering",
            "Machine Learning Fundamentals",
            "Model Evaluation & Validation",
        ],
        "courses": [],
    },
    {
        "id": "devops-sre",
        "label": "DevOps / SRE — Operations",
        "tagline": "Keep it running, and know why when it stops.",
        "blurb": (
            "Linux and shell, containers, CI/CD pipelines, infrastructure as code, "
            "and the observability you need before an incident, not during one."
        ),
        "roles": ["DevOps Engineer", "SRE", "Platform Engineer", "Cloud Engineer"],
        "available": False,
        "planned_courses": [
            "Linux & Shell",
            "Containers & Docker",
            "CI/CD Pipelines",
            "Infrastructure as Code",
            "Observability & Incident Response",
        ],
        "courses": [],
    },
    {
        "id": "qa-sdet",
        "label": "QA / SDET",
        "tagline": "Break it on purpose, then automate the break.",
        "blurb": (
            "Test design and boundary analysis, automation frameworks, API and "
            "performance testing, and building a suite that catches regressions."
        ),
        "roles": ["QA Engineer", "SDET", "Automation Engineer"],
        "available": False,
        "planned_courses": [
            "Test Design & Boundary Analysis",
            "UI Automation",
            "API & Contract Testing",
            "Performance Testing",
        ],
        "courses": [],
    },
    {
        "id": "non-sde",
        "label": "Non-SDE — Product & Business",
        "tagline": "Decide what gets built and why.",
        "blurb": (
            "Product thinking, requirements and user stories, metrics and "
            "experiment design, and enough technical literacy to argue with "
            "engineers productively."
        ),
        "roles": ["Product Manager", "Business Analyst", "Technical Program Manager"],
        "available": False,
        "planned_courses": [
            "Product Thinking",
            "Requirements & User Stories",
            "Metrics & Experimentation",
            "Technical Literacy for PMs",
        ],
        "courses": [],
    },
]

PATH_INDEX: dict[str, dict[str, Any]] = {p["id"]: p for p in PATHS}

COURSE_INDEX: dict[tuple[str, str], dict[str, Any]] = {
    (path["id"], course["id"]): course for path in PATHS for course in path["courses"]
}


def find_course(path_id: str, course_id: str) -> Optional[dict[str, Any]]:
    return COURSE_INDEX.get((path_id, course_id))


def course_ids_for_skill(skill_id: str) -> list[tuple[str, str]]:
    """Reverse lookup, used to tell a learner which course a skill belongs to."""
    return [
        (path["id"], course["id"])
        for path in PATHS
        for course in path["courses"]
        if skill_id in course["skills"]
    ]
