"""アトランティスのシーンを組む。肉付けの順番は plan.CUES。

    python atlantis/scene/build.py --blend out/atlantis/atlantis.blend            # シーンを組んで保存
    python atlantis/scene/build.py --stills 30,150,240,330,420 --res 960x540     # テスト静止画（組んでから描く）

本番の連番は atlantis/make.py が .blend から少しずつ描く。
"""
import argparse
import math
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ATL = os.path.dirname(HERE)
PKG = os.path.dirname(ATL)
sys.path.insert(0, HERE)
sys.path.insert(0, ATL)

import bpy  # noqa: E402

import anim  # noqa: E402
import city  # noqa: E402
import intro  # noqa: E402
import plan as P  # noqa: E402
import shots  # noqa: E402
import world  # noqa: E402
from mats import Mats  # noqa: E402

OUT = os.path.join(PKG, "out", "atlantis")


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "Atlantis"
    M = Mats(os.path.join(OUT, "tex"))
    C = P.CUES
    wire_rise = C["wire_rise"]

    # ---- 冒頭
    intro.scroll(M)
    intro.props(M)
    g0, g1 = C["ink_glow"]
    anim.value("ink_glow", [(1, 0.0), (g0, 0.0), (g1, 1.0), (wire_rise[1], 0.6), (C["scroll_away"][0], 0.2), (C["scroll_away"][1], 0.0)])

    # ---- 地形と海（地形は最初からある。巻物の下に隠れている）
    city.plain(M)
    land = city.land(M)
    anim.grow(land, *C["rings"])
    anim.wire_twin(land, M.wire, 3.0, wire_rise, (C["rings"][0] + 6, C["rings"][1] + 6))
    mts = city.mountains(M)
    mts.scale = (1, 1, 1)
    m0, m1 = C["mountains"]
    mts.scale.z = 0.02
    mts.keyframe_insert("scale", index=2, frame=1)
    mts.keyframe_insert("scale", index=2, frame=m0)
    mts.scale.z = 1.0
    mts.keyframe_insert("scale", index=2, frame=m1)

    # ---- 城壁・塔 → 橋 → 建物
    for w in city.walls(M):
        anim.grow(w, *C["walls"])
        anim.wire_twin(w, M.wire, 1.6, wire_rise, (C["walls"][0] + 6, C["walls"][1] + 6))
    br = city.bridges(M)
    anim.grow(br, *C["bridges"])
    anim.wire_twin(br, M.wire, 1.6, wire_rise, (C["bridges"][0] + 4, C["bridges"][1] + 4))
    for k, b in enumerate(city.buildings(M)):
        f0 = C["buildings"][0] + k * 3
        anim.grow(b, f0, f0 + 12)
        anim.wire_twin(b, M.wire, 1.2, wire_rise, (f0 + 4, f0 + 14))

    # ---- 庭木
    kinds = city.tree_kinds(M)
    gardens, ident = city.gardens(M, kinds)
    anim.modifier_input(gardens, "Instancer", ident, [(1, 0.0), (C["trees"][0], 0.0), (C["trees"][1], 1.1)])

    # ---- 神殿: 基壇 → 柱を一本ずつ → 屋根 → 金の飾り
    T = city.temple(M)
    anim.grow(T["podium"], *C["podium"])
    anim.wire_twin(T["podium"], M.wire_temple, 0.25, wire_rise, (C["podium"][0] + 4, C["podium"][1] + 4))
    c0, c1 = C["columns"]
    cols = T["columns"]
    for i, col in enumerate(cols):
        s = c0 + (c1 - c0 - 6) * i / max(1, len(cols) - 1)
        anim.grow(col, int(s), int(s) + 6)
    import bmesh  # 柱の光の線は 1 つにまとめる（オブジェクト数を抑える）

    bm = bmesh.new()
    for col in cols:
        tmp = col.data.copy()
        tmp.transform(col.matrix_basis)
        bm.from_mesh(tmp)
        bpy.data.meshes.remove(tmp)
    me = bpy.data.meshes.new("TempleColsWireMesh")
    bm.to_mesh(me)
    bm.free()
    me.materials.append(M.silver)
    cw = bpy.data.objects.new("TempleCols", me)
    scene.collection.objects.link(cw)
    cw.hide_render = True
    anim.wire_twin(cw, M.wire_temple, 0.2, wire_rise, (c0 + 10, c1 + 4))
    anim.grow(T["roof"], *C["roof"])
    anim.wire_twin(T["roof"], M.wire_temple, 0.25, wire_rise, (C["roof"][0] + 4, C["roof"][1] + 4))
    for key in ("gold", "shrine", "trident"):
        anim.grow(T[key], *C["gold"])
    anim.wire_twin(T["trident"], M.wire_temple, 0.12, wire_rise, (C["gold"][0], C["gold"][1] + 4))

    # ---- 巻物が消え、海が満ち、山がせり上がり、市街が広がり、灯がともり、船が出る
    world.sky(scene)
    world.sea(M)
    hk = city.house_kinds(M)
    houses, hid, n_houses = city.houses(M, hk)
    s0, s1 = C["city_spread"]
    anim.modifier_input(houses, "Instancer", hid, [(1, 0.0), (s0, 0.0), (s1, 1.1)])
    groves, gid = city.olive_groves(M, kinds)
    anim.modifier_input(groves, "Instancer", gid, [(1, 0.0), (s0 + 10, 0.0), (s1 + 20, 1.1)])
    city.forest_on(mts, kinds)
    H = city.harbor(M)
    for key in ("moles", "lighthouse", "shipyard"):
        anim.grow(H[key], s0, s0 + 24)
    anim.grow(H["beacon"], s0 + 20, s0 + 30)
    ships = city.moored_ships(M)
    ships.scale = (1, 1, 1)
    ships.hide_render = False
    anim.grow(ships, C["sea_fill"][1] - 6, C["sea_fill"][1] + 10, axis="all")
    world.fires(M, city.tower_tops())

    tri = city.trireme(M)
    sx, sy = P.SHIPYARD
    l0, l1 = C["trireme_launch"]
    t0, t1 = C["trireme_sail"]
    tri.rotation_euler = (math.radians(-6), 0, math.radians(90))
    anim.loc(tri, [(1, (sx + 44, sy, 6.0)), (l0, (sx + 44, sy, 6.0)), (l1, (8.0, sy - 10, 0.0))])
    tri.keyframe_insert("rotation_euler", frame=l0)
    tri.rotation_euler = (0, 0, math.radians(180))
    tri.keyframe_insert("rotation_euler", frame=l1 + 6)
    anim.loc(tri, [(t0, (8.0, sy - 10, 0.0)), (t1, (4.0, P.COAST_Y_3D + 120, 0.0))])
    anim.grow(tri, s0, s0 + 12, axis="all")

    cams = shots.cameras(scene)
    shots.title(M, cams["CamOffshore"])
    print("houses:", n_houses, "objects:", len(bpy.data.objects))
    return scene


def configure(scene, res=(1920, 1080), samples=8):
    r = scene.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = 100
    r.fps = P.FPS
    r.use_persistent_data = True
    scene.frame_start, scene.frame_end = 1, P.MAIN_END
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples
    c.adaptive_threshold = 0.06
    c.use_denoising = True
    c.max_bounces = 4
    c.diffuse_bounces = 2
    c.glossy_bounces = 2
    c.transmission_bounces = 2
    c.transparent_max_bounces = 16
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 4.0
    c.light_sampling_threshold = 0.02
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Punchy"
    scene.view_settings.exposure = 0.0


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--blend", default=None)
    ap.add_argument("--stills", default=None, help="カンマ区切りのフレーム")
    ap.add_argument("--res", default="1920x1080")
    ap.add_argument("--samples", type=int, default=8)
    ap.add_argument("--out", default=os.path.join(OUT, "test"))
    a = ap.parse_args(argv)
    res = tuple(int(v) for v in a.res.split("x"))
    t = time.time()
    scene = build()
    configure(scene, res, a.samples)
    end = shots.end_card(scene)
    configure_end = end.cycles
    end.render.engine = "CYCLES"
    configure_end.samples = 8
    configure_end.use_denoising = True
    end.render.fps = P.FPS
    print(f"built in {time.time() - t:.1f}s")
    if a.blend:
        os.makedirs(os.path.dirname(os.path.abspath(a.blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))
        print("saved", a.blend)
    if a.stills:
        os.makedirs(a.out, exist_ok=True)
        for f in [int(v) for v in a.stills.split(",")]:
            scene.frame_set(f)
            scene.render.filepath = os.path.join(a.out, f"still_{f:04d}.png")
            t = time.time()
            bpy.ops.render.render(write_still=True, scene=scene.name)
            print(f"frame {f}: {time.time() - t:.1f}s")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
