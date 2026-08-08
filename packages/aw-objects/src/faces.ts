// 面ごとの説明文。記事側で用意する content/faces.json を読む。空でよい（初期は空）。
// 中身が空でもエラーにせず、面の説明欄が出ないだけにする。

export interface FaceDescription {
  /** 面のインデックス（0〜3）。 */
  face: number;
  title?: string;
  body?: string;
}

/** faces.json（未知の形でも安全に）を FaceDescription[] に正規化する。空なら []。 */
export function parseFaces(data: unknown): FaceDescription[] {
  if (!Array.isArray(data)) return [];
  const out: FaceDescription[] = [];
  for (const item of data) {
    if (item && typeof item === "object" && typeof (item as { face?: unknown }).face === "number") {
      const f = item as { face: number; title?: unknown; body?: unknown };
      out.push({
        face: f.face,
        title: typeof f.title === "string" ? f.title : undefined,
        body: typeof f.body === "string" ? f.body : undefined,
      });
    }
  }
  return out;
}

/** 指定した面の説明を返す。無ければ null。 */
export function faceFor(faces: FaceDescription[], index: number): FaceDescription | null {
  return faces.find((f) => f.face === index) ?? null;
}
