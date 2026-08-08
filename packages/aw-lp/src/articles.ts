// 記事一覧のデータ。content/articles.json を読む。初版は空配列。
// 公開済み記事だけを載せる。0 件ならセクション自体を出さない（呼び出し側で判定）。

export interface Article {
  title: string;
  url: string;
  date?: string;
}

/** articles.json を安全に正規化する。title と url を持つ項目だけ拾う。 */
export function parseArticles(data: unknown): Article[] {
  if (!Array.isArray(data)) return [];
  const out: Article[] = [];
  for (const item of data) {
    if (
      item &&
      typeof item === "object" &&
      typeof (item as { title?: unknown }).title === "string" &&
      typeof (item as { url?: unknown }).url === "string"
    ) {
      const a = item as { title: string; url: string; date?: unknown };
      out.push({
        title: a.title,
        url: a.url,
        date: typeof a.date === "string" ? a.date : undefined,
      });
    }
  }
  return out;
}
