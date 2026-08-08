// 正距円筒図法（equirectangular）。外部ライブラリに頼らず、経緯度を矩形に線形写像する。
// 世界全体の概観にはこれで足りる。ピンも国境も同じ写像で置く。

export interface Size {
  width: number;
  height: number;
}

/** 経度・緯度を [x, y] に写す。左上が (西経180, 北緯90)。 */
export function project(lng: number, lat: number, size: Size): [number, number] {
  const x = ((lng + 180) / 360) * size.width;
  const y = ((90 - lat) / 180) * size.height;
  return [x, y];
}

type Position = [number, number];
type Ring = Position[];

function ringToPath(ring: Ring, size: Size): string {
  let d = "";
  for (let i = 0; i < ring.length; i++) {
    const pt = ring[i]!;
    const [x, y] = project(pt[0], pt[1], size);
    d += (i === 0 ? "M" : "L") + x.toFixed(1) + " " + y.toFixed(1);
  }
  return d + "Z";
}

/** GeoJSON の Polygon / MultiPolygon ジオメトリを SVG path の d 文字列にする。 */
export function geometryToPath(
  geom: { type: string; coordinates: unknown },
  size: Size,
): string {
  if (geom.type === "Polygon") {
    const rings = geom.coordinates as Ring[];
    return rings.map((r) => ringToPath(r, size)).join("");
  }
  if (geom.type === "MultiPolygon") {
    const polys = geom.coordinates as Ring[][];
    return polys.map((poly) => poly.map((r) => ringToPath(r, size)).join("")).join("");
  }
  return "";
}
