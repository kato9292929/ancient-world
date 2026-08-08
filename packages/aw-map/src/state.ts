// URL クエリと画面状態の相互変換。純粋関数。?site= / ?year= / ?cluster= を復元・保存する。
// 記事から特定のピンへ直リンクするために使う。

export interface ViewState {
  site: string | null;
  year: number | null;
  cluster: string | null;
}

export function parseState(search: string): ViewState {
  const p = new URLSearchParams(search.startsWith("?") ? search.slice(1) : search);
  const site = p.get("site");
  const cluster = p.get("cluster");
  const yearRaw = p.get("year");
  let year: number | null = null;
  if (yearRaw !== null && yearRaw !== "") {
    const n = Number.parseInt(yearRaw, 10);
    if (Number.isFinite(n)) year = n;
  }
  return {
    site: site && site.length > 0 ? site : null,
    year,
    cluster: cluster && cluster.length > 0 ? cluster : null,
  };
}

/** null のキーは出さない。空クエリなら "" を返す。 */
export function serializeState(s: ViewState): string {
  const p = new URLSearchParams();
  if (s.cluster) p.set("cluster", s.cluster);
  if (s.year !== null) p.set("year", String(s.year));
  if (s.site) p.set("site", s.site);
  const q = p.toString();
  return q ? "?" + q : "";
}

/** year をスライダーの範囲に丸める。 */
export function clampYear(year: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, year));
}
