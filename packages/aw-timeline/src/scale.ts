// 年表の尺度と整形。純粋関数のみ。DOM もデータ読み込みも持たない。
//
// 尺度は【案A：線形固定】。前1万年から現在までを均等に取る。前1000年以降が空白になるが、
// それをそのまま見せる。断りなく縮尺を変えないため、可変尺度（案B）は採らない。年代の誤読を
// 扱う題材で、自分の年表の縮尺が動くのは筋が悪い、という判断。
import type { AwEvent } from "@aw/data";

export interface Domain {
  /** 下限（最も古い年）。負が紀元前。 */
  min: number;
  /** 上限（現在）。 */
  max: number;
}

/** 前1万年を下限の既定にする。データがそれより古ければ広げる。上限は現在（呼び出し側が渡す）。 */
export const DEFAULT_MIN_YEAR = -10000;

/**
 * 尺度の定義域を決める。min は 前1万年 とデータ最古のうち小さい方。max は現在。
 * データが 前54年 までしか無くても max は現在のままにして、後半の空白を見せる（案A）。
 */
export function computeDomain(years: number[], currentYear: number): Domain {
  const min = years.length ? Math.min(DEFAULT_MIN_YEAR, ...years) : DEFAULT_MIN_YEAR;
  return { min, max: currentYear };
}

/** 年を定義域内の位置（0=最古/上端, 1=現在/下端）に写す。範囲外は 0..1 に丸める。 */
export function positionFraction(year: number, d: Domain): number {
  if (d.max === d.min) return 0;
  const f = (year - d.min) / (d.max - d.min);
  return Math.max(0, Math.min(1, f));
}

/** 年の表記。負は「前N年」、正は「N年」。 */
export function formatYear(n: number): string {
  if (n < 0) return `前${-n}年`;
  if (n > 0) return `${n}年`;
  return "0年";
}

/**
 * 年代の見出しを、数値の部分と但し書き（「頃」「以降」など）に分けて返す。
 * 但し書きは表示から落とさない。呼び出し側が数値の隣に添える。
 */
export function formatEra(
  start: number,
  end: number | null,
  note: string,
): { yearLabel: string; note: string } {
  const yearLabel =
    end !== null && end !== start
      ? `${formatYear(start)}〜${formatYear(end)}`
      : formatYear(start);
  return { yearLabel, note: note.trim() };
}

/**
 * 年表に出す出来事を、古い順に並べて返す。
 * era_status が "unfetched" の項目は出さない（位置を推測して置かない）。
 */
export function shownEvents(events: AwEvent[]): AwEvent[] {
  return events
    .filter((e) => e.era_status !== "unfetched")
    .slice()
    .sort((a, b) => a.era_start - b.era_start || a.id.localeCompare(b.id));
}

/** 出来事の縦位置と高さ（幅のあるものは幅として描く。点にしない）。いずれも 0..1。 */
export function eventBand(e: AwEvent, d: Domain): { top: number; height: number } {
  const top = positionFraction(e.era_start, d);
  if (e.era_end === null || e.era_end === e.era_start) {
    return { top, height: 0 };
  }
  const bottom = positionFraction(e.era_end, d);
  return { top: Math.min(top, bottom), height: Math.abs(bottom - top) };
}

/** aw-map の該当地点 URL。base は aw-map のデプロイ先（別プロジェクト）。 */
export function mapSiteUrl(id: string, base: string): string {
  const b = base.endsWith("/") ? base : base + "/";
  return `${b}?site=${encodeURIComponent(id)}`;
}

/**
 * カードの衝突回避。各カードの「真の位置」(trueTop, px) は動かさず、前のカードと重なる時だけ
 * 最小間隔 gap を空けて下へずらす。返すのは各カードの実際の top(px)。軸の目盛りは真の位置の
 * ままにして、ずれたカードには引き出し線を引く（案A の線形尺度を保つ）。
 * items は trueTop の昇順で渡すこと。
 */
export function resolveCollisions(
  items: { trueTop: number; height: number }[],
  gap: number,
): number[] {
  const tops: number[] = [];
  let prevBottom = -Infinity;
  for (const it of items) {
    const top = Math.max(it.trueTop, prevBottom + gap);
    tops.push(top);
    prevBottom = top + it.height;
  }
  return tops;
}

/** 1000 年ごとの目盛り年を、定義域全体で返す（線形尺度を可視化するため）。 */
export function axisTicks(d: Domain, step = 1000): number[] {
  const first = Math.ceil(d.min / step) * step;
  const ticks: number[] = [];
  for (let y = first; y <= d.max; y += step) ticks.push(y);
  return ticks;
}
