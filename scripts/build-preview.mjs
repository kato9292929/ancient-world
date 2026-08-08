// 4 つのパッケージの dist を preview/ に集め、1 ファイル（preview/index.html）から全部を回れる
// 状態を作る。生成物なので preview/ は .gitignore に入れてある（コミットしない）。
//
// 各パッケージは相対パスで動く設定（Vite の base:'./'、静的生成は相対リンク）。preview 内の
// 相互リンクは、preview/ のディレクトリ構成に合わせて環境変数で注入する。
import { execSync } from "node:child_process";
import { cpSync, rmSync, mkdirSync, writeFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const preview = resolve(root, "preview");

rmSync(preview, { recursive: true, force: true });
mkdirSync(preview, { recursive: true });

const run = (cmd, env) =>
  execSync(cmd, { cwd: root, stdio: "inherit", env: { ...process.env, ...env } });

// preview/ 内の相互リンク先（同階層の兄弟ディレクトリ）。
const crossLinks = {
  AW_MAP_BASE: "../map/",
  AW_TIMELINE_BASE: "../timeline/",
  AW_OBJECTS_BASE: "../objects/",
};

run("pnpm --filter @aw/map build");
run("pnpm --filter @aw/objects build");
run("pnpm --filter @aw/timeline build", { AW_MAP_BASE: crossLinks.AW_MAP_BASE });
run("pnpm --filter @aw/lp build", crossLinks);

// kind: 'static' = 単一の静的 HTML（スクリプト inline）。file:// で確実に開ける。
//       'module' = Vite の外部 ES module を読む。Chromium の file:// では動作確認済みだが、
//                  file:// の module を弾くブラウザではローカルサーバが要る。
const packages = [
  { pkg: "aw-map", dir: "map", title: "遺跡年代マップ", pkgName: "@aw/map", kind: "module" },
  { pkg: "aw-timeline", dir: "timeline", title: "年表", pkgName: "@aw/timeline", kind: "static" },
  { pkg: "aw-objects", dir: "objects", title: "遺物の3Dビューア", pkgName: "@aw/objects", kind: "module" },
  { pkg: "aw-lp", dir: "lp", title: "トップページ", pkgName: "@aw/lp", kind: "static" },
];

for (const { pkg, dir } of packages) {
  cpSync(resolve(root, "packages", pkg, "dist"), resolve(preview, dir), { recursive: true });
}

const cards = packages
  .map(
    (p) => `<li>
    <a href="./${p.dir}/index.html">${p.title}</a>
    <span class="pkg">${p.pkgName}</span>
    ${p.kind === "static" ? '<span class="ok-file">静的 HTML ／ file:// で表示できます</span>' : '<span class="need-server">module バンドル ／ file:// を弾くブラウザではローカルサーバが必要</span>'}
  </a></li>`,
  )
  .join("\n");

const indexHtml = `<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ancient world — 統合プレビュー</title>
<style>
  :root { font-family: system-ui, "Hiragino Kaku Gothic ProN", "Noto Sans JP", sans-serif; }
  body { margin: 0; background: #faf8f4; color: #1a1a1a; line-height: 1.7; }
  main { max-width: 44rem; margin: 0 auto; padding: 3rem 1.5rem; }
  h1 { font-size: 1.8rem; margin: 0 0 0.25rem; }
  .lede { color: #6b6559; margin: 0 0 2rem; }
  ul { list-style: none; padding: 0; margin: 0; display: grid; gap: 0.75rem; }
  li a { display: block; padding: 1rem 1.2rem; background: #fff; border: 1px solid #d8d2c8; border-radius: 0.5rem; text-decoration: none; color: inherit; }
  li a:hover { border-color: #7a5c3e; }
  .pkg { display: inline-block; margin-left: 0.5rem; font-size: 0.75rem; color: #6b6559; }
  .need-server { display: block; font-size: 0.78rem; color: #8a4b4b; margin-top: 0.2rem; }
  .ok-file { display: block; font-size: 0.78rem; color: #3f6b3f; margin-top: 0.2rem; }
  .note { margin-top: 2rem; font-size: 0.85rem; color: #6b6559; border-top: 1px solid #d8d2c8; padding-top: 1rem; }
  code { background: #efe9df; padding: 0.1rem 0.3rem; border-radius: 0.2rem; }
</style>
</head>
<body>
<main>
  <h1>ancient world — 統合プレビュー</h1>
  <p class="lede">4 つのパッケージのビルド結果をまとめたもの。生成物（コミットしない）。</p>
  <ul>${cards}</ul>
  <p class="note">
    <strong>年表・トップページ</strong>は単一の静的 HTML（スクリプトは inline）のため、<code>file://</code>
    でそのまま開けます。<br>
    <strong>マップ・遺物</strong>は ES module の外部スクリプト（Vite バンドル）を読みます。Chromium では
    <code>file://</code> でも動作を確認していますが、<code>file://</code> の module を弾くブラウザでは
    スクリプトが読めず空表示になります。その場合はローカルサーバで開いてください：<br>
    <code>npx serve preview</code> または <code>python3 -m http.server -d preview 8000</code> の後、
    <code>http://localhost:8000/</code> を開く。
  </p>
</main>
</body>
</html>
`;

writeFileSync(resolve(preview, "index.html"), indexHtml, "utf8");
process.stdout.write(`preview: wrote preview/index.html and ${packages.length} sub-apps\n`);
