"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Fragment, ReactNode, useEffect, useState } from "react";

import { Logo } from "@/components/brand/logo";
import { Avatar } from "@/components/ui/avatar";
import { Loader } from "@/components/ui/primitives";
import { useAuth } from "@/hooks/use-auth";
import { cn } from "@/lib/utils";

/**
 * Ordered as the engine loop runs, not alphabetically or by page age:
 *
 *   verify → diagnose → personalise → build → progress
 *
 * Dashboard sits alone at the head as the command centre you return to between
 * stages. The groups are separated in the bar so the reading order is visible
 * rather than implied by position alone.
 *
 * The career catalogue at `/paths` is deliberately absent. It used to sit next
 * to `/path` as "Paths" beside "My Path", which are different things one letter
 * apart — the catalogue of tracks versus this learner's generated route. It is
 * reached from inside My Path instead, where choosing a goal belongs.
 */
const NAV = [
  { href: "/dashboard", label: "Dashboard", group: "home" },
  { href: "/assessment", label: "Verify", group: "know" },
  { href: "/profile", label: "Twin", group: "know" },
  { href: "/path", label: "My Path", group: "know" },
  { href: "/practice", label: "Practice", group: "build" },
  { href: "/projects", label: "Projects", group: "build" },
  { href: "/leaderboard", label: "Leaderboard", group: "progress" },
];

/** Names the stage each nav group belongs to. Shown in the mobile drawer,
 *  where there is room for words instead of a separator rule. */
const GROUP_LABEL: Record<string, string> = {
  know: "What the engine knows",
  build: "Where you build it",
  progress: "Progress",
};

/** Re-exported so existing imports from the shell keep working. */
export { Logo };

/**
 * Application chrome for every authenticated route.
 *
 * The header compresses on scroll so the workspace gets more vertical space, and
 * collapses to a drawer on small screens rather than wrapping into two rows.
 */
export function AppShell({
  children,
  wide = false,
  bleed = false,
}: {
  children: ReactNode;
  /** Wider max width, for board and workspace layouts. */
  wide?: boolean;
  /** Removes the page gutter entirely, for full-height IDE screens. */
  bleed?: boolean;
}) {
  const { user, status, unreachable, refresh, logout } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    // Only bounce to login when the API actually said the session is invalid.
    // If it never answered, the token may still be good, so keep the user here.
    if (status === "anonymous" && !unreachable) router.replace("/login");
  }, [status, unreachable, router]);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  // Close the drawer whenever the route changes.
  useEffect(() => setMenuOpen(false), [pathname]);

  if (unreachable) {
    return (
      <div className="grid min-h-screen place-items-center px-6">
        <div className="w-full max-w-md space-y-4 text-center">
          <p className="label">Connection</p>
          <h1 className="display text-display-sm">Can&apos;t reach SprintForge</h1>
          <p className="text-sm text-muted">
            Your session could not be checked because the server did not respond. You are still
            signed in — this is a connection problem, not a sign-out.
          </p>
          <button type="button" className="btn btn-primary" onClick={() => void refresh()}>
            TRY AGAIN
          </button>
        </div>
      </div>
    );
  }

  if (status !== "authenticated" || !user) {
    return (
      <div className="grid min-h-screen place-items-center">
        <Loader label="Restoring session" />
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <header
        className={cn(
          "sticky top-0 z-50 border-b border-line bg-canvas/85 backdrop-blur-md transition-all duration-300 ease-forge",
          scrolled ? "h-12" : "h-16",
        )}
      >
        <div
          className={cn(
            "mx-auto flex h-full items-center gap-6 px-4 sm:px-6",
            wide ? "max-w-[1800px]" : "max-w-[1400px]",
          )}
        >
          <Link href="/dashboard" className="flex-none">
            <Logo />
          </Link>

          <nav className="ml-2 hidden items-center lg:flex">
            {NAV.map((item, index) => {
              const active =
                pathname === item.href || pathname.startsWith(`${item.href}/`);
              const startsGroup = index > 0 && NAV[index - 1].group !== item.group;
              return (
                <Fragment key={item.href}>
                  {startsGroup ? (
                    <span className="mx-2 h-3 w-px flex-none bg-line-strong" aria-hidden />
                  ) : null}
                <Link
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "group relative px-3 py-2 font-mono text-[11px] uppercase tracking-[0.1em] transition-colors duration-200",
                    active ? "text-ink" : "text-faint hover:text-muted",
                  )}
                >
                  {item.label}
                  {/* Active marker doubles as the hover affordance. */}
                  <span
                    className={cn(
                      "absolute inset-x-3 -bottom-px h-px bg-accent transition-transform duration-300 ease-forge",
                      active ? "scale-x-100" : "scale-x-0 group-hover:scale-x-100",
                    )}
                    aria-hidden
                  />
                </Link>
                </Fragment>
              );
            })}
          </nav>

          <div className="ml-auto flex items-center gap-3">
            <Link
              href="/profile"
              className="hidden items-center gap-2.5 rounded px-2 py-1 transition-colors hover:bg-elevated sm:flex"
            >
              <span className="text-right">
                <span className="block text-[11.5px] leading-tight text-ink">{user.name}</span>
                <span className="block font-mono text-[9.5px] uppercase leading-tight tracking-[0.1em] text-faint">
                  digital twin
                </span>
              </span>
              <Avatar name={user.name} src={user.avatar_url} size="sm" />
            </Link>

            <Link
              href="/settings"
              aria-label="Settings"
              className="hidden font-mono text-[10px] uppercase tracking-[0.12em] text-faint transition-colors hover:text-ink sm:block"
            >
              Settings
            </Link>

            <button
              onClick={() => void logout()}
              className="hidden font-mono text-[10px] uppercase tracking-[0.12em] text-faint transition-colors hover:text-danger lg:block"
            >
              Sign out
            </button>

            <button
              onClick={() => setMenuOpen((value) => !value)}
              aria-label="Toggle navigation"
              aria-expanded={menuOpen}
              className="flex h-8 w-8 flex-col items-center justify-center gap-[5px] lg:hidden"
            >
              <span
                className={cn(
                  "h-px w-4 bg-ink transition-transform duration-300",
                  menuOpen && "translate-y-[3px] rotate-45",
                )}
              />
              <span
                className={cn(
                  "h-px w-4 bg-ink transition-transform duration-300",
                  menuOpen && "-translate-y-[3px] -rotate-45",
                )}
              />
            </button>
          </div>
        </div>
      </header>

      {/* Mobile drawer */}
      <div
        className={cn(
          "fixed inset-x-0 top-12 z-40 origin-top border-b border-line bg-canvas/95 backdrop-blur-md transition-all duration-300 ease-forge lg:hidden",
          menuOpen ? "pointer-events-auto opacity-100" : "pointer-events-none -translate-y-2 opacity-0",
        )}
      >
        <nav className="flex flex-col px-4 py-3">
          {NAV.map((item, index) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            const startsGroup = index === 0 || NAV[index - 1].group !== item.group;
            return (
              <Fragment key={item.href}>
                {startsGroup && GROUP_LABEL[item.group] ? (
                  <p className="label mt-4 first:mt-1 pb-1 text-faint">{GROUP_LABEL[item.group]}</p>
                ) : null}
              <Link
                href={item.href}
                className={cn(
                  "flex items-center justify-between border-b border-line/60 py-3 font-mono text-[12px] uppercase tracking-[0.1em] last:border-0",
                  active ? "text-accent" : "text-muted",
                )}
              >
                {item.label}
                {active ? <span className="text-[9px]">●</span> : null}
              </Link>
              </Fragment>
            );
          })}
          <Link
            href="/settings"
            className={cn(
              "flex items-center justify-between border-b border-line/60 py-3 font-mono text-[12px] uppercase tracking-[0.1em]",
              pathname === "/settings" ? "text-accent" : "text-muted",
            )}
          >
            Settings
            {pathname === "/settings" ? <span className="text-[9px]">●</span> : null}
          </Link>
          <button
            onClick={() => void logout()}
            className="mt-3 text-left font-mono text-[11px] uppercase tracking-[0.12em] text-danger"
          >
            Sign out
          </button>
        </nav>
      </div>

      <main
        className={cn(
          bleed ? "" : "mx-auto px-4 py-8 sm:px-6",
          bleed ? "" : wide ? "max-w-[1800px]" : "max-w-[1400px]",
        )}
      >
        {children}
      </main>
    </div>
  );
}

/**
 * Page header used across authenticated screens: mono eyebrow, editorial title,
 * optional metadata row and actions.
 */
export function PageHeader({
  eyebrow,
  title,
  meta,
  actions,
  className,
}: {
  eyebrow?: string;
  title: ReactNode;
  meta?: ReactNode;
  actions?: ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-wrap items-end justify-between gap-5", className)}>
      <div className="min-w-0">
        {eyebrow ? <p className="label">{eyebrow}</p> : null}
        <h1 className="display mt-2 text-display-sm text-balance text-ink">{title}</h1>
        {meta ? <div className="mt-2.5">{meta}</div> : null}
      </div>
      {actions ? <div className="flex flex-wrap items-center gap-2">{actions}</div> : null}
    </div>
  );
}
