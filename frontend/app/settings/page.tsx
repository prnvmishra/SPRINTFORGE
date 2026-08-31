"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { ChangeEvent, FormEvent, ReactNode, useEffect, useRef, useState } from "react";

import { AppShell, PageHeader } from "@/components/app-shell";
import { Avatar, avatarSrc } from "@/components/ui/avatar";
import { Alert, Panel, SectionTitle } from "@/components/ui/primitives";
import { useAuth } from "@/hooks/use-auth";
import { api, API_URL, ApiError, getToken, setToken } from "@/lib/api";
import type { User } from "@/lib/types";
import { errorMessage } from "@/lib/utils";

const ACCEPTED_IMAGE_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_AVATAR_BYTES = 2 * 1024 * 1024;

export default function SettingsPage() {
  const { user, refresh, logout } = useAuth();

  return (
    <AppShell>
      <PageHeader
        eyebrow="Account"
        title="Settings"
        meta={
          <p className="max-w-[62ch] text-[12.5px] leading-[1.7] text-muted">
            Your profile, photo and credentials. Deleting the account removes every attempt,
            ticket, project and skill record the engine holds about you.
          </p>
        }
      />

      {!user ? null : (
        <div className="mt-10 grid gap-6 lg:grid-cols-2">
          <AvatarSection user={user} onSaved={refresh} />
          <ProfileSection user={user} onSaved={refresh} />
          <PasswordSection />
          <DangerZone user={user} onDeleted={logout} />
        </div>
      )}
    </AppShell>
  );
}

/* ------------------------------------------------------------------ photo */

function AvatarSection({ user, onSaved }: { user: User; onSaved: () => Promise<void> }) {
  const [preview, setPreview] = useState<string | null>(null);
  const [pending, setPending] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => () => {
    if (preview) URL.revokeObjectURL(preview);
  }, [preview]);

  function pick(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;
    setDone(null);
    if (!ACCEPTED_IMAGE_TYPES.includes(file.type)) {
      setError("Choose a JPEG, PNG or WebP image.");
      return;
    }
    if (file.size > MAX_AVATAR_BYTES) {
      setError("That image is larger than 2MB.");
      return;
    }
    setError(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(URL.createObjectURL(file));
    setPending(file);
  }

  function discard() {
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setPending(null);
  }

  async function save() {
    if (!pending) return;
    setBusy(true);
    setError(null);
    try {
      const form = new FormData();
      form.append("file", pending);
      const token = getToken();
      const response = await fetch(`${API_URL}/account/avatar`, {
        method: "POST",
        credentials: "include",
        headers: token ? { Authorization: `Bearer ${token}` } : undefined,
        body: form,
      });
      if (!response.ok) {
        const payload = await response.json().catch(() => null);
        throw new ApiError(response.status, payload?.detail ?? "Upload failed.");
      }
      discard();
      await onSaved();
      setDone("Photo updated.");
    } catch (uploadError) {
      setError(errorMessage(uploadError));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setError(null);
    try {
      await api<User>("/account/avatar", { method: "DELETE" });
      discard();
      await onSaved();
      setDone("Photo removed. Showing your initials.");
    } catch (removeError) {
      setError(errorMessage(removeError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel>
      <SectionTitle eyebrow="Profile picture" title="Photo" hint="JPEG, PNG or WebP · up to 2MB." />

      <div className="flex flex-wrap items-center gap-5">
        {preview ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={preview}
            alt="Selected photo preview"
            className="h-24 w-24 flex-none rounded-sm border border-accent/40 object-cover"
          />
        ) : (
          <Avatar name={user.name} src={user.avatar_url} size="xl" />
        )}

        <div className="flex min-w-0 flex-wrap items-center gap-2">
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_IMAGE_TYPES.join(",")}
            onChange={pick}
            className="hidden"
          />
          <button
            type="button"
            onClick={() => inputRef.current?.click()}
            className="btn-subtle btn-mono px-4 py-2"
            disabled={busy}
          >
            Choose photo
          </button>
          {pending ? (
            <>
              <button
                type="button"
                onClick={() => void save()}
                className="btn-primary btn-mono px-4 py-2"
                disabled={busy}
              >
                {busy ? "Uploading…" : "Save photo"}
              </button>
              <button type="button" onClick={discard} className="btn-ghost btn-mono px-4 py-2" disabled={busy}>
                Discard
              </button>
            </>
          ) : avatarSrc(user.avatar_url) ? (
            <button
              type="button"
              onClick={() => void remove()}
              className="btn-ghost btn-mono px-4 py-2"
              disabled={busy}
            >
              Remove
            </button>
          ) : null}
        </div>
      </div>

      {error ? (
        <div className="mt-4">
          <Alert tone="danger">{error}</Alert>
        </div>
      ) : done ? (
        <div className="mt-4">
          <Alert tone="success">{done}</Alert>
        </div>
      ) : null}
    </Panel>
  );
}

/* ---------------------------------------------------------------- profile */

function ProfileSection({ user, onSaved }: { user: User; onSaved: () => Promise<void> }) {
  const [name, setName] = useState(user.name);
  const [email, setEmail] = useState(user.email);
  const [bio, setBio] = useState(user.bio ?? "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setDone(false);
    try {
      await api<User>("/account/profile", { method: "PATCH", body: { name, email, bio } });
      await onSaved();
      setDone(true);
    } catch (saveError) {
      setError(errorMessage(saveError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel>
      <SectionTitle eyebrow="Identity" title="Profile" hint="How you appear on the leaderboard and in module discussions." />

      <form onSubmit={submit} className="space-y-4">
        <Field label="Display name" htmlFor="name">
          <input
            id="name"
            className="input"
            value={name}
            maxLength={120}
            required
            onChange={(event) => setName(event.target.value)}
          />
        </Field>

        <Field label="Email" htmlFor="email">
          <input
            id="email"
            type="email"
            className="input"
            value={email}
            required
            onChange={(event) => setEmail(event.target.value)}
          />
        </Field>

        <Field label="Short bio" htmlFor="bio" hint={`${bio.length}/280`}>
          <textarea
            id="bio"
            className="input min-h-[76px]"
            value={bio}
            maxLength={280}
            onChange={(event) => setBio(event.target.value)}
          />
        </Field>

        {error ? <Alert tone="danger">{error}</Alert> : null}
        {done ? <Alert tone="success">Profile saved.</Alert> : null}

        <button type="submit" className="btn-primary btn-mono px-4 py-2" disabled={busy}>
          {busy ? "Saving…" : "Save profile"}
        </button>
      </form>
    </Panel>
  );
}

/* --------------------------------------------------------------- password */

function PasswordSection() {
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [done, setDone] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setDone(false);
    if (next.length < 8) {
      setError("Use at least 8 characters for the new password.");
      return;
    }
    if (next !== confirm) {
      setError("The new passwords do not match.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api<void>("/account/password", {
        method: "POST",
        body: { current_password: current, new_password: next },
      });
      setCurrent("");
      setNext("");
      setConfirm("");
      setDone(true);
    } catch (changeError) {
      setError(errorMessage(changeError));
    } finally {
      setBusy(false);
    }
  }

  return (
    <Panel>
      <SectionTitle eyebrow="Credentials" title="Change password" hint="Minimum 8 characters." />

      <form onSubmit={submit} className="space-y-4">
        <Field label="Current password" htmlFor="current-password">
          <input
            id="current-password"
            type="password"
            className="input"
            value={current}
            required
            onChange={(event) => setCurrent(event.target.value)}
          />
        </Field>
        <Field label="New password" htmlFor="new-password">
          <input
            id="new-password"
            type="password"
            className="input"
            value={next}
            minLength={8}
            required
            onChange={(event) => setNext(event.target.value)}
          />
        </Field>
        <Field label="Confirm new password" htmlFor="confirm-password">
          <input
            id="confirm-password"
            type="password"
            className="input"
            value={confirm}
            minLength={8}
            required
            onChange={(event) => setConfirm(event.target.value)}
          />
        </Field>

        {error ? <Alert tone="danger">{error}</Alert> : null}
        {done ? <Alert tone="success">Password changed.</Alert> : null}

        <button type="submit" className="btn-primary btn-mono px-4 py-2" disabled={busy}>
          {busy ? "Updating…" : "Change password"}
        </button>
      </form>
    </Panel>
  );
}

/* ------------------------------------------------------------ danger zone */

function DangerZone({ user, onDeleted }: { user: User; onDeleted: () => Promise<void> }) {
  const [confirmation, setConfirmation] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const queryClient = useQueryClient();

  const armed = confirmation.trim() === "DELETE" || confirmation.trim().toLowerCase() === user.email.toLowerCase();

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!armed) return;
    setBusy(true);
    setError(null);
    try {
      await api<void>("/account", { method: "DELETE", body: { confirmation: confirmation.trim() } });
      setToken(null);
      queryClient.clear();
      router.replace("/");
      void onDeleted();
    } catch (deleteError) {
      setError(errorMessage(deleteError));
      setBusy(false);
    }
  }

  return (
    <Panel className="border-danger/30">
      <SectionTitle
        eyebrow="Danger zone"
        title="Delete account"
        hint="Permanent. Every attempt, project, ticket, skill, reward and post is removed."
      />

      <form onSubmit={submit} className="space-y-4">
        <Field
          label="Type DELETE or your email to confirm"
          htmlFor="delete-confirmation"
          hint={user.email}
        >
          <input
            id="delete-confirmation"
            className="input-mono"
            value={confirmation}
            autoComplete="off"
            onChange={(event) => setConfirmation(event.target.value)}
          />
        </Field>

        {error ? <Alert tone="danger">{error}</Alert> : null}

        <button type="submit" className="btn-danger btn-mono px-4 py-2" disabled={!armed || busy}>
          {busy ? "Deleting…" : "Delete my account"}
        </button>
      </form>
    </Panel>
  );
}

function Field({
  label,
  htmlFor,
  hint,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  children: ReactNode;
}) {
  return (
    <div>
      <div className="mb-1.5 flex items-baseline justify-between gap-3">
        <label htmlFor={htmlFor} className="label">
          {label}
        </label>
        {hint ? <span className="font-mono text-[10px] tabular-nums text-faint">{hint}</span> : null}
      </div>
      {children}
    </div>
  );
}
