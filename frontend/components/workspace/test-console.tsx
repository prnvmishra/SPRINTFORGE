"use client";

import { useState, type ReactNode } from "react";

import { CheckList } from "@/components/ui/primitives";
import type { ExecutionResult } from "@/components/workspace/results-dock";
import type { CheckResult, PracticeModule } from "@/lib/types";
import { cn } from "@/lib/utils";

export type ConsoleTab = "testcase" | "result" | "output";

const TABS: { id: ConsoleTab; label: string }[] = [
  { id: "testcase", label: "Testcase" },
  { id: "result", label: "Result" },
  { id: "output", label: "Output" },
];

/**
 * Bottom console of the algorithm workspace.
 *
 * Three tabs, matching the mental model of a judge: the input you are about to
 * send, the verdict per case, and the raw stream the process wrote. It never
 * restates the problem — that lives in the left pane only.
 */
export function TestConsole({
  module,
  tab,
  onTabChange,
  stdin,
  onStdinChange,
  onRunCase,
  busy,
  execution,
  compileError,
  provider,
  passedCount,
  totalCount,
  customRun = false,
  checks,
  banner,
}: {
  module: PracticeModule;
  tab: ConsoleTab;
  onTabChange: (tab: ConsoleTab) => void;
  stdin: string;
  onStdinChange: (value: string) => void;
  onRunCase: () => void;
  busy: boolean;
  execution?: ExecutionResult[] | null;
  compileError?: string | null;
  provider?: string;
  passedCount?: number;
  totalCount?: number;
  customRun?: boolean;
  checks: CheckResult[];
  /** Verdict banner, warnings and failure analysis, owned by the page. */
  banner?: ReactNode;
}) {
  const graded = typeof passedCount === "number" && typeof totalCount === "number";
  const allPassed = graded && passedCount === totalCount;

  /**
   * The stdin behind a result row. A failure is only diagnosable next to the
   * input that produced it, so the case rows resolve it back from the module.
   * Hidden cases resolve to nothing on purpose — their inputs stay sealed.
   */
  const inputFor = (result: ExecutionResult) => {
    if (result.hidden) return undefined;
    if (customRun) return stdin;
    return module.sample_tests.find((sample) => sample.name === result.name)?.stdin;
  };

  return (
    <div className="flex h-full min-h-0 flex-col bg-canvas">
      <div className="flex flex-none items-center gap-3 border-b border-line pr-4">
        <div className="flex items-stretch">
          {TABS.map((item) => (
            <button
              key={item.id}
              onClick={() => onTabChange(item.id)}
              aria-pressed={tab === item.id}
              className={cn(
                "relative px-4 py-2.5 font-mono text-[10px] uppercase tracking-[0.1em] transition-colors duration-200",
                tab === item.id ? "text-ink" : "text-faint hover:text-muted",
              )}
            >
              {item.label}
              <span
                className={cn(
                  "absolute inset-x-0 -bottom-px h-px bg-accent transition-opacity duration-200",
                  tab === item.id ? "opacity-100" : "opacity-0",
                )}
                aria-hidden
              />
            </button>
          ))}
        </div>

        {graded && !customRun ? (
          <span
            className={cn(
              "font-mono text-[10px] tabular-nums",
              allPassed ? "text-success" : "text-warning",
            )}
          >
            {passedCount}/{totalCount} cases
          </span>
        ) : null}

        {provider ? (
          <span className="ml-auto font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
            runtime {provider}
          </span>
        ) : null}
      </div>

      <div className="min-h-0 flex-1 overflow-y-auto p-4">
        {tab === "testcase" ? (
          <TestcaseTab
            module={module}
            stdin={stdin}
            onStdinChange={onStdinChange}
            onRunCase={onRunCase}
            busy={busy}
          />
        ) : tab === "output" ? (
          <OutputTab execution={execution} compileError={compileError} />
        ) : (
          <ResultTab
            banner={banner}
            execution={execution}
            compileError={compileError}
            customRun={customRun}
            checks={checks}
            inputFor={inputFor}
          />
        )}
      </div>
    </div>
  );
}

/* -------------------------------------------------------------------- testcase */

function TestcaseTab({
  module,
  stdin,
  onStdinChange,
  onRunCase,
  busy,
}: {
  module: PracticeModule;
  stdin: string;
  onStdinChange: (value: string) => void;
  onRunCase: () => void;
  busy: boolean;
}) {
  const samples = module.sample_tests;

  return (
    <div className="space-y-4">
      {samples.length > 0 ? (
        <div>
          <p className="label mb-2">Load a sample case</p>
          <div className="flex flex-wrap gap-1.5">
            {samples.map((sample, index) => (
              <button
                key={sample.name}
                onClick={() => onStdinChange(sample.stdin)}
                className={cn(
                  "rounded border px-2.5 py-1 font-mono text-[10px] uppercase tracking-[0.08em] transition-colors duration-200",
                  sample.stdin === stdin
                    ? "border-accent/40 bg-accent/[0.08] text-accent"
                    : "border-line text-muted hover:border-line-strong hover:text-ink",
                )}
              >
                case {index + 1}
              </button>
            ))}
          </div>
        </div>
      ) : null}

      <div>
        <label htmlFor="stdin" className="label mb-2 block">
          stdin
        </label>
        <textarea
          id="stdin"
          className="input-mono min-h-[92px] py-2 text-[11.5px]"
          value={stdin}
          onChange={(event) => onStdinChange(event.target.value)}
          spellCheck={false}
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button onClick={onRunCase} className="btn-subtle btn-mono px-4 py-1.5" disabled={busy}>
          {busy ? "Running…" : "Run this case"}
        </button>
        <p className="font-mono text-[10px] leading-relaxed text-faint">
          output is compared for you on the sample cases · this box runs your own input and just
          prints what the program wrote
        </p>
      </div>

      {module.hidden_test_count > 0 ? (
        <p className="font-mono text-[10px] text-faint">
          + {module.hidden_test_count} hidden{" "}
          {module.hidden_test_count === 1 ? "case" : "cases"} graded on submit
        </p>
      ) : null}
    </div>
  );
}

/* ---------------------------------------------------------------------- result */

function ResultTab({
  banner,
  execution,
  compileError,
  customRun,
  checks,
  inputFor,
}: {
  banner?: ReactNode;
  execution?: ExecutionResult[] | null;
  compileError?: string | null;
  customRun: boolean;
  checks: CheckResult[];
  inputFor: (result: ExecutionResult) => string | undefined;
}) {
  const hasAnything =
    Boolean(banner) || Boolean(compileError) || (execution?.length ?? 0) > 0 || checks.length > 0;

  if (!hasAnything) {
    return (
      <p className="font-mono text-[11px] leading-relaxed text-faint">
        <span className="text-accent">$</span> run for deterministic feedback on the sample cases ·
        submit to grade the attempt and update your twin
      </p>
    );
  }

  return (
    <div className="space-y-4">
      {banner}

      {compileError ? (
        <div>
          <p className="label mb-2 text-danger">compile / runtime error</p>
          <pre className="overflow-x-auto whitespace-pre-wrap rounded border border-danger/25 bg-danger/[0.05] p-3 font-mono text-[11px] leading-relaxed text-danger">
            {compileError}
          </pre>
        </div>
      ) : null}

      {execution && execution.length > 0 ? (
        <ul className="space-y-2">
          {execution.map((result, index) => (
            <CaseRow
              key={result.name}
              result={result}
              index={index}
              customRun={customRun}
              input={inputFor(result)}
            />
          ))}
        </ul>
      ) : null}

      {checks.length > 0 ? (
        <div>
          <p className="label mb-2.5">requirement checks</p>
          <CheckList items={checks} />
        </div>
      ) : null}
    </div>
  );
}

/** One test case, collapsed to a verdict line until you want the comparison. */
function CaseRow({
  result,
  index,
  customRun,
  input,
}: {
  result: ExecutionResult;
  index: number;
  customRun: boolean;
  /** stdin that produced this result; absent for hidden cases. */
  input?: string;
}) {
  const [open, setOpen] = useState(!result.passed || customRun);
  const comparable = result.expected_stdout !== null && !customRun;

  return (
    <li
      className={cn(
        "border-l-2 bg-surface/40",
        result.passed ? "border-success/50" : "border-danger/50",
      )}
    >
      <button
        onClick={() => setOpen((value) => !value)}
        aria-expanded={open}
        className="flex w-full items-center gap-2.5 px-3 py-2 text-left font-mono text-[11px]"
      >
        <span className={result.passed ? "text-success" : "text-danger"}>
          {result.passed ? "✓" : "✕"}
        </span>
        <span className={result.passed ? "text-muted" : "text-ink"}>
          {result.hidden ? `Hidden case ${index + 1}` : result.name}
        </span>
        {result.timed_out ? (
          <span className="text-[9px] uppercase tracking-[0.1em] text-warning">timeout</span>
        ) : null}
        <span className="ml-auto flex items-center gap-2.5 text-faint">
          <span className="tabular-nums">{result.duration_ms}ms</span>
          <span aria-hidden className="text-[9px]">
            {open ? "▲" : "▼"}
          </span>
        </span>
      </button>

      {open ? (
        <div className="space-y-2.5 border-t border-line/60 px-3 py-2.5">
          {input !== undefined ? <Stream term="input" value={input} /> : null}

          {result.hidden ? (
            <p className="font-mono text-[10px] leading-relaxed text-faint">
              Hidden case — its input and expected output stay sealed so the solution has to
              generalise rather than fit the samples.
            </p>
          ) : null}

          {result.stderr ? (
            <Stream term="stderr" value={result.stderr} tone="danger" />
          ) : comparable ? (
            <Diff expected={result.expected_stdout ?? ""} actual={result.stdout} />
          ) : (
            <Stream term="stdout" value={result.stdout} />
          )}
        </div>
      ) : null}
    </li>
  );
}

/* ------------------------------------------------------------------------ diff */

function splitLines(value: string) {
  return value.replace(/\s+$/, "").split("\n");
}

/**
 * Line-for-line comparison of expected and actual stdout.
 *
 * Trailing whitespace is trimmed before comparing because the judge does the
 * same — showing a mismatch the grader ignores is worse than showing none. Where
 * two lines differ only in whitespace that is called out explicitly, since that
 * is the failure people stare at for an hour.
 */
function Diff({ expected, actual }: { expected: string; actual: string }) {
  const expectedLines = splitLines(expected);
  const actualLines = splitLines(actual);
  const count = Math.max(expectedLines.length, actualLines.length);
  const rows = Array.from({ length: count }, (_, index) => {
    const left = expectedLines[index];
    const right = actualLines[index];
    return {
      index,
      expected: left,
      actual: right,
      same: left === right,
      whitespaceOnly:
        left !== right &&
        left !== undefined &&
        right !== undefined &&
        left.replace(/\s+/g, "") === right.replace(/\s+/g, ""),
    };
  });

  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-px overflow-hidden rounded border border-line bg-line">
        <DiffColumn
          term="expected"
          rows={rows.map((row) => ({ ...row, value: row.expected }))}
        />
        <DiffColumn term="your output" rows={rows.map((row) => ({ ...row, value: row.actual }))} />
      </div>

      {rows.some((row) => row.whitespaceOnly) ? (
        <p className="font-mono text-[10px] leading-relaxed text-warning">
          a differing line matches once whitespace is removed — check separators and blank lines
        </p>
      ) : null}
    </div>
  );
}

function DiffColumn({
  term,
  rows,
}: {
  term: string;
  rows: { index: number; value: string | undefined; same: boolean }[];
}) {
  return (
    <div className="min-w-0 bg-canvas">
      <p className="border-b border-line px-2.5 py-1.5 font-mono text-[9px] uppercase tracking-[0.12em] text-faint">
        {term}
      </p>
      <div className="max-h-52 overflow-auto py-1">
        {rows.map((row) => (
          <div
            key={row.index}
            className={cn(
              "flex gap-2 px-2.5 py-px font-mono text-[10.5px] leading-[1.6]",
              row.same ? "text-muted" : "bg-danger/[0.07] text-ink",
            )}
          >
            <span className="w-4 flex-none select-none text-right tabular-nums text-faint/70">
              {row.index + 1}
            </span>
            <span className="min-w-0 whitespace-pre-wrap break-all">
              {row.value === undefined ? (
                <span className="text-faint/60">(no line)</span>
              ) : row.value === "" ? (
                <span className="text-faint/60">(empty)</span>
              ) : (
                row.value
              )}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------------- output */

function OutputTab({
  execution,
  compileError,
}: {
  execution?: ExecutionResult[] | null;
  compileError?: string | null;
}) {
  if (compileError) {
    return <Stream term="compile / runtime error" value={compileError} tone="danger" />;
  }

  if (!execution || execution.length === 0) {
    return (
      <p className="font-mono text-[11px] leading-relaxed text-faint">
        <span className="text-accent">$</span> nothing has run yet · the raw stdout and stderr of
        your program appear here
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {execution.map((result) => (
        <div key={result.name}>
          <p className="mb-1.5 font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
            {result.name}
          </p>
          <Stream term="stdout" value={result.stdout} />
          {result.stderr ? (
            <Stream term="stderr" value={result.stderr} tone="danger" className="mt-1.5" />
          ) : null}
        </div>
      ))}
    </div>
  );
}

function Stream({
  term,
  value,
  tone = "muted",
  className,
}: {
  term: string;
  value: string;
  tone?: "muted" | "danger";
  className?: string;
}) {
  return (
    <div className={className}>
      <p className="mb-1 font-mono text-[9px] uppercase tracking-[0.12em] text-faint">{term}</p>
      <pre
        className={cn(
          "max-h-52 overflow-auto whitespace-pre-wrap rounded border px-2.5 py-2 font-mono text-[10.5px] leading-relaxed",
          tone === "danger"
            ? "border-danger/25 bg-danger/[0.05] text-danger"
            : "border-line bg-canvas text-muted",
        )}
      >
        {value.trim() ? value : "(empty)"}
      </pre>
    </div>
  );
}
