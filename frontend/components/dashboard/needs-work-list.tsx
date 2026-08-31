"use client";

import Link from "next/link";
import { useState } from "react";

import { GrowBar } from "@/components/motion";
import type { Skill } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * The "needs work" panel, written for someone who has never seen the product.
 *
 * The precise score breakdown lives on the Digital Twin page; here we answer only
 * three questions: what is weak, what does that mean, and what do I click now.
 */
export function NeedsWorkList({
  skills,
  threshold,
}: {
  skills: Skill[];
  threshold: number;
}) {
  if (skills.length === 0) {
    return (
      <p className="text-[11.5px] leading-relaxed text-faint">
        Nothing needs work right now. Keep going and we&apos;ll flag anything that slips.
      </p>
    );
  }

  return (
    <div>
      <p className="mb-4 max-w-[44ch] text-[11.5px] leading-relaxed text-muted">
        These are the skills you haven&apos;t proved yet. Fix the top one first — everything else
        gets easier.
      </p>
      <ul className="space-y-px">
        {skills.map((skill, index) => (
          <SkillCard
            key={skill.skill_id}
            skill={skill}
            threshold={threshold}
            isTop={index === 0}
            delay={index * 60}
          />
        ))}
      </ul>
    </div>
  );
}

function SkillCard({
  skill,
  threshold,
  isTop,
  delay,
}: {
  skill: Skill;
  threshold: number;
  isTop: boolean;
  delay: number;
}) {
  const [showWhy, setShowWhy] = useState(false);
  const pct = Math.max(0, Math.min(100, skill.confidence));
  const remaining = Math.max(0, Math.round(threshold - pct));
  const action = skill.next_action;

  const href =
    action?.kind === "assessment"
      ? `/assessment/${skill.skill_id}`
      : action?.module_id
        ? `/practice/${action.module_id}`
        : `/practice?skill=${skill.skill_id}`;

  return (
    <li
      className={cn(
        "border-l-2 py-4 pl-4 transition-colors duration-200",
        isTop ? "border-accent bg-accent/[0.04]" : "border-line hover:border-line-strong",
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="truncate text-[13px] font-medium text-ink">{skill.skill_name}</p>
          <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
            {remaining > 0 ? `${remaining} points from verified` : "Almost verified"}
          </p>
        </div>
        {isTop ? <span className="label-accent flex-none">start here</span> : null}
      </div>

      {/* Progress towards verified, with the goal marked so the number means something */}
      <div className="mt-3">
        <GrowBar
          value={pct}
          threshold={threshold}
          tone={pct >= threshold ? "success" : pct >= threshold * 0.6 ? "warning" : "danger"}
          delay={delay}
        />
        <div className="mt-1.5 flex justify-between font-mono text-[9.5px] tabular-nums text-faint">
          <span>you {pct.toFixed(0)}%</span>
          <span>verified at {threshold}%</span>
        </div>
      </div>

      {/* Plain-language meaning */}
      <p className="mt-3 max-w-[52ch] text-[12px] leading-[1.65] text-ink/85">
        {skill.plain_summary ?? skill.explanation}
      </p>

      {skill.weak_concepts.length > 0 ? (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {skill.weak_concepts.slice(0, 3).map((concept) => (
            <span
              key={concept}
              className="chip border-danger/25 bg-danger/[0.06] text-danger"
            >
              {concept}
            </span>
          ))}
        </div>
      ) : null}

      <div className="mt-4 flex items-center gap-3">
        <Link
          href={href}
          className={cn(
            isTop ? "btn-primary btn-mono px-4 py-2" : "btn-ghost btn-mono px-4 py-2",
          )}
        >
          {action?.label ?? "Practise this"}
          <span aria-hidden>→</span>
        </Link>
        <button
          onClick={() => setShowWhy((value) => !value)}
          aria-expanded={showWhy}
          className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-ink"
        >
          {showWhy ? "Hide details" : "Why this score?"}
        </button>
      </div>

      <div
        className={cn(
          "grid overflow-hidden transition-all duration-400 ease-forge",
          showWhy ? "mt-4 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="min-h-0">
          <div className="space-y-3 border-t border-line pt-3.5">
            <p className="label">Your score comes from four signals</p>
            <ScoreReasons skill={skill} />
            <details className="group">
              <summary className="cursor-pointer list-none font-mono text-[10px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-ink">
                Technical detail
              </summary>
              <p className="mt-2 text-[11px] leading-relaxed text-muted">{skill.explanation}</p>
            </details>
          </div>
        </div>
      </div>
    </li>
  );
}

const CHANNEL_LABELS: Record<string, string> = {
  assessment_accuracy: "Answers you got right",
  execution_success: "Code that ran correctly",
  difficulty_mastery: "Hardest task you passed",
  consistency: "How reliable you've been",
};

function ScoreReasons({ skill }: { skill: Skill }) {
  const components = skill.breakdown?.components ?? {};
  // Always show all four signals. A brand-new skill has no active channels, and an
  // empty list reads as a rendering bug rather than "you haven't started yet".
  const rows = Object.keys(CHANNEL_LABELS);
  const active: string[] = skill.breakdown?.active_channels ?? [];

  return (
    <ul className="space-y-1.5">
      {rows.map((key) => {
        const value = Math.round(components[key] ?? 0);
        const untouched = !active.includes(key);
        return (
          <li key={key} className="flex items-center gap-3">
            <span className="w-[128px] flex-none text-[11px] text-muted">
              {CHANNEL_LABELS[key] ?? key.replace(/_/g, " ")}
            </span>
            <GrowBar
              value={untouched ? 0 : value}
              tone={value >= 65 ? "success" : value >= 40 ? "warning" : "danger"}
              className="h-[3px] flex-1"
            />
            <span
              className={cn(
                "w-14 flex-none text-right font-mono text-[10px] tabular-nums",
                untouched ? "text-faint" : "text-ink",
              )}
            >
              {untouched ? "not yet" : `${value}%`}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
