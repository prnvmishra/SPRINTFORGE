"use client";

import {
  ElementType,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from "react";

import { cn } from "@/lib/utils";

function prefersReducedMotion() {
  if (typeof window === "undefined") return false;
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

/**
 * Fires once when an element scrolls into view.
 *
 * Returns `true` immediately when the user prefers reduced motion, so content is
 * never hidden behind an animation that will not run.
 */
export function useInView<T extends HTMLElement>(options?: { threshold?: number; rootMargin?: string }) {
  const ref = useRef<T | null>(null);
  const [inView, setInView] = useState(false);

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (prefersReducedMotion() || typeof IntersectionObserver === "undefined") {
      setInView(true);
      return;
    }
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setInView(true);
          observer.disconnect();
        }
      },
      // Threshold 0 on purpose: a ratio-based threshold never fires for an
      // element taller than the viewport, which left long lists hidden until
      // the user scrolled. Any pixel entering the margin is enough.
      { threshold: options?.threshold ?? 0, rootMargin: options?.rootMargin ?? "0px 0px -8% 0px" },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [options?.threshold, options?.rootMargin]);

  return { ref, inView };
}

/** Scroll-triggered reveal. Content is always in the DOM for accessibility and SEO. */
export function Reveal({
  children,
  className,
  delay = 0,
  blur = false,
  as: Tag = "div",
}: {
  children: ReactNode;
  className?: string;
  delay?: number;
  blur?: boolean;
  as?: ElementType;
}) {
  const { ref, inView } = useInView<HTMLDivElement>();

  return (
    <Tag
      ref={ref}
      className={cn(
        "transition-[opacity,transform,filter] duration-700 ease-forge",
        inView ? "translate-y-0 opacity-100 blur-0" : "translate-y-3 opacity-0",
        !inView && blur && "blur-[5px]",
        className,
      )}
      style={{ transitionDelay: `${delay}ms` }}
    >
      {children}
    </Tag>
  );
}

/**
 * Counts up to a target once visible. Reduced-motion users get the final value
 * with no interpolation.
 */
export function Counter({
  value,
  decimals = 0,
  suffix = "",
  prefix = "",
  duration = 900,
  className,
}: {
  value: number;
  decimals?: number;
  suffix?: string;
  prefix?: string;
  duration?: number;
  className?: string;
}) {
  const { ref, inView } = useInView<HTMLSpanElement>({ threshold: 0.4 });
  const [shown, setShown] = useState(0);

  useEffect(() => {
    if (!inView) return;
    if (prefersReducedMotion()) {
      setShown(value);
      return;
    }
    let frame = 0;
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min(1, (now - start) / duration);
      // Ease-out cubic: fast start, settled finish.
      setShown(value * (1 - Math.pow(1 - progress, 3)));
      if (progress < 1) frame = requestAnimationFrame(tick);
    };
    frame = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(frame);
  }, [inView, value, duration]);

  return (
    <span ref={ref} className={cn("tabular-nums", className)}>
      {prefix}
      {shown.toFixed(decimals)}
      {suffix}
    </span>
  );
}

/** Animated width bar that only fills once scrolled into view. */
export function GrowBar({
  value,
  threshold,
  tone = "accent",
  className,
  delay = 0,
}: {
  value: number;
  threshold?: number;
  tone?: "accent" | "success" | "warning" | "danger" | "muted";
  className?: string;
  delay?: number;
}) {
  const { ref, inView } = useInView<HTMLDivElement>({ threshold: 0.3 });
  const tones = {
    accent: "bg-accent",
    success: "bg-success",
    warning: "bg-warning",
    danger: "bg-danger",
    muted: "bg-line-strong",
  } as const;

  return (
    <div ref={ref} className={cn("relative h-1 w-full overflow-hidden bg-elevated", className)}>
      <div
        className={cn("h-full transition-[width] duration-[900ms] ease-forge", tones[tone])}
        style={{
          width: inView ? `${Math.max(0, Math.min(100, value))}%` : "0%",
          transitionDelay: `${delay}ms`,
        }}
      />
      {threshold !== undefined ? (
        <span
          className="absolute top-0 h-full w-px bg-ink/35"
          style={{ left: `${threshold}%` }}
          title={`Verified at ${threshold}%`}
        />
      ) : null}
    </div>
  );
}