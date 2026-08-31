"""Check that every learning resource we hand a learner actually resolves.

Two kinds of link rot matter here and they fail differently:

* Documentation URLs move. A dead one usually 404s, which a HEAD request finds.
* YouTube videos get deleted, made private, or region-blocked. Those still
  return 200 for the watch page, so a HEAD request proves nothing. The oEmbed
  endpoint is the honest check: it 404s for anything the public cannot play,
  and for anything live it returns the real title and channel, which lets us
  confirm the video is the one we meant rather than merely that *a* video
  exists at that id.

Read-only. Prints a report and exits non-zero if anything is broken, so it can
run in CI as a guard against silently recommending dead links.

    PYTHONPATH=. .venv/bin/python scripts/verify_resource_links.py
    PYTHONPATH=. .venv/bin/python scripts/verify_resource_links.py --youtube-only
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

TIMEOUT = 15
UA = "Mozilla/5.0 (compatible; SprintForgeLinkCheck/1.0)"


def check_youtube(url: str) -> tuple[bool, str]:
    """Returns (ok, detail). Detail carries the real title for a live video."""
    oembed = "https://www.youtube.com/oembed?" + urllib.parse.urlencode(
        {"url": url, "format": "json"}
    )
    request = urllib.request.Request(oembed, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read().decode("utf-8"))
        return True, f"{payload.get('author_name', '?')} · {payload.get('title', '?')}"
    except urllib.error.HTTPError as error:
        # 401/403 from oEmbed means embedding is disabled but the video plays on
        # YouTube itself, which is fine for a link we are only ever linking to.
        if error.code in (401, 403):
            return True, "playable (embedding disabled)"
        return False, f"HTTP {error.code}"
    except Exception as error:  # noqa: BLE001 - report, never crash the sweep
        return False, type(error).__name__


def check_doc(url: str) -> tuple[bool, str]:
    request = urllib.request.Request(url, headers={"User-Agent": UA}, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.status < 400, f"HTTP {response.status}"
    except urllib.error.HTTPError as error:
        return False, f"HTTP {error.code}"
    except Exception as error:  # noqa: BLE001
        return False, type(error).__name__


def check(entry: tuple[str, str, str]) -> tuple[str, str, str, bool, str]:
    owner, label, url = entry
    if "youtube.com" in url or "youtu.be" in url:
        # A search URL is a query, not a document: it cannot rot, so there is
        # nothing to verify and asking YouTube is only a way to get rate limited.
        if "/results?" in url:
            return owner, label, url, True, "search query"
        ok, detail = check_youtube(url)
    else:
        ok, detail = check_doc(url)
    return owner, label, url, ok, detail


def collect() -> list[tuple[str, str, str]]:
    entries: list[tuple[str, str, str]] = []

    from app.data.learning_resources import EXTERNAL_RESOURCES

    for skill_id, resources in EXTERNAL_RESOURCES.items():
        for resource in resources:
            entries.append((skill_id, resource.get("title", "?"), resource["url"]))

    try:
        from app.data.roadmaps import ROADMAPS
    except ImportError:
        return entries

    for roadmap in ROADMAPS:
        for step in roadmap["steps"]:
            for resource in step.get("resources", []):
                entries.append((roadmap["id"], step["title"], resource["url"]))

    return entries


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--youtube-only", action="store_true")
    args = parser.parse_args()

    entries = collect()
    if args.youtube_only:
        entries = [e for e in entries if "youtu" in e[2]]

    print(f"Checking {len(entries)} links...\n")

    broken: list[tuple[str, str, str, bool, str]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        for owner, label, url, ok, detail in pool.map(check, entries):
            if not ok:
                broken.append((owner, label, url, ok, detail))
                print(f"BROKEN  {owner:<24} {label[:40]:<42} {detail}")
                print(f"        {url}")

    print()
    if broken:
        print(f"{len(broken)} of {len(entries)} links are broken.")
        return 1
    print(f"All {len(entries)} links resolve.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
