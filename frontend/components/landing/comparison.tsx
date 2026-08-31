"use client";

import { useState } from "react";

import { cn } from "@/lib/utils";

const TRADITIONAL = ["Watch", "Watch", "Quiz", "Certificate"];
const SPRINTFORGE = [
  "Claim",
  "Verify",
  "Build",
  "Fail",
  "Understand",
  "Adapt",
  "Build again",
];

/**
 * Two paths, deliberately unequal in weight. The traditional path is rendered
 * thin and grey and literally runs out; the SprintForge path is dense and loops.
 */
export function Comparison() {
  const [hovered, setHovered] = useState<"old" | "new" | null>(null);

  return (
    <div className="grid gap-px overflow-hidden rounded-lg border border-line bg-line md:grid-cols-2">
      <div
        onMouseEnter={() => setHovered("old")}
        onMouseLeave={() => setHovered(null)}
        className={cn(
          "bg-surface p-7 transition-colors duration-300 sm:p-9",
          hovered === "old" && "bg-elevated",
        )}
      >
        <p className="label">The course model</p>
        <h3 className="display mt-3 text-[19px] tracking-tight text-muted">
          Completion as the goal
        </h3>

        <ol className="mt-7 space-y-0">
          {TRADITIONAL.map((step, index) => (
            <li key={`${step}-${index}`} className="flex items-baseline gap-4 py-2">
              <span className="font-mono text-[10px] text-faint">
                {String(index + 1).padStart(2, "0")}
              </span>
              <span className="text-[15px] text-muted">{step}</span>
              {index === TRADITIONAL.length - 1 ? (
                <span className="ml-auto font-mono text-[10px] text-faint">terminates</span>
              ) : null}
            </li>
          ))}
        </ol>

        <p className="mt-7 max-w-[40ch] text-[12px] leading-relaxed text-faint">
          A certificate records that you were present. It cannot tell you, or anyone hiring you,
          which concepts you would fumble under pressure.
        </p>
      </div>

      <div
        onMouseEnter={() => setHovered("new")}
        onMouseLeave={() => setHovered(null)}
        className={cn(
          "relative overflow-hidden bg-surface p-7 transition-colors duration-300 sm:p-9",
          hovered === "new" && "bg-elevated",
        )}
      >
        {/* Accent edge marks this as the product's position */}
        <span className="absolute inset-y-0 left-0 w-px bg-accent/40" aria-hidden />

        <p className="label-accent">The SprintForge model</p>
        <h3 className="display mt-3 text-[19px] tracking-tight text-ink">
          Evidence as the goal
        </h3>

        <ol className="mt-7 space-y-0">
          {SPRINTFORGE.map((step, index) => (
            <li
              key={step}
              className="group flex items-baseline gap-4 py-2"
              style={{ transitionDelay: `${index * 40}ms` }}
            >
              <span
                className={cn(
                  "font-mono text-[10px]",
                  step === "Fail" ? "text-danger" : "text-accent/70",
                )}
              >
                {String(index + 1).padStart(2, "0")}
              </span>
              <span
                className={cn(
                  "text-[15px] transition-colors",
                  step === "Fail" ? "text-danger" : "text-ink",
                )}
              >
                {step}
              </span>
              {step === "Fail" ? (
                <span className="ml-auto font-mono text-[10px] text-danger/80">
                  kept, not hidden
                </span>
              ) : null}
              {step === "Build again" ? (
                <span className="ml-auto font-mono text-[10px] text-accent">↻ loops</span>
              ) : null}
            </li>
          ))}
        </ol>

        <p className="mt-7 max-w-[40ch] text-[12px] leading-relaxed text-muted">
          Failure is the most useful signal in the system. It is where the engine learns what to
          teach you next, which is why nothing here lets you skip it.
        </p>
      </div>
    </div>
  );
}

const LAYERS = [
  {
    id: "html",
    given: ["styles.css", "script.js"],
    missing: "index.html",
    proves: "Semantic structure",
    code: `<!-- Rebuild the markup the styles expect -->\n<article class="profile-card">\n  <img class="avatar" src="..." alt="" />\n  <h1 class="name">…</h1>\n  <button id="followBtn">Follow</button>\n</article>`,
  },
  {
    id: "css",
    given: ["index.html", "script.js"],
    missing: "styles.css",
    proves: "Layout & visual reasoning",
    code: `/* The stylesheet was removed. Rebuild it. */\n.profile-card {\n  display: flex;\n  flex-direction: column;\n  gap: 12px;\n}`,
  },
  {
    id: "javascript",
    given: ["index.html", "styles.css"],
    missing: "script.js",
    proves: "Behaviour & state",
    code: `// Wire the interaction the markup implies\nfollowBtn.addEventListener("click", () => {\n  following = !following;\n  render();\n});`,
  },
  {
    id: "react",
    given: ["App.jsx", "MovieCard.jsx"],
    missing: "useMovieSelection.js",
    proves: "Composition & data flow",
    code: `export function useMovieSelection(movies) {\n  const [selected, setSelected] = useState(null);\n  // derive, memoise, return the API the UI needs\n}`,
  },
] as const;

/**
 * Practice Mode's core idea, made tangible: a working project arrives with
 * exactly one layer missing, and the missing layer is the thing being proved.
 */
export function LayerRemoval() {
  const [active, setActive] = useState(0);
  const layer = LAYERS[active];

  return (
    <div>
      {/* Layer selector reads as an editor tab strip */}
      <div className="flex flex-wrap gap-px overflow-hidden rounded-t-lg border border-line bg-line">
        {LAYERS.map((item, index) => (
          <button
            key={item.id}
            onClick={() => setActive(index)}
            aria-pressed={active === index}
            className={cn(
              "flex-1 bg-surface px-4 py-3 text-left transition-colors duration-200",
              active === index ? "bg-elevated" : "hover:bg-elevated/60",
            )}
          >
            <span
              className={cn(
                "font-mono text-[10px] uppercase tracking-[0.14em]",
                active === index ? "text-accent" : "text-faint",
              )}
            >
              {item.id}
            </span>
            <span
              className={cn(
                "mt-1 block text-[11.5px]",
                active === index ? "text-ink" : "text-muted",
              )}
            >
              {item.proves}
            </span>
          </button>
        ))}
      </div>

      <div className="grid gap-px border-x border-b border-line bg-line lg:grid-cols-[240px_1fr]">
        {/* File tree: what you get vs what was taken away */}
        <div className="bg-surface p-4">
          <p className="label mb-3">Workspace</p>
          <ul className="space-y-1.5">
            {layer.given.map((file) => (
              <li key={file} className="flex items-center gap-2 font-mono text-[11px] text-muted">
                <span className="text-success">✓</span>
                {file}
                <span className="ml-auto text-[9px] text-faint">given</span>
              </li>
            ))}
            <li className="flex items-center gap-2 font-mono text-[11px] text-accent">
              <span className="animate-pulse">◆</span>
              {layer.missing}
              <span className="ml-auto text-[9px] text-accent/70">you</span>
            </li>
          </ul>

          <div className="mt-5 border-t border-line pt-4">
            <p className="label mb-2">Proves</p>
            <p className="text-[12px] leading-relaxed text-ink">{layer.proves}</p>
          </div>
        </div>

        {/* Faux editor pane */}
        <div className="relative overflow-hidden bg-canvas">
          <div className="flex items-center gap-2 border-b border-line px-4 py-2">
            <span className="font-mono text-[10.5px] text-accent">{layer.missing}</span>
            <span className="ml-auto flex items-center gap-1.5">
              <span className="h-1 w-1 rounded-full bg-accent" />
              <span className="font-mono text-[9px] uppercase tracking-[0.14em] text-faint">
                editable
              </span>
            </span>
          </div>
          <pre
            key={layer.id}
            className="animate-reveal overflow-x-auto p-4 font-mono text-[11.5px] leading-[1.75] text-muted"
          >
            {layer.code}
          </pre>
          <div className="flex items-center gap-3 border-t border-line px-4 py-2.5">
            <span className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-faint">
              deterministic checks first
            </span>
            <span className="ml-auto font-mono text-[10px] text-success">10 assertions ready</span>
          </div>
        </div>
      </div>
    </div>
  );
}
