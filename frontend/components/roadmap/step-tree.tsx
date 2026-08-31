"use client";

import type { RoadmapResource, RoadmapStep } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * The roadmap as an indented tree with a drawn spine.
 *
 * Ordering is the content here: step 3 exists because steps 1 and 2 came first,
 * and a child is a thing you cannot skip inside its parent. A flat list of
 * links would lose exactly that, which is the only part a learner cannot get
 * from a search engine on their own.
 */

function ResourceLink({ resource }: { resource: RoadmapResource }) {
  const label =
    resource.kind === "video" ? "watch" : resource.kind === "search" ? "search" : "read";

  return (
    <a
      href={resource.url}
      target="_blank"
      rel="noreferrer noopener"
      className="group flex items-baseline gap-2 py-0.5"
    >
      <span
        className={cn(
          "font-mono text-[9px] uppercase tracking-[0.12em]",
          resource.kind === "doc" ? "text-faint" : "text-accent/80",
        )}
      >
        {label}
      </span>
      <span className="text-[11.5px] leading-[1.5] text-muted underline decoration-line underline-offset-2 group-hover:text-ink group-hover:decoration-accent">
        {resource.title}
      </span>
      <span className="font-mono text-[9.5px] text-faint">{resource.channel}</span>
    </a>
  );
}

function Step({ step, path }: { step: RoadmapStep; path: string }) {
  return (
    <li className="relative pl-5">
      {/* Spine and elbow, so nesting is legible without indentation guesswork. */}
      <span className="absolute left-0 top-0 h-full w-px bg-line" aria-hidden />
      <span className="absolute left-0 top-[0.7rem] h-px w-3 bg-line" aria-hidden />

      <div className="pb-4">
        <p className="flex items-baseline gap-2">
          <span className="font-mono text-[9.5px] tabular-nums text-faint">{path}</span>
          <span className="text-[13px] font-medium leading-[1.4] text-ink">{step.title}</span>
        </p>
        <p className="mt-1 max-w-[68ch] text-[11.5px] leading-[1.6] text-muted">{step.objective}</p>

        {step.resources.length > 0 ? (
          <div className="mt-1.5">
            {step.resources.map((resource) => (
              <ResourceLink key={resource.url} resource={resource} />
            ))}
          </div>
        ) : null}

        {step.children && step.children.length > 0 ? (
          <ol className="mt-3">
            {step.children.map((child, index) => (
              <Step key={child.title} step={child} path={`${path}.${index + 1}`} />
            ))}
          </ol>
        ) : null}
      </div>
    </li>
  );
}

export function StepTree({ steps }: { steps: RoadmapStep[] }) {
  return (
    <ol>
      {steps.map((step, index) => (
        <Step key={step.title} step={step} path={String(index + 1).padStart(2, "0")} />
      ))}
    </ol>
  );
}
