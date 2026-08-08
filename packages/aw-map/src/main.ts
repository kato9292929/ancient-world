// エントリ。データを読み、地図・スライダー・クラスタ一覧・詳細パネルを組み、状態を配線する。
import { sites, clusters } from "@aw/data";
import type { Site } from "@aw/data";
import { buildMapSvg, pinsSvg } from "./map.js";
import { renderClusters } from "./clusters.js";
import { renderDetail } from "./detail.js";
import { eraBounds, visiblePins } from "./filter.js";
import { parseState, serializeState, clampYear, type ViewState } from "./state.js";

// データ読み込みの健全性を確認する。空・不正なら空の地図を出さず失敗させる。
if (!Array.isArray(sites) || sites.length === 0) {
  throw new Error("sites データが読み込めませんでした（空または不正）");
}
if (!Array.isArray(clusters) || clusters.length === 0) {
  throw new Error("clusters データが読み込めませんでした（空または不正）");
}

const siteById = new Map<string, Site>(sites.map((s) => [s.id, s]));
const clusterIds = new Set(clusters.map((c) => c.id));
const bounds = eraBounds(sites);

function $(sel: string): HTMLElement {
  const el = document.querySelector(sel);
  if (!el) throw new Error(`要素が見つかりません: ${sel}`);
  return el as HTMLElement;
}

// ---- 状態 ----
const initial = parseState(window.location.search);
const state: ViewState = {
  site: initial.site && siteById.has(initial.site) ? initial.site : null,
  cluster: initial.cluster && clusterIds.has(initial.cluster) ? initial.cluster : null,
  year: initial.year !== null ? clampYear(initial.year, bounds.min, bounds.max) : bounds.max,
};

// ---- 一度だけ組む地図 ----
$("#map").innerHTML = buildMapSvg();
const pinsGroup = document.querySelector<SVGGElement>("#map .pins")!;

// ---- スライダー ----
const slider = $("#year-slider") as unknown as HTMLInputElement;
slider.min = String(bounds.min);
slider.max = String(bounds.max);
slider.step = "1";
slider.value = String(state.year ?? bounds.max);

function formatYear(n: number): string {
  return n < 0 ? `前${-n}年` : n > 0 ? `${n}年` : "0年";
}

function updateUrl(): void {
  const q = serializeState(state);
  const url = q || window.location.pathname;
  window.history.replaceState(null, "", url);
}

function renderPins(): void {
  const year = state.year ?? bounds.max;
  const pins = visiblePins(sites, year, state.cluster);
  pinsGroup.innerHTML = pinsSvg(pins, state.site);
  $("#pin-count").textContent = `ピン ${pins.length} 件`;
  for (const g of pinsGroup.querySelectorAll<SVGGElement>(".pin")) {
    const id = g.getAttribute("data-id");
    if (id) g.addEventListener("click", () => selectSite(id));
  }
}

function renderLeft(): void {
  $("#clusters").innerHTML = renderClusters(sites, clusters, state.cluster, state.site);
  for (const b of $("#clusters").querySelectorAll<HTMLElement>("[data-site]")) {
    b.addEventListener("click", () => selectSite(b.getAttribute("data-site")!));
  }
  for (const b of $("#clusters").querySelectorAll<HTMLElement>("[data-cluster-head]")) {
    b.addEventListener("click", () => toggleCluster(b.getAttribute("data-cluster-head")!));
  }
  const clear = $("#clusters").querySelector<HTMLElement>("[data-clear]");
  if (clear) clear.addEventListener("click", () => { state.cluster = null; renderAll(); });
}

function renderDetailPanel(): void {
  const site = state.site ? siteById.get(state.site) ?? null : null;
  $("#detail").innerHTML = renderDetail(site);
  const more = $("#detail").querySelector<HTMLElement>(".more");
  // 記事リンクはそのまま（外部遷移）。
  void more;
}

function renderYearLabel(): void {
  $("#year-label").textContent = formatYear(state.year ?? bounds.max);
}

function renderAll(): void {
  renderPins();
  renderLeft();
  renderDetailPanel();
  renderYearLabel();
  updateUrl();
}

function selectSite(id: string): void {
  if (!siteById.has(id)) return;
  state.site = id;
  renderAll();
}

function toggleCluster(id: string): void {
  state.cluster = state.cluster === id ? null : id;
  renderAll();
}

// ---- スライダー操作 ----
slider.addEventListener("input", () => {
  state.year = clampYear(Number.parseInt(slider.value, 10), bounds.min, bounds.max);
  renderPins();
  renderYearLabel();
  updateUrl();
});

// ---- 上下キーでクラスタを巡回 ----
window.addEventListener("keydown", (e) => {
  if (e.key !== "ArrowUp" && e.key !== "ArrowDown") return;
  const tag = (e.target as HTMLElement | null)?.tagName;
  if (tag === "INPUT") return; // スライダー操作を邪魔しない
  e.preventDefault();
  const ids = clusters.map((c) => c.id);
  const cur = state.cluster ? ids.indexOf(state.cluster) : -1;
  const next =
    e.key === "ArrowDown"
      ? (cur + 1) % ids.length
      : (cur - 1 + ids.length) % ids.length;
  state.cluster = ids[next]!;
  renderAll();
});

// ---- 戻る/進む ----
window.addEventListener("popstate", () => {
  const s = parseState(window.location.search);
  state.site = s.site && siteById.has(s.site) ? s.site : null;
  state.cluster = s.cluster && clusterIds.has(s.cluster) ? s.cluster : null;
  state.year = s.year !== null ? clampYear(s.year, bounds.min, bounds.max) : bounds.max;
  slider.value = String(state.year);
  renderAll();
});

renderAll();
