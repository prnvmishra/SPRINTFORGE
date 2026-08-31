"use client";

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { cn } from "@/lib/utils";

/**
 * Reads a media query reactively. Used so a split only becomes a split where
 * there is room for one — below the breakpoint the panes stack and size to
 * their content instead of fighting over a short viewport.
 */
function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(false);

  useEffect(() => {
    const list = window.matchMedia(query);
    setMatches(list.matches);
    const onChange = (event: MediaQueryListEvent) => setMatches(event.matches);
    list.addEventListener("change", onChange);
    return () => list.removeEventListener("change", onChange);
  }, [query]);

  return matches;
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value));
}

/**
 * Two panes divided by a draggable hairline.
 *
 * The divider is a real `separator` with keyboard support, so the layout is
 * adjustable without a pointer. The split ratio is the only piece of state, held
 * as a percentage of the container so it survives window resizes.
 */
export function SplitPane({
  orientation = "horizontal",
  first,
  second,
  initial = 50,
  min = 18,
  max = 82,
  /** Persists the ratio across visits when set. */
  storageKey,
  /** Below this query the panes stack and the divider is inert. */
  splitFrom = "(min-width: 1024px)",
  className,
  firstClassName,
  secondClassName,
}: {
  orientation?: "horizontal" | "vertical";
  first: ReactNode;
  second: ReactNode;
  initial?: number;
  min?: number;
  max?: number;
  storageKey?: string;
  splitFrom?: string;
  className?: string;
  firstClassName?: string;
  secondClassName?: string;
}) {
  const isSplit = useMediaQuery(splitFrom);
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [size, setSize] = useState(initial);
  const [dragging, setDragging] = useState(false);

  useEffect(() => {
    if (!storageKey) return;
    const stored = Number(window.localStorage.getItem(`split:${storageKey}`));
    if (Number.isFinite(stored) && stored > 0) setSize(clamp(stored, min, max));
  }, [storageKey, min, max]);

  const commit = useCallback(
    (next: number) => {
      const value = clamp(next, min, max);
      setSize(value);
      if (storageKey) {
        window.localStorage.setItem(
          `split:${storageKey}`,
          String(Math.round(value * 10) / 10),
        );
      }
    },
    [min, max, storageKey],
  );

  useEffect(() => {
    if (!dragging) return;

    const onMove = (event: PointerEvent) => {
      const rect = containerRef.current?.getBoundingClientRect();
      if (!rect) return;
      const ratio =
        orientation === "horizontal"
          ? ((event.clientX - rect.left) / rect.width) * 100
          : ((event.clientY - rect.top) / rect.height) * 100;
      commit(ratio);
    };
    const onUp = () => setDragging(false);

    window.addEventListener("pointermove", onMove);
    window.addEventListener("pointerup", onUp);
    window.addEventListener("pointercancel", onUp);
    // The iframe preview and Monaco both swallow pointer events, so selection is
    // suppressed at the document level for the duration of the drag.
    const previousUserSelect = document.body.style.userSelect;
    document.body.style.userSelect = "none";
    document.body.style.cursor = orientation === "horizontal" ? "col-resize" : "row-resize";

    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("pointerup", onUp);
      window.removeEventListener("pointercancel", onUp);
      document.body.style.userSelect = previousUserSelect;
      document.body.style.cursor = "";
    };
  }, [dragging, orientation, commit]);

  if (!isSplit) {
    return (
      <div className={cn("flex flex-col", className)}>
        <div className={cn("min-h-0 min-w-0", firstClassName)}>{first}</div>
        <div className="h-px flex-none bg-line" aria-hidden />
        <div className={cn("min-h-0 min-w-0", secondClassName)}>{second}</div>
      </div>
    );
  }

  const horizontal = orientation === "horizontal";

  return (
    <div
      ref={containerRef}
      className={cn("flex min-h-0 min-w-0", horizontal ? "flex-row" : "flex-col", className)}
    >
      <div
        className={cn("min-h-0 min-w-0 overflow-hidden", firstClassName)}
        style={{ flex: `0 0 ${size}%` }}
      >
        {first}
      </div>

      <div
        role="separator"
        tabIndex={0}
        aria-orientation={horizontal ? "vertical" : "horizontal"}
        aria-label={horizontal ? "Resize panes" : "Resize editor and console"}
        aria-valuenow={Math.round(size)}
        aria-valuemin={min}
        aria-valuemax={max}
        onPointerDown={(event) => {
          event.preventDefault();
          setDragging(true);
        }}
        onDoubleClick={() => commit(initial)}
        onKeyDown={(event) => {
          const step = event.shiftKey ? 6 : 2;
          if (event.key === (horizontal ? "ArrowLeft" : "ArrowUp")) {
            event.preventDefault();
            commit(size - step);
          } else if (event.key === (horizontal ? "ArrowRight" : "ArrowDown")) {
            event.preventDefault();
            commit(size + step);
          } else if (event.key === "Home") {
            event.preventDefault();
            commit(initial);
          }
        }}
        className={cn(
          // z-20 is load-bearing: Monaco paints its own positioned overlays
          // (line numbers, margin, scrollbars) inside the neighbouring pane, and
          // without a stacking order of its own the divider ends up underneath
          // them — leaving a 1px rule that cannot actually be grabbed.
          "relative z-20 flex-none bg-line transition-colors duration-200 hover:bg-accent/50 focus-visible:bg-accent focus-visible:outline-none",
          dragging && "bg-accent/70",
          horizontal ? "w-px cursor-col-resize" : "h-px cursor-row-resize",
        )}
      >
        {/* Widened hit area: the visible rule stays a hairline. */}
        <span
          aria-hidden
          className={cn(
            "absolute",
            horizontal ? "inset-y-0 -inset-x-[5px]" : "inset-x-0 -inset-y-[5px]",
          )}
        />
      </div>

      <div className={cn("min-h-0 min-w-0 flex-1 overflow-hidden", secondClassName)}>{second}</div>
    </div>
  );
}
