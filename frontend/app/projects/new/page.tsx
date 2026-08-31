"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useState } from "react";

import { AppShell } from "@/components/app-shell";
import { Alert, Badge, Loader, Panel, StatusPill } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { Project, Recommendation } from "@/lib/types";
import { cn, errorMessage } from "@/lib/utils";

const STACK = [
  "HTML",
  "CSS",
  "JavaScript",
  "React",
  "Node.js",
  "Database",
  "API",
  "REST",
  "Python",
  "Java",
  "C++",
];

const COMPLEXITY = ["beginner", "intermediate", "advanced"] as const;

const EXAMPLES = [
  {
    title: "Movie Ticket Booking System",
    idea: "A React app to browse movies, choose showtimes, select seats and confirm a booking, backed by a Node API and a database.",
    stack: ["HTML", "CSS", "JavaScript", "React", "Node.js", "Database"],
  },
  {
    title: "Recipe Manager",
    idea: "A web app to save recipes, tag them, search by ingredient and load details from an API.",
    stack: ["HTML", "CSS", "JavaScript", "React"],
  },
  {
    title: "Task Tracker API",
    idea: "A REST API for projects and tasks with validation, status codes and a relational schema.",
    stack: ["Node.js", "Database"],
  },
];

function isComplexity(value: string | null): value is (typeof COMPLEXITY)[number] {
  return COMPLEXITY.includes((value ?? "") as (typeof COMPLEXITY)[number]);
}

export default function NewProjectPage() {
  // useSearchParams opts the subtree out of prerendering, so it needs a boundary.
  return (
    <Suspense
      fallback={
        <AppShell>
          <Loader label="Loading project brief" />
        </AppShell>
      }
    >
      <NewProjectForm />
    </Suspense>
  );
}

function NewProjectForm() {
  const router = useRouter();
  const queryClient = useQueryClient();
  // Course capstones deep-link here with the brief already filled in, so the
  // learner confirms a project rather than inventing one from scratch.
  const params = useSearchParams();
  const preset = {
    title: params.get("title"),
    idea: params.get("idea"),
    stack: params.get("stack"),
    complexity: params.get("complexity"),
    outcome: params.get("outcome"),
  };
  const presetStack = preset.stack
    ? preset.stack.split(",").map((entry) => entry.trim()).filter(Boolean)
    : null;

  const [title, setTitle] = useState(preset.title ?? EXAMPLES[0].title);
  const [idea, setIdea] = useState(preset.idea ?? EXAMPLES[0].idea);
  const [stack, setStack] = useState<string[]>(presetStack ?? EXAMPLES[0].stack);
  const [known, setKnown] = useState<string[]>(["HTML", "CSS", "JavaScript"]);
  const [experience, setExperience] = useState<(typeof COMPLEXITY)[number]>("intermediate");
  const [complexity, setComplexity] = useState<(typeof COMPLEXITY)[number]>(
    isComplexity(preset.complexity) ? preset.complexity : "intermediate",
  );
  const [outcome, setOutcome] = useState(
    preset.outcome ?? "A working end-to-end booking flow I can demo.",
  );
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [plan, setPlan] = useState<{ project: Project; recommendation: Recommendation } | null>(
    null,
  );

  function toggle(list: string[], setList: (value: string[]) => void, item: string) {
    setList(list.includes(item) ? list.filter((entry) => entry !== item) : [...list, item]);
  }

  async function create() {
    if (stack.length === 0) {
      setError("Select at least one technology for the stack.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const response = await api<{
        project: Project;
        plan: { rationale: string };
        recommendation: Recommendation;
      }>("/projects", {
        method: "POST",
        body: {
          title,
          idea,
          tech_stack: stack,
          known_technologies: known,
          experience_level: experience,
          complexity,
          desired_outcome: outcome,
        },
      });
      setPlan({ project: response.project, recommendation: response.recommendation });
      await queryClient.invalidateQueries();
    } catch (createError) {
      setError(errorMessage(createError));
    } finally {
      setBusy(false);
    }
  }

  /* ------------------------------------------------------------- plan view */
  if (plan) {
    const { project, recommendation } = plan;
    const locked =
      project.sprints?.flatMap((sprint) =>
        sprint.tickets.filter(
          (ticket) =>
            ticket.status === "locked" && ticket.lock_reason?.includes("Prerequisite"),
        ),
      ) ?? [];

    return (
      <AppShell>
        <div className="mx-auto max-w-[900px]">
          <div className="flex items-center gap-3">
            <span className="label-accent">plan generated</span>
            <span className="h-px flex-1 bg-line" />
            <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
              {project.sprint_count} sprints · {project.ticket_count} tickets
            </span>
          </div>

          <h1 className="display mt-7 text-display-md text-balance text-ink">{project.title}</h1>
          <p className="mt-5 max-w-[64ch] text-[13px] leading-[1.75] text-muted">
            {project.plan_rationale}
          </p>

          {/* Why this next — the signature explanation, repeated here */}
          <div className="relative mt-9 overflow-hidden rounded-lg border border-accent/25 bg-surface p-6">
            <span className="absolute inset-y-0 left-0 w-[2px] bg-accent" aria-hidden />
            <p className="label-accent">Why this next</p>
            <p className="display mt-3 text-[19px] tracking-tight text-ink">
              {recommendation.title}
            </p>
            <p className="mt-3 max-w-[64ch] border-l border-line pl-4 text-[12.5px] leading-relaxed text-muted">
              {recommendation.reason}
            </p>
          </div>

          {/* Backlog */}
          <div className="mt-10 space-y-10">
            {project.sprints?.map((sprint, index) => (
              <section key={sprint.id}>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <span className="font-mono text-[10px] text-accent">
                    S{String(index + 1).padStart(2, "0")}
                  </span>
                  <span className="font-mono text-[9.5px] uppercase tracking-[0.12em] text-faint">
                    {sprint.milestone}
                  </span>
                  <span className="text-[13px] font-medium text-ink">{sprint.name}</span>
                  <span className="h-px flex-1 bg-line" />
                </div>
                <ul className="divide-y divide-line/60 border-y border-line">
                  {sprint.tickets.map((ticket) => (
                    <li key={ticket.id} className="flex items-center gap-3 py-2.5">
                      <span className="font-mono text-[10px] text-accent">{ticket.key}</span>
                      <span className="min-w-0 flex-1 truncate text-[12px] text-muted">
                        {ticket.title}
                      </span>
                      <StatusPill status={ticket.status} />
                    </li>
                  ))}
                </ul>
              </section>
            ))}
          </div>

          {locked.length > 0 ? (
            <div className="mt-8">
              <Alert tone="warning" title="Some tickets start locked">
                <p>The knowledge graph found prerequisites your twin has evidence against:</p>
                <ul className="mt-2.5 space-y-1.5">
                  {locked.slice(0, 3).map((ticket) => (
                    <li key={ticket.id} className="text-[11.5px]">
                      <span className="font-mono text-[10px] text-accent">{ticket.key}</span>{" "}
                      {ticket.lock_reason}
                    </li>
                  ))}
                </ul>
              </Alert>
            </div>
          ) : null}

          <div className="mt-10 flex flex-wrap gap-2 border-t border-line pt-6">
            <button
              onClick={() => router.push(`/projects/${project.id}`)}
              className="btn-primary btn-mono px-5 py-2.5"
            >
              Open the sprint board →
            </button>
            <button
              onClick={() => router.push("/dashboard")}
              className="btn-ghost btn-mono px-5 py-2.5"
            >
              Back to dashboard
            </button>
          </div>
        </div>
      </AppShell>
    );
  }

  /* ------------------------------------------------------------- form view */
  return (
    <AppShell>
      <div className="mx-auto max-w-[900px]">
        <p className="label">Project execution mode</p>
        <h1 className="display mt-3 text-display-md text-balance text-ink">
          Describe what you want to build
        </h1>
        <p className="mt-5 max-w-[62ch] text-[13px] leading-[1.75] text-muted">
          SprintForge acts as your AI project manager. It will not generate the finished code — it
          decomposes the idea into milestones, sprints and tickets with acceptance criteria, and
          checks your verified skills before unlocking each one.
        </p>

        <Section index="01" title="Start from an example" hint="Or write your own below.">
          <div className="grid gap-px bg-line sm:grid-cols-3">
            {EXAMPLES.map((example) => (
              <button
                key={example.title}
                onClick={() => {
                  setTitle(example.title);
                  setIdea(example.idea);
                  setStack(example.stack);
                }}
                aria-pressed={title === example.title}
                className={cn(
                  "bg-surface px-4 py-3.5 text-left transition-colors duration-200",
                  title === example.title
                    ? "bg-accent/[0.07] text-ink"
                    : "text-muted hover:bg-elevated",
                )}
              >
                <span className="block text-[12.5px]">{example.title}</span>
                <span className="mt-1 block font-mono text-[9.5px] uppercase tracking-[0.08em] text-faint">
                  {example.stack.length} technologies
                </span>
              </button>
            ))}
          </div>
        </Section>

        <Section index="02" title="The brief" hint="Plain language is fine — be specific.">
          <div className="space-y-5">
            <div>
              <label htmlFor="title" className="label mb-2 block">
                project title
              </label>
              <input
                id="title"
                className="input"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </div>
            <div>
              <label htmlFor="idea" className="label mb-2 block">
                project idea
              </label>
              <textarea
                id="idea"
                className="input min-h-[96px] leading-relaxed"
                value={idea}
                onChange={(event) => setIdea(event.target.value)}
                placeholder="I want to build a movie ticket booking system…"
              />
            </div>
            <div>
              <label htmlFor="outcome" className="label mb-2 block">
                desired outcome
              </label>
              <input
                id="outcome"
                className="input"
                value={outcome}
                onChange={(event) => setOutcome(event.target.value)}
              />
            </div>
          </div>
        </Section>

        <Section index="03" title="Tech stack" hint="Drives which skills the backlog covers.">
          <div className="flex flex-wrap gap-1.5">
            {STACK.map((tech) => (
              <TagToggle
                key={tech}
                label={tech}
                active={stack.includes(tech)}
                onClick={() => toggle(stack, setStack, tech)}
              />
            ))}
          </div>
        </Section>

        <Section
          index="04"
          title="Technologies you already know"
          hint="Recorded as a claim — SprintForge still requires evidence."
        >
          <div className="flex flex-wrap gap-1.5">
            {STACK.map((tech) => (
              <TagToggle
                key={tech}
                label={tech}
                active={known.includes(tech)}
                tone="success"
                onClick={() => toggle(known, setKnown, tech)}
              />
            ))}
          </div>
        </Section>

        <Section index="05" title="Calibration" hint="Sets ticket difficulty and sprint size.">
          <div className="grid gap-6 sm:grid-cols-2">
            <div>
              <p className="label mb-2">your experience</p>
              <Segmented
                options={COMPLEXITY}
                value={experience}
                onChange={(value) => setExperience(value)}
              />
            </div>
            <div>
              <p className="label mb-2">project complexity</p>
              <Segmented
                options={COMPLEXITY}
                value={complexity}
                onChange={(value) => setComplexity(value)}
              />
            </div>
          </div>
        </Section>

        {error ? (
          <div className="mt-6">
            <Alert tone="danger">{error}</Alert>
          </div>
        ) : null}

        <div className="mt-10 flex flex-wrap items-center justify-between gap-4 border-t border-line pt-6">
          <p className="max-w-[42ch] text-[11.5px] leading-relaxed text-faint">
            Planning runs against the knowledge graph, so tickets you are not ready for will arrive
            locked with the reason attached.
          </p>
          <button
            onClick={() => void create()}
            className="btn-primary btn-mono px-5 py-3"
            disabled={busy}
          >
            {busy ? <Loader label="Planning sprints" /> : <>Generate the sprint plan →</>}
          </button>
        </div>

        {busy ? (
          <Panel className="mt-6">
            <Loader label="Decomposing idea into milestones" />
            <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
              The planner is mapping your stack onto the knowledge graph, ordering tickets by
              prerequisite depth and gating anything your twin has not verified.
            </p>
          </Panel>
        ) : null}
      </div>
    </AppShell>
  );
}

function Section({
  index,
  title,
  hint,
  children,
}: {
  index: string;
  title: string;
  hint: string;
  children: React.ReactNode;
}) {
  return (
    <section className="mt-12 border-t border-line pt-7">
      <div className="mb-5 flex items-baseline gap-4">
        <span className="font-mono text-[10px] text-accent">{index}</span>
        <div>
          <h2 className="text-[13px] font-medium text-ink">{title}</h2>
          <p className="mt-1 text-[11.5px] text-muted">{hint}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function TagToggle({
  label,
  active,
  onClick,
  tone = "accent",
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  tone?: "accent" | "success";
}) {
  return (
    <button
      onClick={onClick}
      aria-pressed={active}
      className={cn(
        "flex items-center gap-2 rounded border px-2.5 py-1.5 text-[11.5px] transition-colors duration-200",
        active
          ? tone === "success"
            ? "border-success/45 bg-success/[0.08] text-ink"
            : "border-accent/50 bg-accent/[0.08] text-ink"
          : "border-line text-muted hover:border-line-strong hover:bg-elevated",
      )}
    >
      <span
        className={cn(
          "font-mono text-[9px]",
          active ? (tone === "success" ? "text-success" : "text-accent") : "text-faint",
        )}
      >
        {active ? "✓" : "+"}
      </span>
      {label}
    </button>
  );
}

function Segmented<T extends string>({
  options,
  value,
  onChange,
}: {
  options: readonly T[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="flex gap-px overflow-hidden rounded border border-line bg-line">
      {options.map((option) => (
        <button
          key={option}
          onClick={() => onChange(option)}
          aria-pressed={value === option}
          className={cn("seg", value === option ? "seg-on" : "seg-off")}
        >
          {option}
        </button>
      ))}
    </div>
  );
}
