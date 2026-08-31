import { cn } from "@/lib/utils";

/**
 * SprintForge mark — three forged blocks rising in isometric projection.
 *
 * Geometry is a true isometric projection (x,y,z) → (x−y)·cos30, (x+y)·sin30 − z,
 * so the three faces of every block share real vanishing edges rather than being
 * faked with skewed rectangles. Each block gets a lit top, a mid-tone right face
 * and a shaded left face, plus a contact shadow and a forge glow at the apex —
 * that shading, not the outline, is what gives the mark its depth.
 *
 * Face polygons were precomputed on a 48-unit grid; blocks are painted back to
 * front so adjacent faces occlude correctly and the staircase reads as one solid.
 */
function LogoMark({
  className,
  animated = false,
  /** Namespaces gradient ids when several marks share a document. */
  idPrefix = "sf",
}: {
  className?: string;
  animated?: boolean;
  idPrefix?: string;
}) {
  const id = (name: string) => `${idPrefix}-${name}`;

  return (
    <svg
      viewBox="0 0 48 48"
      className={cn("h-7 w-7 flex-none", className)}
      fill="none"
      aria-hidden
    >
      <defs>
        {/* Tile: brushed dark metal, lit from the upper left. */}
        <linearGradient id={id("tile")} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#22262d" />
          <stop offset="45%" stopColor="#14171c" />
          <stop offset="100%" stopColor="#0a0c0f" />
        </linearGradient>

        {/* Top faces: hottest surface, catching the light. */}
        <linearGradient id={id("top")} x1="0.1" y1="0" x2="0.9" y2="1">
          <stop offset="0%" stopColor="#eaffa4" />
          <stop offset="40%" stopColor="#d3fd63" />
          <stop offset="100%" stopColor="#b6ea3f" />
        </linearGradient>

        {/* Right faces: mid tone, falling away from the source. */}
        <linearGradient id={id("right")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#a9dc38" />
          <stop offset="100%" stopColor="#6f9622" />
        </linearGradient>

        {/* Left faces: deepest shade, keeps the silhouette readable. */}
        <linearGradient id={id("left")} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#6f9622" />
          <stop offset="100%" stopColor="#3f5614" />
        </linearGradient>

        {/* Forge glow at the apex. */}
        <radialGradient id={id("glow")} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="#f4ffcf" stopOpacity="0.95" />
          <stop offset="45%" stopColor="#d3fd63" stopOpacity="0.35" />
          <stop offset="100%" stopColor="#d3fd63" stopOpacity="0" />
        </radialGradient>

        {/* Contact shadow beneath the stack. */}
        <radialGradient id={id("shadow")} cx="0.5" cy="0.5" r="0.5">
          <stop offset="0%" stopColor="#000000" stopOpacity="0.55" />
          <stop offset="100%" stopColor="#000000" stopOpacity="0" />
        </radialGradient>

        {/* Specular streak across the tile. */}
        <linearGradient id={id("sheen")} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="#ffffff" stopOpacity="0.14" />
          <stop offset="38%" stopColor="#ffffff" stopOpacity="0.02" />
          <stop offset="100%" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* ------------------------------------------------------------- tile */}
      <rect x="1" y="1" width="46" height="46" rx="11" fill={`url(#${id("tile")})`} />
      <rect x="1" y="1" width="46" height="46" rx="11" fill={`url(#${id("sheen")})`} />
      {/* Bevel: bright top-left edge, dark bottom-right edge. */}
      <rect
        x="1.5"
        y="1.5"
        width="45"
        height="45"
        rx="10.5"
        stroke="#ffffff"
        strokeOpacity="0.1"
        strokeWidth="1"
      />
      <rect
        x="1"
        y="1"
        width="46"
        height="46"
        rx="11"
        stroke="#000000"
        strokeOpacity="0.5"
        strokeWidth="0.75"
      />

      {/* Stack scaled about the tile centre for optical padding */}
      <g transform="translate(24 24) scale(0.82) translate(-24 -24)">
        {/* Ground shadow */}
      <ellipse cx="24.5" cy="41.5" rx="15" ry="4" fill={`url(#${id("shadow")})`} />

      {/* --------------------------------------------- block 1 (back, short) */}
      <g>
        <polygon
          points="10.07,20.2 17,24.2 17,33 10.07,29"
          fill={`url(#${id("left")})`}
        />
        <polygon points="17,16.2 23.93,20.2 17,24.2 10.07,20.2" fill={`url(#${id("top")})`} />
      </g>

      {/* ------------------------------------------- block 2 (middle, taller) */}
      <g>
        <polygon points="17,15.4 23.93,19.4 23.93,37 17,33" fill={`url(#${id("left")})`} />
        <polygon
          points="30.86,15.4 23.93,19.4 23.93,37 30.86,33"
          fill={`url(#${id("right")})`}
        />
        <polygon
          points="23.93,11.4 30.86,15.4 23.93,19.4 17,15.4"
          fill={`url(#${id("top")})`}
        />
      </g>

      {/* --------------------------------------------- block 3 (front, tall) */}
      <g>
        <polygon
          points="23.93,10.6 30.86,14.6 30.86,41 23.93,37"
          fill={`url(#${id("left")})`}
        />
        <polygon
          points="37.79,10.6 30.86,14.6 30.86,41 37.79,37"
          fill={`url(#${id("right")})`}
        />
        <polygon
          points="30.86,6.6 37.79,10.6 30.86,14.6 23.93,10.6"
          fill={`url(#${id("top")})`}
        />
      </g>

      {/* Crisp highlight along the leading vertical edge of the tall block */}
      <path
        d="M30.86 14.6 L30.86 41"
        stroke="#eaffa4"
        strokeOpacity="0.4"
        strokeWidth="0.6"
      />

      {/* Forge glow at the apex */}
      <circle
        cx="30.86"
        cy="8.4"
        r="9"
        fill={`url(#${id("glow")})`}
        className={animated ? "animate-pulse" : undefined}
      />
        <circle cx="30.86" cy="7.6" r="1.15" fill="#f7ffe0" />
      </g>
    </svg>
  );
}

/** Full lockup: mark plus wordmark. */
export function Logo({
  compact = false,
  className,
  animated = false,
}: {
  compact?: boolean;
  className?: string;
  animated?: boolean;
}) {
  return (
    <span className={cn("flex items-center gap-2.5", className)}>
      <LogoMark animated={animated} />
      {compact ? null : (
        <span className="font-mono text-[12px] font-medium tracking-[0.06em] text-ink">
          SPRINTFORGE<span className="text-accent">.AI</span>
        </span>
      )}
    </span>
  );
}
