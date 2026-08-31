"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Counter, GrowBar, Reveal } from "@/components/motion";
import { NextStepPanel } from "@/components/path/next-step";
import { RouteList } from "@/components/path/route-list";
import {
  Alert,
  Badge,
  EmptyState,
  Loader,
  Panel,
  PanelSkeleton,
  SectionTitle,
  StatusPill,
} from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { LearningMilestone, LearningPath } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

/**
 * My Learning Path.
 *
 * One argument, top to bottom: the goal, what has actually been proven, the
 * prerequisite-ordered route to the goal, and the single next step with the
 * reason the engine chose it.
 */
export default function LearningPathPage() {
  const query = useQuery({
    queryKey: ["learning-path"],
    queryFn: () => api<LearningPath>("/learning-path"),
  });

  if (query.isLoading) {
    return (
      <AppShell>
        <Loader label="Routing your path" />
        <div className="mt-8 space-y-6">
          <Panel>
            <PanelSkeleton lines={3} />
          </Panel>
          <Panel>
            <PanelSkeleton lines={6} />
          </Panel>
        </div>
      </AppShell>
    );
  }

  if (query.isError || !query.data) {
    return (
      <AppShell>
        <PageHeader eyebrow="My learning path" title="Route unavailable" />
        <div className="mt-8">
          <Alert tone="danger" title="Could not load your path">
            {errorMessage(query.error)}
          </Alert>
          <button onClick={() => void query.refetch()} className="btn-ghost btn-mono mt-5 px-4 py-2">
            Retry
          </button>
        </div>
      </AppShell>
    );
  }

  const data = query.data;
  const { goal, progress, confidence_threshold: threshold } = data;

  if (!goal.goal) {
    return (
      <AppShell>
        <PageHeader eyebrow="My learning path" title="No goal set yet" />
        <div className="mt-8">
          <EmptyState
            eyebrow="Nothing to route"
            title="Tell us what you're building toward"
            description="Your route is derived from a goal and the skills you claim. Complete onboarding and the engine will order a path from where you are to where you want to be."
            action={
              <Link href="/onboarding" className="btn-primary btn-mono px-5 py-2.5">
                Start onboarding <span aria-hidden>→</span>
              </Link>
            }
          />
        </div>
      </AppShell>
    );
  }

  const verifiedCount = progress.skills_verified;
  const totalCount = progress.skills_total;

  return (
    <AppShell>
      <PageHeader
        eyebrow="My learning path"
        title={goal.goal}
        meta={
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
            <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
              experience <span className="text-ink">{goal.experience_level}</span>
            </span>
            {goal.target_stack.length > 0 ? (
              <span className="flex flex-wrap items-center gap-1.5">
                <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
                  stack
                </span>
                {goal.target_stack.map((item) => (
                  <Badge key={item}>{item}</Badge>
                ))}
              </span>
            ) : null}
            {goal.active_project_id && goal.active_project_title ? (
              <Link
                href={`/projects/${goal.active_project_id}`}
                className="link font-mono text-[10.5px] uppercase tracking-[0.1em]"
              >
                building {goal.active_project_title}
              </Link>
            ) : null}
          </div>
        }
        actions={
          goal.path_id && goal.next_course_id ? (
            <Link
              href={`/paths/${goal.path_id}/courses/${goal.next_course_id}`}
              className="btn-ghost btn-mono px-4 py-2"
            >
              Next course
            </Link>
          ) : null
        }
      />

      {/* ---------------------------------------------------------- progress */}
      <Reveal className="mt-8">
        <Panel>
          <SectionTitle
            eyebrow="Proven so far"
            title="Verified skills on this route"
            hint={`Verified means confidence at or above ${threshold.toFixed(0)}%. Claims alone never count.`}
          />
          <div className="flex flex-wrap items-end justify-between gap-6">
            <p className="display text-display-sm text-ink">
              <Counter value={verifiedCount} />
              <span className="text-faint"> / {totalCount}</span>
            </p>
            <p className="font-mono text-[11px] tabular-nums text-muted">
              <Counter value={progress.percent} decimals={0} suffix="%" /> of the route verified
            </p>
          </div>
          <GrowBar
            value={progress.percent}
            tone={progress.percent > 0 ? "accent" : "muted"}
            className="mt-4"
          />
          {verifiedCount === 0 ? (
            <p className="mt-4 max-w-[62ch] text-[12px] leading-relaxed text-muted">
              Nothing is verified yet — that is the honest starting point, not a failure. The route
              below is already ordered for you; clearing the first step unlocks the ones behind it.
            </p>
          ) : null}
        </Panel>
      </Reveal>

      {/* ------------------------------------------------------- next action */}
      <Reveal className="mt-6" delay={60}>
        {data.next_action ? (
          <NextStepPanel action={data.next_action} />
        ) : (
          <EmptyState
            eyebrow="Next step"
            title="No recommendation right now"
            description="The routing engine has nothing queued for you at this moment. Verify a skill on the route below and it will re-route from the result."
          />
        )}
      </Reveal>

      {/* -------------------------------------------------------------- route */}
      <Reveal className="mt-12" delay={90}>
        <SectionTitle
          eyebrow="The route"
          title="Ordered by prerequisites, not by preference"
          hint="Each step unlocks the next. A step stays locked until every prerequisite clears the threshold."
        />
        {data.path.length > 0 ? (
          <RouteList path={data.path} milestones={data.milestones} threshold={threshold} />
        ) : (
          <EmptyState
            eyebrow="Empty route"
            title="No skills are mapped to this goal yet"
            description="The knowledge graph has no route for this goal. Run an assessment so the engine has evidence to plan from."
            action={
              <Link href="/assessment" className="btn-ghost btn-mono px-4 py-2">
                Go to skills
              </Link>
            }
          />
        )}
      </Reveal>

      {/* --------------------------------------------- execution milestones */}
      {data.execution_milestones.length > 0 ? (
        <Reveal className="mt-12" delay={120}>
          <SectionTitle
            eyebrow="Project delivery"
            title="Execution milestones"
            hint="Sprints on your project. Separate from the learning milestones above — these track shipped work, not verified skills."
          />
          <div className="grid gap-3 sm:grid-cols-2">
            {data.execution_milestones.map((milestone) => (
              <ExecutionMilestoneCard key={milestone.name} milestone={milestone} />
            ))}
          </div>
        </Reveal>
      ) : null}
    </AppShell>
  );
}

function ExecutionMilestoneCard({ milestone }: { milestone: LearningMilestone }) {
  const percent =
    milestone.total_count > 0
      ? Math.round((milestone.completed_count / milestone.total_count) * 100)
      : 0;
  return (
    <Panel>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <h3 className="text-[13px] font-medium text-ink">{milestone.name}</h3>
        <StatusPill status={milestone.status} />
      </div>
      <p className="mt-2 font-mono text-[10px] tabular-nums text-faint">
        {milestone.completed_count}/{milestone.total_count} complete
      </p>
      <GrowBar value={percent} tone={percent > 0 ? "accent" : "muted"} className="mt-3" />
    </Panel>
  );
}
