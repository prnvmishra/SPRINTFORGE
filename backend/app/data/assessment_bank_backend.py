"""Assessment items for the backend and application-architecture skills.

These four skills had no items at all, which left the SDE path's "Backend &
Databases" course untestable and its "React Development" course thin. Items
follow the same contract as the main bank: difficulty 1-10, one correct option
per MCQ, and an explanation that teaches rather than just confirms.

Difficulty is spread deliberately so the adaptive engine has somewhere to move
in both directions instead of replaying a single tier.
"""

from __future__ import annotations

from typing import Any

BACKEND_ITEMS: list[dict[str, Any]] = [
    # --------------------------------------------------------- node_basics
    {
        "id": "node_basics_e1",
        "skill_id": "node_basics",
        "difficulty": 2,
        "type": "mcq",
        "concept": "modules",
        "prompt": "In a CommonJS Node module, what does `module.exports` do?",
        "options": [
            "Declares which npm packages the file depends on",
            "Defines the value returned when another file calls require() on this module",
            "Loads a module synchronously from node_modules",
            "Registers the file as an entry point in package.json",
        ],
        "correct_option": 1,
        "explanation": (
            "module.exports is the module's public value. require() returns whatever "
            "it points to at the time the module finishes executing."
        ),
    },
    {
        "id": "node_basics_e2",
        "skill_id": "node_basics",
        "difficulty": 3,
        "type": "mcq",
        "concept": "event loop",
        "prompt": (
            "Node is single-threaded for your JavaScript. Why can it still handle "
            "many concurrent requests?"
        ),
        "options": [
            "It spawns a new thread for every incoming request",
            "I/O is delegated to the system and completions are queued as callbacks, so the thread is never left waiting",
            "Requests are processed in strict order, one fully finished before the next begins",
            "The V8 engine runs JavaScript in parallel across CPU cores",
        ],
        "correct_option": 1,
        "explanation": (
            "Blocking work is handed off; the event loop only runs your callbacks "
            "when the I/O has already completed. CPU-bound work still blocks it."
        ),
    },
    {
        "id": "node_basics_m1",
        "skill_id": "node_basics",
        "difficulty": 5,
        "type": "output_prediction",
        "concept": "event loop ordering",
        "prompt": "In what order do these lines print?",
        "code": (
            "console.log('a');\n"
            "setTimeout(() => console.log('b'), 0);\n"
            "Promise.resolve().then(() => console.log('c'));\n"
            "console.log('d');"
        ),
        "expected_answer": "a d c b",
        "answer_checks": [r"a\s*,?\s*d\s*,?\s*c\s*,?\s*b"],
        "explanation": (
            "Synchronous code first (a, d). Then microtasks — the promise callback (c) "
            "— and only then the timer macrotask (b)."
        ),
    },
    {
        "id": "node_basics_h1",
        "skill_id": "node_basics",
        "difficulty": 7,
        "type": "mcq",
        "concept": "blocking",
        "prompt": (
            "A request handler runs a tight loop over 50 million numbers. What is the "
            "effect on a Node server?"
        ),
        "options": [
            "Only that one request is slow; others are served normally",
            "Every other request stalls until the loop finishes, because the event loop is blocked",
            "Node moves the loop to a worker thread automatically",
            "The request times out but throughput is unaffected",
        ],
        "correct_option": 1,
        "explanation": (
            "CPU-bound work occupies the single JavaScript thread. Nothing else runs "
            "until it yields — this is why such work belongs in a worker thread or a queue."
        ),
    },
    # ------------------------------------------------------------ rest_api
    {
        "id": "rest_api_e1",
        "skill_id": "rest_api",
        "difficulty": 2,
        "type": "mcq",
        "concept": "status codes",
        "prompt": (
            "A client POSTs a new resource and it is created successfully. Which "
            "status code is correct?"
        ),
        "options": ["200 OK", "201 Created", "202 Accepted", "204 No Content"],
        "correct_option": 1,
        "explanation": (
            "201 signals a new resource exists, and should carry its location. 200 is "
            "for a successful request that did not create anything."
        ),
    },
    {
        "id": "rest_api_e2",
        "skill_id": "rest_api",
        "difficulty": 3,
        "type": "mcq",
        "concept": "status codes",
        "prompt": (
            "A request arrives with a well-formed body, but the email field fails "
            "validation. Which response is most appropriate?"
        ),
        "options": [
            "500 Internal Server Error",
            "400 Bad Request with details about the invalid field",
            "404 Not Found",
            "403 Forbidden",
        ],
        "correct_option": 1,
        "explanation": (
            "The client can fix this, so it is a 4xx. A 500 would wrongly blame the "
            "server and hide a user-correctable problem."
        ),
    },
    {
        "id": "rest_api_m1",
        "skill_id": "rest_api",
        "difficulty": 5,
        "type": "mcq",
        "concept": "idempotency",
        "prompt": "Which HTTP method is expected to be idempotent?",
        "options": [
            "POST",
            "PUT",
            "PATCH as commonly implemented",
            "None of them are",
        ],
        "correct_option": 1,
        "explanation": (
            "PUT replaces a resource, so repeating the same PUT leaves the same state. "
            "Repeating a POST typically creates another resource."
        ),
    },
    {
        "id": "rest_api_h1",
        "skill_id": "rest_api",
        "difficulty": 7,
        "type": "mcq",
        "concept": "resource design",
        "prompt": (
            "Which endpoint best follows REST resource conventions for listing a "
            "user's orders?"
        ),
        "options": [
            "GET /getUserOrders?id=42",
            "GET /users/42/orders",
            "POST /orders/fetchByUser",
            "GET /api/doGetOrders/42",
        ],
        "correct_option": 1,
        "explanation": (
            "REST identifies nouns hierarchically and lets the method express the verb. "
            "Actions encoded in the path are RPC, not REST."
        ),
    },
    # --------------------------------------------------- database_modeling
    {
        "id": "database_modeling_e1",
        "skill_id": "database_modeling",
        "difficulty": 2,
        "type": "mcq",
        "concept": "keys",
        "prompt": "What does a primary key guarantee about a table?",
        "options": [
            "Its column is indexed for faster text search",
            "Every row is uniquely identifiable and the column cannot be null",
            "Rows are physically stored in sorted order",
            "Values in the column increase automatically",
        ],
        "correct_option": 1,
        "explanation": (
            "Uniqueness and non-nullability are the guarantees. Auto-increment and "
            "clustering are separate, optional features."
        ),
    },
    {
        "id": "database_modeling_e2",
        "skill_id": "database_modeling",
        "difficulty": 3,
        "type": "mcq",
        "concept": "relationships",
        "prompt": (
            "A task belongs to exactly one project, and a project has many tasks. How "
            "should this be modelled?"
        ),
        "options": [
            "A project_ids array column on tasks",
            "A project_id foreign key column on tasks referencing projects(id)",
            "A join table between tasks and projects",
            "Duplicate the project's columns onto every task row",
        ],
        "correct_option": 1,
        "explanation": (
            "One-to-many puts the foreign key on the many side. A join table is for "
            "many-to-many, and duplication invites inconsistency."
        ),
    },
    {
        "id": "database_modeling_m1",
        "skill_id": "database_modeling",
        "difficulty": 5,
        "type": "mcq",
        "concept": "normalisation",
        "prompt": (
            "An orders table repeats customer_name and customer_email on every row. "
            "What is the main risk?"
        ),
        "options": [
            "Queries become slower because rows are wider",
            "The same customer can end up with conflicting details across rows, with no single source of truth",
            "The table cannot be indexed",
            "Foreign keys stop working",
        ],
        "correct_option": 1,
        "explanation": (
            "Update anomalies are the real cost: correcting an email means finding "
            "every row, and missing one leaves the data contradicting itself."
        ),
    },
    {
        "id": "database_modeling_h1",
        "skill_id": "database_modeling",
        "difficulty": 7,
        "type": "mcq",
        "concept": "many-to-many",
        "prompt": (
            "A student can enrol in many courses, and a course has many students. "
            "Enrolment also has its own date. What is the correct schema?"
        ),
        "options": [
            "A courses array column on students",
            "An enrolments table with student_id, course_id and enrolled_at, unique on (student_id, course_id)",
            "A student_id column on courses",
            "A course_id column on students",
        ],
        "correct_option": 1,
        "explanation": (
            "Many-to-many needs a join table, and because enrolment carries its own "
            "attribute it is a real entity. The unique constraint prevents duplicates."
        ),
    },
    # ---------------------------------------------------- react_dashboard
    {
        "id": "react_dashboard_e1",
        "skill_id": "react_dashboard",
        "difficulty": 4,
        "type": "mcq",
        "concept": "state placement",
        "prompt": (
            "Two sibling components need to read and update the same filter value. "
            "Where should that state live?"
        ),
        "options": [
            "Duplicated in both siblings and kept in sync with effects",
            "In their closest common parent, passed down as props",
            "In a module-level variable outside React",
            "In each sibling's own useState, synced through the URL",
        ],
        "correct_option": 1,
        "explanation": (
            "Lifting state to the common parent gives one source of truth. Duplicated "
            "state synced by effects is the classic source of drift bugs."
        ),
    },
    {
        "id": "react_dashboard_m1",
        "skill_id": "react_dashboard",
        "difficulty": 6,
        "type": "mcq",
        "concept": "derived state",
        "prompt": (
            "You hold `items` in state and also store `filteredItems` in a second "
            "useState, updated by an effect. Why is this a problem?"
        ),
        "options": [
            "Effects cannot call setState",
            "filteredItems is derived data, so storing it adds a render pass and can go stale; it should be computed during render",
            "It breaks the rules of hooks",
            "useState cannot hold arrays",
        ],
        "correct_option": 1,
        "explanation": (
            "Anything computable from existing state should be computed, not stored. "
            "Storing it means two sources of truth that can disagree."
        ),
    },
    {
        "id": "react_dashboard_m2",
        "skill_id": "react_dashboard",
        "difficulty": 7,
        "type": "mcq",
        "concept": "composition",
        "prompt": (
            "A dashboard component has grown to 600 lines handling fetching, "
            "filtering, and three chart layouts. What is the most useful first refactor?"
        ),
        "options": [
            "Wrap the whole thing in React.memo",
            "Extract the data fetching into a custom hook and each chart into its own component, so each piece has one responsibility",
            "Move all state into a single reducer and keep the component intact",
            "Split the JSX into helper functions inside the same component",
        ],
        "correct_option": 1,
        "explanation": (
            "Separating data concerns from presentation makes each part testable and "
            "reusable. memo is a performance tool and does not address structure."
        ),
    },
    {
        "id": "react_dashboard_h1",
        "skill_id": "react_dashboard",
        "difficulty": 8,
        "type": "mcq",
        "concept": "render performance",
        "prompt": (
            "A dashboard re-renders every child on each keystroke in a search box. "
            "Which change addresses the cause rather than the symptom?"
        ),
        "options": [
            "Wrap every child in React.memo and move on",
            "Keep the input's value in the component that owns the input, so typing does not re-render the whole dashboard tree",
            "Debounce every child's render with a timeout",
            "Move the search state to a global store",
        ],
        "correct_option": 1,
        "explanation": (
            "Re-renders follow state placement. Narrowing where the fast-changing "
            "state lives removes the work; memo only masks a badly placed state."
        ),
    },
]
