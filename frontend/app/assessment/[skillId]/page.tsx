"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useCallback, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Counter, GrowBar } from "@/components/motion";
import { Alert, Badge, Loader, Panel, SectionTitle } from "@/components/ui/primitives";
import { CodeEditor } from "@/components/workspace/code-editor";
import { api } from "@/lib/api";
import type { AssessmentState, AssessmentSubmitResponse, DigitalTwin } from "@/lib/types";
import { cn, difficultyLabel, errorMessage } from "@/lib/utils";

const TYPE_LABEL: Record<string, string> = {
  mcq: "Multiple choice",
  output_prediction: "Predict the output",
  code_debug: "Debug the code",
  code_completion: "Complete the code",
  scenario: "Scenario reasoning",
};

/** Grading bands the engine actually uses, surfaced before the first question. */
const BANDS = [
  { level: "advanced", rule: "85%+ and a level 6 item passed" },
  { level: "intermediate", rule: "60% or more" },
  { level: "beginner", rule: "35% or more" },
  { level: "needs improvement", rule: "under 35%" },
];

export default function AssessmentSessionPage() {
  return (
    <Suspense
      fallback={
        <AppShell>
          <div className="grid min-h-[50vh] place-items-center">
            <Loader label="Loading" />
          </div>
        </AppShell>
      }
    >
      <AssessmentSession />
    </Suspense>
  );
}

function AssessmentSession() {
  const params = useParams<{ skillId: string }>();
  const searchParams = useSearchParams();
  const router = useRouter();
  const queryClient = useQueryClient();
  const skillId = params.skillId;
  const isPlacement = searchParams.get("placement") === "1";

  const [state, setState] = useState<AssessmentState | null>(null);
  const [answer, setAnswer] = useState("");
  const [choice, setChoice] = useState<number | null>(null);
  const [lastResponse, setLastResponse] = useState<AssessmentSubmitResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [starting, setStarting] = useState(false);
  const startedAt = useRef<number>(Date.now());
  const claimedLevel = useRef<string | null>(null);

  const skills = useQuery({
    queryKey: ["assessable-skills"],
    queryFn: () =>
      api<{
        skills: {
          skill_id: string;
          skill_name: string;
          item_count: number;
          difficulty_range: [number, number];
        }[];
      }>("/assessment/skills"),
  });
  const skillMeta = skills.data?.skills.find((s) => s.skill_id === skillId);

  const twin = useQuery({
    queryKey: ["digital-twin"],
    queryFn: () => api<DigitalTwin>("/profile/digital-twin"),
  });

  // The session is no longer started on mount. A graded check that begins before
  // the learner has read what is being graded is the thing they asked us to fix.
  const begin = useCallback(async () => {
    setStarting(true);
    setError(null);
    try {
      const profile = twin.data ?? (await api<DigitalTwin>("/profile/digital-twin"));
      claimedLevel.current = profile.claimed_skills?.[skillId] ?? profile.experience_level ?? null;
      const session = await api<AssessmentState>("/assessment/start", {
        method: "POST",
        body: {
          skill_id: skillId,
          claimed_level: claimedLevel.current,
          max_questions: 5,
          placement: isPlacement,
        },
      });
      setState(session);
      startedAt.current = Date.now();
    } catch (startError) {
      setError(errorMessage(startError));
    } finally {
      setStarting(false);
    }
  }, [isPlacement, skillId, twin.data]);

  async function submitAnswer() {
    if (!state?.question) return;
    const value = state.question.type === "mcq" ? String(choice ?? "") : answer;
    if (!value.trim()) {
      setError("Provide an answer before submitting.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await api<AssessmentSubmitResponse>("/assessment/submit", {
        method: "POST",
        body: {
          session_id: state.session_id,
          question_id: state.question.id,
          answer: value,
          duration_seconds: (Date.now() - startedAt.current) / 1000,
        },
      });
      setLastResponse(response);
      setState(response.state);
      setAnswer("");
      setChoice(null);
      startedAt.current = Date.now();
      await queryClient.invalidateQueries();
    } catch (submitError) {
      setError(errorMessage(submitError));
    } finally {
      setBusy(false);
    }
  }

  // ------------------------------------------------------------- pre-flight
  if (!state) {
    const questionCount = isPlacement ? 3 : 5;
    return (
      <AppShell>
        <div className="mx-auto max-w-[760px]">
          <p className="label">{isPlacement ? "Placement check" : "Adaptive verification"}</p>
          <h1 className="display mt-2 text-display-sm capitalize text-ink">
            {skillMeta?.skill_name ?? skillId.replace(/_/g, " ")}
          </h1>
          <p className="mt-4 max-w-[60ch] text-[13px] leading-[1.7] text-muted">
            {isPlacement
              ? "A short check so we can tell whether you can skip the course this skill sits at the top of. There is no penalty for a low score — it just changes where you start."
              : "Answers are graded on the server and go straight into your Digital Twin. Read what is being measured before you begin."}
          </p>

          <Panel className="mt-8" inset={false}>
            <div className="border-b border-line px-5 py-4">
              <SectionTitle
                className="mb-0"
                eyebrow="Before you start"
                title="How this is scored"
              />
            </div>
            <div className="grid gap-px bg-line sm:grid-cols-3">
              <Stat label="Questions" value={`${questionCount} max`} />
              <Stat
                label="Difficulty"
                value={
                  skillMeta
                    ? `L${skillMeta.difficulty_range[0]}–L${skillMeta.difficulty_range[1]}`
                    : "adaptive"
                }
              />
              <Stat
                label="Verified at"
                value="65% confidence"
                accent
              />
            </div>
            <div className="space-y-5 p-5">
              <div>
                <p className="label mb-2.5">Your result band</p>
                <ul className="divide-y divide-line/60">
                  {BANDS.map((band) => (
                    <li
                      key={band.level}
                      className="flex items-baseline justify-between gap-3 py-2 first:pt-0"
                    >
                      <span className="text-[12px] capitalize text-ink">{band.level}</span>
                      <span className="flex-none font-mono text-[10.5px] text-faint">
                        {band.rule}
                      </span>
                    </li>
                  ))}
                </ul>
              </div>
              <ul className="space-y-2 text-[11.5px] leading-relaxed text-muted">
                <li>
                  Difficulty moves up when you are right and down when you are wrong, so the score
                  reflects the hardest level you actually held.
                </li>
                <li>
                  A miss at your frontier triggers one easier follow-up on the same concept — that
                  is how the exact gap gets named instead of guessed.
                </li>
                <li>
                  Accuracy alone does not verify a skill. Confidence is difficulty-weighted, and
                  writing working code raises it faster than answering questions.
                </li>
              </ul>
            </div>
            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-4">
              <Link
                href={isPlacement ? "/placement" : "/assessment"}
                className="btn-ghost btn-mono px-4 py-2"
              >
                ← Back
              </Link>
              <button
                onClick={() => void begin()}
                className="btn-primary btn-mono px-5 py-2.5"
                disabled={starting}
                type="button"
              >
                {starting ? <Loader label="Selecting your first item" /> : <>Begin →</>}
              </button>
            </div>
          </Panel>

          {error ? (
            <div className="mt-6">
              <Alert tone="danger" title="Could not start the assessment">
                {error}
              </Alert>
            </div>
          ) : null}
        </div>
      </AppShell>
    );
  }

  const result = state.result;
  const question = state.question;
  const progress = (state.questions_asked / state.max_questions) * 100;

  return (
    <AppShell>
      <div className="mx-auto max-w-[820px]">
        {/* ------------------------------------------------- session header */}
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div className="min-w-0">
            <p className="label">Adaptive verification</p>
            <h1 className="display mt-2 text-display-sm capitalize text-ink">
              {result?.skill_name ?? skillId.replace(/_/g, " ")}
            </h1>
          </div>
          <div className="flex items-center gap-5 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
            <span>
              item <span className="text-ink">{state.questions_asked}</span>/{state.max_questions}
            </span>
            <span>
              difficulty <span className="text-accent">{state.current_difficulty}</span>/10
            </span>
            <span>
              correct <span className="text-success">{state.correct_count}</span>
            </span>
          </div>
        </div>

        {/* Progress: segmented, one cell per item, so position is legible */}
        <div className="mt-4 flex gap-1">
          {Array.from({ length: state.max_questions }).map((_, index) => (
            <span
              key={index}
              className={cn(
                "h-[3px] flex-1 transition-colors duration-500",
                index < state.questions_asked ? "bg-accent" : "bg-elevated",
              )}
            />
          ))}
        </div>
        <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
          {progress.toFixed(0)}% of this session
        </p>

        {/* --------------------------------------------- last item verdict */}
        {lastResponse ? (
          <div className="mt-6 animate-reveal">
            <div
              className={cn(
                "overflow-hidden rounded border",
                lastResponse.is_correct
                  ? "border-success/30 bg-success/[0.05]"
                  : "border-warning/30 bg-warning/[0.05]",
              )}
            >
              <div className="flex flex-wrap items-center gap-3 border-b border-line/60 px-4 py-2.5">
                <span
                  className={cn(
                    "font-mono text-[10px] uppercase tracking-[0.14em]",
                    lastResponse.is_correct ? "text-success" : "text-warning",
                  )}
                >
                  {lastResponse.is_correct ? "correct" : "not quite"}
                </span>
                <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
                  next difficulty {lastResponse.evaluation.next_difficulty}/10
                </span>
                <span className="ml-auto font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
                  evaluated by {lastResponse.evaluation.provider}
                </span>
              </div>
              <div className="px-4 py-3.5">
                <p className="text-[12.5px] leading-relaxed text-ink/90">
                  {lastResponse.evaluation.feedback}
                </p>
                {lastResponse.evaluation.conceptual_mistake ? (
                  <p className="mt-2.5 border-l-2 border-danger/50 pl-3 text-[12px] leading-relaxed text-muted">
                    <span className="label mr-1.5 text-danger">gap</span>
                    {lastResponse.evaluation.conceptual_mistake}
                  </p>
                ) : null}
                <div className="mt-3.5">
                  <div className="mb-1.5 flex items-baseline justify-between">
                    <span className="label">confidence</span>
                    <span className="font-mono text-[11px] tabular-nums text-ink">
                      {lastResponse.skill.confidence.toFixed(0)}%
                    </span>
                  </div>
                  <GrowBar
                    value={lastResponse.skill.confidence}
                    tone={lastResponse.is_correct ? "success" : "warning"}
                  />
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {/* --------------------------------------------------- current item */}
        {question ? (
          <Panel className="mt-6" inset={false}>
            <div className="flex flex-wrap items-center gap-1.5 border-b border-line px-5 py-3.5">
              <Badge tone="accent">{TYPE_LABEL[question.type] ?? question.type}</Badge>
              <Badge>
                {difficultyLabel(question.difficulty)} L{question.difficulty}
              </Badge>
              {question.concept ? <Badge>{question.concept}</Badge> : null}
              {question.skill_id !== skillId ? (
                <Badge tone="warning">diagnostic · prerequisite</Badge>
              ) : null}
            </div>

            <div className="p-5">
              <p className="whitespace-pre-wrap text-[14px] leading-[1.65] text-ink">
                {question.prompt}
              </p>

              {question.code ? (
                <pre className="mt-4 overflow-x-auto rounded border border-line bg-canvas p-4 font-mono text-[11.5px] leading-[1.75] text-ink">
                  {question.code}
                </pre>
              ) : null}

              {question.type === "mcq" && question.options ? (
                <div className="mt-5 space-y-px">
                  {question.options.map((option, index) => (
                    <button
                      key={option}
                      onClick={() => setChoice(index)}
                      aria-pressed={choice === index}
                      className={cn(
                        "flex w-full items-start gap-3.5 border-l-2 px-4 py-3 text-left transition-colors duration-200",
                        choice === index
                          ? "border-accent bg-accent/[0.07]"
                          : "border-line hover:border-line-strong hover:bg-elevated",
                      )}
                    >
                      <span
                        className={cn(
                          "font-mono text-[11px]",
                          choice === index ? "text-accent" : "text-faint",
                        )}
                      >
                        {String.fromCharCode(65 + index)}
                      </span>
                      <span
                        className={cn(
                          "font-mono text-[12px] leading-relaxed",
                          choice === index ? "text-ink" : "text-muted",
                        )}
                      >
                        {option}
                      </span>
                    </button>
                  ))}
                </div>
              ) : question.type === "scenario" ? (
                <textarea
                  className="input mt-5 min-h-[150px] font-sans leading-relaxed"
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  placeholder="Explain the root cause and how you would fix it…"
                />
              ) : (
                <div className="mt-5 h-56 overflow-hidden rounded border border-line">
                  <CodeEditor
                    path={`assessment/${question.id}`}
                    value={answer}
                    language={question.language === "javascript" ? "javascript" : "plaintext"}
                    onChange={setAnswer}
                  />
                </div>
              )}

              {error ? (
                <div className="mt-4">
                  <Alert tone="danger">{error}</Alert>
                </div>
              ) : null}
            </div>

            <div className="flex flex-wrap items-center justify-between gap-3 border-t border-line px-5 py-3.5">
              <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                graded server-side · your client never decides correctness
              </p>
              <button
                onClick={() => void submitAnswer()}
                className="btn-primary btn-mono px-5 py-2.5"
                disabled={busy}
              >
                {busy ? <Loader label="Evaluating" /> : <>Submit answer →</>}
              </button>
            </div>
          </Panel>
        ) : result ? (
          /* ------------------------------------------------ final result */
          <div className="mt-6 space-y-6">
            <Panel inset={false}>
              <div className="border-b border-line px-5 py-4">
                <SectionTitle
                  className="mb-0"
                  eyebrow="Session complete"
                  title="Verification result"
                  hint="Claimed level versus what you demonstrated"
                />
              </div>

              <div className="grid gap-px bg-line sm:grid-cols-3">
                <Stat label="Claimed" value={result.claimed_level ?? "unspecified"} />
                <Stat label="Verified" value={result.verified_level.replace(/_/g, " ")} accent />
                <Stat label="Accuracy" value={`${result.accuracy}%`} numeric={result.accuracy} />
              </div>

              <div className="space-y-6 p-5">
                {!result.claim_matches_reality ? (
                  <Alert tone="warning" title="Claim did not match performance">
                    You claimed <span className="text-ink">{result.claimed_level}</span> but
                    demonstrated{" "}
                    <span className="text-ink">{result.verified_level.replace(/_/g, " ")}</span>{" "}
                    across {result.questions_answered} adaptive items — hardest passed level{" "}
                    {result.hardest_difficulty_passed}. Your Digital Twin now reflects the
                    evidence, not the claim.
                  </Alert>
                ) : null}

                {result.weak_concepts.length > 0 ? (
                  <div>
                    <p className="label mb-2.5">Conceptual gaps detected</p>
                    <div className="flex flex-wrap gap-1.5">
                      {result.weak_concepts.map((concept) => (
                        <Badge key={concept} tone="danger">
                          {concept}
                        </Badge>
                      ))}
                    </div>
                  </div>
                ) : null}

                {/* The adaptive path: how difficulty moved with each answer */}
                <div>
                  <p className="label mb-3">Adaptive path</p>
                  <ul className="space-y-px">
                    {result.timeline.map((entry, index) => (
                      <li
                        key={`${entry.question_id}-${index}`}
                        className={cn(
                          "flex items-center gap-3 border-l-2 py-2 pl-3",
                          entry.is_correct ? "border-success/40" : "border-danger/40",
                        )}
                      >
                        <span
                          className={cn(
                            "font-mono text-[10px]",
                            entry.is_correct ? "text-success" : "text-danger",
                          )}
                        >
                          {entry.is_correct ? "✓" : "✕"}
                        </span>
                        <span className="font-mono text-[10px] tabular-nums text-faint">
                          L{entry.difficulty}
                        </span>
                        <span className="min-w-0 flex-1 truncate text-[11.5px] text-muted">
                          {entry.concept ?? entry.question_id}
                        </span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              <div className="flex flex-wrap gap-2 border-t border-line px-5 py-4">
                {isPlacement ? (
                  <Link href="/placement" className="btn-primary btn-mono px-4 py-2">
                    Back to placement →
                  </Link>
                ) : (
                  <Link href="/profile" className="btn-primary btn-mono px-4 py-2">
                    See updated twin →
                  </Link>
                )}
                <Link href="/assessment" className="btn-ghost btn-mono px-4 py-2">
                  Verify another skill
                </Link>
                <button
                  onClick={() => router.refresh()}
                  className="btn-ghost btn-mono px-4 py-2"
                  type="button"
                >
                  Refresh
                </button>
              </div>
            </Panel>
          </div>
        ) : null}
      </div>
    </AppShell>
  );
}

function Stat({
  label,
  value,
  accent = false,
  numeric,
}: {
  label: string;
  value: string;
  accent?: boolean;
  numeric?: number;
}) {
  return (
    <div className="bg-surface p-5">
      <p className="label">{label}</p>
      <p
        className={cn(
          "display mt-2 text-[22px] capitalize tracking-tight",
          accent ? "text-accent" : "text-ink",
        )}
      >
        {numeric !== undefined ? (
          <>
            <Counter value={numeric} />%
          </>
        ) : (
          value
        )}
      </p>
    </div>
  );
}
