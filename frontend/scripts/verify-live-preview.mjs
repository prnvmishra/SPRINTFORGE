/**
 * Browser proof that the preview is live and cumulative.
 *
 * The defect this guards: a CSS- or JS-only ticket owns no entry document, so
 * the pane used to render nothing the learner typed and stayed frozen on the
 * document fetched at page load. This drives a real browser against a real
 * ticket, edits the stylesheet, and asserts the rendered page changes with no
 * Run and no check request at all.
 *
 * Credentials come from the environment, never the command line, and are meant
 * to belong to a throwaway fixture account.
 *
 * Usage:
 *   PREVIEW_QA_EMAIL=... PREVIEW_QA_PASSWORD=... \
 *   node scripts/verify-live-preview.mjs \
 *     --base http://localhost:3023 --ticket <ticketId> --project <projectId>
 */

import { mkdirSync } from "node:fs";
import { chromium } from "playwright";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i].replace(/^--/, ""), process.argv[i + 1]);
}
const BASE = args.get("base") ?? "http://localhost:3023";
const EMAIL = process.env.PREVIEW_QA_EMAIL;
const PASSWORD = process.env.PREVIEW_QA_PASSWORD;
const TICKET = args.get("ticket");
const PROJECT = args.get("project");
const SHOTS = args.get("shots") ?? ".preview-evidence";

let failures = 0;
function check(label, condition, detail = "") {
  if (!condition) failures += 1;
  console.log(`  [${condition ? "PASS" : "FAIL"}] ${label}${detail ? `  — ${detail}` : ""}`);
}

/** Computed background of the previewed document, i.e. what the learner sees. */
async function previewBackground(page) {
  const frame = page.frameLocator('iframe[title="Live preview"]');
  return frame.locator("body").evaluate((el) => getComputedStyle(el).backgroundColor);
}

async function main() {
  mkdirSync(SHOTS, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });

  // Any request to these would mean the preview is not independent of grading.
  const graded = [];
  page.on("request", (r) => {
    if (/\/(run|submit)$/.test(new URL(r.url()).pathname)) graded.push(r.url());
  });

  console.log("\n=== 1. Sign in ===");
  await page.goto(`${BASE}/login`, { waitUntil: "networkidle" });
  await page.getByLabel(/email/i).fill(EMAIL);
  await page.getByLabel(/password/i).fill(PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();
  await page.waitForURL(/dashboard|onboarding|path/, { timeout: 120000 });
  check("signed in", true, EMAIL);

  console.log("\n=== 2. A CSS-only ticket renders the whole project ===");
  await page.goto(`${BASE}/workspace/${TICKET}`, { waitUntil: "networkidle" });
  await page.waitForSelector(".monaco-editor", { timeout: 90000 });
  await page.waitForSelector('iframe[title="Live preview"]', { timeout: 60000 });
  await page.waitForTimeout(2500);

  const files = await page.locator("button:has-text('styles.css')").count();
  check("workspace owns only the stylesheet", files > 0);
  check(
    "preview shows markup from an earlier ticket",
    (await page
      .frameLocator('iframe[title="Live preview"]')
      .locator("#movieList")
      .count()) > 0,
  );

  const before = await previewBackground(page);
  check("preview is styled by the learner's CSS", before === "rgb(11, 12, 16)", before);
  await page.screenshot({ path: `${SHOTS}/1-before-edit.png`, fullPage: false });

  console.log("\n=== 3. Editing CSS updates the preview with no Run ===");
  await page.locator(".monaco-editor .view-lines").click();
  await page.keyboard.press("Control+End");
  await page.keyboard.press("Enter");
  await page.keyboard.type("body { background: rgb(120, 20, 60); }", { delay: 15 });

  // The recomposition is debounced, so give it a beat — but far less than a
  // network round trip would take.
  await page.waitForTimeout(1500);
  const after = await previewBackground(page);
  check("preview background changed as typed", after === "rgb(120, 20, 60)", `${before} → ${after}`);
  check("no run or submit request was made", graded.length === 0, graded.join(", "));
  await page.screenshot({ path: `${SHOTS}/2-after-edit.png`, fullPage: false });

  console.log("\n=== 4. Whole-project preview from the Projects section ===");
  await page.goto(`${BASE}/projects/${PROJECT}/preview`, { waitUntil: "networkidle" });
  await page.waitForSelector('iframe[title="Project preview"]', { timeout: 60000 });
  const projectFrame = page.frameLocator('iframe[title="Project preview"]');
  check(
    "project preview renders the verified work",
    (await projectFrame.locator("#movieList").count()) > 0,
  );
  const shown = await page.locator("body").innerText();
  check("states how much is built", /1\/2|1 of 2/.test(shown), shown.slice(0, 120));
  await page.screenshot({ path: `${SHOTS}/3-project-preview.png`, fullPage: true });

  const EMPTY = args.get("empty-project");
  if (EMPTY) {
    console.log("\n=== 5. A project with nothing verified ===");
    await page.goto(`${BASE}/projects/${EMPTY}/preview`, { waitUntil: "networkidle" });
    await page.waitForTimeout(1500);
    const text = await page.locator("body").innerText();
    check(
      "shows a real empty state, not a blank frame",
      /No verified work in this project/i.test(text),
      text.slice(0, 80),
    );
    check(
      "renders no preview iframe at all",
      (await page.locator('iframe[title="Project preview"]').count()) === 0,
    );
    await page.screenshot({ path: `${SHOTS}/4-empty-project.png`, fullPage: true });
  }

  await browser.close();
  console.log("\n" + "=".repeat(60));
  console.log(failures === 0 ? "All live-preview checks passed." : `${failures} check(s) FAILED.`);
  if (failures > 0) process.exitCode = 1;
}

main().catch((error) => {
  console.error("verification crashed:", error);
  process.exitCode = 1;
});
