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

const ACCENT = "200, 250, 75";

/**
 * Rotating 3D dependency lattice.
 *
 * A real perspective projection rather than a decorative particle field: nodes
 * are laid out on tiered shells (foundation skills at the core, advanced skills
 * further out), edges only connect adjacent tiers, and depth drives size, alpha
 * and blur. Pointer position eases the camera so the whole structure feels
 * physical without any dependency on a 3D library.
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
      { count: 24, radius: 300 },
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

    /* -------------------------------------------------------------- camera */
    let width = 0;
    let height = 0;
    let dpr = 1;

    const resize = () => {
      const rect = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      width = rect.width;
      height = rect.height;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();

    const pointer = { x: 0, y: 0 };
    const camera = { x: 0, y: 0 };

    const onPointerMove = (event: PointerEvent) => {
      const rect = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width - 0.5) * 2;
      pointer.y = ((event.clientY - rect.top) / rect.height - 0.5) * 2;
    };

    /* ------------------------------------------------------------ pipeline */
    // The "verify" sweep: a pulse index that walks outward through the tiers so
    // nodes light up as though the engine were re-verifying them.
    let spin = 0;
    let frame = 0;
    let visible = true;
    let running = false;

    const project = (node: Node, sin: number, cos: number, tilt: number) => {
      // Yaw about Y, then a gentle pitch from the eased camera.
      const x = node.x * cos - node.z * sin;
      const z = node.x * sin + node.z * cos;
      const y = node.y * Math.cos(tilt) - z * Math.sin(tilt) * 0.35;
      const depth = z * Math.cos(tilt) + node.y * Math.sin(tilt) * 0.35;

      const perspective = 620 / (620 + depth);
      return {
        sx: width / 2 + x * perspective + camera.x * 26,
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

      camera.x += (pointer.x - camera.x) * 0.045;
      camera.y += (pointer.y - camera.y) * 0.045;

      spin += 0.0016;
      const sin = Math.sin(spin);
      const cos = Math.cos(spin);
      const tilt = 0.34 + camera.y * 0.16;

      ctx.clearRect(0, 0, width, height);

      const points = nodes.map((node) => project(node, sin, cos, tilt));

      // Edges first, so nodes always sit on top of their connections.
      ctx.lineWidth = 1;
      for (const [a, b] of edges) {
        const pa = points[a];
        const pb = points[b];
        const nearness = 1 - (pa.depth + 260) / 620;
        const alpha = Math.max(0, Math.min(0.6, nearness * 0.52));
        if (alpha <= 0.01) continue;
        ctx.strokeStyle = `rgba(132, 145, 162, ${alpha * 0.72})`;
        ctx.beginPath();
        ctx.moveTo(pa.sx, pa.sy);
        ctx.lineTo(pb.sx, pb.sy);
        ctx.stroke();
      }

      // Outward verification sweep, one tier at a time.
      const sweep = (time / 1150) % (TIERS.length + 1.2);

      points.forEach((point, index) => {
        const node = nodes[index];
        const nearness = 1 - (point.depth + 260) / 620;
        if (nearness <= 0) return;

        const proximity = Math.max(0, 1 - Math.abs(sweep - node.tier) / 1.05);
        const radius = (1.1 + node.tier * 0.16) * point.scale * (1 + proximity * 0.9);

        if (proximity > 0.02) {
          // Verified node: accent core plus a soft halo.
          ctx.fillStyle = `rgba(${ACCENT}, ${Math.min(0.95, proximity * nearness * 1.5)})`;
          ctx.beginPath();
          ctx.arc(point.sx, point.sy, radius, 0, Math.PI * 2);
          ctx.fill();

          ctx.fillStyle = `rgba(${ACCENT}, ${proximity * nearness * 0.1})`;
          ctx.beginPath();
          ctx.arc(point.sx, point.sy, radius * 4.5, 0, Math.PI * 2);
          ctx.fill();
        } else {
          ctx.fillStyle = `rgba(202, 212, 226, ${Math.min(0.62, nearness * 0.55)})`;
          ctx.beginPath();
          ctx.arc(point.sx, point.sy, radius, 0, Math.PI * 2);
          ctx.fill();
        }
      });

      frame = requestAnimationFrame(render);
    };

    const start = () => {
      if (running || reduced) return;
      running = true;
      frame = requestAnimationFrame(render);
    };

    /* -------------------------------------------------------- lifecycle */
    if (reduced) {
      // Static single frame so the composition still exists without motion.
      const sin = Math.sin(0.6);
      const cos = Math.cos(0.6);
      ctx.clearRect(0, 0, width, height);
      const points = nodes.map((node) => project(node, sin, cos, 0.34));
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
    document.addEventListener("visibilitychange", onVisibility);
    start();

    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("resize", resize);
      window.removeEventListener("pointermove", onPointerMove);
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
