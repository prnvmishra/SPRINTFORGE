"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Alert, Loader, Panel, SectionTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { RoadmapResolution, RoadmapSummary } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

/**
 * "What do you want to learn?" and an honest answer to it.
 *
 * Three outcomes, and the page says which one you got rather than blurring
 * them: the subject is graded here, there is a guided roadmap for it, or we
 * have nothing and will say so instead of inventing a plan.
 */
export default function RoadmapCatalogue() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [asked, setAsked] = useState<string | null>(null);

  const catalogue = useQuery({
    queryKey: ["roadmaps"],
    queryFn: () => api<{ roadmaps: RoadmapSummary[] }>("/roadmaps"),
  });

  const resolution = useQuery({
    queryKey: ["roadmap-resolve", asked],
    queryFn: () =>
      api<RoadmapResolution>(`/roadmaps/resolve?q=${encodeURIComponent(asked ?? "")}`),
    enabled: Boolean(asked),
  });

  return (
    <AppShell>
      <PageHeader
        eyebrow="Learn something else"
        title="What do you want to learn?"
        meta={
          <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">
            Ask in your own words. If SprintForge can grade the subject, it will send you to the
            verified track. If it cannot, it will hand you an ordered roadmap instead of
            pretending.
          </p>
        }
      />

      <form
        className="mt-8 flex flex-wrap gap-2"
        onSubmit={(event) => {
          event.preventDefault();
          const trimmed = query.trim();
          if (trimmed) setAsked(trimmed);
        }}
      >
        <input
          className="input min-w-[280px] flex-1"
          placeholder="e.g. I want to learn Docker"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          aria-label="What do you want to learn?"
        />
        <button type="submit" className="btn-primary btn-mono px-6 py-3">
          Ask
        </button>
      </form>

      {asked ? (
        <div className="mt-6">
          {resolution.isLoading ? (
            <Loader label="Checking what we can teach you" />
          ) : resolution.error ? (
            <Alert tone="warning">{errorMessage(resolution.error)}</Alert>
          ) : resolution.data ? (
            <Answer data={resolution.data} onPick={(id) => router.push(`/roadmap/${id}`)} />
          ) : null}
        </div>
      ) : null}

      <Panel className="mt-10">
        <SectionTitle
          eyebrow="Guided roadmaps"
          title="Subjects we route but do not grade"
          hint="Ordered plans with links out. Finishing one does not change your confidence scores."
        />
        {catalogue.isLoading ? (
          <Loader label="Loading" />
        ) : catalogue.error ? (
          <Alert tone="warning">{errorMessage(catalogue.error)}</Alert>
        ) : (
          <ul className="grid gap-px sm:grid-cols-2 lg:grid-cols-3">
            {catalogue.data?.roadmaps.map((roadmap) => (
              <li key={roadmap.id} className="ring-1 ring-line">
                <Link
                  href={`/roadmap/${roadmap.id}`}
                  className="block h-full px-4 py-3.5 transition-colors hover:bg-surface"
                >
                  <p className="text-[13px] font-medium text-ink">{roadmap.label}</p>
                  <p className="mt-1 text-[11.5px] leading-[1.55] text-muted">{roadmap.summary}</p>
                  <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
                    {roadmap.step_count} steps
                  </p>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </Panel>
    </AppShell>
  );
}

function Answer({
  data,
  onPick,
}: {
  data: RoadmapResolution;
  onPick: (id: string) => void;
}) {
  if (data.outcome === "graded_skill") {
    return (
      <Panel>
        <SectionTitle eyebrow="We grade this" title={data.skill_name ?? "Verified skill"} />
        <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">
          This one SprintForge can actually verify — you will write code and the checks decide,
          rather than reading about it. Start with an assessment to find where you already are.
        </p>
        <div className="mt-4 flex flex-wrap gap-2">
          <Link
            href={`/assessment/${data.skill_id}`}
            className="btn-primary btn-mono px-5 py-2.5"
          >
            Verify this skill
          </Link>
          <Link href="/practice" className="btn-ghost btn-mono px-5 py-2.5">
            Practise it
          </Link>
        </div>
      </Panel>
    );
  }

  if (data.outcome === "roadmap" && data.roadmap) {
    return (
      <Panel>
        <SectionTitle eyebrow="Guided roadmap" title={data.roadmap.label} />
        <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">
          {data.roadmap.summary}
        </p>
        <p className="mt-2 text-[11.5px] leading-[1.6] text-faint">{data.roadmap.disclaimer}</p>
        <button
          type="button"
          onClick={() => onPick(data.roadmap!.id)}
          className="btn-primary btn-mono mt-4 px-5 py-2.5"
        >
          Open the roadmap
        </button>
      </Panel>
    );
  }

  return (
    <Panel>
      <SectionTitle eyebrow="No match" title="We do not cover that yet" />
      <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">
        Rather than generate a plan we cannot stand behind, here is what does exist. If your
        subject is close to one of these, start there.
      </p>
      <ul className="mt-4 flex flex-wrap gap-2">
        {data.available?.map((roadmap) => (
          <li key={roadmap.id}>
            <Link href={`/roadmap/${roadmap.id}`} className="chip">
              {roadmap.label}
            </Link>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
