// エントリ。WebGL があれば 3D ビューア、無ければ模式図フォールバック。
// 模型であることのラベルは常時、初期表示で見える位置に置く（HTML 側で常に表示）。
import { WELD_BLUNDELL_PRISM, holeFits } from "./geometry.js";
import { createViewer } from "./viewer.js";
import { hasWebGL, renderFallback } from "./fallback.js";
import { parseFaces, faceFor } from "./faces.js";
import facesJson from "../content/faces.json";

function $(sel: string): HTMLElement {
  const el = document.querySelector(sel);
  if (!el) throw new Error(`要素が見つかりません: ${sel}`);
  return el as HTMLElement;
}

const spec = WELD_BLUNDELL_PRISM;

// 形状の健全性。名目値でも穴が断面に収まらない等の破綻があれば、黙って進めず落とす。
if (!holeFits(spec)) {
  throw new Error("軸穴の寸法が断面に収まりません（形状生成の不整合）");
}

const faces = parseFaces(facesJson);
const stage = $("#stage");
const facePanel = $("#face-panel");

function showFace(index: number | null): void {
  if (index === null) {
    facePanel.innerHTML = "";
    facePanel.hidden = true;
    return;
  }
  const f = faceFor(faces, index);
  // faces.json が空なら説明欄は出さない（面の番号だけ示す）。準備中は出さない。
  if (!f || (!f.title && !f.body)) {
    facePanel.innerHTML = `<p class="face-index">第 ${index + 1} 面</p><p class="face-empty">この面の説明はまだありません。</p>`;
  } else {
    facePanel.innerHTML =
      `<p class="face-index">第 ${index + 1} 面</p>` +
      (f.title ? `<h2>${escapeHtml(f.title)}</h2>` : "") +
      (f.body ? `<p>${escapeHtml(f.body)}</p>` : "");
  }
  facePanel.hidden = false;
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

if (hasWebGL()) {
  try {
    createViewer(stage, spec, showFace);
  } catch (err) {
    // 初期化に失敗したら白画面にせず、フォールバックへ。
    console.error(err);
    renderFallback(stage, spec);
  }
} else {
  renderFallback(stage, spec);
}
