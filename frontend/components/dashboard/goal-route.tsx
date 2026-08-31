"use client";

import Link from "next/link";

import { Counter, GrowBar } from "@/components/motion";
import { Badge, PanelSkeleton } from "@/components/ui/primitives";
import type { LearningPath } from "@/lib/types";

/**
 * Tier 2: the goal, how far along the route the learner is, and a way into the
 * full route at `/path`. Deliberately a summary — the route itself lives on that
 * page and is not duplicated here.
 */
export function GoalRoute({
  path,
  isLoading,
  errorText,
  fallbackGoal,
  threshold,
}: {
  path: LearningPath | undefined;
  isLoading: boolean;
  errorText: string | null;
  fallbackGoal: string | null;
  threshold: number;
}) {
  const goal = path?.goal.goal ?? fallbackGoal;
  const progress = path?.progress;

  // The milestone in flight, else the first one still ahead.
  const milestones = path?.milestones ?? [];
  const currentMilestone =
    milestones.find((milestone) => milestone.status === "in_progress") ??
    milestones.find((milestone) => milestone.status === "not_started") ??
    null;

  return (
    <section className="panel rounded-lg">
      <div className="flex flex-wrap items-start justify-between gap-4 border-b border-line px-5 py-4">
        <div className="min-w-0">
          <p className="label">Goal</p>
          <h2 className="mt-1.5 max-w-[52ch] text-[15px] font-medium leading-snug text-ink">
            {goal ?? "No goal set yet"}
          </h2>
        </div>
        <Link href="/path" className="btn-ghost btn-mono flex-none px-4 py-2">
          Open full route →
        </Link>
      </div>

      <div className="p-5">
        {isLoading ? (
          <PanelSkeleton lines={3} />
        ) : (
          <>
            {errorText ? (
              <p className="mb-4 text-[11.5px] leading-relaxed text-warning">{errorText}</p>
            ) : null}

            {progress ? (
              <div className="grid gap-6 sm:grid-cols-[auto_1fr] sm:items-end">
                <div>
                  <p className="label">Route progress</p>
                  <p className="display mt-2 text-[30px] leading-none tracking-tight text-ink">
                    <Counter value={progress.percent} />
                    <span className="text-[15px] text-faint">%</span>
                  </p>
                </div>
                <div className="min-w-0">
                  <div className="mb-1.5 flex items-baseline justify-between font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                    <span>
                      <span className="text-ink">{progress.skills_verified}</span> of{" "}
                      {progress.skills_total} skills verified
                    </span>
                    <span>threshold {threshold}%</span>
                  </div>
                  <GrowBar value={progress.percent} tone="accent" />
                  {currentMilestone ? (
                    <div className="mt-4 flex flex-wrap items-center gap-2.5">
                      <span className="label">next milestone</span>
                      <span className="text-[12.5px] text-ink">{currentMilestone.name}</span>
                      <Badge>
                        {currentMilestone.completed_count}/{currentMilestone.total_count} skills
                      </Badge>
                      {currentMilestone.path_id && currentMilestone.course_id ? (
                        <Link
                          href={`/paths/${currentMilestone.path_id}/courses/${currentMilestone.course_id}`}
                          className="btn-quiet btn-mono text-[10px]"
                        >
                          Course →
                        </Link>
                      ) : null}
                    </div>
                  ) : null}
                </div>
              </div>
            ) : (
              <p className="text-[12px] leading-relaxed text-muted">
                Route progress appears once your goal has been turned into a skill route.
              </p>
            )}
          </>
        )}
      </div>
    </section>
  );
}
