// WebGL が使えない環境向けのフォールバック。白画面にしない。寸法の模式図（静止画）と
// テキスト説明を出す。刻文は描かず、欄の区切りだけを示す。
import { type PrismSpec, halfSide, columnDividers } from "./geometry.js";

export function hasWebGL(): boolean {
  try {
    const canvas = document.createElement("canvas");
    return !!(
      window.WebGLRenderingContext &&
      (canvas.getContext("webgl") || canvas.getContext("experimental-webgl"))
    );
  } catch {
    return false;
  }
}

function esc(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

/** 寸法の模式図（正面図）を SVG で描く。実測ではなく記録寸法からの模型であることを併記。 */
export function fallbackSvg(spec: PrismSpec): string {
  const scale = 14; // cm → px
  const w = spec.crossSection * scale;
  const h = spec.height * scale;
  const pad = 60;
  const vw = w + pad * 2 + 120;
  const vh = h + pad * 2;
  const x0 = pad + 60;
  const y0 = pad;

  const dividers = columnDividers(spec)
    .map((off) => {
      const x = x0 + (off + halfSide(spec)) * scale;
      return `<line x1="${x}" y1="${y0}" x2="${x}" y2="${y0 + h}" stroke="#8a7a5c" stroke-width="1.5" stroke-dasharray="4 4"/>`;
    })
    .join("");

  const holeW = spec.holeRadius * 2 * scale;
  const holeX = x0 + w / 2 - holeW / 2;

  return `<svg viewBox="0 0 ${vw} ${vh}" role="img" aria-label="Weld-Blundell Prism の寸法模式図" class="fallback-svg">
  <rect x="${x0}" y="${y0}" width="${w}" height="${h}" fill="#cdbfa6" stroke="#8a7a5c" stroke-width="2"/>
  <rect x="${holeX}" y="${y0}" width="${holeW}" height="${h}" fill="#f3efe7" stroke="#8a7a5c" stroke-width="1" opacity="0.9"/>
  ${dividers}
  <text x="${x0 + w / 2}" y="${y0 + h + 28}" text-anchor="middle" font-size="16" fill="#6b6559">幅 約${spec.crossSection}cm（正面）</text>
  <text x="${x0 - 16}" y="${y0 + h / 2}" text-anchor="middle" font-size="16" fill="#6b6559" transform="rotate(-90 ${x0 - 16} ${y0 + h / 2})">高さ 約${spec.height}cm</text>
  <text x="${x0 + w / 2}" y="${y0 - 20}" text-anchor="middle" font-size="14" fill="#8a7a5c">中央に軸穴（貫通）</text>
</svg>`;
}

export function renderFallback(container: HTMLElement, spec: PrismSpec): void {
  container.innerHTML = `<div class="fallback">
    ${fallbackSvg(spec)}
    <p class="fallback-note">${esc(
      "この環境では 3D 表示（WebGL）が使えないため、記録寸法からの模式図を表示しています。",
    )}</p>
  </div>`;
}
