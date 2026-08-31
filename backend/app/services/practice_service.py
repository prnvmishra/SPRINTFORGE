"""Practice Mode orchestration: modules, running code, and graded submission."""

from __future__ import annotations

import asyncio
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.data.practice_modules import PRACTICE_MODULE_INDEX, PRACTICE_MODULES
from app.models import ExecutionAttempt, LearningDigitalTwin, PracticeAttempt
from app.schemas.ai import EvaluationRequest, EvaluationResult
from app.schemas.execution import ExecutionResult, TestCase
from app.services import digital_twin_service as twin_service
from app.services import render_judge
from app.services import failure_analysis_service, reward_service
from app.services.ai_evaluator import get_ai_provider
from app.services.code_execution_service import get_code_execution_service
from app.services.knowledge_graph import get_knowledge_graph
from app.services.validation_service import run_behaviour_tests, run_static_checks
from app.services import sql_judge


def list_modules(technology: Optional[str] = None, layer: Optional[str] = None) -> list[dict[str, Any]]:
    graph = get_knowledge_graph()
    modules = []
    for module in PRACTICE_MODULES:
        if technology and module["technology"].lower() != technology.lower():
            continue
        if layer and module.get("practice_layer") != layer:
            continue
        modules.append(
            {
                "id": module["id"],
                "title": module["title"],
                "kind": module["kind"],
                "practice_layer": module.get("practice_layer"),
                "technology": module["technology"],
                "skill_id": module["skill_id"],
                "skill_name": graph.name_of(module["skill_id"]),
                "difficulty": module["difficulty"],
                "estimated_minutes": module.get("estimated_minutes", 20),
                "summary": module["summary"],
                "is_remediation": bool(module.get("is_remediation")),
                "xp_reward": reward_service.xp_for_difficulty(module["difficulty"]),
            }
        )
    return modules


def module_detail(module_id: str) -> Optional[dict[str, Any]]:
    module = PRACTICE_MODULE_INDEX.get(module_id)
    if not module:
        return None
    graph = get_knowledge_graph()
    visible_tests = [t for t in module.get("test_cases", []) if not t.get("hidden")]
    return {
        "id": module["id"],
        "title": module["title"],
        "kind": module["kind"],
        "practice_layer": module.get("practice_layer"),
        "technology": module["technology"],
        "language": module.get("language"),
        "skill_id": module["skill_id"],
        "skill_name": graph.name_of(module["skill_id"]),
        "difficulty": module["difficulty"],
        "estimated_minutes": module.get("estimated_minutes", 20),
        "summary": module["summary"],
        "problem_statement": module.get("problem_statement"),
        "constraints": module.get("constraints", []),
        "input_format": module.get("input_format"),
        "output_format": module.get("output_format"),
        "requirements": module.get("requirements", []),
        "examples": module.get("examples", []),
        "track": module.get("track"),
        "files": module["files"],
        "editable_files": module.get("editable_files", list(module["files"].keys())),
        "entry_file": module.get("entry_file"),
        "sample_tests": visible_tests,
        # SQL questions publish their DDL and their *visible* fixture rows, the
        # same contract the stdin/stdout judge uses: you can see what you are
        # querying, but not the datasets that grade you on Submit.
        "sql": sql_judge.public_schema(module["sql_spec"]) if module.get("sql_spec") else None,
        "hidden_test_count": _hidden_total(module),
        "xp_reward": reward_service.xp_for_difficulty(module["difficulty"]),
        "is_remediation": bool(module.get("is_remediation")),
    }


def _sql_file(module: dict[str, Any]) -> str:
    """The single editable file a SQL question is answered in."""
    return module.get("editable_files", ["query.sql"])[0]


def _merge_files(module: dict[str, Any], submitted: dict[str, str]) -> dict[str, str]:
    files = dict(module["files"])
    editable = set(module.get("editable_files", files.keys()))
    for name, content in (submitted or {}).items():
        if name in editable:
            files[name] = content
    return files


async def run_module(
    db: Session,
    user_id: str,
    module_id: str,
    files: dict[str, str],
    stdin: Optional[str] = None,
) -> dict[str, Any]:
    """The Run button: execute against visible tests only, no grading, no XP."""
    module = PRACTICE_MODULE_INDEX.get(module_id)
    if not module:
        raise KeyError(module_id)

    merged = _merge_files(module, files)

    if module["kind"] == "challenge":
        language = module["language"]
        source = merged["solution"]
        if stdin is not None:
            cases = [TestCase(name="custom input", stdin=stdin, expected_stdout="", match="trimmed")]
        else:
            cases = [
                TestCase(**t) for t in module.get("test_cases", []) if not t.get("hidden")
            ]
        service = get_code_execution_service()
        execution = await service.run(language, source, cases)
        _record_execution(db, user_id, module_id, language, source, execution)
        return {
            "kind": "challenge",
            "provider": execution.provider,
            "supported": execution.supported,
            "compile_error": execution.compile_error,
            "results": [r.model_dump() for r in execution.results],
            "passed_count": execution.passed_count,
            "total_count": execution.total_count,
            "custom_run": stdin is not None,
            "hidden_total": _hidden_total(module),
        }

    if module["kind"] == "sql":
        # Run shows only the visible fixture datasets; the hidden ones grade on
        # Submit, so a query cannot be tuned against the data that judges it.
        grade = await asyncio.to_thread(
            sql_judge.grade,
            merged[_sql_file(module)],
            module["sql_spec"],
            False,
        )
        return {
            "kind": "sql",
            "static_results": [],
            "test_results": grade.to_check_dicts(module.get("concept", "sql")),
            "preview": None,
            "hidden_total": _hidden_total(module),
        }

    # Web / JS modules: static checks give instant feedback, plus a preview bundle.
    # Run shows only the visible checks — hidden ones are graded on Submit, the
    # same contract the stdin-stdout judge uses.
    static = [
        o.to_dict()
        for o in run_static_checks(merged, module.get("checks", []), include_hidden=False)
    ]
    behaviour: list[dict[str, Any]] = []
    behaviour_spec = module.get("behaviour") or {}
    if behaviour_spec.get("assertions"):
        code_file = module.get("editable_files", ["solution.js"])[0]
        behaviour = [
            o.to_dict()
            for o in await run_behaviour_tests(
                merged.get(code_file, ""),
                behaviour_spec["assertions"],
                behaviour_spec.get("prelude", ""),
                wrap_as=behaviour_spec.get("wrap_as"),
                include_hidden=False,
            )
        ]
    return {
        "kind": "web",
        "static_results": static,
        "test_results": behaviour,
        "preview": build_preview(merged, module),
        "hidden_total": _hidden_total(module),
    }


def _hidden_total(module: dict[str, Any]) -> int:
    """How many hidden cases this module grades on Submit.

    Surfaced to the UI so a learner knows a passing Run is not the whole bar,
    without revealing anything about the cases themselves.
    """
    hidden = sum(1 for t in module.get("test_cases", []) if t.get("hidden"))
    hidden += sum(1 for c in module.get("checks", []) if c.get("hidden"))
    hidden += sum(
        1 for a in (module.get("behaviour") or {}).get("assertions", []) if a.get("hidden")
    )
    hidden += sum(
        1 for d in (module.get("sql_spec") or {}).get("datasets", []) if d.get("hidden")
    )
    return hidden


def build_preview(files: dict[str, str], module: dict[str, Any]) -> Optional[str]:
    """Inline CSS/JS into a single HTML document the browser can render in an iframe.

    Shares `render_judge.assemble_page` with the rendered grader on purpose: the
    document a learner sees in the preview is byte-for-byte the one the browser
    judge grades, so a passing preview and a passing grade cannot disagree.
    """
    return render_judge.assemble_page(files, module.get("entry_file"))


def _record_execution(
    db: Session,
    user_id: str,
    module_id: str,
    language: str,
    source: str,
    execution: ExecutionResult,
    context_type: str = "practice",
) -> None:
    db.add(
        ExecutionAttempt(
            user_id=user_id,
            context_type=context_type,
            context_id=module_id,
            language=language,
            provider=execution.provider,
            source_code=source[:20000],
            passed_count=execution.passed_count,
            total_count=execution.total_count,
            stderr=execution.combined_stderr()[:4000] or None,
            results=[r.model_dump() for r in execution.results],
        )
    )
    db.flush()


async def submit_module(
    db: Session,
    twin: LearningDigitalTwin,
    module_id: str,
    files: dict[str, str],
    duration_seconds: float = 0.0,
) -> dict[str, Any]:
    """Full graded submission: deterministic layers, then AI, then twin/XP updates."""
    module = PRACTICE_MODULE_INDEX.get(module_id)
    if not module:
        raise KeyError(module_id)

    graph = get_knowledge_graph()
    merged = _merge_files(module, files)
    skill_id = module["skill_id"]
    difficulty = module["difficulty"]

    static_results: list[dict[str, Any]] = []
    test_results: list[dict[str, Any]] = []
    error_logs: Optional[str] = None
    submission_text = "\n\n".join(
        f"// {name}\n{merged.get(name, '')}" for name in module.get("editable_files", [])
    )
    language = module.get("language", "text")

    if module["kind"] == "challenge":
        cases = [TestCase(**t) for t in module.get("test_cases", [])]
        service = get_code_execution_service()
        execution = await service.run(module["language"], merged["solution"], cases)
        _record_execution(db, twin.user_id, module_id, module["language"], merged["solution"], execution)
        error_logs = execution.combined_stderr() or None
        test_results = [
            {
                "id": r.name,
                "label": r.name,
                "passed": r.passed,
                "hidden": r.hidden,
                "concept": "edge cases" if r.hidden else None,
                "detail": r.stderr or (None if r.hidden else f"expected: {r.expected_stdout!r}, got: {r.stdout!r}"),
            }
            for r in execution.results
        ]
        deterministic_pass = execution.all_passed and execution.supported
        if not execution.supported:
            error_logs = execution.compile_error
    elif module["kind"] == "sql":
        language = "sql"
        grade = await asyncio.to_thread(
            sql_judge.grade, merged[_sql_file(module)], module["sql_spec"], True
        )
        test_results = grade.to_check_dicts(module.get("concept", "sql"))
        # A query that never ran (empty, several statements, a write) has no
        # dataset verdicts at all, so `all()` over an empty list must not pass.
        deterministic_pass = grade.passed and bool(grade.outcomes)
        if not grade.passed:
            error_logs = grade.rejection or "; ".join(
                f"{o.dataset}: {o.detail}" for o in grade.outcomes if not o.passed
            )
    else:
        static_results = [o.to_dict() for o in run_static_checks(merged, module.get("checks", []))]
        behaviour_spec = module.get("behaviour") or {}
        if behaviour_spec.get("assertions"):
            code_file = module.get("editable_files", ["solution.js"])[0]
            test_results = [
                o.to_dict()
                for o in await run_behaviour_tests(
                    merged.get(code_file, ""),
                    behaviour_spec["assertions"],
                    behaviour_spec.get("prelude", ""),
                )
            ]
        deterministic_pass = all(r["passed"] for r in static_results + test_results) and bool(
            static_results or test_results
        )

    all_checks = static_results + test_results
    failed_checks = [c for c in all_checks if not c["passed"]]

    provider = get_ai_provider()
    evaluation = await provider.evaluate(
        EvaluationRequest(
            skill_id=skill_id,
            skill_name=graph.name_of(skill_id),
            task_context=f"{module['title']}\n\n{module['summary']}",
            requirements=module.get("requirements", []),
            user_submission=submission_text,
            language=language,
            current_difficulty=difficulty,
            deterministic_results=all_checks,
            error_logs=error_logs,
        )
    )

    # Deterministic layers are authoritative for pass/fail.
    passed = deterministic_pass and evaluation.is_correct
    if not deterministic_pass:
        evaluation = EvaluationResult(**{**evaluation.model_dump(), "is_correct": False})

    xp_awarded = 0
    failure = None

    # Read before the scoring engine overwrites it (see ticket_service).
    confidence_before = twin_service.confidence_of(twin, skill_id)

    if passed:
        twin_service.record_execution_outcome(
            db, twin, skill_id, True, difficulty, module.get("remediates_concepts", [])
        )
        if module.get("secondary_skill_id"):
            twin_service.record_execution_outcome(
                db, twin, module["secondary_skill_id"], True, difficulty
            )
        xp_awarded = reward_service.xp_for_difficulty(difficulty)
        if module.get("is_remediation"):
            xp_awarded += reward_service.XP_TABLE["remediation"]
        reward_service.award_xp(
            db, twin, xp_awarded, f"Completed practice: {module['title']}", "practice", module_id
        )
        resolved = failure_analysis_service.resolve_open_analyses(
            db,
            twin.user_id,
            list(module.get("remediates_concepts", [])) + [module["skill_id"]],
        )
        twin_service.register_activity(
            db,
            twin.user_id,
            "practice_passed",
            f"Passed {module['title']}",
            f"+{xp_awarded} XP · {graph.name_of(skill_id)} confidence updated",
            {
                "module_id": module_id,
                "resolved_gaps": resolved,
                "skill_id": skill_id,
                "confidence_before": confidence_before,
                "confidence_after": twin_service.confidence_of(twin, skill_id),
            },
        )
    else:
        twin_service.record_execution_outcome(
            db, twin, skill_id, False, difficulty, evaluation.missing_concepts
        )
        analysis = failure_analysis_service.analyze_failure(
            db, twin, skill_id, "practice", module_id, evaluation, failed_checks
        )
        failure = failure_analysis_service.analysis_to_dict(analysis)
        twin_service.register_activity(
            db,
            twin.user_id,
            "practice_failed",
            f"Failed {module['title']}",
            analysis.root_cause,
            {
                "module_id": module_id,
                "failure_analysis_id": analysis.id,
                "skill_id": skill_id,
                "confidence_before": confidence_before,
                "confidence_after": twin_service.confidence_of(twin, skill_id),
            },
        )

    twin_service.touch_activity_metrics(db, twin, duration_seconds)

    attempt = PracticeAttempt(
        user_id=twin.user_id,
        module_id=module_id,
        skill_id=skill_id,
        difficulty=difficulty,
        submitted_files={k: merged.get(k, "") for k in module.get("editable_files", [])},
        passed=passed,
        static_results=static_results,
        test_results=test_results,
        ai_evaluation=evaluation.model_dump(),
        xp_awarded=xp_awarded,
        duration_seconds=duration_seconds,
        confidence_before=confidence_before,
        confidence_after=twin_service.confidence_of(twin, skill_id),
    )
    db.add(attempt)
    db.flush()

    skill = twin_service.get_or_create_skill(db, twin, skill_id)
    return {
        "attempt_id": attempt.id,
        "passed": passed,
        "static_results": static_results,
        "test_results": test_results,
        "evaluation": evaluation.model_dump(),
        "xp_awarded": xp_awarded,
        "failure_analysis": failure,
        "skill": {
            "skill_id": skill.skill_id,
            "skill_name": skill.skill_name,
            "confidence": skill.confidence,
            "verified_level": skill.verified_level,
            "breakdown": skill.score_breakdown,
        },
        "overall_confidence": twin.overall_confidence,
        "xp": twin.xp,
        "level": twin.level,
    }
