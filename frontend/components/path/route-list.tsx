"use client";

import Link from "next/link";

import { GrowBar } from "@/components/motion";
import { Badge, StatusPill } from "@/components/ui/primitives";
import type { LearningMilestone, LearningPathStep } from "@/lib/types";
import { cn, confidenceTone } from "@/lib/utils";

/** Copy for each route state. Colour is never the only signal. */
const STATE_COPY: Record<LearningPathStep["state"], string> = {
  verified: "Verified",
  in_progress: "In progress",
  needs_work: "Needs work",
  not_started: "Not started",
  locked: "Locked",
};

type MilestoneGroup = {
  /** Null when the route contains skills no learning milestone claims. */
  milestone: LearningMilestone | null;
  steps: LearningPathStep[];
};

/**
 * Groups the ordered route by learning milestone without reordering it.
 *
 * Group order follows first appearance in the path, so the vertical reading
 * order stays identical to the prerequisite-derived sequence.
 */
function groupByMilestone(
  path: LearningPathStep[],
  milestones: LearningMilestone[],
): MilestoneGroup[] {
  const owner = new Map<string, LearningMilestone>();
  for (const milestone of milestones) {
    for (const skill of milestone.skills) {
      if (!owner.has(skill.skill_id)) owner.set(skill.skill_id, milestone);
    }
  }

  const groups: MilestoneGroup[] = [];
  const index = new Map<LearningMilestone | null, MilestoneGroup>();

  for (const step of path) {
    const milestone = owner.get(step.skill_id) ?? null;
    let group = index.get(milestone);
    if (!group) {
      group = { milestone, steps: [] };
      index.set(milestone, group);
      groups.push(group);
    }
    group.steps.push(step);
  }

  return groups;
}

export function RouteList({
  path,
  milestones,
  threshold,
}: {
  path: LearningPathStep[];
  milestones: LearningMilestone[];
  threshold: number;
}) {
  const groups = groupByMilestone(path, milestones);

  return (
    <div className="space-y-10">
      {groups.map((group, groupIndex) => (
        <section key={group.milestone?.course_id ?? group.milestone?.name ?? `unsorted-${groupIndex}`}>
          <MilestoneHeader milestone={group.milestone} />
          <ol className="mt-4">
            {group.steps.map((step) => (
              <RouteStep key={step.skill_id} step={step} threshold={threshold} />
            ))}
          </ol>
        </section>
      ))}
    </div>
  );
}

function MilestoneHeader({ milestone }: { milestone: LearningMilestone | null }) {
  if (!milestone) {
    return (
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2 border-b border-line pb-3">
        <span className="label">Learning milestone · unassigned</span>
        <span className="hidden h-px flex-1 bg-line sm:block" />
        <span className="font-mono text-[10px] text-faint">
          not part of an authored course
        </span>
      </div>
    );
  }

  const percent =
    milestone.total_count > 0
      ? Math.round((milestone.completed_count / milestone.total_count) * 100)
      : 0;

  return (
    <div className="border-b border-line pb-3">
      <div className="flex flex-wrap items-center gap-x-3 gap-y-2">
        <span className="label">Learning milestone</span>
        <StatusPill status={milestone.status} />
        <span className="hidden h-px flex-1 bg-line sm:block" />
        <span className="font-mono text-[10px] tabular-nums text-faint">
          {milestone.completed_count}/{milestone.total_count} skills verified
        </span>
      </div>

      <div className="mt-2.5 flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <h3 className="display text-[15px] tracking-tight text-ink">{milestone.name}</h3>
        {milestone.path_id && milestone.course_id ? (
          <Link
            href={`/paths/${milestone.path_id}/courses/${milestone.course_id}`}
            className="link font-mono text-[10px] uppercase tracking-[0.1em]"
          >
            Open course →
          </Link>
        ) : null}
      </div>

      <GrowBar
        value={percent}
        tone={milestone.status === "completed" ? "success" : "muted"}
        className="mt-3"
      />
    </div>
  );
}

function RouteStep({ step, threshold }: { step: LearningPathStep; threshold: number }) {
  const tone = confidenceTone(step.confidence, threshold);
  const locked = step.state === "locked";
  const courseHref = step.taught_by
    ? `/paths/${step.taught_by.path_id}/courses/${step.taught_by.course_id}`
    : null;

  return (
    <li
      aria-current={step.is_next ? "step" : undefined}
      className={cn(
        "relative border-b border-line/70 pl-8 sm:pl-11",
        step.is_next ? "bg-accent/[0.035]" : undefined,
      )}
    >
      {/* Connector: the spine that makes the sequence, not the styling, the message. */}
      <span
        aria-hidden
        className="absolute left-[9px] top-0 h-full w-px bg-line sm:left-[13px]"
      />
      <span
        aria-hidden
        className={cn(
          "absolute left-[5px] top-[26px] h-[9px] w-[9px] rounded-full border sm:left-[9px]",
          step.state === "verified"
            ? "border-success bg-success"
            : step.is_next
              ? "border-accent bg-accent"
              : locked
                ? "border-line-strong bg-canvas"
                : "border-line-strong bg-elevated",
        )}
      />
      {step.is_next ? (
        <span aria-hidden className="absolute inset-y-0 left-0 w-[2px] bg-accent" />
      ) : null}

      <div className="py-5 pr-1">
        <div className="flex flex-wrap items-baseline gap-x-3 gap-y-2">
          <span className="font-mono text-[11px] tabular-nums text-faint">
            {String(step.order).padStart(2, "0")}
          </span>
          <h4
            className={cn(
              "text-[14px] font-medium tracking-tight",
              locked ? "text-muted" : "text-ink",
            )}
          >
            {step.skill_name}
          </h4>
          {step.is_next ? <Badge tone="accent">next up</Badge> : null}
          <span className="hidden h-px flex-1 bg-line/70 sm:block" />
          <span
            className={cn(
              "font-mono text-[10px] uppercase tracking-[0.12em]",
              step.state === "verified"
                ? "text-success"
                : locked
                  ? "text-faint"
                  : "text-muted",
            )}
          >
            {STATE_COPY[step.state]}
          </span>
        </div>

        <div className="mt-3 flex flex-wrap items-center gap-x-4 gap-y-2">
          <div className="flex min-w-[180px] flex-1 items-center gap-3">
            <GrowBar
              value={step.confidence}
              threshold={threshold}
              tone={step.confidence >= threshold ? tone.tone : locked ? "muted" : "warning"}
              className="flex-1"
            />
            <span className={cn("w-20 flex-none font-mono text-[10.5px] tabular-nums", tone.text)}>
              {step.confidence.toFixed(0)}%
              <span className="text-faint"> / {threshold.toFixed(0)}%</span>
            </span>
          </div>

          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
            {step.track} · weight {step.difficulty_weight} · {step.item_count} items
          </span>
        </div>

        <ClaimRow step={step} />

        {locked && step.missing_prerequisites.length > 0 ? (
          <div className="mt-3 border-l border-line pl-3">
            <p className="label mb-1.5">Blocked by</p>
            <ul className="space-y-1">
              {step.missing_prerequisites.map((gap) => (
                <li key={gap.skill_id} className="text-[11.5px] leading-relaxed text-muted">
                  Needs{" "}
                  <Link href={`/practice?skill=${gap.skill_id}`} className="link text-ink">
                    {gap.skill_name}
                  </Link>{" "}
                  at {gap.required.toFixed(0)}% — currently{" "}
                  <span className="font-mono text-warning">{gap.confidence.toFixed(0)}%</span>.
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {step.weak_concepts.length > 0 ? (
          <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
            <span className="label mr-2">Weak concepts</span>
            {step.weak_concepts.join(", ")}
          </p>
        ) : null}

        {step.has_open_gap ? (
          <p className="mt-2 font-mono text-[10px] uppercase tracking-[0.1em] text-warning">
            open gap from a previous failure
          </p>
        ) : null}

        <div className="mt-3.5 flex flex-wrap items-center gap-x-4 gap-y-2">
          {locked ? (
            <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              Clear the prerequisite above to unlock
            </span>
          ) : (
            <>
              <Link
                href={`/assessment/${step.skill_id}`}
                className="link font-mono text-[10px] uppercase tracking-[0.1em]"
              >
                Verify with assessment
              </Link>
              <Link
                href={`/practice?skill=${step.skill_id}`}
                className="link font-mono text-[10px] uppercase tracking-[0.1em]"
              >
                Practice
              </Link>
            </>
          )}
          {courseHref ? (
            <Link
              href={courseHref}
              className="link font-mono text-[10px] uppercase tracking-[0.1em]"
            >
              Taught in course
            </Link>
          ) : null}
        </div>
      </div>
    </li>
  );
}

/**
 * A claimed level is a hypothesis, never a result. This row keeps the claim and
 * the evidence side by side so the difference is impossible to miss.
 */
function ClaimRow({ step }: { step: LearningPathStep }) {
  if (!step.claimed_level) return null;

  return (
    <div className="mt-3 flex flex-wrap items-center gap-x-6 gap-y-1.5 border-l border-line pl-3">
      <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
        claimed <span className="text-muted">{step.claimed_level}</span>
      </span>
      <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
        verified{" "}
        {step.verified ? (
          <span className="text-success">{step.verified_level ?? "verified"}</span>
        ) : (
          <span className="text-warning">not yet</span>
        )}
      </span>
      {!step.verified ? (
        <span className="text-[11.5px] leading-relaxed text-muted">
          {step.has_evidence
            ? "Evidence so far does not support this claim yet."
            : "This claim is untested — no evidence recorded."}
        </span>
      ) : null}
    </div>
  );
}
