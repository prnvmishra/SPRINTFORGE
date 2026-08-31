"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { GrowBar } from "@/components/motion";
import type { FailureAnalysis } from "@/lib/types";
import { cn } from "@/lib/utils";

const PHASES = ["FAILED", "DIAGNOSED", "REMEDIATION", "RE-VERIFY"] as const;

/**
 * The diagnosis panel shown after a rejected submission.
 *
 * It stages itself: the verdict lands first, then the root cause, then the
 * remediation. That sequencing is the point — the learner should watch the system
 * reason rather than receive a wall of text.
 */
export function FailureAnalysisPanel({
  analysis,
  confidence,
  goalContext,
  currentModuleId,
}: {
  analysis: FailureAnalysis;
  /** Current confidence for the affected skill, after this attempt. */
  confidence: number;
  /** Why the skill matters, e.g. the active project title. */
  goalContext?: string | null;
  /** Suppresses the remediation link when it points at the module you are on. */
  currentModuleId?: string;
}) {
  const [phase, setPhase] = useState(0);

  useEffect(() => {
    const reduced =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setPhase(PHASES.length - 1);
      return;
    }
    setPhase(0);
    const timers = PHASES.map((_, index) =>
      setTimeout(() => setPhase(index), index * 520),
    );
    return () => timers.forEach(clearTimeout);
  }, [analysis.id]);

  const showRemediation =
    analysis.remediation_module_id && analysis.remediation_module_id !== currentModuleId;

  return (
    <section className="overflow-hidden rounded-lg border border-danger/25 bg-surface">
      {/* Phase rail: the state machine, visible */}
      <div className="flex items-stretch border-b border-line bg-canvas/60">
        {PHASES.map((item, index) => {
          const reached = index <= phase;
          const isCurrent = index === phase;
          return (
            <div
              key={item}
              className={cn(
                "relative flex-1 px-3 py-2.5 transition-colors duration-500",
                reached ? "text-ink" : "text-faint/60",
              )}
            >
              <span className="flex items-center gap-2">
                <span
                  className={cn(
                    "h-1 w-1 flex-none rounded-full transition-colors duration-500",
                    index === 0 && reached
                      ? "bg-danger"
                      : reached
                        ? "bg-accent"
                        : "bg-line-strong",
                    isCurrent && "animate-pulse",
                  )}
                />
                <span className="font-mono text-[9.5px] uppercase tracking-[0.12em]">
                  {item}
                </span>
              </span>
              {/* Connector that fills as the phase is reached */}
              {index < PHASES.length - 1 ? (
                <span
                  className={cn(
                    "absolute -right-px top-1/2 h-4 w-px -translate-y-1/2 transition-colors duration-500",
                    reached ? "bg-line-strong" : "bg-line",
                  )}
                  aria-hidden
                />
              ) : null}
            </div>
          );
        })}
      </div>

      <div className="space-y-5 p-5">
        <div
          className={cn(
            "transition-all duration-500 ease-forge",
            phase >= 0 ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
          )}
        >
          <p className="label">Submission failed</p>
          <p className="display mt-2 text-[19px] tracking-tight text-danger">
            {analysis.root_cause}
          </p>
        </div>

        <Row
          visible={phase >= 1}
          label="Detected skill gap"
          tone="warning"
          value={analysis.skill_name}
          extra={
            analysis.missing_concepts.length > 0 ? (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {analysis.missing_concepts.map((concept) => (
                  <span
                    key={concept}
                    className="chip border-danger/25 bg-danger/[0.06] text-danger"
                  >
                    {concept}
                  </span>
                ))}
              </div>
            ) : null
          }
        />

        <Row
          visible={phase >= 1}
          label="Why this matters"
          value={
            goalContext
              ? `Your target project — ${goalContext} — depends on this skill.`
              : analysis.explanation
          }
          muted
        />

        {goalContext ? (
          <Row visible={phase >= 2} label="Diagnosis" value={analysis.explanation} muted />
        ) : null}

        <div
          className={cn(
            "transition-all duration-500 ease-forge",
            phase >= 3 ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
          )}
        >
          <div className="mb-1.5 flex items-baseline justify-between">
            <p className="label">{analysis.skill_name} confidence</p>
            <p className="font-mono text-[11px] tabular-nums text-warning">
              {confidence.toFixed(0)}%
            </p>
          </div>
          <GrowBar value={confidence} tone="warning" />
        </div>

        {showRemediation ? (
          <div
            className={cn(
              "transition-all duration-500 ease-forge",
              phase >= 3 ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
            )}
          >
            <p className="label mb-2">Next action</p>
            <Link
              href={`/practice/${analysis.remediation_module_id}`}
              className="btn-primary btn-mono w-full py-2.5"
            >
              {analysis.remediation_title ?? "Start remediation"}
              <span aria-hidden>→</span>
            </Link>
          </div>
        ) : null}
      </div>
    </section>
  );
}

function Row({
  visible,
  label,
  value,
  extra,
  tone,
  muted = false,
}: {
  visible: boolean;
  label: string;
  value: string;
  extra?: React.ReactNode;
  tone?: "warning";
  muted?: boolean;
}) {
  return (
    <div
      className={cn(
        "border-l-2 pl-3.5 transition-all duration-500 ease-forge",
        tone === "warning" ? "border-warning/50" : "border-line",
        visible ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
      )}
    >
      <p className="label">{label}</p>
      <p
        className={cn(
          "mt-1.5 max-w-[56ch] leading-relaxed",
          muted ? "text-[12px] text-muted" : "text-[13.5px] text-ink",
          tone === "warning" && !muted && "text-warning",
        )}
      >
        {value}
      </p>
      {extra}
    </div>
  );
}
