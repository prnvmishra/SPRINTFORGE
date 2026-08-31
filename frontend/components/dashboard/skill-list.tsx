"use client";

import { useState } from "react";

import { GrowBar } from "@/components/motion";
import { Badge } from "@/components/ui/primitives";
import type { Skill } from "@/lib/types";
import { cn, confidenceTone } from "@/lib/utils";

/**
 * Verified-skill readout. Rows behave like a technical table: dense, aligned,
 * expandable into the score's evidence rather than a second card.
 */
export function SkillList({
  skills,
  threshold,
  showExplanation = false,
  emptyMessage,
}: {
  skills: Skill[];
  threshold: number;
  showExplanation?: boolean;
  emptyMessage: string;
}) {
  if (skills.length === 0) {
    return emptyMessage ? <p className="text-[11.5px] text-faint">{emptyMessage}</p> : null;
  }

  return (
    <ul className="divide-y divide-line/70">
      {skills.map((skill, index) => (
        <SkillRow
          key={skill.skill_id}
          skill={skill}
          threshold={threshold}
          defaultOpen={showExplanation}
          delay={index * 50}
        />
      ))}
    </ul>
  );
}

function SkillRow({
  skill,
  threshold,
  defaultOpen,
  delay,
}: {
  skill: Skill;
  threshold: number;
  defaultOpen: boolean;
  delay: number;
}) {
  const [open, setOpen] = useState(defaultOpen);
  const tone = confidenceTone(skill.confidence, threshold);

  return (
    <li className="py-3 first:pt-0 last:pb-0">
      <button
        onClick={() => setOpen((value) => !value)}
        className="group w-full text-left"
        aria-expanded={open}
      >
        <div className="flex items-baseline justify-between gap-3">
          <span className="flex min-w-0 items-baseline gap-2">
            <span
              className={cn(
                "font-mono text-[9px] transition-transform duration-300",
                open ? "rotate-90 text-accent" : "text-faint group-hover:text-muted",
              )}
              aria-hidden
            >
              ▸
            </span>
            <span className="truncate text-[12.5px] text-ink">{skill.skill_name}</span>
          </span>
          <span className="flex flex-none items-baseline gap-2.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
              {skill.verified_level.replace(/_/g, " ")}
            </span>
            <span className={cn("w-9 text-right font-mono text-[12px] tabular-nums", tone.text)}>
              {skill.confidence.toFixed(0)}%
            </span>
          </span>
        </div>
        <GrowBar
          value={skill.confidence}
          threshold={threshold}
          tone={tone.tone}
          className="mt-2"
          delay={delay}
        />
      </button>

      <div
        className={cn(
          "grid overflow-hidden transition-all duration-400 ease-forge",
          open ? "mt-3 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
        )}
      >
        <div className="min-h-0">
          <div className="space-y-3 border-l border-line pl-3.5">
            <p className="text-[11.5px] leading-relaxed text-muted">{skill.explanation}</p>

            {skill.breakdown.contributions ? (
              <dl className="grid grid-cols-2 gap-x-5 gap-y-1.5">
                {Object.entries(skill.breakdown.contributions).map(([key, contribution]) => (
                  <div key={key} className="flex items-baseline justify-between gap-2">
                    <dt className="truncate font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
                      {key.replace(/_/g, " ")}
                    </dt>
                    <dd className="flex-none font-mono text-[10.5px] tabular-nums text-ink">
                      {contribution.toFixed(1)}
                      <span className="text-faint">
                        /{(skill.breakdown.effective_weights?.[key] ?? 0).toFixed(0)}
                      </span>
                    </dd>
                  </div>
                ))}
              </dl>
            ) : null}

            {skill.weak_concepts.length > 0 ? (
              <div className="flex flex-wrap gap-1.5">
                {skill.weak_concepts.map((concept) => (
                  <Badge key={concept} tone="danger">
                    {concept}
                  </Badge>
                ))}
              </div>
            ) : null}

            <p className="font-mono text-[10px] leading-relaxed text-faint">
              {skill.evidence.assessment_correct ?? 0}/{skill.evidence.assessment_total ?? 0}{" "}
              assessment · {skill.evidence.execution_passed ?? 0}/
              {skill.evidence.execution_total ?? 0} execution · hardest passed L
              {skill.evidence.hardest_difficulty_passed ?? 0}
            </p>
          </div>
        </div>
      </div>
    </li>
  );
}
