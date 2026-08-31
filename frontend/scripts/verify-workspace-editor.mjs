/**
 * Browser regression test for the practice workspace editor.
 *
 * Guards the file-tab contract that unit tests cannot reach: each tab must show
 * its own buffer, typed edits must survive tab switches, provided files must stay
 * read-only, and the text the backend grades must be the text the user typed.
 *
 * Usage: node scripts/verify-workspace-editor.mjs [baseUrl]
 */

import { chromium } from "playwright";

const BASE = process.argv[2] ?? "http://localhost:3100";
const MODULE_PATH = "/practice/css-profile-card";
const TYPED = ".profile-card { color: rgb(9, 9, 9); }";

let failures = 0;
function check(label, condition, detail = "") {
  const status = condition ? "PASS" : "FAIL";
  if (!condition) failures += 1;
  console.log(`  [${status}] ${label}${detail ? `  — ${detail}` : ""}`);
}

const oneLine = (s) => (s ?? "").replace(/\s+/g, " ").trim().slice(0, 90);

async function main() {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1500, height: 950 } });
  page.on("console", (m) => {
    if (m.type() === "error") console.log("  [console error]", m.text().slice(0, 160));
  });
  page.on("requestfailed", (r) =>
    console.log("  [request failed]", r.method(), r.url(), r.failure()?.errorText),
  );
  page.on("response", (r) => {
    if (r.url().includes("/auth/") || r.url().includes("/profile/"))
      console.log("  [network]", r.status(), r.request().method(), r.url());
  });

  // --- account -----------------------------------------------------------
  const email = `editor${Date.now()}@sprintforge.dev`;
  // networkidle, not domcontentloaded: filling inputs before React hydrates sets
  // the DOM value without updating state, so the form submits empty.
  await page.goto(`${BASE}/register`, { waitUntil: "networkidle" });
  await page.getByLabel(/full name/i).fill("Editor Regression");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill("Testpass123!");
  await page.getByRole("button", { name: /create account/i }).click();
  try {
    // Remote Postgres can make the first write slow; be generous.
    await page.waitForURL(/onboarding|dashboard/, { timeout: 150000 });
  } catch (err) {
    const shown = await page.locator("body").innerText().catch(() => "");
    console.log("  [debug] still on", page.url());
    console.log("  [debug] page text:", oneLine(shown));
    throw err;
  }
  console.log("\n=== 1. Workspace loads ===");
  check("registered a fresh user", true, email);

  await page.goto(`${BASE}${MODULE_PATH}`, { waitUntil: "networkidle" });
  await page.waitForSelector(".monaco-editor", { timeout: 60000 });
  await page.waitForTimeout(1500);

  const tab = (name) => page.getByRole("button", { name, exact: false }).first();
  const editorText = async () => {
    // Monaco virtualises lines; read the model instead of the DOM.
    return page.evaluate(() => {
      const m = window.monaco?.editor?.getModels?.() ?? [];
      const active = m.find((x) => !x.isDisposed());
      return active ? active.getValue() : "";
    });
  };

  async function open(name) {
    await tab(name).click();
    await page.waitForTimeout(700);
    return editorText();
  }

  // --- 2. per-tab content, no bleed --------------------------------------
  console.log("\n=== 2. Each tab shows its own buffer ===");
  const sequence = ["index.html", "script.js", "styles.css", "index.html", "styles.css", "script.js", "styles.css"];
  const expect = {
    "index.html": (t) => t.includes("<!DOCTYPE html>"),
    "script.js": (t) => t.includes("getElementById"),
    "styles.css": (t) => t.includes("stylesheet was removed") || t.includes("profile-card"),
  };
  const forbidden = {
    "index.html": (t) => t.includes("stylesheet was removed"),
    "script.js": (t) => t.includes("<!DOCTYPE html>"),
    "styles.css": (t) => t.includes("<!DOCTYPE html>") || t.includes("getElementById"),
  };
  for (const [i, name] of sequence.entries()) {
    const text = await open(name);
    check(`click ${i + 1}: ${name} shows its own content`, expect[name](text), oneLine(text));
    check(`click ${i + 1}: ${name} has no foreign content`, !forbidden[name](text));
  }

  // --- 3. typed edits survive tab switching ------------------------------
  console.log("\n=== 3. Typed edits survive tab switches ===");
  await tab("styles.css").click();
  await page.waitForTimeout(500);
  await page.locator(".monaco-editor .view-lines").click();
  await page.keyboard.press("Control+End");
  await page.keyboard.press("Enter");
  await page.keyboard.type(TYPED, { delay: 12 });
  await page.waitForTimeout(600);

  let css = await editorText();
  check("typed text is in the editor", css.includes(TYPED), oneLine(css));

  const afterHtml = await open("index.html");
  check("typed CSS did not leak into index.html", !afterHtml.includes("profile-card { color"), oneLine(afterHtml));
  check("index.html still shows HTML", afterHtml.includes("<!DOCTYPE html>"));

  const afterJs = await open("script.js");
  check("typed CSS did not leak into script.js", !afterJs.includes("profile-card { color"), oneLine(afterJs));

  css = await open("styles.css");
  check("typed CSS survived the round trip", css.includes(TYPED), oneLine(css));

  await open("index.html");
  css = await open("styles.css");
  check("typed CSS survived a second round trip", css.includes(TYPED));

  // --- 4. provided files stay read-only ----------------------------------
  console.log("\n=== 4. Provided files are read-only ===");
  const htmlBefore = await open("index.html");
  await page.locator(".monaco-editor .view-lines").click();
  await page.keyboard.type("SHOULD_NOT_APPEAR", { delay: 10 });
  await page.waitForTimeout(400);
  const htmlAfter = await editorText();
  check("typing into index.html is rejected", !htmlAfter.includes("SHOULD_NOT_APPEAR"));
  check("index.html content unchanged", htmlAfter.trim() === htmlBefore.trim());

  // --- 5. the backend grades what was typed ------------------------------
  console.log("\n=== 5. Backend receives the typed buffer ===");
  await open("styles.css");
  const runResponse = page.waitForResponse(
    (r) => /\/practice\/modules\/.+\/run$/.test(r.url()) && r.request().method() === "POST",
    { timeout: 60000 },
  );
  await page.getByRole("button", { name: /^run/i }).first().click();
  const res = await runResponse;
  const sent = JSON.parse(res.request().postData() ?? "{}");
  const sentCss = sent.files?.["styles.css"] ?? "";
  check("run request carried the typed CSS", sentCss.includes(TYPED), oneLine(sentCss));
  check("run request did not send HTML as the CSS file", !sentCss.includes("<!DOCTYPE html>"));
  const body = await res.json().catch(() => ({}));
  const checksRun = (body.static_results?.length ?? 0) + (body.test_results?.length ?? 0);
  check("backend returned check results", checksRun > 0, `${checksRun} checks`);

  // --- 6. reset restores the starter buffer ------------------------------
  console.log("\n=== 6. Reset restores the starter buffer ===");
  const resetBtn = page.getByRole("button", { name: /^reset/i }).first();
  if (await resetBtn.count()) {
    await resetBtn.click();
    await page.waitForTimeout(1200);
    const afterReset = await editorText();
    check("typed CSS cleared by Reset", !afterReset.includes(TYPED), oneLine(afterReset));
  } else {
    check("reset button present", false);
  }

  await browser.close();

  console.log("\n" + "=".repeat(60));
  if (failures === 0) {
    console.log("All editor checks passed. File tabs are isolated and edits persist.");
  } else {
    console.log(`${failures} editor check(s) FAILED.`);
    process.exitCode = 1;
  }
}

main().catch((err) => {
  console.error("verification crashed:", err);
  process.exitCode = 1;
});
