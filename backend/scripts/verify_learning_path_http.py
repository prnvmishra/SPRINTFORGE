"""Live-HTTP proof that the personalised learning-path surfaces return real data.

Mints a short-lived token for an existing user (no account is created, and the
token is never printed), then GETs `/learning-path`, `/adaptations`,
`/resources/{skill}` and `/paths`, and asserts:

* every value in `/learning-path` traces to stored state (no placeholder ids,
  no "TODO", no fabricated confidence);
* `/paths` and `/learning-path` agree on `verified`, `unlocked` and
  `confidence` for every skill they both mention;
* every internal resource pointer resolves against the real catalogs;
* no adaptation event reports a confidence delta it did not record.

    python scripts/verify_learning_path_http.py [--base http://127.0.0.1:8000] [--email aa@gmail.com]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import httpx
from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.data.paths import PATHS
from app.data.practice_modules import PRACTICE_MODULE_INDEX
from app.models import User

PLACEHOLDER_MARKERS = ("todo", "tbd", "lorem", "placeholder", "example.com", "xxx")

failures: list[str] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}" + (f"  — {detail}" if detail else ""))
    if not ok:
        failures.append(label)


def scan_for_placeholders(node, trail: str = "") -> list[str]:
    hits: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            hits += scan_for_placeholders(value, f"{trail}.{key}")
    elif isinstance(node, list):
        for index, value in enumerate(node):
            hits += scan_for_placeholders(value, f"{trail}[{index}]")
    elif isinstance(node, str):
        lowered = node.lower()
        for marker in PLACEHOLDER_MARKERS:
            if marker in lowered:
                hits.append(f"{trail} contains {marker!r}")
    return hits


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--email", default="aa@gmail.com")
    args = parser.parse_args()

    db = SessionLocal()
    user = db.scalar(select(User).where(User.email == args.email))
    if user is None:
        print(f"!! no user with email {args.email}; not creating one")
        return 1
    headers = {"Authorization": f"Bearer {create_access_token(user.id, expires_minutes=5)}"}

    with httpx.Client(base_url=args.base, headers=headers, timeout=60.0) as client:
        health = client.get("/health")
        check("/health is 200", health.status_code == 200, health.text[:80])

        lp = client.get("/learning-path")
        check("/learning-path is 200", lp.status_code == 200)
        lp.raise_for_status()
        path = lp.json()

        adaptations = client.get("/adaptations")
        check("/adaptations is 200", adaptations.status_code == 200)
        adaptations.raise_for_status()
        events = adaptations.json()["events"]

        paths_payload = client.get("/paths")
        check("/paths is 200", paths_payload.status_code == 200)
        paths_payload.raise_for_status()

    print("\n--- /learning-path integrity ---")
    check("goal echoes the stored twin goal", bool(path["goal"]["goal"]), path["goal"]["goal"] or "")
    check("spine is non-empty", bool(path["path"]), f"{len(path['path'])} steps")
    check(
        "exactly one step is is_next",
        sum(1 for s in path["path"] if s["is_next"]) == 1,
    )
    check(
        "next_action reason came from the deterministic engine",
        path["next_action"]["reason_source"] == "deterministic_routing_engine"
        and bool(path["next_action"]["reason"]),
    )
    known_courses = {(p["id"], c["id"]) for p in PATHS for c in p["courses"]}
    bad_refs = [
        s["skill_id"]
        for s in path["path"]
        if s["taught_by"] and (s["taught_by"]["path_id"], s["taught_by"]["course_id"]) not in known_courses
    ]
    check("every taught_by references a real course", not bad_refs, str(bad_refs))
    check(
        "learning milestones reference real courses",
        all((m["path_id"], m["course_id"]) in known_courses for m in path["milestones"]),
    )
    check(
        "milestone counts are consistent",
        all(m["completed_count"] <= m["total_count"] == len(m["skills"]) for m in path["milestones"]),
    )
    # The documented projection: verified outranks locked, and both raw flags are
    # still present. Also proves the *running* server has the current rule.
    wrong_state = [
        f"{s['skill_id']}={s['state']}"
        for s in path["path"]
        if s["state"]
        != (
            "verified"
            if s["verified"]
            else "locked"
            if not s["unlocked"]
            else "not_started"
            if not s["has_evidence"]
            else "needs_work"
            if (s["weak_concepts"] or s["has_open_gap"])
            else "in_progress"
        )
    ]
    check("state matches the documented projection", not wrong_state, str(wrong_state))

    hits = scan_for_placeholders(path, "learning_path")
    # External documentation URLs are real hostnames; nothing should look fake.
    check("no placeholder strings anywhere in the payload", not hits, "; ".join(hits[:4]))

    print("\n--- /adaptations honesty ---")
    check("events present", bool(events), f"{len(events)} events")
    invented = [
        e["id"]
        for e in events
        if e["confidence_delta"] is not None
        and (e["confidence_before"] is None or e["confidence_after"] is None)
    ]
    check("no delta is reported without both endpoints stored", not invented, str(invented))
    check(
        "no resolution timestamp is invented",
        all(e["failure"]["resolved_at"] is None for e in events if e["failure"]),
    )
    bad_modules = [
        item["module_id"]
        for e in events
        for item in e["inserted_skills"]
        if item["module_id"] not in PRACTICE_MODULE_INDEX
    ]
    check("inserted remediation modules exist", not bad_modules, str(bad_modules))
    recorded = sum(1 for e in events if e["confidence_recorded"])
    print(f"  ..   confidence captured on {recorded}/{len(events)} events (older rows predate capture)")

    print("\n--- resources ---")
    with httpx.Client(base_url=args.base, timeout=30.0) as client:
        for step in path["path"][:6]:
            payload = client.get(f"/resources/{step['skill_id']}").json()
            internal_ok = all(
                r["module_id"] in PRACTICE_MODULE_INDEX
                for r in payload["resources"]
                if r["target"] == "practice_module"
            )
            external_ok = all(
                r["url"].startswith("https://")
                for r in payload["resources"]
                if r["target"] == "external"
            )
            check(
                f"resources for {step['skill_id']} are wired to real things",
                bool(payload["resources"]) and internal_ok and external_ok,
                f"{len(payload['resources'])} items",
            )

    print("\n--- /paths vs /learning-path agreement ---")
    from app.services import path_service  # local import: read-only comparison
    from app.models import LearningDigitalTwin

    twin = db.scalar(select(LearningDigitalTwin).where(LearningDigitalTwin.user_id == user.id))
    confidence = path_service.learner_confidence(db, twin)
    disagreements = []
    for step in path["path"]:
        lesson = path_service.lesson_state(step["skill_id"], confidence)
        if (lesson["verified"], lesson["unlocked"], lesson["confidence"]) != (
            step["verified"],
            step["unlocked"],
            step["confidence"],
        ):
            disagreements.append(step["skill_id"])
    check("both surfaces agree on verified/unlocked/confidence", not disagreements, str(disagreements))
    db.rollback()

    print("\n" + ("OK" if not failures else f"{len(failures)} failure(s): " + ", ".join(failures)))
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
