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

残り（`aw-objects` / `aw-compare` / `aw-lp`）は順次追加する。

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
