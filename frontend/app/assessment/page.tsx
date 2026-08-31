"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { GrowBar } from "@/components/motion";
import { Badge, Loader, Panel, PanelSkeleton, SectionTitle } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { DigitalTwin } from "@/lib/types";
import { cn, confidenceTone } from "@/lib/utils";

type AssessableSkill = {
  skill_id: string;
  skill_name: string;
  item_count: number;
  difficulty_range: [number, number];
};

export default function AssessmentIndexPage() {
  const skills = useQuery({
    queryKey: ["assessable-skills"],
    queryFn: () => api<{ skills: AssessableSkill[] }>("/assessment/skills"),
  });
  const twin = useQuery({
    queryKey: ["digital-twin"],
    queryFn: () => api<DigitalTwin>("/profile/digital-twin"),
  });

  const claimed = twin.data?.claimed_skills ?? {};
  const confidences = new Map(
    (twin.data?.verified_skills ?? []).map((skill) => [skill.skill_id, skill]),
  );

  const ordered = (skills.data?.skills ?? [])
    .slice()
    .sort((a, b) => {
      const aClaimed = claimed[a.skill_id] ? 0 : 1;
      const bClaimed = claimed[b.skill_id] ? 0 : 1;
      return aClaimed - bClaimed || a.skill_name.localeCompare(b.skill_name);
    });

  return (
    <AppShell>
      <div className="mx-auto max-w-[1000px]">
        <PageHeader
          eyebrow="Adaptive skill verification"
          title="Prove what you know"
          meta={
            <p className="max-w-[68ch] text-[12.5px] leading-[1.7] text-muted">
              These are not static quizzes. Difficulty rises when you succeed and drops when you
              fail, and a wrong answer at your frontier triggers a diagnostic follow-up designed to
              isolate the exact concept you are missing.
            </p>
          }
        />

        {/* Question types, stated as a technical inventory */}
        <div className="mt-8 flex flex-wrap items-center gap-x-1 gap-y-2 border-y border-line py-3">
          <span className="label mr-3">item types</span>
          {["mcq", "output prediction", "code debug", "code completion", "scenario"].map(
            (type) => (
              <span key={type} className="chip border-0 bg-transparent px-2 text-faint">
                {type}
              </span>
            ),
          )}
        </div>

        <Panel className="mt-8" inset={false}>
          <div className="border-b border-line px-5 py-4">
            <SectionTitle
              className="mb-0"
              eyebrow="Claims mean nothing until verified"
              title="Available skills"
            />
          </div>

          {skills.isLoading || twin.isLoading ? (
            <div className="space-y-4 p-5">
              <Loader label="Loading question banks" />
              <PanelSkeleton lines={5} />
            </div>
          ) : (
            <ul className="divide-y divide-line">
              {ordered.map((skill) => {
                const existing = confidences.get(skill.skill_id);
                const verified = Boolean(existing?.evidence.assessment_total);
                const tone = existing ? confidenceTone(existing.confidence) : null;
                return (
                  <li
                    key={skill.skill_id}
                    className="group flex flex-wrap items-center gap-4 px-5 py-4 transition-colors hover:bg-elevated/50"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <span className="text-[13px] text-ink">{skill.skill_name}</span>
                        {claimed[skill.skill_id] ? (
                          <Badge tone="accent">claimed {claimed[skill.skill_id]}</Badge>
                        ) : null}
                        {!verified ? <Badge>unverified</Badge> : null}
                      </div>
                      <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
                        {skill.item_count} items · difficulty {skill.difficulty_range[0]}–
                        {skill.difficulty_range[1]}
                      </p>
                    </div>

                    {/* Verified confidence rendered inline so the row stays a table row */}
                    <div className="w-full sm:w-40">
                      {verified && existing ? (
                        <>
                          <div className="mb-1 flex items-baseline justify-between">
                            <span className="label">confidence</span>
                            <span
                              className={cn(
                                "font-mono text-[11px] tabular-nums",
                                tone?.text,
                              )}
                            >
                              {existing.confidence.toFixed(0)}%
                            </span>
                          </div>
                          <GrowBar
                            value={existing.confidence}
                            tone={tone?.tone ?? "muted"}
                          />
                        </>
                      ) : (
                        <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                          no evidence yet
                        </p>
                      )}
                    </div>

                    <Link
                      href={`/assessment/${skill.skill_id}`}
                      className="btn-ghost btn-mono flex-none px-4 py-2"
                    >
                      {verified ? "Re-verify" : "Verify"} →
                    </Link>
                  </li>
                );
              })}
            </ul>
          )}
        </Panel>
      </div>
    </AppShell>
  );
}
