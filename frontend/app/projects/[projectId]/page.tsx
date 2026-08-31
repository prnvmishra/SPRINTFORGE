"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Counter, GrowBar, Reveal } from "@/components/motion";
import { Alert, Badge, Loader, StatusPill } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Project, Ticket } from "@/lib/types";
import { cn, errorMessage, statusGlyph } from "@/lib/utils";

export default function ProjectBoardPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;

  const { data, isLoading, error } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () =>
      api<{ project: Project; next_ticket: Ticket | null }>(`/projects/${projectId}`),
  });

  if (isLoading) {
    return (
      <AppShell wide>
        <div className="grid min-h-[50vh] place-items-center">
          <Loader label="Loading sprint board" />
        </div>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell wide>
        <Alert tone="danger" title="Could not load the project">
          {errorMessage(error) || "Project not found."}
        </Alert>
      </AppShell>
    );
  }

  const { project, next_ticket: nextTicket } = data;
  const sprints = project.sprints ?? [];
  const milestones = Array.from(new Set(sprints.map((s) => s.milestone)));

  return (
    <AppShell wide>
      <PageHeader
        eyebrow="Project execution mode"
        title={project.title}
        meta={
          <>
            <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">{project.idea}</p>
            <div className="mt-3 flex flex-wrap gap-1.5">
              {project.tech_stack.map((tech) => (
                <Badge key={tech}>{tech}</Badge>
              ))}
              <Badge>{project.complexity}</Badge>
              <Badge>{milestones.length} milestones</Badge>
            </div>
          </>
        }
        actions={
          <>
            <Link href="/projects" className="btn-ghost btn-mono px-4 py-2">
              All projects
            </Link>
            {/* The board plans the work; this shows the product it has produced
                so far, in progress or finished. */}
            <Link
              href={`/projects/${projectId}/preview`}
              className="btn-subtle btn-mono px-4 py-2"
            >
              Preview project ▸
            </Link>
            {nextTicket ? (
              <Link
                href={`/workspace/${nextTicket.id}`}
                className="btn-primary btn-mono px-4 py-2"
              >
                Open {nextTicket.key} →
              </Link>
            ) : null}
          </>
        }
      />

      {/* ------------------------------------------------------ plan summary */}
      <div className="mt-8 grid gap-px border border-line bg-line md:grid-cols-[auto_1fr]">
        <div className="flex items-center gap-6 bg-surface px-6 py-5">
          <div>
            <p className="label">Verified</p>
            <p className="display mt-1.5 text-[30px] leading-none text-accent">
              <Counter value={project.progress_percent} />
              <span className="text-[15px] text-faint">%</span>
            </p>
          </div>
          <div className="border-l border-line pl-6">
            <p className="label">Tickets</p>
            <p className="display mt-1.5 text-[30px] leading-none text-ink">
              {project.tickets_done}
              <span className="text-[15px] text-faint">/{project.ticket_count}</span>
            </p>
          </div>
        </div>

        <div className="flex flex-col justify-center gap-3 bg-surface px-6 py-5">
          <div className="flex items-center gap-3">
            <StatusPill status={project.status} />
            <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {sprints.length} sprints planned
            </span>
          </div>
          <GrowBar value={project.progress_percent} tone="accent" />
          {project.plan_rationale ? (
            <p className="max-w-[80ch] text-[11.5px] leading-relaxed text-muted">
              {project.plan_rationale}
            </p>
          ) : null}
        </div>
      </div>

      {/* ------------------------------------------------------------ board */}
      <div className="mt-12 space-y-14">
        {milestones.map((milestone, milestoneIndex) => (
          <section key={milestone}>
            <div className="mb-6 flex items-center gap-4">
              <span className="font-mono text-[10px] text-accent">
                M{String(milestoneIndex + 1).padStart(2, "0")}
              </span>
              <h2 className="display text-[17px] tracking-tight text-ink">{milestone}</h2>
              <span className="h-px flex-1 bg-line" />
            </div>

            {/* Real gaps with per-panel borders rather than a hairline background
                grid: a milestone with fewer sprints than columns would otherwise
                render the leftover track as an empty slab. */}
            <div className="grid gap-4 lg:grid-cols-2 xl:grid-cols-3">
              {sprints
                .filter((sprint) => sprint.milestone === milestone)
                .map((sprint, sprintIndex) => {
                  const done = sprint.tickets.filter((t) => t.status === "done").length;
                  const pct = sprint.tickets.length
                    ? (done / sprint.tickets.length) * 100
                    : 0;
                  return (
                    <Reveal
                      key={sprint.id}
                      delay={sprintIndex * 60}
                      className="flex flex-col rounded border border-line bg-surface"
                    >
                      {/* Sprint header */}
                      <div className="border-b border-line px-4 py-3.5">
                        <div className="flex items-center justify-between gap-3">
                          <p className="text-[12.5px] font-medium text-ink">{sprint.name}</p>
                          <StatusPill status={sprint.status} />
                        </div>
                        <div className="mt-2.5 flex items-center gap-3">
                          <GrowBar
                            value={pct}
                            tone={pct === 100 ? "success" : "accent"}
                            className="flex-1"
                          />
                          <span className="flex-none font-mono text-[9.5px] tabular-nums text-faint">
                            {done}/{sprint.tickets.length}
                          </span>
                        </div>
                      </div>

                      {/* Tickets as a compact engineering list */}
                      <ul className="divide-y divide-line/60">
                        {sprint.tickets.map((ticket) => (
                          <TicketRow key={ticket.id} ticket={ticket} />
                        ))}
                      </ul>
                    </Reveal>
                  );
                })}
            </div>
          </section>
        ))}
      </div>
    </AppShell>
  );
}

/**
 * A ticket row. Compact and information-dense: id, status glyph, title, target
 * skill and cost — the things you triage on.
 */
function TicketRow({ ticket }: { ticket: Ticket }) {
  const locked = ticket.status === "locked";
  const done = ticket.status === "done";

  const body = (
    <div
      className={cn(
        "border-l-2 px-4 py-3 transition-colors duration-200",
        locked
          ? "border-transparent"
          : done
            ? "border-success/40 hover:bg-elevated"
            : "border-accent/40 hover:bg-elevated",
      )}
    >
      <div className="flex items-center gap-2.5">
        <span
          className={cn(
            "font-mono text-[9px]",
            done ? "text-success" : locked ? "text-faint" : "text-accent",
          )}
          aria-hidden
        >
          {statusGlyph(ticket.status)}
        </span>
        <span
          className={cn(
            "font-mono text-[10px]",
            locked ? "text-faint" : "text-accent",
          )}
        >
          {ticket.key}
        </span>
        <span
          className={cn(
            "min-w-0 flex-1 truncate text-[12px]",
            locked ? "text-faint" : done ? "text-muted line-through decoration-line-strong" : "text-ink",
          )}
        >
          {ticket.title}
        </span>
        <span className="flex-none font-mono text-[9.5px] tabular-nums text-faint">
          L{ticket.difficulty}
        </span>
      </div>

      <div className="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 pl-[26px] font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
        <span className="truncate">{ticket.target_skill_name}</span>
        <span>{ticket.estimated_minutes}m</span>
        <span className={done ? "text-success" : "text-faint"}>+{ticket.xp_reward} xp</span>
        {ticket.attempt_count > 0 ? (
          <span className="text-warning">
            {ticket.attempt_count} attempt{ticket.attempt_count === 1 ? "" : "s"}
          </span>
        ) : null}
      </div>

      {locked && ticket.lock_reason ? (
        <p className="mt-2 pl-[26px] text-[10.5px] leading-relaxed text-warning/80">
          {ticket.lock_reason}
        </p>
      ) : null}
    </div>
  );

  if (locked) return <li className="opacity-60">{body}</li>;
  return (
    <li>
      <Link href={`/workspace/${ticket.id}`} className="block">
        {body}
      </Link>
    </li>
  );
}
