"""ギョベクリ・テペ（第III層、前9600年頃）の復元イメージを組んでレンダリングする。

    python scene/build.py --mode preview          # 960x540 の確認用静止画
    python scene/build.py --mode still            # 1600x900 の仕上げ静止画
    python scene/build.py --mode anim             # 640x360 の連番 → ffmpeg で mp4
    python scene/build.py --mode preview --blend out/gobekli.blend

GUI の Blender からは `blender -b -P scene/build.py -- --mode preview` でも同じものが組める。
"""
import argparse
import json
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import enclosure  # noqa: E402
import life  # noqa: E402
import terrain  # noqa: E402
from materials import Palette  # noqa: E402
from util import add_noise, look_at  # noqa: E402

PKG = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PKG))
DATA = os.path.join(REPO, "packages", "aw-data", "data")

FRAMES = (1, 144)  # 24fps で 6 秒

MODES = {
    "preview": dict(res=(960, 540), samples=24),
    "still": dict(res=(1600, 900), samples=96),
    "anim": dict(res=(640, 360), samples=12),
}

# 囲い遺構の配置（模式的）。D を原点に、ほかは周りに寄せて置く。
# (名前, 中心, 内半径, 外半径, 周壁の柱の数, 中央柱の高さ, 浮彫, 詳細)。壁の高さは地表から決める。
ENCLOSURES = [
    ("EnclosureD", (0.0, 0.0), 8.6, 10.4, 11, 5.5, ("fox", "boar", "snake", "bird", "fox"), True),
    ("EnclosureC", (-24.0, -5.0), 7.6, 9.2, 10, 4.8, ("boar", "snake"), True),
    ("EnclosureB", (-11.0, 21.0), 5.2, 6.6, 8, 4.2, (), False),
    ("EnclosureA", (-28.0, 17.0), 4.6, 6.0, 7, 3.8, (), False),
]


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def site_record():
    """台帳（aw-data）からギョベクリ・テペの行を引く。年代表記はここから取る（推測で書かない）。"""
    sites = json.load(open(os.path.join(DATA, "sites.json"), encoding="utf-8"))
    return next(s for s in sites if s["id"] == "gobekli-tepe")


def sky_and_sun(scene, elevation_deg=6.0, azimuth_deg=250.0):
    """夕方の低い太陽。azimuth は北(+Y)から時計回り。西南西から差し、柱の西面を照らす。"""
    el, az = math.radians(elevation_deg), math.radians(azimuth_deg)
    to_sun = Vector((math.sin(az) * math.cos(el), math.cos(az) * math.cos(el), math.sin(el)))

    world = bpy.data.worlds.new("Sky")
    scene.world = world
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "MULTIPLE_SCATTERING"
    sky.sun_elevation = el
    # Blender の空は sun_rotation = 0 で +X、反時計回り（向きを実測して合わせた）
    sky.sun_rotation = math.atan2(to_sun.y, to_sun.x)
    sky.sun_disc = True
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    bg.inputs["Strength"].default_value = 0.12

    bpy.ops.object.light_add(type="SUN", location=(0, 0, 50))
    sun = bpy.context.object
    sun.name = "Sun"
    sun.data.energy = 5.5
    sun.data.angle = math.radians(0.8)
    sun.data.color = (1.0, 0.56, 0.3)
    sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
    return to_sun


def camera(scene, frames, focus):
    """クレーンショット: 西南西の上空から、太陽を背に D の縁まで降りてくる。"""
    data = bpy.data.cameras.new("Cam")
    data.lens = 24
    data.sensor_width = 36
    data.clip_end = 5000
    cam = bpy.data.objects.new("Cam", data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    keys = [
        (frames[0], (-24.0, -28.0, 18.0), (1.0, 2.0, 1.2)),
        (frames[1], (-5.3, -11.3, 3.4), (0.3, 1.2, 2.7)),  # 周壁の柱 7 と 8 の間から中央の2本を見る
    ]
    for f, loc, tgt in keys:
        cam.location = loc
        look_at(cam, tgt)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    add_noise(cam, "rotation_euler", strength=0.004, scale=30)
    add_noise(cam, "location", strength=0.03, scale=45)
    data.dof.use_dof = True
    data.dof.focus_object = focus
    data.dof.aperture_fstop = 5.6
    return cam


def build_scene():
    scene = bpy.context.scene
    p = Palette()
    rec = site_record()

    hollows = [terrain.Hollow(c, ri + 0.6, ro, floor_z=-0.45) for _, c, ri, ro, *_ in ENCLOSURES]
    near, far = terrain.build(p, hollows)

    found = {}
    for k, (name, c, ri, ro, n, ch, motifs, detailed) in enumerate(ENCLOSURES):
        # 壁の天端を周りの地表にそろえる（囲いは地面に掘り込まれ、外からは壁の上端だけが見える）
        ring = [terrain.height(c[0] + ro * math.cos(a), c[1] + ro * math.sin(a), []) for a in [i * math.pi / 8 for i in range(16)]]
        wh = sum(ring) / len(ring) - 0.05
        found[name] = enclosure.enclosure(p, name, c, ri, ro, wh, n, ch, seed=100 + k, motifs=motifs, detailed=detailed, rot0=0.2 * k)

    sun_dir = sky_and_sun(scene)
    life.grass(p, near, hollows, count=220000)
    life.woodland(p, hollows, avoid=[((-15, -20), 10)])
    life.hearth(p, (-13.0, -14.0, terrain.height(-13.0, -14.0, hollows) + 0.02), FRAMES)
    life.vultures(p, (0, 0), FRAMES)
    for m in (p.ground, p.leaves, p.leaves_dry, p.bark, p.rubble, p.soil, p.grass, p.grass_green):
        life.haze(m)

    focus = found["EnclosureD"]["centrals"][0]
    camera(scene, FRAMES, focus)
    print("site:", rec["name_ja"], rec["era_start"], rec["era_note"], "sun:", tuple(round(c, 2) for c in sun_dir))
    return scene


def configure(scene, mode, samples=None):
    cfg = MODES[mode]
    r = scene.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = cfg["res"]
    r.fps = 24
    scene.frame_start, scene.frame_end = FRAMES
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples or cfg["samples"]
    c.use_adaptive_sampling = True
    c.use_denoising = True
    c.max_bounces = 6
    c.diffuse_bounces = 2
    c.glossy_bounces = 2
    c.transparent_max_bounces = 8
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.sample_clamp_indirect = 8.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = -0.2


def render(scene, mode, out_dir, frame=None):
    os.makedirs(out_dir, exist_ok=True)
    if mode == "anim":
        frames_dir = os.path.join(out_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(frames_dir, "f_")
        bpy.ops.render.render(animation=True)
        if shutil.which("ffmpeg"):
            mp4 = os.path.join(out_dir, "gobekli.mp4")
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(frames_dir, "f_%04d.png"),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", mp4],
                check=True,
            )
            print("wrote", mp4)
    else:
        scene.frame_set(frame or FRAMES[1])
        scene.render.filepath = os.path.join(out_dir, f"gobekli-{mode}.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=list(MODES), default="preview")
    ap.add_argument("--out", default=os.path.join(PKG, "out"))
    ap.add_argument("--frame", type=int, default=None, help="静止画で描くフレーム（既定は最終フレーム）")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--blend", default=None)
    ap.add_argument("--view", default=None, help="カメラを固定して確認する: 'x,y,z:tx,ty,tz'（アニメーションを外す）")
    args = ap.parse_args(argv)

    reset()
    scene = build_scene()
    configure(scene, args.mode, args.samples)
    if args.view:
        cam = scene.camera
        cam.animation_data_clear()
        loc, tgt = (tuple(float(v) for v in part.split(",")) for part in args.view.split(":"))
        cam.location = loc
        look_at(cam, tgt)
        cam.data.dof.use_dof = False
    if args.blend:
        os.makedirs(os.path.dirname(os.path.abspath(args.blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    render(scene, args.mode, args.out, args.frame)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:])
