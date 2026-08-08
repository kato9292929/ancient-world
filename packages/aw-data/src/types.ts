// aw-data の型。sites.json / events.json / clusters.json のスキーマに対応する。

// verified=座標確定。ambiguous=複数候補が返り未確定（人手で選ぶ）。unfetched=未取得。
// unfetched と ambiguous を区別する：手つかずの地点と、候補は出たが確定していない地点を混ぜない。
// verified=座標確定。ambiguous=複数候補が返り未確定（人手で選ぶ）。unlocated=所在がそもそも
// 特定されていない（比定地未確定など。取得対象外）。unfetched=まだ取得していない。
// unfetched / ambiguous / unlocated を区別する：手つかず／候補は出たが未確定／取得しても
// 埋まらない、を混ぜない。unlocated を unfetched に混ぜると未取得件数が永久に減らない。
export type CoordStatus = "verified" | "ambiguous" | "unlocated" | "unfetched";
// wikidata / pleiades / other。other は Wikidata・Pleiades 以外（行政資料・地理院など）で、
// coord_ref に出所の URL か文書名を必ず持たせる。「推測で埋めない」は維持される。
export type CoordSource = "wikidata" | "pleiades" | "other" | null;
export type EraStatus = "sourced" | "unfetched";

export interface Site {
  id: string;
  name_ja: string;
  name_en: string;
  cluster: string;
  country: string;
  lat: number | null;
  lng: number | null;
  coord_source: CoordSource;
  /** 出所の識別子・文書名。wikidata=Qコード、pleiades=ID、other=出所URLか文書名（必須）。 */
  coord_ref: string | null;
  coord_status: CoordStatus;
  era_start: number | null;
  era_end: number | null;
  era_status: EraStatus;
  era_note: string;
  attributes: Record<string, unknown>;
  article_url: string | null;
  summary: string[];
}

export interface AwEvent {
  id: string;
  title: string;
  description: string;
  era_start: number;
  era_end: number | null;
  era_status: EraStatus;
  era_note: string;
  site_ids: string[];
  article_url: string | null;
}

export interface Cluster {
  id: string;
  name_ja: string;
  name_en?: string;
  note?: string;
}

// 洪水層クラスタの attributes の形。"absent" と "unknown" を区別する。
export interface FloodLayerAttributes {
  flood_layer: "present" | "absent" | "unknown";
  layer_period: string | null;
  layer_note: string | null;
}
