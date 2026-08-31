"""Guided roadmaps for subjects SprintForge does not yet grade.

The engine can only *verify* a skill it has executable checks for. That list is
finite, and a learner will ask for things outside it — Docker, system design,
mobile, whatever their job posting mentioned. Refusing those requests makes the
product look narrow; pretending to grade them would be dishonest.

So these sit deliberately between the two. Each roadmap is an ordered tree with
a stated objective per node and links out to material, and each is labelled in
the UI as guided rather than verified. Where a roadmap depends on something we
*do* grade, `prerequisites` names those skill ids, so a learner's real
confidence decides where they are told to start rather than a generic
"beginners start here".

On links, two rules, both learned the hard way:

* Every YouTube entry is either a specific video whose id has been checked
  against the oEmbed endpoint (which 404s for deleted, private and blocked
  videos), or a search URL, which is a query and cannot rot. Nothing here is a
  video id typed from memory.
* `scripts/verify_resource_links.py` re-checks the whole set. Videos do get
  deleted, so this is expected to catch things eventually; that is the point.
"""

from __future__ import annotations

import urllib.parse
from typing import Any


def _search(query: str) -> str:
    """A YouTube search for a concept.

    Used wherever a single canonical video would be a guess. A search always
    resolves, always reflects what is currently good on the topic, and is honest
    about being a starting point rather than a curated pick.
    """
    return "https://www.youtube.com/results?" + urllib.parse.urlencode(
        {"search_query": query}
    )


def _video(video_id: str, title: str, channel: str) -> dict[str, str]:
    """A checked video. Title and channel are the real ones oEmbed returned."""
    return {
        "kind": "video",
        "title": title,
        "channel": channel,
        "url": f"https://www.youtube.com/watch?v={video_id}",
    }


def _watch(query: str, label: str) -> dict[str, str]:
    return {"kind": "search", "title": label, "channel": "YouTube search", "url": _search(query)}


def _doc(title: str, url: str) -> dict[str, str]:
    return {"kind": "doc", "title": title, "channel": "Official docs", "url": url}


ROADMAPS: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ git
    {
        "id": "git",
        "label": "Git & GitHub",
        "aliases": ["git", "github", "version control", "vcs", "commit", "branching"],
        "summary": "Track your work, undo mistakes safely, and collaborate without overwriting anyone.",
        "why": (
            "Every project ticket you finish here is code someone should be able to review. "
            "Git is the one tool that is assumed rather than listed on a job description."
        ),
        "prerequisites": [],
        "course": _video("RGOj5yH7evk", "Git and GitHub for Beginners - Crash Course", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "What a commit actually is",
                "objective": "Understand snapshots, the staging area, and why history is a graph and not a list.",
                "resources": [
                    _doc("Git Book — Getting Started", "https://git-scm.com/book/en/v2"),
                    _watch("git staging area explained", "Staging area explained"),
                ],
                "children": [
                    {
                        "title": "init, add, commit, status, log",
                        "objective": "Make and inspect history on a local repository with no remote involved.",
                        "resources": [_watch("git init add commit tutorial", "The first five commands")],
                    },
                    {
                        "title": "Writing a message worth reading",
                        "objective": "Say why the change exists, not what the diff already shows.",
                        "resources": [_doc("How to write a commit message", "https://cbea.ms/git-commit/")],
                    },
                ],
            },
            {
                "title": "Branching and merging",
                "objective": "Work on two things at once and combine them without losing either.",
                "resources": [
                    _doc("Git branching", "https://git-scm.com/book/en/v2/Git-Branching-Branches-in-a-Nutshell"),
                    _watch("git branching and merging tutorial", "Branch and merge"),
                ],
                "children": [
                    {
                        "title": "Resolving a merge conflict",
                        "objective": "Read conflict markers and choose deliberately instead of deleting one side.",
                        "resources": [_watch("git merge conflict resolve tutorial", "Conflict resolution")],
                    },
                ],
            },
            {
                "title": "Remotes, push, pull",
                "objective": "Publish to GitHub and pull other people's work into yours.",
                "resources": [_doc("Working with remotes", "https://git-scm.com/book/en/v2/Git-Basics-Working-with-Remotes")],
            },
            {
                "title": "Pull requests and review",
                "objective": "Propose a change, respond to review comments, and get it merged.",
                "resources": [_doc("GitHub — About pull requests", "https://docs.github.com/en/pull-requests")],
            },
            {
                "title": "Undoing things safely",
                "objective": "Know which of restore, revert and reset to reach for, and which one rewrites history.",
                "resources": [
                    _watch("git reset revert restore difference", "reset vs revert vs restore"),
                    _doc("Git — Undoing things", "https://git-scm.com/book/en/v2/Git-Basics-Undoing-Things"),
                ],
            },
        ],
    },
    # --------------------------------------------------------------- docker
    {
        "id": "docker",
        "label": "Docker & Containers",
        "aliases": ["docker", "container", "containers", "devops", "kubernetes", "dockerfile"],
        "summary": "Package an app with its environment so it runs the same on your laptop and a server.",
        "why": (
            "\"Works on my machine\" is the failure this removes. Once your project has a backend "
            "and a database, containers are how you run all of it with one command."
        ),
        "prerequisites": ["node_basics"],
        "course": _video("fqMOX6JJhGo", "Docker Tutorial for Beginners - A Full DevOps Course", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "Images versus containers",
                "objective": "Separate the built artefact from the running process; most confusion starts here.",
                "resources": [_doc("Docker — Get started", "https://docs.docker.com/get-started/")],
            },
            {
                "title": "Writing a Dockerfile",
                "objective": "Build your own image with a base, dependencies, and a start command.",
                "resources": [
                    _doc("Dockerfile reference", "https://docs.docker.com/reference/dockerfile/"),
                    _watch("dockerfile tutorial node app", "Dockerfile for a Node app"),
                ],
                "children": [
                    {
                        "title": "Layers and caching",
                        "objective": "Order instructions so a code change does not reinstall every dependency.",
                        "resources": [_watch("docker layer caching build optimization", "Layer caching")],
                    },
                ],
            },
            {
                "title": "Volumes and ports",
                "objective": "Persist data past a container's life and reach it from your browser.",
                "resources": [_doc("Docker volumes", "https://docs.docker.com/engine/storage/volumes/")],
            },
            {
                "title": "docker compose",
                "objective": "Run an app and its database together as one declared stack.",
                "resources": [
                    _doc("Compose overview", "https://docs.docker.com/compose/"),
                    _watch("docker compose tutorial database", "Compose with a database"),
                ],
            },
        ],
    },
    # ------------------------------------------------------- node + express
    {
        "id": "node_backend",
        "label": "Node.js & Express Backend",
        "aliases": ["node", "nodejs", "express", "backend", "server", "api server"],
        "summary": "Serve your own HTTP API instead of consuming someone else's.",
        "why": (
            "Your project's frontend is currently talking to data you faked. This is the step that "
            "makes the other half real."
        ),
        "prerequisites": ["js_async", "api_integration"],
        "course": _video("Oe421EPjeBE", "Node.js and Express.js - Full Course", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "The Node runtime",
                "objective": "Modules, npm, and why server JavaScript has no DOM.",
                "resources": [_doc("Node.js — Introduction", "https://nodejs.org/en/learn/getting-started/introduction-to-nodejs")],
            },
            {
                "title": "An HTTP server with Express",
                "objective": "Routes, request, response, and returning JSON.",
                "resources": [
                    _video("SccSCuHhOw0", "Learn Express JS In 35 Minutes", "Web Dev Simplified"),
                    _doc("Express — Routing", "https://expressjs.com/en/guide/routing.html"),
                ],
                "children": [
                    {
                        "title": "Middleware",
                        "objective": "Understand the chain: logging, parsing and auth are all the same shape.",
                        "resources": [_doc("Express — Using middleware", "https://expressjs.com/en/guide/using-middleware.html")],
                    },
                    {
                        "title": "Error handling",
                        "objective": "Return a correct status code instead of a 200 with an error inside it.",
                        "resources": [_watch("express error handling middleware tutorial", "Error middleware")],
                    },
                ],
            },
            {
                "title": "Talking to a database",
                "objective": "Persist data past a restart and keep queries out of your route handlers.",
                "resources": [_watch("express postgres crud tutorial", "CRUD against Postgres")],
            },
            {
                "title": "Environment and configuration",
                "objective": "Keep secrets and connection strings out of the code you commit.",
                "resources": [_doc("The Twelve-Factor App — Config", "https://12factor.net/config")],
            },
        ],
    },
    # --------------------------------------------------------------- nextjs
    {
        "id": "nextjs",
        "label": "Next.js",
        "aliases": ["next", "nextjs", "next.js", "ssr", "server components", "app router"],
        "summary": "React with routing, server rendering and data loading decided for you.",
        "why": "Once a React app needs URLs, SEO or a server, this is what teams reach for.",
        "prerequisites": ["react_fundamentals", "react_data_fetching"],
        "course": _video("ZVnjOPwW4ZA", "Next js Tutorial for Beginners | Nextjs 13 (App Router)", "Programming with Mosh"),
        "steps": [
            {
                "title": "File-based routing",
                "objective": "Understand how folders become URLs, and what layouts nest.",
                "resources": [_doc("Next.js — Routing", "https://nextjs.org/docs/app/building-your-application/routing")],
            },
            {
                "title": "Server and client components",
                "objective": "Know which code runs where, and why 'use client' exists.",
                "resources": [
                    _doc("Server Components", "https://nextjs.org/docs/app/building-your-application/rendering/server-components"),
                    _watch("next js server vs client components explained", "Server vs client"),
                ],
            },
            {
                "title": "Data fetching and caching",
                "objective": "Load data on the server and control how long it is reused.",
                "resources": [_doc("Data fetching", "https://nextjs.org/docs/app/building-your-application/data-fetching")],
            },
            {
                "title": "Route handlers",
                "objective": "Ship API endpoints beside the pages that call them.",
                "resources": [_doc("Route handlers", "https://nextjs.org/docs/app/building-your-application/routing/route-handlers")],
            },
        ],
    },
    # -------------------------------------------------------------- mongodb
    {
        "id": "mongodb",
        "label": "MongoDB & NoSQL",
        "aliases": ["mongo", "mongodb", "nosql", "document database", "mongoose"],
        "summary": "Store documents instead of rows, and know when that is the wrong choice.",
        "why": "Common in Node projects. Worth learning alongside SQL so you can argue for either.",
        "prerequisites": ["database_modeling"],
        "course": _video("-56x56UppqQ", "MongoDB Crash Course", "Traversy Media"),
        "steps": [
            {
                "title": "Documents and collections",
                "objective": "Map what you already know about tables and rows onto this model.",
                "resources": [_doc("MongoDB — Databases and collections", "https://www.mongodb.com/docs/manual/core/databases-and-collections/")],
            },
            {
                "title": "CRUD and query operators",
                "objective": "Find, filter, update and delete with the query language.",
                "resources": [_doc("CRUD operations", "https://www.mongodb.com/docs/manual/crud/")],
            },
            {
                "title": "Modelling: embed or reference",
                "objective": "The central design decision, and the one that is expensive to get wrong.",
                "resources": [
                    _doc("Data model design", "https://www.mongodb.com/docs/manual/core/data-model-design/"),
                    _watch("mongodb embedding vs referencing schema design", "Embed vs reference"),
                ],
            },
            {
                "title": "Indexes",
                "objective": "Understand why a query that was instant on 100 documents dies on 100,000.",
                "resources": [_doc("Indexes", "https://www.mongodb.com/docs/manual/indexes/")],
            },
        ],
    },
    # -------------------------------------------------------------- testing
    {
        "id": "testing",
        "label": "Automated Testing",
        "aliases": ["testing", "test", "jest", "unit test", "tdd", "pytest", "vitest"],
        "summary": "Write the checks yourself instead of only being graded by ours.",
        "why": (
            "SprintForge grades your tickets with automated checks. Learning to write those checks "
            "is how you keep that safety net on work nobody is grading."
        ),
        "prerequisites": ["js_functions"],
        "course": _video("7r4xVDI2vho", "Jest Crash Course - Unit Testing in JavaScript", "Traversy Media"),
        "steps": [
            {
                "title": "What makes a test useful",
                "objective": "Arrange, act, assert — and why a test that never fails is worthless.",
                "resources": [_watch("what makes a good unit test", "Anatomy of a test")],
            },
            {
                "title": "Unit tests",
                "objective": "Test one function's behaviour, including its error paths.",
                "resources": [_doc("Jest — Getting started", "https://jestjs.io/docs/getting-started")],
                "children": [
                    {
                        "title": "Mocking",
                        "objective": "Replace the network and the clock so a test is deterministic.",
                        "resources": [_doc("Jest — Mock functions", "https://jestjs.io/docs/mock-functions")],
                    },
                ],
            },
            {
                "title": "Testing the DOM",
                "objective": "Assert on what a user can see rather than on implementation details.",
                "resources": [_doc("Testing Library — Guiding principles", "https://testing-library.com/docs/guiding-principles/")],
            },
            {
                "title": "Coverage, and its limits",
                "objective": "Read a coverage report without treating 100% as proof of correctness.",
                "resources": [_watch("code coverage is not enough testing", "Why coverage misleads")],
            },
        ],
    },
    # --------------------------------------------------------- system design
    {
        "id": "system_design",
        "label": "System Design",
        "aliases": ["system design", "architecture", "scalability", "hld", "design interview"],
        "summary": "Reason about what breaks when a working app meets real traffic.",
        "why": "The interview round that pure coding practice does not prepare you for.",
        "prerequisites": ["rest_api", "database_modeling"],
        "course": _video("i53Gi_K3o7I", "20 System Design Concepts Explained in 10 Minutes", "NeetCode"),
        "steps": [
            {
                "title": "Latency, throughput, availability",
                "objective": "Speak in the units the discussion is actually conducted in.",
                "resources": [_watch("latency throughput availability explained system design", "The vocabulary")],
            },
            {
                "title": "Caching",
                "objective": "Where to put a cache, and how you decide when it is stale.",
                "resources": [_watch("caching strategies system design explained", "Cache strategies")],
            },
            {
                "title": "Databases at scale",
                "objective": "Replication, sharding, and the read/write trade-offs of each.",
                "resources": [_watch("database sharding replication system design", "Replication and sharding")],
            },
            {
                "title": "Queues and asynchronous work",
                "objective": "Move slow work off the request path without losing it.",
                "resources": [_watch("message queue system design tutorial", "Queues")],
            },
            {
                "title": "Working through a real design",
                "objective": "Practise the whole conversation end to end, out loud.",
                "resources": [_doc("System Design Primer", "https://github.com/donnemartin/system-design-primer")],
            },
        ],
    },
    # ----------------------------------------------------------------- auth
    {
        "id": "auth",
        "label": "Authentication & Security",
        "aliases": ["auth", "authentication", "jwt", "login", "security", "oauth", "session"],
        "summary": "Let the right people in and keep everyone else out, without inventing your own crypto.",
        "why": "Your project has a login screen. This is what has to be true behind it.",
        "prerequisites": ["rest_api"],
        "course": _video("mbsmsi7l3r4", "JWT Authentication Tutorial - Node.js", "Web Dev Simplified"),
        "steps": [
            {
                "title": "Passwords",
                "objective": "Hash with a slow algorithm and salt; never store or log the original.",
                "resources": [_doc("OWASP — Password storage cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html")],
            },
            {
                "title": "Sessions versus tokens",
                "objective": "Know what each costs you in revocation, storage and complexity.",
                "resources": [_watch("session vs jwt authentication difference", "Sessions vs JWT")],
            },
            {
                "title": "Authorisation",
                "objective": "Separate who you are from what you may do, and check it server-side every time.",
                "resources": [_doc("OWASP — Authorization cheat sheet", "https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html")],
            },
            {
                "title": "The common attacks",
                "objective": "Recognise injection, XSS and CSRF in your own code before someone else does.",
                "resources": [_doc("OWASP Top Ten", "https://owasp.org/www-project-top-ten/")],
            },
        ],
    },
    # ---------------------------------------------------------------- linux
    {
        "id": "linux",
        "label": "Linux & the Command Line",
        "aliases": ["linux", "bash", "shell", "terminal", "command line", "cli", "ubuntu"],
        "summary": "Be comfortable on the machine your code will actually run on.",
        "why": "Servers, containers and CI are all Linux. This stops being optional very quickly.",
        "prerequisites": [],
        "course": _video("sWbUDq4S6Y8", "Introduction to Linux – Full Course for Beginners", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "Filesystem and navigation",
                "objective": "Move around, read and edit files without a graphical file manager.",
                "resources": [_doc("The Linux Command Line (free book)", "https://linuxcommand.org/tlcl.php")],
            },
            {
                "title": "Permissions and ownership",
                "objective": "Read an ls -l line and know why the script will not execute.",
                "resources": [_watch("linux file permissions chmod explained", "Permissions")],
            },
            {
                "title": "Pipes and redirection",
                "objective": "Chain small tools into something none of them do alone.",
                "resources": [_watch("linux pipes redirection tutorial", "Pipes and redirection")],
            },
            {
                "title": "Processes and logs",
                "objective": "Find what is running, what is eating the CPU, and what it printed.",
                "resources": [_watch("linux process management ps top kill", "Processes")],
            },
        ],
    },
    # ------------------------------------------------------------------ aws
    {
        "id": "cloud_aws",
        "label": "Cloud Fundamentals (AWS)",
        "aliases": ["aws", "cloud", "s3", "ec2", "deploy", "deployment", "hosting"],
        "summary": "Get something you built onto the internet, and understand the bill.",
        "why": "A project nobody can open is hard to show. Deployment is the last mile.",
        "prerequisites": ["node_basics"],
        "course": _video("ulprqHHWlng", "AWS Certified Cloud Practitioner – Full Course", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "Regions, compute and storage",
                "objective": "The three primitives everything else is assembled from.",
                "resources": [_doc("AWS — Getting started", "https://aws.amazon.com/getting-started/")],
            },
            {
                "title": "Deploying a static site",
                "objective": "Ship the frontend first; it is the cheapest possible win.",
                "resources": [_watch("deploy static site s3 cloudfront tutorial", "Static hosting")],
            },
            {
                "title": "Running a server",
                "objective": "Get the API online and reachable over HTTPS.",
                "resources": [_watch("deploy node api to aws tutorial", "Deploying an API")],
            },
            {
                "title": "Identity and cost",
                "objective": "Least-privilege access, and a billing alarm before the first surprise.",
                "resources": [_doc("IAM best practices", "https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html")],
            },
        ],
    },
    # -------------------------------------------------------------- graphql
    {
        "id": "graphql",
        "label": "GraphQL",
        "aliases": ["graphql", "apollo", "schema", "resolver"],
        "summary": "Let the client ask for exactly the fields it needs, and nothing more.",
        "why": "An alternative to REST worth understanding well enough to choose against.",
        "prerequisites": ["api_integration", "rest_api"],
        "course": _video("ed8SzALpx1Q", "GraphQL Full Course - Novice to Expert", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "Schema and types",
                "objective": "Describe your data as a graph the client can traverse.",
                "resources": [_doc("GraphQL — Schemas and types", "https://graphql.org/learn/schema/")],
            },
            {
                "title": "Queries and mutations",
                "objective": "Read and write, and see why there is only ever one endpoint.",
                "resources": [_doc("Queries and mutations", "https://graphql.org/learn/queries/")],
            },
            {
                "title": "Resolvers",
                "objective": "Where the data actually comes from, field by field.",
                "resources": [_watch("graphql resolvers explained tutorial", "Resolvers")],
            },
            {
                "title": "The N+1 problem",
                "objective": "The performance trap this design walks straight into, and batching as the fix.",
                "resources": [_watch("graphql n+1 problem dataloader", "N+1 and DataLoader")],
            },
        ],
    },
    # ----------------------------------------------------- machine learning
    {
        "id": "machine_learning",
        "label": "Machine Learning Basics",
        "aliases": ["ml", "machine learning", "ai", "model", "sklearn", "deep learning"],
        "summary": "Fit a model, measure it honestly, and know when the answer is 'not machine learning'.",
        "why": "The natural next step once you can already clean and analyse data.",
        "prerequisites": ["python_basics", "exploratory_analysis", "statistics_business"],
        "course": _video("i_LwzRVP7bg", "Machine Learning for Everybody – Full Course", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "Supervised learning",
                "objective": "Features, labels, and the split between training and test data.",
                "resources": [_doc("scikit-learn — Getting started", "https://scikit-learn.org/stable/getting_started.html")],
            },
            {
                "title": "Your first models",
                "objective": "Linear and tree-based models, and reading what they learned.",
                "resources": [_doc("Supervised learning", "https://scikit-learn.org/stable/supervised_learning.html")],
            },
            {
                "title": "Evaluating honestly",
                "objective": "Why accuracy lies on imbalanced data, and what to report instead.",
                "resources": [
                    _doc("Model evaluation", "https://scikit-learn.org/stable/modules/model_evaluation.html"),
                    _watch("precision recall f1 explained imbalanced data", "Precision, recall, F1"),
                ],
            },
            {
                "title": "Overfitting",
                "objective": "Recognise a model that memorised the training set, and cross-validate.",
                "resources": [_watch("overfitting underfitting cross validation explained", "Overfitting")],
            },
        ],
    },
    # --------------------------------------------------------- react native
    {
        "id": "react_native",
        "label": "Mobile with React Native",
        "aliases": ["react native", "mobile", "android", "ios", "app", "expo", "flutter"],
        "summary": "Reuse what you know about React to ship something that installs on a phone.",
        "why": "The shortest path from web React to a real mobile app.",
        "prerequisites": ["react_fundamentals", "react_state"],
        "course": _video("0-S5a0eXPoc", "React Native Tutorial for Beginners", "Programming with Mosh"),
        "steps": [
            {
                "title": "Setting up with Expo",
                "objective": "Run on a real device without installing a native toolchain first.",
                "resources": [_doc("Expo — Get started", "https://docs.expo.dev/get-started/introduction/")],
            },
            {
                "title": "Core components and styling",
                "objective": "View, Text and Flexbox instead of div, span and CSS.",
                "resources": [_doc("React Native — Core components", "https://reactnative.dev/docs/intro-react-native-components")],
            },
            {
                "title": "Navigation",
                "objective": "Stacks and tabs, which is what mobile has instead of URLs.",
                "resources": [_doc("React Navigation", "https://reactnavigation.org/docs/getting-started")],
            },
            {
                "title": "Device APIs",
                "objective": "Camera, storage and permissions — the parts the web cannot reach.",
                "resources": [_watch("react native expo camera permissions tutorial", "Device APIs")],
            },
        ],
    },
    # ------------------------------------------------------------- tailwind
    {
        "id": "tailwind",
        "label": "Tailwind CSS",
        "aliases": ["tailwind", "utility css", "tailwindcss"],
        "summary": "Compose styling from utilities instead of naming a class for everything.",
        "why": "Widely used, and quick once your CSS fundamentals are already verified.",
        "prerequisites": ["css_layout", "css_responsive"],
        "course": _video("ft30zcMlFao", "Learn Tailwind CSS – Course for Beginners", "freeCodeCamp.org"),
        "steps": [
            {
                "title": "The utility model",
                "objective": "Why the classes look like that, and what it replaces.",
                "resources": [_doc("Tailwind — Styling with utility classes", "https://tailwindcss.com/docs/styling-with-utility-classes")],
            },
            {
                "title": "Responsive and state variants",
                "objective": "Breakpoints, hover and focus without leaving the markup.",
                "resources": [_doc("Responsive design", "https://tailwindcss.com/docs/responsive-design")],
            },
            {
                "title": "Design tokens and theming",
                "objective": "Configure the scale so the output stays consistent.",
                "resources": [_doc("Theme configuration", "https://tailwindcss.com/docs/theme")],
            },
        ],
    },
]

ROADMAP_INDEX: dict[str, dict[str, Any]] = {roadmap["id"]: roadmap for roadmap in ROADMAPS}


# The graph's own `concept_to_skill` map is fine-grained ("promise rejection",
# "left join"). Nobody types that when they are asking to learn something; they
# type "react" or "sql". These are the everyday names for skills we do grade, so
# a request for one is answered with the graded skill rather than a roadmap.
SKILL_ALIASES: dict[str, str] = {
    "html": "html_basics",
    "css": "css_basics",
    "flexbox": "css_layout",
    "grid": "css_layout",
    "responsive": "css_responsive",
    "javascript": "js_basics",
    "js": "js_basics",
    "dom": "js_dom",
    "async": "js_async",
    "typescript": "typescript_basics",
    "ts": "typescript_basics",
    "api": "api_integration",
    "rest": "rest_api",
    "rest api": "rest_api",
    "react": "react_fundamentals",
    "hooks": "react_state",
    "node": "node_basics",
    "nodejs": "node_basics",
    "python": "python_basics",
    "java": "java_basics",
    "c": "c_basics",
    "cpp": "cpp_basics",
    "c++": "cpp_basics",
    "dsa": "dsa_arrays",
    "algorithms": "dsa_arrays",
    "data structures": "dsa_arrays",
    "arrays": "dsa_arrays",
    "sql": "sql_basics",
    "joins": "sql_joins",
    "database": "database_modeling",
    "data cleaning": "data_cleaning",
    "eda": "exploratory_analysis",
    "statistics": "statistics_business",
    "stats": "statistics_business",
    "visualisation": "data_visualization",
    "visualization": "data_visualization",
    "charts": "data_visualization",
    "dashboard": "dashboard_design",
    "excel": "spreadsheet_modeling",
    "spreadsheet": "spreadsheet_modeling",
}


def normalise(text: str) -> str:
    """Lowercased, punctuation flattened to spaces, padded so tokens match.

    `c++` becomes `c` under this, which is why the alias table carries both and
    the longest-match rule decides between them.
    """
    return " " + "".join(c.lower() if c.isalnum() else " " for c in text) + " "
