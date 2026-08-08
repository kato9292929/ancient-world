# ancient world

遺跡・出来事のデータと、それを参照する複数のビジュアルを収めたモノレポ。

## 構成

共有データ（`aw-data`）を中心に、5本のビジュアルがそこを参照する。データが最初に立たないと他が着手できない、という依存関係のため、パッケージは分けつつ1リポジトリにまとめている。

```
packages/
  aw-data       共有データ。遺跡・出来事・クラスタと、スキーマ・検証・座標取得スクリプト
  aw-map        遺跡年代マップ（年代スライダー付き世界地図）      ※ aw-data を参照
  aw-timeline   縦スクロール年表                                  ※ aw-data を参照（座標は使わない）
  aw-objects    遺物の3Dビューア                                  ※ aw-data を参照
  aw-compare    比較スライダー（2状態の切り替え）
  aw-lp         ancient world のトップページ（モーションのLP）    ※ aw-data の実データ由来の形状
```

現時点で立っているもの:

- **`aw-data`** — スキーマ・検証・座標取得スクリプト・フィクスチャ単体テスト。台帳の全件を投入済み（sites 38 / events 14 / clusters 7）。座標は全件 null（未取得）
- **`aw-timeline`** — 縦スクロール年表。座標を使わないため座標取得を待たず完成。尺度は線形固定（案A）。近接カードは衝突回避＋引き出し線。JS 無効でも全項目が読める
- **`aw-map`** — 遺跡年代マップ。同梱の Natural Earth 地形（外部タイル非依存）に、年代スライダーとクラスタ一覧・詳細パネル。座標が全件 null でも「一覧 38・ピン 0・所在未特定 1」で起動する
- **`aw-objects`** — 遺物の3Dビューア（Weld-Blundell Prism）。寸法から形状をコード生成した模型。刻文は再現せず、WebGL 非対応時は模式図にフォールバック
- **`aw-lp`** — トップページ。クラスタ件数を点の密度で示すデータ由来のモーション（CSS/SVG のみ、画像0）と、3つの入口・記事一覧。JS 無効でも読める

残るは `aw-compare`（比較スライダー）のみ。題材が未確定のため着手前に判断が要る。

## 統合プレビュー

4 つのビジュアルのビルド結果を 1 か所に集め、1 ファイルから全部を回れる状態を作れる。

```bash
pnpm preview:build          # preview/ に map / timeline / objects / lp を集約
```

`preview/index.html` を開くと 4 つへのリンクが出る。`preview/` は生成物なので Git に含めない
（`.gitignore` 済み）。

`file://` で開いたときの挙動（Chromium で確認）:

| パッケージ | 種別 | `file://` |
|---|---|---|
| 年表 / トップページ | 単一の静的 HTML（スクリプト inline） | そのまま開ける |
| マップ / 遺物 | Vite の外部 ES module を読む | Chromium では動作を確認。`file://` の module を弾くブラウザでは空表示 |

`file://` で module が読めないブラウザでは、ローカルサーバで開く:

```bash
npx serve preview
# または: python3 -m http.server -d preview 8000  → http://localhost:8000/
```

## デプロイ（Vercel・未実施）

> **このリポジトリではまだ Vercel へデプロイしていない（サンドボックスから外部サービスに接続
> できないため）。** 以下は手順の記録。実施は別環境で行う。`vercel.json` はどのパッケージにも
> 置いていない（未設定）ため、下記は各プロジェクトのダッシュボード設定を前提にしている。

各パッケージを**別プロジェクト**として登録し、個別 URL で見せる。パッケージごとの設定（`package.json`
の `build` スクリプトと本 README から確認できる範囲）:

| パッケージ | Root Directory | Build Command | Output Directory |
|---|---|---|---|
| `@aw/map` | `packages/aw-map` | `pnpm --filter @aw/map build` | `dist` |
| `@aw/timeline` | `packages/aw-timeline` | `pnpm --filter @aw/timeline build` | `dist` |
| `@aw/objects` | `packages/aw-objects` | `pnpm --filter @aw/objects build` | `dist` |
| `@aw/lp` | `packages/aw-lp` | `pnpm --filter @aw/lp build` | `dist` |

- **Install Command**：ワークスペース依存（`@aw/data`）を解決するため、リポジトリルートで
  `pnpm install` を走らせる必要がある。Vercel のモノレポ検出でルートインストールになるか、
  ルート指定が要るかは**未確認**（実際に接続して確認する）。
- **PR ごとのプレビュー URL**：Vercel に Git 連携すると各 PR に自動でプレビューデプロイが発行される
  のが標準挙動だが、本リポジトリでは**未接続・未確認**。
- **環境変数の設定先**：`aw-lp` と `aw-timeline` は入口・地点リンクの base を環境変数で受ける。
  各プロジェクトの Environment Variables に設定する:
  - `aw-lp`：`AW_MAP_BASE` / `AW_TIMELINE_BASE` / `AW_OBJECTS_BASE`（各ビジュアルの公開 URL）
  - `aw-timeline`：`AW_MAP_BASE`（aw-map の公開 URL。`?site=` リンク用）
  - 値は各ビジュアルの公開 URL に依存する。**公開ドメインが未確定のため具体値は未定。**未設定でも
    相対パスの既定値でビルドは通る。

## デプロイ単位

モノレポだが、デプロイ単位はパッケージごとに分離できる形にしてある。制作事例として個別URLで見せられるよう、Vercel では各パッケージを別プロジェクトとして設定する想定（各プロジェクトの Root Directory に `packages/aw-map` などを指定する）。

## 開発

```bash
pnpm install        # ワークスペース全体の依存を導入
pnpm validate       # 各パッケージの検証（aw-data のスキーマ検証を含む）
pnpm test           # 各パッケージの単体テスト
pnpm typecheck      # 型チェック
```

Node.js 20 以上、pnpm 10 系で確認している。

## 座標データについて

`aw-data` の遺跡座標は、サンドボックス（外部APIに到達できない環境）では取得できないため、初期状態では全件 `null` / `coord_status: "unfetched"` で入る。取得スクリプトは書いてあるが未実行。詳細は [`packages/aw-data/README.md`](packages/aw-data/README.md) を参照。
