// 右の詳細パネル。選択中の地点の HTML を組む。純粋関数。
import type { Site } from "@aw/data";
import { STATUS_LABEL } from "./filter.js";

export function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function formatYear(n: number): string {
  if (n < 0) return `前${-n}年`;
  if (n > 0) return `${n}年`;
  return "0年";
}

// 年代の行。era_status: sourced のときだけ出す。unfetched は年代の行も era_note も出さない。
// 数字だけを出さない：era_note があれば必ず添える。
function eraLine(s: Site): string {
  if (s.era_status !== "sourced" || s.era_start === null) return "";
  const year = formatYear(s.era_start);
  const range =
    s.era_end !== null && s.era_end !== s.era_start ? `${year}〜${formatYear(s.era_end)}` : year;
  const note = s.era_note.trim();
  const noteHtml = note ? ` <span class="note">${escapeHtml(note)}</span>` : "";
  return `<p class="era">${escapeHtml(range)}${noteHtml}</p>`;
}

// 一般的な注記。年代の有無に関わらず、あれば出す。無ければ欄を出さない。
function noteLine(s: Site): string {
  if (!s.note || s.note.trim() === "") return "";
  return `<p class="note-line">${escapeHtml(s.note)}</p>`;
}

// 洪水層クラスタの属性表示。present/absent/unknown を区別して出す。
function floodAttrs(attrs: Record<string, unknown>): string {
  if (!("flood_layer" in attrs)) return "";
  const fl = attrs["flood_layer"];
  const label =
    fl === "present" ? "あり" : fl === "absent" ? "なし（調査済み）" : "不明";
  const period = typeof attrs["layer_period"] === "string" ? attrs["layer_period"] : null;
  const note = typeof attrs["layer_note"] === "string" ? attrs["layer_note"] : null;
  const rows = [`<div class="attr"><dt>洪水層</dt><dd>${escapeHtml(label)}</dd></div>`];
  if (period) rows.push(`<div class="attr"><dt>時期</dt><dd>${escapeHtml(period)}</dd></div>`);
  if (note) rows.push(`<div class="attr"><dt>備考</dt><dd>${escapeHtml(note)}</dd></div>`);
  return `<dl class="attrs">${rows.join("")}</dl>`;
}

function summaryList(summary: string[]): string {
  if (summary.length === 0) return ""; // 空なら出さない
  return `<ul class="summary">${summary.map((t) => `<li>${escapeHtml(t)}</li>`).join("")}</ul>`;
}

/** 詳細パネルの HTML。site が null なら未選択メッセージ。 */
export function renderDetail(site: Site | null): string {
  if (!site) {
    return `<p class="detail-empty">地図のピン、または左の一覧から地点を選ぶと、ここに詳細が出ます。</p>`;
  }
  const statusLabel = STATUS_LABEL[site.coord_status];
  const coordLine =
    site.coord_status === "verified" && site.lat !== null && site.lng !== null
      ? `<p class="coord">${site.lat.toFixed(4)}, ${site.lng.toFixed(4)}<span class="src">（${escapeHtml(site.coord_source ?? "")}）</span></p>`
      : `<p class="coord coord-missing">${escapeHtml(statusLabel)}</p>`;

  // article_url があれば「詳しく」を出す。null ならリンク自体を出さない。「準備中」は出さない。
  const article = site.article_url
    ? `<a class="more" href="${escapeHtml(site.article_url)}">詳しく</a>`
    : "";

  return `<article class="detail">
  <h2>${escapeHtml(site.name_ja)}</h2>
  <p class="name-en">${escapeHtml(site.name_en)}</p>
  <p class="country">${escapeHtml(site.country)}</p>
  ${eraLine(site)}
  ${noteLine(site)}
  ${floodAttrs(site.attributes as Record<string, unknown>)}
  ${coordLine}
  ${summaryList(site.summary)}
  ${article}
</article>`;
}
