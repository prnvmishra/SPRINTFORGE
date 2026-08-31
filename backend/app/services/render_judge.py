"""Layer 1b: grading HTML/CSS by *rendering* the page in a real browser.

The textual checks in `validation_service` can only prove that a declaration
exists on a selector that looks plausible. They cannot prove that the selector
matches anything, that the value is legal, or that the layout the requirement
describes actually happened. This module closes that gap: it assembles the
learner's bundle into one document, loads it in headless Chromium (Playwright),
and reports facts the browser computed — resolved styles, box geometry,
visibility, colours after `var()` substitution, and real track/row counts.

Design rules, both of which matter equally:

* A fake must not pass. Every verdict comes from the rendered page, and when
  the browser cannot run the check *fails* (or is explicitly marked skipped in
  a test environment) rather than passing by default.
* A correct solution must not be rejected. Assertions are written against
  outcomes with tolerances and ranges — "the children are laid out in a row",
  not "`display` is exactly `flex`" — so any legitimate technique passes.

Threading: Playwright's sync API refuses to run inside a live asyncio loop, and
grading is called from `async def` request handlers. So the browser lives in one
long-lived worker thread (`_Browser`) and callers hand it jobs and block on a
future. One browser process is reused for the whole server lifetime; each job
gets a fresh, isolated context and page, and every job is bounded by a hard
timeout so a pathological page cannot hang a submission.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import posixpath
import queue
import re
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from app.services import spec_interpolation

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------
# Check types owned by this module
# --------------------------------------------------------------------------

RENDER_CHECK_TYPES = {
    "render_computed_style",
    "render_grid_columns",
    "render_row_layout",
    "render_centered",
    "render_visible",
    "render_color",
    "render_box",
    "render_on_top",
}

#: Wall-clock ceiling for one rendered job (assemble → load → probe), including
#: a cold browser launch. Grading happens inside a request, so this is the
#: promise that a submission always gets an answer.
JOB_TIMEOUT_SECONDS = float(os.environ.get("SPRINTFORGE_RENDER_TIMEOUT", "20"))
#: Per-page navigation budget. Well inside `JOB_TIMEOUT_SECONDS` so a slow page
#: is reported as a graded failure rather than as a dead worker.
PAGE_TIMEOUT_MS = 6000
BROWSER_LAUNCH_TIMEOUT_MS = 25000

DEFAULT_VIEWPORT = {"width": 1280, "height": 900}
DEFAULT_ENTRY = "index.html"


@dataclass
class RenderVerdict:
    """One rendered check's outcome, in the shape `run_static_checks` needs."""

    passed: bool
    detail: str
    hint: Optional[str] = None
    #: True only when the judge deliberately declined to run (test environments).
    #: Never true in the default configuration, so a real submission can never
    #: be credited for a check that did not execute.
    skipped: bool = False
    #: True when the check itself is broken — an unresolved template placeholder
    #: in its selector, say. The learner's work was never examined, so this is
    #: reported as a validator configuration error and never as their failure.
    config_error: bool = False


# --------------------------------------------------------------------------
# Page assembly
# --------------------------------------------------------------------------

_LINK_TAG = re.compile(r"<link\b[^>]*>", re.IGNORECASE)
_SCRIPT_TAG = re.compile(r"<script\b[^>]*\bsrc\s*=[^>]*>\s*</script\s*>", re.IGNORECASE)
_HREF = re.compile(r"\bhref\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)
_SRC = re.compile(r"\bsrc\s*=\s*[\"']([^\"']+)[\"']", re.IGNORECASE)


def _local_asset(reference: str, files: dict[str, str]) -> Optional[str]:
    """Resolve a tag's href/src to a file in the bundle, ignoring remote URLs."""
    if not reference or "//" in reference:
        return None
    name = posixpath.basename(reference.split("?", 1)[0].split("#", 1)[0])
    return name if name in files else None


def assemble_page(files: dict[str, str], entry: Optional[str]) -> Optional[str]:
    """Inline the bundle's own CSS/JS into a single renderable document.

    Tag spelling is matched loosely on purpose: learner-authored markup varies
    (`<link ...>` vs `<link ... />`, attributes in any order), and an unmatched
    tag would silently render the page unstyled or inert — which would fail a
    correct solution. Remote URLs are left as they are.
    """
    if not entry or entry not in files:
        return None
    html = files[entry]

    def inline_link(match: re.Match[str]) -> str:
        tag = match.group(0)
        href = _HREF.search(tag)
        name = _local_asset(href.group(1), files) if href else None
        if not name or not name.lower().endswith(".css"):
            return tag
        return f"<style>\n{files.get(name, '')}\n</style>"

    def inline_script(match: re.Match[str]) -> str:
        tag = match.group(0)
        src = _SRC.search(tag)
        name = _local_asset(src.group(1), files) if src else None
        if not name or not name.lower().endswith(".js"):
            return tag
        return f"<script>\n{files.get(name, '')}\n</script>"

    html = _LINK_TAG.sub(inline_link, html)
    html = _SCRIPT_TAG.sub(inline_script, html)
    return html


def _guess_entry(files: dict[str, str]) -> Optional[str]:
    if DEFAULT_ENTRY in files:
        return DEFAULT_ENTRY
    for name in files:
        if name.lower().endswith((".html", ".htm")):
            return name
    return None


# --------------------------------------------------------------------------
# The in-page probe
#
# One `evaluate` per job gathers every fact the batched checks need. The browser
# only ever reports observations; all pass/fail judgement stays in Python so the
# failure messages can say what was observed versus what was required.
# --------------------------------------------------------------------------

PROBE_JS = r"""
(specs) => {
  const round = (n) => Math.round(n * 100) / 100;

  const splitTracks = (value) => {
    if (!value || value === 'none') return [];
    const out = [];
    let depth = 0;
    let current = '';
    for (const ch of value) {
      if (ch === '(' || ch === '[') depth++;
      else if (ch === ')' || ch === ']') depth--;
      if (/\s/.test(ch) && depth === 0) {
        if (current) out.push(current);
        current = '';
      } else {
        current += ch;
      }
    }
    if (current) out.push(current);
    // Named grid lines appear in the computed track list in some engines.
    return out.filter((t) => !t.startsWith('['));
  };

  const rectOf = (el) => {
    const r = el.getBoundingClientRect();
    return {
      left: round(r.left), right: round(r.right), top: round(r.top),
      bottom: round(r.bottom), width: round(r.width), height: round(r.height),
    };
  };

  const isVisible = (el) => {
    const cs = getComputedStyle(el);
    if (cs.display === 'none' || cs.visibility === 'hidden' || cs.visibility === 'collapse') {
      return { visible: false, reason: 'computed ' + (cs.display === 'none' ? 'display: none' : 'visibility: ' + cs.visibility) };
    }
    const opacity = parseFloat(cs.opacity);
    if (!isNaN(opacity) && opacity <= 0.05) {
      return { visible: false, reason: 'computed opacity: ' + cs.opacity };
    }
    const r = el.getBoundingClientRect();
    if (r.width < 1 || r.height < 1) {
      return { visible: false, reason: 'rendered box is ' + round(r.width) + 'x' + round(r.height) + 'px' };
    }
    if (cs.clipPath === 'inset(100%)' || (cs.clip && cs.clip.replace(/\s/g, '') === 'rect(0px,0px,0px,0px)')) {
      return { visible: false, reason: 'clipped away by ' + (cs.clipPath !== 'none' ? 'clip-path' : 'clip') };
    }
    // Pushed entirely outside the document (the classic off-screen hide).
    if (r.right <= 0 || r.bottom <= 0 || r.left >= document.documentElement.scrollWidth) {
      return { visible: false, reason: 'positioned outside the page at x=' + round(r.left) + ', y=' + round(r.top) };
    }
    return { visible: true, reason: null };
  };

  const describe = (el) => {
    let out = el.tagName.toLowerCase();
    if (el.id) out += '#' + el.id;
    if (el.classList.length) out += '.' + Array.from(el.classList).join('.');
    return out;
  };

  const parseColor = (value) => {
    const m = String(value).match(/-?[\d.]+/g);
    if (!m || m.length < 3) return null;
    const [r, g, b] = m.slice(0, 3).map(Number);
    const alpha = m.length > 3 ? Number(m[3]) : 1;
    const lin = (c) => {
      const s = c / 255;
      return s <= 0.03928 ? s / 12.92 : Math.pow((s + 0.055) / 1.055, 2.4);
    };
    const luminance = 0.2126 * lin(r) + 0.7152 * lin(g) + 0.0722 * lin(b);
    return {
      text: String(value),
      rgb: [r, g, b],
      alpha,
      luminance: Math.round(luminance * 10000) / 10000,
    };
  };

  const contentBox = (el) => {
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    const px = (v) => parseFloat(v) || 0;
    return {
      left: round(r.left + px(cs.paddingLeft) + px(cs.borderLeftWidth)),
      right: round(r.right - px(cs.paddingRight) - px(cs.borderRightWidth)),
      top: round(r.top + px(cs.paddingTop) + px(cs.borderTopWidth)),
      bottom: round(r.bottom - px(cs.paddingBottom) - px(cs.borderBottomWidth)),
    };
  };

  return specs.map((spec) => {
    let nodes;
    try {
      nodes = Array.from(document.querySelectorAll(spec.selector));
    } catch (e) {
      return { error: 'invalid selector: ' + String(e.message || e) };
    }
    const out = { count: nodes.length, kind: spec.kind };
    if (!nodes.length) return out;

    if (spec.kind === 'computed_style') {
      out.values = nodes.map((el) => {
        const cs = getComputedStyle(el);
        return {
          who: describe(el),
          value: String(cs.getPropertyValue(spec.property)).trim(),
          visible: isVisible(el).visible,
        };
      });
      return out;
    }

    if (spec.kind === 'grid_columns') {
      out.items = nodes.map((el) => {
        const cs = getComputedStyle(el);
        // `auto-fit` collapses the tracks it does not need to 0px and still
        // reports them, so counting raw tracks would say "4 columns" for a grid
        // that renders 3. Zero-width tracks are not columns anyone can see.
        const tracks = splitTracks(cs.gridTemplateColumns).filter(
          (t) => !/^0(?:px|%)?$/.test(t.trim())
        );
        // A grid can produce columns without an explicit track list (implicit
        // columns, auto-flow), so fall back to where the children actually sit.
        const kids = Array.from(el.children).filter((k) => isVisible(k).visible);
        const lefts = new Set(kids.map((k) => Math.round(k.getBoundingClientRect().left)));
        return {
          who: describe(el),
          display: cs.display,
          track_list: cs.gridTemplateColumns,
          tracks: tracks.length,
          distinct_child_lefts: lefts.size,
          columns: tracks.length || (cs.display.includes('grid') ? lefts.size : 0),
          gap: { column: cs.columnGap, row: cs.rowGap },
        };
      });
      return out;
    }

    if (spec.kind === 'row_layout') {
      out.items = nodes.map((el) => {
        const kids = Array.from(el.children).filter((k) => isVisible(k).visible);
        const rects = kids.map((k) => ({ who: describe(k), ...rectOf(k) }));
        let rowPairs = 0;
        for (let i = 0; i < rects.length - 1; i++) {
          const a = rects[i];
          const b = rects[i + 1];
          const overlap = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
          const shortest = Math.max(1, Math.min(a.height, b.height));
          // Side by side = the boxes share most of their vertical extent and the
          // later one starts meaningfully further right. The x threshold is half
          // the narrower box, so genuinely overlapping designs (negative
          // margins) still count while stacked full-width blocks — which share a
          // left edge — never do.
          const step = 0.5 * Math.max(1, Math.min(a.width, b.width));
          if (overlap / shortest >= 0.5 && b.left >= a.left + step) rowPairs++;
        }
        // Group into visual rows by vertical overlap, the same test rowPairs
        // uses. Bucketing raw `top` counted `align-items: center` as stacking:
        // centring children of unequal height gives each a different top, so a
        // header that renders perfectly side by side reported one row per child.
        const byTop = rects.slice().sort((a, b) => a.top - b.top);
        const bands = [];
        for (const r of byTop) {
          const band = bands.find((b) => {
            const overlap = Math.min(b.bottom, r.bottom) - Math.max(b.top, r.top);
            return overlap / Math.max(1, Math.min(b.bottom - b.top, r.height)) >= 0.5;
          });
          if (band) {
            band.top = Math.min(band.top, r.top);
            band.bottom = Math.max(band.bottom, r.bottom);
          } else {
            bands.push({ top: r.top, bottom: r.bottom });
          }
        }
        return {
          who: describe(el),
          display: getComputedStyle(el).display,
          children: rects.length,
          row_pairs: rowPairs,
          distinct_rows: bands.length,
          rects: rects.slice(0, 6),
        };
      });
      return out;
    }

    if (spec.kind === 'centered') {
      out.items = nodes.map((el) => {
        const parent = spec.within ? el.closest(spec.within) || el.parentElement : el.parentElement;
        if (!parent) return { who: describe(el), parent: null };
        const box = contentBox(parent);
        const r = rectOf(el);
        return {
          who: describe(el),
          parent: describe(parent),
          left_gap: round(r.left - box.left),
          right_gap: round(box.right - r.right),
          top_gap: round(r.top - box.top),
          bottom_gap: round(box.bottom - r.bottom),
          parent_width: round(box.right - box.left),
          parent_height: round(box.bottom - box.top),
          width: r.width,
          height: r.height,
          visible: isVisible(el).visible,
        };
      });
      return out;
    }

    if (spec.kind === 'visible') {
      out.items = nodes.map((el) => {
        const v = isVisible(el);
        const r = rectOf(el);
        return {
          who: describe(el),
          visible: v.visible,
          reason: v.reason,
          width: r.width,
          height: r.height,
          text: (el.textContent || '').trim().slice(0, 80),
          has_media: !!el.querySelector('img,svg,canvas,video,input,button,select,textarea'),
          is_media: ['IMG', 'SVG', 'CANVAS', 'VIDEO', 'INPUT', 'BUTTON', 'SELECT', 'TEXTAREA'].includes(el.tagName),
        };
      });
      return out;
    }

    if (spec.kind === 'color') {
      out.items = nodes.map((el) => {
        const cs = getComputedStyle(el);
        const raw = cs.getPropertyValue(spec.property);
        const colour = parseColor(raw);
        // An element with a transparent background paints its ancestor's, and
        // "the page is dark" is a requirement about what the eye sees.
        let effective = colour;
        if (spec.resolve_through_ancestors && colour && colour.alpha === 0) {
          let node = el.parentElement;
          while (node) {
            const parsed = parseColor(getComputedStyle(node).getPropertyValue(spec.property));
            if (parsed && parsed.alpha > 0) { effective = parsed; break; }
            node = node.parentElement;
          }
        }
        const parent = el.parentElement;
        return {
          who: describe(el),
          raw: String(raw).trim(),
          declared: colour,
          effective,
          parent_who: parent ? describe(parent) : null,
          parent_colour: parent
            ? parseColor(getComputedStyle(parent).getPropertyValue(spec.property))
            : null,
          visible: isVisible(el).visible,
        };
      });
      return out;
    }

    if (spec.kind === 'box') {
      out.items = nodes.map((el) => {
        const parent = el.parentElement;
        const r = rectOf(el);
        const pbox = parent ? contentBox(parent) : null;
        return {
          who: describe(el),
          ...r,
          visible: isVisible(el).visible,
          parent_width: pbox ? round(pbox.right - pbox.left) : null,
          parent_height: pbox ? round(pbox.bottom - pbox.top) : null,
        };
      });
      return out;
    }

    if (spec.kind === 'on_top') {
      out.items = nodes.map((el) => {
        const r = el.getBoundingClientRect();
        const x = Math.min(Math.max(r.left + r.width / 2, 1), window.innerWidth - 1);
        const y = Math.min(Math.max(r.top + r.height / 2, 1), window.innerHeight - 1);
        const hit = document.elementFromPoint(x, y);
        return {
          who: describe(el),
          point: [round(x), round(y)],
          hit: hit ? describe(hit) : null,
          hit_is_self: !!hit && (hit === el || el.contains(hit)),
          hit_inside_other: !!hit && !!spec.over && !!hit.closest(spec.over),
          visible: isVisible(el).visible,
          z_index: getComputedStyle(el).zIndex,
        };
      });
      return out;
    }

    return { error: 'unknown probe kind ' + spec.kind };
  });
}
"""

#: Every remote image is answered with a fixed-size SVG so geometry is
#: deterministic and offline. Without it an aborted image collapses to a 0x0
#: box and a *correct* layout would fail its geometry check.
_IMAGE_STUB = (
    b'<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
    b'<rect width="400" height="300" fill="#8899aa"/></svg>'
)
_IMAGE_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif", ".bmp", ".ico")


# --------------------------------------------------------------------------
# The browser worker
# --------------------------------------------------------------------------


class RenderUnavailable(RuntimeError):
    """Raised when no browser could be obtained; never swallowed into a pass."""


@dataclass
class _Job:
    html: str
    viewport: dict[str, int]
    specs: list[dict[str, Any]]
    done: threading.Event = field(default_factory=threading.Event)
    result: Optional[list[dict[str, Any]]] = None
    error: Optional[str] = None


class _Browser:
    """Owns one Chromium process on a private thread, for the process lifetime.

    Launching Chromium costs ~250ms, so it is done once and reused; each job
    gets a fresh browser context (~5ms) so one learner's page cannot leak state
    into the next. When a job times out the whole browser is recycled, because a
    wedged page would otherwise poison every later submission.
    """

    def __init__(self) -> None:
        self._queue: "queue.Queue[Optional[_Job]]" = queue.Queue()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._unavailable: Optional[str] = None
        self._ready = threading.Event()
        self._generation = 0

    # -- public ------------------------------------------------------------
    def run(self, html: str, viewport: dict[str, int], specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        self._ensure_thread()
        if self._unavailable:
            raise RenderUnavailable(self._unavailable)
        job = _Job(html=html, viewport=viewport, specs=specs)
        generation = self._generation
        self._queue.put(job)
        if not job.done.wait(JOB_TIMEOUT_SECONDS):
            self._recycle(generation)
            raise TimeoutError(
                f"the page did not finish rendering within {JOB_TIMEOUT_SECONDS:.0f}s"
            )
        if job.error:
            raise RenderUnavailable(job.error)
        return job.result or []

    def probe_availability(self) -> Optional[str]:
        """None when a browser is usable, else the reason it is not."""
        try:
            self.run("<!doctype html><title>probe</title><p>ok</p>", DEFAULT_VIEWPORT, [])
        except (RenderUnavailable, TimeoutError) as exc:
            return str(exc)
        return None

    def shutdown(self) -> None:
        with self._lock:
            thread, self._thread = self._thread, None
            if thread is not None:
                self._queue.put(None)

    # -- internals ---------------------------------------------------------
    def _ensure_thread(self) -> None:
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return
            self._ready.clear()
            self._unavailable = None
            self._thread = threading.Thread(
                target=self._serve, name="sprintforge-render", daemon=True
            )
            self._thread.start()
        self._ready.wait(JOB_TIMEOUT_SECONDS + 20)

    def _recycle(self, generation: int) -> None:
        """Drop a wedged browser so the next submission gets a fresh one."""
        with self._lock:
            if generation != self._generation:
                return
            self._generation += 1
            thread, self._thread = self._thread, None
        if thread is not None:
            self._queue.put(None)

    def _serve(self) -> None:
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:  # pragma: no cover - environment dependent
            self._unavailable = (
                "Playwright is not installed (`pip install playwright && "
                f"playwright install chromium`): {exc}"
            )
            self._ready.set()
            return

        playwright = None
        browser = None
        try:
            playwright = sync_playwright().start()
            browser = playwright.chromium.launch(
                args=["--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"],
                timeout=BROWSER_LAUNCH_TIMEOUT_MS,
            )
        except Exception as exc:  # noqa: BLE001 - reported, never swallowed
            self._unavailable = (
                "headless Chromium could not be launched — run "
                f"`playwright install chromium`: {type(exc).__name__}: {str(exc)[:300]}"
            )
            self._ready.set()
            if browser is not None:
                _quietly(browser.close)
            if playwright is not None:
                _quietly(playwright.stop)
            return

        self._ready.set()
        try:
            while True:
                job = self._queue.get()
                if job is None:
                    return
                try:
                    job.result = self._render(browser, job)
                except Exception as exc:  # noqa: BLE001
                    job.error = f"{type(exc).__name__}: {str(exc)[:400]}"
                finally:
                    job.done.set()
        finally:
            _quietly(browser.close)
            _quietly(playwright.stop)

    @staticmethod
    def _render(browser: Any, job: _Job) -> list[dict[str, Any]]:
        context = browser.new_context(viewport=job.viewport, device_scale_factor=1)
        try:
            context.set_default_timeout(PAGE_TIMEOUT_MS)
            page = context.new_page()
            page.route("**/*", _handle_route)
            page.set_content(job.html, wait_until="load", timeout=PAGE_TIMEOUT_MS)
            if not job.specs:
                return []
            return page.evaluate(PROBE_JS, job.specs)
        finally:
            _quietly(context.close)


def _handle_route(route: Any) -> None:
    """Keep rendering offline and deterministic.

    Grading must not depend on a CDN being reachable: images are answered with a
    fixed-size placeholder and everything else remote is aborted.
    """
    request = route.request
    url = request.url
    try:
        if url.startswith("data:") or url.startswith("about:"):
            route.continue_()
            return
        path = url.split("?", 1)[0].lower()
        if request.resource_type == "image" or path.endswith(_IMAGE_SUFFIXES):
            route.fulfill(status=200, content_type="image/svg+xml", body=_IMAGE_STUB)
            return
        route.abort()
    except Exception:  # noqa: BLE001 - a closed page mid-route is not a verdict
        _quietly(route.abort)


def _quietly(fn: Callable[[], Any]) -> None:
    try:
        fn()
    except Exception:  # noqa: BLE001
        pass


_BROWSER = _Browser()


def shutdown() -> None:
    """Release the browser (used by tests; the daemon thread dies with the app)."""
    _BROWSER.shutdown()


def mode() -> str:
    """`require` (default) fails closed; `skip` marks checks as not run."""
    value = (os.environ.get("SPRINTFORGE_RENDER_JUDGE") or "require").strip().lower()
    return "skip" if value in {"skip", "off", "0", "false"} else "require"


def is_available() -> bool:
    """True when a rendered check would really execute. Intended for tests."""
    return _BROWSER.probe_availability() is None


# --------------------------------------------------------------------------
# Judging
# --------------------------------------------------------------------------


def _tolerance(check: dict[str, Any], reference: float, default_ratio: float = 0.02) -> float:
    """Absolute px slack. Ranges beat exact pixels: sub-pixel rounding, font
    metrics and scrollbar width all move a *correct* layout by a pixel or two."""
    if check.get("tolerance") is not None:
        return float(check["tolerance"])
    return max(float(check.get("min_tolerance", 2.0)), abs(reference) * default_ratio)


def _spec_for(check: dict[str, Any]) -> dict[str, Any]:
    kind = {
        "render_computed_style": "computed_style",
        "render_grid_columns": "grid_columns",
        "render_row_layout": "row_layout",
        "render_centered": "centered",
        "render_visible": "visible",
        "render_color": "color",
        "render_box": "box",
        "render_on_top": "on_top",
    }[check["type"]]
    spec: dict[str, Any] = {"kind": kind, "selector": check.get("selector", "")}
    if kind == "computed_style":
        spec["property"] = str(check.get("property", "")).lower()
    if kind == "color":
        spec["property"] = str(check.get("property", "background-color")).lower()
        spec["resolve_through_ancestors"] = bool(check.get("resolve_through_ancestors", True))
    if kind == "centered":
        spec["within"] = check.get("within")
    if kind == "on_top":
        spec["over"] = check.get("over")
    return spec


def _viewport(check: dict[str, Any]) -> dict[str, int]:
    given = check.get("viewport") or {}
    return {
        "width": int(given.get("width", DEFAULT_VIEWPORT["width"])),
        "height": int(given.get("height", DEFAULT_VIEWPORT["height"])),
    }


def _in_range(value: float, check: dict[str, Any], keys: tuple[str, str]) -> Optional[str]:
    low_key, high_key = keys
    if check.get(low_key) is not None and value < float(check[low_key]) - 1e-9:
        return f"below the required minimum of {check[low_key]}"
    if check.get(high_key) is not None and value > float(check[high_key]) + 1e-9:
        return f"above the allowed maximum of {check[high_key]}"
    return None


def _value_ok(value: str, check: dict[str, Any]) -> bool:
    """A computed value satisfies the constraints, with normalised whitespace."""
    normalised = " ".join(value.split()).lower()
    if check.get("value_in") is not None:
        accepted = {" ".join(str(v).split()).lower() for v in check["value_in"]}
        if normalised not in accepted:
            return False
    if check.get("value_pattern") is not None:
        if not re.search(check["value_pattern"], normalised, re.IGNORECASE):
            return False
    if check.get("value_not_in") is not None:
        rejected = {" ".join(str(v).split()).lower() for v in check["value_not_in"]}
        if normalised in rejected:
            return False
    number = _leading_number(normalised)
    if check.get("min_value") is not None or check.get("max_value") is not None:
        if number is None:
            return False
        if _in_range(number, check, ("min_value", "max_value")):
            return False
    return True


def _leading_number(value: str) -> Optional[float]:
    match = re.search(r"-?\d+(?:\.\d+)?", value)
    return float(match.group(0)) if match else None


def _required_text(check: dict[str, Any]) -> str:
    parts = []
    if check.get("value_in") is not None:
        parts.append("one of " + " | ".join(str(v) for v in check["value_in"]))
    if check.get("value_pattern") is not None:
        parts.append(f"matching /{check['value_pattern']}/")
    if check.get("value_not_in") is not None:
        parts.append("not " + " | ".join(str(v) for v in check["value_not_in"]))
    if check.get("min_value") is not None:
        parts.append(f">= {check['min_value']}")
    if check.get("max_value") is not None:
        parts.append(f"<= {check['max_value']}")
    return ", ".join(parts) or "a value to be present"


def _judge(check: dict[str, Any], facts: dict[str, Any]) -> RenderVerdict:
    """Turn one probe's observations into a verdict with an explaining message."""
    selector = check.get("selector", "")
    if facts.get("error"):
        return RenderVerdict(False, f"{selector}: {facts['error']}")
    count = int(facts.get("count", 0))
    min_count = int(check.get("min_count", 1))
    if count < min_count:
        return RenderVerdict(
            False,
            f"the rendered page has {count} element(s) matching {selector}, need {min_count}",
        )

    kind = facts.get("kind")

    if kind == "computed_style":
        prop = check.get("property")
        entries = facts.get("values") or []
        if check.get("require_visible", False):
            visible = [e for e in entries if e.get("visible")]
            if not visible:
                return RenderVerdict(
                    False, f"every element matching {selector} is invisible on the page"
                )
            entries = visible
        matching = [e for e in entries if _value_ok(e.get("value", ""), check)]
        needed = len(entries) if check.get("all_match") else 1
        if len(matching) >= needed:
            return RenderVerdict(
                True,
                f"{prop} on {matching[0]['who']} computes to '{matching[0]['value']}'",
            )
        observed = ", ".join(f"{e['who']} -> '{e['value'] or '(empty)'}'" for e in entries[:4])
        return RenderVerdict(
            False,
            f"computed {prop} was {observed}; required {_required_text(check)}",
        )

    if kind == "grid_columns":
        items = facts.get("items") or []
        best = max(items, key=lambda i: i.get("columns", 0))
        columns = int(best.get("columns", 0))
        if check.get("require_grid", True) and "grid" not in (best.get("display") or ""):
            return RenderVerdict(
                False,
                f"{best['who']} renders with display: {best.get('display')}, so it is not a "
                f"grid container (its column track list is '{best.get('track_list')}')",
            )
        equals = check.get("equals")
        if equals is not None and columns != int(equals):
            return RenderVerdict(
                False,
                f"expected {equals} columns, rendered {columns} "
                f"(track list '{best.get('track_list')}')",
            )
        problem = _in_range(columns, check, ("min", "max"))
        if problem:
            bound = check.get("min") if "minimum" in problem else check.get("max")
            return RenderVerdict(
                False,
                f"expected {'at least' if 'minimum' in problem else 'at most'} {bound} columns, "
                f"rendered {columns} (track list '{best.get('track_list')}')",
            )
        return RenderVerdict(
            True,
            f"{best['who']} renders {columns} column(s) at "
            f"{_viewport(check)['width']}px (track list '{best.get('track_list')}')",
        )

    if kind == "row_layout":
        items = facts.get("items") or []
        min_children = int(check.get("min_children", 2))
        best = max(items, key=lambda i: (i.get("row_pairs", 0), i.get("children", 0)))
        children = int(best.get("children", 0))
        if children < min_children:
            return RenderVerdict(
                False,
                f"{best['who']} has {children} visible child element(s), need {min_children} "
                "to form a row",
            )
        needed_pairs = int(check.get("min_row_pairs", children - 1))
        pairs = int(best.get("row_pairs", 0))
        if pairs < needed_pairs:
            stacked = [
                f"{r['who']} at y={r['top']}" for r in (best.get("rects") or [])[:4]
            ]
            return RenderVerdict(
                False,
                f"{best['who']} lays its children out on {best.get('distinct_rows')} row(s): "
                f"only {pairs} of {needed_pairs} adjacent pairs sit side by side "
                f"({'; '.join(stacked)})",
            )
        if check.get("max_rows") is not None and int(best.get("distinct_rows", 0)) > int(
            check["max_rows"]
        ):
            return RenderVerdict(
                False,
                f"expected at most {check['max_rows']} row(s), the children rendered on "
                f"{best.get('distinct_rows')}",
            )
        return RenderVerdict(
            True,
            f"{best['who']} lays {children} children out in a row "
            f"(display: {best.get('display')})",
        )

    if kind == "centered":
        axis = check.get("axis", "horizontal")
        items = [i for i in (facts.get("items") or []) if i.get("parent")]
        if not items:
            return RenderVerdict(False, f"{selector} has no parent to be centred within")
        best = None
        worst_message = ""
        for item in items:
            if check.get("require_visible", True) and not item.get("visible"):
                worst_message = f"{item['who']} is not visible, so it is not centred anywhere"
                continue
            failures = []
            if axis in {"horizontal", "both"} and not check.get("allow_full_width"):
                # A block that fills its parent has equal gaps of zero on both
                # sides. Calling that "centred" is how an unstyled page passes.
                parent_width = float(item.get("parent_width") or 0)
                if parent_width and float(item["width"]) >= parent_width - _tolerance(
                    check, parent_width
                ):
                    failures.append(
                        f"fills the full width of {item['parent']} "
                        f"({item['width']}px of {parent_width}px), so it is not centred "
                        "within it — give it a width or a max-width first"
                    )
            if axis in {"horizontal", "both"}:
                tol = _tolerance(check, item.get("parent_width") or 0)
                delta = abs(float(item["left_gap"]) - float(item["right_gap"]))
                if delta > tol:
                    failures.append(
                        f"horizontally off by {delta:.1f}px (left gap {item['left_gap']}px vs "
                        f"right gap {item['right_gap']}px, tolerance {tol:.1f}px)"
                    )
            if axis in {"vertical", "both"}:
                tol = _tolerance(check, item.get("parent_height") or 0)
                delta = abs(float(item["top_gap"]) - float(item["bottom_gap"]))
                if delta > tol:
                    failures.append(
                        f"vertically off by {delta:.1f}px (top gap {item['top_gap']}px vs "
                        f"bottom gap {item['bottom_gap']}px, tolerance {tol:.1f}px)"
                    )
            if not failures:
                best = item
                break
            worst_message = f"{item['who']} is {' and '.join(failures)}"
        if best is not None:
            return RenderVerdict(
                True,
                f"{best['who']} is centred {axis}ly inside {best['parent']}",
            )
        return RenderVerdict(False, worst_message or f"{selector} is not centred")

    if kind == "visible":
        items = facts.get("items") or []
        failures = []
        for item in items:
            if not item.get("visible"):
                failures.append(f"{item['who']} is not visible: {item.get('reason')}")
                continue
            if check.get("min_height") is not None and float(item["height"]) < float(
                check["min_height"]
            ):
                failures.append(
                    f"{item['who']} renders {item['height']}px tall, need at least "
                    f"{check['min_height']}px"
                )
                continue
            if check.get("min_width") is not None and float(item["width"]) < float(
                check["min_width"]
            ):
                failures.append(
                    f"{item['who']} renders {item['width']}px wide, need at least "
                    f"{check['min_width']}px"
                )
                continue
            if check.get("non_empty") and not (
                item.get("text") or item.get("has_media") or item.get("is_media")
            ):
                failures.append(f"{item['who']} is visible but renders no content")
                continue
            return RenderVerdict(
                True,
                f"{item['who']} renders {item['width']}x{item['height']}px and is visible",
            )
        return RenderVerdict(
            False, "; ".join(failures[:3]) or f"{selector} did not render visibly"
        )

    if kind == "color":
        prop = check.get("property", "background-color")
        items = facts.get("items") or []
        failures = []
        for item in items:
            colour = item.get("effective") or item.get("declared")
            if not colour:
                failures.append(
                    f"{item['who']} has no resolvable {prop} (computed '{item.get('raw')}')"
                )
                continue
            if check.get("require_opaque", True) and float(colour.get("alpha", 1)) <= 0.05:
                failures.append(
                    f"{item['who']} resolves {prop} to {colour['text']}, which paints nothing"
                )
                continue
            luminance = float(colour.get("luminance", 0))
            problem = _in_range(luminance, check, ("min_luminance", "max_luminance"))
            if problem:
                failures.append(
                    f"{item['who']} resolves {prop} to {colour['text']} "
                    f"(relative luminance {luminance:.3f}), {problem}"
                )
                continue
            # "This element is coloured by its own token" is only observable as
            # a difference from what it would have inherited: an unresolvable
            # `var()` silently computes to the inherited colour.
            if check.get("differs_from_parent") and item.get("parent_colour"):
                parent_colour = item["parent_colour"]
                distance = max(
                    abs(float(a) - float(b))
                    for a, b in zip(colour["rgb"], parent_colour["rgb"])
                )
                if distance <= float(check.get("min_channel_difference", 12)):
                    failures.append(
                        f"{item['who']} resolves {prop} to {colour['text']}, the same colour "
                        f"{item.get('parent_who')} already has ({parent_colour['text']}) — the "
                        "value did not resolve to anything of its own"
                    )
                    continue
            near = check.get("near_rgb")
            if near is not None:
                distance = max(
                    abs(float(a) - float(b)) for a, b in zip(colour["rgb"], near)
                )
                allowed = float(check.get("max_channel_distance", 48))
                if distance > allowed:
                    failures.append(
                        f"{item['who']} resolves {prop} to {colour['text']}, "
                        f"{distance:.0f} off rgb({', '.join(str(c) for c in near)}) "
                        f"(allowed {allowed:.0f} per channel)"
                    )
                    continue
            return RenderVerdict(
                True,
                f"{item['who']} resolves {prop} to {colour['text']} "
                f"(relative luminance {luminance:.3f})",
            )
        return RenderVerdict(False, "; ".join(failures[:3]) or f"{selector}: {prop} not resolved")

    if kind == "box":
        items = facts.get("items") or []
        failures = []
        for item in items:
            if check.get("require_visible", True) and not item.get("visible"):
                failures.append(f"{item['who']} is not visible")
                continue
            problems = []
            for axis, keys in (("width", ("min_width", "max_width")), ("height", ("min_height", "max_height"))):
                problem = _in_range(float(item[axis]), check, keys)
                if problem:
                    problems.append(f"rendered {axis} {item[axis]}px is {problem}")
            for axis, keys in (
                ("width", ("min_width_ratio", "max_width_ratio")),
                ("height", ("min_height_ratio", "max_height_ratio")),
            ):
                if check.get(keys[0]) is None and check.get(keys[1]) is None:
                    continue
                parent = item.get(f"parent_{axis}") or 0
                if parent <= 0:
                    problems.append(f"parent has no measurable {axis}")
                    continue
                ratio = float(item[axis]) / float(parent)
                problem = _in_range(ratio, check, keys)
                if problem:
                    problems.append(
                        f"rendered {axis} is {ratio:.2f} of its parent ({item[axis]}px of "
                        f"{parent}px), which is {problem}"
                    )
            if not problems:
                return RenderVerdict(
                    True, f"{item['who']} renders {item['width']}x{item['height']}px"
                )
            failures.append(f"{item['who']}: {'; '.join(problems)}")
        return RenderVerdict(False, "; ".join(failures[:3]) or f"{selector} box constraints failed")

    if kind == "on_top":
        items = facts.get("items") or []
        failures = []
        for item in items:
            if not item.get("visible"):
                failures.append(f"{item['who']} is not visible, so it cannot be on top")
                continue
            if check.get("over") and item.get("hit_inside_other") and not item.get("hit_is_self"):
                failures.append(
                    f"at {tuple(item['point'])} the topmost element is {item['hit']}, which is "
                    f"inside {check['over']} — {item['who']} is painted underneath "
                    f"(z-index {item.get('z_index')})"
                )
                continue
            if not item.get("hit_is_self"):
                failures.append(
                    f"at {tuple(item['point'])} the topmost element is {item['hit']}, "
                    f"not {item['who']} (z-index {item.get('z_index')})"
                )
                continue
            return RenderVerdict(
                True,
                f"{item['who']} is the topmost element at {tuple(item['point'])}",
            )
        return RenderVerdict(False, "; ".join(failures[:3]) or f"{selector} is not on top")

    return RenderVerdict(False, f"unsupported rendered check '{check.get('type')}'")


def _configuration_error(check: dict[str, Any], reason: str) -> RenderVerdict:
    """A verdict that blames the validator, loudly, instead of the learner."""
    logger.error(
        "validator configuration error on check %r (%s): %s",
        check.get("id"),
        check.get("type"),
        reason,
    )
    return RenderVerdict(
        passed=False,
        detail=f"validator configuration error: {reason}",
        hint=(
            "This is a fault in the ticket's checks, not in your code. It has been "
            "logged for the SprintForge team; nothing you write can satisfy this "
            "check until the spec is repaired."
        ),
        config_error=True,
    )


def run_render_checks(
    files: dict[str, str], checks: list[tuple[int, dict[str, Any]]]
) -> dict[int, RenderVerdict]:
    """Grade `checks` (index, spec) by rendering. Never returns a silent pass.

    Checks that share an entry document and a viewport are graded in one page
    load, so a module's whole rendered suite normally costs one navigation.
    """
    verdicts: dict[int, RenderVerdict] = {}
    if not checks:
        return verdicts

    groups: dict[tuple[str, int, int], list[tuple[int, dict[str, Any]]]] = {}
    for index, check in checks:
        # Never hand an uninterpolated selector to the browser. `querySelectorAll`
        # answers `#{entity}List` with "invalid selector", which reads exactly like
        # a learner mistake and is not one.
        # `within` and `over` reach `closest()`, so they are guarded alongside
        # the selector that reaches `querySelectorAll`.
        leak = next(
            (
                spec_interpolation.selector_leak(check.get(field))
                for field in ("selector", "within", "over")
                if spec_interpolation.selector_leak(check.get(field))
            ),
            None,
        )
        if leak:
            verdicts[index] = _configuration_error(check, leak)
            continue
        entry = check.get("entry") or check.get("file") or _guess_entry(files)
        if not entry or entry not in files:
            verdicts[index] = RenderVerdict(
                False,
                f"the page could not be assembled: no entry document '{entry or DEFAULT_ENTRY}' "
                "in this submission",
            )
            continue
        viewport = _viewport(check)
        groups.setdefault((entry, viewport["width"], viewport["height"]), []).append(
            (index, check)
        )

    skip_mode = mode() == "skip"
    for (entry, width, height), group in groups.items():
        html = assemble_page(files, entry)
        if not html or not html.strip():
            for index, _check in group:
                verdicts[index] = RenderVerdict(False, f"{entry} is empty, so nothing renders")
            continue
        specs = [_spec_for(check) for _index, check in group]
        try:
            observations = _BROWSER.run(html, {"width": width, "height": height}, specs)
        except (RenderUnavailable, TimeoutError) as exc:
            reason = str(exc)
            for index, _check in group:
                verdicts[index] = RenderVerdict(
                    passed=False,
                    detail=(
                        f"this check is graded by rendering the page, and the browser was "
                        f"unavailable: {reason}"
                    ),
                    hint=(
                        "Rendered checks need Playwright's Chromium: "
                        "`pip install playwright && playwright install chromium`."
                    ),
                    skipped=skip_mode,
                )
            continue
        for (index, check), facts in zip(group, observations):
            try:
                verdicts[index] = _judge(check, facts or {})
            except Exception as exc:  # noqa: BLE001 - a broken spec fails closed
                verdicts[index] = RenderVerdict(
                    False, f"this rendered check could not be evaluated: {exc}"
                )
    return verdicts


#: Truncated because this field exists to answer "was the same content used?",
#: which a prefix settles, not to be a cryptographic commitment to a body.
_HASH_LENGTH = 12


def assembly_report(
    files: dict[str, str], checks: list[tuple[int, dict[str, Any]]]
) -> dict[str, Any]:
    """What the render sandbox assembled, in a form safe to send to a client.

    Deliberately only three things: the file names in the bundle, the entry
    document each rendered check resolved to, and a hash per file. Enough to see
    at a glance that `index.html` was present and which stylesheet was used, which
    is the whole reason this exists — the assembly bug it diagnoses was invisible
    without reading the database.

    What is *not* here matters more than what is. No file bodies, no assembled
    HTML, and nothing at all about the checks: no ids, no labels, no selectors, no
    expected values, and so no way to tell a hidden check from a visible one. The
    bundle itself holds only the learner's own files and the read-only project
    documents they are already shown, so there is no reference solution, expected
    output or scale-case data in scope to hash in the first place.
    """
    entries: list[str] = []
    for _index, check in checks:
        # `DEFAULT_ENTRY` when nothing resolves, which is the name the grading
        # verdict reports as missing — the two must not tell different stories.
        entry = check.get("entry") or check.get("file") or _guess_entry(files) or DEFAULT_ENTRY
        if entry not in entries:
            entries.append(entry)
    resolved = [entry for entry in entries if entry in files]
    return {
        "files": sorted(files),
        # None is the diagnosis, not an omission: it is exactly the state that
        # produced "no entry document in this submission".
        "entry": resolved[0] if resolved else None,
        "requested_entries": entries,
        "missing_entries": [entry for entry in entries if entry not in files],
        "hashes": {
            name: "sha256:"
            + hashlib.sha256((content or "").encode("utf-8")).hexdigest()[:_HASH_LENGTH]
            for name, content in sorted(files.items())
        },
    }


def describe_spec() -> str:
    """Human-readable summary of the spec shape, used by the docs/tests."""
    return json.dumps(sorted(RENDER_CHECK_TYPES), indent=2)
