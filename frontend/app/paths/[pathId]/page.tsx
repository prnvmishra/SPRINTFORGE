"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Reveal } from "@/components/motion";
import { Badge, EmptyState, Loader } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { CourseSummary, PathDetail } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

export default function PathDetailPage() {
  const pathId = String(useParams().pathId ?? "");

  const path = useQuery({
    queryKey: ["path", pathId],
    queryFn: () => api<PathDetail>(`/paths/${pathId}`),
    enabled: Boolean(pathId),
  });

  if (path.isLoading) {
    return (
      <AppShell>
        <Loader label="Loading path" />
      </AppShell>
    );
  }

  if (path.isError || !path.data) {
    return (
      <AppShell>
        <EmptyState
          title="Path not found"
          description={path.error ? errorMessage(path.error) : "This path does not exist."}
        />
      </AppShell>
    );
  }

  const detail = path.data;

  return (
    <AppShell>
      <Link href="/paths" className="link font-mono text-[10px] uppercase tracking-[0.1em]">
        ← All paths
      </Link>

      <PageHeader
        className="mt-4"
        eyebrow="Career path"
        title={detail.label}
        meta={
          <div className="max-w-2xl space-y-2">
            <p className="text-[12px] leading-relaxed text-muted">{detail.blurb}</p>
            <p className="font-mono text-[10px] text-faint">
              {detail.progress.courses_completed}/{detail.progress.courses_total} courses complete ·{" "}
              {detail.progress.percent}% average confidence
            </p>
          </div>
        }
      />

      {!detail.available ? (
        <div className="mt-10">
          <EmptyState
            title="Curriculum not authored yet"
            description="This path is mapped but has no courses behind it. Nothing here is graded."
          />
        </div>
      ) : (
        <div className="mt-10 space-y-4">
          {detail.courses.map((course, index) => (
            <Reveal key={course.id} delay={index * 0.04}>
              <CourseRow
                course={course}
                index={index + 1}
                isNext={course.id === detail.next_course_id}
              />
            </Reveal>
          ))}
        </div>
      )}
    </AppShell>
  );
}

function CourseRow({
  course,
  index,
  isNext,
}: {
  course: CourseSummary;
  index: number;
  isNext: boolean;
}) {
  const { progress } = course;
  return (
    <Link
      href={`/paths/${course.path_id}/courses/${course.id}`}
      className="group flex flex-col gap-4 rounded border border-line bg-surface p-5 transition-colors hover:border-accent/40 sm:flex-row sm:items-center"
    >
      <span className="font-mono text-[11px] text-faint sm:w-8">
        {String(index).padStart(2, "0")}
      </span>

      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-2">
          <h2 className="text-[14px] font-medium text-ink">{course.title}</h2>
          {progress.complete ? <Badge tone="success">complete</Badge> : null}
          {isNext && !progress.complete ? <Badge tone="accent">next</Badge> : null}
        </div>
        <p className="mt-1.5 text-[11.5px] leading-relaxed text-muted">{course.blurb}</p>

        <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 font-mono text-[10px] text-faint">
          <span>
            {progress.skills_verified}/{progress.skills_total} skills verified
          </span>
          <span>{course.module_count} practice</span>
          <span>{course.test_available ? `test · ${course.test_item_count} items` : "no test yet"}</span>
          {course.has_project ? (
            <span>{course.project_started_id ? "project started" : "project"}</span>
          ) : null}
        </div>
      </div>

      <div className="sm:w-28">
        <div className="flex items-center justify-between font-mono text-[10px] text-faint sm:justify-end sm:gap-2">
          <span>{progress.percent}%</span>
        </div>
        <div className="mt-2 h-px w-full bg-line">
          <div
            className="h-px bg-accent transition-[width]"
            style={{ width: `${Math.min(progress.percent, 100)}%` }}
          />
        </div>
      </div>
    </Link>
  );
}
