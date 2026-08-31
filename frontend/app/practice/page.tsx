"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Reveal } from "@/components/motion";
import { Badge, EmptyState, Loader, PanelSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { PracticeModuleSummary } from "@/lib/types";
import { cn, difficultyLabel } from "@/lib/utils";

const LAYER_COPY: Record<string, string> = {
  html: "CSS and JavaScript provided. Write the missing HTML.",
  css: "HTML and JavaScript provided. Write the missing CSS.",
  javascript: "HTML and CSS provided. Write the missing JavaScript.",
  react: "App structure exists. Implement the missing component logic.",
  algorithm: "Solve the problem and pass the visible and hidden cases.",
  language: "Learn the language itself. Type errors fail the submission.",
};

export default function PracticePage() {
  // useSearchParams opts the subtree out of prerendering, so it needs its own boundary.
  return (
    <Suspense
      fallback={
        <AppShell>
          <Loader label="Loading practice catalog" />
        </AppShell>
      }
    >
      <PracticeCatalog />
    </Suspense>
  );
}

function PracticeCatalog() {
  const [technology, setTechnology] = useState<string | null>(null);
  // Dashboard cards deep-link here with ?skill=… when a weak skill has no single
  // recommended module, so the learner still lands on a filtered list.
  const skillFilter = useSearchParams().get("skill");

  const counts = useQuery({
    queryKey: ["community-counts"],
    queryFn: () => api<{ counts: Record<string, number> }>("/community/counts"),
  });

  const modules = useQuery({
    queryKey: ["practice-modules"],
    queryFn: () =>
      api<{ modules: PracticeModuleSummary[]; supported_languages: string[] }>("/practice/modules"),
  });

  const all = modules.data?.modules ?? [];
  const forSkill = skillFilter ? modulesForSkill(all, skillFilter) : all;
  // A skill with no dedicated module should not produce an empty page.
  const fellBack = Boolean(skillFilter) && forSkill.length === 0;
  const scoped = fellBack ? all : forSkill;
  const technologies = Array.from(new Set(scoped.map((module) => module.technology)));
  const visible = technology
    ? scoped.filter((module) => module.technology === technology)
    : scoped;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Practice mode"
        title="Practise one layer at a time"
        meta={
          <p className="max-w-[62ch] text-[12.5px] leading-[1.7] text-muted">
            Web modules load a complete sample project with exactly one layer removed, so you write
            only the code you are practising. Language modules give you a problem statement, sample
            cases and hidden edge cases executed in a sandboxed runtime.
          </p>
        }
        actions={
          <Link href="/dashboard" className="btn-ghost btn-mono px-4 py-2">
            ← Dashboard
          </Link>
        }
      />

      {skillFilter && !modules.isLoading ? (
        <div className="mt-6 flex flex-wrap items-center gap-3 border-l-2 border-accent/60 bg-accent/[0.04] px-4 py-2.5">
          <p className="text-[12px] text-ink">
            {fellBack ? (
              <>
                No module targets that skill yet — showing the full catalog so you can pick the
                closest match.
              </>
            ) : (
              <>
                Showing practice for{" "}
                <span className="font-medium text-accent">{forSkill[0].skill_name}</span>
              </>
            )}
          </p>
          <Link
            href="/practice"
            className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-ink"
          >
            Show everything
          </Link>
        </div>
      ) : null}

      {/* Technology filter reads as a mono tag row, not a set of pill buttons. */}
      <div className="mt-8 flex flex-wrap items-center gap-x-1 gap-y-2 border-y border-line py-3">
        <span className="label mr-3">filter</span>
        <FilterChip label="All" active={technology === null} onClick={() => setTechnology(null)} />
        {technologies.map((tech) => (
          <FilterChip
            key={tech}
            label={tech}
            active={technology === tech}
            onClick={() => setTechnology(tech)}
          />
        ))}
        <span className="ml-auto font-mono text-[10px] tabular-nums text-faint">
          {visible.length} module{visible.length === 1 ? "" : "s"}
        </span>
      </div>

      {modules.isLoading ? (
        <div className="mt-8 grid gap-px sm:grid-cols-2 xl:grid-cols-3">
          {Array.from({ length: 6 }).map((_, index) => (
            <div key={index} className="bg-surface p-5 ring-1 ring-line">
              <PanelSkeleton lines={4} />
            </div>
          ))}
        </div>
      ) : visible.length === 0 ? (
        <div className="mt-8">
          <EmptyState
            eyebrow="Nothing here"
            title="No modules match this filter."
            description="Clear the filter to see the full practice catalog."
            action={
              <button onClick={() => setTechnology(null)} className="btn-ghost btn-mono px-4 py-2">
                Clear filter
              </button>
            }
          />
        </div>
      ) : (
        /* Hairline grid: the catalog reads as a single table of work, not floating cards. */
        <div className="mt-px grid gap-px sm:grid-cols-2 xl:grid-cols-3">
          {visible.map((module, index) => (
            <Reveal key={module.id} delay={Math.min(index * 35, 280)}>
              <Link
                href={`/practice/${module.id}`}
                className="group flex h-full flex-col bg-surface p-5 ring-1 ring-line transition-colors duration-200 hover:bg-elevated"
              >
                <div className="flex flex-wrap items-center gap-1.5">
                  <Badge tone="accent">{module.technology}</Badge>
                  <Badge>
                    {difficultyLabel(module.difficulty)} L{module.difficulty}
                  </Badge>
                  {module.is_remediation ? <Badge tone="warning">remediation</Badge> : null}
                </div>

                <h2 className="mt-4 text-[14px] font-medium leading-snug text-ink transition-colors group-hover:text-accent">
                  {module.title}
                </h2>
                <p className="mt-2 line-clamp-3 text-[12px] leading-relaxed text-muted">
                  {module.summary}
                </p>

                <p className="mt-3 text-[11px] leading-relaxed text-faint">
                  {LAYER_COPY[module.practice_layer] ?? ""}
                </p>

                <div className="mt-auto flex items-center justify-between gap-3 border-t border-line pt-3.5 font-mono text-[10px] uppercase tracking-[0.08em]">
                  <span className="min-w-0 truncate text-faint">
                    {module.skill_name} · {module.estimated_minutes}m
                  </span>
                  <span className="flex flex-none items-center gap-2.5">
                    <span className="text-faint">
                      {counts.data?.counts[module.id] ?? 0} posts
                    </span>
                    <span className="text-accent">+{module.xp_reward} XP</span>
                  </span>
                </div>

                {/* Hover rule: the only motion on the card. */}
                <span
                  className="mt-3 block h-px w-0 bg-accent/50 transition-all duration-500 ease-forge group-hover:w-10"
                  aria-hidden
                />
              </Link>
            </Reveal>
          ))}
        </div>
      )}
    </AppShell>
  );
}

/** Skill ids are hierarchical (`js_async` covers `js_async_error_handling`), so an
 *  exact-only match would drop the modules a weak skill actually needs. */
function modulesForSkill(modules: PracticeModuleSummary[], skillId: string) {
  const exact = modules.filter((module) => module.skill_id === skillId);
  if (exact.length > 0) return exact;
  return modules.filter(
    (module) => module.skill_id.startsWith(`${skillId}_`) || skillId.startsWith(`${module.skill_id}_`),
  );
}

function FilterChip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "rounded px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.1em] transition-colors duration-200",
        active
          ? "bg-accent/10 text-accent"
          : "text-faint hover:bg-elevated hover:text-muted",
      )}
    >
      {label}
    </button>
  );
}
