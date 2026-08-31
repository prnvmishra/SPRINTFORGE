"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { GrowBar } from "@/components/motion";
import { Loader } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Recommendation, WhyThisNext } from "@/lib/types";
import { cn } from "@/lib/utils";

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

/**
 * The single most important element on the dashboard.
 *
 * This is the product's argument: it never recommends without a reason, and the
 * reason is inspectable down to the prerequisite chain.
 */
export function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const [showChain, setShowChain] = useState(false);

  const why = useQuery({
    queryKey: ["why-this-next"],
    queryFn: () => api<WhyThisNext>("/ai/why-this-next"),
    enabled: showChain,
  });

  const href =
    recommendation.type === "placement"
      ? "/placement"
      : recommendation.type === "ticket" && recommendation.ticket_id
      ? `/workspace/${recommendation.ticket_id}`
      : recommendation.module_id
        ? `/practice/${recommendation.module_id}`
        : recommendation.type === "assessment"
          ? "/assessment"
          : recommendation.type === "project"
            ? "/projects/new"
            : "/practice";

  return (
    <section className="noise relative overflow-hidden rounded-lg border border-accent/25 bg-surface">
      <div className="grid-bg-fine absolute inset-0 opacity-60" aria-hidden />
      {/* Accent edge: the only element on the page allowed this much emphasis. */}
      <span className="absolute inset-y-0 left-0 w-[2px] bg-accent" aria-hidden />

      <div className="relative p-6 sm:p-7">
        <div className="flex flex-wrap items-center gap-3">
          <span className="flex items-center gap-2">
            <span className="relative flex h-1.5 w-1.5">
              <span className="absolute inset-0 rounded-full bg-accent animate-pulse-ring" />
              <span className="relative h-1.5 w-1.5 rounded-full bg-accent" />
            </span>
            <span className="label-accent">Why this next</span>
          </span>
          <span className="h-px flex-1 bg-line" />
          <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
            {TYPE_LABEL[recommendation.type]}
          </span>
        </div>

        <div className="mt-6 grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
          <div className="min-w-0">
            <h2 className="display text-display-sm text-balance text-ink">
              {recommendation.title}
            </h2>

            {/* The reason is quoted, because it is the engine speaking. */}
            <blockquote className="mt-5 border-l border-line pl-4">
              <p className="max-w-[62ch] text-[13px] leading-[1.7] text-muted">
                {recommendation.reason}
              </p>
            </blockquote>

            <div className="mt-5 flex flex-wrap items-center gap-x-5 gap-y-2">
              {recommendation.skill_name ? (
                <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
                  target skill{" "}
                  <span className="text-ink">{recommendation.skill_name}</span>
                </span>
              ) : null}
              {recommendation.blocked_ticket ? (
                <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-warning">
                  blocking {recommendation.blocked_ticket.key}
                </span>
              ) : null}
            </div>
          </div>

          <div className="flex flex-none flex-wrap items-center gap-2">
            <Link href={href} className="btn-primary btn-mono px-5 py-2.5">
              {ACTION_LABEL[recommendation.type]}
              <span aria-hidden>→</span>
            </Link>
            <button
              onClick={() => setShowChain((value) => !value)}
              aria-expanded={showChain}
              className="btn-ghost btn-mono px-4 py-2.5"
            >
              {showChain ? "Hide chain" : "Dependency chain"}
            </button>
          </div>
        </div>

        {/* Prerequisite chain: proof that the ordering is not arbitrary. */}
        <div
          className={cn(
            "grid overflow-hidden transition-all duration-500 ease-forge",
            showChain ? "mt-7 grid-rows-[1fr] opacity-100" : "grid-rows-[0fr] opacity-0",
          )}
        >
          <div className="min-h-0">
            <div className="border-t border-line pt-5">
              {why.isLoading ? (
                <Loader label="Routing the knowledge graph" />
              ) : why.data && why.data.dependency_chain.length > 0 ? (
                <>
                  <p className="label mb-4">Prerequisite chain</p>
                  <ol className="space-y-3.5">
                    {why.data.dependency_chain.map((node, index) => {
                      const met = node.confidence >= node.threshold;
                      return (
                        <li key={node.skill_id}>
                          <div className="flex items-baseline justify-between gap-3">
                            <span className="flex min-w-0 items-baseline gap-2.5 text-[12.5px]">
                              <span className="font-mono text-[10px] text-faint">
                                {String(index + 1).padStart(2, "0")}
                              </span>
                              <span className="truncate text-ink">{node.skill_name}</span>
                              {met ? (
                                <span className="font-mono text-[9.5px] text-success">met</span>
                              ) : null}
                            </span>
                            <span className="flex-none font-mono text-[10.5px] tabular-nums text-faint">
                              <span className={met ? "text-success" : "text-warning"}>
                                {node.confidence.toFixed(0)}%
                              </span>
                              {" / "}
                              {node.threshold}%
                            </span>
                          </div>
                          <GrowBar
                            value={node.confidence}
                            threshold={node.threshold}
                            tone={met ? "success" : "warning"}
                            className="mt-2"
                            delay={index * 70}
                          />
                        </li>
                      );
                    })}
                  </ol>
                </>
              ) : (
                <p className="text-[12px] text-muted">
                  No prerequisite chain applies to this recommendation.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
