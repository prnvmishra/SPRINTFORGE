"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { GrowBar, Reveal } from "@/components/motion";
import { Badge, EmptyState, Loader, PanelSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Project } from "@/lib/types";

export default function ProjectsPage() {
  const projects = useQuery({
    queryKey: ["projects"],
    queryFn: () => api<{ projects: Project[] }>("/projects"),
  });

  const list = projects.data?.projects ?? [];

  return (
    <AppShell>
      <PageHeader
        eyebrow="Project execution mode"
        title="Your projects"
        meta={
          <p className="max-w-[64ch] text-[12.5px] leading-[1.7] text-muted">
            SprintForge does not hand you a finished project. It plans milestones, sprints and
            engineering tickets, then verifies each ticket against real acceptance checks before the
            next one unlocks.
          </p>
        }
        actions={
          <Link href="/projects/new" className="btn-primary btn-mono px-4 py-2">
            New project →
          </Link>
        }
      />

      {projects.isLoading ? (
        <div className="mt-10 space-y-5">
          <Loader label="Loading project plans" />
          <div className="grid gap-px md:grid-cols-2">
            {Array.from({ length: 2 }).map((_, index) => (
              <div key={index} className="bg-surface p-5 ring-1 ring-line">
                <PanelSkeleton lines={4} />
              </div>
            ))}
          </div>
        </div>
      ) : list.length === 0 ? (
        <div className="mt-10">
          <EmptyState
            eyebrow="Nothing in flight"
            title="Your next build starts here."
            description="Describe what you want to build and SprintForge turns it into a sprint backlog gated by your verified skills."
            action={
              <Link href="/projects/new" className="btn-primary btn-mono px-5 py-2.5">
                Create your first project →
              </Link>
            }
          />
        </div>
      ) : (
        <div className="mt-10 grid gap-px md:grid-cols-2">
          {list.map((project, index) => (
            <Reveal key={project.id} delay={index * 60}>
              <Link
                href={`/projects/${project.id}`}
                className="group flex h-full flex-col bg-surface p-6 ring-1 ring-line transition-colors duration-200 hover:bg-elevated"
              >
                <div className="flex items-start justify-between gap-4">
                  <h2 className="display text-[17px] tracking-tight text-ink transition-colors group-hover:text-accent">
                    {project.title}
                  </h2>
                  <Badge>{project.status}</Badge>
                </div>

                <p className="mt-3 line-clamp-2 max-w-[52ch] text-[12px] leading-relaxed text-muted">
                  {project.idea}
                </p>

                <div className="mt-4 flex flex-wrap gap-1.5">
                  {project.tech_stack.map((tech) => (
                    <Badge key={tech}>{tech}</Badge>
                  ))}
                </div>

                <div className="mt-auto pt-6">
                  <div className="mb-2 flex items-baseline justify-between font-mono text-[10px] uppercase tracking-[0.1em]">
                    <span className="text-faint">
                      {project.tickets_done}/{project.ticket_count} tickets ·{" "}
                      {project.sprint_count} sprints
                    </span>
                    <span className="tabular-nums text-ink">
                      {project.progress_percent.toFixed(0)}%
                    </span>
                  </div>
                  <GrowBar value={project.progress_percent} tone="accent" delay={index * 60} />
                </div>
              </Link>
            </Reveal>
          ))}
        </div>
      )}
    </AppShell>
  );
}
