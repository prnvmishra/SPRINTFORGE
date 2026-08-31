"use client";

import Link from "next/link";
import { useMemo, useState } from "react";

import { GrowBar } from "@/components/motion";
import type { GraphNode, PrerequisiteGap } from "@/lib/types";
import { cn, confidenceTone, difficultyLabel } from "@/lib/utils";

/**
 * The Skill Route.
 *
 * Same dependency-depth layout as before — a node's column is the longest chain
 * of prerequisites behind it — but framed around the four questions a learner
 * actually asks: where am I, what's next, what's blocking me, where does this
 * lead. Precise numbers stay available in mono for the technically minded.
 */

/**
 * Route state, derived only from what the backend reports.
 *
 * `blocked` comes from `unlocked === false`; nothing else is ever presented as a
 * lock. `ready` is the actionable frontier: open to work on *and* standing on
 * prerequisites that are already proven. Everything else that is open but whose
 * groundwork is unproven is `open` — legitimately startable, just not the
 * obvious next move.
 */
type RouteState = "verified" | "in_progress" | "ready" | "open" | "blocked";

const STATE_COPY: Record<
  RouteState,
  { glyph: string; short: string; sentence: string; text: string; dot: string }
> = {
  verified: {
    glyph: "●",
    short: "Proven",
    sentence: "You have proven this.",
    text: "text-success",
    dot: "bg-success",
  },
  in_progress: {
    glyph: "◐",
    short: "In progress",
    sentence: "You have started this, but it is not proven yet.",
    text: "text-warning",
    dot: "bg-warning",
  },
  ready: {
    glyph: "▸",
    short: "Ready now",
    sentence: "Everything this depends on is already proven. You can start it today.",
    text: "text-accent",
    dot: "bg-accent",
  },
  open: {
    glyph: "○",
    short: "Open",
    sentence:
      "Nothing is stopping you, but the skills underneath it are not proven yet — those are the safer place to start.",
    text: "text-muted",
    dot: "bg-line-strong",
  },
  blocked: {
    glyph: "✕",
    short: "Blocked",
    sentence: "A prerequisite is short of the bar, so this is closed for now.",
    text: "text-danger",
    dot: "bg-danger",
  },
};

function routeState(node: GraphNode, threshold: number, byId: Map<string, GraphNode>): RouteState {
  if (!node.unlocked) return "blocked";
  if (node.confidence >= threshold) return "verified";
  if (node.has_evidence) return "in_progress";
  const groundworkProven = node.prerequisites.every((id) => {
    const prerequisite = byId.get(id);
    return prerequisite ? prerequisite.confidence >= threshold : false;
  });
  return groundworkProven ? "ready" : "open";
}

/** "Stage 3" is meaningless on its own; the subtitle says what it costs to get there. */
function stageCopy(level: number) {
  if (level === 0) {
    return { title: "Start here", note: "nothing needed first" };
  }
  return {
    title: `Stage ${level + 1}`,
    note: level === 1 ? "one skill deep" : `${level} skills deep`,
  };
}

export function KnowledgeGraph({
  nodes,
  threshold,
}: {
  nodes: GraphNode[];
  threshold: number;
}) {
  const [activeId, setActiveId] = useState<string | null>(null);
  const [pinnedId, setPinnedId] = useState<string | null>(null);

  const byId = useMemo(() => new Map(nodes.map((node) => [node.id, node])), [nodes]);

  // Column index = longest prerequisite chain behind a node. Memoised with a
  // guard so a malformed cycle in the graph cannot hang the render.
  const layout = useMemo(() => {
    const depth = new Map<string, number>();
    const resolve = (id: string, seen: Set<string>): number => {
      if (depth.has(id)) return depth.get(id)!;
      if (seen.has(id)) return 0;
      const node = byId.get(id);
      if (!node || node.prerequisites.length === 0) {
        depth.set(id, 0);
        return 0;
      }
      seen.add(id);
      const value =
        1 +
        Math.max(
          ...node.prerequisites.map((prerequisite) => resolve(prerequisite, seen)),
        );
      seen.delete(id);
      depth.set(id, value);
      return value;
    };

    nodes.forEach((node) => resolve(node.id, new Set()));

    const columns = new Map<number, GraphNode[]>();
    nodes.forEach((node) => {
      const level = depth.get(node.id) ?? 0;
      columns.set(level, [...(columns.get(level) ?? []), node]);
    });

    return Array.from(columns.entries())
      .sort(([a], [b]) => a - b)
      .map(([level, items]) => ({
        level,
        items: items.slice().sort((a, b) => a.difficulty_weight - b.difficulty_weight),
      }));
  }, [nodes, byId]);

  const states = useMemo(() => {
    const map = new Map<string, RouteState>();
    nodes.forEach((node) => map.set(node.id, routeState(node, threshold, byId)));
    return map;
  }, [nodes, byId, threshold]);

  const tally = useMemo(() => {
    const counts: Record<RouteState, number> = {
      verified: 0,
      in_progress: 0,
      ready: 0,
      open: 0,
      blocked: 0,
    };
    states.forEach((state) => {
      counts[state] += 1;
    });
    return counts;
  }, [states]);

  const active = activeId ? byId.get(activeId) ?? null : null;
  // Everything one hop from the active node, so related nodes stay legible while
  // the rest recedes.
  const related = new Set<string>(
    active ? [...active.prerequisites, ...active.unlocks, active.id] : [],
  );

  const select = (id: string) => {
    setPinnedId(id);
    setActiveId(id);
  };

  return (
    <div className="grid min-w-0 gap-px bg-line lg:grid-cols-[minmax(0,1fr)_320px]">
      {/* ------------------------------------------------------------ route */}
      {/* `min-w-0` on the scroller matters: without it the grid item grows to
          the width of the widest stage and the whole page scrolls sideways. */}
      <div
        className="grid-bg-fine relative min-w-0 bg-canvas"
        onMouseLeave={() => setActiveId(pinnedId)}
      >
        {/* Where you stand overall — the first thing read, and the thing that
            keeps a zero-progress route from looking like a wall of grey. */}
        <div className="border-b border-line px-5 py-4 sm:px-6">
          <p className="max-w-[62ch] text-[12.5px] leading-[1.7] text-muted">
            {tally.verified === 0 ? (
              <>
                Nothing is proven yet, so the route is wide open.{" "}
                <span className="text-ink">
                  {tally.ready} skill{tally.ready === 1 ? "" : "s"} can be started right now
                </span>{" "}
                — prove one and the stages after it start opening.
              </>
            ) : (
              <>
                <span className="text-ink">
                  {tally.verified} of {nodes.length} skills proven
                </span>
                . {tally.ready} ready to start
                {tally.blocked > 0 ? `, ${tally.blocked} blocked behind a prerequisite` : ""}.
              </>
            )}
          </p>
          <div className="mt-3.5 flex flex-wrap gap-x-5 gap-y-2">
            {(["verified", "in_progress", "ready", "open", "blocked"] as RouteState[]).map(
              (state) => (
                <span key={state} className="flex items-baseline gap-1.5">
                  <span className={cn("font-mono text-[10px] leading-none", STATE_COPY[state].text)}>
                    {STATE_COPY[state].glyph}
                  </span>
                  <span className="font-mono text-[11px] tabular-nums text-ink">
                    {tally[state]}
                  </span>
                  <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
                    {STATE_COPY[state].short}
                  </span>
                </span>
              ),
            )}
          </div>
        </div>

        <div className="overflow-x-auto p-5 sm:p-6">
          <div className="flex min-w-max gap-7">
            {layout.map(({ level, items }) => {
              const stage = stageCopy(level);
              return (
                <div key={level} className="min-w-[188px] flex-1">
                  <div className="mb-4">
                    <p className="text-[11.5px] font-medium tracking-tight text-ink">
                      {stage.title}
                    </p>
                    <p className="label mt-1">{stage.note}</p>
                  </div>
                  <ul className="space-y-2">
                    {items.map((node) => {
                      const state = states.get(node.id) ?? "open";
                      const copy = STATE_COPY[state];
                      const tone = confidenceTone(node.confidence, threshold);
                      const dimmed = Boolean(active) && !related.has(node.id);
                      const isActive = node.id === activeId;
                      const blocker = node.missing_prerequisites[0];
                      return (
                        <li key={node.id}>
                          <button
                            type="button"
                            aria-pressed={pinnedId === node.id}
                            aria-label={`${node.name}. ${copy.short}. ${
                              node.has_evidence
                                ? `Confidence ${node.confidence.toFixed(0)} percent of ${threshold} needed.`
                                : "No evidence yet."
                            }${
                              state === "blocked" && blocker
                                ? ` Blocked by ${blocker.skill_name}.`
                                : ""
                            }`}
                            onMouseEnter={() => setActiveId(node.id)}
                            onFocus={() => setActiveId(node.id)}
                            onClick={() => select(node.id)}
                            className={cn(
                              "w-full border-l-2 px-3 py-2.5 text-left transition-all duration-300 ease-forge",
                              "focus:outline-none focus-visible:ring-1 focus-visible:ring-accent focus-visible:ring-offset-1 focus-visible:ring-offset-canvas",
                              isActive
                                ? "border-accent bg-accent/[0.07]"
                                : state === "ready"
                                  ? "border-accent/60 bg-accent/[0.03] hover:bg-accent/[0.07]"
                                  : state === "verified"
                                    ? "border-success/50 hover:bg-elevated"
                                    : state === "blocked"
                                      ? "border-line border-dashed hover:bg-elevated"
                                      : "border-line-strong hover:bg-elevated",
                              dimmed && "opacity-30",
                            )}
                          >
                            <div className="flex items-center gap-2">
                              {/* Glyph, not just colour: state survives greyscale. */}
                              <span
                                aria-hidden
                                className={cn(
                                  "flex-none font-mono text-[10px] leading-none",
                                  copy.text,
                                )}
                              >
                                {copy.glyph}
                              </span>
                              <span
                                className={cn(
                                  "min-w-0 flex-1 truncate text-[12px]",
                                  state === "blocked" ? "text-faint" : "text-ink",
                                )}
                              >
                                {node.name}
                              </span>
                              <span
                                className={cn(
                                  "flex-none font-mono text-[9.5px] tabular-nums",
                                  node.has_evidence ? tone.text : "text-faint",
                                )}
                              >
                                {node.has_evidence ? `${node.confidence.toFixed(0)}%` : "—"}
                              </span>
                            </div>

                            {state === "blocked" && blocker ? (
                              <p className="mt-1.5 truncate text-[10.5px] text-danger/90">
                                Needs {blocker.skill_name}
                                {node.missing_prerequisites.length > 1
                                  ? ` +${node.missing_prerequisites.length - 1} more`
                                  : ""}
                              </p>
                            ) : state === "ready" ? (
                              <p className="mt-1.5 text-[10.5px] text-accent/90">Ready to start</p>
                            ) : null}

                            <div className="mt-2 flex items-center gap-2">
                              <GrowBar
                                value={node.has_evidence ? node.confidence : 0}
                                tone={node.has_evidence ? tone.tone : "muted"}
                                className="h-[2px] flex-1"
                              />
                              <span className="flex-none font-mono text-[9px] text-faint">
                                L{node.difficulty_weight}
                              </span>
                            </div>
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* -------------------------------------------------------- inspector */}
      <aside className="bg-surface p-5" aria-live="polite">
        {active ? (
          <Inspector
            key={active.id}
            node={active}
            state={states.get(active.id) ?? "open"}
            threshold={threshold}
            byId={byId}
            onPick={select}
          />
        ) : (
          <div className="flex h-full flex-col justify-center">
            <p className="label">Pick a skill</p>
            <p className="mt-3 max-w-[32ch] text-[12px] leading-relaxed text-muted">
              Select any skill on the route to see where you stand on it, exactly what is holding it
              back, and what proving it opens up.
            </p>
            <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {nodes.length} skills mapped · verified at {threshold}%
            </p>
          </div>
        )}
      </aside>
    </div>
  );
}

function Inspector({
  node,
  state,
  threshold,
  byId,
  onPick,
}: {
  node: GraphNode;
  state: RouteState;
  threshold: number;
  byId: Map<string, GraphNode>;
  onPick: (id: string) => void;
}) {
  const copy = STATE_COPY[state];
  const tone = confidenceTone(node.confidence, threshold);

  return (
    <div className="animate-reveal">
      <p className="label">{node.track}</p>
      <h3 className="display mt-2 text-[17px] tracking-tight text-ink">{node.name}</h3>

      {/* Where am I — a sentence first, the number second. */}
      <p className={cn("mt-3 flex items-baseline gap-2 text-[12px]", copy.text)}>
        <span aria-hidden className="font-mono text-[10px] leading-none">
          {copy.glyph}
        </span>
        <span className="font-mono text-[10px] uppercase tracking-[0.1em]">{copy.short}</span>
      </p>
      <p className="mt-2 text-[12px] leading-relaxed text-muted">{copy.sentence}</p>

      <div className="mt-4 flex items-baseline justify-between">
        <span className="label">confidence</span>
        <span className={cn("font-mono text-[13px] tabular-nums", tone.text)}>
          {node.has_evidence ? `${node.confidence.toFixed(0)}%` : "no evidence"}
          <span className="ml-1.5 text-faint">/ {threshold}%</span>
        </span>
      </div>
      <GrowBar
        value={node.confidence}
        threshold={threshold}
        tone={tone.tone}
        className="mt-2"
      />

      {/* What's blocking me — the concrete gap, named and quantified. */}
      {state === "blocked" ? (
        node.missing_prerequisites.length > 0 ? (
          <div className="mt-5 rounded-r border border-line border-l-2 border-l-danger/60 bg-danger/[0.05] px-3.5 py-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-danger">
              What&apos;s blocking this
            </p>
            <ul className="mt-2.5 space-y-3">
              {node.missing_prerequisites.map((gap) => (
                <Blocker key={gap.skill_id} gap={gap} onPick={onPick} byId={byId} />
              ))}
            </ul>
          </div>
        ) : (
          <div className="mt-5 rounded-r border border-line border-l-2 border-l-warning/60 bg-warning/[0.05] px-3.5 py-3">
            <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-warning">
              Closed for now
            </p>
            <p className="mt-1.5 text-[12px] leading-relaxed text-ink/90">
              This skill is not open yet, but no specific prerequisite gap was reported — the
              prerequisite state is unclear. Working through the skills before it is the reliable
              way forward.
            </p>
          </div>
        )
      ) : null}

      {/* Where does this lead. */}
      {node.unlocks.length > 0 ? (
        <div className="mt-5 border-t border-line pt-4">
          <p className="label mb-2">Proving this opens</p>
          <div className="flex flex-wrap gap-1.5">
            {node.unlocks.map((id) => (
              <button
                key={id}
                type="button"
                onClick={() => onPick(id)}
                className="chip transition-colors hover:border-accent/40 hover:text-accent"
              >
                {byId.get(id)?.name ?? id}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <dl className="mt-5 space-y-3.5 border-t border-line pt-4">
        <Row label="builds on">
          <NodeNames ids={node.prerequisites} byId={byId} onPick={onPick} threshold={threshold} />
        </Row>
        <Row label="difficulty">
          <span className="text-[11px] text-ink">
            {difficultyLabel(node.difficulty_weight)}{" "}
            <span className="font-mono text-[10px] text-faint">
              L{node.difficulty_weight}
            </span>
          </span>
        </Row>
        <Row label="skill id">
          <span className="font-mono text-[10px] text-faint">{node.id}</span>
        </Row>
      </dl>

      {node.related_concepts.length > 0 ? (
        <div className="mt-5 border-t border-line pt-4">
          <p className="label mb-2">what it covers</p>
          <div className="flex flex-wrap gap-1.5">
            {node.related_concepts.map((concept) => (
              <span key={concept} className="chip">
                {concept}
              </span>
            ))}
          </div>
        </div>
      ) : null}

      <div className="mt-5 flex flex-col gap-2 border-t border-line pt-4">
        {node.recommended_practice.length > 0 ? (
          <Link
            href={`/practice/${node.recommended_practice[0]}`}
            className="btn-primary btn-mono py-2"
          >
            Practise this →
          </Link>
        ) : null}
        <Link href={`/assessment/${node.id}`} className="btn-ghost btn-mono py-2">
          Verify this skill
        </Link>
      </div>
    </div>
  );
}

/** One named, quantified gap: the plain sentence, then the numbers, then a way to fix it. */
function Blocker({
  gap,
  byId,
  onPick,
}: {
  gap: PrerequisiteGap;
  byId: Map<string, GraphNode>;
  onPick: (id: string) => void;
}) {
  const known = byId.has(gap.skill_id);
  const practice = gap.recommended_practice?.[0];

  return (
    <li>
      <p className="text-[12px] leading-relaxed text-ink/90">
        Needs{" "}
        {known ? (
          <button
            type="button"
            onClick={() => onPick(gap.skill_id)}
            className="link font-medium"
          >
            {gap.skill_name}
          </button>
        ) : (
          <span className="font-medium">{gap.skill_name}</span>
        )}{" "}
        at {gap.required.toFixed(0)}% — currently{" "}
        <span className="font-mono tabular-nums text-danger">{gap.confidence.toFixed(0)}%</span>
      </p>
      <GrowBar
        value={gap.confidence}
        threshold={gap.required}
        tone="danger"
        className="mt-1.5 h-[3px]"
      />
      <p className="mt-1.5 font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
        {(gap.required - gap.confidence).toFixed(0)} points short
        {gap.difficulty_weight !== undefined ? ` · L${gap.difficulty_weight}` : ""}
      </p>
      {practice ? (
        <Link
          href={`/practice/${practice}`}
          className="mt-1.5 inline-block font-mono text-[10px] uppercase tracking-[0.1em] text-accent transition-opacity hover:opacity-75"
        >
          Close this gap →
        </Link>
      ) : null}
    </li>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <dt className="label flex-none pt-0.5">{label}</dt>
      <dd className="min-w-0 text-right">{children}</dd>
    </div>
  );
}

function NodeNames({
  ids,
  byId,
  onPick,
  threshold,
}: {
  ids: string[];
  byId: Map<string, GraphNode>;
  onPick: (id: string) => void;
  threshold: number;
}) {
  if (ids.length === 0) {
    return <span className="text-[11px] text-faint">nothing — this is a starting point</span>;
  }
  return (
    <span className="flex flex-wrap justify-end gap-x-2 gap-y-1">
      {ids.map((id) => {
        const node = byId.get(id);
        const proven = node ? node.confidence >= threshold : false;
        return (
          <button
            key={id}
            type="button"
            onClick={() => onPick(id)}
            className="text-[11px] text-muted transition-colors hover:text-accent"
          >
            <span aria-hidden className={cn("mr-1 font-mono text-[9px]", proven ? "text-success" : "text-faint")}>
              {proven ? "●" : "○"}
            </span>
            {node?.name ?? id}
          </button>
        );
      })}
    </span>
  );
}
