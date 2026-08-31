"""Screenshot the project a learner ends up with, composed from the templates.

The ticket templates are only as good as the thing they produce, and that is a
visual judgement no check can make. This assembles the reference solutions of
the web tickets into the finished bundle — exactly as `render_judge.assemble_page`
does when grading — loads it in headless Chromium and writes PNGs at a laptop
and a phone width.

Remote posters are replaced with locally generated gradient SVGs so the run is
offline and deterministic; pass `--live` to let the real image URLs load.

    cd backend && PYTHONPATH=. .venv/bin/python scripts/shoot_composed_project.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.data.ticket_templates import (  # noqa: E402
    CSS_RESPONSIVE_SOLUTION,
    HTML_NAVIGATION_SOLUTION,
    JS_RENDER_LIST_SOLUTION,
    STARTER_FILES,
)
from app.services.render_judge import assemble_page  # noqa: E402

CONTEXT = {
    "domain": "Movie Ticket Booking System",
    "entity": "movie",
    "entity_plural": "movies",
}

OUT_DIR = Path(__file__).resolve().parents[1] / "docs" / "screenshots"

SHOTS = [
    ("composed-project-laptop.png", 1280, 900, True),
    ("composed-project-phone.png", 390, 844, True),
]

#: The same markup with the stylesheet a learner starts from: the default serif
#: and blue underlined links the owner complained about. Kept as the baseline the
#: styling tickets are judged against.
BASELINE_SHOT = ("unstyled-baseline-laptop.png", 1280, 900, True)

#: Stand-in artwork. Two-stop gradients per seed, so the cards look like posters
#: rather than grey rectangles and the crop is visible.
PALETTES = [
    ("#2b3a67", "#f26a4b"), ("#123c3c", "#6ee7b7"), ("#3b1f4e", "#f472b6"),
    ("#1e3a5f", "#38bdf8"), ("#4a2b0f", "#fbbf24"), ("#0f2f2b", "#a3e635"),
    ("#3a1c2b", "#fb7185"),
]


def fill(text: str) -> str:
    for key, value in CONTEXT.items():
        text = text.replace("{" + key + "}", value)
    return text


def placeholder(index: int, width: int, height: int) -> str:
    top, bottom = PALETTES[index % len(PALETTES)]
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}">'
        f'<defs><linearGradient id="g" x1="0" y1="0" x2="0.6" y2="1">'
        f'<stop offset="0" stop-color="{top}"/><stop offset="1" stop-color="{bottom}"/>'
        f"</linearGradient></defs>"
        f'<rect width="{width}" height="{height}" fill="url(#g)"/></svg>'
    )
    from urllib.parse import quote

    return "data:image/svg+xml;utf8," + quote(svg)


def localise_images(html: str) -> str:
    """Swap every remote image URL for a deterministic inline gradient."""
    counter = {"n": 0}

    def swap(match: re.Match[str]) -> str:
        url = match.group(1)
        if url.startswith("data:"):
            return match.group(0)
        wide = "hero" in url or "1200" in url
        counter["n"] += 1
        size = (1200, 450) if wide else (400, 600)
        return match.group(0).replace(url, placeholder(counter["n"], *size))

    html = re.sub(r'src\s*=\s*"([^"]+)"', swap, html)
    return re.sub(r'src="\$\{item\.poster\}"', swap, html)


def build(live: bool, css: str) -> str:
    files = {
        "index.html": fill(HTML_NAVIGATION_SOLUTION),
        "styles.css": fill(css),
        "script.js": fill(JS_RENDER_LIST_SOLUTION),
    }
    page = assemble_page(files, "index.html")
    assert page, "the bundle did not assemble"
    return page if live else localise_images(page)


def main() -> int:
    live = "--live" in sys.argv
    html = build(live, CSS_RESPONSIVE_SOLUTION)
    baseline = build(live, STARTER_FILES["styles.css"].format(**CONTEXT))
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(args=["--hide-scrollbars"])
        try:
            name, width, height, full_page = BASELINE_SHOT
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()
            page.set_content(baseline, wait_until="load")
            page.screenshot(path=str(OUT_DIR / name), full_page=full_page)
            print(f"{OUT_DIR / name}  {width}x{height}  (unstyled baseline)")
            context.close()

            for name, width, height, full_page in SHOTS:
                context = browser.new_context(
                    viewport={"width": width, "height": height}, device_scale_factor=2
                )
                page = context.new_page()
                page.set_content(html, wait_until="load")
                page.wait_for_timeout(400)
                target = OUT_DIR / name
                page.screenshot(path=str(target), full_page=full_page)
                metrics = page.evaluate(
                    "() => ({"
                    " scrollWidth: document.documentElement.scrollWidth,"
                    " columns: getComputedStyle(document.querySelector('#movieList'))"
                    "   .gridTemplateColumns.split(' ').length,"
                    " headline: getComputedStyle(document.querySelector('#hero h2')).fontSize,"
                    " font: getComputedStyle(document.body).fontFamily,"
                    " linkColour: getComputedStyle(document.querySelector('nav a')).color,"
                    " cards: document.querySelectorAll('.card').length,"
                    "})"
                )
                print(f"{target}  {width}x{height}  {metrics}")
                context.close()
        finally:
            browser.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
