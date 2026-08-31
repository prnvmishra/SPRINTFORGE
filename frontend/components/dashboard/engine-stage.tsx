"use client";

import Link from "next/link";

import { cn } from "@/lib/utils";
import type { Skill } from "@/lib/types";

/**
 * The engine loop, as a strip you can read left to right and click through.
 *
 *   goal → verify → diagnose → personalise → build → evaluate → adapt ↻
 *
 * Every stage carries a line of evidence pulled from the learner's own state
 * rather than a description of what the stage would do, so the strip doubles as
 * a status readout: where the engine currently has you, and what it used to
 * decide that. The last two stages are consequences of submitting work rather
 * than destinations, so they link to where their output is visible.
 */

type Stage = {
  id: string;
  label: string;
  href: string | null;
  evidence: string;
};

export function EngineStage({
  goal,
  verifiedCount,
  totalSkills,
  weakest,
  routeSteps,
  projectTitle,
  ticketKey,
  ticketId,
  adaptationCount,
  placementPending,
}: {
  goal: string | null;
  verifiedCount: number;
  totalSkills: number;
  weakest: Skill | null;
  routeSteps: number | null;
  projectTitle: string | null;
  ticketKey: string | null;
  ticketId: string | null;
  adaptationCount: number | null;
  placementPending: boolean;
}) {
  const stages: Stage[] = [
    {
      id: "goal",
      label: "Goal",
      href: "/path",
      evidence: goal ?? "not set yet",
    },
    {
      id: "verify",
      label: "Verify",
      href: placementPending ? "/placement" : "/assessment",
      evidence: placementPending
        ? "placement pending"
        : totalSkills > 0
          ? `${verifiedCount}/${totalSkills} skills verified`
          : "nothing verified yet",
    },
    {
      id: "diagnose",
      label: "Diagnose",
      href: "/profile",
      evidence: weakest
        ? `weakest: ${weakest.skill_name} ${weakest.confidence.toFixed(0)}%`
        : "no gap detected",
    },
    {
      id: "personalise",
      label: "Personalise",
      href: "/path",
      evidence: routeSteps ? `${routeSteps} steps routed` : "route not built yet",
    },
    {
      id: "build",
      label: "Build",
      href: projectTitle ? "/projects" : "/practice",
      evidence: projectTitle ?? "practice a skill",
    },
    {
      id: "evaluate",
      label: "Evaluate",
      href: ticketId ? `/workspace/${ticketId}` : null,
      evidence: ticketKey ? `on ${ticketKey}` : "on your next submission",
    },
    {
      id: "adapt",
      label: "Adapt",
      // The adaptation feed this count comes from lives on the twin page.
      href: "/profile",
      // Null is "not loaded", which must not be reported as an empty history.
      evidence:
        adaptationCount === null
          ? "—"
          : adaptationCount > 0
            ? `${adaptationCount} path changes`
            : "no changes yet",
    },
  ];

  // A single defensible index rather than a guess per stage: the earliest thing
  // still outstanding is where the learner actually is.
  const current = !goal
    ? 0
    : placementPending || verifiedCount === 0
      ? 1
      : ticketKey || projectTitle
        ? 4
        : routeSteps
          ? 3
          : 2;

  return (
    <section
      aria-label="Where you are in the engine loop"
      className="overflow-hidden rounded border border-line bg-surface/40"
    >
      <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3">
        <p className="label">The loop</p>
        <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
          goal → verify → diagnose → personalise → build → evaluate → adapt ↻
        </p>
      </div>

      <ol className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7">
        {stages.map((stage, index) => {
          const active = index === current;
          const done = index < current;
          const body = (
            <>
              <span className="flex items-baseline gap-1.5">
                <span
                  className={cn(
                    "font-mono text-[9.5px] tabular-nums",
                    active ? "text-accent" : "text-faint",
                  )}
                >
                  {String(index + 1).padStart(2, "0")}
                </span>
                <span
                  className={cn(
                    "font-mono text-[11px] uppercase tracking-[0.1em]",
                    active ? "text-ink" : done ? "text-muted" : "text-faint",
                  )}
                >
                  {stage.label}
                </span>
              </span>
              <span
                className={cn(
                  "mt-1 block truncate text-[11px] leading-[1.5]",
                  active ? "text-muted" : "text-faint",
                )}
                title={stage.evidence}
              >
                {stage.evidence}
              </span>
            </>
          );

          return (
            <li
              key={stage.id}
              aria-current={active ? "step" : undefined}
              className={cn(
                "relative border-b border-r border-line px-4 py-3 last:border-r-0 xl:border-b-0",
                active && "bg-accent/[0.05]",
              )}
            >
              {/* Accent rule marks the current stage without moving anything. */}
              <span
                className={cn(
                  "absolute inset-x-0 top-0 h-px",
                  active ? "bg-accent" : "bg-transparent",
                )}
                aria-hidden
              />
              {stage.href ? (
                <Link href={stage.href} className="block transition-opacity hover:opacity-80">
                  {body}
                </Link>
              ) : (
                <div>{body}</div>
              )}
            </li>
          );
        })}
      </ol>
    </section>
  );
}
