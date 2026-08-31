"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { GoalRoute } from "@/components/dashboard/goal-route";
import { NeedsWorkList } from "@/components/dashboard/needs-work-list";
import { PlacementGate } from "@/components/dashboard/placement-gate";
import { RecommendationCard } from "@/components/dashboard/recommendation-card";
import { GrowBar } from "@/components/motion";
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
import type { Dashboard, LearningPath } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

export default function DashboardPage() {
  const { data, isLoading, error } = useQuery({
    queryKey: ["dashboard"],
    queryFn: () => api<Dashboard>("/profile/dashboard"),
  });

  // The route degrades in place: the dashboard must still render if it fails, so
  // its error is handled inside its own section.
  const path = useQuery({
    queryKey: ["learning-path"],
    queryFn: () => api<LearningPath>("/learning-path"),
  });

  return (
    <AppShell>
      {isLoading ? (
        <DashboardLoading />
      ) : error ? (
        <Alert tone="danger" title="Could not load the dashboard">
          {errorMessage(error)}
        </Alert>
      ) : data ? (
        <DashboardView data={data} path={path} />
      ) : null}
    </AppShell>
  );
}

function DashboardLoading() {
  return (
    <div className="space-y-6">
      <Loader label="Reading your digital twin" />
      <Panel className="h-40">
        <PanelSkeleton lines={4} />
      </Panel>
      <Panel className="h-28">
        <PanelSkeleton lines={2} />
      </Panel>
    </div>
  );
}

type QueryLike<T> = { data: T | undefined; isLoading: boolean; error: unknown };

/**
 * The dashboard answers one question: **what do I do right now?**
 *
 *   1. placement, when a real recommendation would still be a guess
 *   2. the next action and why it was chosen
 *   3. goal and route progress
 *   4. the build in flight
 *   5. the shortest list of what is holding you back
 *
 * Everything historical — verified skills, XP ledger, activity log, adaptation
 * trail, diagnosed failures — lives on the Digital Twin page. It is a record of
 * the past, and mixing it in here buried the one thing this page is for.
 */
function DashboardView({
  data,
  path,
}: {
  data: Dashboard;
  path: QueryLike<LearningPath>;
}) {
  const { twin, rewards, active_project: project, current_ticket: ticket, placement } = data;
  const firstName = data.user.name.split(" ")[0];
  const verifiedCount = data.verified_skills.filter(
    (skill) => skill.confidence >= data.confidence_threshold,
  ).length;
  const placementPending = placement?.required ?? false;

  return (
    <div className="space-y-8">
      {/* ------------------------------------------------------------ header */}
      <PageHeader
        eyebrow={twin.goal ?? "No goal set"}
        title={
          <>
            Welcome back, <span className="text-accent">{firstName}</span>
          </>
        }
        meta={
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
            <span>
              level <span className="text-ink">{rewards.level}</span>
            </span>
            <span className="h-2.5 w-px bg-line" />
            <span>
              <span className="text-ink">{twin.overall_confidence.toFixed(0)}%</span> confidence
            </span>
            <span className="h-2.5 w-px bg-line" />
            <span>
              <span className="text-ink">{verifiedCount}</span>/{data.verified_skills.length}{" "}
              skills verified
            </span>
            {twin.streak_days > 0 ? (
              <>
                <span className="h-2.5 w-px bg-line" />
                <span>
                  <span className="text-accent">{twin.streak_days}</span> day streak
                </span>
              </>
            ) : null}
          </div>
        }
        actions={
          <>
            <Link href="/path" className="btn-ghost btn-mono px-4 py-2">
              My path
            </Link>
            <Link href="/profile" className="btn-ghost btn-mono px-4 py-2">
              Digital twin
            </Link>
          </>
        }
      />

      {/* ---------------------------------------------------- 1. placement */}
      {placement ? <PlacementGate placement={placement} /> : null}

      {/* ------------------------------------------- 2. the next action + why */}
      {/* Suppressed during placement: two competing "do this next" cards is
          exactly the clutter this page was cut down to remove, and the
          recommendation card would only be repeating the gate above. */}
      {!placementPending ? (
        <section>
          <RecommendationCard recommendation={data.recommendation} />
          <p className="mt-2.5 flex flex-wrap items-center gap-x-2 gap-y-1 font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
            <span>chosen by the deterministic routing engine</span>
            <span className="h-2.5 w-px bg-line" />
            <span>rule-based · traceable · not model-generated</span>
          </p>
        </section>
      ) : null}

      {/* ---------------------------------------------- 3. goal and the route */}
      <GoalRoute
        path={path.data}
        isLoading={path.isLoading}
        errorText={path.error ? errorMessage(path.error) : null}
        fallbackGoal={twin.goal}
        threshold={data.confidence_threshold}
      />

      {/* -------------------------------------------- 4. execution: the build */}
      <Panel inset={false}>
        <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-4">
          <div>
            <p className="label">In progress</p>
            <h2 className="mt-1.5 text-[13px] font-medium text-ink">
              {project ? project.title : "No active project"}
            </h2>
          </div>
          {project ? (
            <Link
              href={`/projects/${project.id}`}
              className="btn-quiet btn-mono flex-none text-[10px]"
            >
              Open board →
            </Link>
          ) : null}
        </div>

        {project ? (
          <div className="p-5">
            <div className="flex flex-wrap items-center gap-1.5">
              {project.tech_stack.map((tech) => (
                <Badge key={tech}>{tech}</Badge>
              ))}
            </div>

            <div className="mt-4">
              <div className="mb-1.5 flex items-baseline justify-between font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                <span>
                  {project.tickets_done}/{project.ticket_count} tickets ·{" "}
                  {project.sprint_count} sprints
                </span>
                <span className="text-ink">{project.progress_percent.toFixed(0)}%</span>
              </div>
              <GrowBar value={project.progress_percent} tone="accent" />
            </div>

            {data.current_sprint ? (
              <p className="mt-4 font-mono text-[10.5px] uppercase tracking-[0.08em] text-faint">
                {data.current_sprint.milestone}
                <span className="mx-1.5 text-line-strong">/</span>
                <span className="text-ink">{data.current_sprint.name}</span>
              </p>
            ) : null}

            {ticket ? (
              <div className="mt-5 border-l-2 border-accent/50 pl-4">
                <div className="flex flex-wrap items-center gap-3">
                  <span className="font-mono text-[11px] text-accent">{ticket.key}</span>
                  <StatusPill status={ticket.status} />
                </div>
                <p className="mt-2 text-[14px] font-medium text-ink">{ticket.title}</p>
                <p className="mt-1.5 max-w-[62ch] text-[12px] leading-relaxed text-muted">
                  {ticket.description}
                </p>
                <div className="mt-4 flex flex-wrap items-center gap-1.5">
                  <Badge>{ticket.target_skill_name}</Badge>
                  <Badge>L{ticket.difficulty}/10</Badge>
                  <Badge>{ticket.estimated_minutes}m</Badge>
                  <Badge tone="accent">+{ticket.xp_reward} XP</Badge>
                  <Link
                    href={`/workspace/${ticket.id}`}
                    className="btn-primary btn-mono ml-auto px-4 py-2"
                  >
                    Open workspace →
                  </Link>
                </div>
              </div>
            ) : (
              <p className="mt-5 border-l-2 border-line pl-4 text-[12px] leading-relaxed text-muted">
                No actionable ticket right now. Clear the gap above and the next ticket unlocks.
              </p>
            )}
          </div>
        ) : (
          <div className="p-5">
            <EmptyState
              eyebrow="Project execution mode"
              title="Your next build starts here."
              description="Describe an idea and SprintForge breaks it into milestones, sprints and verified engineering tickets."
              action={
                <Link href="/projects/new" className="btn-primary btn-mono px-5 py-2.5">
                  Create project →
                </Link>
              }
            />
          </div>
        )}
      </Panel>

      {/* -------------------------------------------- 5. the shortest to-fix */}
      {data.skills_needing_improvement.length > 0 ? (
        <Panel>
          <SectionTitle
            eyebrow={`${data.skills_needing_improvement.length} below ${data.confidence_threshold}%`}
            title="What needs work"
            hint="The three weakest first. The full breakdown, your failure history and the XP ledger live on your Digital Twin."
            action={
              <Link href="/profile" className="btn-quiet btn-mono text-[10px]">
                Full twin →
              </Link>
            }
          />
          <NeedsWorkList
            skills={data.skills_needing_improvement.slice(0, 3)}
            threshold={data.confidence_threshold}
          />
        </Panel>
      ) : null}
    </div>
  );
}
