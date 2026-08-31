"use client";

import Link from "next/link";

import type { LearningResource, NextAction, Recommendation } from "@/lib/types";

/** Kept in step with `components/dashboard/recommendation-card.tsx`. */
const TYPE_LABEL: Record<Recommendation["type"], string> = {
  remediation_practice: "Remediation required",
  prerequisite_practice: "Prerequisite gap",
  practice: "Recommended practice",
  ticket: "Next ticket",
  assessment: "Verification needed",
  placement: "Placement required",
  project: "New project",
};

const ACTION_LABEL: Record<Recommendation["type"], string> = {
  remediation_practice: "Start remediation",
  prerequisite_practice: "Close the gap",
  practice: "Start practice",
  ticket: "Open workspace",
  assessment: "Start verification",
  placement: "Start placement",
  project: "Create project",
};

function actionHref(action: NextAction): string {
  if (action.type === "placement") return "/placement";
  if (action.type === "ticket" && action.ticket_id) return `/workspace/${action.ticket_id}`;
  if (action.module_id) return `/practice/${action.module_id}`;
  if (action.type === "assessment") return "/assessment";
  if (action.type === "project") return "/projects/new";
  return "/practice";
}

/** Returns null when the payload lacks the id or url the target needs. */
function resourceHref(resource: LearningResource): string | null {
  switch (resource.target) {
    case "practice_module":
      return resource.module_id ? `/practice/${resource.module_id}` : null;
    case "assessment":
      return resource.skill_id ? `/assessment/${resource.skill_id}` : null;
    case "course":
      return resource.path_id && resource.course_id
        ? `/paths/${resource.path_id}/courses/${resource.course_id}`
        : null;
    case "external":
      return resource.url;
    default:
      return null;
  }
}

/**
 * The recommendation, its reason, and where the reason came from.
 *
 * The reason is produced by a deterministic routing engine — rule-based and
 * traceable — and is labelled as such rather than as model output.
 */
export function NextStepPanel({ action }: { action: NextAction }) {
  const href = actionHref(action);
  const deterministic = action.reason_source === "deterministic_routing_engine";
  const resources = action.resources.filter((resource) => resourceHref(resource) !== null);

  return (
    <section className="noise relative overflow-hidden rounded-lg border border-accent/25 bg-surface">
      <div className="grid-bg-fine absolute inset-0 opacity-60" aria-hidden />
      <span className="absolute inset-y-0 left-0 w-[2px] bg-accent" aria-hidden />

      <div className="relative p-6 sm:p-7">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-2">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inset-0 rounded-full bg-accent animate-pulse-ring" />
              <span className="relative h-1.5 w-1.5 rounded-full bg-accent" />
            </span>
            <span className="label-accent">Your next step</span>
          </span>
          <span className="hidden h-px flex-1 bg-line sm:block" />
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
            {TYPE_LABEL[action.type]}
          </span>
        </div>

        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="min-w-0">
            <h2 className="display text-display-sm text-balance text-ink">{action.title}</h2>

            <blockquote className="mt-5 border-l border-line pl-4">
              <p className="max-w-[62ch] text-[13px] leading-[1.7] text-muted">{action.reason}</p>
            </blockquote>

            <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {deterministic
                ? "reason from the deterministic routing engine · rule-based and traceable"
                : `reason source · ${action.reason_source}`}
            </p>

            {action.skill_name ? (
              <p className="mt-3 font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
                target skill <span className="text-ink">{action.skill_name}</span>
              </p>
            ) : null}
          </div>

          <div className="flex flex-none flex-wrap items-center gap-2">
            <Link href={href} className="btn-primary btn-mono px-5 py-2.5">
              {ACTION_LABEL[action.type]}
              <span aria-hidden>→</span>
            </Link>
          </div>
        </div>

        {resources.length > 0 ? (
          <div className="mt-7 border-t border-line pt-5">
            <p className="label mb-3">Materials for this step</p>
            <ul className="divide-y divide-line/70">
              {resources.map((resource, index) => {
                const resourceLink = resourceHref(resource) as string;
                const external = !resource.internal;
                return (
                  <li
                    key={`${resource.target}-${resourceLink}-${index}`}
                    className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2.5 first:pt-0"
                  >
                    <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                      {resource.kind.replace(/_/g, " ")}
                    </span>
                    {external ? (
                      <a
                        href={resourceLink}
                        target="_blank"
                        rel="noreferrer"
                        className="link text-[12.5px] text-ink"
                      >
                        {resource.title} <span aria-hidden>↗</span>
                      </a>
                    ) : (
                      <Link href={resourceLink} className="link text-[12.5px] text-ink">
                        {resource.title}
                      </Link>
                    )}
                    <span className="hidden h-px flex-1 bg-line/70 sm:block" />
                    {resource.minutes ? (
                      <span className="font-mono text-[10px] tabular-nums text-faint">
                        {resource.minutes} min
                      </span>
                    ) : null}
                  </li>
                );
              })}
            </ul>
          </div>
        ) : null}
      </div>
    </section>
  );
}
