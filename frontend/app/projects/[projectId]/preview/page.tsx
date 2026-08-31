"use client";

import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useParams } from "next/navigation";

import { AppShell, PageHeader } from "@/components/app-shell";
import { GrowBar } from "@/components/motion";
import { Alert, Badge, EmptyState, Loader, Panel, StatusPill } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { ProjectPreview } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

/**
 * The product itself, rather than the board that plans it.
 *
 * Assembled server-side from every verified ticket in board order by the same
 * service the ticket workspace uses, so this can never disagree with the pane a
 * learner sees while working. Display only.
 */
export default function ProjectPreviewPage() {
  const params = useParams<{ projectId: string }>();
  const projectId = params.projectId;

  const { data, isLoading, error } = useQuery({
    queryKey: ["project-preview", projectId],
    queryFn: () => api<ProjectPreview>(`/projects/${projectId}/preview`),
  });

  if (isLoading) {
    return (
      <AppShell wide>
        <div className="grid min-h-[50vh] place-items-center">
          <Loader label="Assembling your project" />
        </div>
      </AppShell>
    );
  }

  if (error || !data) {
    return (
      <AppShell wide>
        <Alert tone="danger" title="Could not build the preview">
          {errorMessage(error) || "Project not found."}
        </Alert>
      </AppShell>
    );
  }

  const { project, html, meta } = data;
  const percent =
    meta.total_tickets > 0 ? (meta.verified_tickets / meta.total_tickets) * 100 : 0;
  /**
   * Defaulted rather than read straight off `meta`.
   *
   * These arrived in a later backend revision, so a server running older code —
   * or any future response that drops a field — would otherwise reach
   * `undefined.length` and white-screen the whole page. A preview is a
   * read-only view; a missing count should cost a badge, not the render.
   */
  const unfinished = meta.unfinished_tickets ?? [];
  const inProgress = meta.in_progress_contributors ?? [];
  const verifiedContributors = meta.verified_contributors ?? [];
  const contributingTickets = meta.contributing_tickets ?? [];
  const previewFiles = meta.files ?? [];
  const mountPoints = meta.mount_points ?? [];

  return (
    <AppShell wide>
      <PageHeader
        eyebrow="Live product preview"
        title={project.title}
        meta={
          <>
            <p className="max-w-[70ch] text-[12.5px] leading-[1.7] text-muted">
              Everything your verified tickets have shipped, rendered as one document — the
              product, not the plan
              {meta.includes_unverified
                ? ", with the work you have started but not finished layered on top."
                : "."}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-1.5">
              <StatusPill status={project.status} />
              <Badge tone="accent">
                {meta.verified_tickets}/{meta.total_tickets} tickets verified
              </Badge>
              {inProgress.length > 0 ? (
                <Badge tone="warning">
                  {inProgress.length} unverified ticket{inProgress.length === 1 ? "" : "s"} included
                </Badge>
              ) : null}
              {meta.synthesized_host ? <Badge tone="warning">scaffolded host</Badge> : null}
            </div>
          </>
        }
        actions={
          <Link href={`/projects/${projectId}`} className="btn-ghost btn-mono px-4 py-2">
            ← Sprint board
          </Link>
        }
      />

      {unfinished.length > 0 ? (
        <div className="mt-8">
          {/* Half-finished work is in the preview but is not shipped work, so it
              is named, flagged, and given a way back rather than blended in. */}
          <Alert tone="warning" title="Some of this is unfinished work">
            <p className="text-[12px] leading-relaxed text-muted">
              You left {unfinished.length === 1 ? "a ticket" : `${unfinished.length} tickets`} part
              way through. That code is layered into the preview above so you can see it, but it is
              not verified yet. Finish {unfinished.length === 1 ? "it" : "them"} and this preview
              becomes the complete, verified product.
            </p>
            <div className="mt-3 space-y-1.5">
              {unfinished.map((ticket) => (
                <div
                  key={ticket.ticket_id}
                  className="flex flex-wrap items-center justify-between gap-2 rounded border border-line px-3 py-2"
                >
                  <div className="min-w-0">
                    <p className="font-mono text-[10px] uppercase tracking-[0.1em] text-faint">
                      {ticket.key} · unverified
                    </p>
                    <p className="truncate text-[12.5px] text-ink">{ticket.title}</p>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <StatusPill status={ticket.status} />
                    <Link
                      href={`/workspace/${ticket.ticket_id}`}
                      className="btn-primary btn-mono px-3 py-1.5"
                    >
                      Finish {ticket.key} →
                    </Link>
                  </div>
                </div>
              ))}
            </div>
          </Alert>
        </div>
      ) : null}

      <div
        className={`grid gap-4 lg:grid-cols-[1fr_300px] ${
          unfinished.length > 0 ? "mt-4" : "mt-8"
        }`}
      >
        <Panel inset={false} className="overflow-hidden">
          <div className="flex items-center justify-between gap-4 border-b border-line px-5 py-3">
            <p className="label">Rendered output</p>
            <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
              read-only · sandboxed
              {meta.includes_unverified ? " · includes unverified work" : ""}
            </span>
          </div>
          {html ? (
            <iframe
              title="Project preview"
              srcDoc={html}
              sandbox="allow-scripts"
              className="h-[70vh] w-full border-0 bg-white"
            />
          ) : (
            <div className="p-5">
              {/* A project with nothing verified must say so rather than render a
                  blank white frame that reads as a broken preview. */}
              <EmptyState
                eyebrow="nothing to render yet"
                title={
                  unfinished.length > 0
                    ? "Not enough written yet to render"
                    : "No work in this project yet"
                }
                description={
                  unfinished.length > 0
                    ? "The tickets you started do not yet contain anything a browser can draw. Pick one up above and the product starts appearing here."
                    : "Tickets contribute to this preview as soon as you start writing in them. Open your first ticket and the product appears here."
                }
                action={
                  <Link
                    href={
                      unfinished.length > 0
                        ? `/workspace/${unfinished[0].ticket_id}`
                        : `/projects/${projectId}`
                    }
                    className="btn-primary btn-mono px-4 py-2"
                  >
                    {unfinished.length > 0
                      ? `Resume ${unfinished[0].key} →`
                      : "Open the sprint board →"}
                  </Link>
                }
              />
            </div>
          )}
        </Panel>

        <div className="space-y-4">
          <Panel>
            <p className="label">Build progress</p>
            <p className="display mt-1.5 text-[30px] leading-none text-accent">
              {meta.verified_tickets}
              <span className="text-[15px] text-faint">/{meta.total_tickets}</span>
            </p>
            <GrowBar value={percent} tone={percent === 100 ? "success" : "accent"} className="mt-3" />
            <p className="mt-3 text-[11.5px] leading-relaxed text-muted">
              {meta.verified_tickets === 0
                ? "No ticket has been verified yet, so nothing has shipped."
                : `Composed from ${verifiedContributors.length} ticket${
                    verifiedContributors.length === 1 ? "" : "s"
                  } of verified work.`}
              {inProgress.length > 0
                ? ` ${inProgress.length} more ticket${
                    inProgress.length === 1 ? " is" : "s are"
                  } drawn in from unverified work in progress.`
                : ""}
            </p>
          </Panel>

          {contributingTickets.length > 0 ? (
            <Panel>
              <p className="label">Contributing tickets</p>
              {verifiedContributors.length > 0 ? (
                <div className="mt-2.5 flex flex-wrap gap-1.5">
                  {verifiedContributors.map((key) => (
                    <Badge key={key} tone="success">
                      {key}
                    </Badge>
                  ))}
                </div>
              ) : null}
              {inProgress.length > 0 ? (
                <>
                  <p className="label mt-4">Unverified, in progress</p>
                  <div className="mt-2.5 flex flex-wrap gap-1.5">
                    {inProgress.map((ticket) => (
                      <Link key={ticket.ticket_id} href={`/workspace/${ticket.ticket_id}`}>
                        <Badge tone="warning">{ticket.key}</Badge>
                      </Link>
                    ))}
                  </div>
                </>
              ) : null}
            </Panel>
          ) : null}

          {previewFiles.length > 0 ? (
            <Panel>
              <p className="label">Files in this build</p>
              <div className="mt-2.5 flex flex-wrap gap-1.5">
                {previewFiles.map((file) => (
                  <span key={file} className="chip font-mono text-[9.5px]">
                    {file}
                  </span>
                ))}
              </div>
              {meta.synthesized_host ? (
                <p className="mt-3 text-[11px] leading-relaxed text-faint">
                  This project has no page markup yet, so the preview uses a plain scaffold
                  {mountPoints.length > 0
                    ? ` with the mount points your scripts need (${mountPoints
                        .map((id) => `#${id}`)
                        .join(" ")})`
                    : ""}
                  . An HTML ticket will replace it with your own.
                </p>
              ) : null}
            </Panel>
          ) : null}
        </div>
      </div>
    </AppShell>
  );
}
