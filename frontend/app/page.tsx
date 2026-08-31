import Link from "next/link";

import { Logo } from "@/components/brand/logo";
import { Comparison, LayerRemoval } from "@/components/landing/comparison";
import { EngineLoop } from "@/components/landing/engine-loop";
import { KnowledgeField } from "@/components/landing/knowledge-field";
import { StorySequence } from "@/components/landing/story-sequence";
import { Counter, Reveal } from "@/components/motion";
import { SectionMarker } from "@/components/ui/primitives";

const SIGNALS = [
  { weight: 40, name: "Assessment accuracy", detail: "Adaptive items, difficulty-weighted" },
  { weight: 25, name: "Code execution success", detail: "Sandboxed runs against real assertions" },
  { weight: 20, name: "Task difficulty mastery", detail: "The hardest thing you actually passed" },
  { weight: 15, name: "Consistency", detail: "Smoothed across attempts, not one lucky run" },
];

const CAPABILITIES = [
  {
    id: "01",
    title: "Practice Mode",
    body: "A complete project loads with exactly one layer stripped out. You write the missing layer — nothing else — and deterministic checks decide whether it holds.",
  },
  {
    id: "02",
    title: "Project Execution",
    body: "Describe an idea. The engine returns milestones, sprints and engineering tickets with acceptance criteria that cannot be self-marked as done.",
  },
  {
    id: "03",
    title: "Learning Digital Twin",
    body: "A persistent model of your verified skills, repeated mistakes, consistency and learning velocity. It is the reason the second week differs from the first.",
  },
  {
    id: "04",
    title: "Deterministic before AI",
    body: "Static checks and sandboxed tests decide pass or fail. The model diagnoses, mentors and remediates on top — it is never the source of truth.",
  },
];

/**
 * The six deliverables from the brief, each mapped to the surface that answers
 * it. Ordered as the brief orders them so the mapping is checkable at a glance.
 */
const DELIVERABLES = [
  {
    id: "01",
    brief: "Conversational interface for goals in natural language",
    built: "Onboarding + AI Mentor",
    body: "State a goal in plain language. It is parsed into a target, a stack and a skill set — then every claim inside it is queued for verification.",
  },
  {
    id: "02",
    brief: "Learner profiling engine",
    built: "Learning Digital Twin",
    body: "Interests, experience level, completed work and objectives held as one persistent model, updated from executed code rather than self-report.",
  },
  {
    id: "03",
    brief: "Recommendation engine for resources and projects",
    built: "Routing engine",
    body: "Practice modules, projects and remediation selected by traversing the dependency graph from your weakest verified prerequisite.",
  },
  {
    id: "04",
    brief: "Learning path generator with prerequisites and milestones",
    built: "Milestones → Sprints → Tickets",
    body: "A goal decomposes into milestones, sprints and engineering tickets with acceptance criteria and explicit blocked-by edges.",
  },
  {
    id: "05",
    brief: "AI assistant that explains recommendations and answers queries",
    built: "Why this next? + Mentor",
    body: "Every recommendation ships with the evidence that produced it. The mentor answers in context of the ticket, the failing checks and your twin.",
  },
  {
    id: "06",
    brief: "Dashboard for progress, skills, milestones and next actions",
    built: "Command centre + Knowledge graph",
    body: "Confidence per skill, repeated mistakes, sprint state and the single next action — with the dependency graph that justifies the ordering.",
  },
];

export default function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-x-hidden">
      <SiteHeader />

      {/* ------------------------------------------------------------- hero */}
      <section className="noise relative overflow-hidden border-b border-line">
        <div className="grid-bg absolute inset-0 opacity-40" aria-hidden />

        {/* Live 3D dependency lattice. Sits behind the type, masked at the edges so
            it never competes with the headline. */}
        <div
          className="pointer-events-none absolute inset-0 opacity-[0.85] [mask-image:radial-gradient(circle_at_62%_50%,black,transparent_72%)]"
          aria-hidden
        >
          <KnowledgeField />
        </div>

        <div
          className="pointer-events-none absolute -left-40 top-1/3 h-[520px] w-[520px] rounded-full bg-accent opacity-[0.06] blur-[120px]"
          aria-hidden
        />

        <div className="relative mx-auto grid max-w-[1400px] items-center gap-16 px-6 py-24 sm:px-10 lg:grid-cols-[1.15fr_1fr] lg:py-36">
          <div>
            <div className="animate-reveal flex items-center gap-3">
              <span className="h-1 w-1 rounded-full bg-accent" />
              <p className="label">Continuous adaptive learning engine</p>
            </div>

            {/* Line breaks are art-directed, so each line must not re-wrap. */}
            <h1 className="display mt-8 text-display-xl text-ink">
              <span
                className="block animate-reveal-blur whitespace-nowrap"
                style={{ animationDelay: "40ms" }}
              >
                DON&apos;T LEARN
              </span>
              <span
                className="block animate-reveal-blur whitespace-nowrap"
                style={{ animationDelay: "140ms" }}
              >
                WHAT YOU
              </span>
              <span
                className="block animate-reveal-blur whitespace-nowrap text-faint"
                style={{ animationDelay: "240ms" }}
              >
                ALREADY KNOW.
              </span>
            </h1>

            <p
              className="display mt-8 animate-reveal text-display-sm text-accent"
              style={{ animationDelay: "360ms" }}
            >
              Build what you don&apos;t.
            </p>

            <p
              className="mt-8 max-w-[52ch] animate-reveal text-[14px] leading-[1.75] text-muted"
              style={{ animationDelay: "440ms" }}
            >
              SprintForge verifies what you know, watches how you build, and continuously adapts
              what you learn next.
            </p>

            <div
              className="mt-11 flex animate-reveal flex-wrap items-center gap-3"
              style={{ animationDelay: "520ms" }}
            >
              <Link href="/register" className="btn-primary btn-mono px-6 py-3">
                Start building
                <span aria-hidden>→</span>
              </Link>
              <Link href="#engine" className="btn-ghost btn-mono px-6 py-3">
                Explore the engine
              </Link>
            </div>

            <p
              className="mt-12 animate-reveal font-mono text-[11px] leading-relaxed text-faint"
              style={{ animationDelay: "600ms" }}
            >
              No video library. No completion certificate.
              <br />
              Every score in this product traces back to code that ran.
            </p>
          </div>

          <div className="animate-reveal lg:justify-self-end" style={{ animationDelay: "280ms" }}>
            <EngineLoop />
          </div>
        </div>
      </section>

      {/* --------------------------------------------------- marquee strip */}
      <div className="overflow-hidden border-b border-line bg-surface py-3">
        <div className="fade-edge-r flex w-max animate-marquee items-center gap-10 whitespace-nowrap">
          {Array.from({ length: 2 }).map((_, copy) => (
            <div key={copy} className="flex items-center gap-10">
              {[
                "claim → verify",
                "sandboxed execution",
                "knowledge dependency graph",
                "confidence 0–100, explainable",
                "failure → root cause → remediation",
                "tickets with acceptance criteria",
                "digital twin updated per attempt",
                "difficulty adapts every submission",
              ].map((item) => (
                <span key={item} className="flex items-center gap-10">
                  <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-faint">
                    {item}
                  </span>
                  <span className="h-1 w-1 rounded-full bg-line-strong" />
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>

      {/* ------------------------------------------------------ the trace */}
      <section id="engine" className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
        <Reveal>
          <SectionMarker index="01" label="What the engine actually does" />
        </Reveal>
        <Reveal delay={80}>
          <h2 className="display mt-10 max-w-[26ch] text-display-md text-balance text-ink">
            It does not believe you. It checks.
          </h2>
          <p className="lede mt-6">
            Below is a real trace through the system: one claim, one assessment, one detected gap,
            and the roadmap rewriting itself around it.
          </p>
        </Reveal>

        <div className="mt-16">
          <StorySequence />
        </div>
      </section>

      {/* -------------------------------------------------- layer removal */}
      <section className="border-y border-line bg-surface/40">
        <div className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
          <Reveal>
            <SectionMarker index="02" label="Practice Mode" />
          </Reveal>
          <Reveal delay={80}>
            <div className="mt-10 grid gap-8 lg:grid-cols-[1fr_auto] lg:items-end">
              <h2 className="display max-w-[30ch] text-display-md text-balance text-ink">
                The system removes what you need to prove.
              </h2>
              <p className="max-w-[40ch] text-[13px] leading-relaxed text-muted">
                Not a quiz about CSS. A working product with the stylesheet deleted, the assertions
                already written, and no way to fake the result.
              </p>
            </div>
          </Reveal>

          <Reveal delay={140} className="mt-14">
            <LayerRemoval />
          </Reveal>
        </div>
      </section>

      {/* ----------------------------------------------------- comparison */}
      <section className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
        <Reveal>
          <SectionMarker index="03" label="Two models of learning" />
        </Reveal>
        <Reveal delay={80}>
          <h2 className="display mt-10 max-w-[24ch] text-display-md text-balance text-ink">
            One ends. One compounds.
          </h2>
        </Reveal>
        <Reveal delay={140} className="mt-14">
          <Comparison />
        </Reveal>
      </section>

      {/* ------------------------------------------------ confidence score */}
      <section className="border-y border-line bg-surface/40">
        <div className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
          <div className="grid gap-16 lg:grid-cols-[1fr_1.1fr]">
            <div>
              <Reveal>
                <SectionMarker index="04" label="The confidence score" />
              </Reveal>
              <Reveal delay={80}>
                <h2 className="display mt-10 max-w-[22ch] text-display-md text-balance text-ink">
                  A number you can argue with.
                </h2>
                <p className="lede mt-6">
                  The score is deterministic, so it can always be taken apart. When it is low,
                  SprintForge names the signal holding it back and hands you the task that moves it.
                </p>
              </Reveal>

              <Reveal delay={160} className="mt-10 flex items-baseline gap-4">
                <span className="display text-display-lg text-accent">
                  <Counter value={82} suffix="%" />
                </span>
                <span className="max-w-[16ch] font-mono text-[10px] uppercase tracking-[0.14em] text-faint">
                  example composite for a verified learner
                </span>
              </Reveal>
            </div>

            <Reveal delay={120}>
              <ul className="divide-y divide-line border-y border-line">
                {SIGNALS.map((signal, index) => (
                  <li key={signal.name} className="group flex items-center gap-5 py-5">
                    <span className="display w-16 flex-none text-[26px] tabular-nums text-ink transition-colors group-hover:text-accent">
                      {signal.weight}
                      <span className="text-[13px] text-faint">%</span>
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-[13px] text-ink">{signal.name}</span>
                      <span className="mt-0.5 block text-[11.5px] leading-relaxed text-muted">
                        {signal.detail}
                      </span>
                    </span>
                    <span
                      className="h-8 w-px flex-none origin-bottom bg-accent/30 animate-line-grow"
                      style={{
                        height: `${signal.weight * 0.7}px`,
                        animationDelay: `${index * 90}ms`,
                      }}
                      aria-hidden
                    />
                  </li>
                ))}
              </ul>
            </Reveal>
          </div>
        </div>
      </section>

      {/* --------------------------------------------------- capabilities */}
      <section className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
        <Reveal>
          <SectionMarker index="05" label="Inside the platform" />
        </Reveal>
        <div className="mt-14 grid gap-px overflow-hidden rounded-lg border border-line bg-line sm:grid-cols-2">
          {CAPABILITIES.map((item, index) => (
            <Reveal
              key={item.id}
              delay={index * 70}
              className="group bg-surface p-8 transition-colors duration-300 hover:bg-elevated"
            >
              <span className="font-mono text-[10px] text-accent">{item.id}</span>
              <h3 className="display mt-4 text-[17px] tracking-tight text-ink">{item.title}</h3>
              <p className="mt-3 max-w-[44ch] text-[12.5px] leading-[1.7] text-muted">
                {item.body}
              </p>
              <span
                className="mt-6 block h-px w-0 bg-accent/50 transition-all duration-500 ease-forge group-hover:w-12"
                aria-hidden
              />
            </Reveal>
          ))}
        </div>
      </section>

      {/* ----------------------------------------------- brief -> product */}
      <section className="border-t border-line bg-surface/30">
        <div className="mx-auto max-w-[1400px] px-6 py-24 sm:px-10 lg:py-32">
          <Reveal>
            <SectionMarker index="06" label="The brief, and where it is built" />
          </Reveal>

          <Reveal delay={60}>
            <h2 className="display mt-10 max-w-[26ch] text-display-sm text-balance text-ink">
              An AI-powered personalised learning path recommender — shipped as an engine, not a
              course catalogue.
            </h2>
          </Reveal>

          <ul className="mt-14 divide-y divide-line/70 border-y border-line">
            {DELIVERABLES.map((item, index) => (
              <Reveal as="li" key={item.id} delay={index * 50} className="group">
                <div className="grid gap-x-8 gap-y-3 py-6 md:grid-cols-[3rem_minmax(0,1fr)_minmax(0,1.15fr)] md:items-baseline">
                  <span className="font-mono text-[10px] text-accent">{item.id}</span>

                  <div>
                    <p className="text-[13.5px] leading-snug text-ink">{item.brief}</p>
                    <p className="mt-2 flex items-center gap-2">
                      <span className="h-px w-4 bg-accent/60 transition-all duration-500 ease-forge group-hover:w-8" />
                      <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-accent">
                        {item.built}
                      </span>
                    </p>
                  </div>

                  <p className="max-w-[52ch] text-[12px] leading-[1.75] text-muted">{item.body}</p>
                </div>
              </Reveal>
            ))}
          </ul>
        </div>
      </section>

      {/* ---------------------------------------------------------- close */}
      <section className="noise relative overflow-hidden border-t border-line">
        <div className="grid-bg absolute inset-0 opacity-60" aria-hidden />
        <div className="relative mx-auto max-w-[1400px] px-6 py-28 sm:px-10 lg:py-36">
          <Reveal>
            <h2 className="display max-w-[20ch] text-display-lg text-balance text-ink">
              Prove it, then build past it.
            </h2>
            <p className="lede mt-7">
              Start with one honest claim. The engine will take it from there — and it will tell you
              exactly why it chose whatever comes next.
            </p>
            <div className="mt-11 flex flex-wrap items-center gap-3">
              <Link href="/register" className="btn-primary btn-mono px-6 py-3">
                Start building
                <span aria-hidden>→</span>
              </Link>
              <Link href="/login" className="btn-ghost btn-mono px-6 py-3">
                Sign in
              </Link>
            </div>
          </Reveal>
        </div>
      </section>

      <footer className="border-t border-line">
        <div className="mx-auto flex max-w-[1400px] flex-wrap items-center gap-4 px-6 py-8 sm:px-10">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-faint">
            SprintForge.AI
          </span>
          <span className="h-px flex-1 bg-line" />
          <span className="font-mono text-[10px] text-faint">
            Learn by building · Verify by doing · Adapt by performance
          </span>
        </div>
      </footer>
    </div>
  );
}

function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line bg-canvas/80 backdrop-blur-md">
      <div className="mx-auto flex h-16 max-w-[1400px] items-center gap-6 px-6 sm:px-10">
        <Link href="/">
          <Logo animated />
        </Link>

        <nav className="ml-auto flex items-center gap-1">
          <Link
            href="/login"
            className="rounded px-3 py-1.5 font-mono text-[11px] uppercase tracking-[0.1em] text-muted transition-colors hover:text-ink"
          >
            Sign in
          </Link>
          <Link href="/register" className="btn-primary btn-mono px-4 py-2">
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
