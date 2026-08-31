"use client";

import { ReactNode } from "react";

import { GrowBar } from "@/components/motion";
import { cn, confidenceTone, humanStatus, statusGlyph, statusTone } from "@/lib/utils";

/* -------------------------------------------------------------------------- */
/*  Surfaces                                                                   */
/* -------------------------------------------------------------------------- */

/**
 * A flat technical panel. Deliberately low-radius and shadowless by default so
 * screens read as one composition rather than a pile of floating cards.
 */
export function Panel({
  children,
  className,
  as: Tag = "div",
  flush = false,
  inset = true,
}: {
  children: ReactNode;
  className?: string;
  as?: "div" | "section" | "article" | "aside" | "li";
  flush?: boolean;
  inset?: boolean;
}) {
  return (
    <Tag className={cn("panel rounded-lg", inset && "p-5", flush && "rounded-none", className)}>
      {children}
    </Tag>
  );
}

/**
 * Section header with a mono eyebrow. The eyebrow carries the taxonomy so the
 * title itself can stay short and human.
 */
export function SectionTitle({
  title,
  hint,
  action,
  eyebrow,
  className,
}: {
  title: string;
  hint?: string;
  action?: ReactNode;
  eyebrow?: string;
  className?: string;
}) {
  return (
    <div className={cn("mb-4 flex items-start justify-between gap-4", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className="label mb-1.5">{eyebrow}</p> : null}
        <h2 className="text-[13px] font-medium tracking-tight text-ink">{title}</h2>
        {hint ? <p className="mt-1 text-[11.5px] leading-relaxed text-muted">{hint}</p> : null}
      </div>
      {action ? <div className="flex-none">{action}</div> : null}
    </div>
  );
}

/** Full-bleed section divider with an index and a label, used on marketing pages. */
export function SectionMarker({ index, label }: { index: string; label: string }) {
  return (
    <div className="flex items-center gap-4">
      <span className="font-mono text-[10px] text-accent">{index}</span>
      <span className="label">{label}</span>
      <span className="h-px flex-1 bg-line" />
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Badges and status                                                          */
/* -------------------------------------------------------------------------- */

export function Badge({
  children,
  className,
  tone,
}: {
  children: ReactNode;
  className?: string;
  tone?: "accent" | "success" | "warning" | "danger";
}) {
  const tones = {
    accent: "border-accent/25 bg-accent/[0.07] text-accent",
    success: "border-success/25 bg-success/[0.07] text-success",
    warning: "border-warning/25 bg-warning/[0.07] text-warning",
    danger: "border-danger/25 bg-danger/[0.07] text-danger",
  } as const;
  return <span className={cn("chip", tone && tones[tone], className)}>{children}</span>;
}

/** Status pill that communicates through glyph + text, not colour alone. */
export function StatusPill({
  status,
  className,
  pulse = false,
}: {
  status: string;
  className?: string;
  pulse?: boolean;
}) {
  const live = pulse || status === "in_progress" || status === "analyzing";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded border px-2 py-0.5 font-mono text-[10px] uppercase tracking-[0.1em]",
        statusTone(status),
        className,
      )}
    >
      <span className={cn("text-[9px] leading-none", live && "animate-pulse")}>
        {statusGlyph(status)}
      </span>
      {humanStatus(status)}
    </span>
  );
}

/* -------------------------------------------------------------------------- */
/*  Metrics                                                                    */
/* -------------------------------------------------------------------------- */

export function ConfidenceBar({
  value,
  threshold = 65,
  showValue = true,
  className,
}: {
  value: number;
  threshold?: number;
  showValue?: boolean;
  className?: string;
}) {
  const tone = confidenceTone(value, threshold);
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <GrowBar value={value} threshold={threshold} tone={tone.tone} className="flex-1" />
      {showValue ? (
        <span className={cn("w-9 text-right font-mono text-[11px] tabular-nums", tone.text)}>
          {value.toFixed(0)}%
        </span>
      ) : null}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Loading                                                                    */
/* -------------------------------------------------------------------------- */

/**
 * System-voice loader. The label states what the engine is doing, so waiting
 * time doubles as an explanation of the product.
 */
export function Loader({
  label = "Working",
  className,
}: {
  label?: string;
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <span className="relative flex h-1.5 w-1.5">
        <span className="absolute inset-0 rounded-full bg-accent animate-pulse-ring" />
        <span className="relative h-1.5 w-1.5 rounded-full bg-accent" />
      </span>
      <span className="font-mono text-[10.5px] uppercase tracking-[0.14em] text-muted">
        {label}
        <span className="animate-caret">_</span>
      </span>
    </div>
  );
}

/** Full-region loading state with skeleton lines, for first paint of a panel. */
export function PanelSkeleton({ lines = 3, className }: { lines?: number; className?: string }) {
  return (
    <div className={cn("space-y-2.5", className)} aria-hidden>
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className="skeleton h-2.5 rounded"
          style={{ width: `${100 - index * 12}%` }}
        />
      ))}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Empty / error                                                              */
/* -------------------------------------------------------------------------- */

export function EmptyState({
  title,
  description,
  action,
  eyebrow,
}: {
  title: string;
  description: string;
  action?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="grid-bg-fine relative overflow-hidden rounded-lg border border-dashed border-line px-6 py-12 text-center">
      <div className="relative">
        {eyebrow ? <p className="label mb-3">{eyebrow}</p> : null}
        <p className="display text-[17px] tracking-tight text-ink">{title}</p>
        <p className="mx-auto mt-2 max-w-[42ch] text-[12px] leading-relaxed text-muted">
          {description}
        </p>
        {action ? <div className="mt-5 flex justify-center">{action}</div> : null}
      </div>
    </div>
  );
}

export function Alert({
  tone = "info",
  title,
  children,
}: {
  tone?: "info" | "success" | "warning" | "danger";
  title?: string;
  children: ReactNode;
}) {
  const tones = {
    info: "border-l-info/60 bg-info/[0.05]",
    success: "border-l-success/60 bg-success/[0.05]",
    warning: "border-l-warning/60 bg-warning/[0.05]",
    danger: "border-l-danger/60 bg-danger/[0.05]",
  } as const;
  const titleTones = {
    info: "text-info",
    success: "text-success",
    warning: "text-warning",
    danger: "text-danger",
  } as const;
  return (
    <div
      className={cn(
        "rounded-r border border-line border-l-2 px-4 py-3 text-[12px] leading-relaxed text-ink/90",
        tones[tone],
      )}
      role={tone === "danger" ? "alert" : undefined}
    >
      {title ? (
        <p className={cn("mb-1 font-mono text-[10px] uppercase tracking-[0.14em]", titleTones[tone])}>
          {title}
        </p>
      ) : null}
      {children}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Check results                                                              */
/* -------------------------------------------------------------------------- */

export function CheckList({
  items,
}: {
  items: {
    id: string;
    label: string;
    passed: boolean;
    hidden?: boolean;
    detail?: string | null;
    hint?: string | null;
    /**
     * The check is broken, so it graded nothing. Shown as our fault in its own
     * colour with a "validator config" badge — never as a red cross, which would
     * read as "your code is wrong" for a mistake in the ticket's spec.
     */
    config_error?: boolean;
  }[];
}) {
  if (items.length === 0) {
    return <p className="text-[11.5px] text-faint">No checks have run yet.</p>;
  }
  return (
    <ul className="divide-y divide-line/70">
      {items.map((item) => (
        <li key={item.id} className="flex gap-2.5 py-2 text-[12px] leading-relaxed first:pt-0">
          <span
            className={cn(
              "mt-[3px] flex h-3.5 w-3.5 flex-none items-center justify-center rounded-sm font-mono text-[9px] font-bold",
              item.config_error
                ? "bg-warning/15 text-warning"
                : item.passed
                  ? "bg-success/15 text-success"
                  : "bg-danger/15 text-danger",
            )}
          >
            {item.config_error ? "!" : item.passed ? "✓" : "✕"}
          </span>
          <span className="min-w-0">
            <span className={item.passed && !item.config_error ? "text-muted" : "text-ink"}>
              {item.label}
            </span>
            {item.config_error ? (
              <span className="ml-1.5 label text-warning">validator config error</span>
            ) : null}
            {item.hidden ? <span className="ml-1.5 label">hidden</span> : null}
            {/*
              `detail` reports what actually happened in this run (e.g. the
              runtime error the code threw); `hint` is the generic remedy. The
              specific one leads, and both are shown when they differ, because
              collapsing to one used to hide the only actionable message.
            */}
            {!item.passed && item.detail ? (
              <span className="mt-1 block break-words font-mono text-[10.5px] text-warning/90">
                {item.detail}
              </span>
            ) : null}
            {!item.passed && item.hint && item.hint !== item.detail ? (
              <span className="mt-1 block break-words font-mono text-[10.5px] text-faint">
                {item.hint}
              </span>
            ) : null}
          </span>
        </li>
      ))}
    </ul>
  );
}
