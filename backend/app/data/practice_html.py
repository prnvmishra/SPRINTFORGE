"""HTML-layer practice modules.

Kept separate from `practice_modules.py` so each layer's catalogue can grow
without turning one file into a thousand-line wall. Registered by
`practice_modules.py` via `extend`, which also enforces unique ids.

Authoring rules that the checks below follow deliberately:

* Every check is either mapped to the requirement it proves
  (`requirement_index` / `requirement_indexes`) or declared a `precondition`.
  The "N of M requirements met" ratio is derived from that mapping, so an
  unmapped check would silently drift from the panel the learner reads.
* Checks assert *relationships*, not mere existence: an element sits inside the
  right parent, a `<label for>` matches an input `id`, a `<th>` carries
  `scope`, an `alt` is present and long enough to be a real description. A
  requirement that could only be graded by "does this tag appear anywhere" is
  restated until it can be graded honestly.
* Negative checks (`not_regex`) close the obvious cheats: missing `alt`, a
  `<th>` without `scope`, `href="#"`, `<div class="header">` soup, a second
  `<h1>`, an `aria-label` too short to name anything.
* Starter files contain the surrounding page and a TODO, never the answer.
  No `solution_files` are shipped for these modules.
"""

from __future__ import annotations

from typing import Any


def _empty_behaviour() -> dict[str, Any]:
    """HTML modules are graded entirely by layer 1 (static structure)."""
    return {"prelude": "", "assertions": []}


# Reused negative patterns -------------------------------------------------

#: An <img> tag that has no alt attribute at all.
IMG_WITHOUT_ALT = r"<img(?![^>]*\balt\s*=)[^>]*>"
#: A non-empty alt that is too short to describe anything (1-14 characters).
#: alt="" stays legal so decorative images can still be marked as such.
ALT_TOO_SHORT = r"alt\s*=\s*[\"'][^\"']{1,14}[\"']"
#: alt text that is really a filename.
ALT_IS_FILENAME = r"alt\s*=\s*[\"'][^\"']*\.(?:png|jpe?g|gif|webp|svg|avif)[\"']"


HTML_MODULES: list[dict[str, Any]] = [
    # ------------------------------------------------------------------ 1
    {
        "id": "html-document-skeleton",
        "title": "Bakery Landing Page — Document Skeleton & Metadata",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 1,
        "estimated_minutes": 15,
        "summary": (
            "The team has copy for a new bakery landing page but no page to put it in. "
            "Write the document shell: doctype, language, encoding, viewport, title and "
            "description, so the page renders correctly and is shareable."
        ),
        "problem_statement": (
            "Marketing is about to launch the landing page for Rye & Ember Bakery. The "
            "file you are given is empty apart from a TODO. Build the complete HTML "
            "document shell around the content.\n\n"
            "This is the metadata that decides how the page renders on a phone, which "
            "language a screen reader announces it in, and what a search result or a "
            "shared link looks like. Getting it wrong is invisible in the browser and "
            "very visible in production."
        ),
        "constraints": [
            "Write only in index.html; there is no CSS or JS layer in this task.",
            "The doctype must be the first thing in the file (no blank markup before it).",
            "The <title> must be at least 10 characters and must not be left as \"Document\".",
            "The meta description content must be at least 40 characters — a real sentence.",
            "The viewport meta must set width=device-width.",
        ],
        "requirements": [
            "Open the file with <!DOCTYPE html> and a root <html> element carrying a lang attribute (e.g. lang=\"en\")",
            "Add a <head> containing <meta charset=\"utf-8\">",
            "Add a responsive viewport meta tag: name=\"viewport\" with content including width=device-width",
            "Give the page a descriptive <title> inside <head>: at least 10 characters, not \"Document\"",
            "Add <meta name=\"description\"> whose content is a real sentence of at least 40 characters",
            "Put the visible content in <body>, starting with an <h1> containing the bakery name",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": (
                "<!-- TODO: build the whole document shell here.\n"
                "     Nothing exists yet: no doctype, no root element, no head, no body.\n"
                "     Copy to place inside the body once the shell exists:\n"
                "       Bakery name: Rye and Ember Bakery\n"
                "       Tagline paragraph: Sourdough baked overnight, sold before noon.\n"
                "-->\n"
            )
        },
        "checks": [
            {
                "id": "file_not_empty",
                "precondition": True,
                "requirement_index": None,
                "type": "non_empty",
                "file": "index.html",
                "label": "index.html is not empty",
                "concept": "document structure",
                "hint": "Write your markup in index.html.",
            },
            {
                "id": "doctype_first",
                "requirement_index": 0,
                "type": "regex",
                "file": "index.html",
                "pattern": r"\A\s*<!DOCTYPE\s+html\s*>",
                "ignore_case": True,
                "label": "The file starts with <!DOCTYPE html>",
                "concept": "document structure",
                "hint": "The doctype must be the very first thing in the file, before any element or comment.",
            },
            {
                "id": "html_lang",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "html",
                "with_attributes": {"lang": "*"},
                "label": "<html> declares the page language with a non-empty lang",
                "concept": "document structure",
                "hint": "Screen readers pick pronunciation from <html lang=\"...\">; an empty lang tells them nothing.",
            },
            {
                "id": "charset",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "meta",
                "with_attributes": {"charset": "utf-8"},
                "label": "<meta charset=\"utf-8\"> is declared",
                "concept": "metadata",
                "hint": "Without a character encoding the browser guesses, and accented characters break.",
            },
            {
                "id": "charset_in_head",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "meta",
                "parent": "head",
                "label": "Metadata lives inside <head>",
                "concept": "metadata",
                "hint": "meta elements belong in <head>, not in <body>.",
            },
            {
                "id": "viewport",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "meta",
                "with_attributes": {"name": "viewport", "content": "width=device-width"},
                "label": "A viewport meta tag sets width=device-width",
                "concept": "responsive metadata",
                "hint": "Both attributes must be on the same meta element: name=\"viewport\" and a content value containing width=device-width.",
            },
            {
                "id": "title_present",
                "requirement_index": 3,
                "type": "html_nested",
                "file": "index.html",
                "selector": "title",
                "parent": "head",
                "label": "<title> is inside <head>",
                "concept": "metadata",
                "hint": "The title element belongs in the head.",
            },
            {
                "id": "title_meaningful",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<title[^>]*>\s*(?!Document\s*<)[^<]{10,}</title>",
                "label": "<title> is a real title (10+ characters, not \"Document\")",
                "concept": "metadata",
                "hint": "The title is the tab label and the search-result headline: name the business and what the page is.",
            },
            {
                "id": "description_meta",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "meta",
                "with_attributes": {"name": "description", "content": "*"},
                "label": "<meta name=\"description\"> exists with a non-empty content",
                "concept": "metadata",
                "hint": "One meta element needs both name=\"description\" and a content attribute.",
            },
            {
                "id": "description_length",
                "requirement_index": 4,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<meta[^>]*(?:name\s*=\s*[\"']description[\"'][^>]*content\s*=\s*[\"'][^\"']{40,}[\"']"
                    r"|content\s*=\s*[\"'][^\"']{40,}[\"'][^>]*name\s*=\s*[\"']description[\"'])"
                ),
                "label": "The description is a real sentence (40+ characters)",
                "concept": "metadata",
                "hint": "A two-word description is not a summary. Write the sentence you would want to see under a search result.",
            },
            {
                "id": "h1_in_body",
                "requirement_index": 5,
                "type": "html_nested",
                "file": "index.html",
                "selector": "h1",
                "parent": "body",
                "label": "An <h1> is inside <body>",
                "concept": "document structure",
                "hint": "Visible content goes in <body>; the page's main heading is an <h1>.",
            },
            {
                "id": "h1_has_text",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "h1",
                "non_empty_text": True,
                "label": "The <h1> contains the bakery name",
                "concept": "headings hierarchy",
                "hint": "An empty heading is not a heading — put the visible name inside it.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 2
    {
        "id": "html-heading-outline",
        "title": "Employee Handbook — Heading Outline",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 2,
        "estimated_minutes": 18,
        "summary": (
            "A handbook page was pasted in as bold text with no headings, so nobody can "
            "navigate it. Rebuild it as a correct heading outline with body copy."
        ),
        "problem_statement": (
            "The internal handbook page currently fakes its headings with bold text, so "
            "the document outline is flat: assistive technology cannot jump between "
            "sections and the auto-generated table of contents is empty.\n\n"
            "Rebuild the page body as a real outline. One page title, three top-level "
            "sections, and sub-sections under the middle one. Levels may not be skipped, "
            "and no styling element may stand in for a heading."
        ),
        "constraints": [
            "Edit only index.html; the head is already written for you.",
            "Exactly one <h1> on the page.",
            "Do not use <h4>, <h5> or <h6> — this page is only three levels deep.",
            "Do not fake headings with <b>, <big>, <font> or a class named heading/headline/title.",
            "Every heading must contain visible text.",
        ],
        "requirements": [
            "Add exactly one <h1> containing the handbook title, with visible text",
            "Add three <h2> section headings",
            "Add at least two <h3> sub-section headings, appearing after an <h2>",
            "Do not skip heading levels: no <h4>, <h5> or <h6> anywhere on the page",
            "No empty headings, and no element styled to look like a heading instead of being one",
            "Give the sections body copy: at least three non-empty <p> elements, with a <p> following an <h2>",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Employee Handbook</title>
  </head>
  <body>
    <main>
      <!-- TODO: rebuild this page as a real heading outline.
           Sections to cover (wording is up to you):
             1. Working hours
             2. Time off  -> sub-sections: Holiday, Sick leave
             3. Expenses
           Each section needs at least one paragraph of body copy.
      -->
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "h1_present",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "h1",
                "non_empty_text": True,
                "label": "One <h1> with visible text exists",
                "concept": "headings hierarchy",
                "hint": "The page title is the single <h1>; it must contain text.",
            },
            {
                "id": "h1_is_unique",
                "requirement_index": 0,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<h1[^>]*>[\s\S]*<h1[^>]*>",
                "label": "There is only one <h1>",
                "concept": "headings hierarchy",
                "hint": "A second <h1> gives the document two titles. Demote the extra one to <h2>.",
            },
            {
                "id": "three_h2",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "h2",
                "min_count": 3,
                "label": "Three <h2> section headings exist",
                "concept": "headings hierarchy",
                "hint": "Each top-level section of the handbook gets its own <h2>.",
            },
            {
                "id": "two_h3",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "h3",
                "min_count": 2,
                "label": "At least two <h3> sub-sections exist",
                "concept": "headings hierarchy",
                "hint": "Holiday and sick leave are sub-sections of Time off, so they are one level deeper.",
            },
            {
                "id": "h3_follows_h2",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<h2[^>]*>[\s\S]*<h3[^>]*>",
                "label": "An <h3> appears after an <h2> (it nests under a section)",
                "concept": "headings hierarchy",
                "hint": "An <h3> before any <h2> has nothing to be a sub-section of.",
            },
            {
                "id": "no_skipped_levels",
                "requirement_index": 3,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<h[456]\b",
                "label": "No heading levels are skipped (no h4/h5/h6)",
                "concept": "headings hierarchy",
                "hint": "Jumping from <h2> to <h4> breaks the outline. This page needs only h1-h3.",
            },
            {
                "id": "no_empty_heading",
                "requirement_index": 4,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<h([1-6])[^>]*>\s*</h\1>",
                "label": "No heading is left empty",
                "concept": "headings hierarchy",
                "hint": "An empty heading still appears in the outline as a blank entry. Put the section name inside it.",
            },
            {
                "id": "no_fake_heading",
                "requirement_index": 4,
                "type": "not_regex",
                "file": "index.html",
                "pattern": (
                    r"(?:<b>|<b\s|<big\b|<font\b"
                    r"|<(?:p|div|span)[^>]*class\s*=\s*[\"'][^\"']*(?:heading|headline|title))"
                ),
                "label": "No element is styled to impersonate a heading",
                "concept": "semantic html",
                "hint": "Bold text is not a heading: it carries no level and no outline entry. Use h1-h3.",
            },
            {
                "id": "body_copy",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "p",
                "min_count": 3,
                "non_empty_text": True,
                "label": "At least three paragraphs of body copy exist",
                "concept": "elements",
                "hint": "An outline with no prose is a table of contents, not a handbook page.",
            },
            {
                "id": "paragraph_after_section",
                "requirement_index": 5,
                "type": "regex",
                "file": "index.html",
                "pattern": r"</h2>\s*(?:<!--[\s\S]*?-->\s*)*<p(?=[\s>])[^>]*>\s*[^<\s]",
                "label": "A section heading is followed by a paragraph with text",
                "concept": "elements",
                "hint": "Each <h2> should introduce content: put a non-empty <p> straight after it.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 3
    {
        "id": "html-recipe-lists",
        "title": "Recipe Card — Ordered, Unordered and Description Lists",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 1,
        "estimated_minutes": 18,
        "summary": (
            "A recipe was written as one long paragraph with <br> tags. Rebuild it with "
            "the three real list types: ingredients, numbered method, and a facts list."
        ),
        "problem_statement": (
            "The recipe page currently separates every ingredient with a <br>. Visually it "
            "looks like a list; structurally it is one paragraph, so nothing can announce "
            "\"list, 5 items\" or renumber the method when a step is inserted.\n\n"
            "Rebuild the recipe body using the right list type for each job: an unordered "
            "list for ingredients (order does not matter), an ordered list for the method "
            "(order is the whole point), and a description list for the recipe facts, where "
            "each name has a value."
        ),
        "constraints": [
            "Edit only index.html.",
            "The ingredient list must have id=\"ingredients\" and the method list id=\"steps\".",
            "The only direct children of a <ul> or <ol> may be <li> elements.",
            "No <br>-separated pseudo lists.",
            "Every list item must contain visible text.",
        ],
        "requirements": [
            "Build the ingredients as <ul id=\"ingredients\"> containing at least four <li> items",
            "Build the method as <ol id=\"steps\"> containing at least three <li> items",
            "Nest a sub-list: put a <ul> inside one of the ingredient <li> items for its variations",
            "Add a description list <dl> of recipe facts with at least three <dt>/<dd> pairs",
            "No empty list items and no <br>-separated fake list",
            "The only direct children of a list are <li> elements",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Overnight Focaccia — Recipe</title>
  </head>
  <body>
    <main>
      <h1>Overnight Focaccia</h1>

      <h2>Ingredients</h2>
      <!-- TODO: replace the paragraph below with a real unordered list.
           One of the ingredients (the olive oil) has variations that belong in a
           sub-list nested inside its own item.
      -->
      <p>
        500 g flour<br />
        400 ml water<br />
        10 g salt<br />
        4 g dried yeast<br />
        olive oil
      </p>

      <h2>Method</h2>
      <!-- TODO: the steps must be numbered and stay numbered when one is inserted. -->

      <h2>Recipe facts</h2>
      <!-- TODO: prep time, rest time and serves are name/value pairs. -->
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "ingredients_list",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "ul#ingredients",
                "label": "<ul id=\"ingredients\"> exists",
                "concept": "lists",
                "hint": "Ingredients have no meaningful order, so they belong in a <ul>.",
            },
            {
                "id": "ingredients_items",
                "requirement_index": 0,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<ul[^>]*id\s*=\s*[\"']ingredients[\"'][^>]*>(?:[\s\S]*?<li\b){4}",
                "label": "The ingredients list holds at least four items",
                "concept": "lists",
                "hint": "Each ingredient is its own <li> inside the ingredients list.",
            },
            {
                "id": "steps_list",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "ol#steps",
                "label": "<ol id=\"steps\"> exists",
                "concept": "lists",
                "hint": "Method steps are sequential, so the list type must be ordered.",
            },
            {
                "id": "steps_items",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<ol[^>]*id\s*=\s*[\"']steps[\"'][^>]*>(?:[\s\S]*?<li\b){3}",
                "label": "The method list holds at least three items",
                "concept": "lists",
                "hint": "One <li> per step; the browser numbers them for you.",
            },
            {
                "id": "nested_sub_list",
                "requirement_index": 2,
                "type": "html_nested",
                "file": "index.html",
                "selector": "ul",
                "parent": "li",
                "label": "A sub-list is nested inside a list item",
                "concept": "nesting",
                "hint": "A sub-list belongs inside the <li> it qualifies, not between two <li> elements.",
            },
            {
                "id": "description_list",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "dl",
                "label": "A <dl> description list exists",
                "concept": "lists",
                "hint": "Name/value pairs (prep time: 20 minutes) are what <dl> is for.",
            },
            {
                "id": "dt_in_dl",
                "requirement_index": 3,
                "type": "html_nested",
                "file": "index.html",
                "selector": "dt",
                "parent": "dl",
                "label": "<dt> terms are inside the <dl>",
                "concept": "nesting",
                "hint": "<dt> and <dd> are only meaningful as children of a <dl>.",
            },
            {
                "id": "dd_in_dl",
                "requirement_index": 3,
                "type": "html_nested",
                "file": "index.html",
                "selector": "dd",
                "parent": "dl",
                "label": "<dd> descriptions are inside the <dl>",
                "concept": "nesting",
                "hint": "Every term needs its description inside the same <dl>.",
            },
            {
                "id": "three_pairs",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"(?:<dt[^>]*>\s*[^<\s][\s\S]*?<dd[^>]*>\s*[^<\s][\s\S]*?){3}",
                "label": "Three non-empty <dt>/<dd> pairs exist",
                "concept": "lists",
                "hint": "Each fact is a <dt> with its name followed by a <dd> with its value — three of them.",
            },
            {
                "id": "no_empty_items",
                "requirement_index": 4,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<li[^>]*>\s*</li>",
                "label": "No list item is empty",
                "concept": "lists",
                "hint": "An empty <li> is announced as a blank item. Remove it or fill it in.",
            },
            {
                "id": "no_br_pseudo_list",
                "requirement_index": 4,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"(?:<br\s*/?>\s*){2}",
                "label": "No <br>-separated pseudo list remains",
                "concept": "semantic html",
                "hint": "Repeated <br> only moves text down a line; it creates no list for assistive technology.",
            },
            {
                "id": "only_li_children",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<(?:ul|ol)[^>]*>\s*(?!\s*(?:<li\b|<!--))\S",
                "label": "Lists contain only <li> children",
                "concept": "nesting",
                "hint": "A <p> or <div> directly inside <ul>/<ol> is invalid: wrap that content in an <li>.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 4
    {
        "id": "html-site-navigation",
        "title": "Docs Site — Primary Navigation and Link Semantics",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_semantics",
        "technology": "HTML",
        "difficulty": 2,
        "estimated_minutes": 22,
        "summary": (
            "Build the primary navigation for a documentation site: a labelled landmark, "
            "a real list of links, the current page marked, a safe external link and a "
            "working skip link."
        ),
        "problem_statement": (
            "The docs site has navigation built from loose <a> tags inside a <div>. "
            "Keyboard users have to tab through every nav link before reaching the "
            "content, screen-reader users cannot tell which page they are on, and one "
            "external link opens a new tab with a security hole.\n\n"
            "Rebuild the navigation properly. The page you are editing is the Pricing "
            "page, so Pricing is the current page. Section ids are fixed by the design: "
            "the in-page anchor target is id=\"pricing\" and the content landmark is "
            "<main id=\"main\">."
        ),
        "constraints": [
            "Edit only index.html.",
            "The skip link must be the first element inside <body>.",
            "The in-page link must point at #pricing, and an element with id=\"pricing\" must exist.",
            "The external link must carry both target=\"_blank\" and rel containing noopener and noreferrer.",
            "No href=\"#\" placeholders, no empty link text, no \"click here\" link text.",
        ],
        "requirements": [
            "Wrap the navigation links in a <nav> element with a non-empty aria-label",
            "Inside the nav, use a <ul> whose <li> items each contain one <a href>, with at least four items",
            "Mark the current page's link with aria-current=\"page\"",
            "Add an in-page link to href=\"#pricing\" and make sure an element with id=\"pricing\" exists",
            "The external link must have target=\"_blank\" and rel containing both noopener and noreferrer",
            "Add a \"Skip to main content\" link as the first element in <body>, pointing at #main, and give the content landmark <main id=\"main\">",
            "No placeholder href=\"#\", no empty link text and no \"click here\" wording",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pricing — Orbit Docs</title>
  </head>
  <body>
    <!-- TODO: a skip link belongs here, before anything else in the body. -->

    <header>
      <!-- TODO: build the primary navigation landmark here.
           Destinations: Home (index.html), Guides (guides.html),
           Pricing (this page), Changelog (changelog.html),
           and the community forum at https://community.example.com
      -->
    </header>

    <!-- TODO: the content landmark and the #pricing section are missing. -->
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "nav_labelled",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "nav",
                "with_attributes": {"aria-label": "*"},
                "label": "<nav> exists and carries a non-empty aria-label",
                "concept": "landmarks",
                "hint": "A page can have several navigations; the label is how a user tells them apart.",
            },
            {
                "id": "list_in_nav",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "ul",
                "parent": "nav",
                "label": "The nav links are in a <ul> inside the <nav>",
                "concept": "landmarks",
                "hint": "A list tells the user how many destinations there are before they start tabbing.",
            },
            {
                "id": "links_in_items",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "a",
                "parent": "li",
                "label": "Each navigation link sits inside an <li>",
                "concept": "nesting",
                "hint": "Loose <a> elements inside a <ul> are invalid; one link per list item.",
            },
            {
                "id": "four_nav_items",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<nav[\s\S]*?(?:<li\b[\s\S]*?){4}[\s\S]*?</nav>",
                "label": "The nav holds at least four list items",
                "concept": "lists",
                "hint": "There are four internal destinations plus the forum link.",
            },
            {
                "id": "aria_current_present",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "[aria-current]",
                "with_attributes": {"aria-current": "page"},
                "label": "An element declares aria-current=\"page\"",
                "concept": "aria",
                "hint": "The current page needs aria-current=\"page\" in the rendered markup, not in a comment.",
            },
            {
                "id": "aria_current",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<a[^>]*aria-current\s*=\s*[\"']page[\"']",
                "label": "The current page's link has aria-current=\"page\"",
                "concept": "aria",
                "hint": "Styling the current link is not enough — aria-current is what announces it.",
            },
            {
                "id": "fragment_link",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "a",
                "with_attributes": {"href": "#pricing"},
                "label": "A link points at the in-page target #pricing",
                "concept": "links",
                "hint": "An in-page link uses a fragment href: href=\"#pricing\".",
            },
            {
                "id": "fragment_target",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "#pricing",
                "label": "An element with id=\"pricing\" exists to jump to",
                "concept": "links",
                "hint": "A fragment link with no matching id does nothing. Give the section that id.",
            },
            {
                "id": "external_noopener",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "a",
                "with_attributes": {"href": "https://", "target": "_blank", "rel": "noopener"},
                "label": "The external link has target=\"_blank\" and rel including noopener",
                "concept": "links",
                "hint": "All three attributes must be on the same <a>: without rel=noopener the new tab can reach back into this page.",
            },
            {
                "id": "external_noreferrer",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "a",
                "with_attributes": {"href": "https://", "target": "_blank", "rel": "noreferrer"},
                "label": "The same external link's rel also includes noreferrer",
                "concept": "links",
                "hint": "rel=\"noopener noreferrer\" — both tokens, one attribute.",
            },
            {
                "id": "main_landmark",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "main#main",
                "label": "<main id=\"main\"> exists as the skip target",
                "concept": "landmarks",
                "hint": "The skip link needs something to land on: give <main> the id=\"main\".",
            },
            {
                "id": "skip_link_target",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "a",
                "with_attributes": {"href": "#main"},
                "label": "A skip link points at #main",
                "concept": "accessibility",
                "hint": "The skip link is a normal anchor: <a href=\"#main\">Skip to main content</a>.",
            },
            {
                "id": "skip_link_first",
                "requirement_index": 5,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<body[^>]*>\s*(?:<!--[\s\S]*?-->\s*)*<a[^>]*href\s*=\s*[\"']#main[\"'][^>]*>\s*[^<\s]",
                "label": "The skip link is the first element in <body> and has visible text",
                "concept": "accessibility",
                "hint": "A skip link placed after the nav skips nothing: it must be the first focusable thing on the page.",
            },
            {
                "id": "no_placeholder_href",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"href\s*=\s*[\"'](?:#|javascript:)?[\"']|href\s*=\s*[\"']#[\"']",
                "label": "No placeholder or empty href remains",
                "concept": "links",
                "hint": "href=\"#\" is a link to nowhere. Point it at the real destination.",
            },
            {
                "id": "no_empty_link_text",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<a(?=[\s>])[^>]*>\s*</a>",
                "label": "No link has empty text",
                "concept": "links",
                "hint": "A link with no text has no accessible name; say where it goes.",
            },
            {
                "id": "no_click_here",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r">\s*(?:[Cc]lick [Hh]ere|CLICK HERE|[Rr]ead [Mm]ore|[Hh]ere)\s*<",
                "label": "No \"click here\" style link text",
                "concept": "links",
                "hint": "Link text is read out of context, so it must describe the destination, not the gesture.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 5
    {
        "id": "html-image-gallery-alt",
        "title": "Product Gallery — Images, Alt Text and Layout Stability",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 2,
        "estimated_minutes": 20,
        "summary": (
            "Mark up a product gallery: three content images with real alt text, one "
            "decorative image correctly hidden, intrinsic sizes to stop layout shift, and "
            "lazy loading below the fold."
        ),
        "problem_statement": (
            "The gallery on the product page fails the accessibility audit and the "
            "performance budget at the same time: alt attributes are missing or contain "
            "file names, nothing declares intrinsic size (so the page jumps as images "
            "arrive), and every image loads eagerly.\n\n"
            "Rebuild the gallery. Three images show the product and need descriptions a "
            "person who cannot see them would find useful. One image is a purely "
            "decorative divider and must be hidden from assistive technology rather than "
            "described."
        ),
        "constraints": [
            "Edit only index.html.",
            "Every <img> must have an alt attribute — including the decorative one.",
            "Content alt text must be at least 15 characters and must not be a file name.",
            "The decorative divider image has class=\"divider\" and alt=\"\" (empty on purpose).",
            "Every <img> needs width and height attributes.",
        ],
        "requirements": [
            "Add four <img> elements, each with src, width and height attributes",
            "Give each of the three content images descriptive alt text of at least 15 characters (never a file name)",
            "Mark the decorative image (class=\"divider\") with an empty alt=\"\" so it is skipped",
            "Give at least two below-the-fold images loading=\"lazy\"",
            "Structure the gallery as <ul class=\"gallery\"> with each content image inside an <li>",
            "No <img> may be missing its alt attribute",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Kettle 900 — Gallery</title>
  </head>
  <body>
    <main>
      <h1>Kettle 900</h1>

      <!-- TODO: build the gallery here.
           Available assets (use these paths, sizes are 640x480):
             /img/kettle-front.jpg   - the kettle seen from the front, lid closed
             /img/kettle-pouring.jpg - the kettle pouring water into a cup
             /img/kettle-base.jpg    - the kettle sitting on its charging base
             /img/divider.svg        - a decorative wave used between rows (300x12)
           The first image is above the fold; the rest are not.
      -->
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "four_images",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "img",
                "min_count": 4,
                "with_attributes": {"src": "*"},
                "label": "Four images exist, with src attributes",
                "concept": "images",
                "hint": "Three product shots plus the decorative divider.",
            },
            {
                "id": "all_have_width",
                "requirement_index": 0,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<img(?![^>]*\bwidth\s*=)[^>]*>",
                "label": "Every <img> declares a width",
                "concept": "layout stability",
                "hint": "Without width/height the browser cannot reserve space, so the page jumps when the image loads.",
            },
            {
                "id": "all_have_height",
                "requirement_index": 0,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<img(?![^>]*\bheight\s*=)[^>]*>",
                "label": "Every <img> declares a height",
                "concept": "layout stability",
                "hint": "Declare both intrinsic dimensions so the aspect ratio is known before the bytes arrive.",
            },
            {
                "id": "alt_present_everywhere",
                "requirement_indexes": [1, 5],
                "type": "not_regex",
                "file": "index.html",
                "pattern": IMG_WITHOUT_ALT,
                "label": "No <img> is missing its alt attribute",
                "concept": "alt text",
                "hint": "A missing alt makes a screen reader read the file name. An intentionally empty alt=\"\" is different from no alt at all.",
            },
            {
                "id": "alt_is_descriptive",
                "requirement_index": 1,
                "type": "not_regex",
                "file": "index.html",
                "pattern": ALT_TOO_SHORT,
                "label": "No alt text is too short to describe the image (1-14 characters)",
                "concept": "alt text",
                "hint": "Describe what a sighted user gains from the image, in at least 15 characters. alt=\"\" stays allowed for the decorative one.",
            },
            {
                "id": "alt_not_filename",
                "requirement_index": 1,
                "type": "not_regex",
                "file": "index.html",
                "pattern": ALT_IS_FILENAME,
                "label": "No alt text is a file name",
                "concept": "alt text",
                "hint": "\"kettle-front.jpg\" tells the listener nothing. Describe the picture.",
            },
            {
                "id": "content_images_have_alt",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "img",
                "min_count": 3,
                "with_attributes": {"alt": "*"},
                "label": "Rendered images carry non-empty alt text",
                "concept": "alt text",
                "hint": "The alt has to be on a real <img> element, not described in a comment.",
            },
            {
                "id": "three_described_images",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": r"(?:<img[^>]*alt\s*=\s*[\"'][^\"']{15,}[\"'][\s\S]*?){3}",
                "label": "Three images carry descriptive alt text",
                "concept": "alt text",
                "hint": "All three product shots need their own description — they show different things.",
            },
            {
                "id": "divider_image",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "img.divider",
                "with_attributes": {"src": "*"},
                "label": "The decorative divider image exists with class=\"divider\"",
                "concept": "images",
                "hint": "Use class=\"divider\" on the decorative image so the audit can tell it apart.",
            },
            {
                "id": "divider_alt_empty",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<img[^>]*(?:class\s*=\s*[\"'][^\"']*\bdivider\b[^\"']*[\"'][^>]*alt\s*=\s*[\"'][\"']"
                    r"|alt\s*=\s*[\"'][\"'][^>]*class\s*=\s*[\"'][^\"']*\bdivider\b)"
                ),
                "label": "The divider image is hidden with an empty alt=\"\"",
                "concept": "alt text",
                "hint": "Decoration is not content: alt=\"\" removes it from the accessibility tree instead of describing a wave.",
            },
            {
                "id": "lazy_attribute_present",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "img",
                "with_attributes": {"loading": "lazy"},
                "label": "At least one rendered <img> carries loading=\"lazy\"",
                "concept": "performance",
                "hint": "The attribute has to be on a real <img> element in the document.",
            },
            {
                "id": "lazy_loading",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"(?:<img[^>]*loading\s*=\s*[\"']lazy[\"'][\s\S]*?){2}",
                "label": "At least two images use loading=\"lazy\"",
                "concept": "performance",
                "hint": "Images below the fold should not compete with the first paint. The above-the-fold one stays eager.",
            },
            {
                "id": "gallery_list",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "ul.gallery",
                "label": "<ul class=\"gallery\"> wraps the gallery",
                "concept": "lists",
                "hint": "A gallery is a list of items, so the count can be announced.",
            },
            {
                "id": "image_in_item",
                "requirement_index": 4,
                "type": "html_nested",
                "file": "index.html",
                "selector": "img",
                "parent": "li",
                "label": "Gallery images sit inside <li> items",
                "concept": "nesting",
                "hint": "Each product image belongs in its own list item.",
            },
            {
                "id": "item_in_gallery",
                "requirement_index": 4,
                "type": "html_nested",
                "file": "index.html",
                "selector": "li",
                "parent": "ul",
                "label": "The gallery items are children of the list",
                "concept": "nesting",
                "hint": "<li> is only valid inside <ul> or <ol>.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 6
    {
        "id": "html-data-table",
        "title": "Quarterly Report — Accessible Data Table",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 3,
        "estimated_minutes": 25,
        "summary": (
            "Rebuild a sales table so every cell can be traced to its row and column "
            "header: caption, thead/tbody/tfoot, and scope on every header cell."
        ),
        "problem_statement": (
            "The quarterly sales table is currently a grid of <td> cells with a bold "
            "first row. On screen it reads fine; with a screen reader every cell is just "
            "a number, because no cell is a header and nothing has a scope.\n\n"
            "Rebuild the table so that reading a single cell also announces which region "
            "and which quarter it belongs to. The data has four columns of figures "
            "(Region, Q1, Q2, Q3), three regions, and a totals row."
        ),
        "constraints": [
            "Edit only index.html.",
            "Every <th> must carry a scope attribute.",
            "Column headers use scope=\"col\"; the first cell of each body row uses scope=\"row\".",
            "No presentational table attributes (border, cellpadding, cellspacing, align).",
            "The caption must be at least 10 characters of real description.",
        ],
        "requirements": [
            "Add a <table> with a <caption> of at least 10 characters describing the data",
            "Put the header row in a <thead> with at least four <th scope=\"col\"> cells",
            "Put the data in a <tbody> containing at least three rows",
            "Start every body row with a <th scope=\"row\"> naming the region",
            "Add a <tfoot> containing the totals row with real content",
            "No <th> without scope, and no presentational table attributes",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Quarterly Sales — Report</title>
  </head>
  <body>
    <main>
      <h1>Quarterly sales</h1>

      <!-- TODO: rebuild this as an accessible data table.
           Columns: Region, Q1, Q2, Q3
           Rows:    North  120  138  151
                    South   96  104   99
                    Europe 210  225  243
           Totals:         426  467  493
           Nothing below is markup you can reuse; start from <table>.
      -->
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "table_exists",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "table",
                "label": "A <table> exists",
                "concept": "tables",
                "hint": "Tabular data belongs in a <table>, not in stacked <div> rows.",
            },
            {
                "id": "caption_in_table",
                "requirement_index": 0,
                "type": "html_nested",
                "file": "index.html",
                "selector": "caption",
                "parent": "table",
                "label": "A <caption> is the table's first child",
                "concept": "tables",
                "hint": "<caption> must be inside the <table> it names.",
            },
            {
                "id": "caption_describes_data",
                "requirement_index": 0,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<caption[^>]*>\s*[^<]{10,}",
                "label": "The caption describes the data (10+ characters)",
                "concept": "tables",
                "hint": "The caption is the table's accessible name: say what the numbers are and for when.",
            },
            {
                "id": "thead_exists",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "thead",
                "label": "A <thead> groups the header row",
                "concept": "tables",
                "hint": "Separating <thead> from <tbody> tells the browser which row is the header.",
            },
            {
                "id": "th_in_thead",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "th",
                "parent": "thead",
                "label": "Header cells are <th> inside <thead>",
                "concept": "tables",
                "hint": "A bold <td> is still a data cell. Column headers must be <th>.",
            },
            {
                "id": "four_col_headers",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<thead[\s\S]*?(?:<th(?=[\s>])[^>]*scope\s*=\s*[\"']col[\"'][\s\S]*?){4}[\s\S]*?</thead>",
                "label": "Four column headers use scope=\"col\"",
                "concept": "tables",
                "hint": "scope=\"col\" is what binds every cell below to this header.",
            },
            {
                "id": "tbody_exists",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "tbody",
                "label": "A <tbody> holds the data rows",
                "concept": "tables",
                "hint": "Group the data rows in <tbody> so they are distinct from header and footer.",
            },
            {
                "id": "three_body_rows",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<tbody[\s\S]*?(?:<tr\b[\s\S]*?){3}[\s\S]*?</tbody>",
                "label": "The body has at least three rows",
                "concept": "tables",
                "hint": "One row per region: North, South, Europe.",
            },
            {
                "id": "row_header_cells",
                "requirement_index": 3,
                "type": "html_nested",
                "file": "index.html",
                "selector": "th",
                "parent": "tbody",
                "label": "The body rows contain <th> header cells",
                "concept": "tables",
                "hint": "The region name in each data row must be a <th> inside <tbody>, not a <td>.",
            },
            {
                "id": "row_headers",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<tbody[\s\S]*?"
                    r"(?:<tr[^>]*>\s*(?:<!--[\s\S]*?-->\s*)*<th(?=[\s>])[^>]*scope\s*=\s*[\"']row[\"'][\s\S]*?){3}"
                ),
                "label": "All three body rows start with a <th scope=\"row\">",
                "concept": "tables",
                "hint": "The region name is a header for its row, not data. scope=\"row\" binds the figures to it.",
            },
            {
                "id": "tfoot_exists",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "tfoot",
                "label": "A <tfoot> exists",
                "concept": "tables",
                "hint": "Summary rows belong in <tfoot>, which keeps them out of the data set.",
            },
            {
                "id": "tfoot_has_totals",
                "requirement_index": 4,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<tfoot[\s\S]*?<t[dh](?=[\s>])[^>]*>\s*[^<\s][\s\S]*?</tfoot>",
                "label": "The footer row contains real cells with content",
                "concept": "tables",
                "hint": "An empty <tfoot> is worse than none: put the totals in it.",
            },
            {
                "id": "every_th_scoped",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<th(?=[\s>])(?![^>]*\bscope\s*=)[^>]*>",
                "label": "Every <th> carries a scope attribute",
                "concept": "tables",
                "hint": "A <th> without scope leaves the browser guessing whether it heads a row or a column.",
            },
            {
                "id": "no_presentational_attrs",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<table[^>]*\s(?:border|cellpadding|cellspacing|align)\s*=",
                "label": "No presentational attributes on <table>",
                "concept": "semantic html",
                "hint": "border/cellpadding are layout-era attributes; presentation belongs in CSS.",
            },
            # --- rendered: markup that parses is not the same as markup that
            # renders. These load the page in a browser and measure it.
            {
                "id": "table_renders_as_table",
                "requirement_index": 0,
                "type": "render_computed_style",
                "selector": "table",
                "property": "display",
                "value_in": ["table", "inline-table"],
                "label": "The table renders as a real table box",
                "concept": "tables",
                "hint": (
                    "Loaded in a browser: a <table> that has been hidden or overridden to "
                    "display as blocks no longer conveys rows and columns."
                ),
            },
            {
                "id": "caption_renders_visibly",
                "requirement_index": 0,
                "type": "render_visible",
                "selector": "caption",
                "non_empty": True,
                "min_height": 8,
                "label": "The caption renders visibly with real text",
                "concept": "tables",
                "hint": (
                    "A caption that is present in the source but hidden, collapsed or "
                    "empty tells a sighted reader nothing."
                ),
            },
            {
                "id": "body_cells_render_in_rows",
                "requirement_index": 2,
                "type": "render_row_layout",
                "selector": "tbody tr",
                "min_children": 4,
                "max_rows": 1,
                "label": "Each body row renders its four cells side by side",
                "concept": "tables",
                "hint": (
                    "Measured from the painted cell boxes: the region and its three "
                    "quarters must share one row."
                ),
            },
            {
                "id": "row_headers_render",
                "requirement_index": 3,
                "type": "render_visible",
                "selector": "tbody th",
                "min_count": 3,
                "non_empty": True,
                "label": "Every row header renders with a visible region name",
                "concept": "tables",
                "hint": "An empty or hidden <th scope=\"row\"> heads nothing.",
            },
            {
                "id": "tfoot_renders",
                "requirement_index": 4,
                "type": "render_visible",
                "selector": "tfoot",
                "non_empty": True,
                "min_height": 8,
                "label": "The totals row renders visibly",
                "concept": "tables",
                "hint": "The footer has to be on the page, not just in the file.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 7
    {
        "id": "html-workshop-signup-form",
        "title": "Workshop Signup — Labels, Controls and Grouping",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_basics",
        "technology": "HTML",
        "difficulty": 3,
        "estimated_minutes": 30,
        "summary": (
            "Build a signup form where every control has a real label bound to it, the "
            "radio group is grouped by a fieldset and legend, and the browser can "
            "validate before submit."
        ),
        "problem_statement": (
            "The workshop signup form was built with placeholders instead of labels. The "
            "placeholder disappears as soon as the user types, autofill misfires, and "
            "clicking a caption does not focus its field. The radio buttons have no group "
            "name, so nothing says what the choice is about.\n\n"
            "Rebuild the form. Field ids are fixed by the analytics contract and must be "
            "used exactly: fullName, email, session, ticketStandard, ticketStudent, terms."
        ),
        "constraints": [
            "Edit only index.html.",
            "Use these exact ids: fullName, email, session, ticketStandard, ticketStudent, terms.",
            "Every label must be associated with its control using for=\"<id>\" — wrapping alone is not accepted here.",
            "Every visible control must have an id; placeholders may not replace labels.",
            "Do not lay the form out with a <table>.",
        ],
        "requirements": [
            "Wrap the controls in a <form> with method=\"post\" and an action",
            "Add a text input id=\"fullName\" name=\"fullName\" type=\"text\" required, with a non-empty <label for=\"fullName\">",
            "Add an email input id=\"email\" name=\"email\" type=\"email\" required, with a non-empty <label for=\"email\">",
            "Add <select id=\"session\"> with a <label for=\"session\"> and at least three <option> elements that each have a value",
            "Group the ticket radios in a <fieldset> with a non-empty <legend>: inputs id=\"ticketStandard\" and id=\"ticketStudent\", both type=\"radio\" name=\"ticket\", each with its own label",
            "Add a checkbox id=\"terms\" with a <label for=\"terms\">, and a <button type=\"submit\"> with visible text",
            "Every visible control has an id, every label has a for attribute, and no <table> is used for layout",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Workshop signup</title>
  </head>
  <body>
    <main>
      <h1>Reserve your seat</h1>

      <!-- TODO: build the signup form here. It posts to /api/signup.
           Fields required by the analytics contract (ids are fixed):
             fullName        - text, required
             email           - email, required
             session         - select: Morning / Afternoon / Evening
             ticket          - radio group: ticketStandard, ticketStudent
             terms           - checkbox: accept the code of conduct
           Then a submit button.
      -->
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "form_posts",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "form",
                "with_attributes": {"method": "post", "action": "*"},
                "label": "<form> has method=\"post\" and an action",
                "concept": "forms",
                "hint": "A signup changes server state, so it posts; the action says where.",
            },
            {
                "id": "name_input",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "input#fullName",
                "with_attributes": {"type": "text", "name": "fullName"},
                "label": "input#fullName is a text input with name=\"fullName\"",
                "concept": "forms",
                "hint": "The name attribute is what gets submitted; the id is what the label points at.",
            },
            {
                "id": "name_required",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<input[^>]*id\s*=\s*[\"']fullName[\"'][^>]*\brequired\b"
                    r"|<input[^>]*\brequired\b[^>]*id\s*=\s*[\"']fullName[\"']"
                ),
                "label": "input#fullName is required",
                "concept": "forms",
                "hint": "required lets the browser block an empty submit before any JavaScript runs.",
            },
            {
                "id": "name_label",
                "requirement_index": 1,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<label[^>]*for\s*=\s*[\"']fullName[\"'][^>]*>\s*[^<\s][^<]*</label>",
                "label": "<label for=\"fullName\"> exists with visible text",
                "concept": "labels",
                "hint": "for must match the input's id exactly, and the label needs text a user can read and click.",
            },
            {
                "id": "email_input",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "input#email",
                "with_attributes": {"type": "email", "name": "email"},
                "label": "input#email uses type=\"email\" with name=\"email\"",
                "concept": "forms",
                "hint": "type=\"email\" gives free validation and the right mobile keyboard.",
            },
            {
                "id": "email_required",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<input[^>]*id\s*=\s*[\"']email[\"'][^>]*\brequired\b"
                    r"|<input[^>]*\brequired\b[^>]*id\s*=\s*[\"']email[\"']"
                ),
                "label": "input#email is required",
                "concept": "forms",
                "hint": "Add the required attribute to the email field.",
            },
            {
                "id": "email_label",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<label[^>]*for\s*=\s*[\"']email[\"'][^>]*>\s*[^<\s][^<]*</label>",
                "label": "<label for=\"email\"> exists with visible text",
                "concept": "labels",
                "hint": "A placeholder is not a label — it vanishes the moment the field is used.",
            },
            {
                "id": "session_select",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "select#session",
                "label": "<select id=\"session\"> exists",
                "concept": "forms",
                "hint": "A short fixed choice list is a <select>.",
            },
            {
                "id": "session_label",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<label[^>]*for\s*=\s*[\"']session[\"'][^>]*>\s*[^<\s][^<]*</label>",
                "label": "<label for=\"session\"> exists with visible text",
                "concept": "labels",
                "hint": "A select needs a label just as much as a text input does.",
            },
            {
                "id": "session_options",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<select[^>]*id\s*=\s*[\"']session[\"'][^>]*>"
                    r"(?:[\s\S]*?<option[^>]*value\s*=\s*[\"'][^\"']+[\"']){3}[\s\S]*?</select>"
                ),
                "label": "The select holds at least three options that each carry a value",
                "concept": "forms",
                "hint": "Options without a value submit their text, which breaks as soon as the wording changes.",
            },
            {
                "id": "fieldset",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "fieldset",
                "label": "A <fieldset> groups the radio buttons",
                "concept": "forms",
                "hint": "Radios are one question with several answers; the fieldset is the question.",
            },
            {
                "id": "legend_in_fieldset",
                "requirement_index": 4,
                "type": "html_nested",
                "file": "index.html",
                "selector": "legend",
                "parent": "fieldset",
                "label": "A <legend> is inside the <fieldset>",
                "concept": "forms",
                "hint": "The legend is the group's accessible name and must be its first child.",
            },
            {
                "id": "legend_text",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "legend",
                "non_empty_text": True,
                "label": "The <legend> has visible text",
                "concept": "forms",
                "hint": "Name the choice: \"Ticket type\".",
            },
            {
                "id": "radio_standard",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "input#ticketStandard",
                "with_attributes": {"type": "radio", "name": "ticket"},
                "label": "input#ticketStandard is a radio in the \"ticket\" group",
                "concept": "forms",
                "hint": "Radios only behave as one group when they share the same name.",
            },
            {
                "id": "radio_student",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "input#ticketStudent",
                "with_attributes": {"type": "radio", "name": "ticket"},
                "label": "input#ticketStudent is a radio in the same \"ticket\" group",
                "concept": "forms",
                "hint": "Same name, different id and value.",
            },
            {
                "id": "radio_labels",
                "requirement_index": 4,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<label[^>]*for\s*=\s*[\"']ticketStandard[\"'][^>]*>\s*[^<\s][\s\S]*?"
                    r"<label[^>]*for\s*=\s*[\"']ticketStudent[\"'][^>]*>\s*[^<\s]"
                ),
                "label": "Both radios have their own non-empty <label for=...>",
                "concept": "labels",
                "hint": "Each radio needs its own label; the legend names the group, not the options.",
            },
            {
                "id": "terms_checkbox",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "input#terms",
                "with_attributes": {"type": "checkbox"},
                "label": "input#terms is a checkbox",
                "concept": "forms",
                "hint": "A single yes/no agreement is a checkbox, not a radio.",
            },
            {
                "id": "terms_label",
                "requirement_index": 5,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<label[^>]*for\s*=\s*[\"']terms[\"'][^>]*>\s*[^<\s]",
                "label": "<label for=\"terms\"> exists with visible text",
                "concept": "labels",
                "hint": "The label is also the click target that toggles the checkbox.",
            },
            {
                "id": "submit_button",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "button",
                "with_attributes": {"type": "submit"},
                "non_empty_text": True,
                "label": "A <button type=\"submit\"> with visible text ends the form",
                "concept": "forms",
                "hint": "Say what happens: \"Reserve my seat\" beats \"Submit\".",
            },
            {
                "id": "controls_have_ids",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<input(?![^>]*\btype\s*=\s*[\"'](?:hidden|submit|reset)[\"'])(?![^>]*\bid\s*=)[^>]*>",
                "label": "Every visible input has an id a label can point at",
                "concept": "labels",
                "hint": "Without an id, nothing can be bound to the field with for=.",
            },
            {
                "id": "labels_are_bound",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<label(?![^>]*\bfor\s*=)[^>]*>",
                "label": "Every <label> declares what it labels with for=",
                "concept": "labels",
                "hint": "A label with no for and no wrapped control is just text; this task requires explicit for=.",
            },
            {
                "id": "no_table_layout",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<table\b",
                "label": "The form is not laid out with a <table>",
                "concept": "semantic html",
                "hint": "Tables are for data. Form layout is CSS's job.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 8
    {
        "id": "html-landmark-layout",
        "title": "News Homepage — Semantic Landmarks Instead of Div Soup",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_semantics",
        "technology": "HTML",
        "difficulty": 2,
        "estimated_minutes": 22,
        "summary": (
            "Replace a page built from <div class=\"header\"> style wrappers with real "
            "landmarks: header, nav, main, article, aside and footer."
        ),
        "problem_statement": (
            "The news homepage is built entirely from <div> elements with names like "
            "\"header\", \"nav\" and \"main\". The class names mean something to the CSS "
            "and nothing to anyone else: the landmarks menu of a screen reader is empty, "
            "so there is no way to jump to the content.\n\n"
            "Rebuild the page structure with the elements that carry those meanings "
            "natively. Two stories are on the page; each is independently "
            "redistributable, plus there is a \"Most read\" side panel."
        ),
        "constraints": [
            "Edit only index.html.",
            "Exactly one <main> on the page.",
            "The <footer> must not be inside <main>.",
            "Do not name a <div> after a landmark (header/nav/main/footer/sidebar/banner).",
            "Do not add role=\"banner\"/\"navigation\"/\"main\"/\"contentinfo\" — the elements already imply them.",
        ],
        "requirements": [
            "Add a <header> directly inside <body> containing a link with class=\"brand\" and the site name",
            "Put the site navigation in a <nav> inside the header, using a <ul> of <li><a> links",
            "Add exactly one <main> directly inside <body>",
            "Put at least two <article> elements inside <main>, each with its own non-empty <h2>",
            "Add an <aside> inside <main> for the \"Most read\" panel",
            "Add a <footer> outside <main> containing a <small> with the copyright line",
            "Use no landmark-named <div> wrappers and no redundant landmark roles",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>The Daily Signal</title>
  </head>
  <body>
    <!-- TODO: rebuild the page skeleton with real landmarks.
         Content to place (wording is yours):
           Site name: The Daily Signal  (a link, class="brand", to index.html)
           Nav: Home, World, Science, Opinion
           Story 1: "Harbour tunnel opens six months early"
           Story 2: "City tests overnight bus network"
           Side panel: "Most read" with three links
           Footer: copyright line for The Daily Signal
    -->
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "header_landmark",
                "requirement_index": 0,
                "type": "html_nested",
                "file": "index.html",
                "selector": "header",
                "parent": "body",
                "label": "A <header> sits inside <body>",
                "concept": "landmarks",
                "hint": "The page banner is a <header> at the top level of the body.",
            },
            {
                "id": "brand_link",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "a.brand",
                "non_empty_text": True,
                "label": "A link with class=\"brand\" carries the site name",
                "concept": "links",
                "hint": "The masthead links home and must contain the site name as text.",
            },
            {
                "id": "brand_inside_header",
                "requirement_index": 0,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<header[\s\S]*?<a[^>]*class\s*=\s*[\"'][^\"']*\bbrand\b[\s\S]*?</header>",
                "label": "The brand link is inside the <header>",
                "concept": "landmarks",
                "hint": "The site name belongs in the banner, not floating above it.",
            },
            {
                "id": "nav_in_header",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "nav",
                "parent": "header",
                "label": "A <nav> is inside the <header>",
                "concept": "landmarks",
                "hint": "The primary navigation lives in the banner on this design.",
            },
            {
                "id": "nav_list",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "ul",
                "parent": "nav",
                "label": "The nav uses a <ul> of links",
                "concept": "lists",
                "hint": "A list makes the number of destinations knowable.",
            },
            {
                "id": "nav_links_in_items",
                "requirement_index": 1,
                "type": "html_nested",
                "file": "index.html",
                "selector": "a",
                "parent": "li",
                "label": "Nav links sit inside <li> items",
                "concept": "nesting",
                "hint": "One <a> per <li>.",
            },
            {
                "id": "main_exists",
                "requirement_index": 2,
                "type": "html_nested",
                "file": "index.html",
                "selector": "main",
                "parent": "body",
                "label": "A <main> sits directly inside <body>",
                "concept": "landmarks",
                "hint": "<main> holds what is unique to this page.",
            },
            {
                "id": "single_main",
                "requirement_index": 2,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<main[^>]*>[\s\S]*<main[^>]*>",
                "label": "There is only one <main>",
                "concept": "landmarks",
                "hint": "Two main landmarks make \"jump to content\" ambiguous.",
            },
            {
                "id": "two_articles",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "article",
                "min_count": 2,
                "label": "Two <article> elements exist",
                "concept": "landmarks",
                "hint": "Each story stands on its own, so each is an <article>.",
            },
            {
                "id": "articles_in_main",
                "requirement_index": 3,
                "type": "html_nested",
                "file": "index.html",
                "selector": "article",
                "parent": "main",
                "label": "The articles are inside <main>",
                "concept": "nesting",
                "hint": "Page-unique content belongs inside the main landmark.",
            },
            {
                "id": "articles_have_headings",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"(?:<article[^>]*>[\s\S]*?<h2[^>]*>\s*[^<\s][\s\S]*?</article>[\s\S]*?){2}",
                "label": "Each article has its own non-empty <h2>",
                "concept": "headings hierarchy",
                "hint": "An article without a heading has no entry in the outline.",
            },
            {
                "id": "aside_exists",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "aside",
                "label": "An <aside> holds the side panel",
                "concept": "landmarks",
                "hint": "\"Most read\" is tangentially related content: that is what <aside> means.",
            },
            {
                "id": "aside_in_main",
                "requirement_index": 4,
                "type": "html_nested",
                "file": "index.html",
                "selector": "aside",
                "parent": "main",
                "label": "The <aside> is inside <main>",
                "concept": "nesting",
                "hint": "This design places the panel within the page content region.",
            },
            {
                "id": "footer_exists",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "footer",
                "label": "A <footer> exists",
                "concept": "landmarks",
                "hint": "The site-wide footer is a <footer>.",
            },
            {
                "id": "small_in_footer",
                "requirement_index": 5,
                "type": "html_nested",
                "file": "index.html",
                "selector": "small",
                "parent": "footer",
                "label": "The copyright line is a <small> inside the <footer>",
                "concept": "semantic html",
                "hint": "<small> is the element for side comments and legal small print.",
            },
            {
                "id": "footer_outside_main",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<main[^>]*>[\s\S]*<footer[\s\S]*?</footer>[\s\S]*</main>",
                "label": "The <footer> is not nested inside <main>",
                "concept": "landmarks",
                "hint": "A footer inside main stops being the page's contentinfo landmark.",
            },
            {
                "id": "no_landmark_divs",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": (
                    r"<div[^>]*class\s*=\s*[\"'][^\"']*"
                    r"\b(?:header|nav|navbar|main|footer|sidebar|banner)\b"
                ),
                "label": "No <div> is named after a landmark it should be",
                "concept": "semantic html",
                "hint": "If the class name is \"header\", the element should be a <header>.",
            },
            {
                "id": "no_redundant_roles",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"role\s*=\s*[\"'](?:banner|navigation|main|contentinfo|complementary|article)[\"']",
                "label": "No redundant landmark roles are added",
                "concept": "aria",
                "hint": "The first rule of ARIA: do not use ARIA when a native element already says it.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 9
    {
        "id": "html-accessible-disclosure",
        "title": "FAQ Accordion — ARIA Only Where It Is Actually Needed",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_semantics",
        "technology": "HTML",
        "difficulty": 4,
        "estimated_minutes": 30,
        "summary": (
            "Mark up a two-question FAQ accordion with native buttons, correct "
            "aria-expanded/aria-controls wiring, a live status region, and no redundant "
            "ARIA anywhere."
        ),
        "problem_statement": (
            "The FAQ accordion was built from <div role=\"button\"> headers with ARIA "
            "sprinkled on afterwards. It cannot be reached by keyboard, the state is "
            "invisible to assistive technology, and several roles duplicate what the "
            "elements already mean.\n\n"
            "Rebuild the markup. This task is about knowing when ARIA is required and "
            "when it is noise: state (expanded/collapsed) and relationships (which panel "
            "a control owns) genuinely need it, whereas a button being a button does not. "
            "The JavaScript that toggles the panels is already written and expects these "
            "exact ids: buttons faq1-button / faq2-button, panels faq1-panel / faq2-panel, "
            "and a status region with id=\"status\"."
        ),
        "constraints": [
            "Edit only index.html; script.js is already written and must not be changed.",
            "Ids are fixed: faq1-button, faq2-button, faq1-panel, faq2-panel, status, closeHelp.",
            "Both panels start collapsed: hidden on the panel and aria-expanded=\"false\" on its button.",
            "No role=\"button\", no role on a <ul>, no aria-hidden on an interactive element.",
            "The icon-only button's aria-label must be at least four characters.",
        ],
        "requirements": [
            "Each question is a native <button type=\"button\"> with id faq1-button / faq2-button and visible question text",
            "Each question button declares its state and target: aria-expanded=\"false\" and aria-controls pointing at its own panel id",
            "Each answer panel exists with id faq1-panel / faq2-panel and starts hidden",
            "Each panel points back at its button with aria-labelledby",
            "Add a live region <p id=\"status\" role=\"status\"> for announcing changes",
            "Add no redundant ARIA: no role=\"button\", no role on a <ul>, no aria-hidden on a button or link",
            "Give the icon-only <button id=\"closeHelp\"> an accessible name with aria-label, and hide its decorative icon <span> with aria-hidden=\"true\"",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Help centre — FAQ</title>
  </head>
  <body>
    <main>
      <h1>Frequently asked questions</h1>

      <!-- TODO: build the accordion here.
           Question 1: "How do I change my plan?"   Answer: one paragraph.
           Question 2: "Can I export my data?"      Answer: one paragraph.
           Then the status live region, and the icon-only dismiss button
           (id="closeHelp") whose only visible content is a decorative x glyph.
           script.js flips the state; your markup supplies the starting state.
      -->
    </main>
    <script src="script.js"></script>
  </body>
</html>
""",
            "script.js": """// Already implemented. Do not edit.
// Each question button toggles the panel named by its aria-controls attribute
// and keeps aria-expanded and the status region in sync.
document.querySelectorAll("[aria-controls]").forEach((button) => {
  button.addEventListener("click", () => {
    const panel = document.getElementById(button.getAttribute("aria-controls"));
    if (!panel) return;
    const isOpen = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!isOpen));
    panel.hidden = isOpen;
    const status = document.getElementById("status");
    if (status) {
      status.textContent = `${button.textContent.trim()} ${isOpen ? "collapsed" : "expanded"}`;
    }
  });
});
""",
        },
        "checks": [
            {
                "id": "button_one_native",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#faq1-button",
                "with_attributes": {"type": "button"},
                "non_empty_text": True,
                "label": "Question 1 is a native <button type=\"button\"> with visible text",
                "concept": "accessibility",
                "hint": "A native button is focusable, activates on Enter and Space, and needs no role.",
            },
            {
                "id": "button_two_native",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#faq2-button",
                "with_attributes": {"type": "button"},
                "non_empty_text": True,
                "label": "Question 2 is a native <button type=\"button\"> with visible text",
                "concept": "accessibility",
                "hint": "Same treatment for the second question; ids must match the script.",
            },
            {
                "id": "button_one_wiring",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#faq1-button",
                "with_attributes": {"aria-expanded": "false", "aria-controls": "faq1-panel"},
                "label": "Question 1's button declares aria-expanded=\"false\" and aria-controls=\"faq1-panel\"",
                "concept": "aria",
                "hint": "Both attributes belong on the button itself: state on the control, and the id of the panel it owns.",
            },
            {
                "id": "button_two_wiring",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#faq2-button",
                "with_attributes": {"aria-expanded": "false", "aria-controls": "faq2-panel"},
                "label": "Question 2's button declares aria-expanded=\"false\" and aria-controls=\"faq2-panel\"",
                "concept": "aria",
                "hint": "Each button controls its own panel — check the id it points at.",
            },
            {
                "id": "panel_one_exists",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "#faq1-panel",
                "label": "Panel faq1-panel exists",
                "concept": "aria",
                "hint": "aria-controls must resolve to a real element on the page.",
            },
            {
                "id": "panel_one_has_answer",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"id\s*=\s*[\"']faq1-panel[\"'][^>]*>\s*(?:<!--[\s\S]*?-->\s*)*<p(?=[\s>])[^>]*>\s*[^<\s]",
                "label": "Panel faq1-panel contains the answer text",
                "concept": "aria",
                "hint": "An empty panel means the button opens nothing. Put the answer paragraph inside it.",
            },
            {
                "id": "panel_two_exists",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "#faq2-panel",
                "label": "Panel faq2-panel exists",
                "concept": "aria",
                "hint": "The second button needs its own panel element.",
            },
            {
                "id": "panel_two_has_answer",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"id\s*=\s*[\"']faq2-panel[\"'][^>]*>\s*(?:<!--[\s\S]*?-->\s*)*<p(?=[\s>])[^>]*>\s*[^<\s]",
                "label": "Panel faq2-panel contains the answer text",
                "concept": "aria",
                "hint": "Second panel, second answer.",
            },
            {
                "id": "panel_one_hidden",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<[a-zA-Z]+[^>]*id\s*=\s*[\"']faq1-panel[\"'][^>]*\shidden\b"
                    r"|<[a-zA-Z]+[^>]*\shidden\b[^>]*id\s*=\s*[\"']faq1-panel[\"']"
                ),
                "label": "Panel faq1-panel starts collapsed (hidden)",
                "concept": "accessibility",
                "hint": "display:none in CSS would hide it from everyone but leave the markup lying about its state; use the hidden attribute so it matches aria-expanded=\"false\".",
            },
            {
                "id": "panel_two_hidden",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<[a-zA-Z]+[^>]*id\s*=\s*[\"']faq2-panel[\"'][^>]*\shidden\b"
                    r"|<[a-zA-Z]+[^>]*\shidden\b[^>]*id\s*=\s*[\"']faq2-panel[\"']"
                ),
                "label": "Panel faq2-panel starts collapsed (hidden)",
                "concept": "accessibility",
                "hint": "Both panels are collapsed on load, so both carry the hidden attribute.",
            },
            {
                "id": "panel_one_labelled",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "#faq1-panel",
                "with_attributes": {"aria-labelledby": "faq1-button"},
                "label": "Panel faq1-panel is labelled by its button",
                "concept": "aria",
                "hint": "aria-labelledby closes the loop: the panel's name is the question that opened it.",
            },
            {
                "id": "panel_two_labelled",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "#faq2-panel",
                "with_attributes": {"aria-labelledby": "faq2-button"},
                "label": "Panel faq2-panel is labelled by its button",
                "concept": "aria",
                "hint": "Point at the matching button id.",
            },
            {
                "id": "status_region",
                "requirement_index": 4,
                "type": "html_element",
                "file": "index.html",
                "selector": "p#status",
                "with_attributes": {"role": "status"},
                "label": "<p id=\"status\" role=\"status\"> live region exists",
                "concept": "aria",
                "hint": "A live region is one of the cases where ARIA adds something HTML cannot express.",
            },
            {
                "id": "no_role_button",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"role\s*=\s*[\"']button[\"']",
                "label": "No role=\"button\" anywhere",
                "concept": "aria",
                "hint": "role=\"button\" on a <div> promises keyboard behaviour you would then have to write yourself; on a <button> it is noise.",
            },
            {
                "id": "no_role_on_list",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<ul[^>]*\srole\s*=",
                "label": "No redundant role on a <ul>",
                "concept": "aria",
                "hint": "A <ul> is already a list.",
            },
            {
                "id": "no_aria_hidden_on_controls",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<(?:button|a)[^>]*aria-hidden\s*=\s*[\"']true[\"']",
                "label": "No interactive element is hidden with aria-hidden",
                "concept": "aria",
                "hint": "aria-hidden on a focusable control creates a control a screen-reader user can reach but not perceive.",
            },
            {
                "id": "close_button_named",
                "requirement_index": 6,
                "type": "html_element",
                "file": "index.html",
                "selector": "button#closeHelp",
                "with_attributes": {"type": "button", "aria-label": "*"},
                "label": "button#closeHelp has an aria-label accessible name",
                "concept": "aria",
                "hint": "An icon-only button has no text node, so its name has to come from aria-label — this is ARIA earning its place.",
            },
            {
                "id": "close_button_label_real",
                "requirement_index": 6,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"aria-label\s*=\s*[\"'][^\"']{0,3}[\"']",
                "label": "The aria-label is a real name (4+ characters)",
                "concept": "aria",
                "hint": "aria-label=\"x\" names the button after its glyph. Say what it does: \"Dismiss help\".",
            },
            {
                "id": "decorative_icon_hidden",
                "requirement_index": 6,
                "type": "regex",
                "file": "index.html",
                "pattern": (
                    r"<button[^>]*id\s*=\s*[\"']closeHelp[\"'][\s\S]*?"
                    r"<span[^>]*aria-hidden\s*=\s*[\"']true[\"'][\s\S]*?</button>"
                ),
                "label": "The decorative icon <span> inside the button is aria-hidden=\"true\"",
                "concept": "aria",
                "hint": "The glyph would be read out after the label. Hide the span, not the button.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
    # ------------------------------------------------------------------ 10
    {
        "id": "html-media-figure-embed",
        "title": "Field Report — Figures, Captioned Video and Safe Embeds",
        "kind": "web",
        "practice_layer": "html",
        "skill_id": "html_semantics",
        "technology": "HTML",
        "difficulty": 3,
        "estimated_minutes": 28,
        "summary": (
            "Mark up an article's media: a captioned figure, a video with real captions "
            "and a fallback, and a map iframe that is named and lazy."
        ),
        "problem_statement": (
            "The field report page has media pasted in raw: an image with its caption in "
            "a loose paragraph, a video with no captions and no fallback, and a map "
            "iframe with no name at all — which a screen reader announces as an unlabelled "
            "frame.\n\n"
            "Rebuild the media block so the caption is programmatically tied to its image, "
            "the video is usable without sound, and the embed announces what it is."
        ),
        "constraints": [
            "Edit only index.html.",
            "The caption must be a <figcaption> inside the same <figure> as the image.",
            "Content alt text must be at least 15 characters and must not be a file name.",
            "The <track> element must use kind=\"captions\" with srclang, label and src.",
            "The iframe needs a title of at least 10 characters and loading=\"lazy\"; the legacy frameborder attribute is not allowed.",
        ],
        "requirements": [
            "Wrap the photo in a <figure> containing both the <img> and a <figcaption> of at least 15 characters",
            "Give the photo descriptive alt text of at least 15 characters that is not a file name",
            "Add a <video> with the controls attribute, a poster, and a <source> inside it carrying src and type",
            "Add a <track kind=\"captions\"> inside the video with src, srclang and label",
            "Provide fallback content inside <video>: a <p> of at least 10 characters for browsers that cannot play it",
            "Embed the map with an <iframe> that has a title of at least 10 characters and loading=\"lazy\", and no frameborder attribute",
        ],
        "editable_files": ["index.html"],
        "entry_file": "index.html",
        "files": {
            "index.html": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Field report — Kilder Glacier</title>
  </head>
  <body>
    <main>
      <article>
        <h1>Field report: Kilder Glacier</h1>
        <p>
          The survey team spent four days on the eastern ice front measuring
          retreat against the 2019 markers.
        </p>

        <!-- TODO: mark up the media block here.
             Assets:
               /media/ice-front.jpg   - the ice front with the 2019 marker post
                                        in the foreground (1200x800)
               /media/survey.mp4      - type video/mp4
               /media/survey.jpg      - poster frame
               /media/survey-en.vtt   - English captions
               map embed: https://maps.example.com/embed?q=kilder-glacier
             Caption for the photo: the ice front in August, with the 2019
             marker post now 40 metres from the edge.
        -->
      </article>
    </main>
  </body>
</html>
""",
        },
        "checks": [
            {
                "id": "figure_exists",
                "requirement_index": 0,
                "type": "html_element",
                "file": "index.html",
                "selector": "figure",
                "label": "A <figure> wraps the media and its caption",
                "concept": "semantic html",
                "hint": "<figure> is the unit of self-contained content plus caption.",
            },
            {
                "id": "img_in_figure",
                "requirement_index": 0,
                "type": "html_nested",
                "file": "index.html",
                "selector": "img",
                "parent": "figure",
                "label": "The image is inside the <figure>",
                "concept": "nesting",
                "hint": "The figure must contain the thing it captions.",
            },
            {
                "id": "figcaption_in_figure",
                "requirement_index": 0,
                "type": "html_nested",
                "file": "index.html",
                "selector": "figcaption",
                "parent": "figure",
                "label": "The caption is a <figcaption> inside the <figure>",
                "concept": "semantic html",
                "hint": "A loose <p> under the image looks the same but is not tied to it.",
            },
            {
                "id": "figcaption_text",
                "requirement_index": 0,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<figcaption[^>]*>\s*[^<]{15,}",
                "label": "The caption is real text (15+ characters)",
                "concept": "semantic html",
                "hint": "The caption is for everyone; the alt text is for people who cannot see the image. They are not the same sentence.",
            },
            {
                "id": "img_has_alt",
                "requirement_index": 1,
                "type": "html_element",
                "file": "index.html",
                "selector": "img",
                "with_attributes": {"src": "*", "alt": "*"},
                "label": "The image has a src and a non-empty alt",
                "concept": "alt text",
                "hint": "A captioned image still needs alt text — the caption is not a substitute.",
            },
            {
                "id": "img_alt_long_enough",
                "requirement_index": 1,
                "type": "not_regex",
                "file": "index.html",
                "pattern": ALT_TOO_SHORT,
                "label": "The alt text is at least 15 characters",
                "concept": "alt text",
                "hint": "Describe what the photo shows: the ice front and the marker post.",
            },
            {
                "id": "img_alt_not_filename",
                "requirement_index": 1,
                "type": "not_regex",
                "file": "index.html",
                "pattern": ALT_IS_FILENAME,
                "label": "The alt text is not a file name",
                "concept": "alt text",
                "hint": "\"ice-front.jpg\" is not a description.",
            },
            {
                "id": "video_poster",
                "requirement_index": 2,
                "type": "html_element",
                "file": "index.html",
                "selector": "video",
                "with_attributes": {"poster": "*"},
                "label": "<video> declares a poster frame",
                "concept": "media",
                "hint": "The poster is what fills the box before playback starts.",
            },
            {
                "id": "video_controls",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<video[^>]*\scontrols\b",
                "label": "<video> exposes native controls",
                "concept": "media",
                "hint": "Without the controls attribute there is no way to pause it.",
            },
            {
                "id": "video_source",
                "requirement_index": 2,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<video[\s\S]*?<source[^>]*(?:src[^>]*type|type[^>]*src)[^>]*>[\s\S]*?</video>",
                "label": "A <source> inside the video declares src and type",
                "concept": "media",
                "hint": "The type lets the browser skip formats it cannot play without downloading them.",
            },
            {
                "id": "captions_track",
                "requirement_index": 3,
                "type": "html_element",
                "file": "index.html",
                "selector": "track",
                "with_attributes": {"kind": "captions", "src": "*", "srclang": "*", "label": "*"},
                "label": "<track kind=\"captions\"> declares src, srclang and label",
                "concept": "media",
                "hint": "All four attributes belong on the same <track>; the label is what appears in the captions menu.",
            },
            {
                "id": "track_inside_video",
                "requirement_index": 3,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<video[\s\S]*?<track[^>]*kind\s*=\s*[\"']captions[\"'][\s\S]*?</video>",
                "label": "The captions track is inside the <video>",
                "concept": "media",
                "hint": "A track outside the video element is attached to nothing.",
            },
            {
                "id": "fallback_in_video",
                "requirement_index": 4,
                "type": "html_nested",
                "file": "index.html",
                "selector": "p",
                "parent": "video",
                "label": "A paragraph sits inside the <video> element",
                "concept": "media",
                "hint": "The fallback goes between <video> and </video>, so it renders only when playback fails.",
            },
            {
                "id": "video_fallback",
                "requirement_index": 4,
                "type": "regex",
                "file": "index.html",
                "pattern": r"<video[\s\S]*?<p(?=[\s>])[^>]*>\s*[^<]{10,}[\s\S]*?</video>",
                "label": "Fallback content inside <video> explains what to do instead",
                "concept": "media",
                "hint": "Anything between <video> and </video> that is not a source/track is shown when playback is impossible — offer a download link or a transcript.",
            },
            {
                "id": "iframe_named",
                "requirement_index": 5,
                "type": "html_element",
                "file": "index.html",
                "selector": "iframe",
                "with_attributes": {"src": "*", "title": "*", "loading": "lazy"},
                "label": "<iframe> has src, a non-empty title and loading=\"lazy\"",
                "concept": "accessibility",
                "hint": "An untitled frame is announced as \"frame\". The title is the only name it can have.",
            },
            {
                "id": "iframe_title_real",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<iframe[^>]*title\s*=\s*[\"'][^\"']{0,9}[\"']",
                "label": "The iframe title is descriptive (10+ characters)",
                "concept": "accessibility",
                "hint": "title=\"map\" barely names it. Say which map.",
            },
            {
                "id": "no_frameborder",
                "requirement_index": 5,
                "type": "not_regex",
                "file": "index.html",
                "pattern": r"<iframe[^>]*\s(?:frameborder|allowtransparency|scrolling)\s*=",
                "label": "No legacy presentational iframe attributes",
                "concept": "semantic html",
                "hint": "frameborder was replaced by CSS borders years ago.",
            },
        ],
        "behaviour": _empty_behaviour(),
    },
]


# ---------------------------------------------------------------------------
# Reference solutions
# ---------------------------------------------------------------------------
#
# These are never served: `practice_service.module_detail` builds the client
# payload from an explicit key list and `solution_files` is not in it. They
# exist so `test_every_web_module_solution_passes_its_own_checks` grades each
# module's own spec on every run — a check that drifts away from a solvable
# task fails in CI instead of in front of a learner.
#
# Kept out of the module dicts above so the task definition a reviewer reads is
# not interleaved with its answer.

REFERENCE_SOLUTIONS: dict[str, str] = {
    "html-document-skeleton": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Rye and Ember Bakery — Sourdough in Leith</title>
    <meta
      name="description"
      content="Rye and Ember is a Leith bakery baking sourdough overnight and selling it before noon."
    />
  </head>
  <body>
    <h1>Rye and Ember Bakery</h1>
    <p>Sourdough baked overnight, sold before noon.</p>
  </body>
</html>
""",
    "html-heading-outline": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Employee Handbook</title>
  </head>
  <body>
    <main>
      <h1>Employee Handbook</h1>

      <h2>Working hours</h2>
      <p>Core hours are 10:00 to 16:00 and the rest of the day is flexible.</p>

      <h2>Time off</h2>
      <p>Everyone gets 28 days of holiday plus public holidays.</p>

      <h3>Holiday</h3>
      <p>Request holiday at least two weeks ahead in the HR tool.</p>

      <h3>Sick leave</h3>
      <p>Message your lead before 10:00 on the first day you are unwell.</p>

      <h2>Expenses</h2>
      <p>Submit receipts within thirty days of the purchase.</p>
    </main>
  </body>
</html>
""",
    "html-recipe-lists": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Overnight Focaccia — Recipe</title>
  </head>
  <body>
    <main>
      <h1>Overnight Focaccia</h1>

      <h2>Ingredients</h2>
      <ul id="ingredients">
        <li>500 g strong white flour</li>
        <li>400 ml cold water</li>
        <li>10 g fine salt</li>
        <li>4 g dried yeast</li>
        <li>
          Olive oil
          <ul>
            <li>Peppery oil for finishing</li>
            <li>Mild oil for the tin</li>
          </ul>
        </li>
      </ul>

      <h2>Method</h2>
      <ol id="steps">
        <li>Mix the flour, water, salt and yeast into a wet dough.</li>
        <li>Cover and rest the dough in the fridge overnight.</li>
        <li>Dimple, oil and bake at 230C for 20 minutes.</li>
      </ol>

      <h2>Recipe facts</h2>
      <dl>
        <dt>Prep time</dt>
        <dd>20 minutes</dd>
        <dt>Rest time</dt>
        <dd>12 hours</dd>
        <dt>Serves</dt>
        <dd>8 people</dd>
      </dl>
    </main>
  </body>
</html>
""",
    "html-site-navigation": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Pricing — Orbit Docs</title>
  </head>
  <body>
    <a href="#main" class="skip-link">Skip to main content</a>

    <header>
      <nav aria-label="Primary">
        <ul>
          <li><a href="index.html">Home</a></li>
          <li><a href="guides.html">Guides</a></li>
          <li><a href="pricing.html" aria-current="page">Pricing</a></li>
          <li><a href="changelog.html">Changelog</a></li>
          <li>
            <a href="https://community.example.com" target="_blank" rel="noopener noreferrer">
              Community forum
            </a>
          </li>
          <li><a href="#pricing">Jump to plan comparison</a></li>
        </ul>
      </nav>
    </header>

    <main id="main">
      <h1>Pricing</h1>
      <section id="pricing">
        <h2>Plan comparison</h2>
        <p>Every plan includes the full API and unlimited projects.</p>
      </section>
    </main>
  </body>
</html>
""",
    "html-image-gallery-alt": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Kettle 900 — Gallery</title>
  </head>
  <body>
    <main>
      <h1>Kettle 900</h1>

      <ul class="gallery">
        <li>
          <img
            src="/img/kettle-front.jpg"
            width="640"
            height="480"
            alt="The Kettle 900 seen from the front with its lid closed"
          />
        </li>
        <li>
          <img
            src="/img/kettle-pouring.jpg"
            width="640"
            height="480"
            loading="lazy"
            alt="The kettle pouring a steady stream of water into a white cup"
          />
        </li>
        <li>
          <img
            src="/img/kettle-base.jpg"
            width="640"
            height="480"
            loading="lazy"
            alt="The kettle resting on its charging base with the standby light on"
          />
        </li>
      </ul>

      <img class="divider" src="/img/divider.svg" width="300" height="12" alt="" />
    </main>
  </body>
</html>
""",
    "html-data-table": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Quarterly Sales — Report</title>
  </head>
  <body>
    <main>
      <h1>Quarterly sales</h1>

      <table>
        <caption>Sales by region for the first three quarters of 2024, in thousands</caption>
        <thead>
          <tr>
            <th scope="col">Region</th>
            <th scope="col">Q1</th>
            <th scope="col">Q2</th>
            <th scope="col">Q3</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th scope="row">North</th>
            <td>120</td>
            <td>138</td>
            <td>151</td>
          </tr>
          <tr>
            <th scope="row">South</th>
            <td>96</td>
            <td>104</td>
            <td>99</td>
          </tr>
          <tr>
            <th scope="row">Europe</th>
            <td>210</td>
            <td>225</td>
            <td>243</td>
          </tr>
        </tbody>
        <tfoot>
          <tr>
            <th scope="row">Total</th>
            <td>426</td>
            <td>467</td>
            <td>493</td>
          </tr>
        </tfoot>
      </table>
    </main>
  </body>
</html>
""",
    "html-workshop-signup-form": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Workshop signup</title>
  </head>
  <body>
    <main>
      <h1>Reserve your seat</h1>

      <form action="/api/signup" method="post">
        <p>
          <label for="fullName">Full name</label>
          <input type="text" id="fullName" name="fullName" required />
        </p>

        <p>
          <label for="email">Email address</label>
          <input type="email" id="email" name="email" required />
        </p>

        <p>
          <label for="session">Session</label>
          <select id="session" name="session">
            <option value="morning">Morning</option>
            <option value="afternoon">Afternoon</option>
            <option value="evening">Evening</option>
          </select>
        </p>

        <fieldset>
          <legend>Ticket type</legend>
          <p>
            <input type="radio" id="ticketStandard" name="ticket" value="standard" />
            <label for="ticketStandard">Standard</label>
          </p>
          <p>
            <input type="radio" id="ticketStudent" name="ticket" value="student" />
            <label for="ticketStudent">Student</label>
          </p>
        </fieldset>

        <p>
          <input type="checkbox" id="terms" name="terms" required />
          <label for="terms">I accept the code of conduct</label>
        </p>

        <button type="submit">Reserve my seat</button>
      </form>
    </main>
  </body>
</html>
""",
    "html-landmark-layout": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>The Daily Signal</title>
  </head>
  <body>
    <header>
      <a class="brand" href="index.html">The Daily Signal</a>
      <nav aria-label="Sections">
        <ul>
          <li><a href="index.html">Home</a></li>
          <li><a href="world.html">World</a></li>
          <li><a href="science.html">Science</a></li>
          <li><a href="opinion.html">Opinion</a></li>
        </ul>
      </nav>
    </header>

    <main>
      <article>
        <h2>Harbour tunnel opens six months early</h2>
        <p>The tunnel opened to traffic on Monday morning, well ahead of schedule.</p>
      </article>

      <article>
        <h2>City tests overnight bus network</h2>
        <p>Six routes will run hourly through the night for a year.</p>
      </article>

      <aside>
        <h2>Most read</h2>
        <ul>
          <li><a href="ferries.html">Ferry timetable changes</a></li>
          <li><a href="swimming.html">Where to swim this summer</a></li>
          <li><a href="budget.html">The council budget explained</a></li>
        </ul>
      </aside>
    </main>

    <footer>
      <small>&copy; 2024 The Daily Signal</small>
    </footer>
  </body>
</html>
""",
    "html-accessible-disclosure": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Help centre — FAQ</title>
  </head>
  <body>
    <main>
      <h1>Frequently asked questions</h1>

      <h2>
        <button type="button" id="faq1-button" aria-expanded="false" aria-controls="faq1-panel">
          How do I change my plan?
        </button>
      </h2>
      <div id="faq1-panel" role="region" aria-labelledby="faq1-button" hidden>
        <p>Open Billing, choose a plan and confirm. The change applies immediately.</p>
      </div>

      <h2>
        <button type="button" id="faq2-button" aria-expanded="false" aria-controls="faq2-panel">
          Can I export my data?
        </button>
      </h2>
      <div id="faq2-panel" role="region" aria-labelledby="faq2-button" hidden>
        <p>Yes. Settings then Export produces a JSON archive within an hour.</p>
      </div>

      <p id="status" role="status"></p>

      <button type="button" id="closeHelp" aria-label="Dismiss help panel">
        <span aria-hidden="true">&times;</span>
      </button>
    </main>
    <script src="script.js"></script>
  </body>
</html>
""",
    "html-media-figure-embed": """<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Field report — Kilder Glacier</title>
  </head>
  <body>
    <main>
      <article>
        <h1>Field report: Kilder Glacier</h1>
        <p>
          The survey team spent four days on the eastern ice front measuring
          retreat against the 2019 markers.
        </p>

        <figure>
          <img
            src="/media/ice-front.jpg"
            width="1200"
            height="800"
            alt="The glacier ice front with the 2019 marker post standing in meltwater"
          />
          <figcaption>
            The ice front in August, with the 2019 marker post now 40 metres from the edge.
          </figcaption>
        </figure>

        <video controls poster="/media/survey.jpg" width="960" height="540">
          <source src="/media/survey.mp4" type="video/mp4" />
          <track kind="captions" src="/media/survey-en.vtt" srclang="en" label="English" />
          <p>Your browser cannot play this video. Download the survey footage instead.</p>
        </video>

        <iframe
          src="https://maps.example.com/embed?q=kilder-glacier"
          title="Map of the Kilder Glacier survey area"
          loading="lazy"
          width="600"
          height="400"
        ></iframe>
      </article>
    </main>
  </body>
</html>
""",
}

# Attached by id rather than inline, so a module added without a solution raises
# here instead of silently skipping the CI check that grades it.
for _module in HTML_MODULES:
    _module["solution_files"] = {"index.html": REFERENCE_SOLUTIONS[_module["id"]]}
