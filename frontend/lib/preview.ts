/**
 * Client-side preview bundler.
 *
 * The API only returns a preview as a side effect of running checks, and only
 * when the workspace happens to contain an entry document — so CSS/JS-only
 * tickets could never render, and rendering always cost a round trip. Composing
 * the document in the browser makes Run instant, independent of validation, and
 * uniform across practice modules and tickets.
 *
 * Nothing here executes the code: the string is handed to a sandboxed iframe.
 */

const HTML_EXTENSIONS = /\.html?$/i;

/**
 * The conventional browser entry script, and the only file appended when the
 * document never referenced it. A project can also hold `server.js` or a
 * migration script, and running those in the iframe throws instead of
 * rendering. Mirrors `BROWSER_SCRIPT` in `project_preview_service.py`.
 */
const BROWSER_SCRIPT = "script.js";

/**
 * Layers the learner's live editor buffers over the project's composed files.
 *
 * The cross-ticket composition — which ticket's copy of a filename wins — is
 * decided by the server in `project_preview_service.learner_work`: a later
 * ticket only contributes a file it actually holds work for, so an untouched or
 * emptied later copy can never erase an earlier ticket's work. By the time the
 * map reaches this function there is one entry per filename, and the only rule
 * left is the same unconditional override the server applies to the current
 * ticket: the buffer in the editor wins, including when the learner has just
 * emptied it.
 */
export function composeProjectFiles(
  projectFiles: Record<string, string>,
  liveFiles: Record<string, string>,
): Record<string, string> {
  return { ...projectFiles, ...liveFiles };
}

/** Entry document for a file map, or null when there is nothing to render. */
function previewEntry(files: Record<string, string>): string | null {
  const names = Object.keys(files);
  if (names.includes("index.html")) return "index.html";
  return names.find((name) => HTML_EXTENSIONS.test(name)) ?? null;
}

/** Whether this workspace can produce a live preview at all. */
export function canPreview(files: Record<string, string>): boolean {
  return previewEntry(files) !== null;
}

function escapeForRegExp(value: string) {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

/**
 * Inlines local stylesheet and script references so the iframe needs no network
 * and no file server. Remote URLs are left untouched.
 */
export function buildPreview(files: Record<string, string>): string | null {
  const entry = previewEntry(files);
  if (!entry) return null;

  let html = files[entry] ?? "";

  for (const [name, content] of Object.entries(files)) {
    if (name === entry) continue;
    const escaped = escapeForRegExp(name);

    if (/\.css$/i.test(name)) {
      // <link rel="stylesheet" href="styles.css"> → inline <style>
      html = html.replace(
        new RegExp(`<link[^>]*href=["'][^"']*${escaped}["'][^>]*>`, "gi"),
        `<style>\n${content}\n</style>`,
      );
    } else if (/\.m?js$/i.test(name)) {
      // <script src="script.js"></script> → inline module-free script
      html = html.replace(
        new RegExp(`<script[^>]*src=["'][^"']*${escaped}["'][^>]*>\\s*</script>`, "gi"),
        `<script>\n${content}\n</script>`,
      );
    }
  }

  // Any stylesheet, and the browser entry script, that the document never
  // referenced still belongs in it — a learner writing styles.css should see it
  // applied even if the HTML from an earlier ticket forgot the <link>. Kept in
  // step with `_append_unreferenced` in `project_preview_service.py`.
  const appended: string[] = [];
  for (const [name, content] of Object.entries(files)) {
    if (name === entry || !content.trim()) continue;
    if (/\.css$/i.test(name) && !html.includes(content)) {
      appended.push(`<style>\n${content}\n</style>`);
    }
    if (name === BROWSER_SCRIPT && !html.includes(content)) {
      appended.push(`<script>\n${content}\n</script>`);
    }
  }

  if (appended.length > 0) {
    const block = appended.join("\n");
    html = html.includes("</body>")
      ? html.replace("</body>", `${block}\n</body>`)
      : `${html}\n${block}`;
  }

  return html;
}
