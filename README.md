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

現時点では `aw-data` の土台（スキーマ・検証・座標取得スクリプト・フィクスチャ単体テスト）を先に固めている。各ビジュアルは順次追加する。

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
