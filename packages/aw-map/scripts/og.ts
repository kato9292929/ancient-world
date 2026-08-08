// 地点個別の OG 画像を静的生成する。ブラウザに依存せず、SVG で書き出す。
// 生成できない地点があってもビルドを止めない。件数を標準出力に出す。
// vite build のあとに走らせる（dist/ が既にある前提）。
import { writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { sites, clusters } from "@aw/data";
import type { Site } from "@aw/data";

const here = dirname(fileURLToPath(import.meta.url));
const outDir = resolve(here, "..", "dist", "og");

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function formatYear(n: number | null): string {
  if (n === null) return "";
  return n < 0 ? `前${-n}年` : n > 0 ? `${n}年` : "0年";
}

function ogSvg(s: Site, clusterName: string): string {
  const era = formatYear(s.era_start);
  const eraLine = era ? `${era}${s.era_note ? " " + s.era_note : ""}` : s.era_note;
  return `<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630">
  <rect width="1200" height="630" fill="#faf8f4"/>
  <rect x="0" y="0" width="1200" height="10" fill="#7a5c3e"/>
  <text x="80" y="180" font-family="system-ui, sans-serif" font-size="34" fill="#6b6559">ancient world ／ ${esc(clusterName)}</text>
  <text x="80" y="300" font-family="system-ui, sans-serif" font-size="82" font-weight="700" fill="#1a1a1a">${esc(s.name_ja)}</text>
  <text x="80" y="370" font-family="system-ui, sans-serif" font-size="40" fill="#6b6559">${esc(s.name_en)}・${esc(s.country)}</text>
  <text x="80" y="470" font-family="system-ui, sans-serif" font-size="40" fill="#7a5c3e">${esc(eraLine)}</text>
</svg>
`;
}

function main(): void {
  mkdirSync(outDir, { recursive: true });
  const clusterName = new Map(clusters.map((c) => [c.id, c.name_ja]));
  let ok = 0;
  const failed: string[] = [];
  for (const s of sites) {
    try {
      writeFileSync(resolve(outDir, `${s.id}.svg`), ogSvg(s, clusterName.get(s.cluster) ?? s.cluster));
      ok += 1;
    } catch (err) {
      failed.push(`${s.id}: ${(err as Error).message}`);
    }
  }
  process.stdout.write(`og: ${ok} 件生成、${failed.length} 件失敗\n`);
  for (const f of failed) process.stdout.write(`  - ${f}\n`);
  // 失敗があってもビルドは止めない（非ゼロ終了しない）。
}

main();
