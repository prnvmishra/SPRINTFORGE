"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Reveal } from "@/components/motion";
import { Avatar } from "@/components/ui/avatar";
import { Alert, EmptyState, Panel, PanelSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Leaderboard, LeaderboardEntry } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

const PAGE_SIZE = 25;

export default function LeaderboardPage() {
  const [offset, setOffset] = useState(0);

  const board = useQuery({
    queryKey: ["leaderboard", offset],
    queryFn: () => api<Leaderboard>(`/leaderboard?limit=${PAGE_SIZE}&offset=${offset}`),
  });

  const data = board.data;
  const entries = data?.entries ?? [];
  const me = data?.current_user ?? null;
  const mePinned = Boolean(me && !entries.some((entry) => entry.user_id === me.user_id));

  return (
    <AppShell>
      <PageHeader
        eyebrow="Standings"
        title="Leaderboard"
        meta={
          <p className="max-w-[62ch] text-[12.5px] leading-[1.7] text-muted">
            One deterministic score, computed from evidence the engine already holds. No hidden
            weighting — the formula is printed below.
          </p>
        }
        actions={
          <Link href="/profile" className="btn-ghost btn-mono px-4 py-2">
            Your twin →
          </Link>
        }
      />

      {data ? (
        <Panel className="mt-8">
          <p className="label">Scoring formula</p>
          <p className="mt-2.5 break-words font-mono text-[11.5px] leading-relaxed text-ink">
            {data.formula.expression}
          </p>
          <div className="mt-4 grid gap-px border-t border-line pt-4 sm:grid-cols-2 lg:grid-cols-4">
            {data.formula.components.map((component) => (
              <div key={component.key}>
                <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                  {component.label}
                </p>
                <p className="mt-1 font-mono text-[13px] tabular-nums text-accent">
                  {Math.round(component.weight * 100)}%
                </p>
              </div>
            ))}
          </div>
          <p className="mt-4 text-[11.5px] leading-relaxed text-faint">
            A skill counts as verified at {data.confidence_threshold}% confidence or above. Ties break
            on {data.formula.tie_break}.
          </p>
        </Panel>
      ) : null}

      {board.isLoading ? (
        <Panel className="mt-6">
          <PanelSkeleton lines={8} />
        </Panel>
      ) : board.error ? (
        <div className="mt-6">
          <Alert tone="danger" title="Leaderboard unavailable">
            {errorMessage(board.error)}
          </Alert>
        </div>
      ) : entries.length === 0 ? (
        <div className="mt-6">
          <EmptyState
            eyebrow="No standings yet"
            title="Nobody has earned a score."
            description="Scores appear as soon as learners verify skills and bank XP. Run a practice module to put yourself on the board."
            action={
              <Link href="/practice" className="btn-primary btn-mono px-4 py-2">
                Start practising →
              </Link>
            }
          />
        </div>
      ) : (
        <Reveal>
          <div className="mt-6 overflow-hidden rounded-lg border border-line">
            <div className="hidden grid-cols-[3rem_minmax(0,1fr)_4.5rem_4.5rem_4rem_3.5rem] gap-3 border-b border-line bg-elevated px-4 py-2.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint sm:grid">
              <span>Rank</span>
              <span>Learner</span>
              <span className="text-right">Score</span>
              <span className="text-right">Conf</span>
              <span className="text-right">XP</span>
              <span className="text-right">Skills</span>
            </div>

            <ul className="divide-y divide-line">
              {entries.map((entry) => (
                <Row key={entry.user_id} entry={entry} />
              ))}
            </ul>

            {mePinned && me ? (
              <div className="border-t-2 border-accent/40">
                <ul>
                  <Row entry={me} pinned />
                </ul>
              </div>
            ) : null}
          </div>

          <div className="mt-4 flex flex-wrap items-center justify-between gap-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {offset + 1}–{Math.min(offset + PAGE_SIZE, data?.total ?? 0)} of {data?.total ?? 0}
            </p>
            <div className="flex gap-2">
              <button
                className="btn-ghost btn-mono px-4 py-2"
                disabled={offset === 0}
                onClick={() => setOffset((value) => Math.max(0, value - PAGE_SIZE))}
              >
                ← Prev
              </button>
              <button
                className="btn-ghost btn-mono px-4 py-2"
                disabled={offset + PAGE_SIZE >= (data?.total ?? 0)}
                onClick={() => setOffset((value) => value + PAGE_SIZE)}
              >
                Next →
              </button>
            </div>
          </div>
        </Reveal>
      )}
    </AppShell>
  );
}

function Row({ entry, pinned = false }: { entry: LeaderboardEntry; pinned?: boolean }) {
  return (
    <li
      className={cn(
        "grid grid-cols-[2.5rem_minmax(0,1fr)_4.5rem] items-center gap-3 px-4 py-3 sm:grid-cols-[3rem_minmax(0,1fr)_4.5rem_4.5rem_4rem_3.5rem]",
        entry.is_current_user ? "bg-accent/[0.06]" : "bg-surface",
      )}
    >
      <span
        className={cn(
          "font-mono text-[12px] tabular-nums",
          entry.is_current_user ? "text-accent" : "text-faint",
        )}
      >
        {entry.rank}
      </span>

      <span className="flex min-w-0 items-center gap-2.5">
        <Avatar name={entry.name} src={entry.avatar_url} size="sm" />
        <span className="min-w-0">
          <span
            className={cn(
              "block truncate text-[12.5px]",
              entry.is_current_user ? "text-accent" : "text-ink",
            )}
          >
            {entry.name}
          </span>
          <span className="block font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint sm:hidden">
            {entry.overall_confidence.toFixed(0)}% conf · {entry.xp} XP · {entry.verified_skills} skills
          </span>
          {pinned ? (
            <span className="hidden font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint sm:block">
              your standing
            </span>
          ) : null}
        </span>
      </span>

      <span className="text-right font-mono text-[13px] tabular-nums text-ink">
        {entry.score.toFixed(1)}
      </span>
      <span className="hidden text-right font-mono text-[12px] tabular-nums text-muted sm:block">
        {entry.overall_confidence.toFixed(0)}%
      </span>
      <span className="hidden text-right font-mono text-[12px] tabular-nums text-muted sm:block">
        {entry.xp}
      </span>
      <span className="hidden text-right font-mono text-[12px] tabular-nums text-muted sm:block">
        {entry.verified_skills}
      </span>
    </li>
  );
}
