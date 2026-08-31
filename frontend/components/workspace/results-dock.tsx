"use client";

import { ReactNode } from "react";

import { CheckList } from "@/components/ui/primitives";
import type { CheckResult } from "@/lib/types";
import { cn } from "@/lib/utils";

export type ExecutionResult = {
  name: string;
  passed: boolean;
  hidden: boolean;
  stdout: string;
  stderr: string;
  expected_stdout: string | null;
  duration_ms: number;
  timed_out: boolean;
};

/**
 * Bottom dock of the workspace: the machine's output.
 *
 * Styled as a terminal rather than a set of cards, because that is what it is —
 * process output, assertion results and timings.
 */
export function ResultsDock({
  checks,
  execution,
  compileError,
  provider,
  checkCount,
  passedCount,
  totalCount,
  customRun = false,
  emptyHint,
  children,
}: {
  checks: CheckResult[];
  execution?: ExecutionResult[] | null;
  compileError?: string | null;
  provider?: string;
  /** How many of `checks` are static checks; the rest are behaviour tests. */
  checkCount?: number;
  passedCount?: number;
  totalCount?: number;
  customRun?: boolean;
  emptyHint?: ReactNode;
  children?: ReactNode;
}) {
  const allStaticChecks = typeof checkCount === "number" ? checks.slice(0, checkCount) : checks;
  // A broken check graded nothing, so it belongs in neither side of the ratio;
  // counting it as a failure would report the validator's bug as the learner's.
  const configErrors = allStaticChecks.filter((item) => item.config_error);
  const staticChecks = allStaticChecks.filter((item) => !item.config_error);
  const passedChecks = staticChecks.filter((item) => item.passed).length;
  const hasAnything =
    checks.length > 0 || (execution && execution.length > 0) || compileError || children;

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas">
      {/* Dock status line */}
      <div className="flex flex-none items-center gap-3 border-b border-line px-4 py-2">
        <span className="font-mono text-[9.5px] uppercase tracking-[0.14em] text-faint">
          output
        </span>
        {staticChecks.length > 0 ? (
          <span
            className={cn(
              "font-mono text-[10px] tabular-nums",
              passedChecks === staticChecks.length ? "text-success" : "text-warning",
            )}
          >
            {passedChecks}/{staticChecks.length} checks
          </span>
        ) : null}
        {configErrors.length > 0 ? (
          <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-warning">
            {configErrors.length} validator config error
            {configErrors.length === 1 ? "" : "s"}
          </span>
        ) : null}
        {typeof passedCount === "number" && typeof totalCount === "number" ? (
          <span
            className={cn(
              "font-mono text-[10px] tabular-nums",
              passedCount === totalCount ? "text-success" : "text-warning",
            )}
          >
            {passedCount}/{totalCount} tests
          </span>
        ) : null}
        {provider ? (
          <span className="ml-auto font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
            runtime {provider}
          </span>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {children}

        {compileError ? (
          <div className="mb-4">
            <p className="label mb-2 text-danger">compile / runtime error</p>
            <pre className="overflow-x-auto whitespace-pre-wrap rounded border border-danger/25 bg-danger/[0.05] p-3 font-mono text-[11px] leading-relaxed text-danger">
              {compileError}
            </pre>
          </div>
        ) : null}

        {execution && execution.length > 0 ? (
          <div className="mb-5">
            <p className="label mb-2.5">execution</p>
            <ul className="space-y-px">
              {execution.map((result) => (
                <li
                  key={result.name}
                  className={cn(
                    "border-l-2 py-2 pl-3",
                    result.passed ? "border-success/50" : "border-danger/50",
                  )}
                >
                  <p className="flex items-center justify-between gap-2 font-mono text-[11px]">
                    <span className={result.passed ? "text-muted" : "text-ink"}>
                      <span className={result.passed ? "text-success" : "text-danger"}>
                        {result.passed ? "✓" : "✕"}
                      </span>{" "}
                      {result.name}
                      {result.hidden ? (
                        <span className="ml-2 text-[9px] uppercase tracking-[0.1em] text-faint">
                          hidden
                        </span>
                      ) : null}
                    </span>
                    <span className="flex-none tabular-nums text-faint">
                      {result.timed_out ? "timeout" : `${result.duration_ms}ms`}
                    </span>
                  </p>
                  {customRun || !result.passed ? (
                    <pre className="mt-1.5 max-h-40 overflow-auto whitespace-pre-wrap font-mono text-[10.5px] leading-relaxed text-faint">
                      {result.stderr
                        ? result.stderr
                        : `got      ${result.stdout.trim() || "(empty)"}${
                            result.expected_stdout !== null && !customRun
                              ? `\nexpected ${result.expected_stdout}`
                              : ""
                          }`}
                    </pre>
                  ) : null}
                </li>
              ))}
            </ul>
          </div>
        ) : null}

        {checks.length > 0 ? (
          <div>
            <p className="label mb-2.5">requirement checks</p>
            <CheckList items={checks} />
          </div>
        ) : null}

        {!hasAnything && emptyHint ? (
          <div className="font-mono text-[11px] leading-relaxed text-faint">
            <span className="text-accent">$</span> {emptyHint}
          </div>
        ) : null}
      </div>
    </div>
  );
}
