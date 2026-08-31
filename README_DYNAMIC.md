# SprintForge.AI

<div align="center">

**Learn by Building. Verify by Doing. Adapt by Performance.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node 18+](https://img.shields.io/badge/node-18+-green.svg)](https://nodejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-red.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-14.2-black.svg)](https://nextjs.org/)

*A closed-loop adaptive learning engine that verifies skills through code execution, diagnoses gaps with deterministic analysis, and routes learners to targeted remediation.*

[Quick Start](#quick-start) • [Architecture](#architecture) • [Features](#features) • [API](#api-surface) • [Deployment](#deploying) • [Contributing](#contributing)

</div>

---

## 🎯 The Core Philosophy

SprintForge.AI is **not** a course platform. There are no videos to watch, no "mark as complete" buttons, and no passive consumption. Instead, it implements a closed-loop adaptive learning system:

```
CLAIM → VERIFY → DIAGNOSE → PLAN → EXECUTE → OBSERVE
   → FAILURE ANALYSIS → ADAPT → RE-VERIFY → UNLOCK NEXT
```

A learner claims a skill → the platform makes them prove it → diagnoses exact conceptual gaps when they fail → routes them to targeted remediation → only then unlocks the next piece of real project work.

Every score traces back to executed code. Every recommendation is grounded in evidence. The system adapts based on what the learner *actually* does, not what they claim to know.

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+** (3.13 recommended)
- **Node 18+** (20 recommended)
- No database server, API key, or Docker required for local development

### Backend Setup

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
(cd app/tools/js_ast && npm install)   # acorn, used by JavaScript validator
PYTHONPATH=. .venv/bin/python -m scripts.build_test_cases   # once, ~7 min
PYTHONPATH=. .venv/bin/python -m scripts.split_case_bank
.venv/bin/uvicorn app.main:app --reload --port 8000
```

> **Note:** `build_test_cases.py` generates ~197MB of test cases and takes ~7 minutes. This runs once per checkout, not every boot. Use `--only <slug-prefix>` for incremental rebuilds.

### Frontend Setup

```bash
cd frontend
npm install
cp .env.example .env.local     # NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```

### Verify Installation

```bash
# Backend: Complete adaptive workflow test
cd backend
PYTHONPATH=. .venv/bin/python scripts/verify_flow.py
# Expected: "All 86 checks passed. Closed-loop adaptive workflow verified."

# Frontend: Editor verification (needs both servers running)
cd frontend
npx playwright install chromium
npm run verify:editor
```

### Access Points

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Documentation:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Next.js Frontend                        │
│  (Landing, Dashboard, Workspace, Assessment, Practice, Projects) │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP/REST
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Routers: auth, profile, assessment, practice, projects, │  │
│  │           tickets, ai, rewards, roadmaps, placement       │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Services: Digital Twin, Knowledge Graph, Assessment,     │  │
│  │            Validation, Sprint Generator, AI Evaluator     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  Data: Curriculum, Practice Modules, Skills Graph,        │  │
│  │        Roadmaps, Assessment Bank, Ticket Templates       │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    SQLAlchemy ORM + Database                     │
│                  (SQLite default, PostgreSQL ready)              │
└─────────────────────────────────────────────────────────────────┘
```

### Backend Structure

```
backend/app/
├── main.py                    # App factory, CORS, routers, error handling
├── core/
│   ├── config.py             # Settings with production safety checks
│   ├── database.py           # SQLAlchemy session management
│   ├── security.py           # JWT + bcrypt authentication
│   └── dependencies.py       # FastAPI dependency injection
├── models/
│   └── entities.py           # 14 persisted entities (User, DigitalTwin, etc.)
├── schemas/                  # Pydantic contracts (API + AI + execution)
├── routers/                  # HTTP endpoints (auth, profile, assessment, etc.)
├── services/
│   ├── knowledge_graph.py    # JSON dependency graph + prerequisite gating
│   ├── scoring_engine.py     # Deterministic confidence formula
│   ├── digital_twin_service.py  # Single writer of learner state
│   ├── assessment_engine.py  # Adaptive item selection + evaluation
│   ├── practice_service.py   # Practice run/submit orchestration
│   ├── validation_service.py # Static checks + behavior tests (layers 1–3)
│   ├── sprint_generator.py   # AI project manager: project → sprints → tickets
│   ├── ticket_service.py     # Ticket lifecycle + unlock propagation
│   ├── failure_analysis_service.py # Root cause → concept gap → remediation
│   ├── graph_router.py       # "Why this next?" recommendation engine
│   ├── ai_evaluator.py       # AI provider abstraction (layer 4)
│   ├── code_execution_service.py # Sandboxed execution abstraction
│   └── reward_service.py     # XP and levels
└── data/
    ├── skills_graph.json     # Skill dependency graph
    ├── curriculum.py         # Practice modules catalog
    ├── roadmaps.py           # Guided learning paths
    ├── assessment_bank.py    # Adaptive assessment items
    └── ticket_templates.py   # Project ticket generators
```

### Frontend Structure

```
frontend/
├── app/
│   ├── page.tsx              # Landing page with hero and features
│   ├── layout.tsx            # Root layout with app shell
│   ├── dashboard/            # Command centre with progress tracking
│   ├── assessment/           # Adaptive skill assessment
│   ├── practice/             # Practice modules with layered problems
│   ├── projects/             # Project creation and management
│   ├── workspace/            # Ticket execution with Monaco editor
│   ├── profile/              # User profile and digital twin view
│   ├── roadmap/              # Guided learning paths
│   └── placement/            # Placement preparation
├── components/
│   ├── ui/                   # Primitives and design system
│   ├── workspace/            # Monaco editor, preview, mentor panel
│   ├── dashboard/            # Progress charts and statistics
│   ├── landing/              # Hero, comparison, engine loop
│   └── path/                 # Learning path visualization
├── hooks/
│   └── use-auth.ts           # Authentication state management
└── lib/
    ├── api.ts                # Type-safe API client
    ├── types.ts              # Shared TypeScript types
    └── utils.ts              # Utility functions
```

---

## ✨ Features

### 🧠 Learning Digital Twin

A persistent model of what the learner can actually do, continuously updated from executed code rather than self-report:

- **Verified Skills:** Skills confirmed through assessment and practice
- **Confidence Scores:** 0-100 scale with explainable breakdown
- **Repeated Mistakes:** Pattern recognition for conceptual gaps
- **Learning Velocity:** Progress tracking over time
- **Adaptive Routing:** Personalized next-step recommendations

### 🎯 Deterministic Validation

Four-layer validation system where AI is last, not first:

| Layer | Mechanism | Authority |
|-------|-----------|-----------|
| 1 | Static structural checks (HTML/CSS parsing, JavaScript AST analysis) | Deterministic, blocking |
| 2 | Automated behavior tests in execution sandbox | Deterministic, blocking |
| 3 | Expected output comparison (including hidden tests) | Deterministic, blocking |
| 4 | AI evaluation of approach and conceptual mistakes | Advisory + diagnosis |

**Key principle:** A submission cannot pass on AI opinion alone. The frontend never decides correctness—it submits raw code and renders whatever the backend concludes.

### 📊 Confidence Scoring

Deterministic formula (never AI-generated):

```
confidence = 40% assessment accuracy
           + 25% code execution success
           + 20% task difficulty mastery
           + 15% consistency
```

- **Re-normalized** over available evidence channels
- **Exponential moving average** for consistency (one bad day doesn't erase track record)
- **Limiting factor** exposure shows exactly what's holding a score back

### 🔐 Prerequisite Gating

A prerequisite blocks downstream work only when the graph *knows* it is weak:

- **No evidence = unknown, not weak** — learners can attempt work and generate evidence
- **Proof by doing counts** — passing a submission at or above skill difficulty satisfies the prerequisite even while aggregate confidence is still climbing

### 🤖 AI Integration

Provider abstraction with graceful degradation:

- **MockProvider** (default) — Works without any API keys
- **OpenAIProvider** — Targets any OpenAI-compatible endpoint
- **GeminiProvider** — Free tier available via Google AI Studio

**Safety features:**
- All output parsed and validated against Pydantic schemas
- Malformed LLM responses fall back to mock provider
- Circuit breaker after 3 consecutive failures (2-minute cooldown)
- Missing API key ⇒ automatic mock mode

### ⚡ Code Execution

Multiple execution providers with sandboxing:

- **LocalSubprocessProvider** — Development only (not a sandbox)
- **PistonProvider** — Recommended for production (self-hosted or public)
- **Judge0Provider** — Alternative via RapidAPI

**Security note:** With `ENVIRONMENT=production`, the app refuses to start while `CODE_EXECUTION_PROVIDER=local`.

### 🎨 Layered Practice System

Practice modules load with exactly one layer stripped out:

1. **Structure Layer** — HTML skeleton, missing content
2. **Style Layer** — Complete HTML, missing CSS
3. **Behavior Layer** — Complete UI, missing JavaScript logic
4. **Integration Layer** — Complete component, missing state management

Learners write only the missing layer. Deterministic checks decide whether it holds.

### 📋 Project Execution

Describe an idea → Engine returns milestones, sprints, and engineering tickets:

- **AI Sprint Generator** decomposes projects into actionable tickets
- **Knowledge Graph** blocks tickets dependent on unverified skills
- **Acceptance Criteria** cannot be self-marked as complete
- **Progress Tracking** per sprint, per ticket, with time estimates

### 🗺️ Guided Roadmaps

For subjects SprintForge doesn't yet grade (Docker, system design, mobile):

- Ordered trees with stated objectives per node
- Links to curated external resources
- Prerequisites based on verified skills
- Clearly labelled as "guided" rather than "verified"

---

## 🔌 API Surface

### Authentication
- `POST /auth/register` — User registration
- `POST /auth/login` — User login with JWT token
- `POST /auth/logout` — Token invalidation
- `GET /auth/me` — Current user profile

### Profile & Digital Twin
- `POST /profile/onboard` — Complete onboarding flow
- `GET /profile/digital-twin` — Full learning digital twin
- `GET /profile/dashboard` — Dashboard statistics
- `GET /profile/knowledge-graph` — Skill dependency graph

### Assessment
- `GET /assessment/skills` — Available skills for assessment
- `POST /assessment/start` — Begin adaptive assessment
- `POST /assessment/submit` — Submit assessment answer
- `GET /assessment/{id}/result` — Get assessment results
- `GET /assessment/history` — Assessment history

### Practice
- `GET /practice/modules` — Available practice modules
- `GET /practice/{id}` — Module details with problems
- `POST /practice/run` — Start practice problem
- `POST /practice/submit` — Submit practice solution
- `GET /practice/attempts` — Practice attempt history

### Projects
- `POST /projects` — Create new project
- `GET /projects` — List user projects
- `GET /projects/{id}` — Project details
- `GET /projects/{id}/sprints` — Project sprints
- `GET /projects/{id}/next-ticket` — Next actionable ticket

### Tickets
- `GET /tickets/{id}` — Ticket details
- `POST /tickets/{id}/start` — Start working on ticket
- `POST /tickets/{id}/run` — Run code in sandbox
- `POST /tickets/{id}/submit` — Submit ticket solution
- `POST /tickets/{id}/reset` — Reset ticket to initial state

### AI
- `GET /ai/status` — AI provider status
- `POST /ai/evaluate` — AI code evaluation
- `POST /ai/mentor` — AI mentor assistance
- `GET /ai/why-this-next` — Recommendation explanation

### Rewards
- `GET /rewards/me` — User XP and level
- `GET /rewards/failures` — Failure analysis history

### Roadmaps
- `GET /roadmaps` — Available guided roadmaps
- `GET /roadmaps/{id}` — Roadmap details with steps

**Full interactive reference:** `/docs` (Swagger UI)

---

## 🗄️ Data Model

### Core Entities

- **User** — Account information with authentication
- **LearningDigitalTwin** — Persistent learner model
- **VerifiedSkill** — Skills confirmed through assessment
- **AssessmentSession** — Adaptive assessment instances
- **AssessmentAttempt** — Individual assessment answers
- **PracticeAttempt** — Practice module submissions
- **Project** — User-created learning projects
- **Sprint** — Project milestones
- **Ticket** — Individual engineering tasks
- **TicketAttempt** — Ticket submission history
- **ExecutionAttempt** — Code execution records
- **FailureAnalysis** — Root cause analysis
- **RewardTransaction** — XP and level changes
- **ActivityLog** — User activity tracking

All entities are UUID-keyed with proper relationships and cascade deletes.

---

## ⚙️ Configuration

### Backend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATABASE_URL` | `sqlite:///./sprintforge.db` | Database connection (PostgreSQL-ready) |
| `AUTH_SECRET` | `dev-only-insecure-secret-change-me` | JWT signing key — **change in production** |
| `AI_PROVIDER` | `mock` | `mock` \| `openai` \| `gemini` |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI-compatible endpoint |
| `OPENAI_API_KEY` | empty | OpenAI API key (unset ⇒ mock mode) |
| `GEMINI_API_KEY` | empty | Gemini API key (unset ⇒ mock mode) |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Gemini model identifier |
| `AI_MAX_OUTPUT_TOKENS` | `700` | Completion token cap |
| `CODE_EXECUTION_PROVIDER` | `local` | `local` \| `piston` \| `judge0` |
| `PISTON_URL` | `https://emkc.org/api/v2/piston` | Piston execution endpoint |
| `JUDGE0_URL` | `https://judge0-ce.p.rapidapi.com` | Judge0 endpoint |
| `JUDGE0_API_KEY` | empty | Judge0 API key |
| `CORS_ORIGINS` | `localhost:3000` | Allowed browser origins |
| `CORS_ORIGIN_REGEX` | `any localhost port` | CORS regex (dev convenience) |

### Frontend Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## 🚀 Deploying

### Production Safety Checks

Set `ENVIRONMENT=production` and the app validates its configuration at startup:

| Must be set | Why it blocks startup |
|-------------|----------------------|
| `CODE_EXECUTION_PROVIDER=piston` or `judge0` | `local` runs learner code as API process (arbitrary remote code execution) |
| `AUTH_SECRET` ≠ dev default | Default is in repository, anyone could forge tokens |
| `DATABASE_URL` not SQLite | Container restart would lose all learner data |
| `JUDGE0_API_KEY` (if using judge0) | Otherwise submissions fail as tooling errors |

### Recommended Deployment Architecture

**Frontend:** Vercel (Next.js optimized, CDN, free tier available)
**Database:** Neon (PostgreSQL, serverless, free tier available)
**Backend:** Oracle Cloud Always Free ARM or $5/month VPS
**Code Execution:** Self-hosted Piston via Docker

### Docker Deployment

```bash
# Build case store first (on trusted machine)
cd backend
python -m scripts.build_test_cases
python -m scripts.split_case_bank
python -m scripts.build_curriculum_manifest

# Build and run backend
docker build -t sprintforge-api backend/
docker run -d --restart unless-stopped -p 8000:8000 \
  -e DATABASE_URL='postgresql+psycopg://...' \
  -e AUTH_SECRET="$(openssl rand -hex 32)" \
  -e CORS_ORIGINS='https://your-app.vercel.app' \
  -e CORS_ORIGIN_REGEX='' \
  -e ENVIRONMENT=production \
  -e CODE_EXECUTION_PROVIDER=piston \
  -e PISTON_URL=http://localhost:2000/api/v2 \
  sprintforge-api

# Run Piston for code execution
docker compose -f docker-compose.judge.yml up -d
```

### Deployment Verification

Check startup log for:
```
SprintForge.AI started · AI provider=gemini · execution provider=piston (sandboxed=True)
```

If `sandboxed=False`, the deployment is **not safe for public access**.

---

## 🧪 Testing

### Backend Tests

```bash
cd backend
.venv/bin/python -m pytest tests/                      # Unit tests
.venv/bin/python scripts/verify_flow.py                 # E2E workflow
.venv/bin/python scripts/verify_strict_validation.py  # Validation strictness
```

### Frontend Tests

```bash
cd frontend
npx playwright install chromium    # First time only
npm run verify:editor              # Workspace editor tests
npm run verify:preview             # Live preview tests
```

### Test Coverage

- **86 E2E checks** covering the complete adaptive workflow
- **Deterministic validation** proof that syntactically invalid code cannot pass
- **Workspace editor** isolation, persistence, and read-only enforcement
- **Production safety** configuration validation

---

## 📈 Performance Metrics

### Backend Performance

| Metric | Before Optimization | After Optimization |
|--------|-------------------|-------------------|
| Boot time | 14s | 1.6s |
| Peak memory | 580MB | 96MB |
| Case store size | 197MB (loaded) | 1.7MB manifest + 76MB hidden (on-demand) |

**Optimization:** Split case bank into visible manifest (60KB) and gzipped hidden cases (76MB), loaded per problem on demand.

### Frontend Performance

- **Next.js 14** with App Router for optimal performance
- **Monaco Editor** for code editing with lazy loading
- **React Query** for efficient data fetching and caching
- **Tailwind CSS** with JIT compilation for minimal CSS bundle

---

## 🔒 Security Considerations

### Authentication & Authorization

- **JWT tokens** with configurable expiration
- **Bcrypt** password hashing
- **CORS** configuration with origin validation
- **Production checks** prevent insecure deployments

### Code Execution Safety

- **Never run learner code as API process in production**
- **Use Piston or Judge0** for sandboxed execution
- **Resource limits** on execution time and memory
- **Network isolation** in execution sandbox

### Data Protection

- **SQL injection prevention** via SQLAlchemy ORM
- **XSS prevention** via React's built-in escaping
- **CSRF protection** via same-site cookie policies
- **Secrets management** via environment variables

### AI Safety

- **Deterministic validation before AI evaluation**
- **AI as advisory, not authoritative**
- **Graceful degradation** to mock provider on failures
- **Structured output validation** via Pydantic schemas

---

## 🛠️ Development Workflow

### Adding New Practice Problems

1. Define problem in `backend/app/data/curriculum_source.py`
2. Add reference solution and test cases
3. Run `PYTHONPATH=. .venv/bin/python -m scripts.build_test_cases --only <slug>`
4. Run `PYTHONPATH=. .venv/bin/python -m scripts.build_curriculum_manifest`
5. Verify with `PYTHONPATH=. .venv/bin/python -m scripts.build_curriculum_manifest --check`

### Adding New Skills

1. Update `backend/app/data/skills_graph.json`
2. Define prerequisites and unlocks
3. Add assessment items to `backend/app/data/assessment_bank.py`
4. Create practice modules in `backend/app/data/practice_*.py`

### Modifying Validation Rules

1. Update `backend/app/services/validation_service.py`
2. Adjust `backend/app/services/js_ast.py` for JavaScript AST checks
3. Run test suite to ensure no regressions
4. Update documentation if behavior changes

---

## 🤝 Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow the development workflow above
4. Ensure all tests pass: `pytest tests/` and `npm run verify:editor`
5. Submit a pull request with clear description

### Code Style

- **Backend:** PEP 8, type hints where appropriate
- **Frontend:** ESLint + Prettier, strict TypeScript
- **Commits:** Conventional commits format
- **Documentation:** Update README for user-facing changes

### Testing Requirements

- All existing tests must pass
- New features require test coverage
- E2E workflow must remain intact
- Production safety checks must not be compromised

---

## 📚 Documentation

### Internal Documentation

- `docs/deployment.md` — Detailed deployment guide
- `docs/curriculum_authoring.md` — Adding curriculum content
- Backend docstrings — Service and router documentation
- Frontend component comments — UI component documentation

### API Documentation

Interactive API documentation available at `/docs` (Swagger UI) when backend is running.

---

## 🐛 Troubleshooting

### Common Issues

**Problem:** Backend fails to start in production
- **Solution:** Check `AUTH_SECRET`, `DATABASE_URL`, and `CODE_EXECUTION_PROVIDER` are set correctly

**Problem:** Hidden test cases missing
- **Solution:** Run `scripts/build_test_cases.py` and `scripts/split_case_bank.py`

**Problem:** JavaScript validation fails
- **Solution:** Ensure Node.js 18+ is installed and run `cd app/tools/js_ast && npm install`

**Problem:** Rendered HTML/CSS checks fail
- **Solution:** Install Chromium: `.venv/bin/playwright install chromium`

**Problem:** AI returns mock responses
- **Solution:** Check API key is set and provider is configured correctly

---

## 🗺️ Roadmap

### Planned Features

- [ ] Multi-language support beyond current 5 languages
- [ ] Collaborative projects with peer review
- [ ] Integrated video explanations for failed concepts
- [ ] Mobile application for on-the-go practice
- [ ] Advanced analytics dashboard for instructors
- [ ] Certification based on verified skills
- [ ] Community-driven problem contributions
- [ ] Real-time collaborative coding sessions

### Technology Improvements

- [ ] GraphQL API for more efficient data fetching
- [ ] WebSocket support for real-time updates
- [ ] Advanced code execution sandboxing
- [ ] Machine learning models for difficulty prediction
- [ ] Distributed task processing for scalability

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **FastAPI** for the excellent web framework
- **Next.js** for the React framework
- **Monaco Editor** for the code editing experience
- **Piston** for the code execution sandbox
- **Playwright** for browser automation
- The open-source community for the amazing tools and libraries

---

## 📞 Support

- **Issues:** GitHub Issues
- **Documentation:** This README and `/docs`
- **Email:** [Support email if available]

---

<div align="center">

**Built with ❤️ for learners who want to prove their skills, not just claim them.**

[⬆ Back to top](#sprintforgeai)

</div>