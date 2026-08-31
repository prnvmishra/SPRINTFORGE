"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { GrowBar } from "@/components/motion";
import { Alert, Badge, Loader, StatusPill } from "@/components/ui/primitives";
import { CodeEditor, FileTabs, PreviewFrame } from "@/components/workspace/code-editor";
import { FailureAnalysisPanel } from "@/components/workspace/failure-analysis";
import { MentorPanel } from "@/components/workspace/mentor-panel";
import {
  ContextLine,
  EvidenceChain,
  PathContextPanel,
} from "@/components/workspace/path-context";
import { RequirementList } from "@/components/workspace/requirement-progress";
import { ResultsDock } from "@/components/workspace/results-dock";
import { SplitPane } from "@/components/workspace/split-pane";
import { api } from "@/lib/api";
import { buildPreview, canPreview, composeProjectFiles } from "@/lib/preview";
import type { CheckResult, PreviewMeta, Ticket, TicketSubmitResult } from "@/lib/types";
import { cn, errorMessage, isAbort, languageForFile } from "@/lib/utils";

type RunResult = {
  static_results: CheckResult[];
  passed_count: number;
  total_count: number;
  test_results?: CheckResult[];
  tests_passed_count?: number;
  tests_total_count?: number;
  preview: string | null;
  preview_meta?: PreviewMeta;
  preview_files?: Record<string, string>;
};

/** How long after the last keystroke the preview recomposes. */
const PREVIEW_DEBOUNCE_MS = 400;

export default function TicketWorkspacePage() {
  const params = useParams<{ ticketId: string }>();
  const ticketId = params.ticketId;
  const queryClient = useQueryClient();

  const ticketQuery = useQuery({
    queryKey: ["ticket", ticketId],
    queryFn: () => api<Ticket>(`/tickets/${ticketId}`),
  });

  /**
   * Editor buffers live in a ref, not state.
   *
   * Monaco is uncontrolled (it takes `defaultValue` per model), so React never
   * needs to re-render on a keystroke — it only needs the current text when the
   * learner runs, previews or submits. Keeping this out of state is what makes
   * typing and every surrounding interaction stay smooth.
   */
  const filesRef = useRef<Record<string, string>>({});
  /**
   * The rest of the project: files from earlier verified tickets, as the API
   * assembled them for the cumulative preview.
   *
   * Most tickets after the first own no `index.html` — the project's markup was
   * written once and lives in an earlier ticket — so composing a preview from
   * the ticket's own files alone produces nothing at all, and the pane freezes
   * on whatever was fetched at page load. Keeping the project map client-side
   * lets every recompose layer the live buffers over the stored copies locally.
   */
  const projectFilesRef = useRef<Record<string, string>>({});
  /** File list only changes when the workspace is loaded or reset. */
  const [fileNames, setFileNames] = useState<string[]>([]);
  const [activeFile, setActiveFile] = useState("");
  /** Mirrors `activeFile` for use inside Monaco's change handler. */
  const activeFileRef = useRef("");
  const [preview, setPreview] = useState<string | null>(null);
  const [previewable, setPreviewable] = useState(false);
  const [previewMeta, setPreviewMeta] = useState<PreviewMeta | null>(null);
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [submitResult, setSubmitResult] = useState<TicketSubmitResult | null>(null);
  const [status, setStatus] = useState<string>("todo");
  const [busy, setBusy] = useState<"start" | "run" | "submit" | "reset" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tab, setTab] = useState<"ticket" | "preview" | "mentor">("ticket");
  const [showTicket, setShowTicket] = useState(false);
  // Bumped whenever files are replaced wholesale (load, Start, Reset) to force the
  // editor to remount and pick up the new buffer contents.
  const [revision, setRevision] = useState(0);
  const startedAt = useRef(Date.now());

  const ticket = ticketQuery.data;

  /**
   * Loads the workspace once per ticket.
   *
   * Keyed on the ticket id rather than the query object: a background refetch
   * returns a new object identity, and re-running this would throw away
   * unsaved edits, reset the open tab and remount the editor.
   */
  const loadedTicketRef = useRef<string | null>(null);
  useEffect(() => {
    if (!ticket || loadedTicketRef.current === ticket.id) return;
    loadedTicketRef.current = ticket.id;

    const loaded = ticket.files ?? {};
    filesRef.current = { ...loaded };
    projectFilesRef.current = { ...(ticket.preview_files ?? {}) };
    const names = Object.keys(loaded);
    setFileNames(names);
    const first = ticket.editable_files?.[0] ?? names[0] ?? "";
    setActiveFile(first);
    activeFileRef.current = first;
    setStatus(ticket.status);
    // The API ships the cumulative project preview with the ticket, so the tab
    // is populated on open rather than only after a Run.
    setPreview(ticket.preview ?? null);
    setPreviewMeta(ticket.preview_meta ?? null);
    setPreviewable(canPreview(composeProjectFiles(projectFilesRef.current, loaded)));
    setRunResult(null);
    setSubmitResult(null);
    setError(null);
    setTab(ticket.preview || canPreview(composeProjectFiles(projectFilesRef.current, loaded)) ? "preview" : "ticket");
    setRevision((r) => r + 1);
    startedAt.current = Date.now();
  }, [ticket]);

  /**
   * Composes the whole project as it stands right now: the stored files from
   * earlier verified tickets, with the learner's live buffers layered on top so
   * an unsaved edit always wins over the verified copy.
   *
   * Purely local, and nothing composed here is ever sent back — grading reads
   * the workspace files the server already holds.
   */
  const composeLive = useCallback(
    () => buildPreview(composeProjectFiles(projectFilesRef.current, filesRef.current)),
    [],
  );

  /**
   * Recompose on a trailing debounce.
   *
   * Composition is a few string replacements, so it is cheap enough to run on
   * every pause in typing; the reason for the delay is the iframe, which
   * reloads whenever `srcDoc` changes and would flicker and lose scroll
   * position if that happened per character. The identity check below keeps a
   * no-op edit (retyping the same text, or editing a file the document does not
   * use) from reloading it at all.
   */
  const previewTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const schedulePreview = useCallback(() => {
    if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
    previewTimerRef.current = setTimeout(() => {
      previewTimerRef.current = null;
      const next = composeLive();
      setPreviewable(next !== null);
      if (next === null) return;
      setPreview((current) => (current === next ? current : next));
    }, PREVIEW_DEBOUNCE_MS);
  }, [composeLive]);

  useEffect(() => {
    return () => {
      if (previewTimerRef.current) clearTimeout(previewTimerRef.current);
      previewTimerRef.current = null;
    };
  }, [ticketId]);

  /** Aborts in-flight work when the learner navigates to another ticket. */
  const abortRef = useRef<AbortController | null>(null);
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      abortRef.current = null;
    };
  }, [ticketId]);

  const nextSignal = useCallback(() => {
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    return controller.signal;
  }, []);

  /** Replaces every buffer, e.g. after Start or Reset. */
  const loadFiles = useCallback(
    (loaded: Record<string, string>) => {
      filesRef.current = { ...loaded };
      setFileNames(Object.keys(loaded));
      setPreviewable(canPreview(composeProjectFiles(projectFilesRef.current, loaded)));
      setRevision((r) => r + 1);
    },
    [],
  );

  /**
   * Refreshes the views that this action changed, without blocking the button.
   *
   * The ticket query is deliberately excluded: its status is already applied
   * locally, and refetching it would replace the buffers the learner is editing.
   */
  function refreshRelated() {
    void queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    void queryClient.invalidateQueries({ queryKey: ["project"] });
    void queryClient.invalidateQueries({ queryKey: ["twin"] });
  }

  async function start() {
    setBusy("start");
    setError(null);
    try {
      const updated = await api<Ticket>(`/tickets/${ticketId}/start`, {
        method: "POST",
        signal: nextSignal(),
      });
      if (updated.preview_files) projectFilesRef.current = { ...updated.preview_files };
      loadFiles(updated.files ?? {});
      setStatus(updated.status);
      if (updated.preview) setPreview(updated.preview);
      if (updated.preview_meta) setPreviewMeta(updated.preview_meta);
      startedAt.current = Date.now();
      refreshRelated();
    } catch (startError) {
      if (!isAbort(startError)) setError(errorMessage(startError));
    } finally {
      setBusy(null);
    }
  }

  /**
   * Renders the current buffers into the preview pane.
   *
   * Local and synchronous, so it is independent of validation and of the
   * network — pressing Run never waits on checks and never blocks the UI.
   */
  const runPreview = useCallback(() => {
    // Composed from the whole project, so a CSS- or JS-only ticket renders too.
    // When even that yields nothing, keeping the last render beats blanking.
    const local = composeLive();
    if (local) setPreview(local);
    setTab("preview");
  }, [composeLive]);

  async function runChecks() {
    setBusy("run");
    setError(null);
    // Show the learner's markup immediately; checks arrive when they arrive.
    const local = composeLive();
    if (local) setPreview(local);
    try {
      const result = await api<RunResult>(`/tickets/${ticketId}/run`, {
        method: "POST",
        body: { files: filesRef.current },
        signal: nextSignal(),
      });
      setRunResult(result);
      setSubmitResult(null);
      if (result.preview_files) projectFilesRef.current = { ...result.preview_files };
      if (result.preview) setPreview(result.preview);
      if (result.preview_meta) setPreviewMeta(result.preview_meta);
    } catch (runError) {
      if (!isAbort(runError)) setError(errorMessage(runError));
    } finally {
      setBusy(null);
    }
  }

  async function submit() {
    setBusy("submit");
    setError(null);
    try {
      const result = await api<TicketSubmitResult>(`/tickets/${ticketId}/submit`, {
        method: "POST",
        body: {
          files: filesRef.current,
          duration_seconds: (Date.now() - startedAt.current) / 1000,
        },
        signal: nextSignal(),
      });
      setSubmitResult(result);
      setRunResult(null);
      setStatus(result.ticket.status);
      refreshRelated();
    } catch (submitError) {
      if (!isAbort(submitError)) setError(errorMessage(submitError));
    } finally {
      setBusy(null);
    }
  }

  /** Writes straight to the buffer ref — intentionally does not set state. */
  const updateFile = useCallback(
    (file: string, value: string) => {
      const writable = ticket?.editable_files ?? [];
      if (status === "locked") return;
      if (writable.length > 0 && !writable.includes(file)) return;
      filesRef.current = { ...filesRef.current, [file]: value };
      schedulePreview();
    },
    [ticket?.editable_files, status, schedulePreview],
  );

  /**
   * Attributing a change to the ref rather than the render closure is what keeps
   * a change event raised during a model swap from being written into the file
   * the learner just left.
   */
  const handleEditorChange = useCallback(
    (value: string) => updateFile(activeFileRef.current, value),
    [updateFile],
  );

  /** Reads the live buffer on demand, so the mentor never needs a render to see it. */
  const getActiveCode = useCallback(
    () => filesRef.current[activeFileRef.current] ?? "",
    [],
  );

  const selectFile = useCallback((file: string) => {
    activeFileRef.current = file;
    setActiveFile(file);
  }, []);

  async function reset() {
    setBusy("reset");
    try {
      const updated = await api<Ticket>(`/tickets/${ticketId}/reset`, {
        method: "POST",
        signal: nextSignal(),
      });
      if (updated.preview_files) projectFilesRef.current = { ...updated.preview_files };
      loadFiles(updated.files ?? {});
      setStatus(updated.status);
      setRunResult(null);
      setSubmitResult(null);
      setPreview(updated.preview ?? null);
      setPreviewMeta(updated.preview_meta ?? null);
    } catch (resetError) {
      if (!isAbort(resetError)) setError(errorMessage(resetError));
    } finally {
      setBusy(null);
    }
  }

  if (ticketQuery.isLoading) {
    return (
      <AppShell wide>
        <div className="grid min-h-[60vh] place-items-center">
          <Loader label="Opening ticket workspace" />
        </div>
      </AppShell>
    );
  }

  if (ticketQuery.error || !ticket) {
    return (
      <AppShell wide>
        <Alert tone="danger" title="Ticket unavailable">
          {errorMessage(ticketQuery.error) || "Ticket not found."}
        </Alert>
      </AppShell>
    );
  }

  const editable = ticket.editable_files ?? [];
  // Static checks and behaviour tests are two distinct layers: show both, and
  // never report the same list twice under two labels.
  const source = submitResult ?? runResult;
  const staticChecks = source?.static_results ?? [];
  const behaviourTests = source?.test_results ?? [];
  const checks = [...staticChecks, ...behaviourTests];
  const locked = status === "locked";
  const failingChecks = checks.filter((item) => !item.passed).map((item) => item.label);

  return (
    <AppShell wide bleed>
      {/* ------------------------------------------------------ ticket bar */}
      <div className="sticky top-12 z-30 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto max-w-[1800px] px-4 py-3 sm:px-6">
          {/* Breadcrumb: project / milestone / sprint */}
          <div className="flex flex-wrap items-center gap-2 font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
            {ticket.project_id ? (
              <Link
                href={`/projects/${ticket.project_id}`}
                className="transition-colors hover:text-ink"
              >
                {ticket.project_title}
              </Link>
            ) : (
              <span>{ticket.project_title}</span>
            )}
            <span className="text-line-strong">/</span>
            <span>{ticket.milestone}</span>
            <span className="text-line-strong">/</span>
            <span className="text-muted">{ticket.sprint_name}</span>
          </div>

          <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2">
            <span className="font-mono text-[12px] text-accent">{ticket.key}</span>
            <h1 className="min-w-0 truncate text-[14px] font-medium text-ink">{ticket.title}</h1>
            <StatusPill status={status} />
            <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {ticket.target_skill_name} · L{ticket.difficulty}
            </span>

            <div className="ml-auto flex flex-wrap items-center gap-2">
              <button
                onClick={() => setShowTicket((value) => !value)}
                className="btn-ghost btn-mono px-3 py-1.5 xl:hidden"
              >
                {showTicket ? "Hide brief" : "Brief"}
              </button>
              {status === "todo" || locked ? (
                <button
                  onClick={() => void start()}
                  className="btn-primary btn-mono px-4 py-1.5"
                  disabled={busy !== null}
                >
                  {busy === "start" ? "Starting…" : "Start ticket →"}
                </button>
              ) : (
                <>
                  <button
                    onClick={() => void reset()}
                    className="btn-ghost btn-mono px-3 py-1.5"
                    disabled={busy !== null || locked}
                  >
                    Reset
                  </button>
                  {/* Render is separate from validation: it is instant, local,
                      and never gated behind Run checks. */}
                  {previewable ? (
                    <button
                      onClick={runPreview}
                      className="btn-ghost btn-mono px-3 py-1.5"
                      disabled={locked}
                    >
                      Run ▸
                    </button>
                  ) : null}
                  <button
                    onClick={() => void runChecks()}
                    className="btn-subtle btn-mono px-4 py-1.5"
                    disabled={busy !== null || locked}
                  >
                    {busy === "run" ? "Running…" : "Run checks"}
                  </button>
                  <button
                    onClick={() => void submit()}
                    className="btn-primary btn-mono px-4 py-1.5"
                    disabled={busy !== null || locked}
                  >
                    {busy === "submit" ? "Reviewing…" : "Submit →"}
                  </button>
                </>
              )}
            </div>
          </div>
        </div>
      </div>

      {locked && ticket.lock_reason ? (
        <div className="mx-auto max-w-[1800px] px-4 pt-4 sm:px-6">
          <Alert tone="warning" title="Ticket locked">
            {ticket.lock_reason}
          </Alert>
        </div>
      ) : null}

      {/* --------------------------------------------------- editor + panes */}
      {/*
        The rail was a fixed 380px, which was too narrow for its own content:
        long brief text and the route context collided inside it. It is a split
        now so the learner can trade editor width for reading width, and the
        ratio is remembered per browser.
      */}
      <div className="mx-auto max-w-[1800px] xl:h-[calc(100vh-8.5rem)]">
        <SplitPane
          orientation="horizontal"
          storageKey="ticket-workspace"
          initial={64}
          min={40}
          max={86}
          splitFrom="(min-width: 1280px)"
          className="h-full"
          first={
        <section className="flex h-full min-h-0 min-w-0 flex-col bg-canvas">
          <FileTabs
            files={fileNames}
            active={activeFile}
            editable={editable}
            onSelect={selectFile}
          />
          <div className="min-h-[320px] flex-1 xl:min-h-0">
            <CodeEditor
              path={`${ticket.id}/r${revision}/${activeFile}`}
              value={filesRef.current[activeFile] ?? ""}
              language={languageForFile(activeFile)}
              readOnly={locked || (editable.length > 0 && !editable.includes(activeFile))}
              onChange={handleEditorChange}
              onRun={() => void runChecks()}
              onSubmit={() => {
                if (!locked) void submit();
              }}
            />
          </div>

          <div className="min-h-[120px] flex-none border-t border-line xl:h-[38%] xl:min-h-[210px]">
            <ResultsDock
              checks={checks}
              checkCount={staticChecks.length}
              passedCount={behaviourTests.filter((item) => item.passed).length}
              totalCount={behaviourTests.length || undefined}
              emptyHint="run checks for deterministic feedback · submit for review and verification"
            >
              {error ? (
                <div className="mb-4">
                  <Alert tone="danger">{error}</Alert>
                </div>
              ) : null}

              {submitResult ? (
                <div className="mb-4">
                  <TicketVerdict
                    result={submitResult}
                    projectId={ticket.project_id ?? ""}
                  />
                </div>
              ) : null}

              {submitResult?.failure_analysis ? (
                <div className="mb-4">
                  <FailureAnalysisPanel
                    analysis={submitResult.failure_analysis}
                    confidence={submitResult.skill.confidence}
                    goalContext={ticket.project_title}
                  />
                </div>
              ) : null}
            </ResultsDock>
          </div>
        </section>
          }
          /* Right rail: ticket brief, preview, mentor */
          second={
        <aside
          className={cn(
            "h-full min-h-0 flex-col bg-surface xl:flex",
            showTicket ? "flex" : "hidden xl:flex",
          )}
        >
          <div className="flex flex-none border-b border-line">
            {(["ticket", "preview", "mentor"] as const).map((item) => (
              <button
                key={item}
                onClick={() => setTab(item)}
                aria-pressed={tab === item}
                className={cn(
                  "relative flex-1 px-3 py-2.5 font-mono text-[10px] uppercase tracking-[0.12em] transition-colors",
                  tab === item ? "text-ink" : "text-faint hover:text-muted",
                )}
              >
                {item === "mentor" ? "AI Mentor" : item}
                <span
                  className={cn(
                    "absolute inset-x-0 -bottom-px h-px bg-accent transition-opacity",
                    tab === item ? "opacity-100" : "opacity-0",
                  )}
                />
              </button>
            ))}
          </div>

          {/* All three panels stay mounted and are toggled with CSS: switching tabs
              then costs nothing, the preview iframe does not re-execute, and the
              mentor conversation survives a trip to the brief. */}
          <div className="min-h-[300px] flex-1 overflow-y-auto xl:min-h-0">
            <div
              className={cn(
                "flex h-full min-h-[300px] flex-col",
                tab === "preview" ? "flex" : "hidden",
              )}
            >
              {preview && previewMeta ? (
                <ProjectProgressStrip meta={previewMeta} projectId={ticket.project_id} />
              ) : null}
              <div className="min-h-0 flex-1">
                <PreviewFrame html={preview} previewable={previewable} />
              </div>
            </div>

            <div className={cn("p-4", tab === "mentor" ? "block" : "hidden")}>
              <MentorPanel
                skillId={ticket.target_skill_id}
                skillName={ticket.target_skill_name}
                ticketId={ticket.id}
                getCode={getActiveCode}
                failingChecks={failingChecks}
              />
            </div>

            <div className={tab === "ticket" ? "block" : "hidden"}>
              <div className="space-y-6 p-5">
                {/* The ticket is a unit of work; this states the skill it is
                    there to raise and why it sits where it does. */}
                <PathContextPanel
                  skillId={ticket.target_skill_id}
                  objective={
                    <>
                      <ContextLine term="objective">
                        Ship {ticket.key} to {ticket.acceptance_criteria.length} acceptance
                        {ticket.acceptance_criteria.length === 1 ? " criterion" : " criteria"} at
                        difficulty L{ticket.difficulty}, producing execution evidence for{" "}
                        {ticket.target_skill_name}.
                      </ContextLine>
                      {ticket.milestone ? (
                        <ContextLine term="milestone">{ticket.milestone}</ContextLine>
                      ) : null}
                    </>
                  }
                />

                <div>
                  <p className="label">Ticket</p>
                  <p className="mt-2.5 text-[12px] leading-[1.7] text-muted">
                    {ticket.description}
                  </p>
                  <div className="mt-3 flex flex-wrap gap-1.5">
                    <Badge>{ticket.target_skill_name}</Badge>
                    <Badge>L{ticket.difficulty}/10</Badge>
                    <Badge>{ticket.estimated_minutes}m</Badge>
                    <Badge tone="accent">+{ticket.xp_reward} XP</Badge>
                  </div>
                </div>

                <RequirementList
                  requirements={ticket.requirements}
                  checks={checks}
                  graded={checks.length > 0}
                />

                <div>
                  <p className="label">Acceptance criteria</p>
                  <ul className="mt-2.5 space-y-2">
                    {ticket.acceptance_criteria.map((criterion) => (
                      <li key={criterion} className="flex gap-2.5 text-[12px] leading-relaxed">
                        <span className="mt-px font-mono text-[10px] text-accent/60">◆</span>
                        <span className="text-muted">{criterion}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {ticket.dependencies.length > 0 ? (
                  <div>
                    <p className="label">Dependencies</p>
                    <div className="mt-2.5 flex flex-wrap gap-1.5">
                      {ticket.dependencies.map((dependency) => (
                        <Badge key={dependency}>{dependency}</Badge>
                      ))}
                    </div>
                  </div>
                ) : null}

                <div className="border-t border-line pt-4">
                  <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                    {ticket.attempt_count} previous attempt
                    {ticket.attempt_count === 1 ? "" : "s"}
                  </p>
                  <p className="mt-2 text-[11px] leading-relaxed text-faint">
                    Deterministic checks run before any AI review, so the acceptance criteria above
                    are exactly what decides the verdict.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </aside>
          }
        />
      </div>
    </AppShell>
  );
}

/**
 * Header for the cumulative preview.
 *
 * The pane renders the whole project, not just this ticket, so it has to say so
 * — the point is that finishing a ticket visibly grows the product.
 */
function ProjectProgressStrip({
  meta,
  projectId,
}: {
  meta: PreviewMeta;
  projectId?: string;
}) {
  const percent =
    meta.total_tickets > 0 ? (meta.verified_tickets / meta.total_tickets) * 100 : 0;
  return (
    <div className="flex-none border-b border-line bg-surface px-4 py-3">
      <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
        <p className="label">Your app so far</p>
        <span className="font-mono text-[10px] tabular-nums text-accent">
          {meta.verified_tickets} of {meta.total_tickets} tickets verified
        </span>
        {projectId ? (
          <Link
            href={`/projects/${projectId}/preview`}
            className="ml-auto font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint transition-colors hover:text-accent"
          >
            full project ↗
          </Link>
        ) : null}
      </div>
      <GrowBar value={percent} tone="accent" className="mt-2.5" />
      <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
        {meta.files.map((file) => (
          <span key={file} className="chip font-mono text-[9.5px]">
            {file}
          </span>
        ))}
      </div>
      {meta.synthesized_host ? (
        <p className="mt-2.5 text-[11px] leading-relaxed text-faint">
          No page markup exists in this project yet, so the preview uses a plain scaffold
          {meta.mount_points.length > 0 ? (
            <>
              {" "}
              with the mount points your script needs (
              <span className="font-mono text-[10px] text-muted">
                {meta.mount_points.map((id) => `#${id}`).join(" ")}
              </span>
              )
            </>
          ) : null}
          . An HTML ticket will replace it with your own.
        </p>
      ) : null}
    </div>
  );
}

/** Verdict for a reviewed ticket submission, including unlocks. */
function TicketVerdict({
  result,
  projectId,
}: {
  result: TicketSubmitResult;
  projectId: string;
}) {
  const passed = result.passed;
  const [next, ...rest] = result.unlocked_tickets;
  return (
    <div
      className={cn(
        "overflow-hidden rounded border",
        passed ? "border-success/30 bg-success/[0.05]" : "border-danger/30 bg-danger/[0.05]",
      )}
    >
      <div className="flex flex-wrap items-center gap-3 px-4 py-2.5">
        <span
          className={cn(
            "font-mono text-[10px] uppercase tracking-[0.14em]",
            passed ? "text-success" : "text-danger",
          )}
        >
          {passed ? "ticket verified" : "rework required"}
        </span>
        {passed ? (
          <span className="font-mono text-[10px] text-accent">+{result.xp_awarded} XP</span>
        ) : null}
        {result.milestone_bonus > 0 ? (
          <span className="font-mono text-[10px] text-success">
            sprint bonus +{result.milestone_bonus}
          </span>
        ) : null}
        <span className="ml-auto font-mono text-[10px] tabular-nums text-faint">
          {result.skill.skill_name} {result.skill.confidence.toFixed(0)}%
        </span>
      </div>
      <div className="border-t border-line/60 px-4 py-3">
        <p className="text-[12px] leading-relaxed text-ink/90">{result.evaluation.feedback}</p>
        <GrowBar
          value={result.skill.confidence}
          tone={passed ? "success" : "warning"}
          className="mt-3"
        />
        {/* The review verdict updates a confidence score; make that chain, and
            its effect on the route, explicit rather than implied by a number. */}
        <EvidenceChain
          skillId={result.skill.skill_id}
          confidence={result.skill.confidence}
          className="mt-4"
        />
        {/* A verified ticket is a dead end without this: the next unlocked ticket
            becomes the primary action, with any others listed beside it. */}
        {passed && next ? (
          <div className="mt-4 border-t border-line/60 pt-4">
            <p className="label">Next ticket</p>
            <Link
              href={`/workspace/${next.ticket_id}`}
              className="group mt-2.5 flex items-center gap-3 rounded border border-accent/30 bg-accent/[0.06] px-3.5 py-3 transition-colors duration-200 hover:bg-accent/[0.12]"
            >
              <span className="font-mono text-[10px] text-accent">{next.key}</span>
              <span className="min-w-0 flex-1 truncate text-[12.5px] text-ink">{next.title}</span>
              <span className="flex-none font-mono text-[10px] uppercase tracking-[0.12em] text-accent transition-transform duration-200 group-hover:translate-x-0.5">
                open →
              </span>
            </Link>

            {rest.length > 0 ? (
              <div className="mt-2.5 flex flex-wrap items-center gap-2">
                <span className="label">also unlocked</span>
                {rest.map((item) => (
                  <Link
                    key={item.ticket_id}
                    href={`/workspace/${item.ticket_id}`}
                    className="chip border-accent/30 text-accent transition-colors hover:bg-accent/10"
                  >
                    {item.key}
                  </Link>
                ))}
              </div>
            ) : null}
          </div>
        ) : passed ? (
          // Nothing unlocked: the sprint boundary is the next meaningful step.
          <div className="mt-4 border-t border-line/60 pt-4">
            <p className="label">Next</p>
            <Link
              href={`/projects/${projectId}`}
              className="btn-primary btn-mono mt-2.5 w-full py-2"
            >
              Back to sprint board →
            </Link>
          </div>
        ) : null}
      </div>
    </div>
  );
}
