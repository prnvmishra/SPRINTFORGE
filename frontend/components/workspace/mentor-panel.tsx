"use client";

import { memo, useEffect, useRef, useState } from "react";

import { Alert, Badge, Loader } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { MentorResponse } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

const MODES = [
  {
    id: "hint",
    label: "Hint",
    blurb: "The smallest nudge to get unstuck — no answers.",
  },
  {
    id: "concept",
    label: "Concept",
    blurb: "Teach me the idea behind this task in plain words.",
  },
  {
    id: "debug",
    label: "Debug",
    blurb: "Look at my code and tell me what to check first.",
  },
] as const;

type Mode = (typeof MODES)[number]["id"];

type Turn =
  | { role: "user"; text: string }
  | { role: "mentor"; text: string; reply: MentorResponse };

function MentorPanelImpl({
  skillId,
  skillName,
  ticketId,
  moduleId,
  code,
  getCode,
  failingChecks = [],
}: {
  skillId?: string;
  skillName?: string;
  ticketId?: string;
  moduleId?: string;
  code?: string;
  /**
   * Reads the current editor buffer at send time. Preferred over `code`, which
   * would force this panel to re-render on every keystroke.
   */
  getCode?: () => string;
  /** Labels of checks currently failing, so the mentor can be specific. */
  failingChecks?: string[];
}) {
  const [mode, setMode] = useState<Mode>("hint");
  const [question, setQuestion] = useState("");
  const [turns, setTurns] = useState<Turn[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const threadEnd = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    threadEnd.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, busy]);

  // Offer the questions a stuck learner would actually want to ask, built from the
  // check that is actually failing rather than generic prompts.
  const suggestions = (() => {
    const target = failingChecks[0];
    const items: string[] = [];
    if (target) {
      items.push(`Why is "${trim(target)}" still failing?`);
      items.push(`What do I need to add to satisfy "${trim(target)}"?`);
    }
    if (skillName) items.push(`Explain ${skillName} simply`);
    items.push("I'm stuck — where do I start?");
    return items.slice(0, 4);
  })();

  async function ask(raw?: string) {
    const text =
      (raw ?? question).trim() || "I am stuck on this task. Where should I look first?";
    setBusy(true);
    setError(null);
    setQuestion("");
    const priorTurns = turns;
    setTurns((current) => [...current, { role: "user", text }]);
    try {
      const reply = await api<MentorResponse>("/ai/mentor", {
        method: "POST",
        body: {
          question: text,
          skill_id: skillId,
          ticket_id: ticketId,
          module_id: moduleId,
          user_code: getCode ? getCode() : code,
          mode,
          failing_checks: failingChecks,
          history: priorTurns.map((t) => ({ role: t.role, text: t.text })),
        },
      });
      setTurns((current) => [...current, { role: "mentor", text: reply.answer, reply }]);
    } catch (askError) {
      setError(errorMessage(askError));
    } finally {
      setBusy(false);
    }
  }

  const activeMode = MODES.find((m) => m.id === mode)!;

  return (
    <div className="flex h-full flex-col gap-4">
      {/* Mode selector: a segmented control, not three buttons */}
      <div>
        <div className="flex gap-px overflow-hidden rounded border border-line bg-line">
          {MODES.map((option) => (
            <button
              key={option.id}
              onClick={() => setMode(option.id)}
              aria-pressed={mode === option.id}
              className={cn("seg py-2", mode === option.id ? "seg-on" : "seg-off")}
            >
              {option.label}
            </button>
          ))}
        </div>
        <p className="mt-2 text-[11px] leading-relaxed text-faint">{activeMode.blurb}</p>
      </div>

      {/* Conversation */}
      {turns.length > 0 ? (
        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto pr-1">
          {turns.map((turn, index) =>
            turn.role === "user" ? (
              <div key={index} className="flex justify-end">
                <p className="max-w-[88%] rounded rounded-br-none border border-accent/25 bg-accent/[0.08] px-3 py-2 text-[11.5px] leading-relaxed text-ink">
                  {turn.text}
                </p>
              </div>
            ) : (
              <MentorBubble key={index} reply={turn.reply} onAsk={(q) => void ask(q)} />
            ),
          )}
          {busy ? <Loader label="Mentor reasoning" /> : null}
          <div ref={threadEnd} />
        </div>
      ) : (
        <div className="min-h-0 flex-1 border-l-2 border-line pl-3">
          <p className="text-[11.5px] leading-relaxed text-muted">
            Ask anything about this task. The mentor explains and points you in the right
            direction — it will never write the answer for you.
          </p>
          {failingChecks.length > 0 ? (
            <p className="mt-3 font-mono text-[10px] uppercase tracking-[0.1em] text-warning">
              {failingChecks.length} check{failingChecks.length > 1 ? "s" : ""} failing · it can
              see them
            </p>
          ) : null}
        </div>
      )}

      {/* Suggested questions */}
      {!busy ? (
        <div className="flex flex-wrap gap-1.5">
          {suggestions.map((item) => (
            <button
              key={item}
              onClick={() => void ask(item)}
              className="rounded border border-line px-2.5 py-1 text-left text-[10.5px] text-muted transition-colors hover:border-accent/40 hover:text-ink"
            >
              {item}
            </button>
          ))}
        </div>
      ) : null}

      {error ? <Alert tone="danger">{error}</Alert> : null}

      {/* Composer */}
      <div className="flex-none space-y-2">
        <textarea
          className="input min-h-[56px] text-[12px]"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              void ask();
            }
          }}
          placeholder="Ask a question… (⌘/Ctrl + Enter)"
        />
        <div className="flex items-center gap-2">
          <button
            onClick={() => void ask()}
            className="btn-subtle btn-mono flex-1 py-2"
            disabled={busy}
          >
            {busy ? "Thinking…" : "Ask mentor →"}
          </button>
          {turns.length > 0 ? (
            <button
              onClick={() => setTurns([])}
              className="btn-ghost btn-mono px-3 py-2"
            >
              Clear
            </button>
          ) : null}
        </div>
      </div>
    </div>
  );
}

function MentorBubble({
  reply,
  onAsk,
}: {
  reply: MentorResponse;
  onAsk: (question: string) => void;
}) {
  return (
    <div className="animate-reveal space-y-3 border-l-2 border-accent/40 pl-3">
      <p className="text-[11.5px] leading-[1.7] text-ink">{reply.answer}</p>

      {reply.next_step ? (
        <div className="rounded border border-accent/25 bg-accent/[0.06] p-2.5">
          <p className="label-accent mb-1">Do this next</p>
          <p className="text-[11px] leading-relaxed text-ink">{reply.next_step}</p>
        </div>
      ) : null}

      {reply.guiding_questions.length > 0 ? (
        <div>
          <p className="label mb-1.5">Think about</p>
          <ul className="space-y-1">
            {reply.guiding_questions.map((item) => (
              <li key={item}>
                <button
                  onClick={() => onAsk(item)}
                  className="flex gap-2 text-left text-[11px] leading-relaxed text-muted transition-colors hover:text-ink"
                  title="Ask the mentor this"
                >
                  <span className="text-accent">→</span>
                  {item}
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      {reply.concepts.length > 0 ? (
        <div className="flex flex-wrap items-center gap-1.5">
          {reply.concepts.map((concept) => (
            <Badge key={concept}>{concept}</Badge>
          ))}
        </div>
      ) : null}
    </div>
  );
}

function trim(text: string, max = 42) {
  return text.length > max ? `${text.slice(0, max).trimEnd()}…` : text;
}

/**
 * Memoised so workspace re-renders (status changes, check results, tab switches)
 * do not re-render the conversation. `failingChecks` is rebuilt each render, so
 * it is compared by content rather than identity.
 */
export const MentorPanel = memo(MentorPanelImpl, (prev, next) => {
  return (
    prev.skillId === next.skillId &&
    prev.skillName === next.skillName &&
    prev.ticketId === next.ticketId &&
    prev.moduleId === next.moduleId &&
    prev.code === next.code &&
    prev.getCode === next.getCode &&
    (prev.failingChecks ?? []).join("\u0000") === (next.failingChecks ?? []).join("\u0000")
  );
});
