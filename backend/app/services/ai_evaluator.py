"""AI provider abstraction.

AIProvider
├── MockProvider   (deterministic, always available, no API key required)
├── OpenAIProvider
└── GeminiProvider

Every provider must return data that validates against EvaluationResult /
MentorResponse. Raw LLM output is never trusted directly: it is parsed, then
validated, and on any failure we fall back to the deterministic MockProvider so
the platform keeps working.
"""

from __future__ import annotations

import json
import logging
import re
import time
from abc import ABC, abstractmethod
from functools import lru_cache
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.schemas.ai import EvaluationRequest, EvaluationResult, MentorRequest, MentorResponse
from app.services.knowledge_graph import get_knowledge_graph

logger = logging.getLogger(__name__)

EVALUATION_SYSTEM_PROMPT = """You are SprintForge.AI's strict technical evaluator.
Judge whether the learner's submission satisfies the requirements.
Rules:
- Never reject code merely for containing comments or differing style.
- Focus on functionality, requirements coverage, correctness and edge cases.
- If deterministic test results are supplied, they are authoritative for pass/fail.
- Identify the single most important conceptual mistake, if any.
Respond ONLY with minified JSON matching this schema:
{"is_correct":bool,"conceptual_mistake":string|null,"next_difficulty":int(1-10),
"feedback":string,"missing_concepts":string[],"suggested_remediation":string|null}"""

MENTOR_BASE_PROMPT = """You are SprintForge.AI's mentor, sitting next to a learner who is
stuck on a real task. You teach; you do not hand over answers.

HARD RULES
- Never output the finished solution, and never output a code block that could be pasted in
  to make the task pass. Naming an API, a keyword, or one isolated line as an illustration is
  fine; a working implementation of the task is not.
- Be concrete. If you know which requirement is failing, talk about that exact requirement.
  Never say "re-read the acceptance criteria" as your whole answer — that is useless.
- Point at the place: the file, the function, the line, the missing branch.
- Write for a learner who may be a beginner. Short sentences, plain words, no jargon unless
  you define it in the same breath. Never more than about 90 words in `answer`.
- If the learner's question is vague, answer the most likely real problem based on the failing
  checks and their code, instead of asking them to clarify.

RESPONSE SHAPE
Respond ONLY with minified JSON:
{"answer":string,"next_step":string,"guiding_questions":string[],"concepts":string[],"reveals_solution":false}
- `answer`: the explanation, in plain language.
- `next_step`: ONE action they should take right now, phrased as an instruction. How much it
  may give away depends on the MODE below — obey the mode over this line.
- `guiding_questions`: 1-3 short questions that lead them to the insight themselves.
- `concepts`: 1-3 short concept names they should understand (e.g. "promise rejection")."""

MENTOR_MODE_PROMPTS = {
    "hint": """MODE: HINT
Give the smallest nudge that unblocks them, and no more. Name the area that is wrong and why
it matters, then stop.

Withhold the literal fix. Do not state the exact tag, element, attribute, class, function,
method, value or shape they must write, and do not enumerate the steps — any of those turns a
hint into the answer. This applies to `next_step` too: point them at where to look or what to
compare, never at what to type.
  BAD  next_step: "Replace the <div> with <main class=\\"page\\">."
  GOOD next_step: "Re-read the failing requirement and compare the element it names against
       the one wrapping your content."
The learner should still have one real decision left to make after reading you.""",
    "concept": """MODE: EXPLAIN CONCEPT
Teach the underlying idea behind this task. Start from what it is and why it exists, use one
short everyday analogy, then connect it back to their current task. Do not debug their code
line by line here — explain the idea so they can debug it themselves.""",
    "debug": """MODE: DEBUG WITH ME
Work like a debugging partner. Say what the evidence (failing checks, error output, their
code) tells you, name the most likely cause, and tell them the one thing to inspect or print
to confirm it. Prefer teaching them the diagnostic move over stating the fix.""",
}


def _question_intent(question: str) -> str:
    """Coarse intent of the learner's question, so the offline mentor can vary."""
    q = (question or "").lower()
    if re.search(r"\bwhy\b|kyun|kyu\b", q):
        return "why"
    if re.search(r"\bwhere\b|which (file|line|place)|kaha", q):
        return "where"
    if re.search(r"\bstuck\b|no idea|don'?t know|guide me|help me|samajh", q):
        return "stuck"
    if re.search(r"\bhow\b|what (tag|element|method|should)", q):
        return "how"
    return "hint"


def _affordable_tokens(body: str) -> Optional[int]:
    """Pull the output-token allowance out of a gateway's 402 body, if it states one."""
    match = re.search(r"can only afford (\d+)", body)
    return int(match.group(1)) if match else None


def _mentor_system_prompt(mode: str) -> str:
    return f"{MENTOR_BASE_PROMPT}\n\n{MENTOR_MODE_PROMPTS.get(mode, MENTOR_MODE_PROMPTS['hint'])}"


def _extract_json(text: str) -> dict[str, Any]:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    else:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            text = match.group(0)
    return json.loads(text)


class AIProvider(ABC):
    name: str = "base"

    @abstractmethod
    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult: ...

    @abstractmethod
    async def mentor(self, request: MentorRequest) -> MentorResponse: ...


class MockProvider(AIProvider):
    """Deterministic heuristic evaluator used when no LLM key is configured.

    It is intentionally rule-based rather than random so demos and tests are
    reproducible, and so failure analysis still receives real signals.
    """

    name = "mock"

    CONCEPT_HINTS: list[tuple[str, str, str]] = [
        (
            r"\bawait\b|\.then\(|Promise",
            "try",
            "async error handling",
        ),
    ]

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        failed = [r for r in request.deterministic_results if not r.get("passed", False)]
        submission = request.user_submission or ""
        missing_concepts: list[str] = []
        conceptual_mistake: Optional[str] = None

        if failed:
            first = failed[0]
            label = first.get("label") or first.get("name") or "a required check"
            conceptual_mistake = first.get("concept") or f"Requirement not satisfied: {label}"
            for item in failed:
                concept = item.get("concept")
                if concept and concept not in missing_concepts:
                    missing_concepts.append(concept)
            if not missing_concepts:
                missing_concepts.append(request.skill_name.lower())
            feedback = (
                f"{len(failed)} of {len(request.deterministic_results)} checks failed. "
                f"Start with: {label}. "
                + (first.get("hint") or "Re-read the requirement and verify your output against it.")
            )
            next_difficulty = max(1, request.current_difficulty - 1)
            return EvaluationResult(
                is_correct=False,
                conceptual_mistake=conceptual_mistake,
                next_difficulty=next_difficulty,
                feedback=feedback,
                missing_concepts=missing_concepts,
                suggested_remediation=f"Practice {missing_concepts[0]} before retrying this task.",
                provider=self.name,
            )

        if request.error_logs:
            return EvaluationResult(
                is_correct=False,
                conceptual_mistake="Runtime error before requirements could be verified.",
                next_difficulty=max(1, request.current_difficulty - 1),
                feedback=f"Your code raised an error: {request.error_logs.strip()[:400]}",
                missing_concepts=["debugging"],
                suggested_remediation="Fix the runtime error, then resubmit.",
                provider=self.name,
            )

        if not submission.strip():
            return EvaluationResult(
                is_correct=False,
                conceptual_mistake="Empty submission.",
                next_difficulty=max(1, request.current_difficulty - 1),
                feedback="Nothing was submitted. Implement the requirements in the editor first.",
                missing_concepts=[request.skill_name.lower()],
                suggested_remediation="Review the task requirements panel and write an implementation.",
                provider=self.name,
            )

        quality_notes: list[str] = []
        if len(submission.splitlines()) > 120:
            quality_notes.append("The implementation is long; consider extracting helpers.")

        return EvaluationResult(
            is_correct=True,
            conceptual_mistake=None,
            next_difficulty=min(10, request.current_difficulty + 1),
            feedback=" ".join(
                ["All requirement checks passed. Implementation satisfies the acceptance criteria."]
                + quality_notes
            ),
            missing_concepts=[],
            suggested_remediation=None,
            provider=self.name,
        )

    async def mentor(self, request: MentorRequest) -> MentorResponse:
        """Rule-based mentor used when no LLM is reachable.

        Two rules keep this honest. It only asserts things SprintForge actually
        knows — the failing requirement and the skill's own concept list from the
        knowledge graph — so it never invents domain mechanics that happen to be
        wrong for the current skill. And it reads the learner's question, so asking
        something different produces a different answer.
        """
        graph = get_knowledge_graph()
        node = graph.get(request.skill_id) if request.skill_id else None
        topic = request.skill_name or (node.name if node else None) or "this task"
        concepts = list(node.related_concepts) if node else []
        target = next((c for c in request.failing_checks if c), None)
        intent = _question_intent(request.question)

        if target:
            focus = f'The requirement still failing is: "{target}".'
            next_step = f'Make this one true, then run again: "{target}".'
        else:
            focus = "Nothing is failing right now, so take the next requirement in the list."
            next_step = "Run your code and use the first failing requirement as your target."

        questions: list[str]

        if request.mode == "concept":
            # Anchor on the skill's own concept list rather than inventing mechanics.
            if concepts:
                spine = ", ".join(concepts[:4])
                answer = (
                    f"{topic} is really about a handful of ideas: {spine}. "
                    f"This task is checking whether you can apply them for real, not just "
                    f"recognise them. {focus} Work out which of those ideas that requirement "
                    f"is testing, and the rest of the task follows."
                )
                questions = [
                    f"Which of these matters most here: {concepts[0]} or {concepts[1] if len(concepts) > 1 else 'the others'}?",
                    f"In your own words, what does {concepts[0]} mean?",
                ]
            else:
                answer = (
                    f"{topic} is best learned by stating the goal in plain words before writing "
                    f"any code. {focus} Say out loud what that requirement is asking for, then "
                    "write the smallest thing that satisfies it."
                )
                questions = [
                    "Can you restate that requirement in your own words?",
                    "What would you have to add for it to be true?",
                ]
            next_step = f"Write one sentence explaining what {topic} means here, then implement it."

        elif request.mode == "debug":
            answer = (
                f"{focus} Work backwards from that one line rather than re-reading everything. "
                "Check the thing it names actually exists and is spelled exactly as written — "
                "names, classes and ids have to match character for character. If it looks right, "
                "print or inspect it to confirm what is really there."
            )
            questions = [
                "Does the name in that requirement match your code exactly, including case?",
                "What did you expect to be there, and what is actually there?",
                "Did it ever pass, or has it failed from the start?",
            ]

        elif intent == "where":
            answer = (
                f"{focus} Look at the file you are allowed to edit and find the place that "
                "requirement is talking about. It names the thing it wants; your job is to decide "
                "where that thing belongs in the structure you already have."
            )
            questions = [
                "Which file is yours to edit in this exercise?",
                "Where in that file would this belong, and what has to contain it?",
            ]

        elif intent == "why":
            answer = (
                f"{focus} It is failing because that exact condition is not true yet — the checker "
                "looks for it literally, so a near-miss counts as a miss. Compare what the "
                f"requirement names against what your code has, one piece at a time."
            )
            questions = [
                "What exactly is the requirement looking for?",
                "Which part of it is missing from your code right now?",
            ]

        else:  # hint, including "stuck" and "how"
            answer = (
                f"{focus} Do not try to satisfy everything at once. Take that single requirement, "
                "change the smallest amount of code that could make it true, and run again. "
                "Let the result tell you whether your guess was right before you move on."
            )
            questions = [
                "What is the smallest change that could make that requirement true?",
                "Which line would you add, and what would contain it?",
            ]

        return MentorResponse(
            answer=answer,
            next_step=next_step,
            guiding_questions=questions,
            concepts=[c for c in [topic, *concepts[:2]] if c][:3],
            reveals_solution=False,
            provider=self.name,
        )


class _HTTPLLMProvider(AIProvider):
    """Shared plumbing: call the LLM, parse JSON, validate, fall back to mock."""

    # After this many consecutive failures, stop calling the provider for
    # BREAKER_COOLDOWN_SECONDS. A misconfigured or unfunded provider otherwise adds a
    # doomed round-trip to every submission; the mock fallback is used meanwhile and
    # the provider is retried automatically once the cooldown expires.
    BREAKER_THRESHOLD = 3
    BREAKER_COOLDOWN_SECONDS = 120.0

    def __init__(self) -> None:
        self._fallback = MockProvider()
        self._consecutive_failures = 0
        self._breaker_opened_at: float | None = None

    @abstractmethod
    async def _complete(self, system_prompt: str, user_prompt: str) -> str: ...

    @property
    def _breaker_open(self) -> bool:
        if self._breaker_opened_at is None:
            return False
        if time.monotonic() - self._breaker_opened_at >= self.BREAKER_COOLDOWN_SECONDS:
            self._breaker_opened_at = None
            self._consecutive_failures = 0
            logger.info("AI provider %s breaker cooled down; retrying live calls", self.name)
            return False
        return True

    def _record_success(self) -> None:
        self._consecutive_failures = 0
        self._breaker_opened_at = None

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        if self._consecutive_failures >= self.BREAKER_THRESHOLD and self._breaker_opened_at is None:
            self._breaker_opened_at = time.monotonic()
            logger.warning(
                "AI provider %s failed %d times in a row; serving mock evaluations for %.0fs",
                self.name,
                self._consecutive_failures,
                self.BREAKER_COOLDOWN_SECONDS,
            )

    async def evaluate(self, request: EvaluationRequest) -> EvaluationResult:
        # Deterministic test failures are authoritative; no need to spend a call.
        if any(not r.get("passed", False) for r in request.deterministic_results):
            return await self._fallback.evaluate(request)

        if self._breaker_open:
            result = await self._fallback.evaluate(request)
            result.provider = f"{self.name}:fallback_mock"
            return result

        user_prompt = json.dumps(
            {
                "skill": request.skill_name,
                "task_context": request.task_context,
                "requirements": request.requirements,
                "language": request.language,
                "current_difficulty": request.current_difficulty,
                "deterministic_results": request.deterministic_results,
                "error_logs": request.error_logs,
                "expected_answer": request.expected_answer,
                "submission": request.user_submission[:12000],
            }
        )
        try:
            raw = await self._complete(EVALUATION_SYSTEM_PROMPT, user_prompt)
            payload = _extract_json(raw)
            payload["provider"] = self.name
            result = EvaluationResult.model_validate(payload)
            self._record_success()
            return result
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError, ValueError) as exc:
            self._record_failure()
            logger.warning("AI provider %s evaluation failed (%s); using mock fallback", self.name, exc)
            result = await self._fallback.evaluate(request)
            result.provider = f"{self.name}:fallback_mock"
            return result

    async def mentor(self, request: MentorRequest) -> MentorResponse:
        if self._breaker_open:
            response = await self._fallback.mentor(request)
            response.provider = f"{self.name}:fallback_mock"
            return response

        user_prompt = json.dumps(
            {
                "question": request.question,
                "skill": request.skill_name or request.skill_id,
                "task_context": request.task_context,
                "mode": request.mode,
                "language": request.language,
                "currently_failing_requirements": request.failing_checks[:8],
                "conversation_so_far": [
                    {"role": t.role, "text": t.text[:600]} for t in request.history[-6:]
                ],
                "user_code": (request.user_code or "")[:8000],
            }
        )
        try:
            raw = await self._complete(_mentor_system_prompt(request.mode), user_prompt)
            payload = _extract_json(raw)
            payload["provider"] = self.name
            response = MentorResponse.model_validate(payload)
            self._record_success()
            return response
        except (httpx.HTTPError, json.JSONDecodeError, ValidationError, KeyError, ValueError) as exc:
            self._record_failure()
            logger.warning("AI provider %s mentor failed (%s); using mock fallback", self.name, exc)
            response = await self._fallback.mentor(request)
            response.provider = f"{self.name}:fallback_mock"
            return response


class OpenAIProvider(_HTTPLLMProvider):
    name = "openai"

    # Below this a structured verdict cannot be produced, so fall back instead.
    MIN_USEFUL_TOKENS = 150

    async def _complete(self, system_prompt: str, user_prompt: str) -> str:
        return await self._request(
            system_prompt, user_prompt, settings.AI_MAX_OUTPUT_TOKENS, allow_retry=True
        )

    async def _request(
        self, system_prompt: str, user_prompt: str, max_tokens: int, allow_retry: bool
    ) -> str:
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                f"{settings.OPENAI_BASE_URL.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
                json={
                    "model": settings.OPENAI_MODEL,
                    "temperature": 0.2,
                    "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                },
            )
            # Credit-metered gateways price a request against the *reserved* output
            # budget, and that allowance shrinks as the balance is spent. They tell us
            # what is affordable, so retry once inside that budget instead of failing.
            if response.status_code == 402 and allow_retry:
                affordable = _affordable_tokens(response.text)
                if affordable and affordable >= self.MIN_USEFUL_TOKENS:
                    budget = min(max_tokens, affordable - 10)
                    logger.info(
                        "AI provider %s retrying within the affordable budget (%d tokens)",
                        self.name,
                        budget,
                    )
                    return await self._request(
                        system_prompt, user_prompt, budget, allow_retry=False
                    )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]


def _gemini_text(body: dict[str, Any]) -> str:
    """Join the text parts of a Gemini candidate.

    Not just `parts[0]["text"]`: thinking models emit parts that carry only a
    thought signature, and when the reasoning consumes the whole output budget the
    candidate comes back with `finishReason: MAX_TOKENS` and no text at all. Both
    shapes must raise something legible rather than an IndexError, because the
    caller turns the message into the reason the request fell back to mock.
    """
    candidates = body.get("candidates") or []
    if not candidates:
        blocked = (body.get("promptFeedback") or {}).get("blockReason")
        raise RuntimeError(f"gemini returned no candidates (blockReason={blocked})")

    candidate = candidates[0]
    parts = (candidate.get("content") or {}).get("parts") or []
    text = "".join(str(p["text"]) for p in parts if isinstance(p, dict) and p.get("text"))
    if text.strip():
        return text

    reason = candidate.get("finishReason")
    if reason == "MAX_TOKENS":
        raise RuntimeError(
            "gemini spent the entire output budget on reasoning; "
            "raise AI_MAX_OUTPUT_TOKENS"
        )
    raise RuntimeError(f"gemini returned no text (finishReason={reason})")


class GeminiProvider(_HTTPLLMProvider):
    name = "gemini"

    async def _complete(self, system_prompt: str, user_prompt: str) -> str:
        url = (
            f"https://generativelanguage.googleapis.com/v1beta/models/"
            f"{settings.GEMINI_MODEL}:generateContent"
        )
        async with httpx.AsyncClient(timeout=settings.AI_TIMEOUT_SECONDS) as client:
            response = await client.post(
                url,
                params={"key": settings.GEMINI_API_KEY},
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                    "generationConfig": {
                        "temperature": 0.2,
                        "responseMimeType": "application/json",
                        "maxOutputTokens": settings.AI_MAX_OUTPUT_TOKENS,
                    },
                },
            )
            response.raise_for_status()
            return _gemini_text(response.json())


_PROVIDERS: dict[str, type[AIProvider]] = {
    "mock": MockProvider,
    "openai": OpenAIProvider,
    "gemini": GeminiProvider,
}


@lru_cache(maxsize=None)
def _provider_instance(key: str) -> AIProvider:
    return _PROVIDERS.get(key, MockProvider)()


def get_ai_provider() -> AIProvider:
    """Return the shared provider instance.

    Shared, not per-call: the circuit breaker keeps its failure count on the
    instance, so building a new provider for every request would reset it and the
    breaker would never trip.
    """
    return _provider_instance(settings.ai_provider_effective)
