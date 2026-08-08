// 表示側。geometry.ts の寸法から three のメッシュを組む。ここは three に依存する。
// 形状はコードで生成する。バイナリのモデルファイルは同梱しない。
import * as THREE from "three";
import { type PrismSpec, halfSide, columnDividers } from "./geometry.js";

export interface PrismBuild {
  group: THREE.Group;
  /** 面ごとの当たり判定用プレーン（index 0〜3）。ピックに使う。 */
  facePlanes: THREE.Mesh[];
}

// 面の向き（法線方向）と、その面のローカル「幅」軸。index 0:+X, 1:+Z, 2:-X, 3:-Z。
const FACE_DIRS: { normal: THREE.Vector3; widthAxis: "x" | "z"; rotY: number }[] = [
  { normal: new THREE.Vector3(1, 0, 0), widthAxis: "z", rotY: Math.PI / 2 },
  { normal: new THREE.Vector3(0, 0, 1), widthAxis: "x", rotY: 0 },
  { normal: new THREE.Vector3(-1, 0, 0), widthAxis: "z", rotY: -Math.PI / 2 },
  { normal: new THREE.Vector3(0, 0, -1), widthAxis: "x", rotY: Math.PI },
];

export function buildPrism(spec: PrismSpec): PrismBuild {
  const group = new THREE.Group();
  const half = halfSide(spec);
  const h = spec.height;

  // 断面：正方形の輪郭 + 中心の円（軸穴）。Shape に穴を持たせて押し出す。
  const shape = new THREE.Shape();
  shape.moveTo(-half, -half);
  shape.lineTo(half, -half);
  shape.lineTo(half, half);
  shape.lineTo(-half, half);
  shape.closePath();
  const hole = new THREE.Path();
  hole.absarc(0, 0, spec.holeRadius, 0, Math.PI * 2, true);
  shape.holes.push(hole);

  const geom = new THREE.ExtrudeGeometry(shape, {
    depth: h,
    bevelEnabled: false,
    curveSegments: 48, // 軸穴の円の滑らかさ
  });
  geom.translate(0, 0, -h / 2);
  geom.rotateX(-Math.PI / 2); // 押し出し軸(Z)を縦(Y)にする。軸穴は縦に貫通する
  geom.computeVertexNormals();

  // 無地〜簡略な陰影にとどめる。テクスチャや刻文は載せない。
  const material = new THREE.MeshStandardMaterial({
    color: 0xcdbfa6,
    roughness: 0.85,
    metalness: 0.02,
    flatShading: false,
  });
  const mesh = new THREE.Mesh(geom, material);
  group.add(mesh);

  // 各面に、欄の区切りだけを線で示す（刻文は描かない）。2欄 → 面の中央に1本。
  const dividerMat = new THREE.LineBasicMaterial({ color: 0x8a7a5c });
  const eps = 0.02;
  for (const dir of FACE_DIRS) {
    for (const off of columnDividers(spec)) {
      const pts: THREE.Vector3[] = [];
      const top = new THREE.Vector3();
      const bot = new THREE.Vector3();
      if (dir.widthAxis === "z") {
        const x = dir.normal.x * (half + eps);
        top.set(x, h / 2, off);
        bot.set(x, -h / 2, off);
      } else {
        const z = dir.normal.z * (half + eps);
        top.set(off, h / 2, z);
        bot.set(off, -h / 2, z);
      }
      pts.push(top, bot);
      const g = new THREE.BufferGeometry().setFromPoints(pts);
      group.add(new THREE.Line(g, dividerMat));
    }
  }

  // 面ごとの当たり判定プレーン（透明）。選択時にうっすら光らせる。
  const facePlanes: THREE.Mesh[] = [];
  for (let i = 0; i < FACE_DIRS.length; i++) {
    const dir = FACE_DIRS[i]!;
    const planeGeom = new THREE.PlaneGeometry(spec.crossSection, h);
    const planeMat = new THREE.MeshBasicMaterial({
      color: 0xffcf6a,
      transparent: true,
      opacity: 0,
      side: THREE.DoubleSide,
      depthWrite: false,
    });
    const plane = new THREE.Mesh(planeGeom, planeMat);
    plane.position.copy(dir.normal).multiplyScalar(half + eps * 2);
    plane.rotation.y = dir.rotY;
    plane.userData["faceIndex"] = i;
    plane.name = `face-${i}`;
    facePlanes.push(plane);
    group.add(plane);
  }

  return { group, facePlanes };
}

/** 選択された面プレーンだけをうっすら光らせる。 */
export function highlightFace(facePlanes: THREE.Mesh[], selected: number | null): void {
  for (const p of facePlanes) {
    const mat = p.material as THREE.MeshBasicMaterial;
    mat.opacity = p.userData["faceIndex"] === selected ? 0.22 : 0;
  }
}
