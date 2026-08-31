import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}

export type Tone = "accent" | "success" | "warning" | "danger" | "muted";

export function confidenceTone(confidence: number, threshold = 65): {
  text: string;
  bar: string;
  label: string;
  tone: Tone;
} {
  if (confidence >= 85)
    return { text: "text-success", bar: "bg-success", label: "Advanced", tone: "success" };
  if (confidence >= threshold)
    return { text: "text-accent", bar: "bg-accent", label: "Verified", tone: "accent" };
  if (confidence >= 40)
    return { text: "text-warning", bar: "bg-warning", label: "Developing", tone: "warning" };
  return { text: "text-danger", bar: "bg-danger", label: "Needs work", tone: "danger" };
}

export function difficultyLabel(difficulty: number): string {
  if (difficulty <= 3) return "Easy";
  if (difficulty <= 6) return "Medium";
  return "Hard";
}

export function statusTone(status: string): string {
  switch (status) {
    case "done":
    case "verified":
      return "border-success/30 bg-success/[0.08] text-success";
    case "in_progress":
      return "border-accent/30 bg-accent/[0.08] text-accent";
    case "failed":
      return "border-danger/30 bg-danger/[0.08] text-danger";
    case "under_review":
    case "analyzing":
    case "submitted":
      return "border-warning/30 bg-warning/[0.08] text-warning";
    case "locked":
      return "border-line bg-elevated text-faint";
    default:
      return "border-line bg-elevated text-muted";
  }
}

/** Small glyph that reads as a status even without colour. */
export function statusGlyph(status: string): string {
  switch (status) {
    case "done":
    case "verified":
      return "●";
    case "in_progress":
      return "◐";
    case "failed":
      return "▲";
    case "submitted":
    case "under_review":
    case "analyzing":
      return "◇";
    case "locked":
      return "✕";
    default:
      return "○";
  }
}

export function humanStatus(status: string): string {
  return status
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}

/**
 * True when a request was cancelled deliberately (e.g. the learner moved on).
 * Aborts are not failures and must never surface as errors.
 */
export function isAbort(error: unknown): boolean {
  return error instanceof Error && error.name === "AbortError";
}

/**
 * Turns anything thrown by the API layer into copy we are willing to show.
 *
 * Backend `detail` strings are written for humans and are kept, but unhandled
 * server errors, transport failures and stack-like payloads are replaced with a
 * calm, actionable sentence instead of leaking internals.
 */
export function errorMessage(error: unknown): string {
  const raw = error instanceof Error ? error.message : String(error ?? "");
  const status = (error as { status?: number } | null)?.status;

  if (status === 0) {
    return "We can't reach SprintForge right now. Check your connection and try again.";
  }
  if (status === 401 || status === 403) {
    return "Your session expired. Sign in again to continue.";
  }
  if (status === 404) {
    return "We couldn't find that. It may have been reset or renamed.";
  }
  if (status === 429) {
    return "That was a lot of requests at once. Give it a moment and retry.";
  }
  if (status && status >= 500) {
    return "Something failed on our side. Nothing you did was lost — try again in a moment.";
  }

  // Anything that looks like an internal error rather than a message for a person.
  const looksInternal =
    !raw ||
    raw.length > 220 ||
    /traceback|exception|<[^>]+>|\bat \w+\.\w+|sqlalchemy|psycopg/i.test(raw);

  return looksInternal ? "Something went wrong. Please try that again." : raw;
}

export function relativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  if (Number.isNaN(then)) return "";
  const seconds = Math.round((Date.now() - then) / 1000);
  if (seconds < 60) return "just now";
  const minutes = Math.round(seconds / 60);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.round(hours / 24);
  return `${days}d ago`;
}

export function languageForFile(filename: string): string {
  if (filename.endsWith(".html")) return "html";
  if (filename.endsWith(".css")) return "css";
  if (filename.endsWith(".jsx")) return "javascript";
  if (filename.endsWith(".tsx") || filename.endsWith(".ts")) return "typescript";
  if (filename.endsWith(".js")) return "javascript";
  if (filename.endsWith(".sql")) return "sql";
  if (filename.endsWith(".py")) return "python";
  return "plaintext";
}

export const MONACO_LANGUAGE: Record<string, string> = {
  python: "python",
  javascript: "javascript",
  typescript: "typescript",
  java: "java",
  c: "c",
  cpp: "cpp",
};
