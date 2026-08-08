// 地点の絞り込みと件数集計。純粋関数のみ。DOM を持たない。
import type { Site, Cluster } from "@aw/data";

export type MapStatus = Site["coord_status"]; // verified | ambiguous | unlocated | unfetched

// 座標状態のラベル。verified はピンになるので一覧ではラベルを出さない。
export const STATUS_LABEL: Record<MapStatus, string> = {
  verified: "",
  ambiguous: "候補が複数",
  unlocated: "所在未特定",
  unfetched: "座標未取得",
};

/** era_start の最小・最大（null は除く）。スライダーの範囲に使う。データが無ければ既定。 */
export function eraBounds(sites: Site[]): { min: number; max: number } {
  const eras = sites
    .map((s) => s.era_start)
    .filter((v): v is number => v !== null);
  if (eras.length === 0) return { min: -10000, max: 0 };
  return { min: Math.min(...eras), max: Math.max(...eras) };
}

/**
 * 地図に描くピン。座標が確定（verified）した地点だけ。スライダーの値以前に成立したもの。
 * era_start が null（年代未取得）の verified 地点は、時間で絞れないので常に出す
 * （所在が分かっている地点を年代不明で消さない）。cluster 指定があればそれで絞る。
 */
export function visiblePins(
  sites: Site[],
  year: number,
  clusterId: string | null,
): Site[] {
  return sites.filter(
    (s) =>
      s.coord_status === "verified" &&
      s.lat !== null &&
      s.lng !== null &&
      (s.era_start === null || s.era_start <= year) &&
      (clusterId === null || s.cluster === clusterId),
  );
}

export interface ClusterCount {
  id: string;
  total: number;
  verified: number;
  ambiguous: number;
  unlocated: number;
  unfetched: number;
}

/** clusters.json の順で、各クラスタの件数と状態内訳を返す。 */
export function clusterCounts(sites: Site[], clusters: Cluster[]): ClusterCount[] {
  return clusters.map((c) => {
    const cs = sites.filter((s) => s.cluster === c.id);
    const by = (st: MapStatus) => cs.filter((s) => s.coord_status === st).length;
    return {
      id: c.id,
      total: cs.length,
      verified: by("verified"),
      ambiguous: by("ambiguous"),
      unlocated: by("unlocated"),
      unfetched: by("unfetched"),
    };
  });
}

/** あるクラスタに属する地点を、sites.json の並びのまま返す。 */
export function sitesInCluster(sites: Site[], clusterId: string): Site[] {
  return sites.filter((s) => s.cluster === clusterId);
}
