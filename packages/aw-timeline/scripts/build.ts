// 静的サイトを組む。@aw/data から出来事・地点を読み、dist/index.html を書き出す。
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { events, sites } from "@aw/data";
import { renderTimelineHtml } from "../src/render.js";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");

const css = readFileSync(resolve(root, "src/styles.css"), "utf8");
const enhanceJs = readFileSync(resolve(root, "src/enhance.js"), "utf8");

// aw-map のデプロイ先。別プロジェクトとして分離できるよう、base を環境変数で渡す。
// 未指定なら "/"（同一オリジンに aw-map を置く場合）。
const mapBase = process.env["AW_MAP_BASE"] ?? "/";
const currentYear = new Date().getFullYear();

const html = renderTimelineHtml(events, sites, { currentYear, mapBase, css, enhanceJs });

const outDir = resolve(root, "dist");
mkdirSync(outDir, { recursive: true });
writeFileSync(resolve(outDir, "index.html"), html, "utf8");

process.stdout.write(
  `aw-timeline: wrote dist/index.html (${events.length} events, ${sites.length} sites, ` +
    `map base "${mapBase}")\n`,
);
