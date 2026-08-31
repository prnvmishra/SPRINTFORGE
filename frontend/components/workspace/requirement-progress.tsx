"use client";

import type { CheckResult } from "@/lib/types";
import { cn } from "@/lib/utils";

/** "ungraded": no check grades this requirement, so it is never counted. */
type Status = "passed" | "failed" | "pending" | "ungraded";

export type RequirementRow = {
  requirement: string;
  status: Status;
  check: CheckResult | null;
  /** Every check that grades this requirement, in spec order. */
  checks: CheckResult[];
};

const STOP_WORDS = new Set([
  "a",
  "an",
  "and",
  "the",
  "for",
  "with",
  "that",
  "this",
  "your",
  "its",
  "to",
  "of",
  "in",
  "on",
  "is",
  "are",
  "be",
  "add",
  "use",
  "using",
  "must",
  "should",
  "each",
  "has",
  "have",
]);

function tokenize(value: string) {
  return new Set(
    value
      .toLowerCase()
      .replace(/[^a-z0-9<>#.\s-]/g, " ")
      .split(/\s+/)
      .filter((word) => word.length > 1 && !STOP_WORDS.has(word)),
  );
}

/**
 * A check that does not grade a requirement: one the spec excluded, or one that
 * is broken. A validator configuration error examined nothing, so it must never
 * mark a requirement unmet.
 */
function isPrecondition(check: CheckResult) {
  return check.precondition === true || check.config_error === true;
}

/** Did the spec declare what this check grades (even if the answer is "nothing")? */
function declaresMapping(check: CheckResult) {
  return (
    check.requirement_mapped === true ||
    check.requirement_index !== undefined ||
    check.requirement_indexes !== undefined ||
    check.precondition !== undefined
  );
}

function declaredIndexes(check: CheckResult): number[] {
  if (Array.isArray(check.requirement_indexes)) return check.requirement_indexes;
  return typeof check.requirement_index === "number" ? [check.requirement_index] : [];
}

/**
 * Infers the pairing from wording, for specs that predate the declared mapping.
 *
 * Each requirement takes its best-scoring unclaimed check; anything that cannot
 * clear the threshold is left alone rather than guessed at.
 */
function inferPairs(
  requirements: string[],
  checks: CheckResult[],
  openIndexes: Set<number>,
): Map<number, CheckResult> {
  const checkTokens = checks.map((check) => ({
    check,
    tokens: tokenize(`${check.label} ${check.concept ?? ""}`),
  }));
  const claimed = new Set<string>();

  const paired = requirements.map((requirement, index) => {
    if (!openIndexes.has(index)) return { check: null };
    const tokens = tokenize(requirement);
    let best: { check: CheckResult; score: number } | null = null;

    for (const candidate of checkTokens) {
      if (claimed.has(candidate.check.id)) continue;
      let shared = 0;
      for (const token of tokens) {
        if (candidate.tokens.has(token)) shared += 1;
      }
      // Normalise by the shorter side so a verbose check does not dominate.
      const score = shared / Math.max(1, Math.min(tokens.size, candidate.tokens.size));
      if (score >= 0.25 && (!best || score > best.score)) {
        best = { check: candidate.check, score };
      }
    }

    if (best) claimed.add(best.check.id);
    return { check: best?.check ?? null };
  });

  // Graders usually emit one check per requirement, in order. When the counts
  // line up, positional pairing is more reliable than wording overlap, so it
  // fills any gap token matching left behind.
  const alignable = checks.length === requirements.length;
  const pairs = new Map<number, CheckResult>();
  paired.forEach((row, index) => {
    if (!openIndexes.has(index)) return;
    const check = row.check ?? (alignable ? checks[index] : null);
    if (check) pairs.set(index, check);
  });
  return pairs;
}

/**
 * Pairs each requirement with the checks that grade it.
 *
 * Specs declare the pairing (`requirement_index` / `requirement_indexes`), so
 * it is applied verbatim and deterministically. Checks that predate the
 * declaration still fall back to matching by wording, and file-level
 * preconditions (e.g. "the file parses") never own a requirement.
 *
 * A requirement nothing grades is reported as "ungraded", never as unmet.
 */
function matchRequirements(
  requirements: string[],
  checks: CheckResult[],
): RequirementRow[] {
  const gradingChecks = checks.filter((check) => !isPrecondition(check));
  const declared = gradingChecks.filter(declaresMapping);
  const undeclared = gradingChecks.filter((check) => !declaresMapping(check));

  const byRequirement = new Map<number, CheckResult[]>();
  for (const check of declared) {
    for (const index of declaredIndexes(check)) {
      if (index < 0 || index >= requirements.length) continue;
      byRequirement.set(index, [...(byRequirement.get(index) ?? []), check]);
    }
  }

  // Only requirements the declared mapping left open are open to inference, so
  // an annotated spec is never second-guessed.
  const openIndexes = new Set(
    requirements.map((_, index) => index).filter((index) => !byRequirement.has(index)),
  );
  if (undeclared.length && openIndexes.size) {
    for (const [index, check] of inferPairs(requirements, undeclared, openIndexes)) {
      byRequirement.set(index, [check]);
    }
  }

  // The grader's verdict wins over anything derived here: when every check
  // passed, the panel must never claim a requirement is unmet.
  const verdictChecks = checks.filter((check) => check.config_error !== true);
  const allPassed = verdictChecks.length > 0 && verdictChecks.every((check) => check.passed);

  return requirements.map((requirement, index) => {
    const owned = byRequirement.get(index) ?? [];
    if (!owned.length) {
      return { requirement, status: "ungraded" as Status, check: null, checks: [] };
    }
    const failed = owned.find((check) => !check.passed) ?? null;
    const status: Status = !failed || allPassed ? "passed" : "failed";
    return {
      requirement,
      status,
      check: status === "passed" ? owned[0] : failed,
      checks: owned,
    };
  });
}

/**
 * Requirements as a live checklist.
 *
 * Once code has been run, every requirement carries the verdict of the check
 * that grades it, and the first unmet requirement is highlighted as the current
 * task — so the brief tracks progress instead of staying a static list.
 */
export function RequirementList({
  requirements,
  checks,
  /** Suppresses statuses until the learner has actually run something. */
  graded,
}: {
  requirements: string[];
  checks: CheckResult[];
  graded: boolean;
}) {
  const rows = graded ? matchRequirements(requirements, checks) : null;
  // The ratio counts graded requirements only: a requirement nothing checks can
  // never be reported as unmet, so it is not in the denominator either.
  const gradedRows = rows?.filter((row) => row.status !== "ungraded") ?? [];
  const passedCount = gradedRows.filter((row) => row.status === "passed").length;
  const ungradedCount = (rows?.length ?? 0) - gradedRows.length;
  // The current task: the first requirement that is genuinely graded and unmet.
  const currentIndex = rows ? rows.findIndex((row) => row.status === "failed") : 0;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <p className="label">Requirements</p>
        {rows && gradedRows.length === 0 ? (
          // Nothing here is machine-checked, so a "0/0 met" ratio would be a lie
          // in either direction.
          <p className="font-mono text-[10px] text-faint">not auto-graded</p>
        ) : null}
        {rows && gradedRows.length > 0 ? (
          <p
            className={cn(
              "font-mono text-[10px] tabular-nums",
              passedCount === gradedRows.length ? "text-success" : "text-warning",
            )}
          >
            {passedCount}/{gradedRows.length} met
            {ungradedCount > 0 ? (
              <span className="text-faint"> · {ungradedCount} not graded</span>
            ) : null}
          </p>
        ) : null}
      </div>

      {/* Segmented progress: one cell per requirement */}
      {rows ? (
        <div className="mt-2.5 flex gap-px" aria-hidden>
          {rows.map((row, index) => (
            <span
              key={row.requirement}
              className={cn(
                "h-[3px] flex-1 transition-colors duration-500 ease-forge",
                row.status === "passed"
                  ? "bg-success"
                  : index === currentIndex
                    ? "bg-accent"
                    : "bg-elevated",
              )}
            />
          ))}
        </div>
      ) : null}

      <ul className="mt-3 space-y-px">
        {(
          rows ??
          requirements.map((requirement) => ({
            requirement,
            status: "pending" as Status,
            check: null,
            checks: [] as CheckResult[],
          }))
        ).map(
          (row, index) => {
            const isCurrent = rows !== null && index === currentIndex;
            return (
              <li
                key={row.requirement}
                className={cn(
                  "flex gap-2.5 border-l-2 py-2 pl-3 text-[12px] leading-relaxed transition-colors duration-300",
                  row.status === "passed"
                    ? "border-success/50"
                    : isCurrent
                      ? "border-accent bg-accent/[0.05]"
                      : row.status === "failed"
                        ? "border-danger/40"
                        : "border-line",
                )}
              >
                <span
                  className={cn(
                    "mt-px flex-none font-mono text-[9.5px]",
                    row.status === "passed"
                      ? "text-success"
                      : row.status === "failed"
                        ? "text-danger"
                        : isCurrent
                          ? "text-accent"
                          : "text-faint",
                  )}
                >
                  {row.status === "passed" ? "✓" : row.status === "failed" ? "✕" : String(index + 1).padStart(2, "0")}
                </span>

                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      row.status === "passed"
                        ? "text-faint line-through decoration-success/40"
                        : isCurrent
                          ? "text-ink"
                          : "text-muted",
                    )}
                  >
                    {row.requirement}
                  </span>

                  {isCurrent && row.status === "failed" ? (
                    <span className="mt-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-accent">
                      current task
                    </span>
                  ) : null}

                  {/* Said plainly rather than shown as a failure: no check grades this. */}
                  {row.status === "ungraded" && gradedRows.length > 0 ? (
                    <span className="mt-1 block font-mono text-[9px] uppercase tracking-[0.12em] text-faint">
                      not graded automatically
                    </span>
                  ) : null}

                  {/* The grader's own hint, only once it has something to say. */}
                  {row.status === "failed" && row.check?.hint ? (
                    <span className="mt-1 block text-[11px] leading-relaxed text-faint">
                      {row.check.hint}
                    </span>
                  ) : null}
                </span>
              </li>
            );
          },
        )}
      </ul>
    </div>
  );
}
