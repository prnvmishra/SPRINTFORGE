"use client";

import { useQuery } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Loader, PanelSkeleton } from "@/components/ui/primitives";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type { DigitalTwin, GraphNode, PathSummary } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

const GOALS = [
  "Build a React Movie Ticket Booking System",
  "Become a job-ready frontend engineer",
  "Build a full-stack SaaS product",
  "Master data structures and algorithms",
  "Ship a portfolio-quality web application",
];

const LEVELS = ["beginner", "intermediate", "advanced"] as const;

export default function OnboardingPage() {
  const router = useRouter();
  const { refresh } = useAuth();
  // Nothing is pre-filled: the goal and every skill claim must come from the
  // learner. A default claim would put words in their mouth and then be graded
  // against them, which is the one thing claimed-vs-verified must never do.
  const [pathId, setPathId] = useState<string | null>(null);
  const [goal, setGoal] = useState("");
  const [experience, setExperience] = useState<(typeof LEVELS)[number]>("intermediate");
  const [claims, setClaims] = useState<Record<string, string>>({});
  const [showClaims, setShowClaims] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const paths = useQuery({
    queryKey: ["paths"],
    queryFn: () => api<{ paths: PathSummary[] }>("/paths"),
  });

  const graph = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () => api<{ nodes: GraphNode[] }>("/profile/knowledge-graph"),
    enabled: showClaims,
  });

  const nodes = graph.data?.nodes ?? [];
  const tracks = Array.from(new Set(nodes.map((node) => node.track)));
  // Unavailable paths stay visible rather than hidden: pretending they do not
  // exist is worse than saying the curriculum is not built yet.
  const orderedPaths = [...(paths.data?.paths ?? [])].sort(
    (a, b) => Number(b.available) - Number(a.available),
  );

  function toggle(skillId: string) {
    setClaims((current) => {
      const next = { ...current };
      if (next[skillId]) delete next[skillId];
      else next[skillId] = experience;
      return next;
    });
  }

  async function submit() {
    setBusy(true);
    setError(null);
    try {
      await api<DigitalTwin>("/profile/onboard", {
        method: "POST",
        body: {
          goal,
          experience_level: experience,
          claimed_skills: claims,
          path_id: pathId,
        },
      });
      await refresh();
      router.push("/placement");
    } catch (submitError) {
      setError(errorMessage(submitError));
    } finally {
      setBusy(false);
    }
  }

  const claimCount = Object.keys(claims).length;

  return (
    <AppShell>
      <div className="mx-auto max-w-[880px]">
        {/* Step indicator */}
        <div className="flex items-center gap-3">
          <span className="label-accent">step 01 · what you want</span>
          <span className="h-px w-8 bg-accent/50" />
          <span className="label">step 02 · what you can prove</span>
          <span className="h-px flex-1 bg-line" />
        </div>

        <h1 className="display mt-8 text-display-md text-balance text-ink">
          What do you want to learn?
        </h1>
        <p className="mt-5 max-w-[62ch] text-[13px] leading-[1.75] text-muted">
          Tell us the direction. Next we run a short graded check to find out what you already
          know, and then we point you at the exact course to start — not a video library to guess
          your way through.
        </p>

        {/* ------------------------------------------------------------ path */}
        <Section
          index="01"
          title="Career path"
          hint="Decides what we check you on, and which courses you get."
        >
          {paths.isLoading ? (
            <PanelSkeleton lines={4} />
          ) : (
            <div className="grid gap-3 sm:grid-cols-2">
              {orderedPaths.map((path) => {
                const active = pathId === path.id;
                return (
                  <button
                    key={path.id}
                    onClick={() => path.available && setPathId(path.id)}
                    disabled={!path.available}
                    aria-pressed={active}
                    className={cn(
                      "rounded border p-4 text-left transition-colors duration-200",
                      !path.available
                        ? "cursor-not-allowed border-line opacity-55"
                        : active
                          ? "border-accent bg-accent/[0.06]"
                          : "border-line hover:border-line-strong hover:bg-elevated",
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <span className="text-[12.5px] font-medium text-ink">{path.label}</span>
                      {path.available ? (
                        <Badge tone="accent">{path.course_count}</Badge>
                      ) : (
                        <Badge>soon</Badge>
                      )}
                    </div>
                    <span className="mt-1.5 block text-[11.5px] leading-relaxed text-muted">
                      {path.tagline}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </Section>

        {/* ------------------------------------------------------------ goal */}
        <Section index="02" title="Learning goal" hint="Anchors your project plan and routing.">
          <div className="space-y-px">
            {GOALS.map((option) => (
              <button
                key={option}
                onClick={() => setGoal(option)}
                aria-pressed={goal === option}
                className={cn(
                  "flex w-full items-center gap-3 border-l-2 px-4 py-3 text-left transition-colors duration-200",
                  goal === option
                    ? "border-accent bg-accent/[0.06]"
                    : "border-line hover:border-line-strong hover:bg-elevated",
                )}
              >
                <span
                  className={cn(
                    "h-1 w-1 flex-none rounded-full transition-colors",
                    goal === option ? "bg-accent" : "bg-line-strong",
                  )}
                />
                <span
                  className={cn("text-[13px]", goal === option ? "text-ink" : "text-muted")}
                >
                  {option}
                </span>
              </button>
            ))}
          </div>

          <div className="mt-5">
            <label htmlFor="custom-goal" className="label mb-2 block">
              or write your own
            </label>
            <input
              id="custom-goal"
              className="input"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
              placeholder="Build a movie ticket booking system with React"
            />
          </div>
        </Section>

        {/* ------------------------------------------------------ experience */}
        <Section
          index="03"
          title="How much do you think you know?"
          hint="Only sets the difficulty your first question starts at. The check decides the rest."
        >
          <div className="flex gap-px overflow-hidden rounded border border-line bg-line">
            {LEVELS.map((level) => (
              <button
                key={level}
                onClick={() => setExperience(level)}
                aria-pressed={experience === level}
                className={cn("seg py-3", experience === level ? "seg-on" : "seg-off")}
              >
                {level}
              </button>
            ))}
          </div>
        </Section>

        {/* ---------------------------------------------------------- claims */}
        {/* Optional on purpose. Placement produces the evidence; a long claim
            grid up front is friction that changes almost nothing. */}
        <section className="mt-12 border-t border-line pt-7">
          <div className="flex flex-wrap items-baseline justify-between gap-4">
            <div className="flex items-baseline gap-4">
              <span className="font-mono text-[10px] text-accent">04</span>
              <div>
                <h2 className="text-[13px] font-medium text-ink">
                  Skills you already claim{" "}
                  <span className="font-normal text-faint">— optional</span>
                </h2>
                <p className="mt-1 text-[11.5px] text-muted">
                  {claimCount > 0
                    ? `${claimCount} claimed · recorded, never trusted`
                    : "Skip this and the check will find out anyway."}
                </p>
              </div>
            </div>
            <button
              onClick={() => setShowClaims((value) => !value)}
              aria-expanded={showClaims}
              className="btn-quiet btn-mono text-[10px]"
            >
              {showClaims ? "Hide" : "Claim skills"}
            </button>
          </div>

          {showClaims ? (
            <div className="mt-6">
              {graph.isLoading ? (
                <div className="space-y-4">
                  <Loader label="Loading knowledge graph" />
                  <PanelSkeleton lines={4} />
                </div>
              ) : (
                <div className="space-y-6">
                  {tracks.map((track) => (
                    <div key={track}>
                      <p className="label mb-2.5">{track}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {nodes
                          .filter((node) => node.track === track)
                          .map((node) => {
                            const claimed = Boolean(claims[node.id]);
                            return (
                              <button
                                key={node.id}
                                onClick={() => toggle(node.id)}
                                aria-pressed={claimed}
                                className={cn(
                                  "group flex items-center gap-2 rounded border px-2.5 py-1.5 transition-colors duration-200",
                                  claimed
                                    ? "border-accent/50 bg-accent/[0.08]"
                                    : "border-line hover:border-line-strong hover:bg-elevated",
                                )}
                              >
                                <span
                                  className={cn(
                                    "font-mono text-[9px]",
                                    claimed ? "text-accent" : "text-faint",
                                  )}
                                >
                                  {claimed ? "✓" : "+"}
                                </span>
                                <span
                                  className={cn(
                                    "text-[11.5px]",
                                    claimed ? "text-ink" : "text-muted",
                                  )}
                                >
                                  {node.name}
                                </span>
                                <span className="font-mono text-[9px] text-faint">
                                  L{node.difficulty_weight}
                                </span>
                              </button>
                            );
                          })}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ) : null}
        </section>

        {error ? (
          <div className="mt-6">
            <Alert tone="danger">{error}</Alert>
          </div>
        ) : null}

        <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6">
          <p className="max-w-[46ch] text-[11.5px] leading-relaxed text-faint">
            Next: a few short graded checks. They decide which courses you skip and which one you
            start at — nothing on this page does.
          </p>
          <button
            onClick={() => void submit()}
            className="btn-primary btn-mono px-5 py-3"
            disabled={busy || !goal || !pathId}
          >
            {busy ? <Loader label="Saving" /> : <>Continue to placement →</>}
          </button>
        </div>
      </div>
    </AppShell>
  );
}

/** Numbered form section. Flat, with a hairline rule instead of a card. */
function Section({
  index,
  title,
  hint,
  children,
}: {
  index: string;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12 border-t border-line pt-7">
      <div className="mb-5 flex items-baseline gap-4">
        <span className="font-mono text-[10px] text-accent">{index}</span>
        <div>
          <h2 className="text-[13px] font-medium text-ink">{title}</h2>
          <p className="mt-1 text-[11.5px] text-muted">{hint}</p>
        </div>
      </div>
      {children}
    </section>
  );
}
