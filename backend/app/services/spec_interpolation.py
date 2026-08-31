"""The one place a ticket template's `{placeholder}` becomes a real value.

Ticket templates are written against a generic domain noun — `#{entity}List`,
"the {domain} listing" — and every writer of a `validation_spec` has to resolve
those before the spec is stored. There used to be two writers: the generator
(which interpolated) and the re-sync scripts (which did not), so a re-synced
ticket kept the literal string `#{entity}List` in its selectors and the browser
answered `querySelectorAll('#{entity}List')` with "invalid selector" — a red
check for correct learner work.

So this module owns three things and nothing else owns any of them:

* the vocabulary of placeholders (`PLACEHOLDER_NAMES`) and how a context is
  built from a project (`context_for_project`, `context_for_ticket`),
* `fill`, the substitution itself,
* `build_validation_spec`, the only sanctioned way to turn a template into a
  stored spec. It refuses to return a spec that still contains a placeholder,
  so a future writer that routes through it cannot reintroduce this bug, and a
  writer that does not route through it is caught by the write-time guard on
  `Ticket.validation_spec` (see `app/models/entities.py`).

Why not `str.format` alone: it raises `KeyError` on the first unknown key, and
the old helper swallowed that and returned the string *unchanged*. A template
string that mixes a placeholder with literal braces — JSX (`key={item.id}`), a
CSS body, a JS template literal — therefore silently kept its `{entity}`. That
is precisely how this survived. `fill` still tries `format` first (so escaped
`{{` braces keep working), but when `format` cannot cope it substitutes the
known placeholder names directly, and in `strict` mode it raises rather than
returning a half-resolved string.
"""

from __future__ import annotations

import re
from typing import Any, Optional

#: The complete placeholder vocabulary. Deliberately closed: template bodies are
#: full of braces that are *code* (`{item}` in JSX, `${amount}` in a template
#: literal, `{2,}` in a regex), and treating those as placeholders would corrupt
#: the very strings we are trying to protect. A name outside this set is left
#: exactly as it was found.
PLACEHOLDER_NAMES = frozenset({"domain", "entity", "entity_plural"})

_PLACEHOLDER_RE = re.compile(r"\{(" + "|".join(sorted(PLACEHOLDER_NAMES)) + r")\}")

#: `{...}` that a selector cannot legally contain. Any brace at all in a
#: selector is a templating leak, not a CSS construct, so the selector guard is
#: broader than the vocabulary above.
_ANY_BRACE_RE = re.compile(r"\{[^{}]*\}")

STOP_WORDS = {
    "a", "an", "the", "app", "application", "system", "platform", "website", "site",
    "build", "create", "make", "want", "i", "to", "for", "with", "my", "using", "clone",
    "web", "project", "simple", "full", "stack",
}


class SpecInterpolationError(RuntimeError):
    """A spec was about to be stored with an unresolved placeholder in it."""


def infer_entity(idea: str, title: str) -> tuple[str, str]:
    """Derive the primary domain noun used to name tickets and identifiers."""
    words = re.findall(r"[a-zA-Z]+", f"{title} {idea}".lower())
    candidates = [w for w in words if w not in STOP_WORDS and len(w) > 2]
    priority = ["movie", "ticket", "seat", "booking", "product", "task", "recipe", "course", "event", "flight", "hotel", "note"]
    entity = next((p for p in priority if p in candidates), None)
    if entity is None:
        entity = candidates[0] if candidates else "item"
    plural = entity if entity.endswith("s") else f"{entity}s"
    return entity, plural


def context_for(idea: str, title: str) -> dict[str, str]:
    """The interpolation context, built one way for every caller.

    Generation and re-sync used to construct this separately; sharing it is what
    makes "the spec a ticket has" and "the spec it would be re-synced to" the
    same string rather than two things that merely ought to agree.
    """
    entity, entity_plural = infer_entity(idea, title)
    return {"domain": title, "entity": entity, "entity_plural": entity_plural}


def context_for_project(project: Any) -> dict[str, str]:
    return context_for(project.idea, project.title)


def context_for_ticket(ticket: Any) -> dict[str, str]:
    return context_for_project(ticket.sprint.project)


def _substitute_known(text: str, context: dict[str, str]) -> str:
    """Replace only the placeholders this module knows about, leaving code alone."""
    return _PLACEHOLDER_RE.sub(
        lambda match: str(context.get(match.group(1), match.group(0))), text
    )


def fill(value: Any, context: dict[str, str], *, strict: bool = False) -> Any:
    """Resolve placeholders anywhere inside `value` (str/list/dict, recursively).

    With `strict=True` an unresolved placeholder raises `SpecInterpolationError`
    instead of being returned quietly, which is the mode every spec writer uses.
    """
    if isinstance(value, str):
        try:
            filled = value.format(**context)
        except (KeyError, IndexError, ValueError):
            # `format` cannot parse this string (literal braces from code) or was
            # handed a name it does not know. Substituting the vocabulary
            # directly resolves the placeholder without touching the braces that
            # belong to the code around it.
            filled = _substitute_known(value, context)
        if strict:
            missing = unresolved_placeholders(filled)
            if missing:
                raise SpecInterpolationError(
                    f"unresolved placeholder(s) {missing} remain in {filled[:120]!r}; "
                    f"the context supplied {sorted(context)}"
                )
        return filled
    if isinstance(value, list):
        return [fill(v, context, strict=strict) for v in value]
    if isinstance(value, dict):
        return {k: fill(v, context, strict=strict) for k, v in value.items()}
    return value


def unresolved_placeholders(value: Any) -> list[str]:
    """Every placeholder name still present anywhere in `value`, sorted."""
    found: set[str] = set()

    def walk(node: Any) -> None:
        if isinstance(node, str):
            found.update(_PLACEHOLDER_RE.findall(node))
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for item in node.values():
                walk(item)

    walk(value)
    return sorted(found)


def selector_leak(selector: Optional[str]) -> Optional[str]:
    """The templating leak in `selector`, or None when it is safe to query.

    Called before a selector reaches `querySelector`/`querySelectorAll`/
    `matches`/`closest`. A `{...}` in a selector is never valid CSS, so this is
    always our bug and never the learner's.
    """
    if not selector:
        return None
    leaks = _ANY_BRACE_RE.findall(selector)
    if not leaks:
        return None
    return (
        f"the selector {selector!r} still contains the unresolved template "
        f"placeholder(s) {', '.join(sorted(set(leaks)))}"
    )


def build_validation_spec(template: dict[str, Any], context: dict[str, str]) -> dict[str, Any]:
    """The only sanctioned way to turn a ticket template into a stored spec.

    Checks are interpolated strictly. The behaviour harness is *not* — its
    expressions are literal JavaScript whose braces would be mangled — so it is
    asserted to be placeholder-free instead; a behaviour spec that needs the
    domain noun is a template bug to fix at the source, not to paper over here.
    """
    checks = fill(template.get("checks", []) or [], context, strict=True)
    behaviour = template.get("behaviour") or {}
    leaked = unresolved_placeholders(behaviour)
    if leaked:
        raise SpecInterpolationError(
            f"behaviour spec carries placeholder(s) {leaked}; behaviour harnesses are "
            "literal JavaScript and are never interpolated"
        )
    return {"checks": checks, "behaviour": behaviour}
