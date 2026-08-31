"use client";

import { API_URL } from "@/lib/api";
import { cn } from "@/lib/utils";

const SIZES = {
  xs: "h-6 w-6 text-[9px]",
  sm: "h-7 w-7 text-[10px]",
  md: "h-9 w-9 text-[11px]",
  lg: "h-16 w-16 text-[18px]",
  xl: "h-24 w-24 text-[26px]",
} as const;

export type AvatarSize = keyof typeof SIZES;

/** Uploaded avatars are stored relative to the API, everything else is absolute. */
export function avatarSrc(src: string | null | undefined): string | null {
  if (!src) return null;
  return src.startsWith("/") ? `${API_URL}${src}` : src;
}

export function initials(name: string): string {
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return "?";
  const letters = parts.length === 1 ? parts[0].slice(0, 2) : `${parts[0][0]}${parts[parts.length - 1][0]}`;
  return letters.toUpperCase();
}

/**
 * Single avatar surface for the whole app. Falls back to accent-tinted initials
 * whenever there is no photo, so a missing image never renders as a broken box.
 */
export function Avatar({
  name,
  src,
  size = "sm",
  className,
}: {
  name: string;
  src?: string | null;
  size?: AvatarSize;
  className?: string;
}) {
  const resolved = avatarSrc(src);
  const base = cn(
    "flex flex-none items-center justify-center overflow-hidden rounded-sm border border-line",
    SIZES[size],
    className,
  );

  if (!resolved) {
    return (
      <span
        aria-hidden
        className={cn(base, "bg-accent/10 font-mono font-medium tracking-[0.06em] text-accent")}
      >
        {initials(name)}
      </span>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img src={resolved} alt="" className={cn(base, "bg-elevated object-cover")} />
  );
}
