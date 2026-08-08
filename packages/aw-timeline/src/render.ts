// events.json / sites.json から静的な年表 HTML を組む。
//
// 方針:
//   - 全出来事を古い順に、線形尺度（案A）の位置へ絶対配置する。年ごとの実際の間隔が縦の距離に
//     出る。前1000年以降は出来事が無く、空白として見える。それでよい（案A）。
//   - JavaScript が無くても、年代順に並んだ静的な一覧として全項目が読める。
//   - スクロール連動の年代表示は JS による上乗せ。JS 無効時は隠す（誤読させない）。
import type { AwEvent, Site } from "@aw/data";
import {
  type Domain,
  computeDomain,
  positionFraction,
  formatEra,
  shownEvents,
  eventBand,
  mapSiteUrl,
  axisTicks,
  formatYear,
} from "./scale.js";

export interface RenderOptions {
  currentYear: number;
  /** aw-map のデプロイ先。関連地点リンクの base。 */
  mapBase: string;
  /** 1 年あたりのピクセル。縦の総高を決める。 */
  pxPerYear?: number;
  css: string;
  enhanceJs: string;
}

export function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function pct(f: number): string {
  return (f * 100).toFixed(3) + "%";
}

function relatedSitesHtml(e: AwEvent, siteById: Map<string, Site>, mapBase: string): string {
  if (e.site_ids.length === 0) return "";
  const items = e.site_ids.map((id) => {
    const site = siteById.get(id);
    const label = site ? site.name_ja : id;
    const href = mapSiteUrl(id, mapBase);
    return `<li><a href="${escapeHtml(href)}">${escapeHtml(label)}</a></li>`;
  });
  return `<ul class="sites" aria-label="関連地点">${items.join("")}</ul>`;
}

function eventHtml(e: AwEvent, d: Domain, siteById: Map<string, Site>, mapBase: string): string {
  const band = eventBand(e, d);
  const { yearLabel, note } = formatEra(e.era_start, e.era_end, e.era_note);
  const noteHtml = note ? ` <span class="note">${escapeHtml(note)}</span>` : "";
  // 幅のあるものは band を描く（点にしない）。
  const bandHtml =
    band.height > 0
      ? `<span class="band" style="height:${pct(band.height)}" aria-hidden="true"></span>`
      : "";
  const article = e.article_url
    ? `<a class="article" href="${escapeHtml(e.article_url)}">記事を読む</a>`
    : "";
  const dataYear = `${yearLabel}${note ? " " + note : ""}`;
  const desc = e.description.trim()
    ? `<p class="desc">${escapeHtml(e.description)}</p>`
    : "";
  return `<li class="event" style="top:${pct(band.top)}" data-year="${escapeHtml(dataYear)}">
  ${bandHtml}
  <article class="card">
    <p class="era">${escapeHtml(yearLabel)}${noteHtml}</p>
    <h2>${escapeHtml(e.title)}</h2>
    ${desc}
    ${relatedSitesHtml(e, siteById, mapBase)}
    ${article}
  </article>
</li>`;
}

function axisHtml(d: Domain): string {
  const ticks = axisTicks(d).map((y) => {
    const f = positionFraction(y, d);
    return `<li class="tick" style="top:${pct(f)}"><span>${escapeHtml(formatYear(y))}</span></li>`;
  });
  return `<ol class="axis" aria-hidden="true">${ticks.join("")}</ol>`;
}

export function renderTimelineHtml(
  events: AwEvent[],
  sites: Site[],
  opts: RenderOptions,
): string {
  const shown = shownEvents(events);
  const hidden = events.length - shown.length;
  const years = events.flatMap((e) =>
    e.era_end === null ? [e.era_start] : [e.era_start, e.era_end],
  );
  const domain = computeDomain(years, opts.currentYear);
  const pxPerYear = opts.pxPerYear ?? 0.6;
  const heightPx = Math.max(1200, Math.round((domain.max - domain.min) * pxPerYear));
  const siteById = new Map(sites.map((s) => [s.id, s]));

  const eventsHtml = shown.map((e) => eventHtml(e, domain, siteById, opts.mapBase)).join("\n");

  const emptyNote =
    shown.length === 0
      ? `<p class="empty">まだ出来事のデータが入っていません。<code>aw-data</code> の <code>events.json</code> が投入されると、ここに古い順で並びます。</p>`
      : "";

  const hiddenNote =
    hidden > 0
      ? `<p class="hidden-note">年代が未取得（<code>era_status: "unfetched"</code>）の ${hidden} 件は、位置を推測しないため年表に出していません。</p>`
      : "";

  return `<!doctype html>
<html lang="ja" class="no-js">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>年表 — ancient world</title>
<meta name="description" content="前1万年から現在までを線形で縦に貫く年表。">
<script>document.documentElement.classList.remove('no-js');document.documentElement.classList.add('js');</script>
<style>${opts.css}</style>
</head>
<body>
<header class="page-head">
  <h1>年表</h1>
  <p class="lede">前1万年から現在までを、線形の尺度で縦に貫く。縮尺は一定。前1000年以降に
  出来事が無い区間は、空白のまま見せる。</p>
  ${hiddenNote}
</header>
<div class="readout" data-year-readout aria-live="polite"><span class="readout-label">表示中の年代</span><span class="readout-year">${escapeHtml(formatYear(domain.min))}</span></div>
<main class="timeline" style="height:${heightPx}px">
  ${axisHtml(domain)}
  <ol class="events">
${eventsHtml}
  </ol>
  ${emptyNote}
</main>
<script type="module">${opts.enhanceJs}</script>
</body>
</html>
`;
}
