"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { Logo } from "@/components/app-shell";
import { EngineLoop } from "@/components/landing/engine-loop";
import { Alert, Loader } from "@/components/ui/primitives";
import { useAuth } from "@/hooks/use-auth";
import { errorMessage } from "@/lib/utils";

export function AuthForm({ mode }: { mode: "login" | "register" }) {
  const { login, register, status, user } = useAuth();
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (status === "authenticated" && user) {
      router.replace(user.is_onboarded ? "/dashboard" : "/onboarding");
    }
  }, [status, user, router]);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const account =
        mode === "register"
          ? await register({ name, email, password })
          : await login({ email, password });
      router.replace(account.is_onboarded ? "/dashboard" : "/onboarding");
    } catch (submitError) {
      setError(errorMessage(submitError));
    } finally {
      setBusy(false);
    }
  }

  const isRegister = mode === "register";

  return (
    <div className="grid min-h-screen lg:grid-cols-[1fr_1.05fr]">
      {/* ------------------------------------------------------------- form */}
      <div className="flex flex-col justify-center px-6 py-14 sm:px-12 lg:px-16">
        <div className="mx-auto w-full max-w-[380px]">
          <Link href="/" className="inline-block">
            <Logo />
          </Link>

          <p className="label mt-14">
            {isRegister ? "New account" : "Returning learner"}
          </p>
          <h1 className="display mt-3 text-display-sm text-ink">
            {isRegister ? "Claim, then prove." : "Welcome back."}
          </h1>
          <p className="mt-3 max-w-[36ch] text-[12.5px] leading-relaxed text-muted">
            {isRegister
              ? "You will state what you know next — the engine takes it from there and verifies every claim."
              : "Your Digital Twin kept its state. Pick up exactly where the engine left you."}
          </p>

          <form onSubmit={handleSubmit} className="mt-10 space-y-5">
            {isRegister ? (
              <Field
                id="name"
                label="Full name"
                value={name}
                onChange={setName}
                placeholder="Ada Lovelace"
                required
              />
            ) : null}

            <Field
              id="email"
              label="Email"
              type="email"
              value={email}
              onChange={setEmail}
              placeholder="you@example.com"
              required
            />

            <Field
              id="password"
              label="Password"
              type="password"
              value={password}
              onChange={setPassword}
              placeholder={isRegister ? "At least 8 characters" : "••••••••"}
              required
              minLength={isRegister ? 8 : 1}
              hint={isRegister ? "Minimum 8 characters." : undefined}
            />

            {error ? (
              <Alert tone="danger" title="Could not continue">
                {error}
              </Alert>
            ) : null}

            <button type="submit" className="btn-primary btn-mono w-full py-3" disabled={busy}>
              {busy ? (
                <Loader label={isRegister ? "Creating account" : "Signing in"} />
              ) : (
                <>
                  {isRegister ? "Create account" : "Sign in"}
                  <span aria-hidden>→</span>
                </>
              )}
            </button>
          </form>

          <p className="mt-8 font-mono text-[11px] text-faint">
            {isRegister ? "Already have an account? " : "New to SprintForge? "}
            <Link
              href={isRegister ? "/login" : "/register"}
              className="text-accent transition-opacity hover:opacity-75"
            >
              {isRegister ? "Sign in" : "Create one"}
            </Link>
          </p>
        </div>
      </div>

      {/* --------------------------------------------------------- showcase */}
      <div className="noise relative hidden overflow-hidden border-l border-line bg-surface/40 lg:block">
        <div className="grid-bg absolute inset-0 opacity-70" aria-hidden />
        <div className="relative flex h-full flex-col justify-center px-14">
          <p className="label">The loop you are joining</p>
          <div className="mt-8 max-w-[380px]">
            <EngineLoop />
          </div>
          <p className="mt-10 max-w-[40ch] text-[12.5px] leading-relaxed text-muted">
            Every score in SprintForge traces back to code that ran or a question you answered.
            Nothing is granted, and nothing is assumed.
          </p>
        </div>
      </div>
    </div>
  );
}

function Field({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = "text",
  required,
  minLength,
  hint,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
  required?: boolean;
  minLength?: number;
  hint?: string;
}) {
  return (
    <div>
      <div className="mb-2 flex items-baseline justify-between">
        <label htmlFor={id} className="label">
          {label}
        </label>
        {hint ? <span className="font-mono text-[9.5px] text-faint">{hint}</span> : null}
      </div>
      <input
        id={id}
        name={id}
        type={type}
        className="input"
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        required={required}
        minLength={minLength}
      />
    </div>
  );
}
