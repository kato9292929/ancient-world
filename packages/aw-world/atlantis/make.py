"""アトランティスの図面と動画を作る一式。

    python atlantis/make.py assets              # DXF 4 枚（＋確認用 PNG）・巻物の絵・音
    python atlantis/make.py scene               # シーンを組んで out/atlantis/atlantis.blend に保存
    python atlantis/make.py stills 20,250,420   # テスト静止画（本番と同じ設定）と、1 枚あたりの時間
    python atlantis/make.py estimate            # 本番レンダリングの所要時間の見積もり（stills の計測から）
    python atlantis/make.py render [--chunk 24 --cool 20 --threads 3]   # 本番の連番を少しずつ描く
    python atlantis/make.py video               # 連番＋音 → out/atlantis/atlantis.mp4

PC の負荷を抑えるため、Blender は常に 1 本だけ、低い優先度（nice 19）で、少しずつ描いて間に休みを入れる。
描き終えたフレームは飛ばすので、途中で止めても続きから再開できる。
"""
import argparse
import glob
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = os.path.dirname(HERE)
OUT = os.path.join(PKG, "out", "atlantis")
BLEND = os.path.join(OUT, "atlantis.blend")
FRAMES = os.path.join(OUT, "frames")
END_FRAMES = os.path.join(OUT, "endcard")
TIMES = os.path.join(OUT, "times.json")
sys.path.insert(0, HERE)
import plan as P  # noqa: E402

PY = sys.executable


def run(args, low=True):
    cmd = (["nice", "-n", "19"] if low else []) + [PY] + args
    print("$", " ".join(cmd), flush=True)
    subprocess.run(cmd, check=True)


RENDER_SNIPPET = r"""
import bpy, sys, time, json, os
blend, scene_name, out_dir, frames, threads, times_path = sys.argv[sys.argv.index("--") + 1:]
bpy.ops.wm.open_mainfile(filepath=blend)
sc = bpy.data.scenes[scene_name]
# 背景実行では、アクティブでないシーンのアニメーションが描画に反映されないことがあるので、他のシーンを外す
for other in list(bpy.data.scenes):
    if other is not sc:
        bpy.data.scenes.remove(other)
sc.render.threads_mode = "FIXED"
sc.render.threads = int(threads)
sc.render.use_persistent_data = True
os.makedirs(out_dir, exist_ok=True)
times = json.load(open(times_path)) if os.path.exists(times_path) else {}
for f in [int(v) for v in frames.split(",")]:
    path = os.path.join(out_dir, f"f_{f:04d}.png")
    if os.path.exists(path):
        continue
    sc.frame_set(f)
    sc.render.filepath = path
    t = time.time()
    bpy.ops.render.render(write_still=True, scene=sc.name)
    times[f"{scene_name}:{f}"] = round(time.time() - t, 1)
    print(f"frame {f} {times[f'{scene_name}:{f}']}s", flush=True)
json.dump(times, open(times_path, "w"), indent=1)
"""


def render_frames(scene_name, out_dir, frames, threads):
    snip = os.path.join(OUT, "_render.py")
    os.makedirs(OUT, exist_ok=True)
    with open(snip, "w") as f:
        f.write(RENDER_SNIPPET)
    run([snip, "--", BLEND, scene_name, out_dir, ",".join(str(f) for f in frames), str(threads), TIMES])


def cmd_assets(a):
    run([os.path.join(HERE, "drawings", "make_dxf.py"), "--out", os.path.join(OUT, "dxf"), "--png"])
    run([os.path.join(HERE, "drawings", "parchment.py"), os.path.join(OUT, "tex")])
    run([os.path.join(HERE, "audio", "synth.py"), os.path.join(OUT, "audio", "atlantis.wav")])


def cmd_scene(a):
    run([os.path.join(HERE, "scene", "build.py"), "--blend", BLEND])


def cmd_stills(a):
    frames = [int(v) for v in a.frames.split(",")]
    render_frames("Atlantis", os.path.join(OUT, "stills"), frames, a.threads)
    if a.endcard:
        render_frames("EndCard", os.path.join(OUT, "stills_end"), [int(v) for v in a.endcard.split(",")], a.threads)


def cmd_estimate(a):
    times = json.load(open(TIMES))
    main = [v for k, v in times.items() if k.startswith("Atlantis:")]
    end = [v for k, v in times.items() if k.startswith("EndCard:")] or [6.0]
    per = sum(main) / len(main)
    n_main = P.MAIN_END
    n_end = P.END_CARD[1] - P.END_CARD[0] + 1
    load = 25.0  # チャンクごとの .blend 読み込みとシーンの初回準備（秒、実測の目安）
    chunks = -(-n_main // a.chunk) + 1
    total = per * n_main + (sum(end) / len(end)) * n_end + chunks * (load + a.cool)
    print(f"1 枚あたり 本編 {per:.0f}s（{len(main)} 枚の平均）／ エンドカード {sum(end) / len(end):.0f}s")
    print(f"本編 {n_main} 枚 + エンドカード {n_end} 枚、{chunks} 回に分けて休み {a.cool}s")
    print(f"見積もり: 約 {total / 3600:.1f} 時間")


def cmd_render(a):
    todo = [f for f in range(1, P.MAIN_END + 1) if not os.path.exists(os.path.join(FRAMES, f"f_{f:04d}.png"))]
    while todo:
        chunk, todo = todo[: a.chunk], todo[a.chunk :]
        t = time.time()
        render_frames("Atlantis", FRAMES, chunk, a.threads)
        print(f"chunk {chunk[0]}-{chunk[-1]} done in {time.time() - t:.0f}s; 残り {len(todo)} 枚。{a.cool}s 休む", flush=True)
        if todo:
            time.sleep(a.cool)
    n_end = P.END_CARD[1] - P.END_CARD[0] + 1
    render_frames("EndCard", END_FRAMES, list(range(1, n_end + 1)), a.threads)


def cmd_video(a):
    os.makedirs(OUT, exist_ok=True)
    lst = os.path.join(OUT, "_frames.txt")
    with open(lst, "w") as f:
        for p in sorted(glob.glob(os.path.join(FRAMES, "f_*.png"))) + sorted(glob.glob(os.path.join(END_FRAMES, "f_*.png"))):
            f.write(f"file '{p}'\nduration {1 / P.FPS:.6f}\n")
    mp4 = os.path.join(OUT, "atlantis.mp4")
    subprocess.run(
        ["nice", "-n", "19", "ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", lst,
         "-i", os.path.join(OUT, "audio", "atlantis.wav"), "-r", str(P.FPS), "-c:v", "libx264", "-preset", "slow", "-crf", "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", mp4],
        check=True,
    )
    print("wrote", mp4)


def main(argv):
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("assets")
    sub.add_parser("scene")
    s = sub.add_parser("stills")
    s.add_argument("frames")
    s.add_argument("--endcard", default="20")
    s.add_argument("--threads", type=int, default=3)
    e = sub.add_parser("estimate")
    e.add_argument("--chunk", type=int, default=24)
    e.add_argument("--cool", type=int, default=20)
    r = sub.add_parser("render")
    r.add_argument("--chunk", type=int, default=24)
    r.add_argument("--cool", type=int, default=20)
    r.add_argument("--threads", type=int, default=3)
    sub.add_parser("video")
    a = ap.parse_args(argv)
    {"assets": cmd_assets, "scene": cmd_scene, "stills": cmd_stills, "estimate": cmd_estimate, "render": cmd_render, "video": cmd_video}[a.cmd](a)


if __name__ == "__main__":
    main(sys.argv[1:])
