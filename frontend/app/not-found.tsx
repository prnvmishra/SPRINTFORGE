import Link from "next/link";

export default function NotFound() {
  return (
    <div className="grid min-h-screen place-items-center px-6">
      <div className="w-full max-w-[520px]">
        <p className="label">404 · route not found</p>
        <h1 className="display mt-5 text-display-md text-ink">
          Nothing is built here yet.
        </h1>
        <p className="mt-5 max-w-[44ch] text-[12.5px] leading-relaxed text-muted">
          This page does not exist — or the ticket, module or project it pointed at was reset.
        </p>
        <div className="mt-9 flex flex-wrap gap-2">
          <Link href="/dashboard" className="btn-primary btn-mono px-5 py-2.5">
            Back to dashboard →
          </Link>
          <Link href="/practice" className="btn-ghost btn-mono px-5 py-2.5">
            Browse practice
          </Link>
        </div>
      </div>
    </div>
  );
}
