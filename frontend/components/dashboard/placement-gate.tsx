"use client";

import Link from "next/link";

import { GrowBar } from "@/components/motion";
import { Badge } from "@/components/ui/primitives";
import type { PlacementSummary } from "@/lib/types";

const LEVEL_LABEL: Record<string, string> = {
  no_experience: "Starting from scratch",
  early_basics: "Early basics",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

/**
 * The dashboard's placement state, in three honest shapes:
 *
 * * **required** — a full-width gate, because every number below it would be
 *   derived from a self-rating until this is done.
 * * **complete** — one line: the level and where it put you.
 * * **skipped** — a quiet nudge, never dressed up as a result.
 */
export function PlacementGate({ placement }: { placement: PlacementSummary }) {
  if (placement.required) return <Gate placement={placement} />;
  if (placement.status === "complete" && placement.result) {
    return <Placed placement={placement} />;
  }
  if (placement.status === "skipped") return <Skipped />;
  return null;
}

function Gate({ placement }: { placement: PlacementSummary }) {
  const started = placement.probes_completed > 0;
  const percent = placement.total_probes
    ? (placement.probes_completed / placement.total_probes) * 100
    : 0;

  return (
    <section className="noise relative overflow-hidden rounded-lg border border-warning/30 bg-surface">
      <span className="absolute inset-y-0 left-0 w-[2px] bg-warning" aria-hidden />
      <div className="relative p-6 sm:p-7">
        <div className="flex flex-wrap items-center gap-3">
          <span className="font-mono text-[10px] uppercase tracking-[0.14em] text-warning">
            placement required
          </span>
          <span className="h-px flex-1 bg-line" />
          {placement.total_probes ? (
            <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
              {placement.probes_completed}/{placement.total_probes} checks done
            </span>
          ) : null}
        </div>

        <h2 className="display mt-5 text-display-sm text-balance text-ink">
          {started
            ? "Finish your placement to unlock a real recommendation"
            : "First, let's find out what you already know"}
        </h2>
        <p className="mt-4 max-w-[64ch] border-l border-line pl-4 text-[13px] leading-[1.7] text-muted">
          {placement.path_label
            ? `You're aiming at ${placement.path_label}. `
            : "You haven't picked a path yet. "}
          Until something grades you, any course we suggest is only as good as your own estimate of
          your level — and that is the exact guesswork this platform exists to remove.
        </p>

        {placement.total_probes ? (
          <div className="mt-5 max-w-[380px]">
            <GrowBar value={percent} tone="accent" />
          </div>
        ) : null}

        <div className="mt-6 flex flex-wrap items-center gap-3">
          <Link href="/placement" className="btn-primary btn-mono px-5 py-2.5">
            {started ? "Continue placement" : "Start placement"} →
          </Link>
          {placement.next_probe ? (
            <span className="font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
              next up{" "}
              <span className="text-ink">{placement.next_probe.skill_name}</span> ·{" "}
              {placement.next_probe.questions} questions
            </span>
          ) : null}
        </div>
      </div>
    </section>
  );
}

function Placed({ placement }: { placement: PlacementSummary }) {
  const result = placement.result!;
  const start = result.starting_point;
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded border border-line bg-surface px-5 py-3.5">
      <Badge tone="accent">placed</Badge>
      <span className="text-[12px] text-ink">
        {LEVEL_LABEL[result.level] ?? result.level}
      </span>
      <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
        {result.probes_passed}/{result.probes_graded} checks cleared
      </span>
      {start ? (
        <Link
          href={`/paths/${start.path_id}/courses/${start.course_id}`}
          className="btn-quiet btn-mono ml-auto text-[10px]"
        >
          {start.course_title} →
        </Link>
      ) : (
        <Link href="/placement" className="btn-quiet btn-mono ml-auto text-[10px]">
          View result →
        </Link>
      )}
    </div>
  );
}

function Skipped() {
  return (
    <div className="flex flex-wrap items-center gap-x-4 gap-y-2 rounded border border-line bg-surface px-5 py-3.5">
      <Badge tone="warning">placement skipped</Badge>
      <span className="text-[12px] text-muted">
        Your route is running on claimed levels until something grades you.
      </span>
      <Link href="/placement" className="btn-quiet btn-mono ml-auto text-[10px]">
        Take it now →
      </Link>
    </div>
  );
}
