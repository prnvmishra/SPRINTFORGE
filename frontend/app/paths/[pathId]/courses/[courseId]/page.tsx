"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Reveal } from "@/components/motion";
import {
  Alert,
  Badge,
  ConfidenceBar,
  EmptyState,
  Loader,
  Panel,
  SectionTitle,
} from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { CourseDetail } from "@/lib/types";
import { cn, difficultyLabel, errorMessage } from "@/lib/utils";

export default function CourseDetailPage() {
  const params = useParams();
  const pathId = String(params.pathId ?? "");
  const courseId = String(params.courseId ?? "");

  const course = useQuery({
    queryKey: ["course", pathId, courseId],
    queryFn: () => api<CourseDetail>(`/paths/${pathId}/courses/${courseId}`),
    enabled: Boolean(pathId && courseId),
  });

  if (course.isLoading) {
    return (
      <AppShell>
        <Loader label="Loading course" />
      </AppShell>
    );
  }

  if (course.isError || !course.data) {
    return (
      <AppShell>
        <EmptyState
          title="Course not found"
          description={course.error ? errorMessage(course.error) : "This course does not exist."}
        />
      </AppShell>
    );
  }

  const detail = course.data;

  return (
    <AppShell>
      <Link
        href={`/paths/${pathId}`}
        className="link font-mono text-[10px] uppercase tracking-[0.1em]"
      >
        ← {detail.path_label}
      </Link>

      <PageHeader
        className="mt-4"
        eyebrow="Course"
        title={detail.title}
        meta={
          <div className="max-w-2xl space-y-2">
            <p className="text-[12px] leading-relaxed text-muted">{detail.blurb}</p>
            <p className="font-mono text-[10px] text-faint">
              {detail.progress.skills_verified}/{detail.progress.skills_total} skills verified ·{" "}
              {detail.progress.percent}% confidence · pass mark {detail.pass_mark}
            </p>
          </div>
        }
      />

      <div className="mt-10 grid gap-4 lg:grid-cols-[1.35fr_1fr]">
        <div className="space-y-4">
          <Reveal>
            <KnowledgePanel detail={detail} />
          </Reveal>
          <Reveal delay={0.05}>
            <PracticePanel detail={detail} />
          </Reveal>
        </div>

        <div className="space-y-4">
          <Reveal delay={0.1}>
            <TestPanel detail={detail} />
          </Reveal>
          <Reveal delay={0.15}>
            <ProjectPanel detail={detail} />
          </Reveal>
        </div>
      </div>
    </AppShell>
  );
}

/** The ordered skills this course teaches, with live confidence per skill. */
function KnowledgePanel({ detail }: { detail: CourseDetail }) {
  return (
    <Panel>
      <SectionTitle title="Knowledge" hint="Prerequisites first — this order is not arbitrary" />
      <div className="mt-5 space-y-4">
        {detail.lessons.map((lesson) => (
          <div key={lesson.skill_id} className="border-l-2 border-line pl-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="font-mono text-[10px] text-faint">
                {String(lesson.order).padStart(2, "0")}
              </span>
              <p className="text-[12.5px] text-ink">{lesson.skill_name}</p>
              {lesson.verified ? <Badge tone="success">verified</Badge> : null}
              {!lesson.unlocked ? <Badge tone="warning">locked</Badge> : null}
            </div>

            <div className="mt-2">
              <ConfidenceBar value={lesson.confidence} threshold={detail.pass_mark} />
            </div>

            {!lesson.unlocked && lesson.missing_prerequisites.length > 0 ? (
              <p className="mt-2 text-[11px] leading-relaxed text-warning">
                Needs first:{" "}
                {lesson.missing_prerequisites.map((gap) => gap.skill_name).join(", ")}
              </p>
            ) : null}

            <div className="mt-2 flex flex-wrap gap-3 font-mono text-[9.5px] text-faint">
              <Link href={`/assessment/${lesson.skill_id}`} className="link">
                take skill test
              </Link>
              <Link href={`/practice?skill=${lesson.skill_id}`} className="link">
                practice
              </Link>
              {lesson.item_count === 0 ? <span>no questions authored</span> : null}
            </div>
          </div>
        ))}
      </div>
    </Panel>
  );
}

/** Implement-immediately drills, judged the same way as everything else. */
function PracticePanel({ detail }: { detail: CourseDetail }) {
  return (
    <Panel>
      <SectionTitle
        title="Implement"
        hint={`${detail.modules.length} judged exercise${detail.modules.length === 1 ? "" : "s"}`}
      />

      {detail.modules.length === 0 ? (
        <p className="mt-5 text-[11.5px] leading-relaxed text-faint">
          No practice exercises are authored for this course yet. Its skills are still assessed by
          the course test, and the project below still applies.
        </p>
      ) : (
        <div className="mt-5 space-y-px">
          {detail.modules.map((module) => (
            <Link
              key={module.id}
              href={`/practice/${module.id}`}
              className="flex items-center gap-4 bg-surface px-4 py-3 ring-1 ring-line transition-colors hover:ring-accent/40"
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-[12px] text-ink">{module.title}</p>
                <p className="mt-1 font-mono text-[9.5px] text-faint">
                  {module.skill_name} · {difficultyLabel(module.difficulty)} ·{" "}
                  {module.estimated_minutes}m
                  {module.hidden_test_count > 0
                    ? ` · ${module.hidden_test_count} hidden tests`
                    : ""}
                </p>
              </div>
              <span className="font-mono text-[10px] text-accent">+{module.xp_reward}</span>
            </Link>
          ))}
        </div>
      )}
    </Panel>
  );
}

/**
 * The course test runs one adaptive assessment per skill and averages them.
 * The scoring rules are shown up front, before anything is started, so the
 * percentage is never a surprise after the fact.
 */
function TestPanel({ detail }: { detail: CourseDetail }) {
  const router = useRouter();
  const [showRules, setShowRules] = useState(false);
  const { test } = detail;
  const firstAvailable = test.stages.find((stage) => stage.available);

  return (
    <Panel>
      <SectionTitle title="Course test" hint={`Pass mark ${test.pass_mark}`} />

      {!test.available ? (
        <div className="mt-5">
          <Alert tone="info">{test.unavailable_reason}</Alert>
        </div>
      ) : (
        <>
          <p className="mt-5 text-[11.5px] leading-relaxed text-muted">
            One adaptive assessment per skill, {test.total_items} questions available across{" "}
            {test.stages.filter((s) => s.available).length} stages. Difficulty moves with your
            answers, so no two attempts are the same.
          </p>

          <div className="mt-4 space-y-1.5">
            {test.stages.map((stage) => (
              <div
                key={stage.skill_id}
                className="flex items-center justify-between font-mono text-[10px]"
              >
                <span className={cn(stage.available ? "text-muted" : "text-faint")}>
                  {stage.skill_name}
                </span>
                <span className="text-faint">
                  {stage.available ? `${stage.item_count} items` : "not authored"}
                </span>
              </div>
            ))}
          </div>

          <button
            type="button"
            onClick={() => setShowRules((open) => !open)}
            className="btn-ghost btn-mono mt-5 w-full px-3 py-2"
          >
            {showRules ? "Hide scoring rules" : "How is this scored?"}
          </button>

          {showRules ? (
            <div className="mt-3 space-y-2 border-l-2 border-accent/40 pl-3">
              <p className="text-[11px] leading-relaxed text-muted">
                Each stage is scored as the share of questions you answer correctly, weighted by
                the difficulty you reached — clearing harder items counts for more than clearing
                many easy ones.
              </p>
              <p className="text-[11px] leading-relaxed text-muted">
                Your course percentage is the mean of the stage scores. A skill counts as verified
                once its confidence reaches {test.pass_mark}, and confidence also rises from
                practice you pass, not from the test alone.
              </p>
              <p className="text-[11px] leading-relaxed text-faint">
                You can retake any stage. Retakes draw different questions and replace the old
                score rather than averaging with it.
              </p>
            </div>
          ) : null}

          {firstAvailable ? (
            <button
              type="button"
              onClick={() => router.push(`/assessment/${firstAvailable.skill_id}`)}
              className="btn-primary btn-mono mt-4 w-full px-3 py-2"
            >
              Start with {firstAvailable.skill_name}
            </button>
          ) : null}
        </>
      )}
    </Panel>
  );
}

/** The capstone. Pre-fills the project generator from the course definition. */
function ProjectPanel({ detail }: { detail: CourseDetail }) {
  const { project } = detail;

  if (!project) {
    return (
      <Panel>
        <SectionTitle title="Project" hint="Not applicable" />
        <p className="mt-5 text-[11.5px] leading-relaxed text-faint">
          This course is graded entirely by judged problems — the solutions you submit are the
          deliverable, so there is no separate capstone.
        </p>
      </Panel>
    );
  }

  const query = new URLSearchParams({
    title: project.title,
    idea: project.idea,
    stack: project.tech_stack.join(","),
    complexity: project.complexity,
    outcome: project.desired_outcome,
  });

  return (
    <Panel>
      <SectionTitle title="Project" hint="Course capstone" />

      <p className="mt-5 text-[13px] text-ink">{project.title}</p>
      <p className="mt-2 text-[11.5px] leading-relaxed text-muted">{project.idea}</p>

      <div className="mt-4 flex flex-wrap gap-1.5">
        {project.tech_stack.map((tech) => (
          <span
            key={tech}
            className="rounded-sm border border-line px-2 py-0.5 font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint"
          >
            {tech}
          </span>
        ))}
      </div>

      <p className="mt-4 font-mono text-[10px] text-faint">
        Outcome: {project.desired_outcome}
      </p>

      {project.existing_project_id ? (
        <Link
          href={`/projects/${project.existing_project_id}`}
          className="btn-primary btn-mono mt-5 block w-full px-3 py-2 text-center"
        >
          Continue project
        </Link>
      ) : (
        <Link
          href={`/projects/new?${query.toString()}`}
          className="btn-primary btn-mono mt-5 block w-full px-3 py-2 text-center"
        >
          Start project
        </Link>
      )}
    </Panel>
  );
}
