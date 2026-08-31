"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/utils";

/** The eight stages of the SprintForge loop, with the system readout for each. */
const STAGES = [
  { id: "claim", label: "CLAIM", readout: "js_async · self-reported intermediate" },
  { id: "verify", label: "VERIFY", readout: "adaptive assessment · 9 items" },
  { id: "diagnose", label: "DIAGNOSE", readout: "gap found · promise rejection" },
  { id: "plan", label: "PLAN", readout: "graph route · 4 nodes ahead" },
  { id: "execute", label: "EXECUTE", readout: "ticket MTB-14 · seat selection" },
  { id: "observe", label: "OBSERVE", readout: "12 checks · 2 failing" },
  { id: "adapt", label: "ADAPT", readout: "difficulty 4 → 3 · remediation queued" },
  { id: "reverify", label: "RE-VERIFY", readout: "confidence 42% → 67%" },
] as const;

const SIZE = 320;
// The orbit is inset enough that stage labels drawn outside it still fit the
// viewBox, so the whole visual scales as one unit and can never overflow.
const RADIUS = 104;
const CENTER = SIZE / 2;
const LABEL_RADIUS = 130;

function nodePosition(index: number, total: number, radius = RADIUS) {
  // Start at 12 o'clock and walk clockwise.
  const angle = (index / total) * Math.PI * 2 - Math.PI / 2;
  return { x: CENTER + Math.cos(angle) * radius, y: CENTER + Math.sin(angle) * radius };
}

/** Anchor labels away from the circle so they never sit on top of the orbit. */
function labelAnchor(x: number): "start" | "middle" | "end" {
  if (x > CENTER + 12) return "start";
  if (x < CENTER - 12) return "end";
  return "middle";
}

/**
 * The hero visual: a running representation of the adaptive loop.
 *
 * It advances on a timer so the page feels alive, and pauses on hover so a
 * visitor can read a stage. Reduced-motion users get a static, fully legible
 * diagram with the first stage active.
 */
export function EngineLoop({ className }: { className?: string }) {
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);
  const reduced = useRef(false);

  useEffect(() => {
    reduced.current =
      typeof window !== "undefined" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced.current || paused) return;
    const timer = setInterval(() => setActive((value) => (value + 1) % STAGES.length), 1750);
    return () => clearInterval(timer);
  }, [paused]);

  const stage = STAGES[active];

  return (
    <div
      className={cn("relative select-none", className)}
      onMouseLeave={() => setPaused(false)}
      role="img"
      aria-label="The SprintForge loop: claim, verify, diagnose, plan, execute, observe, adapt, re-verify."
    >
      {/* The viewBox is padded horizontally so the widest stage labels
          ("DIAGNOSE", "RE-VERIFY") have room outside the orbit. */}
      <svg
        viewBox={`-38 -18 ${SIZE + 76} ${SIZE + 36}`}
        className="h-auto w-full max-w-[440px]"
        aria-hidden
      >
        {/* Orbit */}
        <circle
          cx={CENTER}
          cy={CENTER}
          r={RADIUS}
          fill="none"
          stroke="#1f2228"
          strokeWidth="1"
        />
        {/* Travelling arc that shows the loop is running */}
        <circle
          cx={CENTER}
          cy={CENTER}
          r={RADIUS}
          fill="none"
          stroke="rgba(200,250,75,0.5)"
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeDasharray={`${(2 * Math.PI * RADIUS) / STAGES.length - 26} ${2 * Math.PI * RADIUS}`}
          transform={`rotate(${(active / STAGES.length) * 360 - 90} ${CENTER} ${CENTER})`}
          style={{ transition: "transform 700ms cubic-bezier(0.16,1,0.3,1)" }}
        />

        {/* Spokes to the centre, brightest for the active stage */}
        {STAGES.map((item, index) => {
          const { x, y } = nodePosition(index, STAGES.length);
          const isActive = index === active;
          return (
            <line
              key={`spoke-${item.id}`}
              x1={CENTER}
              y1={CENTER}
              x2={x}
              y2={y}
              stroke={isActive ? "rgba(200,250,75,0.32)" : "#16181d"}
              strokeWidth="1"
              style={{ transition: "stroke 500ms linear" }}
            />
          );
        })}

        {/* Stage nodes */}
        {STAGES.map((item, index) => {
          const { x, y } = nodePosition(index, STAGES.length);
          const isActive = index === active;
          const isPast = index < active;
          return (
            <g
              key={item.id}
              onMouseEnter={() => {
                setPaused(true);
                setActive(index);
              }}
              className="cursor-pointer"
            >
              {/* Generous invisible hit area */}
              <circle cx={x} cy={y} r="20" fill="transparent" />
              {isActive ? (
                <circle cx={x} cy={y} r="9" fill="rgba(200,250,75,0.16)" />
              ) : null}
              <circle
                cx={x}
                cy={y}
                r={isActive ? 4.5 : 3}
                fill={isActive ? "#c8fa4b" : isPast ? "#4a5220" : "#2c3138"}
                style={{ transition: "all 400ms cubic-bezier(0.16,1,0.3,1)" }}
              />
            </g>
          );
        })}

        {/* Stage labels, drawn in the SVG so they scale with the diagram */}
        {STAGES.map((item, index) => {
          const { x, y } = nodePosition(index, STAGES.length, LABEL_RADIUS);
          const isActive = index === active;
          return (
            <text
              key={`label-${item.id}`}
              x={x}
              y={y + 3}
              textAnchor={labelAnchor(x)}
              className={cn(
                "font-mono transition-colors duration-500",
                isActive ? "fill-accent" : "fill-faint",
              )}
              style={{ fontSize: 7.5, letterSpacing: "0.14em" }}
            >
              {item.label}
            </text>
          );
        })}

        {/* Centre readout */}
        <text
          x={CENTER}
          y={CENTER - 6}
          textAnchor="middle"
          className="fill-faint font-mono"
          style={{ fontSize: 8, letterSpacing: "0.18em" }}
        >
          SPRINTFORGE
        </text>
        <text
          x={CENTER}
          y={CENTER + 12}
          textAnchor="middle"
          className="fill-ink font-mono"
          style={{ fontSize: 13, letterSpacing: "0.04em" }}
        >
          {String(active + 1).padStart(2, "0")}/08
        </text>
      </svg>

      {/* Live readout for the active stage */}
      <div className="mt-6 border-l-2 border-accent/50 pl-3">
        <p className="label-accent">{stage.label}</p>
        <p className="mt-1 font-mono text-[11px] text-muted">{stage.readout}</p>
      </div>
    </div>
  );
}
