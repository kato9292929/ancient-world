// 座標取得の「純粋な部分」。ネットワークに触れず、レスポンス（またはそれを模した
// フィクスチャ）を候補に変換し、候補から結論を出す。fetch-coords.ts と単体テストの
// 両方がここを使う。ネットワーク I/O は fetch-coords.ts 側に閉じ込める。

export interface CoordCandidate {
  lat: number;
  lng: number;
  source: "wikidata" | "pleiades";
  /** 参照した識別子。Q コードまたは Pleiades ID。 */
  identifier: string;
}

export type CoordResolution =
  | {
      status: "verified";
      lat: number;
      lng: number;
      source: "wikidata" | "pleiades";
      identifier: string;
    }
  | { status: "unfetched"; reason: "no-result" }
  | { status: "ambiguous"; candidates: CoordCandidate[] };

/** "Point(lng lat)" 形式の WKT リテラルを [lng, lat] に分解する。失敗したら null。 */
export function parsePointWkt(wkt: string): { lat: number; lng: number } | null {
  const m = /^\s*Point\(\s*(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*\)\s*$/i.exec(wkt);
  if (!m) return null;
  const lng = Number(m[1]);
  const lat = Number(m[2]);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  return { lat, lng };
}

/** Wikidata エンティティ URI から Q コードを取り出す。 */
export function qCodeFromUri(uri: string): string | null {
  const m = /\/(Q\d+)$/.exec(uri);
  return m ? m[1]! : null;
}

/**
 * Wikidata SPARQL の JSON レスポンスを候補配列に変換する。
 * 期待する形は results.bindings[] で、各 binding が
 *   place: エンティティ URI, coord: "Point(lng lat)" リテラル
 * を持つこと。座標が読めない行は捨てる。
 */
export function parseWikidataResponse(json: unknown): CoordCandidate[] {
  const bindings = (json as any)?.results?.bindings;
  if (!Array.isArray(bindings)) return [];
  const out: CoordCandidate[] = [];
  const seen = new Set<string>();
  for (const b of bindings) {
    const uri: unknown = b?.place?.value;
    const coordLiteral: unknown = b?.coord?.value;
    if (typeof uri !== "string" || typeof coordLiteral !== "string") continue;
    const q = qCodeFromUri(uri);
    const point = parsePointWkt(coordLiteral);
    if (!q || !point) continue;
    if (seen.has(q)) continue; // 同一エンティティの重複行は 1 件に畳む
    seen.add(q);
    out.push({ lat: point.lat, lng: point.lng, source: "wikidata", identifier: q });
  }
  return out;
}

/**
 * Pleiades の JSON レスポンス（1 place リソース）を 1 候補に変換する。
 * reprPoint は [lng, lat] の順。読めなければ null。
 */
export function parsePleiadesResponse(json: unknown): CoordCandidate | null {
  const obj = json as any;
  const repr = obj?.reprPoint;
  if (!Array.isArray(repr) || repr.length < 2) return null;
  const lng = Number(repr[0]);
  const lat = Number(repr[1]);
  if (!Number.isFinite(lat) || !Number.isFinite(lng)) return null;
  const id = obj?.id;
  const identifier =
    typeof id === "string" && id.length > 0 ? `pleiades:${id}` : "pleiades:unknown";
  return { lat, lng, source: "pleiades", identifier };
}

/**
 * 候補群から結論を出す。
 *  - 0 件 → unfetched。近隣や中心座標で埋めない。
 *  - 1 件 → verified。
 *  - 2 件以上 → ambiguous。自動選択しない。呼び出し側が候補を出力して当該地点をスキップする。
 */
export function resolveCoord(candidates: CoordCandidate[]): CoordResolution {
  if (candidates.length === 0) return { status: "unfetched", reason: "no-result" };
  if (candidates.length === 1) {
    const c = candidates[0]!;
    return {
      status: "verified",
      lat: c.lat,
      lng: c.lng,
      source: c.source,
      identifier: c.identifier,
    };
  }
  return { status: "ambiguous", candidates };
}
