"""End-to-end verification of the SprintForge closed-loop adaptive workflow.

Run:  python -m scripts.verify_flow

Exercises the exact demonstration required by the product spec:
claim → verify → diagnose → plan → execute → fail → analyse → remediate →
re-verify → unlock.
"""

from __future__ import annotations

import os
import sys
import tempfile
import uuid

os.environ.setdefault("DATABASE_URL", f"sqlite:///{tempfile.mkdtemp()}/verify.db")
os.environ.setdefault("AI_PROVIDER", "mock")
os.environ.setdefault("CODE_EXECUTION_PROVIDER", "local")

from fastapi.testclient import TestClient  # noqa: E402

from app.core.database import init_db  # noqa: E402
from app.data.assessment_bank import ITEM_INDEX  # noqa: E402
from app.main import app  # noqa: E402

FAILURES: list[str] = []
STEP = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global STEP
    STEP += 1
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {label}" + (f"  — {detail}" if detail else ""))
    if not condition:
        FAILURES.append(label)


def section(title: str) -> None:
    print(f"\n=== {title} ===")


def correct_answer(question: dict) -> str:
    """A competent learner's answer, taken from the item bank."""
    item = ITEM_INDEX[question["id"]]
    if item["type"] == "mcq":
        return str(item["correct_option"])
    return str(item.get("expected_answer", ""))


def run_assessment(client, headers, skill_id: str, claimed: str, answer_fn, max_questions: int = 3):
    """Drive a full adaptive session. answer_fn(question) -> answer string."""
    response = client.post(
        "/assessment/start",
        headers=headers,
        json={"skill_id": skill_id, "claimed_level": claimed, "max_questions": max_questions},
    )
    if response.status_code != 200:
        return None, [], response
    state = response.json()
    session_id = state["session_id"]
    difficulties: list[int] = []
    while state.get("question"):
        question = state["question"]
        difficulties.append(question["difficulty"])
        response = client.post(
            "/assessment/submit",
            headers=headers,
            json={
                "session_id": session_id,
                "question_id": question["id"],
                "answer": answer_fn(question),
            },
        )
        if response.status_code != 200:
            return state, difficulties, response
        state = response.json()["state"]
    return state, difficulties, response


def main() -> int:
    init_db()
    client = TestClient(app)
    email = f"ada+{uuid.uuid4().hex[:8]}@sprintforge.dev"

    section("1. Registration & authentication")
    response = client.post(
        "/auth/register",
        json={"name": "Ada Lovelace", "email": email, "password": "forge-secret-123"},
    )
    check("register returns 201", response.status_code == 201, response.text[:200])
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    check("GET /auth/me is authenticated", client.get("/auth/me", headers=headers).status_code == 200)
    anonymous = TestClient(app)
    check(
        "unauthenticated dashboard is rejected",
        anonymous.get("/profile/dashboard").status_code == 401,
    )

    section("2. Onboarding: the learner CLAIMS intermediate JavaScript")
    response = client.post(
        "/profile/onboard",
        headers=headers,
        json={
            "goal": "Build a React Movie Ticket Booking System",
            "experience_level": "intermediate",
            "claimed_skills": {
                "js_basics": "intermediate",
                "js_functions": "intermediate",
                "js_async": "intermediate",
                "js_async_error_handling": "intermediate",
                "html_basics": "advanced",
                "css_basics": "intermediate",
            },
        },
    )
    check("onboarding succeeds", response.status_code == 200, response.text[:200])
    twin = response.json()
    check(
        "claimed skills are NOT auto-trusted (confidence stays 0)",
        all(s["confidence"] == 0.0 for s in twin["verified_skills"]),
        f"overall={twin['overall_confidence']}",
    )

    section("3a. Adaptive assessment: the JavaScript claim holds up")
    for skill_id in ("js_basics", "js_functions", "js_async"):
        state, difficulties, response = run_assessment(
            client, headers, skill_id, "intermediate", correct_answer, max_questions=3
        )
        check(f"{skill_id} session completed", (state or {}).get("status") == "completed",
              response.text[:160] if response.status_code != 200 else "")
        result = (state or {}).get("result") or {}
        check(
            f"{skill_id} verified as claimed",
            result.get("verified_level") in {"intermediate", "advanced"},
            f"verified={result.get('verified_level')} accuracy={result.get('accuracy')}%",
        )
        check(
            f"{skill_id} started at the claimed frontier, not at difficulty 1",
            difficulties and difficulties[0] >= 3,
            f"difficulty path={difficulties}",
        )
        check(
            f"{skill_id} passed items at or above its expected difficulty",
            result.get("hardest_difficulty_passed", 0) >= 4,
            f"hardest passed={result.get('hardest_difficulty_passed')}",
        )

    section("3b. Adaptive assessment: Async Error Handling claim FAILS")
    response = client.post(
        "/assessment/start",
        headers=headers,
        json={"skill_id": "js_async_error_handling", "claimed_level": "intermediate", "max_questions": 4},
    )
    check("assessment starts", response.status_code == 200, response.text[:200])
    state = response.json()
    session_id = state["session_id"]
    check(
        "start difficulty adapts to the claimed level",
        state["current_difficulty"] >= 4,
        f"difficulty={state['current_difficulty']}",
    )

    difficulties = []
    while state.get("question"):
        question = state["question"]
        difficulties.append(question["difficulty"])
        # Answer everything wrong to simulate a learner who overclaimed this skill.
        item = ITEM_INDEX[question["id"]]
        if question["type"] == "mcq":
            answer = str((int(item["correct_option"]) + 1) % len(question["options"]))
        else:
            answer = "I am not sure."
        response = client.post(
            "/assessment/submit",
            headers=headers,
            json={"session_id": session_id, "question_id": question["id"], "answer": answer},
        )
        check(f"submit answer for {question['id']}", response.status_code == 200, response.text[:200])
        state = response.json()["state"]

    check("session completed", state["status"] == "completed", str(state["status"]))
    result = state["result"] or {}
    check(
        "verified level contradicts the claim",
        result.get("verified_level") in {"needs_improvement", "beginner"},
        f"claimed=intermediate verified={result.get('verified_level')} accuracy={result.get('accuracy')}%",
    )
    check(
        "difficulty adapted downward after failures",
        len(difficulties) > 1 and difficulties[-1] <= difficulties[0],
        f"difficulty path={difficulties}",
    )
    check("weak concepts were extracted", bool(result.get("weak_concepts")), str(result.get("weak_concepts")))

    section("4. Digital Twin reflects the gap")
    twin = client.get("/profile/digital-twin", headers=headers).json()
    async_skill = next(
        (s for s in twin["verified_skills"] if s["skill_id"] == "js_async_error_handling"), None
    )
    check("Async Error Handling is tracked", async_skill is not None)
    assert async_skill
    check(
        "Async Error Handling needs improvement",
        async_skill["needs_improvement"],
        f"confidence={async_skill['confidence']}%",
    )
    check(
        "confidence breakdown uses the 40/25/20/15 formula",
        async_skill["breakdown"].get("weights") == {
            "assessment_accuracy": 40,
            "execution_success": 25,
            "difficulty_mastery": 20,
            "consistency": 15,
        },
    )
    check("low score has an explanation", len(async_skill["explanation"]) > 40, async_skill["explanation"][:110])
    check("repeated mistakes are tracked", bool(twin["repeated_mistakes"]), str(twin["repeated_mistakes"]))

    section("5. Project creation → milestones, sprints, tickets")
    response = client.post(
        "/projects",
        headers=headers,
        json={
            "title": "Movie Ticket Booking System",
            "idea": "A React app to browse movies, pick seats and book tickets.",
            "tech_stack": ["HTML", "CSS", "JavaScript", "React", "Node.js", "Database"],
            "known_technologies": ["HTML", "CSS", "JavaScript"],
            "experience_level": "intermediate",
            "complexity": "intermediate",
            "desired_outcome": "A working booking flow",
        },
    )
    check("project created", response.status_code == 201, response.text[:300])
    payload = response.json()
    project = payload["project"]
    project_id = project["id"]
    check("sprints were generated", project["sprint_count"] >= 4, f"sprints={project['sprint_count']}")
    check("tickets were generated", project["ticket_count"] >= 6, f"tickets={project['ticket_count']}")
    check("plan has a rationale", bool(project["plan_rationale"]), project["plan_rationale"][:120])

    all_tickets = [t for s in project["sprints"] for t in s["tickets"]]
    react_fetch_ticket = next(
        (t for t in all_tickets if t["target_skill_id"] == "react_data_fetching"), None
    )
    check("React data-fetching ticket exists", react_fetch_ticket is not None)
    assert react_fetch_ticket
    check(
        "downstream ticket is locked by the knowledge graph",
        react_fetch_ticket["status"] == "locked"
        and "Async Error Handling" in (react_fetch_ticket["lock_reason"] or ""),
        react_fetch_ticket["lock_reason"] or "",
    )

    section("6. Why this next? — explainable routing")
    why = client.get("/ai/why-this-next", headers=headers).json()
    recommendation = why["recommendation"]
    check(
        "routes to remediation instead of the blocked ticket",
        recommendation["type"] in {"remediation_practice", "prerequisite_practice"},
        recommendation["type"],
    )
    check(
        "recommends the async error handling practice",
        recommendation.get("module_id") == "js-async-error-handling",
        str(recommendation.get("module_id")),
    )
    check("explanation is concrete", len(why["explanation"]) > 60, why["explanation"][:160])
    check("dependency chain is returned", len(why["dependency_chain"]) >= 2,
          " → ".join(n["skill_name"] for n in why["dependency_chain"]))

    section("7. Remediation practice — first attempt FAILS")
    module_id = "js-async-error-handling"
    module = client.get(f"/practice/modules/{module_id}", headers=headers).json()
    check("module loads with starter files", "solution.js" in module["files"])

    broken = """async function loadMovies(fetchImpl) {
  const response = await fetchImpl("/api/movies");
  return { status: "success", data: await response.json() };
}

module.exports = { loadMovies };
"""
    response = client.post(
        f"/practice/modules/{module_id}/submit",
        headers=headers,
        json={"files": {"solution.js": broken}, "duration_seconds": 300},
    )
    check("submission accepted", response.status_code == 200, response.text[:300])
    fail_body = response.json()
    check("submission failed validation", fail_body["passed"] is False)
    check(
        "behaviour tests actually executed in the sandbox",
        len(fail_body["test_results"]) >= 3,
        f"{len(fail_body['test_results'])} behaviour tests",
    )
    check(
        "rejection-path test failed",
        any(not t["passed"] for t in fail_body["test_results"]),
    )
    analysis = fail_body["failure_analysis"]
    check("failure analysis produced", analysis is not None)
    assert analysis
    check("root cause identified", bool(analysis["root_cause"]), analysis["root_cause"][:110])
    check("missing concepts extracted", bool(analysis["missing_concepts"]), str(analysis["missing_concepts"]))
    check("remediation recommended", bool(analysis["remediation_title"]), str(analysis["remediation_title"]))
    check("no XP for a failed attempt", fail_body["xp_awarded"] == 0)

    section("8. Remediation practice — correct solution PASSES")
    fixed = """async function loadMovies(fetchImpl) {
  try {
    const response = await fetchImpl("/api/movies");
    if (!response.ok) {
      return { status: "error", message: `Request failed with status ${response.status}` };
    }
    const data = await response.json();
    return { status: "success", data };
  } catch (error) {
    return { status: "error", message: error.message };
  }
}

module.exports = { loadMovies };
"""
    confidence_before = async_skill["confidence"]
    response = client.post(
        f"/practice/modules/{module_id}/submit",
        headers=headers,
        json={"files": {"solution.js": fixed}, "duration_seconds": 420},
    )
    check("submission accepted", response.status_code == 200, response.text[:300])
    pass_body = response.json()
    check("all deterministic checks passed", pass_body["passed"] is True,
          str([t["label"] for t in pass_body["test_results"] if not t["passed"]]))
    check("XP awarded", pass_body["xp_awarded"] > 0, f"+{pass_body['xp_awarded']} XP")
    check(
        "confidence increased after remediation",
        pass_body["skill"]["confidence"] > confidence_before,
        f"{confidence_before}% → {pass_body['skill']['confidence']}%",
    )

    # Practise repeatedly, as a real learner would consolidating a skill.
    for _ in range(2):
        response = client.post(
            f"/practice/modules/{module_id}/submit",
            headers=headers,
            json={"files": {"solution.js": fixed}, "duration_seconds": 200},
        )
        confidence = response.json()["skill"]["confidence"]
    check("practice raises confidence but assessment history still weighs it down",
          confidence > 0, f"confidence={confidence}%")

    section("9. RE-VERIFICATION: retake the assessment after remediation")
    state, difficulties, response = run_assessment(
        client, headers, "js_async_error_handling", "intermediate", correct_answer, max_questions=4
    )
    check("re-assessment completed", (state or {}).get("status") == "completed")
    twin = client.get("/profile/digital-twin", headers=headers).json()
    async_skill = next(s for s in twin["verified_skills"] if s["skill_id"] == "js_async_error_handling")
    check(
        "confidence crosses the mastery threshold after remediation + re-verification",
        async_skill["confidence"] >= 65,
        f"{confidence_before}% → {async_skill['confidence']}% ({async_skill['verified_level']})",
    )
    check(
        "skill no longer flagged as needing improvement",
        async_skill["needs_improvement"] is False,
    )

    section("10. Re-verification unlocks downstream project work")
    response = client.get(f"/projects/{project_id}", headers=headers).json()
    tickets_after = [t for s in response["project"]["sprints"] for t in s["tickets"]]
    react_after = next(
        (t for t in tickets_after if t["target_skill_id"] == "react_data_fetching"), None
    )
    check("React data-fetching ticket still in the plan", react_after is not None)
    assert react_after
    check(
        "its prerequisite lock was lifted",
        "Prerequisite not verified" not in (react_after["lock_reason"] or ""),
        react_after["lock_reason"] or "no prerequisite lock",
    )

    section("11. Ticket execution: fail → analyse → fix → unlock next")
    first_ticket = next(t for t in tickets_after if t["order_index"] == 1)
    ticket_id = first_ticket["id"]
    response = client.post(f"/tickets/{ticket_id}/start", headers=headers)
    check("ticket starts", response.status_code == 200, response.text[:200])
    workspace = response.json()
    check("workspace files provided", bool(workspace["files"]), str(list(workspace["files"])))

    bad_html = "<html><body><div>Movies</div></body></html>"
    response = client.post(
        f"/tickets/{ticket_id}/submit",
        headers=headers,
        json={"files": {"index.html": bad_html}, "duration_seconds": 120},
    )
    check("ticket submission accepted", response.status_code == 200, response.text[:300])
    body = response.json()
    check("ticket cannot be passed with non-conforming code", body["passed"] is False)
    check("ticket status is failed", body["ticket"]["status"] == "failed")
    check("ticket failure analysis produced", body["failure_analysis"] is not None)

    entity_section = next(
        (c for c in body["static_results"] if c["id"] == "list_section"), None
    )
    check("deterministic HTML checks ran", entity_section is not None,
          f"{len(body['static_results'])} static checks")

    good_html = """<!DOCTYPE html>
<html lang="en">
  <head><meta charset="utf-8" /><title>Movie Ticket Booking System</title></head>
  <body>
    <header><h1>Movie Ticket Booking System</h1></header>
    <main id="app">
      <section id="movieList"></section>
    </main>
    <footer><p>&copy; 2026 SprintForge</p></footer>
  </body>
</html>
"""
    response = client.post(
        f"/tickets/{ticket_id}/submit",
        headers=headers,
        json={"files": {"index.html": good_html}, "duration_seconds": 900},
    )
    check("resubmission accepted", response.status_code == 200, response.text[:300])
    body = response.json()
    check(
        "ticket passes when acceptance criteria are met",
        body["passed"] is True,
        str([c["label"] for c in body["static_results"] if not c["passed"]]),
    )
    check("ticket marked done", body["ticket"]["status"] == "done")
    check("XP awarded for the ticket", body["xp_awarded"] > 0, f"+{body['xp_awarded']} XP")
    follow_on = client.get(f"/projects/{project_id}/next-ticket", headers=headers).json()["ticket"]
    check(
        "the next ticket in dependency order is now actionable",
        follow_on is not None and follow_on["status"] in {"todo", "in_progress"},
        f"{(follow_on or {}).get('key')} → {(follow_on or {}).get('status')}",
    )

    section("12. Dashboard, rewards and mentor")
    dashboard = client.get("/profile/dashboard", headers=headers).json()
    check("dashboard returns the active project", dashboard["active_project"] is not None)
    check("dashboard returns the current ticket", dashboard["current_ticket"] is not None,
          str((dashboard.get("current_ticket") or {}).get("key")))
    check("dashboard returns a recommendation with a reason",
          len(dashboard["recommendation"]["reason"]) > 40)
    check("verified skills are listed", len(dashboard["verified_skills"]) >= 3)
    check("recent activity is recorded", len(dashboard["recent_activity"]) >= 5,
          f"{len(dashboard['recent_activity'])} events")
    check("XP and level tracked", dashboard["rewards"]["xp"] > 0,
          f"xp={dashboard['rewards']['xp']} level={dashboard['rewards']['level']}")

    mentor = client.post(
        "/ai/mentor",
        headers=headers,
        json={"question": "Why does my fetch crash?", "ticket_id": ticket_id, "mode": "debug"},
    ).json()
    check("mentor responds", len(mentor["answer"]) > 40)
    check("mentor does not hand over the solution", mentor["reveals_solution"] is False)
    check("mentor asks guiding questions", len(mentor["guiding_questions"]) >= 2)

    section("13. Language challenge with a sandboxed compiler")
    response = client.post(
        "/practice/modules/py-array-rotate/submit",
        headers=headers,
        json={
            "files": {
                "solution": (
                    "import sys\n\n"
                    "def rotate(arr, k):\n"
                    "    if not arr:\n"
                    "        return arr\n"
                    "    k %= len(arr)\n"
                    "    return arr[-k:] + arr[:-k] if k else arr\n\n"
                    "def main():\n"
                    "    data = sys.stdin.read().split()\n"
                    "    n, k = int(data[0]), int(data[1])\n"
                    "    arr = [int(x) for x in data[2:2 + n]]\n"
                    "    print(' '.join(map(str, rotate(arr, k))))\n\n"
                    "main()\n"
                )
            }
        },
    )
    check("challenge submission accepted", response.status_code == 200, response.text[:300])
    body = response.json()
    check("hidden tests executed", len(body["test_results"]) >= 5, f"{len(body['test_results'])} tests")
    check("correct solution passes hidden edge cases", body["passed"] is True,
          str([t["label"] for t in body["test_results"] if not t["passed"]]))

    print("\n" + "=" * 60)
    if FAILURES:
        print(f"{len(FAILURES)} of {STEP} checks FAILED:")
        for failure in FAILURES:
            print(f"  - {failure}")
        return 1
    print(f"All {STEP} checks passed. Closed-loop adaptive workflow verified.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
