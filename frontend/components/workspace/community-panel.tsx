"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FormEvent, useState } from "react";

import { Avatar } from "@/components/ui/avatar";
import { Alert, EmptyState, PanelSkeleton } from "@/components/ui/primitives";
import { api } from "@/lib/api";
import type { CommunityPost } from "@/lib/types";
import { cn, errorMessage, relativeTime } from "@/lib/utils";

const MAX_BODY = 2000;

/**
 * Per-module discussion. Bodies are rendered as text nodes only — user content is
 * never interpreted as markup.
 */
export function CommunityPanel({ moduleId }: { moduleId: string }) {
  const queryClient = useQueryClient();
  const [body, setBody] = useState("");
  const [replyTo, setReplyTo] = useState<string | null>(null);
  const [replyBody, setReplyBody] = useState("");
  const [error, setError] = useState<string | null>(null);

  const thread = useQuery({
    queryKey: ["community", moduleId],
    queryFn: () => api<{ posts: CommunityPost[]; total: number }>(`/community/modules/${moduleId}/posts`),
  });

  async function invalidate() {
    await queryClient.invalidateQueries({ queryKey: ["community", moduleId] });
    await queryClient.invalidateQueries({ queryKey: ["community-counts"] });
  }

  const post = useMutation({
    mutationFn: (input: { body: string; parent_id: string | null }) =>
      api<CommunityPost>(`/community/modules/${moduleId}/posts`, { method: "POST", body: input }),
    onSuccess: async () => {
      setBody("");
      setReplyBody("");
      setReplyTo(null);
      setError(null);
      await invalidate();
    },
    onError: (mutationError) => setError(errorMessage(mutationError)),
  });

  const remove = useMutation({
    mutationFn: (postId: string) => api<void>(`/community/posts/${postId}`, { method: "DELETE" }),
    onSuccess: async () => {
      setError(null);
      await invalidate();
    },
    onError: (mutationError) => setError(errorMessage(mutationError)),
  });

  function submitRoot(event: FormEvent) {
    event.preventDefault();
    const trimmed = body.trim();
    if (!trimmed) return;
    post.mutate({ body: trimmed, parent_id: null });
  }

  function submitReply(event: FormEvent, parentId: string) {
    event.preventDefault();
    const trimmed = replyBody.trim();
    if (!trimmed) return;
    post.mutate({ body: trimmed, parent_id: parentId });
  }

  const posts = thread.data?.posts ?? [];

  return (
    <div className="space-y-5">
      <form onSubmit={submitRoot}>
        <label htmlFor="community-body" className="label mb-1.5 block">
          Ask or share
        </label>
        <textarea
          id="community-body"
          className="input min-h-[76px] text-[12px]"
          placeholder="What tripped you up on this module?"
          maxLength={MAX_BODY}
          value={body}
          onChange={(event) => setBody(event.target.value)}
        />
        <div className="mt-2 flex items-center justify-between gap-3">
          <span className="font-mono text-[10px] tabular-nums text-faint">
            {body.length}/{MAX_BODY}
          </span>
          <button
            type="submit"
            className="btn-primary btn-mono px-4 py-1.5"
            disabled={post.isPending || body.trim().length === 0}
          >
            {post.isPending && replyTo === null ? "Posting…" : "Post"}
          </button>
        </div>
      </form>

      {error ? <Alert tone="danger">{error}</Alert> : null}

      {thread.isLoading ? (
        <PanelSkeleton lines={5} />
      ) : thread.error ? (
        <Alert tone="danger" title="Discussion unavailable">
          {errorMessage(thread.error)}
        </Alert>
      ) : posts.length === 0 ? (
        <EmptyState
          eyebrow="Community"
          title="No discussion yet."
          description="Be the first to post a question, a hint or what finally made this module click."
        />
      ) : (
        <ul className="space-y-4">
          {posts.map((item) => (
            <li key={item.id} className="border-t border-line pt-4 first:border-0 first:pt-0">
              <PostBody post={item} onDelete={() => remove.mutate(item.id)} deleting={remove.isPending} />

              {item.replies.length > 0 ? (
                <ul className="mt-3 space-y-3 border-l border-line pl-3">
                  {item.replies.map((reply) => (
                    <li key={reply.id}>
                      <PostBody
                        post={reply}
                        onDelete={() => remove.mutate(reply.id)}
                        deleting={remove.isPending}
                        compact
                      />
                    </li>
                  ))}
                </ul>
              ) : null}

              {replyTo === item.id ? (
                <form onSubmit={(event) => submitReply(event, item.id)} className="mt-3 pl-3">
                  <textarea
                    className="input min-h-[60px] text-[12px]"
                    placeholder="Reply…"
                    maxLength={MAX_BODY}
                    value={replyBody}
                    autoFocus
                    onChange={(event) => setReplyBody(event.target.value)}
                  />
                  <div className="mt-2 flex gap-2">
                    <button
                      type="submit"
                      className="btn-subtle btn-mono px-3 py-1.5"
                      disabled={post.isPending || replyBody.trim().length === 0}
                    >
                      {post.isPending ? "Replying…" : "Reply"}
                    </button>
                    <button
                      type="button"
                      className="btn-ghost btn-mono px-3 py-1.5"
                      onClick={() => {
                        setReplyTo(null);
                        setReplyBody("");
                      }}
                    >
                      Cancel
                    </button>
                  </div>
                </form>
              ) : (
                <button
                  type="button"
                  className="mt-2 font-mono text-[10px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-accent"
                  onClick={() => {
                    setReplyTo(item.id);
                    setReplyBody("");
                  }}
                >
                  Reply
                </button>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function PostBody({
  post,
  onDelete,
  deleting,
  compact = false,
}: {
  post: CommunityPost;
  onDelete: () => void;
  deleting: boolean;
  compact?: boolean;
}) {
  return (
    <div className="flex min-w-0 gap-2.5">
      <Avatar name={post.author.name} src={post.author.avatar_url} size={compact ? "xs" : "sm"} />
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-baseline gap-x-2 gap-y-0.5">
          <span className={cn("truncate text-ink", compact ? "text-[11.5px]" : "text-[12px]")}>
            {post.author.name}
          </span>
          <span className="font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint">
            {relativeTime(post.created_at)}
          </span>
          {post.can_delete ? (
            <button
              type="button"
              onClick={onDelete}
              disabled={deleting}
              className="ml-auto font-mono text-[9.5px] uppercase tracking-[0.1em] text-faint transition-colors hover:text-danger"
            >
              Delete
            </button>
          ) : null}
        </div>
        <p className="mt-1 whitespace-pre-wrap break-words text-[12px] leading-relaxed text-muted">
          {post.body}
        </p>
      </div>
    </div>
  );
}
