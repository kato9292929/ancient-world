// 台帳（ancient-world-inventory.md）から clusters / sites / events を起こして data/*.json に
// 書き出す一度きりの投入スクリプト。台帳が唯一の出所。台帳にない事実を足さない。
//
// 座標は全件 null（coord_source / coord_ref も null）。larak のみ coord_status: "unlocated"。
// 年代は台帳に記載のある 3 件（gobekli-tepe / dendera / kikai-caldera）だけ sourced。
// events の status: approx は era_note "頃"、exact は "" にして「頃」の有無を表す。
import { writeFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import type { Site, AwEvent, Cluster, FloodLayerAttributes } from "../src/types.js";

const here = dirname(fileURLToPath(import.meta.url));
const dataDir = resolve(here, "..", "data");

// ---- clusters（台帳の記載順を保持）----
const clusters: Cluster[] = [
  { id: "t-pillars", name_ja: "T字柱の遺跡群", note: "先土器新石器時代A" },
  { id: "sumer", name_ja: "シュメールの都市", note: "王名表と洪水層" },
  { id: "bronze-collapse", name_ja: "青銅器時代の崩壊", note: "前1200年頃に放棄された都市" },
  { id: "egypt", name_ja: "エジプト", note: "アトランティス伝承の関係地" },
  { id: "japan", name_ja: "日本", note: "縄文とオホーツク" },
  { id: "benchmark", name_ja: "比較の基準点", note: "年代比較のための参照" },
  { id: "missoula", name_ja: "ミズーラ洪水", note: "記事を書く場合のみ" },
];

// ---- sites ----
// 共通の既定値を作るヘルパ。座標・出所は全件 null。
function site(
  partial: Pick<Site, "id" | "name_ja" | "name_en" | "cluster" | "country"> &
    Partial<Site>,
): Site {
  return {
    lat: null,
    lng: null,
    coord_source: null,
    coord_ref: null,
    coord_status: "unfetched",
    era_start: null,
    era_end: null,
    era_status: "unfetched",
    era_note: "",
    attributes: {},
    article_url: null,
    summary: [],
    ...partial,
  };
}

function flood(
  flood_layer: FloodLayerAttributes["flood_layer"],
  layer_period: string | null,
  layer_note: string | null,
): Record<string, unknown> {
  return { flood_layer, layer_period, layer_note } satisfies FloodLayerAttributes;
}

const sites: Site[] = [
  // cluster: t-pillars（7）
  site({ id: "gobekli-tepe", name_ja: "ギョベクリ・テペ", name_en: "Göbekli Tepe", cluster: "t-pillars", country: "トルコ", era_start: -9600, era_status: "sourced", era_note: "最古の層" }),
  site({ id: "karahan-tepe", name_ja: "カラハン・テペ", name_en: "Karahan Tepe", cluster: "t-pillars", country: "トルコ" }),
  site({ id: "sefer-tepe", name_ja: "セフェル・テペ", name_en: "Sefer Tepe", cluster: "t-pillars", country: "トルコ" }),
  site({ id: "hamzan-tepe", name_ja: "ハムザン・テペ", name_en: "Hamzan Tepe", cluster: "t-pillars", country: "トルコ" }),
  site({ id: "tasli-tepe", name_ja: "タシュル・テペ", name_en: "Taşlı Tepe", cluster: "t-pillars", country: "トルコ" }),
  site({ id: "urfa-yeni-yol", name_ja: "ウルファ・イェニヨル", name_en: "Urfa-Yeni Yol", cluster: "t-pillars", country: "トルコ" }),
  site({ id: "gusir-hoyuk", name_ja: "ギュシル・ホユック", name_en: "Gusir Höyük", cluster: "t-pillars", country: "トルコ" }),

  // cluster: sumer（10・attributes あり。larak のみ unlocated）
  site({ id: "eridu", name_ja: "エリドゥ", name_en: "Eridu", cluster: "sumer", country: "イラク", attributes: flood("absent", null, "ウルから約23km") }),
  site({ id: "bad-tibira", name_ja: "バド・ティビラ", name_en: "Bad-tibira", cluster: "sumer", country: "イラク", attributes: flood("unknown", null, "王名表の洪水前・第2") }),
  site({ id: "larak", name_ja: "ララク", name_en: "Larak", cluster: "sumer", country: "イラク", coord_status: "unlocated", attributes: flood("unknown", null, "王名表の洪水前・第3") }),
  site({ id: "sippar", name_ja: "シッパル", name_en: "Sippar", cluster: "sumer", country: "イラク", attributes: flood("unknown", null, "王名表の洪水前・第4") }),
  site({ id: "shuruppak", name_ja: "シュルッパク", name_en: "Shuruppak", cluster: "sumer", country: "イラク", attributes: flood("present", "ジェムデト・ナスル期末〜初期王朝I期", "王名表の洪水前・最後") }),
  site({ id: "kish", name_ja: "キシュ", name_en: "Kish", cluster: "sumer", country: "イラク", attributes: flood("present", "前2900年頃 と 初期王朝III期", "層が2つ") }),
  site({ id: "ur", name_ja: "ウル", name_en: "Ur", cluster: "sumer", country: "イラク", attributes: flood("present", "前3500年以降", "ウーリーの発表は1929年") }),
  site({ id: "uruk", name_ja: "ウルク", name_en: "Uruk", cluster: "sumer", country: "イラク", attributes: flood("present", null, "厚さ約1.5m") }),
  site({ id: "isin", name_ja: "イシン", name_en: "Isin", cluster: "sumer", country: "イラク", attributes: flood("unknown", null, "王名表の編纂主体") }),
  site({ id: "larsa", name_ja: "ラルサ", name_en: "Larsa", cluster: "sumer", country: "イラク", attributes: flood("unknown", null, "WB444の出土地とされる") }),

  // cluster: bronze-collapse（7）
  site({ id: "ugarit", name_ja: "ウガリット", name_en: "Ugarit", cluster: "bronze-collapse", country: "シリア" }),
  site({ id: "hattusa", name_ja: "ハットゥシャ", name_en: "Hattusa", cluster: "bronze-collapse", country: "トルコ" }),
  site({ id: "mycenae", name_ja: "ミュケナイ", name_en: "Mycenae", cluster: "bronze-collapse", country: "ギリシャ" }),
  site({ id: "pylos", name_ja: "ピュロス", name_en: "Pylos", cluster: "bronze-collapse", country: "ギリシャ" }),
  site({ id: "tiryns", name_ja: "ティリンス", name_en: "Tiryns", cluster: "bronze-collapse", country: "ギリシャ" }),
  site({ id: "troy", name_ja: "トロイ", name_en: "Troy", cluster: "bronze-collapse", country: "トルコ" }),
  site({ id: "carchemish", name_ja: "カルケミシュ", name_en: "Carchemish", cluster: "bronze-collapse", country: "トルコ／シリア" }),

  // cluster: egypt（3。era_note は台帳の era_note 列どおり）
  site({ id: "dendera", name_ja: "デンデラ", name_en: "Dendera", cluster: "egypt", country: "エジプト", era_start: -54, era_status: "sourced", era_note: "ハトホル神殿の建造開始" }),
  site({ id: "sais", name_ja: "サイス", name_en: "Sais", cluster: "egypt", country: "エジプト", era_note: "ネイト神殿" }),
  site({ id: "giza", name_ja: "ギザ", name_en: "Giza", cluster: "egypt", country: "エジプト", era_note: "年代比較の基準" }),

  // cluster: japan（6。note 列は era_note に入れる。oshitoishi に Pleiades/other の但し書きを残す）
  site({ id: "oshitoishi", name_ja: "押戸石の丘", name_en: "Oshitoishi", cluster: "japan", country: "日本", era_note: "南小国町指定の名勝。国指定史跡ではない。Pleiades 対象外・Wikidata にも登録が無い可能性があり、その場合は coord_source を other にして coord_ref に行政資料または地理院の出所を入れる" }),
  site({ id: "kikai-caldera", name_ja: "鬼界カルデラ", name_en: "Kikai Caldera", cluster: "japan", country: "日本", era_start: -5300, era_status: "sourced", era_note: "鬼界アカホヤ噴火" }),
  site({ id: "uenohara", name_ja: "上野原遺跡", name_en: "Uenohara", cluster: "japan", country: "日本", era_note: "噴火前の南九州の文化" }),
  site({ id: "sannai-maruyama", name_ja: "三内丸山遺跡", name_en: "Sannai-Maruyama", cluster: "japan", country: "日本" }),
  site({ id: "moyoro", name_ja: "モヨロ貝塚", name_en: "Moyoro", cluster: "japan", country: "日本", era_note: "オホーツク文化" }),
  site({ id: "funadomari", name_ja: "船泊遺跡", name_en: "Funadomari", cluster: "japan", country: "日本", era_note: "縄文人ゲノムの解析対象" }),

  // cluster: benchmark（2）
  site({ id: "stonehenge", name_ja: "ストーンヘンジ", name_en: "Stonehenge", cluster: "benchmark", country: "イギリス" }),
  site({ id: "catalhoyuk", name_ja: "チャタル・ヒュユク", name_en: "Çatalhöyük", cluster: "benchmark", country: "トルコ" }),

  // cluster: missoula（3）
  site({ id: "dry-falls", name_ja: "ドライフォールズ", name_en: "Dry Falls", cluster: "missoula", country: "アメリカ" }),
  site({ id: "grand-coulee", name_ja: "グランドクーリー", name_en: "Grand Coulee", cluster: "missoula", country: "アメリカ" }),
  site({ id: "lake-missoula", name_ja: "ミズーラ湖跡", name_en: "Lake Missoula", cluster: "missoula", country: "アメリカ" }),
];

// ---- events（14。approx→era_note "頃"、exact→""。related_sites は台帳の記載のみ）----
function ev(
  id: string,
  era: number,
  status: "approx" | "exact",
  title: string,
  related: string[],
): AwEvent {
  return {
    id,
    title,
    description: "",
    era_start: era,
    era_end: null,
    era_status: "sourced",
    era_note: status === "approx" ? "頃" : "",
    site_ids: related,
    article_url: null,
  };
}

const events: AwEvent[] = [
  ev("yd-end", -9700, "approx", "ヤンガードリアス終焉", []),
  ev("gobekli-oldest", -9600, "approx", "ギョベクリ・テペ最古の層", ["gobekli-tepe"]),
  ev("ubaid-start", -5500, "approx", "ウバイド期の開始", []),
  ev("kikai-akahoya", -5300, "approx", "鬼界アカホヤ噴火", ["kikai-caldera", "uenohara"]),
  ev("cuneiform", -3200, "approx", "楔形文字の成立", []),
  ev("flood-layers", -2900, "approx", "キシュ・シュルッパクの洪水層", ["kish", "shuruppak"]),
  ev("wb444", -1800, "approx", "Weld-Blundell Prism の成立", ["larsa", "isin"]),
  ev("bronze-collapse", -1200, "approx", "青銅器時代の崩壊", [
    "ugarit",
    "hattusa",
    "mycenae",
    "pylos",
    "tiryns",
    "troy",
    "carchemish",
  ]),
  ev("sterno-etrussia", -750, "approx", "ステルノ・エトルリア地磁気エクスカーション", []),
  ev("solon-egypt", -600, "approx", "ソロンのエジプト訪問とされる年代", ["sais"]),
  ev("plato-death", -347, "approx", "プラトン没", []),
  ev("nectanebo-dendera", -345, "approx", "デンデラ、ネクタネボ2世の建造", ["dendera"]),
  ev("enoch-watchers", -300, "approx", "エノク書・監視者篇の成立", []),
  ev("dendera-hathor", -54, "exact", "現在のハトホル神殿の建造開始", ["dendera"]),
];

// ---- 自己検証（作業4）----
const problems: string[] = [];
function expect(name: string, actual: number, want: number): void {
  if (actual !== want) problems.push(`${name}: 期待 ${want}、実際 ${actual}`);
}
expect("clusters 件数", clusters.length, 7);
expect("sites 件数", sites.length, 38);
expect("events 件数", events.length, 14);
expect("coord_status unlocated", sites.filter((s) => s.coord_status === "unlocated").length, 1);
expect("coord_status unfetched", sites.filter((s) => s.coord_status === "unfetched").length, 37);
expect("era_status sourced", sites.filter((s) => s.era_status === "sourced").length, 3);
expect("era_status unfetched", sites.filter((s) => s.era_status === "unfetched").length, 35);

const floodOf = (s: Site) =>
  (s.attributes as Partial<FloodLayerAttributes>).flood_layer;
expect("flood_layer present", sites.filter((s) => floodOf(s) === "present").length, 4);
expect("flood_layer absent", sites.filter((s) => floodOf(s) === "absent").length, 1);
expect("flood_layer unknown", sites.filter((s) => floodOf(s) === "unknown").length, 5);

// related_sites の参照先が全件 sites.json に存在するか。
const siteIds = new Set(sites.map((s) => s.id));
for (const e of events) {
  for (const sid of e.site_ids) {
    if (!siteIds.has(sid)) problems.push(`events[${e.id}] の related_sites "${sid}" が sites に無い`);
  }
}
// larak が fetch 対象外（unlocated）であること。
const larak = sites.find((s) => s.id === "larak");
if (!larak || larak.coord_status !== "unlocated") problems.push("larak が unlocated になっていない");

if (problems.length > 0) {
  process.stderr.write("投入を中止。以下の不一致がある:\n");
  for (const p of problems) process.stderr.write(`  - ${p}\n`);
  process.exit(1);
}

writeFileSync(resolve(dataDir, "clusters.json"), JSON.stringify(clusters, null, 2) + "\n");
writeFileSync(resolve(dataDir, "sites.json"), JSON.stringify(sites, null, 2) + "\n");
writeFileSync(resolve(dataDir, "events.json"), JSON.stringify(events, null, 2) + "\n");

const relatedCount = events.filter((e) => e.site_ids.length > 0).length;
process.stdout.write(
  `投入完了: clusters ${clusters.length}, sites ${sites.length}, events ${events.length}\n` +
    `  coord_status: unlocated ${sites.filter((s) => s.coord_status === "unlocated").length} / unfetched ${sites.filter((s) => s.coord_status === "unfetched").length}\n` +
    `  era_status:   sourced ${sites.filter((s) => s.era_status === "sourced").length} / unfetched ${sites.filter((s) => s.era_status === "unfetched").length}\n` +
    `  flood_layer:  present ${sites.filter((s) => floodOf(s) === "present").length} / absent ${sites.filter((s) => floodOf(s) === "absent").length} / unknown ${sites.filter((s) => floodOf(s) === "unknown").length}\n` +
    `  related_sites を持つ events: ${relatedCount} 件\n`,
);
