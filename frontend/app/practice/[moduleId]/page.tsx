"use client";

import { useQuery, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { GrowBar } from "@/components/motion";
import {
  Alert,
  Badge,
  PanelSkeleton,
} from "@/components/ui/primitives";
import {
  CodeEditor,
  FileTabs,
  PreviewFrame,
} from "@/components/workspace/code-editor";
import { CommunityPanel } from "@/components/workspace/community-panel";
import { FailureAnalysisPanel } from "@/components/workspace/failure-analysis";
import { MentorPanel } from "@/components/workspace/mentor-panel";
import { EvidenceChain, PathContextPanel } from "@/components/workspace/path-context";
import { ProblemPanel } from "@/components/workspace/problem-panel";
import { RequirementList } from "@/components/workspace/requirement-progress";
import { ResultsDock, type ExecutionResult } from "@/components/workspace/results-dock";
import { SplitPane } from "@/components/workspace/split-pane";
import { TestConsole, type ConsoleTab } from "@/components/workspace/test-console";
import { api } from "@/lib/api";
import type { CheckResult, PracticeModule, SubmitResult } from "@/lib/types";
import {
  MONACO_LANGUAGE,
  cn,
  difficultyLabel,
  errorMessage,
  languageForFile,
} from "@/lib/utils";

type RunResult = {
  kind: "web" | "challenge";
  static_results?: CheckResult[];
  test_results?: CheckResult[];
  preview?: string | null;
  provider?: string;
  supported?: boolean;
  compile_error?: string | null;
  results?: ExecutionResult[];
  passed_count?: number;
  total_count?: number;
  custom_run?: boolean;
};

/** Right-pane tabs of the web workspace. The brief is not one of them: it owns
 *  the left rail, and duplicating it put the same task on screen twice. */
type WebTab = "preview" | "mentor" | "community";

const LANGUAGE_LABEL: Record<string, string> = {
  python: "Python",
  javascript: "JavaScript",
  typescript: "TypeScript",
  java: "Java",
  c: "C",
  cpp: "C++",
};

export default function PracticeWorkspacePage() {
  const params = useParams<{ moduleId: string }>();
  const moduleId = params.moduleId;
  const queryClient = useQueryClient();

  const moduleQuery = useQuery({
    queryKey: ["practice-module", moduleId],
    queryFn: () => api<PracticeModule>(`/practice/modules/${moduleId}`),
  });

  const [files, setFiles] = useState<Record<string, string>>({});
  const [activeFile, setActiveFile] = useState<string>("");
  /** Mirrors `activeFile` for Monaco's change handler; see selectFile below. */
  const activeFileRef = useRef("");
  /** Mirrors `files` so the mentor can read the buffer without re-rendering. */
  const filesRef = useRef<Record<string, string>>({});
  const [runResult, setRunResult] = useState<RunResult | null>(null);
  const [submitResult, setSubmitResult] = useState<SubmitResult | null>(null);
  const [stdin, setStdin] = useState("");
  const [busy, setBusy] = useState<"run" | "submit" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [webTab, setWebTab] = useState<WebTab>("preview");
  const [consoleTab, setConsoleTab] = useState<ConsoleTab>("testcase");
  const [showBrief, setShowBrief] = useState(false);
  // Bumped whenever files are replaced wholesale (initial load, Reset) to force the
  // editor to remount and pick up the new buffer contents.
  const [revision, setRevision] = useState(0);
  const startedAt = useRef(Date.now());

  const practiceModule = moduleQuery.data;

  useEffect(() => {
    if (!practiceModule) return;
    setFiles(practiceModule.files);
    filesRef.current = practiceModule.files;
    const first = practiceModule.editable_files[0] ?? Object.keys(practiceModule.files)[0] ?? "";
    setActiveFile(first);
    activeFileRef.current = first;
    setWebTab(practiceModule.entry_file ? "preview" : "mentor");
    setConsoleTab("testcase");
    setStdin(practiceModule.sample_tests[0]?.stdin ?? "");
    setRevision((r) => r + 1);
    startedAt.current = Date.now();
  }, [practiceModule]);

  const editorLanguage = useMemo(() => {
    if (!practiceModule) return "plaintext";
    if (practiceModule.kind === "challenge") {
      return MONACO_LANGUAGE[practiceModule.language ?? "javascript"] ?? "plaintext";
    }
    return languageForFile(activeFile);
  }, [practiceModule, activeFile]);

  const getCode = useCallback(() => filesRef.current[activeFileRef.current] ?? "", []);

  async function run(withStdin = false) {
    if (!practiceModule) return;
    setBusy("run");
    setError(null);
    try {
      const result = await api<RunResult>(`/practice/modules/${practiceModule.id}/run`, {
        method: "POST",
        body: { files, stdin: withStdin ? stdin : null },
      });
      setRunResult(result);
      setSubmitResult(null);
      if (result.kind === "web" && practiceModule.entry_file) setWebTab("preview");
      setConsoleTab("result");
    } catch (runError) {
      setError(errorMessage(runError));
      setConsoleTab("result");
    } finally {
      setBusy(null);
    }
  }

  async function submit() {
    if (!practiceModule) return;
    setBusy("submit");
    setError(null);
    try {
      const result = await api<SubmitResult>(`/practice/modules/${practiceModule.id}/submit`, {
        method: "POST",
        body: { files, duration_seconds: (Date.now() - startedAt.current) / 1000 },
      });
      setSubmitResult(result);
      setRunResult(null);
      setConsoleTab("result");
      await queryClient.invalidateQueries();
    } catch (submitError) {
      setError(errorMessage(submitError));
      setConsoleTab("result");
    } finally {
      setBusy(null);
    }
  }

  function selectFile(file: string) {
    activeFileRef.current = file;
    setActiveFile(file);
  }

  function updateFile(file: string, value: string) {
    // Only the layer being practised is writable; provided files must stay pristine
    // so a passing submission cannot come from editing the scaffolding.
    if (!practiceModule?.editable_files.includes(file)) return;
    setFiles((current) => {
      if (current[file] === value) return current;
      const next = { ...current, [file]: value };
      filesRef.current = next;
      return next;
    });
  }

  function reset() {
    if (!practiceModule) return;
    setFiles(practiceModule.files);
    filesRef.current = practiceModule.files;
    setRevision((r) => r + 1);
    setRunResult(null);
    setSubmitResult(null);
    setError(null);
  }

  if (moduleQuery.isLoading) {
    return (
      <AppShell wide>
        <div className="py-10">
          <div className="flex items-center gap-3 text-muted">
            <div className="h-6 w-6 animate-spin rounded-full border-2 border-accent border-t-transparent" />
            <span className="label">Loading practice module...</span>
          </div>
        </div>
      </AppShell>
    );
  }

  if (moduleQuery.error || !practiceModule) {
    return (
      <AppShell wide>
        <div className="py-10">
          <Alert tone="danger" title="Module unavailable">
            {errorMessage(moduleQuery.error) || "Practice practiceModule not found."}
          </Alert>
          <Link href="/practice" className="btn-ghost btn-mono mt-5 px-4 py-2">
            ← Back to practice
          </Link>
        </div>
      </AppShell>
    );
  }

  const isWeb = practiceModule.kind === "web";
  const editable = practiceModule.editable_files;
  const readOnly = !editable.includes(activeFile);
  const checkItems: CheckResult[] = submitResult
    ? [...submitResult.static_results, ...submitResult.test_results]
    : [...(runResult?.static_results ?? []), ...(runResult?.test_results ?? [])];
  const failingChecks = checkItems.filter((item) => !item.passed).map((item) => item.label);

  const samplesAllPassed =
    !submitResult &&
    runResult?.custom_run === false &&
    runResult.passed_count === runResult.total_count &&
    practiceModule.hidden_test_count > 0;
  // Kept explicit so an empty feedback block never counts as content and
  // suppresses the console's "nothing has run yet" state.
  const hasFeedback = Boolean(error || submitResult || samplesAllPassed);

  /** Verdict, transport errors and post-mortem. Shared by both layouts. */
  const feedback = (
    <>
      {error ? <Alert tone="danger">{error}</Alert> : null}

      {submitResult ? <VerdictBanner result={submitResult} /> : null}

      {/* A clean Run reads as "done" unless we say otherwise, and the hidden
          cases are exactly where a nearly-right solution dies. */}
      {samplesAllPassed ? (
        <Alert tone="warning">
          Samples pass. {practiceModule.hidden_test_count} hidden{" "}
          {practiceModule.hidden_test_count === 1 ? "case" : "cases"} still decide the submission — check
          the edge conditions in the constraints before you submit.
        </Alert>
      ) : null}

      {submitResult?.failure_analysis ? (
        <FailureAnalysisPanel
          analysis={submitResult.failure_analysis}
          confidence={submitResult.skill.confidence}
          currentModuleId={practiceModule.id}
        />
      ) : null}
    </>
  );

  /* -------------------------------------------------------------- editor pane */

  const editorPane = (
    <div className="flex h-[440px] min-h-0 flex-col bg-canvas lg:h-full">
      <div className="flex flex-none items-center gap-3 border-b border-line bg-surface px-3 py-1.5">
        <LanguageSelect language={practiceModule.language} />
        {readOnly ? <Badge tone="warning">read only</Badge> : null}
        <span className="ml-auto truncate font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
          {activeFile}
        </span>
      </div>

      {Object.keys(files).length > 1 ? (
        <FileTabs
          files={Object.keys(files)}
          active={activeFile}
          editable={editable}
          onSelect={selectFile}
        />
      ) : null}

      <div className="min-h-0 flex-1">
        <CodeEditor
          path={`${practiceModule.id}/r${revision}/${activeFile}`}
          value={files[activeFile] ?? ""}
          language={editorLanguage}
          readOnly={readOnly}
          onChange={(value) => updateFile(activeFileRef.current, value)}
          onRun={() => {
            if (!readOnly) void run();
          }}
          onSubmit={() => {
            if (!readOnly) void submit();
          }}
        />
      </div>
    </div>
  );

  return (
    <AppShell wide bleed>
      {/* ---------------------------------------------------- workspace bar */}
      <div className="sticky top-12 z-30 border-b border-line bg-canvas/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1800px] flex-wrap items-center gap-x-5 gap-y-2 px-4 py-3 sm:px-6">
          <Link
            href="/practice"
            className="font-mono text-[10px] uppercase tracking-[0.12em] text-faint transition-colors hover:text-ink"
          >
            ← Practice
          </Link>
          <span className="h-3 w-px bg-line" />
          <h1 className="min-w-0 truncate text-[13px] font-medium text-ink">{practiceModule.title}</h1>

          <div className="flex flex-wrap items-center gap-1.5">
            <Badge tone="accent">{practiceModule.technology}</Badge>
            <Badge>
              {difficultyLabel(practiceModule.difficulty)} L{practiceModule.difficulty}
            </Badge>
            <Badge>{practiceModule.skill_name}</Badge>
            <Badge tone="success">+{practiceModule.xp_reward} XP</Badge>
            {practiceModule.is_remediation ? <Badge tone="warning">remediation</Badge> : null}
          </div>

          <div className="ml-auto flex flex-wrap items-center gap-2">
            {isWeb ? (
              <button
                onClick={() => setShowBrief((value) => !value)}
                className="btn-ghost btn-mono px-3 py-1.5 xl:hidden"
              >
                {showBrief ? "Hide brief" : "Brief"}
              </button>
            ) : (
              <TestTally
                samples={practiceModule.sample_tests.length}
                hidden={practiceModule.hidden_test_count}
                passed={runResult?.passed_count}
                total={runResult?.total_count}
                customRun={runResult?.custom_run}
                graded={Boolean(submitResult)}
                gradedPassed={submitResult?.passed}
              />
            )}
            <button
              onClick={reset}
              title="Discard your edits and restore the starter file"
              className="btn-quiet btn-mono px-2 py-1.5"
              disabled={busy !== null}
            >
              Reset
            </button>

            <span className="h-4 w-px bg-line" aria-hidden />

            {/* Run and Submit differ in what they grade, so each says so on its
                face. Before this, four adjacent mono buttons looked like four
                flavours of the same thing. */}
            <button
              onClick={() => void run(false)}
              title={
                isWeb
                  ? "Renders your code and runs the visible checks. Nothing is graded."
                  : `Executes the ${practiceModule.sample_tests.length} sample case${
                      practiceModule.sample_tests.length === 1 ? "" : "s"
                    } only. Nothing is graded.`
              }
              className="btn-subtle btn-mono gap-1.5 px-3.5 py-1.5"
              disabled={busy !== null}
            >
              {busy === "run" ? "Running…" : "Run"}
              <span className="normal-case tracking-normal text-faint">
                {isWeb
                  ? "preview"
                  : `${practiceModule.sample_tests.length} sample${
                      practiceModule.sample_tests.length === 1 ? "" : "s"
                    }`}
              </span>
            </button>
            <button
              onClick={() => void submit()}
              title={
                practiceModule.hidden_test_count > 0
                  ? `Grades every case, including ${practiceModule.hidden_test_count} hidden one${
                      practiceModule.hidden_test_count === 1 ? "" : "s"
                    } you cannot see, and updates your twin.`
                  : "Grades the attempt and updates your twin."
              }
              className="btn-primary btn-mono gap-1.5 px-3.5 py-1.5"
              disabled={busy !== null}
            >
              {busy === "submit" ? "Verifying…" : "Submit"}
              <span className="normal-case tracking-normal text-accent-ink/60">
                {practiceModule.hidden_test_count > 0
                  ? `+${practiceModule.hidden_test_count} hidden`
                  : "graded"}
              </span>
            </button>
          </div>
        </div>
      </div>

      {isWeb ? (
        /* ------------------------------------------- three-pane web workspace */
        <div className="mx-auto grid max-w-[1800px] gap-px bg-line xl:h-[calc(100vh-6.5rem)] xl:grid-cols-[300px_minmax(0,1fr)_360px]">
          {/* LEFT — brief. The only place the task is stated. */}
          <aside
            className={cn(
              "overflow-y-auto bg-surface p-5 xl:block",
              showBrief ? "block" : "hidden",
            )}
          >
            <Brief module={practiceModule} checks={checkItems} />
          </aside>

          {/* CENTER — editor over output dock */}
          <section className="flex min-h-0 min-w-0 flex-col bg-canvas">
            <FileTabs
              files={Object.keys(files)}
              active={activeFile}
              editable={editable}
              onSelect={selectFile}
            />
            <div className="min-h-[300px] flex-1 xl:min-h-0">
              <CodeEditor
                path={`${practiceModule.id}/r${revision}/${activeFile}`}
                value={files[activeFile] ?? ""}
                language={editorLanguage}
                readOnly={readOnly}
                onChange={(value) => updateFile(activeFileRef.current, value)}
                onRun={() => {
                  if (!readOnly) void run();
                }}
                onSubmit={() => {
                  if (!readOnly) void submit();
                }}
              />
            </div>

            {/* Output dock, always docked to the editor bottom. Below xl the panes
                stack, so it sizes to its content instead of reserving a share of
                an unconstrained column. */}
            <div className="min-h-[120px] flex-none border-t border-line xl:h-[38%] xl:min-h-[200px]">
              <ResultsDock
                checks={checkItems}
                execution={runResult?.results}
                compileError={runResult?.compile_error}
                provider={runResult?.provider}
                passedCount={runResult?.passed_count}
                totalCount={runResult?.total_count}
                customRun={runResult?.custom_run}
                emptyHint="run for deterministic feedback · submit to grade the attempt and update your twin"
              >
                {hasFeedback || submitResult?.failure_analysis ? (
                  <div className="mb-4 space-y-4">{feedback}</div>
                ) : null}
              </ResultsDock>
            </div>
          </section>

          {/* RIGHT — preview, mentor, discussion */}
          <aside className="flex min-h-0 flex-col bg-surface">
            <div className="flex flex-none border-b border-line">
              {(["preview", "mentor", "community"] as const)
                .filter((item) => item !== "preview" || practiceModule.entry_file)
                .map((item) => (
                  <button
                    key={item}
                    onClick={() => setWebTab(item)}
                    aria-pressed={webTab === item}
                    className={cn(
                      "relative min-w-0 flex-1 truncate px-2 py-2.5 font-mono text-[10px] uppercase tracking-[0.1em] transition-colors",
                      webTab === item ? "text-ink" : "text-faint hover:text-muted",
                    )}
                  >
                    {item === "mentor" ? "AI Mentor" : item === "community" ? "Discuss" : item}
                    <span
                      className={cn(
                        "absolute inset-x-0 -bottom-px h-px bg-accent transition-opacity",
                        webTab === item ? "opacity-100" : "opacity-0",
                      )}
                    />
                  </button>
                ))}
            </div>

            <div className="min-h-[280px] flex-1 overflow-y-auto xl:min-h-0">
              {webTab === "preview" && practiceModule.entry_file ? (
                <div className="h-full min-h-[280px]">
                  <PreviewFrame html={runResult?.preview ?? null} />
                </div>
              ) : webTab === "community" ? (
                <div className="p-4">
                  <CommunityPanel moduleId={practiceModule.id} />
                </div>
              ) : (
                <div className="h-full p-4">
                  <MentorPanel
                    skillId={practiceModule.skill_id}
                    skillName={practiceModule.skill_name}
                    moduleId={practiceModule.id}
                    getCode={getCode}
                    failingChecks={failingChecks}
                  />
                </div>
              )}
            </div>
          </aside>
        </div>
      ) : (
        /* ------------------------------- two-pane judge workspace (algorithms) */
        <SplitPane
          orientation="horizontal"
          storageKey="practice-problem"
          initial={42}
          min={24}
          max={68}
          className="mx-auto max-w-[1800px] bg-line lg:h-[calc(100vh-6.5rem)]"
          first={
            <ProblemPanel
              module={practiceModule}
              checks={checkItems}
              failingChecks={failingChecks}
              getCode={getCode}
            />
          }
          second={
            <SplitPane
              orientation="vertical"
              storageKey="practice-console"
              initial={62}
              min={30}
              max={85}
              className="h-full bg-line"
              first={editorPane}
              second={
                <div className="h-[320px] min-h-0 lg:h-full">
                  <TestConsole
                    module={practiceModule}
                    tab={consoleTab}
                    onTabChange={setConsoleTab}
                    stdin={stdin}
                    onStdinChange={setStdin}
                    onRunCase={() => void run(true)}
                    busy={busy !== null}
                    execution={runResult?.results}
                    compileError={runResult?.compile_error}
                    provider={runResult?.provider}
                    passedCount={runResult?.passed_count}
                    totalCount={runResult?.total_count}
                    customRun={runResult?.custom_run}
                    checks={checkItems}
                    banner={hasFeedback ? feedback : null}
                  />
                </div>
              }
            />
          }
        />
      )}
    </AppShell>
  );
}

/**
 * First paint of the workspace.
 *
 * Draws the panes it is about to fill rather than a spinner in an empty page,
 * so the layout does not jump and the wait states what is being fetched.
 */
function WorkspaceSkeleton() {
  return (
    <AppShell wide bleed>
      <div className="mx-auto max-w-[1800px]" aria-busy>
        <div className="flex items-center gap-3 border-b border-line bg-canvas px-4 py-3 sm:px-6">
          <div className="skeleton h-2.5 w-16 rounded" />
          <div className="skeleton h-2.5 w-56 rounded" />
          <div className="skeleton ml-auto h-6 w-44 rounded" />
        </div>
        <div className="grid gap-px bg-line lg:h-[calc(100vh-6.5rem)] lg:grid-cols-[42%_minmax(0,1fr)]">
          <div className="space-y-4 bg-surface p-5">
            <p className="font-mono text-[10px] uppercase tracking-[0.16em] text-accent">
              loading problem<span className="animate-caret">_</span>
            </p>
            <PanelSkeleton lines={8} />
          </div>
          <div className="flex min-h-[420px] flex-col">
            <div className="grid-bg-fine flex-1 bg-canvas" />
            <div className="h-[38%] min-h-[140px] space-y-3 border-t border-line bg-canvas p-5">
              <div className="skeleton h-2.5 w-28 rounded" />
              <PanelSkeleton lines={3} />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );
}

/**
 * Standing answer to "how many tests are there, and how am I doing?".
 *
 * Visible before anything runs, because the split between sample and hidden
 * cases changes how you write the solution — a bare `0/2` after a run did not
 * say that, and was easy to miss entirely.
 */
function TestTally({
  samples,
  hidden,
  passed,
  total,
  customRun,
  graded,
  gradedPassed,
}: {
  samples: number;
  hidden: number;
  passed?: number;
  total?: number;
  customRun?: boolean;
  graded: boolean;
  gradedPassed?: boolean;
}) {
  const ran = !customRun && typeof passed === "number" && typeof total === "number";
  const allPassed = ran && passed === total;

  return (
    <span
      className="inline-flex items-center gap-2 rounded border border-line bg-elevated px-2.5 py-1"
      title={`${samples} sample case${samples === 1 ? "" : "s"} you can see, ${hidden} hidden case${
        hidden === 1 ? "" : "s"
      } graded on submit`}
    >
      {graded ? (
        <span
          className={cn(
            "font-mono text-[10px] uppercase tracking-[0.12em]",
            gradedPassed ? "text-success" : "text-danger",
          )}
        >
          {gradedPassed ? "accepted" : "not accepted"}
        </span>
      ) : (
        <>
          <span
            className={cn(
              "font-mono text-[11px] tabular-nums",
              !ran ? "text-faint" : allPassed ? "text-success" : "text-danger",
            )}
          >
            {ran ? `${passed}/${total}` : samples + hidden}
          </span>
          <span className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
            {ran ? "samples pass" : "tests"}
          </span>
        </>
      )}
      <span className="hidden font-mono text-[9.5px] text-faint sm:inline">
        {samples} sample{samples === 1 ? "" : "s"} · {hidden} hidden
      </span>
    </span>
  );
}

/** Language of the challenge. Authored per module, so the alternatives are shown
 *  but not selectable — a silent switch would produce code the judge cannot run. */
function LanguageSelect({ language }: { language: string | null }) {
  const current = language ?? "javascript";
  const label = LANGUAGE_LABEL[current] ?? current;
  return (
    <label className="flex items-center gap-2">
      <span className="sr-only">Language</span>
      <select
        value={current}
        onChange={() => undefined}
        title={`This challenge is authored for ${label}`}
        className="rounded border border-line bg-elevated px-2 py-1 font-mono text-[10.5px] uppercase tracking-[0.1em] text-ink outline-none transition-colors hover:border-line-strong focus:border-accent/60"
      >
        {Object.keys(MONACO_LANGUAGE).map((key) => (
          <option key={key} value={key} disabled={key !== current}>
            {LANGUAGE_LABEL[key] ?? key}
          </option>
        ))}
      </select>
    </label>
  );
}

/** Task, requirements and sample cases for the web workspace. */
function Brief({
  module,
  checks,
}: {
  module: PracticeModule;
  checks: CheckResult[];
}) {
  return (
    <div className="space-y-6">
      {/* Route context first: the brief says what to build, this says why it is
          in front of you. Renders nothing when the skill is off the route. */}
      <PathContextPanel skillId={module.skill_id} />

      <div>
        <p className="label">Task</p>
        <p className="mt-2.5 whitespace-pre-wrap text-[12px] leading-[1.7] text-muted">
          {module.problem_statement ?? module.summary}
        </p>
      </div>

      {module.requirements.length > 0 ? (
        <div>
          <RequirementList
            requirements={module.requirements}
            checks={checks}
            graded={checks.length > 0}
          />
        </div>
      ) : null}

      {module.constraints.length > 0 ? (
        <div>
          <p className="label">Constraints</p>
          <ul className="mt-2.5 space-y-1">
            {module.constraints.map((constraint) => (
              <li key={constraint} className="font-mono text-[10.5px] leading-relaxed text-faint">
                {constraint}
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <div className="border-t border-line pt-4">
        <p className="text-[11px] leading-relaxed text-faint">
          Files marked with an accent dot are yours to write. The rest are provided, so the layer
          you are practising is the only thing that can fail.
        </p>
      </div>
    </div>
  );
}

/** Pass/fail verdict for a graded submission. */
function VerdictBanner({ result }: { result: SubmitResult }) {
  const passed = result.passed;
  return (
    <div
      className={cn(
        "overflow-hidden rounded border",
        passed ? "border-success/30 bg-success/[0.05]" : "border-danger/30 bg-danger/[0.05]",
      )}
    >
      <div className="flex items-center gap-3 px-4 py-2.5">
        <span
          className={cn(
            "font-mono text-[10px] uppercase tracking-[0.14em]",
            passed ? "text-success" : "text-danger",
          )}
        >
          {passed ? "verified" : "not accepted"}
        </span>
        {passed ? (
          <span className="font-mono text-[10px] text-accent">+{result.xp_awarded} XP</span>
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

        {/* A verdict is a confidence update, not a completed lesson — spell out
            the chain from this attempt to the learner's route. */}
        <EvidenceChain
          skillId={result.skill.skill_id}
          confidence={result.skill.confidence}
          className="mt-4"
        />

        {/* A passed module should not dead-end. The engine already knows what is
            next, so route the learner at it rather than back to a catalogue. */}
        {passed ? (
          <div className="mt-4 border-t border-line/60 pt-4">
            <p className="label">Next</p>
            <div className="mt-2.5 flex flex-col gap-2 sm:flex-row">
              <Link href="/dashboard" className="btn-primary btn-mono flex-1 py-2">
                What the engine picked next →
              </Link>
              <Link href="/practice" className="btn-ghost btn-mono flex-1 py-2">
                Browse practice
              </Link>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
