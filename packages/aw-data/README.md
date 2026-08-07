# aw-data

遺跡・出来事のデータを 1 か所に置き、マップ・年表・3D ビューア・比較スライダー・LP が
すべてここを参照する。5 本のビジュアルの土台。

## 中身

```
data/
  sites.json          遺跡・地点
  events.json         年表の出来事
  clusters.json       クラスタの定義
schema/
  sites.schema.json
  events.schema.json
  clusters.schema.json
scripts/
  fetch-coords.ts     Wikidata / Pleiades から座標を取得（実行は別環境）
  validate.ts         スキーマ検証 + 個別ルール。CI で回す
src/
  index.ts            型とデータの公開エントリ（他パッケージはここから import）
  types.ts            Site / AwEvent / Cluster の型
  coords.ts           座標取得の純粋部分（レスポンス→候補→結論）
  validate.ts         検証ルールの中身
test/                 フィクスチャと単体テスト
```

他パッケージからは `@aw/data` として読む:

```ts
import { sites, events, clusters, type Site } from "@aw/data";
```

## 現在の状態：座標は未取得

**着手時点で全地点の `lat` / `lng` は `null`、`coord_status` は `"unfetched"`。**
サンドボックス（このリポジトリを開発している環境）は Wikidata・Pleiades などの外部 API に
到達できないため、座標取得スクリプト `fetch-coords.ts` は**書いてあるが未実行**。

`coord_status` と `era_status` は必ず持たせている。値が入っていない理由が「まだ取得して
いないから（`unfetched`）」なのか「存在しないから」なのかを、フィールドの有無で判別させ
ないため。

初期データ（別紙の素材台帳の全件）を投入する際のルール:

- 名称・クラスタ・国は台帳の記載どおり
- 座標は全件 `lat: null, lng: null, coord_source: null, coord_status: "unfetched"`
- 年代は台帳に記載のあるものだけ入れて `era_status: "sourced"`。記載のないものは `null` と `"unfetched"`
- `summary` は空配列（記事側の作業）
- 台帳にない地点・年代を足さない／推測で埋めない

> 現在 `data/*.json` は空配列。台帳が入り次第、上のルールで投入する。スキーマ・検証・
> 座標取得のテストは台帳の中身に依存しないため、投入は「入れるだけ」で済む。

## 座標を取得する手順（ネットワークのある環境で実行）

```bash
pnpm --filter @aw/data fetch-coords            # 実行して sites.json を書き換える
pnpm --filter @aw/data fetch-coords -- --dry-run  # 書き換えず結果だけ見る
```

スクリプトの挙動:

- Wikidata の SPARQL エンドポイントと Pleiades の JSON API を叩く
- 引くのは緯度経度と、参照した識別子（Q コードまたは Pleiades ID）
- **取得元の優先順位は Pleiades → Wikidata。** 近東・地中海は Pleiades の精度が高く、日本の
  遺跡は Wikidata にしかない、という題材の実態に合わせる。源をまたいで候補を単純連結すると、
  両方から 1 件ずつ返っただけで「複数候補」に化けるため、源ごとに解決する。Pleiades が 1 件でも
  返せばそれで確定し、Wikidata は見ない。Pleiades が空のときだけ Wikidata に問い合わせる
- **取得できた地点だけ** `coord_status` を `"verified"` に更新し、`lat` / `lng` / `coord_source` を埋める
- **複数候補が返った場合は自動選択しない。** 候補を標準出力に列挙し、`coord_status` を
  `"ambiguous"` にして残す（座標は入れない）。手つかずの `"unfetched"` と区別できる
- **取得できなかった地点は `"unfetched"` のまま残す。** 近隣の値や中心座標では埋めない
- 取得失敗（HTTP エラーなど）は握りつぶさず、件数と地点 id を標準エラーに出して非ゼロ終了

参照した識別子（Q コード等）は出所として標準出力に残す。`sites.json` のスキーマには識別子の
フィールドを持たせていない（スキーマ確定のため）。

### coord_status の 3 状態

| 状態 | 意味 | 座標 | 地図（aw-map）での扱い |
|---|---|---|---|
| `verified` | 座標確定 | あり | ピンを出す |
| `ambiguous` | 複数候補が返り未確定（人手で選ぶ） | null | 一覧に「候補が複数」として出す。件数は別に数える |
| `unfetched` | 未取得（手つかず） | null | 一覧に「座標未取得」として出す |

`ambiguous` は指示書には無かった状態だが、「候補は出たが確定していない地点」と「手つかずの
地点」を混ぜないために足した。地図側はこの 3 状態で分岐する。

### 実行後に何が変わるか

- `fetch-coords` で解決できた地点は `coord_status: "verified"` になり、座標が入る
- `aw-map` はその地点だけを地図上のピンとして描画するようになる（`unfetched` は一覧に残るがピンは出ない）
- `validate.ts` は「`verified` なのに `lat` が null」を検出して落とすので、取得後の整合も検証できる
- `aw-timeline` は座標を使わないため、座標取得の前後で表示は変わらない

## 検証

```bash
pnpm --filter @aw/data validate
```

- スキーマ違反で落とす
- `coord_status: "verified"` なのに `lat` / `lng` が null の行があれば落とす
- 逆に、`verified` 以外（`ambiguous` / `unfetched`）なのに座標が入っている行も落とす（未確定の座標を地図に出させない）
- 参照整合：`sites.cluster` が `clusters.json` に無い、`events.site_ids` が `sites.json` に無い場合は落とす
- id の重複で落とす
- `era_start` が正（紀元後）なのに `era_note` が空なら警告（落とさない）

## テスト

```bash
pnpm --filter @aw/data test
```

`fetch-coords.ts` はサンドボックスで実行できないため、動作確認は**レスポンスを模した
フィクスチャに対する単体テスト**で行う（`test/fixtures/`）。単一候補→`verified`、複数候補→
`ambiguous`（自動選択しない）、候補ゼロ→`unfetched`（埋めない）を検証している。

## スキーマ概要

### sites.json

| フィールド | 型 | 備考 |
|---|---|---|
| `id` | string | スラッグ。例 `gobekli-tepe` |
| `name_ja` / `name_en` | string | 日本語表記／ラテン文字表記 |
| `cluster` | string | `clusters.json` の id |
| `country` | string | 国名 |
| `lat` / `lng` | number \| null | 座標。未取得は null |
| `coord_source` | `"wikidata"` \| `"pleiades"` \| null | 出所 |
| `coord_status` | `"verified"` \| `"unfetched"` | 取得状態 |
| `era_start` | integer | 負が紀元前。例 `-9600` |
| `era_end` | integer \| null | |
| `era_status` | `"sourced"` \| `"unfetched"` | |
| `era_note` | string | 年代の但し書き。例「最古の層」 |
| `attributes` | object | クラスタごとに異なる属性 |
| `article_url` | string \| null | |
| `summary` | string[]（最大 3） | 1 要素 1 文 |

洪水層クラスタの `attributes`：`flood_layer`（`"present"` / `"absent"` / `"unknown"`）、
`layer_period`、`layer_note`。**`"absent"` と `"unknown"` は区別する**（調査のうえ層が無い
エリドゥは `"absent"`）。これが記事の論点なので `null` に潰さない。
