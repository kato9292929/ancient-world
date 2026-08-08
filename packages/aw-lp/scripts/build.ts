// 静的サイトを組む。@aw/data の sites/clusters と content/articles.json を読み、
// 入口のリンク先を環境変数で注入して dist/index.html を書き出す。
import { readFileSync, writeFileSync, mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import { sites, clusters } from "@aw/data";
import { renderLp, type Entrance } from "../src/render.js";
import { parseArticles } from "../src/articles.js";

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, "..");

const css = readFileSync(resolve(root, "src/styles.css"), "utf8");
const articles = parseArticles(
  JSON.parse(readFileSync(resolve(root, "content/articles.json"), "utf8")),
);

// リンク先は環境変数で注入。未設定でも相対パスの既定値でビルドが通る。
const env = process.env;
// 入口は配列で持つ。直書きしない。aw-compare 完成時にここへ 1 つ足せば 4 つになる。
// desc は指示書のコピーをそのまま使う。
const entrances: Entrance[] = [
  {
    key: "map",
    title: "遺跡年代マップ",
    desc: "世界の遺跡を年代順に表示します。座標が未取得の地点は一覧に残します。",
    href: env["AW_MAP_BASE"] ?? "/map",
  },
  {
    key: "timeline",
    title: "年表",
    desc: "前1万年から現在までを線形の尺度で並べます。空白は空白のまま表示します。",
    href: env["AW_TIMELINE_BASE"] ?? "/timeline",
  },
  {
    key: "objects",
    title: "遺物",
    desc: "記録された寸法から起こした模型を表示します。実物のスキャンではありません。",
    href: env["AW_OBJECTS_BASE"] ?? "/objects",
  },
];

const html = renderLp(sites, clusters, { entrances, articles, css });

const outDir = resolve(root, "dist");
mkdirSync(outDir, { recursive: true });
writeFileSync(resolve(outDir, "index.html"), html, "utf8");

process.stdout.write(
  `aw-lp: wrote dist/index.html (${entrances.length} entrances, ${articles.length} articles, ` +
    `map=${entrances[0]!.href} timeline=${entrances[1]!.href} objects=${entrances[2]!.href})\n`,
);
