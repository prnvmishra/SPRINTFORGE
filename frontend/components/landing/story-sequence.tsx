"use client";

import { Reveal, useInView } from "@/components/motion";
import { cn } from "@/lib/utils";

/**
 * The product explained as a trace rather than a paragraph: one learner's claim
 * travelling through the engine, with the system's own output at each step.
 */
const TRACE = [
  {
    actor: "USER CLAIM",
    value: "JavaScript — Intermediate",
    note: "Self-reported. Worth nothing yet.",
    tone: "neutral" as const,
  },
  {
    actor: "SPRINTFORGE VERIFIES",
    value: "Confidence 61%",
    note: "Nine adaptive items. Difficulty rose to 6, then fell back.",
    tone: "warning" as const,
  },
  {
    actor: "DETECTED GAP",
    value: "Async Error Handling",
    note: "Two failures on rejected promises. Not a syntax problem — a model problem.",
    tone: "danger" as const,
  },
  {
    actor: "ROADMAP REWRITTEN",
    value: "4 nodes re-ordered",
    note: "The graph inserts the missing prerequisite ahead of everything downstream.",
    tone: "accent" as const,
  },
];

const ROUTE = ["Async JavaScript", "API Fetching", "React Data Fetching", "Dashboard Ticket"];

export function StorySequence() {
  return (
    <div className="grid gap-x-16 gap-y-10 lg:grid-cols-[1fr_360px]">
      <ol className="relative">
        {/* Single continuous spine, so the four steps read as one trace. */}
        <span className="absolute left-[5px] top-2 h-[calc(100%-2rem)] w-px bg-line" aria-hidden />
        {TRACE.map((step, index) => (
          <TraceRow key={step.actor} step={step} index={index} />
        ))}
      </ol>

      <Reveal delay={120} className="lg:pt-2">
        <p className="label mb-4">Resulting route</p>
        <ol className="space-y-px">
          {ROUTE.map((node, index) => (
            <li
              key={node}
              className={cn(
                "flex items-center gap-3 border-l-2 py-2.5 pl-3 transition-colors",
                index === 0
                  ? "border-accent bg-accent/[0.05]"
                  : "border-line hover:border-line-strong",
              )}
            >
              <span className="font-mono text-[10px] text-faint">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                className={cn(
                  "text-[12.5px]",
                  index === 0 ? "text-accent" : "text-muted",
                )}
              >
                {node}
              </span>
              {index === 0 ? <span className="label ml-auto">next</span> : null}
            </li>
          ))}
        </ol>
        <p className="mt-4 max-w-[38ch] text-[11.5px] leading-relaxed text-faint">
          Nothing here was chosen by a content calendar. Each node is a prerequisite the engine
          can defend.
        </p>
      </Reveal>
    </div>
  );
}

function TraceRow({
  step,
  index,
}: {
  step: (typeof TRACE)[number];
  index: number;
}) {
  const { ref, inView } = useInView<HTMLLIElement>({ threshold: 0.5 });
  const tones = {
    neutral: "text-ink",
    warning: "text-warning",
    danger: "text-danger",
    accent: "text-accent",
  };
  const dots = {
    neutral: "bg-line-strong",
    warning: "bg-warning",
    danger: "bg-danger",
    accent: "bg-accent",
  };

  return (
    <li ref={ref} className="relative pb-9 pl-8 last:pb-0">
      {/* Node marker on the spine */}
      <span
        className={cn(
          "absolute left-0 top-1.5 h-[11px] w-[11px] rounded-full border-2 border-canvas transition-all duration-700 ease-forge",
          inView ? dots[step.tone] : "bg-line",
          inView ? "scale-100" : "scale-75",
        )}
        aria-hidden
      />
      <div
        className={cn(
          "transition-all duration-700 ease-forge",
          inView ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0",
        )}
        style={{ transitionDelay: `${index * 60}ms` }}
      >
        <p className="label">{step.actor}</p>
        <p
          className={cn(
            "display mt-1.5 text-display-sm",
            tones[step.tone],
          )}
        >
          {step.value}
        </p>
        <p className="mt-2 max-w-[44ch] text-[12.5px] leading-relaxed text-muted">{step.note}</p>
      </div>
    </li>
  );
}
