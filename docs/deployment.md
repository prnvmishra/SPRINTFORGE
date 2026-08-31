# Deploying SprintForge

## What makes this app different

Most "deploy a FastAPI app" advice does not apply here, because the API is not
a CRUD service. It compiles and runs learner code in five languages, shells out
to Node to parse JavaScript into an AST, and drives a headless Chromium to check
rendered HTML and CSS. The toolchain is the product, so the backend needs a real
container, not a 512MB Python slot.

Measured on the current build:

| | Boot time | Peak memory |
|---|---|---|
| Before the case-store split | 14s | 580MB |
| Now | 1.6s | 96MB |

That difference is what makes free hosting viable at all. The API used to parse
a 197MB test-case bank at import just to reach the few cases each module needs,
which put it over the 512MB ceiling every free tier enforces. It now reads a
1.7MB module manifest and pulls hidden cases per problem on demand.

## Recommended shape

**Frontend on Vercel.** It is a Next.js app, Vercel's free Hobby tier hosts it
well, and static assets are served from a CDN with no cold start. Set
`NEXT_PUBLIC_API_URL` to the backend's public URL. Hobby forbids commercial
use, which is fine for a hackathon and not for a business.

**Database on Neon.** The app already speaks PostgreSQL, so this is a
`DATABASE_URL` change and nothing else. Free Postgres on most hosts expires or
sleeps; check the current terms before a demo.

**Backend on a VM you control.** Oracle Cloud's Always Free ARM instance
(4 OCPU, 24GB RAM) is the only genuinely free option that runs this workload
without cold starts. A $5/month VPS does the same with far less signup
friction, and for a graded demo that is usually money well spent.

### Why not the usual free tiers

Verified in August 2026, and worth re-checking because these change often:

- **Render free** — 512MB and spins down after 15 minutes of inactivity, so the
  first request after a quiet period waits 30–60 seconds. Fatal for a live demo.
- **Koyeb** — no longer offers free compute, only a free Postgres database.
- **Fly.io** — no free tier for new accounts.
- **Railway** — a one-time $5 trial credit, not a free tier.
- **Google Cloud Run** — a genuinely generous always-free allowance, but it
  scales to zero. Keeping one instance always warm exceeds the free allowance by
  a wide margin, and scaling to zero reintroduces cold starts.
- **Hugging Face Spaces** — Docker Spaces moved behind a paid plan in July 2026.

## Build the case store first

Three artifacts, in this order. Only the first is slow.

```bash
cd backend
python -m scripts.build_test_cases          # ~7 min: derives every expected output
python -m scripts.split_case_bank           # partitions into the runtime store
python -m scripts.build_curriculum_manifest # writes the manifest the API reads
```

`build_test_cases.py` runs every reference solution and every known-wrong
solution, so it needs the full toolchain and it is the step that guarantees no
single submission can pass a suite it should fail. Run it on a machine you
trust, not in a deploy pipeline.

`visible.json` and `modules.json` are committed, so a fresh checkout boots. The
gzipped `cases/hidden/` directory is 76MB and is not, for the same reason the
197MB bank is not. Ship it explicitly:

```bash
tar czf cases.tgz -C backend/app/data cases
scp cases.tgz you@your-vm:/srv/sprintforge/
```

If it is missing, the API starts and serves problems normally, and fails with a
clear error the first time someone presses Submit. That is a real trap during a
demo — check it is present before you present.

## Backend on the VM

```bash
docker build -t sprintforge-api backend/
docker run -d --restart unless-stopped -p 8000:8000 \
  -e DATABASE_URL='postgresql+psycopg://...' \
  -e AUTH_SECRET="$(openssl rand -hex 32)" \
  -e CORS_ORIGINS='https://your-app.vercel.app' \
  -e CORS_ORIGIN_REGEX='' \
  -e ENVIRONMENT=production \
  sprintforge-api
```

The image build fails fast if the case store is absent, so a broken image does
not reach a demo.

### Settings that matter in production

See the table in the main README for the full list. The ones that bite:

- `AUTH_SECRET` — the default is a documented placeholder. Anyone who reads the
  repository can forge a token against a deployment that keeps it.
- `CORS_ORIGIN_REGEX` — defaults to trusting any localhost port for dev
  convenience. Clear it in production.
- `CODE_EXECUTION_PROVIDER` — see below.
- `AI_PROVIDER` — falls back to `mock` when the matching key is absent, so a
  deployment missing its key degrades quietly rather than erroring. Verify the
  AI verdicts you expect are real ones.

## Running learner code safely

`CODE_EXECUTION_PROVIDER=local` runs submitted code as the API process's own
user. Its own docstring is explicit that this is not a security boundary. It is
right for local development and wrong for anything reachable from the internet;
many hosts also forbid it outright.

For a deployment, either:

- **Self-host Piston** in Docker on the same VM and point `PISTON_URL` at it.
  This is the recommended setup: proper sandboxing, and no dependency on a
  stranger's uptime during your demo.
- **Use the public Piston** at `https://emkc.org/api/v2/piston`. Zero setup, but
  rate-limited and shared, so it can fail mid-demo.

Note that switching away from `local` does not remove the toolchain from the
image: the deterministic validator's Node AST helper and the Chromium render
judge still run in-process.
