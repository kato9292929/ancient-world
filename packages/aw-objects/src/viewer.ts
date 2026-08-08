// three のシーン・カメラ・操作。軸は縦に固定（実物が軸を通して回された構造に合わせる）。
// ドラッグで縦軸まわりに回転、ホイールで拡大縮小、面クリックで選択。
// prefers-reduced-motion 有効時は自動回転を止める。
import * as THREE from "three";
import type { PrismSpec } from "./geometry.js";
import { buildPrism, highlightFace } from "./prism.js";

export interface Viewer {
  dispose(): void;
  selectFace(index: number | null): void;
}

export function createViewer(
  container: HTMLElement,
  spec: PrismSpec,
  onFaceSelect: (index: number | null) => void,
): Viewer {
  const width = () => container.clientWidth || 640;
  const height = () => container.clientHeight || 480;

  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0xf3efe7);

  const camera = new THREE.PerspectiveCamera(35, width() / height(), 0.1, 1000);
  let camDist = spec.height * 2.0;
  // 上方から見下ろす。天面の軸穴が初期表示で見えるように高めに置く。
  const camElevation = spec.height * 0.85;
  function placeCamera(): void {
    camera.position.set(0, camElevation, camDist);
    camera.lookAt(0, spec.height * 0.05, 0);
  }
  placeCamera();

  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const key = new THREE.DirectionalLight(0xffffff, 0.8);
  key.position.set(1, 2, 2);
  scene.add(key);
  const fill = new THREE.DirectionalLight(0xffffff, 0.3);
  fill.position.set(-2, 1, -1);
  scene.add(fill);

  const { group, facePlanes } = buildPrism(spec);
  scene.add(group);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width(), height());
  container.appendChild(renderer.domElement);

  const reduceMotion =
    window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  let autoRotate = !reduceMotion;

  // --- 操作 ---
  let dragging = false;
  let moved = 0;
  let lastX = 0;
  const raycaster = new THREE.Raycaster();
  const pointer = new THREE.Vector2();

  function onDown(e: PointerEvent): void {
    dragging = true;
    moved = 0;
    lastX = e.clientX;
    autoRotate = false;
    renderer.domElement.setPointerCapture(e.pointerId);
  }
  function onMove(e: PointerEvent): void {
    if (!dragging) return;
    const dx = e.clientX - lastX;
    lastX = e.clientX;
    moved += Math.abs(dx);
    group.rotation.y += dx * 0.01; // 縦軸まわりのみ
  }
  function onUp(e: PointerEvent): void {
    dragging = false;
    // ほぼ動いていなければクリック扱いで面を選ぶ。
    if (moved < 4) pick(e);
  }
  function pick(e: PointerEvent): void {
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1;
    pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1;
    raycaster.setFromCamera(pointer, camera);
    const hits = raycaster.intersectObjects(facePlanes, false);
    if (hits.length > 0) {
      const idx = hits[0]!.object.userData["faceIndex"] as number;
      selectFace(idx);
    } else {
      selectFace(null);
    }
  }
  function onWheel(e: WheelEvent): void {
    e.preventDefault();
    camDist = Math.max(spec.height * 1.1, Math.min(spec.height * 5, camDist + e.deltaY * 0.05));
    placeCamera();
  }

  let selected: number | null = null;
  function selectFace(index: number | null): void {
    selected = index;
    highlightFace(facePlanes, index);
    onFaceSelect(index);
  }

  renderer.domElement.addEventListener("pointerdown", onDown);
  renderer.domElement.addEventListener("pointermove", onMove);
  renderer.domElement.addEventListener("pointerup", onUp);
  renderer.domElement.addEventListener("wheel", onWheel, { passive: false });

  function onResize(): void {
    camera.aspect = width() / height();
    camera.updateProjectionMatrix();
    renderer.setSize(width(), height());
  }
  window.addEventListener("resize", onResize);

  let raf = 0;
  function tick(): void {
    if (autoRotate) group.rotation.y += 0.004;
    renderer.render(scene, camera);
    raf = requestAnimationFrame(tick);
  }
  tick();

  return {
    dispose(): void {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", onResize);
      renderer.dispose();
      renderer.domElement.remove();
    },
    selectFace,
  };
}
