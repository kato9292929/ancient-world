# aw-map

年代スライダー付きの世界地図に、遺跡をピンで置く。

データは `@aw/data` の `sites.json` / `clusters.json` を参照する。着手時点で全地点の座標は null、
`coord_status` は `unlocated` 1 件（larak）と `unfetched` 37 件。これが埋まるのを待たずに動く。

## 地図の描画（外部タイル非依存）

同梱した静的な世界地形を描く。**外部のタイルサーバや API キーを必須にしない。** サンドボックス
（外部に到達できない環境）でも、リポジトリ内で完結して地図が出る。

- 地形データ：[`world-atlas`](https://github.com/topojson/world-atlas) の `countries-110m.json`
  （1:110m、TopoJSON）。
- 出所：[Natural Earth](https://www.naturalearthdata.com/)（**パブリックドメイン**）の
  Admin 0 country boundaries 1:110m を、`world-atlas` が TopoJSON に再配布したもの。
- ライセンス：`world-atlas` は ISC License（Michael Bostock）。元データの Natural Earth は
  パブリックドメイン。いずれも再配布可能。
- 投影：正距円筒図法（equirectangular）を自前で実装（`src/projection.ts`）。d3 等の追加依存なし。

地形データが読めない場合は、空の地図を出して正常終了せず、エラーで落とす（`src/map.ts`）。

## 画面

```
中央     地図。ピン
下部     年代スライダー
左       クラスタ一覧（件数付き）
右       選択中の地点の詳細パネル
```

### 年代スライダー

- 範囲は `sites` の `era_start` の最小〜最大（現データは 前9600年〜前54年）。線形。
- スライダーの値**以前に成立した地点**（`era_start <= 値`）のみピンにする。初期値は最大（全表示）。
- `era_start` が null（年代未取得）の verified 地点は、時間で絞れないので常に出す（年代不明で消さない）。

### ピン

- **`coord_status: "verified"` の地点だけ** 地図に描く。
- `unfetched` / `unlocated` / `ambiguous` の地点は地図に置かない。**左の一覧には残し**、状態ラベル
  （座標未取得 / 所在未特定 / 候補が複数）を付けて件数に数える。地図から消して見えなくしない。

### クラスタ一覧（左）

- `clusters.json` の順に表示。各クラスタの総件数と、内訳（座標未取得・所在未特定・候補が複数）を出す。
- 各地点を状態バッジ付きで並べる。クリックで詳細を開く。
- クラスタ見出しのクリックでそのクラスタに絞り込む。**上下キーでクラスタを巡回**する。

### 詳細パネル（右）

- 名称（日本語・ラテン文字）、国、年代と但し書き（`era_note` を省略して数字だけにしない）。
- `attributes` をクラスタごとの規則で表示。洪水層クラスタなら層の有無（present / **absent（調査済み）** /
  unknown を区別）・時期・備考。
- `summary` があれば出す。空なら出さない。
- `article_url` があれば「詳しく」リンク。null ならリンク自体を出さない。**「準備中」「Coming soon」は出さない。**

## URL 状態

- `?site=<id>` … 個別地点を開いた状態を復元
- `?year=<n>` … スライダー位置を復元
- `?cluster=<id>` … 絞り込みを復元

記事から特定のピンへ直リンクするために使う。

## OG 画像

`scripts/og.ts` が地点個別の OG 画像（SVG・1200×630）を `dist/og/<id>.svg` に静的生成する。生成できない
地点があってもビルドを止めず、件数を標準出力に出す（現状 38 件生成 / 0 件失敗）。ブラウザに依存しない。

## 開発・ビルド

```bash
pnpm --filter @aw/map dev       # 開発サーバ（Vite）
pnpm --filter @aw/map build     # dist/ に静的出力 + OG 生成
pnpm --filter @aw/map test      # 単体テスト
```

### デプロイ（Vercel）

- Root Directory: `packages/aw-map`
- Install Command（リポジトリルートで）: `pnpm install`
- Build Command: `pnpm --filter @aw/map build`
- Output Directory: `dist`

`aw-timeline` から関連地点リンクを受けるため、aw-map の公開 URL を timeline 側の `AW_MAP_BASE` に渡す。

## 完了状態（検証済み）

実ブラウザ（Chromium）で確認:

1. 全 `coord_status` が unlocated/unfetched の状態で起動し、左の一覧に 38 件、地図のピンは 0 件
   （所在未特定 1・座標未取得 37）。
2. 座標を 1 件だけ埋めたフィクスチャで、その 1 件だけがピンとして出る。
3. 座標 2 件のフィクスチャで、年代スライダーを動かすと表示件数が変わる（最大で 2 件 → 前5000年で 1 件）。
4. `?site=<id>` の URL で詳細パネルが開いた状態になる。

## テスト

尺度・絞り込み・件数集計（`filter.ts`）、URL 状態（`state.ts`）、投影（`projection.ts`）、詳細・一覧・
ピンの HTML 生成（`detail.ts` / `clusters.ts` / `map.ts`）を単体テストで検証している。
