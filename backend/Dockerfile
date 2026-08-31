# SprintForge API.
#
# This image is larger than a typical Python service and unavoidably so: the
# judge does not merely serve problems, it compiles and runs learner code in
# five languages and drives a headless browser to check rendered HTML/CSS. The
# toolchain *is* the product. Concretely it needs gcc, g++, a JDK, Node (both
# for the JavaScript judge and for the deterministic validator's AST helper),
# and Chromium for app/services/render_judge.py.
#
# Build from the backend/ directory:
#     docker build -t sprintforge-api backend/
#
# The case store is NOT built here. `scripts/build_test_cases.py` executes every
# reference solution to derive expected outputs, which takes about seven minutes
# and would make every image build pay for it. Build it once on a machine you
# trust and mount or copy app/data/cases/ in. See docs/deployment.md.

FROM python:3.13-slim

# Judged languages plus the validator's Node helper. Kept in one layer so the
# apt cache is not committed to the image.
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        default-jdk-headless \
        nodejs \
        npm \
        curl \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Dependencies before source, so an edit to the application does not reinstall
# them or re-download Chromium.
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Chromium for the rendered HTML/CSS checks. `--with-deps` pulls the shared
# libraries a headless browser needs, which a slim base image does not have.
# Without this the rendered checks fail loudly rather than silently passing.
RUN playwright install --with-deps chromium

# The deterministic validator shells out to this to parse learner JavaScript.
COPY app/tools/js_ast/package.json app/tools/js_ast/package-lock.json* ./app/tools/js_ast/
RUN cd app/tools/js_ast && npm install --omit=dev

COPY . .

# For cloud deployment, only check for visible.json and modules.json
# Hidden cases are built separately due to size (76MB) and build time (7+ minutes)
# For production deployment, hidden cases should be provided via volume or separate build
RUN python -c "import pathlib, sys; \
    p = pathlib.Path('app/data/cases'); \
    missing = [n for n in ('visible.json', 'modules.json') if not (p / n).exists()]; \
    sys.exit('Case store incomplete: ' + ', '.join(missing) + \
    '. Run scripts/build_test_cases.py, scripts/split_case_bank.py and ' \
    'scripts/build_curriculum_manifest.py, then rebuild.') if missing else None"

ENV PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

EXPOSE 8000

# Single worker on purpose. Each one holds its own copy of the module manifest
# and its own hidden-case cache, so workers multiply memory; scale with more
# containers instead, or raise this only after measuring.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT}"]
