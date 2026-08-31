"use client";

import { useState } from "react";

import { Badge } from "@/components/ui/primitives";
import { CommunityPanel } from "@/components/workspace/community-panel";
import { MentorPanel } from "@/components/workspace/mentor-panel";
import { PathContextPanel } from "@/components/workspace/path-context";
import { RequirementList } from "@/components/workspace/requirement-progress";
import type { CheckResult, PracticeModule } from "@/lib/types";
import { cn, difficultyLabel } from "@/lib/utils";

/** Difficulty colour follows the same three bands the catalogue uses. */
function difficultyTone(difficulty: number): "success" | "warning" | "danger" {
  if (difficulty <= 3) return "success";
  if (difficulty <= 6) return "warning";
  return "danger";
}

/**
 * Left pane of the algorithm workspace: everything about the problem and
 * nothing about the machine.
 *
 * This is the single owner of the problem statement — the console on the right
 * shows results only, so the task is never stated twice on one screen.
 */
export function ProblemPanel({
  module,
  checks,
  failingChecks,
  getCode,
}: {
  module: PracticeModule;
  checks: CheckResult[];
  failingChecks: string[];
  getCode: () => string;
}) {
  const [tab, setTab] = useState<"description" | "mentor" | "discuss">("description");

  const tabs = [
    { id: "description", label: "Description" },
    { id: "mentor", label: "AI Mentor" },
    { id: "discuss", label: "Discuss" },
  ] as const;

  return (
    <div className="flex h-full min-h-0 flex-col bg-surface">
      <div className="flex flex-none items-stretch border-b border-line">
        {tabs.map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            aria-pressed={tab === item.id}
            className={cn(
              "relative px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.1em] transition-colors duration-200",
              tab === item.id ? "text-ink" : "text-faint hover:text-muted",
            )}
          >
            {item.label}
            <span
              className={cn(
                "absolute inset-x-0 -bottom-px h-px bg-accent transition-opacity duration-200",
                tab === item.id ? "opacity-100" : "opacity-0",
              )}
              aria-hidden
            />
          </button>
        ))}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto">
        {tab === "description" ? (
          <ProblemDescription module={module} checks={checks} />
        ) : tab === "mentor" ? (
          <div className="h-full p-4">
            <MentorPanel
              skillId={module.skill_id}
              skillName={module.skill_name}
              moduleId={module.id}
              getCode={getCode}
              failingChecks={failingChecks}
            />
          </div>
        ) : (
          <div className="p-4">
            <CommunityPanel moduleId={module.id} />
          </div>
        )}
      </div>
    </div>
  );
}

/** The statement itself: title, tags, prose, constraints, format, examples. */
function ProblemDescription({
  module,
  checks,
}: {
  module: PracticeModule;
  checks: CheckResult[];
}) {
  const tags = [module.technology, module.skill_name, module.track, module.practice_layer]
    .filter((tag): tag is string => Boolean(tag))
    .filter((tag, index, all) => all.indexOf(tag) === index);

  return (
    <div className="px-5 py-5">
      <h2 className="display text-[19px] leading-tight tracking-tight text-ink">{module.title}</h2>

      <div className="mt-3 flex flex-wrap items-center gap-1.5">
        <Badge tone={difficultyTone(module.difficulty)}>
          {difficultyLabel(module.difficulty)} · L{module.difficulty}
        </Badge>
        <Badge tone="accent">+{module.xp_reward} XP</Badge>
        <span className="font-mono text-[10px] tabular-nums text-faint">
          ~{module.estimated_minutes}m
        </span>
        {module.is_remediation ? <Badge tone="warning">remediation</Badge> : null}
      </div>

      <p className="mt-5 whitespace-pre-wrap text-[13px] leading-[1.75] text-ink/85">
        {module.problem_statement ?? module.summary}
      </p>

      {module.examples.length > 0 ? (
        <div className="mt-6 space-y-4">
          {module.examples.map((example, index) => (
            <div key={`${example.stdin}-${index}`}>
              <p className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">
                Example {index + 1}
              </p>
              <div className="mt-2 border-l-2 border-line bg-canvas/60 px-3.5 py-3">
                <IoLine term="Input" value={example.stdin.trim()} />
                <IoLine term="Output" value={example.stdout} className="mt-2" />
                {example.explanation ? (
                  <p className="mt-2.5 text-[11.5px] leading-[1.65] text-muted">
                    <span className="label mr-1.5">why</span>
                    {example.explanation}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
        </div>
      ) : null}

      {module.constraints.length > 0 ? (
        <Section title="Constraints">
          <ul className="space-y-1.5">
            {module.constraints.map((constraint) => (
              <li
                key={constraint}
                className="flex gap-2 font-mono text-[11px] leading-relaxed text-muted"
              >
                <span className="text-faint" aria-hidden>
                  ·
                </span>
                {constraint}
              </li>
            ))}
          </ul>
        </Section>
      ) : null}

      {module.input_format || module.output_format ? (
        <Section title="Input / output format">
          <pre className="whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-muted">
            {[module.input_format, module.output_format].filter(Boolean).join("\n\n")}
          </pre>
        </Section>
      ) : null}

      {module.requirements.length > 0 ? (
        <div className="mt-7 border-t border-line pt-5">
          <RequirementList
            requirements={module.requirements}
            checks={checks}
            graded={checks.length > 0}
          />
        </div>
      ) : null}

      <Section title="Topics">
        <div className="flex flex-wrap gap-1.5">
          {tags.map((tag) => (
            <span key={tag} className="chip">
              {tag}
            </span>
          ))}
        </div>
      </Section>

      {module.hidden_test_count > 0 ? (
        <Section title="How this is judged">
          <p className="text-[11.5px] leading-[1.7] text-muted">
            <span className="font-mono text-ink">Run</span> executes the sample cases above only.{" "}
            <span className="font-mono text-ink">Submit</span> additionally grades{" "}
            {module.hidden_test_count} hidden{" "}
            {module.hidden_test_count === 1 ? "case" : "cases"} covering edge conditions and input
            scale. Every one has to pass — a green Run is not enough.
          </p>
        </Section>
      ) : null}

      {/* Route context last: it explains why this problem is in front of you,
          which is context, not part of the statement. Renders nothing when the
          skill is off the learner's route. */}
      <PathContextPanel skillId={module.skill_id} className="mt-7" />
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="mt-7 border-t border-line pt-5">
      <p className="label mb-2.5">{title}</p>
      {children}
    </div>
  );
}

function IoLine({
  term,
  value,
  className,
}: {
  term: string;
  value: string;
  className?: string;
}) {
  return (
    <div className={cn("flex gap-2.5", className)}>
      <span className="w-[48px] flex-none font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
        {term}
      </span>
      <pre className="min-w-0 flex-1 whitespace-pre-wrap font-mono text-[11px] leading-relaxed text-ink">
        {value}
      </pre>
    </div>
  );
}
