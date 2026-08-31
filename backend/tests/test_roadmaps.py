"""Roadmaps: resolution, honesty, and the shape of the data.

Link liveness is deliberately not tested here. It depends on the network and on
YouTube not deleting a video today, so asserting it would make the suite flaky
and would fail for reasons no code change caused. `scripts/verify_resource_links.py`
does that check on demand instead. What is tested here is everything that is
our fault when it breaks.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.data.roadmaps import ROADMAPS, SKILL_ALIASES
from app.main import app
from app.models import LearningDigitalTwin, User, VerifiedSkill
from app.services import path_service, roadmap_service
from app.services.knowledge_graph import get_knowledge_graph


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Anonymous by default, which is the interesting case: these endpoints are
    public and must not require or create a twin."""
    return TestClient(app)


# --------------------------------------------------------------- data shape


def test_every_roadmap_has_the_fields_the_ui_reads():
    for roadmap in ROADMAPS:
        for field in ("id", "label", "aliases", "summary", "why", "prerequisites", "steps"):
            assert field in roadmap, f"{roadmap.get('id')} is missing {field}"
        assert roadmap["steps"], f"{roadmap['id']} has no steps"


def test_roadmap_ids_are_unique():
    ids = [roadmap["id"] for roadmap in ROADMAPS]
    assert len(ids) == len(set(ids))


def test_every_step_states_an_objective_and_offers_something_to_read():
    def walk(steps, owner):
        for step in steps:
            assert step.get("title"), f"{owner} has a step with no title"
            assert step.get("objective"), f"{owner}/{step['title']} has no objective"
            assert step.get("resources"), f"{owner}/{step['title']} has no resources"
            walk(step.get("children", []), owner)

    for roadmap in ROADMAPS:
        walk(roadmap["steps"], roadmap["id"])


def test_prerequisites_reference_skills_that_actually_exist():
    """A prerequisite naming a skill we do not grade would render as a dead
    requirement the learner can never satisfy."""
    graph = get_knowledge_graph()
    for roadmap in ROADMAPS:
        for skill_id in roadmap["prerequisites"]:
            assert graph.get(skill_id) is not None, f"{roadmap['id']} requires unknown {skill_id}"


def test_skill_aliases_point_at_real_skills():
    graph = get_knowledge_graph()
    for alias, skill_id in SKILL_ALIASES.items():
        assert graph.get(skill_id) is not None, f"alias {alias!r} points at unknown {skill_id}"


def test_youtube_links_are_watch_urls_or_searches_only():
    """Guards against a bare channel or playlist link sneaking in, which the
    verifier cannot check for liveness the same way."""
    def urls(roadmap):
        out = []
        if roadmap.get("course"):
            out.append(roadmap["course"]["url"])

        def walk(steps):
            for step in steps:
                out.extend(r["url"] for r in step.get("resources", []))
                walk(step.get("children", []))

        walk(roadmap["steps"])
        return out

    for roadmap in ROADMAPS:
        for url in urls(roadmap):
            if "youtube.com" not in url:
                continue
            assert "/watch?v=" in url or "/results?" in url, f"{roadmap['id']}: odd YouTube URL {url}"


# ---------------------------------------------------------------- resolution


@pytest.mark.parametrize(
    "query,outcome,expected",
    [
        # Things we grade resolve to the skill, never to a reading list.
        ("i want to learn react", "graded_skill", "react_fundamentals"),
        ("sikhna hai sql", "graded_skill", "sql_basics"),
        ("typescript sikhao", "graded_skill", "typescript_basics"),
        # The more specific request wins even across the graded/guided line.
        ("i want to learn react native", "roadmap", "react_native"),
        # Things we do not grade resolve to a roadmap.
        ("mujhe docker sikhna hai", "roadmap", "docker"),
        ("teach me system design", "roadmap", "system_design"),
        ("i want to learn git", "roadmap", "git"),
        # An alias, not the label.
        ("how do i learn kubernetes", "roadmap", "docker"),
    ],
)
def test_resolution(client, query, outcome, expected):
    payload = client.get("/roadmaps/resolve", params={"q": query}).json()
    assert payload["outcome"] == outcome
    actual = payload["skill_id"] if outcome == "graded_skill" else payload["roadmap"]["id"]
    assert actual == expected


def test_cpp_is_not_swallowed_by_c():
    """`c++` normalises to `c`, so without special handling a C++ request lands
    on the C curriculum. This is the regression that caught it."""
    from app.services import roadmap_service

    result = roadmap_service.resolve(None, None, "i want to learn c++")
    assert result["skill_id"] == "cpp_basics"

    result = roadmap_service.resolve(None, None, "i want to learn c")
    assert result["skill_id"] == "c_basics"


def test_unknown_subjects_say_so_and_offer_what_exists(client):
    payload = client.get("/roadmaps/resolve", params={"q": "quantum knitting"}).json()
    assert payload["outcome"] == "unknown"
    assert payload["roadmap"] is None
    assert payload["available"], "an unknown answer should still list what we do have"


# ------------------------------------------------------------------ honesty


def test_a_roadmap_never_claims_to_be_graded(client):
    for roadmap in ROADMAPS:
        payload = client.get(f"/roadmaps/{roadmap['id']}").json()
        assert payload["graded"] is False
        assert "not a verified skill" in payload["disclaimer"]


def test_unknown_roadmap_is_404(client):
    assert client.get("/roadmaps/does-not-exist").status_code == 404


def test_catalogue_lists_every_roadmap(client):
    payload = client.get("/roadmaps").json()
    assert {r["id"] for r in payload["roadmaps"]} == {r["id"] for r in ROADMAPS}


def test_anonymous_callers_get_roadmaps_without_confidence(client):
    """No session means no twin, and prerequisites must degrade to 'unmeasured'
    rather than to a fabricated zero."""
    payload = client.get("/roadmaps/docker").json()
    for prerequisite in payload["prerequisites"]:
        assert prerequisite["confidence"] is None
        assert prerequisite["verified"] is False


# ------------------------------------------------- the signed-in annotation
#
# Everything above runs anonymously, where `twin` is None and the annotation
# short-circuits before it reads anything off the twin. That is exactly how a
# shipped 500 stayed green: the service read a twin attribute that does not
# exist, and no test ever handed it a twin. These do.


def build_twin(confidences: dict[str, float]):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    user = User(name="Signed In", email="signed-in@test.local")
    twin = LearningDigitalTwin(user=user, goal="Ship a container")
    db.add_all([user, twin])
    db.flush()
    graph = get_knowledge_graph()
    for skill_id, confidence in confidences.items():
        db.add(
            VerifiedSkill(
                twin_id=twin.id,
                skill_id=skill_id,
                skill_name=graph.name_of(skill_id),
                confidence=confidence,
                verified_level="verified" if confidence >= 65 else "unverified",
            )
        )
    db.commit()
    return db, twin


def test_a_signed_in_learner_can_open_a_roadmap():
    """The regression: this raised AttributeError for every authenticated user."""
    db, twin = build_twin({"node_basics": 82.0})
    payload = roadmap_service.detail(db, twin, "docker")
    assert payload is not None
    assert payload["id"] == "docker"


def test_proved_prerequisites_are_reported_as_verified():
    db, twin = build_twin({"node_basics": 82.0})
    payload = roadmap_service.detail(db, twin, "docker")
    node = next(p for p in payload["prerequisites"] if p["skill_id"] == "node_basics")
    assert node["confidence"] == pytest.approx(82.0)
    assert node["verified"] is True
    assert "node_basics" not in {p["skill_id"] for p in payload["unmet_prerequisites"]}


def test_a_weak_prerequisite_stays_unmet_for_a_signed_in_learner():
    db, twin = build_twin({"node_basics": 20.0})
    payload = roadmap_service.detail(db, twin, "docker")
    node = next(p for p in payload["prerequisites"] if p["skill_id"] == "node_basics")
    assert node["verified"] is False
    assert "node_basics" in {p["skill_id"] for p in payload["unmet_prerequisites"]}


def test_resolution_annotates_the_roadmap_it_returns():
    """`resolve` reaches `detail` with the twin, so it shares the same crash path."""
    db, twin = build_twin({"node_basics": 82.0})
    payload = roadmap_service.resolve(db, twin, "i want to learn docker")
    assert payload["outcome"] == "roadmap"
    assert payload["roadmap"]["id"] == "docker"


def test_the_twin_confidence_comes_from_the_shared_accessor():
    """Guards against a private re-read drifting from the graded numbers, which
    is how the original bug was introduced."""
    db, twin = build_twin({"node_basics": 82.0})
    assert roadmap_service._confidence_map(db, twin) == path_service.learner_confidence(db, twin)
