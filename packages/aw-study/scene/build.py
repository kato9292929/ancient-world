"""古代史研究者の書斎を組んでレンダリングする。

    python scene/build.py --mode preview          # 960x540 の確認用静止画
    python scene/build.py --mode still            # 1600x900 の仕上げ静止画
    python scene/build.py --mode anim             # 640x360 の連番 → ffmpeg で mp4
    python scene/build.py --mode preview --blend out/study.blend   # .blend も保存

bpy（pip の Blender モジュール）で動く。GUI の Blender からは
`blender -b -P scene/build.py -- --mode preview` でも同じものが組める。
"""
import argparse
import math
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import bpy  # noqa: E402

import furniture  # noqa: E402
import motion  # noqa: E402
import props  # noqa: E402
import room  # noqa: E402
from materials import Palette, image, stacked_image  # noqa: E402

PKG = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(PKG))
SHOTS = os.path.join(REPO, "docs", "screenshots")
DATA = os.path.join(REPO, "packages", "aw-data", "data")

FRAMES = (1, 144)  # 24fps で 6 秒

MODES = {
    "preview": dict(res=(960, 540), samples=32),
    "still": dict(res=(1600, 900), samples=128),
    "anim": dict(res=(640, 360), samples=12),
}


def shot(rel):
    return os.path.join(SHOTS, rel)


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.app.handlers.frame_change_pre.clear()


def build_scene():
    scene = bpy.context.scene
    p = Palette()

    room.build(p)
    room.lights_and_world(scene)

    furniture.desk(p)
    shelves = furniture.vitsoe_606(p)
    X, Y, TOP = furniture.DESK_X, furniture.DESK_Y, furniture.TOP
    furniture.tolomeo(p, base=(X - 0.6, Y + 0.2), reach_to=(X - 0.3, Y - 0.02, TOP + 0.5))
    furniture.ph5(p, (X + 0.25, Y - 0.75, 2.02))
    furniture.thonet_14(p, (X + 0.05, Y - 0.66, 0), yaw=math.pi + 0.25)

    # モニター: 左は aw-timeline のスクリーンショットを縦スクロール、右は推論ログ。
    # 年表は線形尺度で余白が長いので、カードの詰まった3枚を連結してスクロール素材にする。
    strip = stacked_image(
        "TimelineStrip",
        [shot("aw-timeline/2-top-collision.png"), shot("aw-timeline/3-dense-tail.png"), shot("aw-timeline/4-reduced-motion.png")],
    )
    panel_aspect = (0.6 * 0.56) / 0.34
    visible = strip.size[0] / panel_aspect / strip.size[1]
    screens = {
        "timeline": image("ScreenTimeline", strip, emit=1.1, scale=(1, visible), offset=(0, 1 - visible)),
        "bg": p.screen_bg,
    }
    mon = furniture.monitor(p, screens)
    furniture.keyboard_and_mouse(p)

    info = props.desk_props(p, DATA)
    titles = [c["name_ja"] for c in info["clusters"]] + [s["name_ja"] for s in info["sites"][:10]]
    props.fill_shelves(p, shelves, titles)

    # 壁: aw-map を額装、aw-lp を小さく、コルクボードに aw-objects と年表の切り抜き
    y_wall = room.Y1 - 0.03
    room.poster("PosterMap", shot("aw-map/1-initial.png"), 0.7, 0.45, (X, y_wall, 1.66), p.walnut)
    room.poster("PosterLP", shot("aw-lp/1-initial.png"), 0.33, 0.27, (-1.6, y_wall, 1.62), p.black_plastic)
    from util import box, cylinder, plane

    box("CorkBoard", (0.42, 0.015, 0.5), (0.13, room.Y1 - 0.0075, 1.6), p.cork, bevel=0.003)
    pins = [
        ("PinPrism", "aw-objects/1-prism-hole.png", 0.16, 0.141, (0.04, 1.72), 0.05),
        ("PinTimeline", "aw-timeline/2-top-collision.png", 0.2, 0.124, (0.2, 1.5), -0.04),
    ]
    for name, rel, w, h, (px, pz), tilt in pins:
        plane(name, w, h, (px, room.Y1 - 0.017, pz), rot=(0, tilt, 0), mat=image(name + "Img", shot(rel), rough=0.8))
        cylinder(name + "Tack", 0.005, 0.006, (px, room.Y1 - 0.02, pz + h / 2 - 0.012), p.sticky["pink"], rot=(math.pi / 2, 0, 0))

    # 動く要素
    cx, cy, zc = mon["center"]
    log = props.text(
        "InferenceLog",
        "",
        0.0105,
        (mon["right_x"] + 0.012, cy - 0.0015, zc + mon["h"] / 2 - 0.024),
        (math.pi / 2, 0, 0),
        p.screen_text,
    )
    motion.typewriter(log, motion.inference_lines(info["sites"], info["clusters"]), cps=1.8)
    motion.scroll(screens["timeline"], 1 - visible, 0.0, FRAMES)

    notes = [
        props.sticky_note(p, "StickyA", "yellow", (cx + 0.3, cy - 0.004, zc + 0.16), tilt=0.06),
        props.sticky_note(p, "StickyB", "pink", (cx + 0.3, cy - 0.004, zc + 0.07), size=0.058, tilt=-0.05),
        props.sticky_note(p, "StickyC", "green", (shelves[1]["x"] - 0.2, room.Y1 - 0.316, shelves[1]["z"] - 0.002), size=0.06, curl=0.1),
    ]
    for i, n in enumerate(notes):
        motion.flutter(n, base_rx=0.1 if i < 2 else 0.05, strength=0.16, scale=7 + 2 * i, phase=i * 31.0, frames=FRAMES)

    target = (X + 0.15, Y, 1.0)
    motion.camera(
        scene,
        start=(1.2, -1.35, 1.55),
        end=(0.72, -0.72, 1.45),
        target=target,
        lens=28,
        focus=info["prism"],
        frames=FRAMES,
    )
    return scene


def configure(scene, mode, samples=None):
    cfg = MODES[mode]
    r = scene.render
    r.engine = "CYCLES"
    r.resolution_x, r.resolution_y = cfg["res"]
    r.resolution_percentage = 100
    r.fps = 24
    scene.frame_start, scene.frame_end = FRAMES
    c = scene.cycles
    c.device = "CPU"
    c.samples = samples or cfg["samples"]
    c.use_adaptive_sampling = True
    c.use_denoising = True
    c.max_bounces = 8
    c.diffuse_bounces = 3
    c.glossy_bounces = 3
    c.transmission_bounces = 8
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    c.sample_clamp_indirect = 6.0
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"
    scene.view_settings.exposure = 0.3


def render(scene, mode, out_dir, frame=None):
    os.makedirs(out_dir, exist_ok=True)
    if mode == "anim":
        frames_dir = os.path.join(out_dir, "frames")
        os.makedirs(frames_dir, exist_ok=True)
        scene.render.image_settings.file_format = "PNG"
        scene.render.filepath = os.path.join(frames_dir, "f_")
        bpy.ops.render.render(animation=True)
        mp4 = os.path.join(out_dir, "study.mp4")
        if shutil.which("ffmpeg"):
            subprocess.run(
                ["ffmpeg", "-y", "-loglevel", "error", "-framerate", "24", "-i", os.path.join(frames_dir, "f_%04d.png"),
                 "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "22", mp4],
                check=True,
            )
            print("wrote", mp4)
    else:
        scene.frame_set(frame or FRAMES[1])
        scene.render.filepath = os.path.join(out_dir, f"study-{mode}.png")
        bpy.ops.render.render(write_still=True)
        print("wrote", scene.render.filepath)


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=list(MODES), default="preview")
    ap.add_argument("--out", default=os.path.join(PKG, "out"))
    ap.add_argument("--frame", type=int, default=None, help="静止画で描くフレーム（既定は最終フレーム）")
    ap.add_argument("--samples", type=int, default=None)
    ap.add_argument("--blend", default=None, help=".blend の保存先")
    args = ap.parse_args(argv)

    reset()
    scene = build_scene()
    configure(scene, args.mode, args.samples)
    if args.blend:
        os.makedirs(os.path.dirname(os.path.abspath(args.blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(args.blend))
    render(scene, args.mode, args.out, args.frame)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
    main(argv)
