"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell, PageHeader } from "@/components/app-shell";
import { StepTree } from "@/components/roadmap/step-tree";
import { GrowBar } from "@/components/motion";
import { Alert, Loader, Panel, SectionTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Roadmap } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

export default function RoadmapPage() {
  const params = useParams<{ roadmapId: string }>();
  const roadmapId = params.roadmapId;

  const { data, isLoading, error } = useQuery({
    queryKey: ["roadmap", roadmapId],
    queryFn: () => api<Roadmap>(`/roadmaps/${roadmapId}`),
  });

  if (isLoading) {
    return (
      <AppShell>
        <div className="grid min-h-[40vh] place-items-center">
          <Loader label="Loading roadmap" />
        </div>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell>
        <Alert tone="warning">{error ? errorMessage(error) : "Roadmap not found."}</Alert>
        <Link href="/roadmap" className="link mt-4 inline-block font-mono text-[11px] uppercase">
          All roadmaps
        </Link>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <PageHeader
        eyebrow="Guided roadmap"
        title={data.label}
        meta={
          <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">{data.summary}</p>
        }
        actions={
          <Link href="/roadmap" className="btn-ghost btn-mono px-4 py-2">
            All roadmaps
          </Link>
        }
      />

      {/* The distinction this whole feature rests on, said before anything else
          so it cannot be mistaken for a graded track. */}
      <div className="mt-6">
        <Alert tone="info">{data.disclaimer}</Alert>
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-[1fr_320px]">
        <div className="space-y-6">
          <Panel>
            <SectionTitle eyebrow="Why bother" title="What this unlocks for you" />
            <p className="max-w-[70ch] text-[12.5px] leading-[1.75] text-muted">{data.why}</p>
          </Panel>

          <Panel>
            <SectionTitle
              eyebrow="Step by step"
              title="Learn these in order"
              hint="Indented items sit inside the step above them."
            />
            <StepTree steps={data.steps} />
          </Panel>
        </div>

        <aside className="space-y-6">
          {data.course ? (
            <Panel>
              <SectionTitle eyebrow="One long video" title="Full course" />
              <a
                href={data.course.url}
                target="_blank"
                rel="noreferrer noopener"
                className="block"
              >
                <p className="text-[12.5px] leading-[1.5] text-ink underline decoration-line underline-offset-2 hover:decoration-accent">
                  {data.course.title}
                </p>
                <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                  {data.course.channel}
                </p>
              </a>
              <p className="mt-3 text-[11px] leading-[1.6] text-faint">
                Useful as a single pass through the subject. The steps on the left are the order
                to actually work in.
              </p>
            </Panel>
          ) : null}

          <Panel>
            <SectionTitle
              eyebrow="Before you start"
              title="What this builds on"
              hint={
                data.prerequisites.length === 0
                  ? undefined
                  : "Measured against your own verified confidence."
              }
            />
            {data.prerequisites.length === 0 ? (
              <p className="text-[11.5px] leading-[1.6] text-muted">
                Nothing. You can start this today.
              </p>
            ) : (
              <ul className="space-y-3">
                {data.prerequisites.map((prerequisite) => (
                  <li key={prerequisite.skill_id}>
                    <div className="flex items-baseline justify-between gap-3">
                      <span className="text-[12px] text-ink">{prerequisite.skill_name}</span>
                      <span
                        className={cnConfidence(prerequisite.verified, prerequisite.confidence)}
                      >
                        {prerequisite.confidence === null
                          ? "not measured"
                          : `${prerequisite.confidence.toFixed(0)}%`}
                      </span>
                    </div>
                    <GrowBar value={prerequisite.confidence ?? 0} className="mt-1.5" />
                  </li>
                ))}
              </ul>
            )}

            {data.unmet_prerequisites.length > 0 ? (
              <p className="mt-4 text-[11px] leading-[1.6] text-warning">
                You have not verified{" "}
                {data.unmet_prerequisites.map((p) => p.skill_name).join(", ")} yet. This roadmap
                will make more sense afterwards, and those are things SprintForge can actually
                grade for you.
              </p>
            ) : null}
          </Panel>
        </aside>
      </div>
    </AppShell>
  );
}

function cnConfidence(verified: boolean, confidence: number | null) {
  const base = "font-mono text-[10.5px] uppercase tracking-[0.08em]";
  if (confidence === null) return `${base} text-faint`;
  return verified ? `${base} text-accent` : `${base} text-warning`;
}
