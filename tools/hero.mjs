// Render a post's 1200x630 cover from tools/hero.html.
//   node tools/hero.mjs '{"out": ".../slug.jpg", "title": "...", "kicker": "...", "note": "...",
//                        "count": 9, "sites": [{"domain": "...", "fav": "/abs/path.png"}]}'
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import puppeteer from "puppeteer-core";

const here = path.dirname(fileURLToPath(import.meta.url));
const data = JSON.parse(process.argv[2] || "{}");
const chrome = process.env.CHROME_BIN || ["/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  "/usr/bin/chromium-browser", "/usr/bin/chromium"].find((p) => fs.existsSync(p));

const browser = await puppeteer.launch({
  executablePath: chrome, headless: true,
  args: ["--allow-file-access-from-files",
    ...(process.platform === "linux" ? ["--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"] : [])],
});
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1200, height: 630, deviceScaleFactor: 1 });
  await page.goto("file://" + path.join(here, "hero.html") + "#" + encodeURIComponent(JSON.stringify(data)),
    { waitUntil: "networkidle0" });
  await page.waitForFunction("window.READY === true", { timeout: 15000 });
  fs.mkdirSync(path.dirname(data.out), { recursive: true });
  await page.screenshot({ path: data.out, type: "jpeg", quality: 90 });
  console.log("hero: " + data.out);
} finally {
  await browser.close();
}
