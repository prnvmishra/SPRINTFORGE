"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";

import { AppShell, PageHeader } from "@/components/app-shell";
import { AdaptationFeed } from "@/components/dashboard/adaptation-feed";
import { SkillList } from "@/components/dashboard/skill-list";
import { Counter, GrowBar, Reveal } from "@/components/motion";
import { KnowledgeGraph } from "@/components/profile/knowledge-graph";
import { Avatar } from "@/components/ui/avatar";
import {
  Alert,
  Badge,
  EmptyState,
  Loader,
  Panel,
  PanelSkeleton,
  SectionTitle,
} from "@/components/ui/primitives";
import { useAuth } from "@/hooks/use-auth";
import { api } from "@/lib/api";
import type {
  Adaptations,
  DigitalTwin,
  FailureAnalysis,
  GraphNode,
  RewardSummary,
} from "@/lib/types";
import { cn, errorMessage, relativeTime } from "@/lib/utils";

type ActivityEvent = {
  id: string;
  event_type: string;
  title: string;
  detail: string | null;
  created_at: string;
};

export default function ProfilePage() {
  const { user } = useAuth();

  const twin = useQuery({
    queryKey: ["digital-twin"],
    queryFn: () => api<DigitalTwin>("/profile/digital-twin"),
  });
  const graph = useQuery({
    queryKey: ["knowledge-graph"],
    queryFn: () =>
      api<{ confidence_threshold: number; nodes: GraphNode[] }>("/profile/knowledge-graph"),
  });
  const rewards = useQuery({
    queryKey: ["rewards"],
    queryFn: () => api<RewardSummary>("/rewards/me"),
  });
  const failures = useQuery({
    queryKey: ["failures"],
    queryFn: () => api<{ analyses: FailureAnalysis[] }>("/failures/me"),
  });
  const adaptations = useQuery({
    queryKey: ["adaptations"],
    queryFn: () => api<Adaptations>("/adaptations"),
  });
  const activity = useQuery({
    queryKey: ["activity"],
    queryFn: () => api<{ events: ActivityEvent[] }>("/profile/activity"),
  });

  const threshold = graph.data?.confidence_threshold ?? 65;
  const data = twin.data;
  const openGaps = (failures.data?.analyses ?? []).filter((a) => !a.resolved).slice(0, 5);

  return (
    <AppShell wide>
      <PageHeader
        eyebrow="Learning digital twin"
        title={`${user?.name?.split(" ")[0] ?? "Your"} — performance profile`}
        meta={
          <p className="max-w-[64ch] text-[12.5px] leading-[1.7] text-muted">
            A persistent model of what you can actually do, updated after every assessment,
            practice submission and ticket review.
          </p>
        }
        actions={
          <Link href="/assessment" className="btn-ghost btn-mono px-4 py-2">
            Verify more skills →
          </Link>
        }
      />

      {twin.isLoading || !data ? (
        <div className="mt-10 space-y-6">
          <Loader label="Reading digital twin" />
          <Panel>
            <PanelSkeleton lines={5} />
          </Panel>
        </div>
      ) : (
        <>
          {/* ------------------------------------------- headline confidence */}
          <section className="noise relative mt-10 overflow-hidden rounded-lg border border-line bg-surface">
            <div className="grid-bg absolute inset-0 opacity-60" aria-hidden />
            <div className="relative grid gap-10 p-7 lg:grid-cols-[auto_1fr] lg:items-center sm:p-9">
              <div>
                <div className="mb-6 flex items-center gap-4">
                  <Avatar name={user?.name ?? "You"} src={user?.avatar_url} size="lg" />
                  <div className="min-w-0">
                    <p className="truncate text-[13px] text-ink">{user?.name}</p>
                    {user?.bio ? (
                      <p className="mt-1 max-w-[40ch] text-[11.5px] leading-relaxed text-muted">
                        {user.bio}
                      </p>
                    ) : (
                      <Link
                        href="/settings"
                        className="mt-1 inline-block font-mono text-[10px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-accent"
                      >
                        Add a photo and bio →
                      </Link>
                    )}
                  </div>
                </div>
                <p className="label">SprintForge confidence</p>
                <p className="display mt-3 text-display-lg leading-none text-accent">
                  <Counter value={data.overall_confidence} />
                  <span className="text-[0.35em] text-faint">%</span>
                </p>
                <div className="mt-5 max-w-[320px]">
                  <GrowBar
                    value={data.overall_confidence}
                    threshold={threshold}
                    tone="accent"
                  />
                  <p className="mt-2 font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
                    difficulty-weighted across {data.verified_skills.length} tracked skills ·
                    verified at {threshold}%
                  </p>
                </div>
              </div>

              {/* Performance readout, laid out as an instrument panel */}
              <div className="grid grid-cols-2 gap-px bg-line sm:grid-cols-4">
                <Stat label="Level" value={String(data.level)} />
                <Stat label="XP" value={String(data.xp)} />
                <Stat label="Streak" value={`${data.streak_days}d`} />
                <Stat
                  label="Consistency"
                  value={`${data.consistency_score.toFixed(0)}%`}
                  tone={data.consistency_score >= 65 ? "success" : "warning"}
                />
                <Stat
                  label="Velocity"
                  value={`${data.learning_velocity.toFixed(1)}/d`}
                />
                <Stat
                  label="Avg completion"
                  value={
                    data.avg_completion_seconds > 0
                      ? `${Math.round(data.avg_completion_seconds / 60)}m`
                      : "—"
                  }
                />
                <Stat label="Projects done" value={String(data.completed_projects)} />
                <Stat label="Preferred L" value={String(data.preferred_difficulty)} />
              </div>
            </div>
          </section>

          {/* ---------------------------------------------------- skill route */}
          {/* Promoted directly under the headline: "what do I do next" outranks
              the historical panels below it. Full width, not columned — the
              dependency layout needs every pixel before it starts scrolling. */}
          <Panel className="mt-8" inset={false}>
            <div className="border-b border-line px-5 py-4">
              <SectionTitle
                className="mb-0"
                eyebrow="Where you are, what's next, what's in the way"
                title="Your skill route"
                hint="Ordered by what each skill depends on. Earlier stages are the groundwork for later ones."
              />
            </div>
            {graph.isLoading ? (
              <div className="p-5">
                <Loader label="Skill graph routing" />
              </div>
            ) : graph.isError ? (
              <div className="p-5">
                <Alert tone="danger" title="Route unavailable">
                  {errorMessage(graph.error)}
                </Alert>
              </div>
            ) : (graph.data?.nodes ?? []).length === 0 ? (
              <div className="p-5">
                <EmptyState
                  eyebrow="Nothing mapped yet"
                  title="No skills on your route"
                  description="Once skills are tracked against your profile, this becomes the map of what to prove and in what order."
                  action={
                    <Link href="/assessment" className="btn-primary btn-mono px-4 py-2">
                      Verify a skill →
                    </Link>
                  }
                />
              </div>
            ) : (
              <KnowledgeGraph nodes={graph.data?.nodes ?? []} threshold={threshold} />
            )}
          </Panel>

          <div className="mt-6 grid min-w-0 gap-6 xl:grid-cols-[minmax(0,1.55fr)_minmax(0,1fr)]">
            <div className="min-w-0 space-y-6">
              {/* -------------------------------------- skill-by-skill table */}
              <Panel>
                <SectionTitle
                  eyebrow="Expand a skill for its evidence"
                  title="Skill-by-skill confidence"
                />
                <SkillList
                  skills={data.verified_skills}
                  threshold={threshold}
                  emptyMessage="No skills tracked yet. Claim some in onboarding, then verify them."
                />
              </Panel>

              {/* Moved off the dashboard: a diagnosed gap is a fact about your
                  history, and the dashboard is only about the next action. */}
              {openGaps.length > 0 ? (
                <Panel>
                  <SectionTitle
                    eyebrow="Diagnosed from real failures"
                    title="Open conceptual gaps"
                    hint="Detected by the evaluator, never self-reported"
                  />
                  <ul className="space-y-4">
                    {openGaps.map((gap) => (
                      <li key={gap.id} className="border-l-2 border-warning/50 pl-4">
                        <div className="flex flex-wrap items-center gap-1.5">
                          <Badge tone="warning">{gap.skill_name}</Badge>
                          {gap.missing_concepts.slice(0, 3).map((concept) => (
                            <Badge key={concept}>{concept}</Badge>
                          ))}
                        </div>
                        <p className="mt-2.5 max-w-[64ch] text-[12px] leading-relaxed text-ink/90">
                          {gap.explanation}
                        </p>
                        {gap.remediation_module_id ? (
                          <Link
                            href={`/practice/${gap.remediation_module_id}`}
                            className="btn-ghost btn-mono mt-3 px-4 py-2"
                          >
                            {gap.remediation_title} →
                          </Link>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                </Panel>
              ) : null}

              <AdaptationFeed
                data={adaptations.data}
                isLoading={adaptations.isLoading}
                errorText={adaptations.error ? errorMessage(adaptations.error) : null}
              />

              <Panel>
                <SectionTitle
                  eyebrow="System log"
                  title="Activity"
                  hint="Every event that changed this twin"
                />
                {activity.isLoading ? (
                  <Loader label="Loading activity" />
                ) : (activity.data?.events ?? []).length === 0 ? (
                  <p className="text-[11.5px] text-faint">Nothing recorded yet.</p>
                ) : (
                  <ul className="divide-y divide-line/60">
                    {(activity.data?.events ?? []).map((event) => (
                      <li key={event.id} className="flex gap-3 py-2.5 first:pt-0">
                        <span
                          className={cn(
                            "mt-[7px] h-1 w-1 flex-none rounded-full",
                            event.event_type.includes("failed")
                              ? "bg-danger"
                              : event.event_type.includes("passed") ||
                                  event.event_type.includes("completed")
                                ? "bg-success"
                                : "bg-accent",
                          )}
                        />
                        <span className="min-w-0 flex-1">
                          <span className="block text-[12px] text-ink">{event.title}</span>
                          {event.detail ? (
                            <span className="mt-0.5 block text-[11px] leading-relaxed text-muted">
                              {event.detail}
                            </span>
                          ) : null}
                        </span>
                        <span className="flex-none font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
                          {relativeTime(event.created_at)}
                        </span>
                      </li>
                    ))}
                  </ul>
                )}
              </Panel>
            </div>

            {/* ----------------------------------------------------- side */}
            <div className="min-w-0 space-y-6">
              <Reveal>
                <Panel>
                  <SectionTitle
                    eyebrow="Claims are never trusted"
                    title="Claimed vs verified"
                    hint={
                      Object.keys(data.claimed_skills).length > 0
                        ? `${
                            Object.entries(data.claimed_skills).filter(
                              ([skillId, level]) =>
                                data.verified_skills.find((s) => s.skill_id === skillId)
                                  ?.verified_level === level,
                            ).length
                          } of ${
                            Object.keys(data.claimed_skills).length
                          } claims hold up under assessment. The rest are what your route leads with.`
                        : undefined
                    }
                  />
                  {Object.keys(data.claimed_skills).length === 0 ? (
                    <p className="text-[11.5px] text-faint">No skills claimed.</p>
                  ) : (
                    <ul className="divide-y divide-line/60">
                      {Object.entries(data.claimed_skills).map(([skillId, level]) => {
                        const verified = data.verified_skills.find(
                          (s) => s.skill_id === skillId,
                        );
                        const matches = verified?.verified_level === level;
                        return (
                          <li
                            key={skillId}
                            className="flex items-baseline justify-between gap-3 py-2.5 first:pt-0"
                          >
                            <span className="min-w-0 truncate text-[12px] text-ink">
                              {verified?.skill_name ?? skillId}
                            </span>
                            <span className="flex flex-none items-center gap-1.5 font-mono text-[9.5px] uppercase tracking-[0.08em]">
                              <span className="text-faint">{level}</span>
                              <span className="text-line-strong">→</span>
                              <span className={matches ? "text-success" : "text-warning"}>
                                <span aria-hidden className="mr-1">
                                  {matches ? "●" : "○"}
                                </span>
                                {verified?.verified_level.replace(/_/g, " ") ?? "unverified"}
                              </span>
                            </span>
                          </li>
                        );
                      })}
                    </ul>
                  )}
                </Panel>
              </Reveal>

              <Reveal delay={60}>
                <Panel>
                  <SectionTitle
                    eyebrow="Missed more than once"
                    title="Repeated mistakes"
                  />
                  {Object.keys(data.repeated_mistakes).length === 0 ? (
                    <p className="text-[11.5px] text-faint">No repeated mistakes recorded.</p>
                  ) : (
                    <ul className="space-y-2.5">
                      {Object.entries(data.repeated_mistakes)
                        .sort(([, a], [, b]) => b - a)
                        .map(([concept, count]) => (
                          <li key={concept} className="flex items-center gap-3">
                            <span className="min-w-0 flex-1 truncate text-[11.5px] text-muted">
                              {concept}
                            </span>
                            {/* Repeats as tally marks: reads at a glance */}
                            <span className="flex flex-none items-center gap-0.5">
                              {Array.from({ length: Math.min(count, 5) }).map((_, index) => (
                                <span
                                  key={index}
                                  className={cn(
                                    "h-2.5 w-px",
                                    count > 1 ? "bg-danger" : "bg-warning",
                                  )}
                                />
                              ))}
                            </span>
                            <span
                              className={cn(
                                "w-6 flex-none text-right font-mono text-[10px] tabular-nums",
                                count > 1 ? "text-danger" : "text-muted",
                              )}
                            >
                              ×{count}
                            </span>
                          </li>
                        ))}
                    </ul>
                  )}
                </Panel>
              </Reveal>

              <Reveal delay={120}>
                <Panel>
                  <SectionTitle eyebrow="Diagnosed root causes" title="Failure history" />
                  {failures.isLoading ? (
                    <Loader label="Loading diagnoses" />
                  ) : (failures.data?.analyses ?? []).length === 0 ? (
                    <p className="text-[11.5px] text-faint">No failures analysed yet.</p>
                  ) : (
                    <ul className="space-y-3.5">
                      {(failures.data?.analyses ?? []).slice(0, 8).map((analysis) => (
                        <li
                          key={analysis.id}
                          className={cn(
                            "border-l-2 pl-3",
                            analysis.resolved ? "border-success/40" : "border-warning/50",
                          )}
                        >
                          <div className="flex items-baseline justify-between gap-3">
                            <span className="min-w-0 truncate text-[12px] text-ink">
                              {analysis.skill_name}
                            </span>
                            <span
                              className={cn(
                                "flex-none font-mono text-[9.5px] uppercase tracking-[0.1em]",
                                analysis.resolved ? "text-success" : "text-warning",
                              )}
                            >
                              {analysis.resolved ? "resolved" : "open"}
                            </span>
                          </div>
                          <p className="mt-1 text-[11px] leading-relaxed text-muted">
                            {analysis.root_cause}
                          </p>
                          <p className="mt-1 font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
                            {relativeTime(analysis.created_at)} · {analysis.source_type}
                          </p>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
              </Reveal>

              <Reveal delay={180}>
                <Panel>
                  <SectionTitle eyebrow="Earned, never granted" title="Reward history" />
                  {(rewards.data?.recent ?? []).length === 0 ? (
                    <p className="text-[11.5px] text-faint">No XP earned yet.</p>
                  ) : (
                    <ul className="divide-y divide-line/60">
                      {(rewards.data?.recent ?? []).map((reward) => (
                        <li
                          key={reward.id}
                          className="flex items-baseline gap-3 py-2 first:pt-0"
                        >
                          <span className="font-mono text-[11px] tabular-nums text-accent">
                            +{reward.amount}
                          </span>
                          <span className="min-w-0 flex-1 truncate text-[11.5px] text-muted">
                            {reward.reason}
                          </span>
                        </li>
                      ))}
                    </ul>
                  )}
                </Panel>
              </Reveal>
            </div>
          </div>

        </>
      )}
    </AppShell>
  );
}

function Stat({
  label,
  value,
  tone,
}: {
  label: string;
  value: string;
  tone?: "success" | "warning";
}) {
  return (
    <div className="bg-surface/80 p-4">
      <p className="label">{label}</p>
      <p
        className={cn(
          "display mt-1.5 text-[19px] leading-none tracking-tight",
          tone === "success" ? "text-success" : tone === "warning" ? "text-warning" : "text-ink",
        )}
      >
        {value}
      </p>
    </div>
  );
}
