# aw-lp

ancient world のトップページ。データ由来のモーションと、完成済みビジュアルへの入口。

## 構成

```
ヒーロー   サイト名とリード。データ由来のモーション
入口       完成済みの3つ（マップ／年表／遺物）への導線
記事       公開済み記事の一覧（0 件なら出さない）
```

入口は配列で持ち、コードに直書きしない（`scripts/build.ts` の `entrances`）。`aw-compare` が
完成したら、この配列に 1 つ足すだけで入口が 4 つになる。

## ヒーローのモーション（採用案と使ったデータ）

**採用：案3 — クラスタごとの件数を点の密度で示す。**

- 座標は全件 null で地理配置に使えず、`era_start` を持つのは 3 件だけ。全 38 地点で欠けなく
  使えるデータは所属クラスタなので、これを採った。
- **使ったデータ項目**：`sites.cluster`（全 38 件）、`clusters.json`（順序・id）、クラスタ別の件数。
- 1 地点 = 1 点。クラスタごとに点をまとめ、点の数がそのまま密度になる（ひまわり充填で、件数が
  多いクラスタほど広がる）。点は順に出現する（CSS アニメーション、`--i` で遅延を段階化）。
- 装飾のための架空の図形は使わない。**CSS と inline SVG のみ。動画ファイル・画像ファイルを置かない。**

## コピー

指示どおりのコピーをそのまま使う（書き換え・追加をしない）。サイト名・リード・入口の説明・
記事の見出しは `src/render.ts` と `scripts/build.ts` に定数で持つ。

## 記事一覧

- `content/articles.json` を読む。初版は空配列。
- **公開済み記事が 0 件のときは、記事セクション自体を出さない。**「準備中」「近日公開」は出さない。
- 公開したら `articles.json` に `{ title, url, date? }` を足すだけでセクションが出る。

## リンク先（環境変数で注入）

| 入口 | 環境変数 | 既定値 |
|---|---|---|
| 遺跡年代マップ | `AW_MAP_BASE` | `/map` |
| 年表 | `AW_TIMELINE_BASE` | `/timeline` |
| 遺物 | `AW_OBJECTS_BASE` | `/objects` |

公開ドメインが未確定のため、環境変数が未設定でもビルドが通り、相対パスの既定値でリンクが張られる。

```bash
pnpm --filter @aw/lp build                          # 相対パス（既定）
AW_MAP_BASE=https://… pnpm --filter @aw/lp build     # 絶対 URL を注入
```

## 動きと可読性

- `prefers-reduced-motion: reduce` で静止する（点は最初から見えている）。
- **JavaScript が無効でも、リードと 3 つの入口が読める**（全内容を静的 HTML に埋め込む。モーションは
  CSS のみで、本文の表示を待たせない）。
- 画像ファイルを 1 点も含まない。

## デプロイ（Vercel）

- Root Directory: `packages/aw-lp`
- Install Command（リポジトリルートで）: `pnpm install`
- Build Command: `pnpm --filter @aw/lp build`（入口の URL は環境変数で注入）
- Output Directory: `dist`

## 完了状態（検証済み）

実ブラウザ（Chromium）で確認:

1. モーションなし（`prefers-reduced-motion: reduce`）・JavaScript 無効でも、リードと 3 つの入口が読める。
2. `prefers-reduced-motion: reduce` で静止する（点の opacity は 0.82 で静止）。
3. 画像ファイルを 1 点も含まずに成立している。
4. `content/articles.json` が空配列のとき、記事セクションが出ない。1 件入れると記事セクションが出る。
5. 環境変数が未設定でもビルドが通り、相対パス（`/map` 等）でリンクが張られる。注入すると絶対 URL になる。
