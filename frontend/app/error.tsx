"use client";

import Link from "next/link";
import { useEffect } from "react";

/**
 * Route-level error boundary.
 *
 * The underlying error is logged for developers but never rendered — the user
 * gets a calm system message and a way forward.
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error(error);
  }, [error]);

  return (
    <div className="grid min-h-screen place-items-center px-6">
      <div className="grid-bg-fine w-full max-w-[520px] rounded-lg border border-line bg-surface p-8">
        <div className="flex items-center gap-3">
          <span className="h-1.5 w-1.5 rounded-full bg-danger" />
          <p className="label text-danger">system error</p>
        </div>

        <h1 className="display mt-5 text-display-sm text-ink">Something broke on our side.</h1>
        <p className="mt-4 max-w-[44ch] text-[12.5px] leading-relaxed text-muted">
          Your progress is stored server-side, so nothing you completed was lost. Retry the view,
          or head back to the dashboard.
        </p>

        {error.digest ? (
          <p className="mt-5 font-mono text-[10px] uppercase tracking-[0.12em] text-faint">
            reference {error.digest}
          </p>
        ) : null}

        <div className="mt-8 flex flex-wrap gap-2">
          <button onClick={reset} className="btn-primary btn-mono px-5 py-2.5">
            Try again →
          </button>
          <Link href="/dashboard" className="btn-ghost btn-mono px-5 py-2.5">
            Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
