#!/usr/bin/env bash
# Installs the language runtimes the curriculum needs into a running Piston.
#
# A fresh Piston container ships with no languages at all, so submissions fail
# with "runtime not found" until this runs. Idempotent: re-running an install
# that already exists is a no-op on Piston's side.
#
# Usage:  ./scripts/install_judge_languages.sh [PISTON_URL]

set -euo pipefail

PISTON_URL="${1:-http://localhost:2000/api/v2}"

# Versions are pinned so a grading run is reproducible: an unpinned runtime
# upgrade could change output formatting and silently break generated cases.
declare -a RUNTIMES=(
  "python 3.12.0"
  "node 20.11.1"
  "c++ 10.2.0"
)

echo "Waiting for Piston at ${PISTON_URL} ..."
for _ in $(seq 1 60); do
  if curl -fsS "${PISTON_URL}/runtimes" >/dev/null 2>&1; then
    echo "Piston is up."
    break
  fi
  sleep 2
done

if ! curl -fsS "${PISTON_URL}/runtimes" >/dev/null 2>&1; then
  echo "ERROR: Piston did not become reachable at ${PISTON_URL}" >&2
  echo "Start it with: docker compose -f docker-compose.judge.yml up -d" >&2
  exit 1
fi

for runtime in "${RUNTIMES[@]}"; do
  read -r language version <<<"${runtime}"
  echo "Installing ${language} ${version} ..."
  curl -fsS -X POST "${PISTON_URL}/packages" \
    -H "Content-Type: application/json" \
    -d "{\"language\":\"${language}\",\"version\":\"${version}\"}" \
    || echo "  (already installed or unavailable, continuing)"
  echo
done

echo "Installed runtimes:"
curl -fsS "${PISTON_URL}/runtimes" \
  | python3 -c 'import json,sys; [print("  -", r["language"], r["version"]) for r in json.load(sys.stdin)]' \
  2>/dev/null || echo "  (could not parse runtime list)"

cat <<'EOF'

Next: point the API at this judge in backend/.env

  CODE_EXECUTION_PROVIDER=piston
  PISTON_URL=http://localhost:2000/api/v2

Then restart the backend and run a submission to confirm the provider label
reported in execution results reads "piston" rather than "local".
EOF
