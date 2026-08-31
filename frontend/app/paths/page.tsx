"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Reveal } from "@/components/motion";
import { Badge, Loader, PanelSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { PathSummary } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

export default function PathsPage() {
  const paths = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<{ paths: PathSummary[] }>("/paths"),
  });

  const all = paths.data?.paths ?? [];
  const live = all.filter((path) => path.available);
  const planned = all.filter((path) => !path.available);

  return (
    <AppShell>
      <PageHeader
        eyebrow="Career paths"
        title="Pick the role you are building towards"
        meta={
          <p className="max-w-2xl text-[12px] leading-relaxed text-muted">
            Each path is a sequence of courses. Every course teaches a set of skills, makes you
            implement them against a judge, tests you on them, and ends in a project you ship.
          </p>
        }
      />

      {paths.isLoading ? (
        <div className="mt-10">
          <Loader label="Loading paths" />
        </div>
      ) : null}

      {paths.isError ? (
        <p className="mt-10 text-[12px] text-danger">{errorMessage(paths.error)}</p>
      ) : null}

      {live.length > 0 ? (
        <div className="mt-10 grid gap-4 lg:grid-cols-2">
          {live.map((path, index) => (
            <Reveal key={path.id} delay={index * 0.05}>
              <PathCard path={path} />
            </Reveal>
          ))}
        </div>
      ) : null}

      {planned.length > 0 ? (
        <div className="mt-14">
          <p className="label">In development</p>
          <p className="mt-2 max-w-2xl text-[11px] leading-relaxed text-faint">
            These paths are mapped but their curriculum is not authored yet. They are listed here
            rather than hidden so you know what is coming — nothing behind them is graded.
          </p>
          <div className="mt-5 grid gap-px sm:grid-cols-2 lg:grid-cols-3">
            {planned.map((path) => (
              <PlannedCard key={path.id} path={path} />
            ))}
          </div>
        </div>
      ) : null}

      {!paths.isLoading && all.length === 0 ? (
        <div className="mt-10">
          <PanelSkeleton lines={3} />
        </div>
      ) : null}
    </AppShell>
  );
}

function PathCard({ path }: { path: PathSummary }) {
  const { courses_completed: done, courses_total: total, percent } = path.progress;
  return (
    <Link
      href={`/paths/${path.id}`}
      className="group flex h-full flex-col rounded border border-line bg-surface p-6 transition-colors hover:border-accent/40"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <h2 className="text-[15px] font-medium text-ink">{path.label}</h2>
          <p className="mt-1.5 text-[12px] leading-relaxed text-muted">{path.tagline}</p>
        </div>
        <Badge tone="accent">
          {done}/{total}
        </Badge>
      </div>

      <p className="mt-4 text-[11.5px] leading-relaxed text-faint">{path.blurb}</p>

      <div className="mt-5 flex flex-wrap gap-1.5">
        {path.roles.map((role) => (
          <span
            key={role}
            className="rounded-sm border border-line px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint"
          >
            {role}
          </span>
        ))}
      </div>

      <div className="mt-auto pt-6">
        <div className="flex items-center justify-between font-mono text-[10px] text-faint">
          <span>{path.course_count} courses</span>
          <span>{percent}% confidence</span>
        </div>
        <div className="mt-2 h-px w-full bg-line">
          <div
            className="h-px bg-accent transition-[width]"
            style={{ width: `${Math.min(percent, 100)}%` }}
          />
        </div>
      </div>
    </Link>
  );
}

function PlannedCard({ path }: { path: PathSummary }) {
  return (
    <div className={cn("bg-surface p-5 ring-1 ring-line")}>
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-[13px] font-medium text-muted">{path.label}</h3>
        <span className="font-mono text-[9px] uppercase tracking-[0.1em] text-faint">soon</span>
      </div>
      <p className="mt-2 text-[11px] leading-relaxed text-faint">{path.tagline}</p>
      {path.planned_courses.length > 0 ? (
        <ul className="mt-3.5 space-y-1">
          {path.planned_courses.map((course) => (
            <li key={course} className="font-mono text-[10px] text-faint">
              · {course}
            </li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
