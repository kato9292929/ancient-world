// トップページの静的 HTML を組む。JavaScript 無効でもリードと入口が読める形にする。
// モーションは CSS/SVG のみ（動画ファイル・画像ファイルを置かない）。
import type { Site, Cluster } from "@aw/data";
import { heroSvg } from "./hero.js";
import type { Article } from "./articles.js";

// --- 指定されたコピー（そのまま使う。書き換え・追加をしない）---
const SITE_NAME = "ancient world";
const LEAD = "古代の遺跡と資料について、記録されている内容と、現在の研究状況を並べます。";
const ARTICLES_HEADING = "記事";

export interface Entrance {
  key: string;
  title: string;
  desc: string;
  href: string;
}

export interface RenderOptions {
  /** 入口。配列で持ち、直書きしない。aw-compare 完成時にここへ 1 つ足せば 4 つになる。 */
  entrances: Entrance[];
  articles: Article[];
  css: string;
}

export function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function entrancesHtml(entrances: Entrance[]): string {
  const items = entrances
    .map(
      (e) => `<li class="entrance">
      <a href="${escapeHtml(e.href)}">
        <span class="entrance-title">${escapeHtml(e.title)}</span>
        <span class="entrance-desc">${escapeHtml(e.desc)}</span>
      </a>
    </li>`,
    )
    .join("\n");
  return `<nav class="entrances" aria-label="入口"><ul>${items}</ul></nav>`;
}

// 記事 0 件ならセクション自体を出さない。「準備中」「近日公開」を出さない。
function articlesHtml(articles: Article[]): string {
  if (articles.length === 0) return "";
  const items = articles
    .map((a) => {
      const date = a.date ? `<span class="article-date">${escapeHtml(a.date)}</span>` : "";
      return `<li class="article"><a href="${escapeHtml(a.url)}">${escapeHtml(a.title)}</a>${date}</li>`;
    })
    .join("\n");
  return `<section class="articles" aria-label="${escapeHtml(ARTICLES_HEADING)}">
    <h2>${escapeHtml(ARTICLES_HEADING)}</h2>
    <ul>${items}</ul>
  </section>`;
}

export function renderLp(
  sites: Site[],
  clusters: Cluster[],
  opts: RenderOptions,
): string {
  const hero = heroSvg(sites, clusters, { width: 960, height: 320 });

  return `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${escapeHtml(SITE_NAME)}</title>
<meta name="description" content="${escapeHtml(LEAD)}">
<style>${opts.css}</style>
</head>
<body>
<header class="hero">
  <div class="hero-motion" aria-hidden="true">${hero}</div>
  <div class="hero-copy">
    <h1 class="site-name">${escapeHtml(SITE_NAME)}</h1>
    <p class="lead">${escapeHtml(LEAD)}</p>
  </div>
</header>
<main>
  ${entrancesHtml(opts.entrances)}
  ${articlesHtml(opts.articles)}
</main>
</body>
</html>
`;
}

export { SITE_NAME, LEAD, ARTICLES_HEADING };
