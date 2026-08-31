"use client";

import Link from "next/link";

import { Reveal } from "@/components/motion";
import { Badge, EmptyState, PanelSkeleton, SectionTitle } from "@/components/ui/primitives";
import type { AdaptationEvent, Adaptations } from "@/lib/types";
import { cn, humanStatus, relativeTime } from "@/lib/utils";

/**
 * Per-event-type framing. `label` names the kind of event, `causal` states what
 * the engine does in response to it. Nothing here is learner data — every
 * figure, skill, ticket and reason on screen comes from the API payload.
 */
const EVENT_META: Record<
  string,
  { label: string; causal: string; tone: "accent" | "success" | "warning" | "danger" | "muted" }
> = {
  account_created: {
    label: "Account created",
    causal: "Your digital twin started empty. No skill was assumed until it had evidence.",
    tone: "muted",
  },
  onboarded: {
    label: "Goal set",
    causal:
      "Your goal and claimed skills seeded the route. Claims were recorded as unverified, so the engine plans around what it can prove rather than what was stated.",
    tone: "accent",
  },
  project_created: {
    label: "Project planned",
    causal:
      "The idea was decomposed into milestones, sprints and tickets, each targeting one skill on your route.",
    tone: "accent",
  },
  assessment_started: {
    label: "Assessment opened",
    causal: "An adaptive assessment began: question difficulty moves with each answer.",
    tone: "muted",
  },
  assessment_completed: {
    label: "Skill assessed",
    causal:
      "Assessment evidence was written into the skill's confidence score, and the route was re-ordered around the new score.",
    tone: "success",
  },
  practice_passed: {
    label: "Practice passed",
    causal:
      "Execution evidence raised this skill's confidence, which moves it up the route and can release work behind it.",
    tone: "success",
  },
  practice_failed: {
    label: "Practice failed",
    causal:
      "The evaluator diagnosed a root cause instead of just marking it wrong, and remediation was placed ahead of the blocked work.",
    tone: "danger",
  },
  ticket_started: {
    label: "Ticket started",
    causal: "Project work opened against a specific target skill, so the attempt becomes evidence.",
    tone: "accent",
  },
  ticket_completed: {
    label: "Ticket verified",
    causal:
      "A verified submission updated the target skill and re-evaluated which downstream tickets are still blocked.",
    tone: "success",
  },
  ticket_failed: {
    label: "Ticket failed review",
    causal:
      "The submission did not pass its checks. The failure was traced to concepts, not effort, and remediation was scheduled.",
    tone: "danger",
  },
};

function metaFor(event: AdaptationEvent) {
  return (
    EVENT_META[event.event_type] ?? {
      label: humanStatus(event.event_type),
      causal: "This event was recorded against your twin and taken into account when routing.",
      tone: "muted" as const,
    }
  );
}

const DOT_TONE = {
  accent: "bg-accent",
  success: "bg-success",
  warning: "bg-warning",
  danger: "bg-danger",
  muted: "bg-line-strong",
} as const;

/**
 * "How your path adapted": the audit trail of the routing engine.
 *
 * The bar for what appears here is evidence, not narrative. `unlocked_tickets`,
 * `inserted_skills`, `resolved_gaps` and `failure` are literal proof that the
 * route changed; a confidence delta is only ever drawn when the event actually
 * recorded one.
 */
export function AdaptationFeed({
  data,
  isLoading,
  errorText,
}: {
  data: Adaptations | undefined;
  isLoading: boolean;
  errorText: string | null;
}) {
  const events = data?.events ?? [];
  const unlockedCount = events.reduce((total, event) => total + event.unlocked_tickets.length, 0);
  const insertedCount = events.reduce((total, event) => total + event.inserted_skills.length, 0);
  const hasUnrecorded = events.some((event) => !event.confidence_recorded);

  return (
    <section className="panel rounded-lg" aria-label="How your path adapted">
      <div className="border-b border-line px-5 py-4">
        <SectionTitle
          className="mb-0"
          eyebrow="Deterministic routing engine · audit trail"
          title="How your path adapted"
          hint="Every change the engine made to your route, and the submission that caused it."
          action={
            <div className="flex flex-wrap items-center justify-end gap-1.5">
              {unlockedCount > 0 ? (
                <Badge tone="accent">
                  {unlockedCount} {unlockedCount === 1 ? "ticket" : "tickets"} unlocked
                </Badge>
              ) : null}
              {insertedCount > 0 ? (
                <Badge>
                  {insertedCount} {insertedCount === 1 ? "skill" : "skills"} inserted
                </Badge>
              ) : null}
              {events.length > 0 ? (
                <Badge>
                  {events.length} {events.length === 1 ? "event" : "events"}
                </Badge>
              ) : null}
            </div>
          }
        />
      </div>

      <div className="p-5">
        {isLoading ? (
          <PanelSkeleton lines={5} />
        ) : errorText ? (
          <p className="text-[12px] leading-relaxed text-warning">{errorText}</p>
        ) : events.length === 0 ? (
          <EmptyState
            eyebrow="Nothing to adapt to yet"
            title="Your route hasn't changed yet."
            description="Adaptations appear here as you get assessed and ship tickets. Each entry records what you submitted and what the engine changed because of it — so nothing is shown before there is evidence for it."
          />
        ) : (
          <>
            <ol className="space-y-0">
              {events.map((event, index) => (
                <Reveal key={event.id} as="li" delay={Math.min(index, 6) * 50}>
                  <AdaptationRow event={event} last={index === events.length - 1} />
                </Reveal>
              ))}
            </ol>

            {/*
              Where an event predates confidence capture we show no delta at all.
              The backend's own explanation is quoted so the absence is legible
              as a limit of the record rather than a missing number.
            */}
            {hasUnrecorded && data ? (
              <p className="mt-5 border-t border-line pt-4 font-mono text-[10px] leading-relaxed text-faint">
                <span className="uppercase tracking-[0.14em] text-faint">
                  confidence history —{" "}
                </span>
                {data.confidence_history_available_from}
              </p>
            ) : null}
          </>
        )}
      </div>
    </section>
  );
}

function AdaptationRow({ event, last }: { event: AdaptationEvent; last: boolean }) {
  const meta = metaFor(event);
  const resolvedGaps = event.resolved_gaps?.length ?? 0;

  return (
    <div className="relative flex gap-4 pb-6 last:pb-0">
      {/* Timeline spine */}
      <div className="relative flex flex-none flex-col items-center">
        <span className={cn("mt-[6px] h-1.5 w-1.5 rounded-full", DOT_TONE[meta.tone])} />
        {!last ? <span className="mt-1.5 w-px flex-1 bg-line" aria-hidden /> : null}
      </div>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
          <span className="label">{meta.label}</span>
          {event.skill_name ? (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
              {event.skill_name}
            </span>
          ) : null}
          <span className="ml-auto flex-none font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
            {relativeTime(event.at)}
          </span>
        </div>

        <p className="mt-1.5 text-[13.5px] font-medium leading-snug text-ink">{event.title}</p>

        {event.trigger ? (
          <p className="mt-1 max-w-[64ch] font-mono text-[11px] leading-relaxed text-muted">
            {event.trigger}
          </p>
        ) : null}

        <p className="mt-2 max-w-[68ch] text-[12px] leading-relaxed text-muted">{meta.causal}</p>

        {/* Confidence: drawn only when this event actually recorded one. */}
        {event.confidence_recorded && event.confidence_after !== null ? (
          <ConfidenceReading
            before={event.confidence_before}
            after={event.confidence_after}
            delta={event.confidence_delta}
          />
        ) : null}

        {/* The strongest evidence the route changed: work that became available. */}
        {event.unlocked_tickets.length > 0 ? (
          <div className="mt-3 border-l-2 border-accent/60 bg-accent/[0.04] px-4 py-3">
            <p className="label-accent">
              path changed · {event.unlocked_tickets.length}{" "}
              {event.unlocked_tickets.length === 1 ? "ticket" : "tickets"} unlocked
            </p>
            <ul className="mt-2 space-y-1.5">
              {event.unlocked_tickets.map((ticket) => (
                <li key={ticket.ticket_id} className="flex flex-wrap items-baseline gap-2.5">
                  <span className="font-mono text-[10.5px] text-accent">{ticket.key}</span>
                  <Link
                    href={`/workspace/${ticket.ticket_id}`}
                    className="link min-w-0 text-[12px] text-ink"
                  >
                    {ticket.title}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {/* Diagnose-and-remediate loop. */}
        {event.failure ? (
          <div className="mt-3 border-l-2 border-danger/50 pl-4">
            <p className="label">root cause</p>
            <p className="mt-1.5 max-w-[64ch] text-[12px] leading-relaxed text-ink/90">
              {event.failure.root_cause}
            </p>
            {event.failure.missing_concepts.length > 0 ? (
              <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
                {event.failure.missing_concepts.map((concept) => (
                  <Badge key={concept} tone="danger">
                    {concept}
                  </Badge>
                ))}
              </div>
            ) : null}
            {event.failure.remediation_module_id && event.failure.remediation_title ? (
              <Link
                href={`/practice/${event.failure.remediation_module_id}`}
                className="btn-ghost btn-mono mt-3 px-4 py-2"
              >
                {event.failure.remediation_title} →
              </Link>
            ) : null}
          </div>
        ) : null}

        {/* Route composition changes. */}
        {event.inserted_skills.length > 0 ? (
          <div className="mt-3">
            <p className="label">inserted into your route</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {event.inserted_skills.map((skill) => (
                <Badge key={skill.skill_id} tone="accent">
                  {skill.skill_name}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {resolvedGaps > 0 ? (
          <p className="mt-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-success">
            {resolvedGaps} {resolvedGaps === 1 ? "gap" : "gaps"} closed
          </p>
        ) : null}

        {event.weak_concepts.length > 0 ? (
          <div className="mt-3">
            <p className="label">still weak</p>
            <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
              {event.weak_concepts.map((concept) => (
                <Badge key={concept} tone="warning">
                  {concept}
                </Badge>
              ))}
            </div>
          </div>
        ) : null}

        {/* What the engine decided to do next as a result. */}
        {event.recommendation ? (
          <div className="mt-3 border-l border-line pl-4">
            <p className="label">re-routed next step</p>
            <p className="mt-1.5 text-[12.5px] text-ink">{event.recommendation.title}</p>
            <p className="mt-1 max-w-[64ch] text-[11.5px] leading-relaxed text-muted">
              {event.recommendation.reason}
            </p>
          </div>
        ) : null}
      </div>
    </div>
  );
}

/**
 * Renders exactly as much of the confidence record as the event actually holds.
 *
 * The three fields are independently nullable, so a before → after transition is
 * only drawn when both endpoints exist and the delta only when the backend
 * computed one. Anything missing is simply not shown: never zero, never
 * "no change", never inferred from the other fields.
 */
function ConfidenceReading({
  before,
  after,
  delta,
}: {
  before: number | null;
  after: number;
  delta: number | null;
}) {
  const rose = delta !== null ? delta >= 0 : before !== null ? after >= before : true;
  const tone = rose ? "text-success" : "text-danger";

  return (
    <div className="mt-3 flex flex-wrap items-baseline gap-2.5 font-mono text-[11px] tabular-nums">
      <span className="label">confidence</span>
      {before !== null ? (
        <>
          <span className="text-faint">{before.toFixed(0)}%</span>
          <span className="text-line-strong" aria-hidden>
            →
          </span>
          <span className={tone}>{after.toFixed(0)}%</span>
        </>
      ) : (
        <>
          <span className="text-faint">recorded at</span>
          <span className="text-ink">{after.toFixed(0)}%</span>
        </>
      )}
      {delta !== null ? (
        <span className={cn("text-[10.5px]", tone)}>
          {delta > 0 ? "+" : ""}
          {delta.toFixed(1)}
        </span>
      ) : null}
    </div>
  );
}
