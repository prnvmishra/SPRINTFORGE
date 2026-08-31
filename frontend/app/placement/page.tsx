"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { GrowBar } from "@/components/motion";
import {
  Alert,
  Badge,
  EmptyState,
  Loader,
  Panel,
  PanelSkeleton,
  SectionTitle,
} from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { PathSummary, PlacementProbe, PlacementState } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

const LEVEL_LABEL: Record<string, string> = {
  no_experience: "Starting from scratch",
  early_basics: "Early basics",
  intermediate: "Intermediate",
  advanced: "Advanced",
};

export default function PlacementPage() {
  const queryClient = useQueryClient();
  // Changing path is a UI decision, not server state: `/placement/start` already
  // rebuilds the plan, so there is nothing to clear first.
  const [choosingPath, setChoosingPath] = useState(false);

  const placement = useQuery({
    queryKey: ["placement"],
    queryFn: () => api<PlacementState>("/placement"),
  });

  const paths = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<{ paths: PathSummary[] }>("/paths"),
  });

  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["placement"] });
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    void queryClient.invalidateQueries({ queryKey: ["digital-twin"] });
  };

  const state = placement.data;

  return (
    <AppShell>
      <PageHeader
        eyebrow="Step 02 · placement"
        title="Let's find out where you actually stand"
        meta={
          <p className="max-w-[68ch] text-[12.5px] leading-[1.7] text-muted">
            A few short graded checks, then we tell you which courses you can skip and exactly
            which one to start. Nothing here is a video and nothing here is a certificate — the
            only thing that moves your route is what you can actually do.
          </p>
        }
        actions={
          <Link href="/dashboard" className="btn-ghost btn-mono px-4 py-2">
            Dashboard
          </Link>
        }
      />

      <div className="mt-10">
        {placement.isLoading ? (
          <div className="space-y-6">
            <Loader label="Reading your placement plan" />
            <Panel>
              <PanelSkeleton lines={5} />
            </Panel>
          </div>
        ) : placement.error ? (
          <Alert tone="danger" title="Could not load placement">
            {errorMessage(placement.error)}
          </Alert>
        ) : !state ? null : choosingPath ||
          !state.path_id ||
          state.status === "pending" ||
          state.status === "unavailable" ? (
          <ChoosePath
            paths={paths.data?.paths ?? []}
            isLoading={paths.isLoading}
            unavailableLabel={state.status === "unavailable" ? state.path_label : null}
            onDone={() => {
              setChoosingPath(false);
              refresh();
            }}
          />
        ) : state.status === "complete" && state.result ? (
          <PlacementOutcome
            state={state}
            onRetake={refresh}
            onChangePath={() => setChoosingPath(true)}
          />
        ) : (
          <ProbeRun
            state={state}
            onDone={refresh}
            onChangePath={() => setChoosingPath(true)}
          />
        )}
      </div>
    </AppShell>
  );
}

/* ------------------------------------------------------------------ step 1 */

function ChoosePath({
  paths,
  isLoading,
  unavailableLabel,
  onDone,
}: {
  paths: PathSummary[];
  isLoading: boolean;
  unavailableLabel: string | null;
  onDone: () => void;
}) {
  const [selected, setSelected] = useState<string | null>(null);

  const start = useMutation({
    mutationFn: (pathId: string) =>
      api<PlacementState>("/placement/start", { method: "POST", body: { path_id: pathId } }),
    onSuccess: onDone,
  });

  // Available paths first, and unavailable ones stay visible but unselectable —
  // hiding them would misrepresent what the platform covers.
  const ordered = [...paths].sort((a, b) => Number(b.available) - Number(a.available));

  return (
    <div>
      {unavailableLabel ? (
        <div className="mb-8">
          <Alert tone="warning" title="Nothing to assess on that path yet">
            {unavailableLabel} is registered but has no curriculum behind it, so there is nothing
            honest to grade you against. Pick a path marked available.
          </Alert>
        </div>
      ) : null}

      <SectionTitle
        eyebrow="What do you want to learn?"
        title="Pick the career path you're aiming at"
        hint="This decides what we check you on. You can change it later."
      />

      {isLoading ? (
        <PanelSkeleton lines={5} />
      ) : (
        <div className="grid gap-4 lg:grid-cols-2">
          {ordered.map((path) => {
            const active = selected === path.id;
            return (
              <button
                key={path.id}
                onClick={() => path.available && setSelected(path.id)}
                disabled={!path.available}
                aria-pressed={active}
                className={cn(
                  "rounded border p-5 text-left transition-colors duration-200",
                  !path.available
                    ? "cursor-not-allowed border-line bg-surface/40 opacity-60"
                    : active
                      ? "border-accent bg-accent/[0.06]"
                      : "border-line bg-surface hover:border-line-strong hover:bg-elevated",
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-[13px] font-medium text-ink">{path.label}</p>
                  {path.available ? (
                    <Badge tone="accent">{path.course_count} courses</Badge>
                  ) : (
                    <Badge>coming soon</Badge>
                  )}
                </div>
                <p className="mt-2 text-[12px] leading-relaxed text-muted">{path.tagline}</p>
                <div className="mt-3.5 flex flex-wrap gap-1.5">
                  {path.roles.slice(0, 3).map((role) => (
                    <Badge key={role}>{role}</Badge>
                  ))}
                </div>
              </button>
            );
          })}
        </div>
      )}

      {start.error ? (
        <div className="mt-6">
          <Alert tone="danger">{errorMessage(start.error)}</Alert>
        </div>
      ) : null}

      <div className="mt-8 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6">
        <p className="max-w-[52ch] text-[11.5px] leading-relaxed text-faint">
          Next: one short check per course on this path. Each one adapts to how you answer, and a
          weak result ends the run early instead of dragging you through the rest.
        </p>
        <button
          onClick={() => selected && start.mutate(selected)}
          disabled={!selected || start.isPending}
          className="btn-primary btn-mono px-5 py-3"
        >
          {start.isPending ? <Loader label="Building your check" /> : <>Start placement →</>}
        </button>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ step 2 */

function ProbeRun({
  state,
  onDone,
  onChangePath,
}: {
  state: PlacementState;
  onDone: () => void;
  onChangePath: () => void;
}) {
  const router = useRouter();
  const percent = state.total_probes
    ? (state.probes_completed / state.total_probes) * 100
    : 0;

  return (
    <div className="space-y-6">
      <Panel>
        <SectionTitle
          eyebrow={state.path_label ?? "Your path"}
          title="Your placement checks"
          hint={`${state.probes_completed} of ${state.total_probes} done · ${state.questions_per_probe} questions each · graded server-side`}
        />
        <GrowBar value={percent} tone="accent" />

        <ul className="mt-6 divide-y divide-line/60">
          {state.probes.map((probe, index) => (
            <ProbeRow
              key={probe.skill_id}
              probe={probe}
              index={index}
              threshold={state.confidence_threshold}
              isNext={state.next_probe?.skill_id === probe.skill_id}
              onStart={() =>
                router.push(`/assessment/${probe.skill_id}?placement=1`)
              }
            />
          ))}
        </ul>
      </Panel>

      <Panel>
        <SectionTitle
          eyebrow="Why we ask first"
          title="How this differs from a course platform"
        />
        <ul className="space-y-2.5 text-[12px] leading-relaxed text-muted">
          <li>
            <span className="text-ink">We probe the top of each course, not the bottom.</span>{" "}
            Passing means you can skip that course outright.
          </li>
          <li>
            <span className="text-ink">A bad result ends the check early.</span> Everything after a
            failed probe depends on the skill that just failed, so asking would tell us nothing.
          </li>
          <li>
            <span className="text-ink">Your self-rating is recorded, never trusted.</span> Only
            graded answers move your confidence score.
          </li>
        </ul>
        <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-line pt-5">
          <SkipButton onDone={onDone} />
          <button onClick={onChangePath} className="btn-ghost btn-mono px-4 py-2">
            Change path
          </button>
        </div>
      </Panel>
    </div>
  );
}

function ProbeRow({
  probe,
  index,
  threshold,
  isNext,
  onStart,
}: {
  probe: PlacementProbe;
  index: number;
  threshold: number;
  isNext: boolean;
  onStart: () => void;
}) {
  const done = probe.status === "complete";
  return (
    <li className={cn("py-4 first:pt-0", isNext && "-mx-5 border-l-2 border-accent px-5")}>
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="min-w-0">
          <p className="flex items-center gap-2.5">
            <span className="font-mono text-[10px] text-faint">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="text-[13px] text-ink">{probe.course_title}</span>
            {isNext ? <Badge tone="accent">next</Badge> : null}
          </p>
          <p className="mt-1.5 pl-[26px] text-[11.5px] text-muted">
            checks <span className="text-ink">{probe.skill_name}</span> ·{" "}
            {probe.questions} questions
          </p>
          {done && probe.weak_concepts.length > 0 ? (
            <div className="mt-2.5 flex flex-wrap gap-1.5 pl-[26px]">
              {probe.weak_concepts.slice(0, 3).map((concept) => (
                <Badge key={concept} tone="warning">
                  {concept}
                </Badge>
              ))}
            </div>
          ) : null}
        </div>

        <div className="flex flex-none items-center gap-4">
          {done ? (
            <span className="text-right">
              <span
                className={cn(
                  "block font-mono text-[13px] tabular-nums",
                  probe.passed ? "text-success" : "text-warning",
                )}
              >
                {(probe.confidence ?? 0).toFixed(0)}%
              </span>
              <span className="block font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
                {probe.passed ? "cleared" : `below ${threshold}%`}
              </span>
            </span>
          ) : (
            <button
              onClick={onStart}
              className={cn(
                "btn-mono px-4 py-2",
                isNext ? "btn-primary" : "btn-ghost",
              )}
            >
              {probe.status === "in_progress" ? "Resume" : "Start"} →
            </button>
          )}
        </div>
      </div>
    </li>
  );
}

/* ------------------------------------------------------------------ step 3 */

function PlacementOutcome({
  state,
  onRetake,
  onChangePath,
}: {
  state: PlacementState;
  onRetake: () => void;
  onChangePath: () => void;
}) {
  const result = state.result!;
  const start = result.starting_point;

  return (
    <div className="space-y-6">
      <section className="noise relative overflow-hidden rounded-lg border border-accent/25 bg-surface">
        <div className="grid-bg-fine absolute inset-0 opacity-60" aria-hidden />
        <span className="absolute inset-y-0 left-0 w-[2px] bg-accent" aria-hidden />
        <div className="relative p-6 sm:p-7">
          <p className="label-accent">Placement complete</p>
          <h2 className="display mt-4 text-display-sm text-balance text-ink">
            {LEVEL_LABEL[result.level] ?? result.level}
          </h2>
          <p className="mt-4 max-w-[64ch] border-l border-line pl-4 text-[13px] leading-[1.7] text-muted">
            {result.summary}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 font-mono text-[10.5px] uppercase tracking-[0.1em] text-faint">
            <span>
              <span className="text-ink">{result.probes_passed}</span>/{result.probes_graded}{" "}
              probes cleared
            </span>
            <span className="h-2.5 w-px bg-line" />
            <span>
              avg accuracy <span className="text-ink">{result.accuracy.toFixed(0)}%</span>
            </span>
            {result.stopped_early ? (
              <>
                <span className="h-2.5 w-px bg-line" />
                <span className="text-warning">ended early</span>
              </>
            ) : null}
          </div>
        </div>
      </section>

      {start ? (
        <Panel>
          <SectionTitle
            eyebrow="Your starting point"
            title={start.course_title}
            hint={start.blurb}
          />
          {start.first_skill_name ? (
            <p className="text-[12px] leading-relaxed text-muted">
              First thing you&apos;ll prove:{" "}
              <span className="text-ink">{start.first_skill_name}</span>. You implement it
              immediately — the course only advances when a judge says your code is right.
            </p>
          ) : null}
          <div className="mt-5 flex flex-wrap gap-2">
            <Link
              href={`/paths/${start.path_id}/courses/${start.course_id}`}
              className="btn-primary btn-mono px-5 py-2.5"
            >
              Open this course →
            </Link>
            {start.first_module_id ? (
              <Link
                href={`/practice/${start.first_module_id}`}
                className="btn-ghost btn-mono px-4 py-2.5"
              >
                Jump straight into the first task
              </Link>
            ) : null}
          </div>
        </Panel>
      ) : (
        <Panel>
          <EmptyState
            eyebrow="Nothing left to place you into"
            title="You cleared every probe on this path."
            description="The next honest signal is a project built under judged conditions, where gaps show up that a short check cannot find."
            action={
              <Link href="/projects/new" className="btn-primary btn-mono px-5 py-2.5">
                Start a project →
              </Link>
            }
          />
        </Panel>
      )}

      {result.skip_courses.length > 0 ? (
        <Panel>
          <SectionTitle
            eyebrow="Proved already"
            title="Courses you can skip"
            hint="Cleared the same verification bar the rest of the platform uses. Re-take any of them any time."
          />
          <ul className="divide-y divide-line/60">
            {result.skip_courses.map((course) => (
              <li
                key={course.course_id}
                className="flex items-center justify-between gap-3 py-2.5 first:pt-0"
              >
                <span className="min-w-0 truncate text-[12px] text-ink">
                  {course.course_title}
                </span>
                <Link
                  href={`/paths/${state.path_id}/courses/${course.course_id}`}
                  className="btn-quiet btn-mono flex-none text-[10px]"
                >
                  View →
                </Link>
              </li>
            ))}
          </ul>
        </Panel>
      ) : null}

      <div className="flex flex-wrap items-center gap-3 border-t border-line pt-6">
        <Link href="/dashboard" className="btn-primary btn-mono px-5 py-2.5">
          Go to dashboard →
        </Link>
        <ResetButton onDone={onRetake} label="Re-take placement" />
        <button onClick={onChangePath} className="btn-ghost btn-mono px-4 py-2">
          Change path
        </button>
      </div>
    </div>
  );
}

/* --------------------------------------------------------------- controls */

function SkipButton({ onDone }: { onDone: () => void }) {
  const skip = useMutation({
    mutationFn: () => api<PlacementState>("/placement/skip", { method: "POST" }),
    onSuccess: onDone,
  });
  return (
    <div>
      <button
        onClick={() => skip.mutate()}
        disabled={skip.isPending}
        className="btn-quiet btn-mono text-[10px]"
      >
        Skip for now
      </button>
      <p className="mt-1.5 max-w-[40ch] text-[10.5px] leading-relaxed text-faint">
        Recorded as skipped. Your route will run on guesses until something grades you.
      </p>
      {skip.error ? (
        <p className="mt-1.5 text-[10.5px] text-danger">{errorMessage(skip.error)}</p>
      ) : null}
    </div>
  );
}

function ResetButton({ onDone, label }: { onDone: () => void; label: string }) {
  const reset = useMutation({
    mutationFn: () => api<PlacementState>("/placement/reset", { method: "POST" }),
    onSuccess: onDone,
  });
  return (
    <button
      onClick={() => reset.mutate()}
      disabled={reset.isPending}
      className="btn-ghost btn-mono px-4 py-2"
    >
      {label}
    </button>
  );
}
