// 左のクラスタ一覧。clusters.json の順に、各クラスタの件数と、その地点を状態ラベル付きで並べる。
// 座標が無い地点も一覧に残す（地図から消して見えなくしない）。純粋な HTML 生成。
import type { Site, Cluster } from "@aw/data";
import { clusterCounts, sitesInCluster, STATUS_LABEL } from "./filter.js";
import { escapeHtml } from "./detail.js";

export function renderClusters(
  sites: Site[],
  clusters: Cluster[],
  selectedCluster: string | null,
  selectedSite: string | null,
): string {
  const counts = new Map(clusterCounts(sites, clusters).map((c) => [c.id, c]));

  const sections = clusters.map((c) => {
    const cc = counts.get(c.id)!;
    const activeCluster = c.id === selectedCluster ? " is-active" : "";
    // 件数と、うち座標未取得の件数。所在未特定・候補が複数があれば併記する。
    const extra: string[] = [];
    if (cc.unfetched > 0) extra.push(`座標未取得 ${cc.unfetched}`);
    if (cc.unlocated > 0) extra.push(`所在未特定 ${cc.unlocated}`);
    if (cc.ambiguous > 0) extra.push(`候補が複数 ${cc.ambiguous}`);
    const extraHtml = extra.length ? `<span class="cl-breakdown">${escapeHtml(extra.join(" / "))}</span>` : "";

    const items = sitesInCluster(sites, c.id)
      .map((s) => {
        const label = STATUS_LABEL[s.coord_status];
        const badge = label
          ? `<span class="badge badge-${s.coord_status}">${escapeHtml(label)}</span>`
          : `<span class="badge badge-verified">ピン</span>`;
        const activeSite = s.id === selectedSite ? " is-selected" : "";
        return `<li><button class="site-row${activeSite}" data-site="${escapeHtml(s.id)}">
          <span class="site-name">${escapeHtml(s.name_ja)}</span>${badge}
        </button></li>`;
      })
      .join("");

    return `<section class="cluster${activeCluster}" data-cluster="${escapeHtml(c.id)}">
      <button class="cluster-head" data-cluster-head="${escapeHtml(c.id)}">
        <span class="cl-name">${escapeHtml(c.name_ja)}</span>
        <span class="cl-count">${cc.total}</span>
      </button>
      ${extraHtml}
      <ul class="site-list">${items}</ul>
    </section>`;
  });

  const total = sites.length;
  return `<div class="clusters-head">全 ${total} 地点${selectedCluster ? `（<button class="clear-filter" data-clear>絞り込み解除</button>）` : ""}</div>
  ${sections.join("")}`;
}
