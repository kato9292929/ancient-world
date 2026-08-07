// aw-data の型。sites.json / events.json / clusters.json のスキーマに対応する。

// verified=座標確定。ambiguous=複数候補が返り未確定（人手で選ぶ）。unfetched=未取得。
// unfetched と ambiguous を区別する：手つかずの地点と、候補は出たが確定していない地点を混ぜない。
export type CoordStatus = "verified" | "ambiguous" | "unfetched";
export type CoordSource = "wikidata" | "pleiades" | null;
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
  coord_status: CoordStatus;
  era_start: number;
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
  name_en: string;
  note?: string;
}

// 洪水層クラスタの attributes の形。"absent" と "unknown" を区別する。
export interface FloodLayerAttributes {
  flood_layer: "present" | "absent" | "unknown";
  layer_period: string | null;
  layer_note: string | null;
}
