"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { GrowBar } from "@/components/motion";
import { api } from "@/lib/api";
import type {
  LearningPath,
  LearningPathStep,
  LearningResource,
  SkillResources,
} from "@/lib/types";
import { cn, confidenceTone } from "@/lib/utils";

/**
 * Route context for the two coding workspaces.
 *
 * Everything here is read straight off `/learning-path` and `/resources/{skill}`.
 * When the skill being practised is not on the learner's route there is nothing
 * truthful to say, so the block renders nothing rather than a generic banner.
 */

export type PathContext = {
  path: LearningPath;
  step: LearningPathStep;
  threshold: number;
  /** The routing reason, only when the engine's current pick is this skill. */
  reason: { text: string; deterministic: boolean } | null;
};

/**
 * Secondary and non-blocking: a failure leaves the workspace untouched and
 * silent, which is why it never retries and never surfaces an error.
 */
export function usePathContext(skillId: string | undefined | null): PathContext | null {
  const query = useQuery({
    queryKey: ["learning-path"],
    queryFn: () => api<LearningPath>("/learning-path"),
    retry: false,
    staleTime: 60_000,
  });

  const path = query.data;
  if (!path || !skillId) return null;

  const step = path.path.find((item) => item.skill_id === skillId);
  if (!step) return null;

  const action = path.next_action;
  const reason =
    action && action.skill_id === step.skill_id && action.reason
      ? {
          text: action.reason,
          deterministic: action.reason_source === "deterministic_routing_engine",
        }
      : null;

  return { path, step, threshold: path.confidence_threshold, reason };
}

/** Returns null when the payload lacks the id or url the target needs. */
function resourceHref(resource: LearningResource): string | null {
  switch (resource.target) {
    case "practice_module":
      return resource.module_id ? `/practice/${resource.module_id}` : null;
    case "assessment":
      return resource.skill_id ? `/assessment/${resource.skill_id}` : null;
    case "course":
      return resource.path_id && resource.course_id
        ? `/paths/${resource.path_id}/courses/${resource.course_id}`
        : null;
    case "external":
      return resource.url;
    default:
      return null;
  }
}

function stateLabel(step: LearningPathStep): { text: string; className: string } {
  if (step.verified) return { text: "verified", className: "border-success/25 text-success" };
  if (!step.unlocked) return { text: "locked", className: "border-line text-faint" };
  if (step.is_next) return { text: "engine's next pick", className: "border-accent/25 text-accent" };
  return { text: step.state.replace(/_/g, " "), className: "border-line text-muted" };
}

/** Resolves a skill id to its name using the route, falling back to the raw id. */
function skillLabel(path: LearningPath, skillId: string): string {
  return path.path.find((item) => item.skill_id === skillId)?.skill_name ?? skillId;
}

/* -------------------------------------------------------------------------- */
/*  Workspace block                                                            */
/* -------------------------------------------------------------------------- */

/**
 * Compact "why am I here" block for a workspace brief.
 *
 * Deliberately dense and hairline-separated: it sits above a task brief in a
 * narrow rail and must never compete with the editor.
 */
export function PathContextPanel({
  skillId,
  className,
  objective,
}: {
  skillId: string | undefined | null;
  className?: string;
  /** Extra, workspace-specific lines rendered under the route position. */
  objective?: React.ReactNode;
}) {
  const context = usePathContext(skillId);
  if (!context) return null;

  const { path, step, threshold, reason } = context;
  const tone = confidenceTone(step.confidence, threshold);
  const state = stateLabel(step);
  const remaining = Math.max(0, threshold - step.confidence);

  return (
    <section
      className={cn(
        "relative overflow-hidden border border-line bg-elevated/40 px-3.5 py-3",
        className,
      )}
    >
      <span className="absolute inset-y-0 left-0 w-[2px] bg-accent/70" aria-hidden />

      <div className="flex flex-wrap items-center gap-x-2.5 gap-y-1">
        <p className="label">Why this task</p>
        <span className="hidden h-px flex-1 bg-line sm:block" />
        <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] tabular-nums text-faint">
          step {step.order}/{path.path.length}
        </span>
        <span
          className={cn(
            "rounded border px-1.5 py-px font-mono text-[9px] uppercase tracking-[0.1em]",
            state.className,
          )}
        >
          {state.text}
        </span>
      </div>

      {/* ------------------------------------------------ skill vs threshold */}
      <div className="mt-2.5">
        <div className="flex items-baseline justify-between gap-3">
          <span className="min-w-0 truncate text-[12px] text-ink">{step.skill_name}</span>
          <span
            className={cn(
              "flex-none whitespace-nowrap font-mono text-[11px] tabular-nums",
              tone.text,
            )}
          >
            {step.confidence.toFixed(0)}%
            <span className="text-faint"> / {threshold.toFixed(0)}%</span>
          </span>
        </div>
        <GrowBar
          value={step.confidence}
          threshold={threshold}
          tone={tone.tone}
          className="mt-1.5"
        />
        <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
          {step.verified
            ? "verified · further evidence keeps it current"
            : `${remaining.toFixed(0)} points of evidence below the verified line`}
        </p>
      </div>

      {/* -------------------------------------------------------- the reason */}
      {reason ? (
        <div className="mt-3 border-t border-line/70 pt-2.5">
          <p className="text-[11.5px] leading-[1.65] text-muted">{reason.text}</p>
          <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
            {reason.deterministic
              ? "routed by the deterministic engine · rule-based, not model-generated"
              : `reason source · ${path.next_action?.reason_source}`}
          </p>
        </div>
      ) : null}

      {/* ------------------------------------------------------ goal + route */}
      <dl className="mt-3 space-y-1.5 border-t border-line/70 pt-2.5">
        {path.goal.goal ? (
          <ContextLine term="goal">{path.goal.goal}</ContextLine>
        ) : null}

        {step.prerequisites.length > 0 ? (
          <ContextLine term="after">
            {step.prerequisites.map((id) => skillLabel(path, id)).join(" · ")}
          </ContextLine>
        ) : null}

        {step.unlocks.length > 0 ? (
          <ContextLine term="unlocks">
            {step.unlocks.map((id) => skillLabel(path, id)).join(" · ")}
          </ContextLine>
        ) : null}

        {step.weak_concepts.length > 0 ? (
          <ContextLine term="weak">{step.weak_concepts.join(" · ")}</ContextLine>
        ) : null}

        {objective}
      </dl>

      {/* --------------------------------------------- prerequisites / after */}
      {!step.unlocked && step.missing_prerequisites.length > 0 ? (
        <p className="mt-3 border-t border-line/70 pt-2.5 text-[11px] leading-relaxed text-warning/90">
          Locked on the route until{" "}
          {step.missing_prerequisites
            .map((gap) => `${gap.skill_name} ${gap.confidence.toFixed(0)}%→${gap.required.toFixed(0)}%`)
            .join(", ")}
          .
        </p>
      ) : (
        <p className="mt-3 border-t border-line/70 pt-2.5 text-[11px] leading-relaxed text-faint">
          Passing here files execution evidence against{" "}
          <span className="text-muted">{step.skill_name}</span> and recomputes its confidence.
          {step.verified
            ? " It is already verified, so this keeps the score current."
            : ` At ${threshold.toFixed(0)}% it verifies${
                step.unlocks.length > 0
                  ? ` and opens ${step.unlocks.map((id) => skillLabel(path, id)).join(", ")}`
                  : ""
              }.`}
        </p>
      )}

      <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1">
        <Link href="/path" className="link font-mono text-[10px] uppercase tracking-[0.1em]">
          See full route
        </Link>
        <ReadUpFirst skillId={step.skill_id} />
      </div>
    </section>
  );
}

/** A term/value line inside the context block. Exported for workspace-specific rows. */
export function ContextLine({ term, children }: { term: string; children: React.ReactNode }) {
  return (
    /*
      Stacked below `sm`, and side by side only where the label column is wide
      enough to hold the longest term. A fixed 52px column silently overflowed
      on "unlocks" and "objective", printing the label on top of its own value.
    */
    <div className="sm:flex sm:gap-2.5">
      <dt className="font-mono text-[9.5px] uppercase leading-[1.7] tracking-[0.1em] text-faint sm:w-[68px] sm:flex-none sm:break-words">
        {term}
      </dt>
      <dd className="min-w-0 text-[11px] leading-[1.55] text-muted sm:flex-1">{children}</dd>
    </div>
  );
}

/**
 * A short "read up first" affordance.
 *
 * Collapsed by default and only fetched when opened, so the workspace never
 * turns into a catalogue and never pays for a request nobody asked for.
 */
function ReadUpFirst({ skillId }: { skillId: string }) {
  const [open, setOpen] = useState(false);

  const query = useQuery({
    queryKey: ["resources", skillId],
    queryFn: () => api<SkillResources>(`/resources/${skillId}`),
    enabled: open,
    retry: false,
    staleTime: 5 * 60_000,
  });

  const resources = (query.data?.resources ?? [])
    .map((resource) => ({ resource, href: resourceHref(resource) }))
    .filter((item): item is { resource: LearningResource; href: string } => item.href !== null)
    .slice(0, 3);

  return (
    <>
      <button
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="link font-mono text-[10px] uppercase tracking-[0.1em]"
      >
        {open ? "Hide references" : "Read up first"}
      </button>

      {open ? (
        <div className="w-full">
          {query.data?.related_concepts.length ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {query.data.related_concepts.slice(0, 5).map((concept) => (
                <span key={concept} className="chip font-mono text-[9px]">
                  {concept}
                </span>
              ))}
            </div>
          ) : null}

          {resources.length > 0 ? (
            <ul className="mt-2 divide-y divide-line/70">
              {resources.map(({ resource, href }, index) => (
                <li
                  key={`${resource.target}-${href}-${index}`}
                  className="flex items-center gap-2 py-1.5"
                >
                  <span className="min-w-0 flex-1 truncate text-[11px] text-muted">
                    {resource.internal ? (
                      <Link href={href} className="link text-ink">
                        {resource.title}
                      </Link>
                    ) : (
                      <a
                        href={href}
                        target="_blank"
                        rel="noreferrer"
                        className="link text-ink"
                      >
                        {resource.title} <span aria-hidden>↗</span>
                      </a>
                    )}
                  </span>
                  {resource.minutes ? (
                    <span className="flex-none font-mono text-[9.5px] tabular-nums text-faint">
                      {resource.minutes}m
                    </span>
                  ) : null}
                </li>
              ))}
            </ul>
          ) : query.isFetching ? (
            <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
              loading references…
            </p>
          ) : (
            <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
              no references on file for this skill
            </p>
          )}
        </div>
      ) : null}
    </>
  );
}

/* -------------------------------------------------------------------------- */
/*  Evidence chain, shown inside the existing pass banners                      */
/* -------------------------------------------------------------------------- */

/**
 * Frames a pass as evidence rather than as a completed lesson: this attempt
 * updated a confidence score, which moved the learner along a known route.
 *
 * `confidence` comes from the submission response, not from the route, so the
 * number shown is the post-submission one even before the route refetches.
 */
export function EvidenceChain({
  skillId,
  confidence,
  className,
}: {
  skillId: string | undefined | null;
  confidence: number;
  className?: string;
}) {
  const context = usePathContext(skillId);
  if (!context) return null;

  const { path, step, threshold } = context;
  const verified = confidence >= threshold;
  const unlocks = step.unlocks.map((id) => skillLabel(path, id));

  return (
    <div className={cn("border-t border-line/60 pt-3", className)}>
      <p className="label">Evidence recorded</p>
      <ol className="mt-2 space-y-1.5">
        <ChainItem index="1">
          This attempt was graded and filed as execution evidence for{" "}
          <span className="text-ink">{step.skill_name}</span>.
        </ChainItem>
        <ChainItem index="2">
          Its confidence recomputed to{" "}
          <span className={cn("font-mono tabular-nums", verified ? "text-success" : "text-warning")}>
            {confidence.toFixed(0)}%
          </span>{" "}
          against a verified line of{" "}
          <span className="font-mono tabular-nums text-muted">{threshold.toFixed(0)}%</span>.
        </ChainItem>
        <ChainItem index="3">
          {verified
            ? unlocks.length > 0
              ? `Step ${step.order} of ${path.path.length} is above the line, which opens ${unlocks.join(", ")}.`
              : `Step ${step.order} of ${path.path.length} is above the line.`
            : `Step ${step.order} of ${path.path.length} still needs ${(threshold - confidence).toFixed(0)} more points before it verifies${
                unlocks.length > 0 ? ` and opens ${unlocks.join(", ")}` : ""
              }.`}
        </ChainItem>
      </ol>
      <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
        re-verification, not completion · the route re-routes off this score
      </p>
    </div>
  );
}

function ChainItem({ index, children }: { index: string; children: React.ReactNode }) {
  return (
    <li className="flex gap-2.5 text-[11.5px] leading-[1.6] text-muted">
      <span className="mt-px flex-none font-mono text-[9.5px] text-accent/70">{index}</span>
      <span className="min-w-0">{children}</span>
    </li>
  );
}
