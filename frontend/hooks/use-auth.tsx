"use client";

import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import {
  createContext,
  ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { api, ApiError, getToken, setToken } from "@/lib/api";
import type { AuthResponse, User } from "@/lib/types";

/** How long to wait for the session check before telling the user we cannot reach the API. */
const SESSION_TIMEOUT_MS = 5000;  // Reduced from 8s to 5s for faster feedback

type AuthContextValue = {
  user: User | null;
  status: "loading" | "authenticated" | "anonymous";
  /**
   * True when the session check could not reach the API. Distinct from
   * `anonymous`: the token may be perfectly valid and the server merely
   * unreachable, so signing the user out would be wrong. Surfaces as a
   * retryable message instead of an endless loading screen.
   */
  unreachable: boolean;
  register: (input: { name: string; email: string; password: string }) => Promise<User>;
  login: (input: { email: string; password: string }) => Promise<User>;
  logout: () => Promise<void>;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthContextValue["status"]>("loading");
  const [unreachable, setUnreachable] = useState(false);
  const router = useRouter();
  const queryClient = useQueryClient();

  const refresh = useCallback(async () => {
    if (!getToken()) {
      setUser(null);
      setUnreachable(false);
      setStatus("anonymous");
      return;
    }
    setUnreachable(false);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), SESSION_TIMEOUT_MS);
    try {
      const me = await api<User>("/auth/me", { signal: controller.signal });
      setUser(me);
      setStatus("authenticated");
    } catch (error) {
      // A 401 is a real answer: the token is dead, so drop it.
      if (error instanceof ApiError && error.status === 401) {
        setToken(null);
        setUser(null);
        setStatus("anonymous");
        return;
      }
      // Anything else means we never got an answer. Keep the token and say so,
      // rather than pretending the user is signed out or hanging forever.
      setUser(null);
      setUnreachable(true);
      setStatus("anonymous");
    } finally {
      clearTimeout(timer);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  const adopt = useCallback((response: AuthResponse) => {
    setToken(response.access_token);
    setUser(response.user);
    setUnreachable(false);
    setStatus("authenticated");
    return response.user;
  }, []);

  const register = useCallback(
    async (input: { name: string; email: string; password: string }) => {
      const response = await api<AuthResponse>("/auth/register", { method: "POST", body: input });
      return adopt(response);
    },
    [adopt],
  );

  const login = useCallback(
    async (input: { email: string; password: string }) => {
      const response = await api<AuthResponse>("/auth/login", { method: "POST", body: input });
      return adopt(response);
    },
    [adopt],
  );

  const logout = useCallback(async () => {
    try {
      await api<void>("/auth/logout", { method: "POST" });
    } catch {
      // Logging out locally must succeed even if the API is unreachable.
    }
    setToken(null);
    setUser(null);
    setUnreachable(false);
    setStatus("anonymous");
    queryClient.clear();
    router.push("/login");
  }, [queryClient, router]);

  const value = useMemo(
    () => ({ user, status, unreachable, register, login, logout, refresh }),
    [user, status, unreachable, register, login, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used inside AuthProvider");
  return context;
}
