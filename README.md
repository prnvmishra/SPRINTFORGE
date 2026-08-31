# SprintForge.AI

**Learn by Building. Verify by Doing. Adapt by Performance.**

SprintForge.AI is an adaptive learning and project execution engine. It is not a course
platform: there are no videos and no "mark as complete" buttons. A learner claims a skill,
the platform makes them prove it, diagnoses the exact conceptual gap when they fail, routes
them to targeted remediation, and only then unlocks the next piece of real project work.

The closed loop that the whole system exists to serve:

```
CLAIM → VERIFY → DIAGNOSE → PLAN → EXECUTE → OBSERVE
   → FAILURE ANALYSIS → ADAPT → RE-VERIFY → UNLOCK NEXT
```

---

## Quick start

Requirements: **Python 3.11+** (3.13 recommended) and **Node 18+** (20 recommended).
No database server, API key, or Docker is needed to run the full application.

### 1. Backend

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
(cd app/tools/js_ast && npm install)   # acorn, used by the JavaScript validator
.venv/bin/uvicorn app.main:app --reload --port 8000
```

`app/tools/js_ast` is vendored (its `node_modules` is committed), so a clean checkout
works without the `npm install` above; run it only if the directory is missing or you
bump the acorn version. If Node or the parser is unavailable, JavaScript checks **fail
closed** — they report a tooling error instead of silently passing.

API docs: <http://localhost:8000/docs> · health: <http://localhost:8000/health>

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

App: <http://localhost:3000>

### 3. Verify the closed loop

A scripted end-to-end test drives the real API through the entire adaptive cycle —
registration, claimed skills, a failing assessment, gap diagnosis, project generation,
prerequisite gating, remediation practice, re-verification, ticket submission, and sandboxed
language execution:

```bash
cd backend
PYTHONPATH=. .venv/bin/python scripts/verify_flow.py
```

Expected final line: `All 86 checks passed. Closed-loop adaptive workflow verified.`

The strictness of the deterministic JavaScript validator has its own pytest suite plus a
standalone end-to-end proof that syntactically invalid code can no longer pass a ticket:

```bash
cd backend
.venv/bin/python -m pytest tests
.venv/bin/python scripts/verify_strict_validation.py
```

A second suite covers the workspace editor in a real browser — per-file tab isolation,
persistence of typed edits across tab switches, read-only enforcement on provided files, and
that the buffer the backend grades is the one the user typed. It needs both servers running:

```bash
cd frontend
npx playwright install chromium   # first run only
npm run verify:editor
```

---

## The demonstration flow

This is the scenario the product is built around, and it is what `verify_flow.py` asserts:

1. A user registers and claims **intermediate JavaScript**.
2. The adaptive assessment starts at a difficulty matching the claim, escalates on correct
   answers, and steps *down* into diagnostic prerequisite questions on failure.
3. The learner fails the async questions. The Digital Twin records
   **Async Error Handling — needs improvement**, with `try/catch` and `promises` as repeated
   mistakes.
4. The user creates *"Movie Ticket Booking System"*. The sprint generator decomposes it into
   5 sprints / 11 tickets. The knowledge graph keeps the async-dependent tickets **locked**.
5. The router recommends `Handle Failed API Requests with async/await`, and explains why in
   terms of the actual evidence and the actual blocked ticket.
6. The learner completes that practice. Deterministic checks pass, confidence rises above the
   threshold, the prerequisite is satisfied, and the next ticket becomes actionable.

---

## Architecture

### Backend — FastAPI + SQLAlchemy

```
backend/app/
├── main.py                 # app factory, CORS, routers, error handling
├── core/                   # config, database, security (bcrypt + JWT), dependencies
├── models/entities.py      # all 14 persisted entities
├── schemas/                # Pydantic contracts (API + AI + execution)
├── routers/                # auth, profile, assessment, practice, projects, tickets, ai, rewards
├── services/
│   ├── knowledge_graph.py       # JSON dependency graph + prerequisite gating
│   ├── scoring_engine.py        # deterministic confidence formula
│   ├── digital_twin_service.py  # the single writer of learner state
│   ├── assessment_engine.py     # adaptive item selection + evaluation
│   ├── practice_service.py      # practice run/submit orchestration
│   ├── validation_service.py    # static checks + behaviour tests (layers 1–3)
│   ├── sprint_generator.py      # AI project manager: project → sprints → tickets
│   ├── ticket_service.py        # ticket lifecycle + unlock propagation
│   ├── failure_analysis_service.py # root cause → concept gap → remediation
│   ├── graph_router.py          # "why this next?" recommendation engine
│   ├── ai_evaluator.py          # AI provider abstraction (layer 4)
│   ├── code_execution_service.py # sandboxed execution abstraction
│   └── reward_service.py        # XP and levels
└── data/                   # skills_graph.json, practice modules, assessment bank, ticket templates
```

Business logic lives in services. Routers only handle HTTP concerns.

### Frontend — Next.js App Router + TypeScript + Tailwind

```
frontend/
├── app/          # landing, login, register, onboarding, dashboard, assessment,
│                 # practice, projects, workspace, profile
├── components/   # ui primitives, dashboard, workspace (Monaco, preview, mentor)
├── hooks/        # use-auth
└── lib/          # api client, shared types, utils
```

---

## How the core engines work

### Confidence score (deterministic, never AI-generated)

```
confidence = 40% assessment accuracy
           + 25% code execution success
           + 20% task difficulty mastery
           + 15% consistency
```

Weights are re-normalised over the channels that actually have evidence, so a skill is not
punished for a channel the learner has never exercised. Consistency uses an exponential
moving average, so one bad day does not erase a track record. Every score exposes its own
breakdown and a `limiting_factor`, which is what the UI renders when a score is low.

### Prerequisite gating

A prerequisite blocks downstream work only when the graph *knows* it is weak. Two deliberate
relaxations keep the gate honest rather than a dead end:

- **No evidence means unknown, not weak.** The learner may attempt the work, and the attempt
  becomes the evidence.
- **Proof by doing counts.** A graded submission passed at or above a skill's own difficulty
  satisfies that skill even while its aggregate confidence is still climbing.

### Validation is layered, and AI is last

| Layer | Mechanism | Authority |
|---|---|---|
| 1 | Static structural checks: HTML/CSS parsing, and **JavaScript semantics over a real AST** (acorn) — syntax validity, try/catch placement, control-flow ordering, DOM effects | Deterministic, blocking |
| 2 | Automated behaviour tests in the execution sandbox, with the harness owning the network function so failure paths cannot be faked | Deterministic, blocking |
| 3 | Expected output comparison (incl. hidden tests) | Deterministic, blocking |
| 4 | AI evaluation of approach and conceptual mistakes | Advisory + diagnosis |

A submission cannot pass on AI opinion alone, and the frontend never decides correctness — it
submits raw code and renders whatever the backend concluded.

### Provider abstractions

- **AI**: `MockProvider` (default), `OpenAIProvider`, `GeminiProvider`. All output is parsed
  and validated against Pydantic schemas; malformed LLM responses fall back to the mock
  provider rather than corrupting learner state. Missing key ⇒ automatic mock mode.
  `OpenAIProvider` targets any OpenAI-compatible endpoint via `OPENAI_BASE_URL`, so OpenRouter
  and self-hosted vLLM work without code changes. A circuit breaker trips after 3 consecutive
  failures and serves mock evaluations for 2 minutes, so an unreachable, rate-limited, or
  unfunded provider never adds a doomed round-trip to every submission — and recovers on its
  own once the endpoint works again.
- **Code execution**: `LocalSubprocessProvider`, `PistonProvider`, `Judge0Provider`, selected
  by env var. Nothing in the routers or frontend depends on a specific provider.

> **Security note:** `CODE_EXECUTION_PROVIDER=local` runs code in a subprocess with resource
> limits. That is adequate for local development only — it is *not* a sandbox. Use `piston`
> or `judge0` for anything multi-tenant or internet-facing.

---

## Environment variables

**Backend** (`backend/.env`, see `.env.example` for the full annotated list)

| Variable | Default | Purpose |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./sprintforge.db` | SQLite by default; Postgres-ready |
| `AUTH_SECRET` | dev placeholder | JWT signing key — **change in production** |
| `AI_PROVIDER` | `mock` | `mock` \| `openai` \| `gemini` |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible endpoint (OpenAI, OpenRouter, vLLM…) |
| `OPENAI_API_KEY` / `GEMINI_API_KEY` | empty | Unset ⇒ mock mode |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Free key from [AI Studio](https://aistudio.google.com/apikey) |
| `AI_MAX_OUTPUT_TOKENS` | `700` | Completion cap. Lower it (~400) for gateways that reserve the full context window on low-balance accounts; raise it (~2000) for thinking models, which bill reasoning against this budget |
| `CODE_EXECUTION_PROVIDER` | `local` | `local` \| `piston` \| `judge0` |
| `CORS_ORIGINS` | localhost:3000 | Allowed browser origins |
| `CORS_ORIGIN_REGEX` | any localhost port | Dev convenience; clear in production |

**Frontend** (`frontend/.env.local`)

| Variable | Default | Purpose |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

Switching to PostgreSQL requires only a `DATABASE_URL` change; the ORM models are unchanged.
Bare `postgres://` and `postgresql://` URLs are normalised to the bundled **psycopg 3** driver,
so provider URLs from Neon, Supabase or RDS can be pasted in verbatim — including options such
as `channel_binding` that the older psycopg2 driver rejects. Connection pooling is tuned for
serverless Postgres (`pool_recycle=300`) to avoid handing out connections the platform has
already closed.

Secrets belong in `backend/.env`, which is gitignored. Only `.env.example` is tracked.

---

## API surface

| Area | Endpoints |
|---|---|
| Auth | `POST /auth/register` · `POST /auth/login` · `POST /auth/logout` · `GET /auth/me` |
| Profile / Twin | `POST /profile/onboard` · `GET /profile/digital-twin` · `GET /profile/dashboard` · `GET /profile/knowledge-graph` |
| Assessment | `GET /assessment/skills` · `POST /assessment/start` · `POST /assessment/submit` · `GET /assessment/{id}/result` · `GET /assessment/history` |
| Practice | `GET /practice/modules` · `GET /practice/{id}` · `POST /practice/run` · `POST /practice/submit` · `GET /practice/attempts` |
| Projects | `POST /projects` · `GET /projects` · `GET /projects/{id}` · `GET /projects/{id}/sprints` · `GET /projects/{id}/next-ticket` |
| Tickets | `GET /tickets/{id}` · `POST /tickets/{id}/start` · `POST /tickets/{id}/run` · `POST /tickets/{id}/submit` · `POST /tickets/{id}/reset` |
| AI | `GET /ai/status` · `POST /ai/evaluate` · `POST /ai/mentor` · `GET /ai/why-this-next` |
| Rewards | `GET /rewards/me` · `GET /rewards/failures` |

Full interactive reference at `/docs`.

---

## Data model

`User`, `LearningDigitalTwin`, `VerifiedSkill`, `AssessmentSession`, `AssessmentAttempt`,
`PracticeAttempt`, `Project`, `Sprint`, `Ticket`, `TicketAttempt`, `ExecutionAttempt`,
`FailureAnalysis`, `RewardTransaction`, `ActivityLog` — all UUID-keyed with proper
relationships. Practice modules are catalog data (`app/data/`) rather than user-writable rows;
learner attempts against them are persisted.

---

## Design principles held throughout

1. No button is decorative — every action hits a real endpoint and mutates real state.
2. No hardcoded success anywhere in the grading path.
3. The frontend is never trusted to judge correctness.
4. Deterministic validation runs before, and outranks, AI validation.
5. Every routing decision carries a human-readable explanation grounded in real evidence.
6. The application is fully functional with zero external credentials.
