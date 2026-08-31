"use client";

import { useEffect, useRef } from "react";

import { cn } from "@/lib/utils";

type Node = {
  x: number;
  y: number;
  z: number;
  /** Skill tier, drives which nodes are drawn as "verified". */
  tier: number;
  seed: number;
};

type Edge = [number, number];

const ACCENT: [number, number, number] = [200, 250, 75];
const COOL: [number, number, number] = [188, 202, 220];

/**
 * A camera framing. The scene is never cut between these — it eases through
 * them continuously, because a hard cut behind a headline reads as a glitch
 * rather than as film.
 */
type Shot = {
  /** Distance of the eye from the lattice centre. Lower = pushed in. */
  dolly: number;
  /** Pitch, radians. */
  tilt: number;
  /** Yaw speed multiplier. */
  drift: number;
  /** Depth the lens is focused on; everything else defocuses. */
  focus: number;
  /** Roll, radians. A degree or two is enough to feel handheld. */
  roll: number;
};

const SHOTS: Shot[] = [
  { dolly: 820, tilt: 0.36, drift: 1.0, focus: -30, roll: 0.0 },
  { dolly: 430, tilt: 0.12, drift: 0.45, focus: -240, roll: 0.03 },
  { dolly: 740, tilt: 0.52, drift: 1.5, focus: 140, roll: -0.024 },
  { dolly: 520, tilt: 0.22, drift: 0.7, focus: -90, roll: 0.012 },
];

/** Seconds the camera spends easing from one framing to the next. */
const SHOT_SECONDS = 9;

/** Horizontal centre of the composition, as a fraction of canvas width. */
const SCENE_X = 0.66;

/** Defocus discs are drawn from pre-rendered sprites, one per bucket. */
const BLUR_BUCKETS = 7;
const SPRITE_SIZE = 96;

const smoothstep = (t: number) => t * t * (3 - 2 * t);

/**
 * Builds a soft radial sprite. Drawing ~120 defocused nodes per frame as live
 * `createRadialGradient` calls costs more than the rest of the loop combined;
 * scaling a handful of cached sprites is effectively free.
 *
 * `softness` 0 is a hard point, 1 is a wide bokeh disc with a bright rim — real
 * lenses brighten at the edge of an out-of-focus highlight, and that rim is the
 * single detail that makes this read as glass rather than as a blurred circle.
 */
function makeSprite(rgb: [number, number, number], softness: number): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = SPRITE_SIZE;
  canvas.height = SPRITE_SIZE;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  const mid = SPRITE_SIZE / 2;
  const gradient = ctx.createRadialGradient(mid, mid, 0, mid, mid, mid);
  const [r, g, b] = rgb;

  if (softness < 0.08) {
    gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 1)`);
    gradient.addColorStop(0.42, `rgba(${r}, ${g}, ${b}, 0.92)`);
    gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
  } else {
    const core = 0.34 + softness * 0.4;
    gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${0.5 - softness * 0.3})`);
    gradient.addColorStop(core * 0.86, `rgba(${r}, ${g}, ${b}, ${0.42 - softness * 0.24})`);
    // The rim.
    gradient.addColorStop(core, `rgba(${r}, ${g}, ${b}, ${0.6 - softness * 0.3})`);
    gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0)`);
  }

  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, SPRITE_SIZE, SPRITE_SIZE);
  return canvas;
}

/** A tiling grain plate, sampled at a random offset each frame. */
function makeGrain(size: number): HTMLCanvasElement {
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const ctx = canvas.getContext("2d");
  if (!ctx) return canvas;

  const image = ctx.createImageData(size, size);
  for (let i = 0; i < image.data.length; i += 4) {
    const value = 128 + (Math.random() - 0.5) * 255;
    image.data[i] = value;
    image.data[i + 1] = value;
    image.data[i + 2] = value;
    image.data[i + 3] = 255;
  }
  ctx.putImageData(image, 0, 0);
  return canvas;
}

/**
 * Cinematic 3D dependency lattice.
 *
 * A real perspective projection rather than a decorative particle field: nodes
 * are laid out on tiered shells (foundation skills at the core, advanced skills
 * further out), edges only connect adjacent tiers, and an outward pulse lights
 * tiers up as though the engine were re-verifying them.
 *
 * The presentation is deliberately photographic. A virtual camera eases through
 * a loop of framings, a focal plane travels with it so most of the lattice sits
 * in defocus, accent nodes bloom additively and throw anamorphic streaks, and
 * the whole frame is finished with vignette and grain. Nothing here is a video
 * file — shipping one would cost megabytes and could not respond to the pointer.
 *
 * Rendering is skipped entirely for reduced-motion users and paused when the
 * canvas is off-screen or the tab is hidden.
 */
export function KnowledgeField({ className }: { className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    /* ----------------------------------------------------------- geometry */
    const TIERS = [
      { count: 6, radius: 44 },
      { count: 12, radius: 100 },
      { count: 18, radius: 164 },
      { count: 22, radius: 230 },
      { count: 26, radius: 300 },
      { count: 28, radius: 372 },
    ];

    const nodes: Node[] = [];
    const tierRanges: Array<[number, number]> = [];

    TIERS.forEach((tier, tierIndex) => {
      const start = nodes.length;
      for (let i = 0; i < tier.count; i += 1) {
        // Fibonacci-ish distribution keeps shells from banding visibly.
        const phi = Math.acos(1 - (2 * (i + 0.5)) / tier.count);
        const theta = Math.PI * (1 + Math.sqrt(5)) * i;
        const jitter = 0.86 + ((i * 37) % 100) / 360;
        const radius = tier.radius * jitter;
        nodes.push({
          x: radius * Math.sin(phi) * Math.cos(theta),
          y: radius * Math.cos(phi) * 0.66,
          z: radius * Math.sin(phi) * Math.sin(theta),
          tier: tierIndex,
          seed: (i * 97) % 360,
        });
      }
      tierRanges.push([start, nodes.length]);
    });

    // Edges run inward only: every node depends on the nearest two nodes of the
    // tier beneath it, which is what makes the lattice read as a dependency graph.
    const edges: Edge[] = [];
    for (let tierIndex = 1; tierIndex < tierRanges.length; tierIndex += 1) {
      const [start, end] = tierRanges[tierIndex];
      const [innerStart, innerEnd] = tierRanges[tierIndex - 1];
      for (let i = start; i < end; i += 1) {
        const ranked: Array<{ index: number; distance: number }> = [];
        for (let j = innerStart; j < innerEnd; j += 1) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const dz = nodes[i].z - nodes[j].z;
          ranked.push({ index: j, distance: dx * dx + dy * dy + dz * dz });
        }
        ranked.sort((a, b) => a.distance - b.distance);
        edges.push([i, ranked[0].index]);
        if (ranked[1]) edges.push([i, ranked[1].index]);
      }
    }

    /* ------------------------------------------------------------- sprites */
    const accentSprites: HTMLCanvasElement[] = [];
    const coolSprites: HTMLCanvasElement[] = [];
    for (let i = 0; i < BLUR_BUCKETS; i += 1) {
      const softness = i / (BLUR_BUCKETS - 1);
      accentSprites.push(makeSprite(ACCENT, softness));
      coolSprites.push(makeSprite(COOL, softness));
    }
    // A 512 plate rather than 128: on a wide display the smaller tile cost ~170
    // drawImage calls per frame purely for grain, which was the single most
    // expensive thing in the loop.
    const GRAIN_TILE = 512;
    const grain = makeGrain(GRAIN_TILE);

    /* -------------------------------------------------------------- camera */
    let width = 0;
    let height = 0;
    let dpr = 1;
    /** Scales the 900px design space up to whatever canvas we were handed. */
    let fit = 1;

    const DESIGN = 900;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      // Driven by the smaller axis so a short, very wide hero does not blow the
      // lattice up until only its centre is on screen.
      fit = Math.max(0.8, Math.min(2.6, Math.min(width * 0.78, height * 1.25) / DESIGN));
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const pointer = { x: 0, y: 0 };
    const camera = { x: 0, y: 0 };
    let scroll = 0;

    const onPointerMove = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
      pointer.y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    };

    const onScroll = () => {
      // Only the first viewport matters; the hero has scrolled away past that.
      scroll = Math.min(1, window.scrollY / Math.max(1, window.innerHeight));
    };
    onScroll();

    /* ------------------------------------------------------------ pipeline */
    let spin = 0;
    let frame = 0;
    let visible = true;
    let running = false;
    let last = 0;

    const project = (
      node: Node,
      sin: number,
      cos: number,
      tilt: number,
      dolly: number,
      roll: number,
    ) => {
      // Yaw about Y, then a gentle pitch from the eased camera.
      const x0 = node.x * cos - node.z * sin;
      const z0 = node.x * sin + node.z * cos;
      const y0 = node.y * Math.cos(tilt) - z0 * Math.sin(tilt) * 0.35;
      const depth = z0 * Math.cos(tilt) + node.y * Math.sin(tilt) * 0.35;

      // Roll is applied in screen space, after the projection plane.
      const cr = Math.cos(roll);
      const sr = Math.sin(roll);
      const x = x0 * cr - y0 * sr;
      const y = x0 * sr + y0 * cr;

      // The lattice is authored in a fixed ~900px design space. Without this it
      // occupies a quarter of a wide display and reads as a small ornament
      // rather than as the plate the section is built on.
      const perspective = (dolly / (dolly + depth)) * fit;
      return {
        // Composed right of centre, matching the mask that keeps the plate off
        // the headline. Centring it would hide half the lattice behind type.
        sx: width * SCENE_X + x * perspective + camera.x * 26,
        sy: height / 2 + y * perspective + camera.y * 18,
        scale: perspective,
        depth,
      };
    };

    const render = (time: number) => {
      if (!visible) {
        running = false;
        return;
      }

      const delta = last ? Math.min(64, time - last) : 16;
      last = time;

      camera.x += (pointer.x - camera.x) * 0.045;
      camera.y += (pointer.y - camera.y) * 0.045;

      /* ------------------------------------------------------ shot easing */
      const cursor = (time / 1000 / SHOT_SECONDS) % SHOTS.length;
      const index = Math.floor(cursor);
      const from = SHOTS[index];
      const to = SHOTS[(index + 1) % SHOTS.length];
      const blend = smoothstep(cursor - index);
      const mix = (a: number, b: number) => a + (b - a) * blend;

      // Scrolling pushes the camera back and drops focus, so the lattice
      // recedes as the reader leaves the hero rather than fighting the next
      // section for attention.
      const dolly = mix(from.dolly, to.dolly) + scroll * 420;
      const tilt = mix(from.tilt, to.tilt) + camera.y * 0.16;
      const focus = mix(from.focus, to.focus);
      const roll = mix(from.roll, to.roll) + camera.x * 0.012;
      const exposure = Math.max(0, 1 - scroll * 1.25);

      if (exposure <= 0.01) {
        ctx.clearRect(0, 0, width, height);
        frame = requestAnimationFrame(render);
        return;
      }

      spin += 0.00016 * delta * mix(from.drift, to.drift);
      const sin = Math.sin(spin);
      const cos = Math.cos(spin);

      ctx.clearRect(0, 0, width, height);

      const points = nodes.map((node) => project(node, sin, cos, tilt, dolly, roll));

      /* ------------------------------------------------------------ edges */
      // Painted back to front so nearer connections sit over farther ones.
      const order = points
        .map((_, i) => i)
        .sort((a, b) => points[b].depth - points[a].depth);

      ctx.lineWidth = 1;
      for (const [a, b] of edges) {
        const pa = points[a];
        const pb = points[b];
        const nearness = 1 - (pa.depth + 320) / 760;
        const defocus = Math.min(1, Math.abs(pa.depth - focus) / 300);
        const alpha = Math.max(0, Math.min(0.72, nearness * 0.66)) * (1 - defocus * 0.62);
        if (alpha <= 0.012) continue;
        ctx.strokeStyle = `rgba(150, 166, 186, ${alpha * 0.82 * exposure})`;
        ctx.beginPath();
        ctx.moveTo(pa.sx, pa.sy);
        ctx.lineTo(pb.sx, pb.sy);
        ctx.stroke();
      }

      /* ------------------------------------------------------------ nodes */
      // Outward verification sweep, one tier at a time.
      const sweep = (time / 1150) % (TIERS.length + 1.2);

      ctx.globalCompositeOperation = "lighter";

      for (const i of order) {
        const point = points[i];
        const node = nodes[i];
        const nearness = 1 - (point.depth + 320) / 760;
        if (nearness <= 0) continue;

        const proximity = Math.max(0, 1 - Math.abs(sweep - node.tier) / 1.6);
        const verified = proximity > 0.02;

        // Circle of confusion: how far this node sits from the focal plane.
        const defocus = Math.min(1, Math.abs(point.depth - focus) / 300);
        const bucket = Math.min(BLUR_BUCKETS - 1, Math.round(defocus * (BLUR_BUCKETS - 1)));
        const sprite = verified ? accentSprites[bucket] : coolSprites[bucket];

        const base = (1.5 + node.tier * 0.2) * point.scale;
        const size = base * (2.4 + defocus * 13) * (1 + proximity * 0.7);
        const alpha =
          (verified ? Math.min(1, proximity * nearness * 1.9) : Math.min(0.72, nearness * 0.66)) *
          (1 - defocus * 0.34) *
          exposure;

        if (alpha <= 0.012) continue;

        ctx.globalAlpha = alpha;
        ctx.drawImage(sprite as CanvasImageSource, point.sx - size / 2, point.sy - size / 2, size, size);

        if (verified && defocus < 0.5) {
          // Anamorphic streak. Only in-focus highlights throw one, which is
          // what keeps it from turning into a smear of horizontal lines.
          const reach = size * (5 + proximity * 5);
          const streak = ctx.createLinearGradient(point.sx - reach, 0, point.sx + reach, 0);
          const tint = `rgba(${ACCENT[0]}, ${ACCENT[1]}, ${ACCENT[2]}`;
          streak.addColorStop(0, `${tint}, 0)`);
          streak.addColorStop(0.5, `${tint}, ${0.2 * proximity * (1 - defocus * 2)})`);
          streak.addColorStop(1, `${tint}, 0)`);
          ctx.globalAlpha = alpha * 0.85;
          ctx.fillStyle = streak;
          ctx.fillRect(point.sx - reach, point.sy - size * 0.06 - 0.5, reach * 2, size * 0.12 + 1);
        }
      }

      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";

      /* ----------------------------------------------------------- finish */
      // Vignette. Drawn after the scene so it darkens the bloom too.
      const vignette = ctx.createRadialGradient(
        width * SCENE_X,
        height * 0.5,
        Math.min(width, height) * 0.16,
        width * SCENE_X,
        height * 0.5,
        Math.max(width, height) * 0.74,
      );
      vignette.addColorStop(0, "rgba(0, 0, 0, 0)");
      vignette.addColorStop(1, `rgba(0, 0, 0, ${0.42 * exposure})`);
      ctx.fillStyle = vignette;
      ctx.fillRect(0, 0, width, height);

      // Grain, sampled at a random offset so it crawls like film rather than
      // sitting still like a texture.
      ctx.globalAlpha = 0.028 * exposure;
      ctx.globalCompositeOperation = "overlay";
      const ox = Math.random() * GRAIN_TILE;
      const oy = Math.random() * GRAIN_TILE;
      for (let x = -ox; x < width; x += GRAIN_TILE) {
        for (let y = -oy; y < height; y += GRAIN_TILE) {
          ctx.drawImage(grain as CanvasImageSource, x, y);
        }
      }
      ctx.globalAlpha = 1;
      ctx.globalCompositeOperation = "source-over";

      frame = requestAnimationFrame(render);
    };

    const start = () => {
      if (running || reduced) return;
      running = true;
      last = 0;
      frame = requestAnimationFrame(render);
    };

    /* -------------------------------------------------------- lifecycle */
    if (reduced) {
      // Static single frame so the composition still exists without motion.
      const sin = Math.sin(0.6);
      const cos = Math.cos(0.6);
      ctx.clearRect(0, 0, width, height);
      const points = nodes.map((node) => project(node, sin, cos, 0.34, 700, 0));
      for (const [a, b] of edges) {
        ctx.strokeStyle = "rgba(120, 132, 148, 0.16)";
        ctx.beginPath();
        ctx.moveTo(points[a].sx, points[a].sy);
        ctx.lineTo(points[b].sx, points[b].sy);
        ctx.stroke();
      }
      points.forEach((point) => {
        ctx.fillStyle = "rgba(196, 206, 220, 0.3)";
        ctx.beginPath();
        ctx.arc(point.sx, point.sy, 1.4 * point.scale, 0, Math.PI * 2);
        ctx.fill();
      });
      return;
    }

    const observer = new IntersectionObserver(
      (entries) => {
        visible = entries.some((entry) => entry.isIntersecting);
        if (visible) start();
      },
      { threshold: 0 },
    );
    observer.observe(canvas);

    const onVisibility = () => {
      visible = !document.hidden;
      if (visible) start();
    };

    window.addEventListener("resize", resize);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("scroll", onScroll, { passive: true });
    document.addEventListener("visibilitychange", onVisibility);
    start();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("scroll", onScroll);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className={cn("pointer-events-none h-full w-full", className)}
      aria-hidden
    />
  );
}
