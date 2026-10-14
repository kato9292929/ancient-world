# 動く要素。カメラのドリー＋手ブレ、付箋のなびき、モニターの年表スクロールと推論ログのタイプ表示。
# カメラ・付箋・スクロールはキーフレーム（.blend に保存される）。タイプ表示は frame_change ハンドラで
# 本文を差し替える（ハンドラは .blend に残らないので、レンダリングはこのスクリプトから行う）。
import bpy

from util import add_noise, linear_keys, look_at


def camera(scene, start, end, target, lens=26, focus=None, frames=(1, 144), shake=1.0):
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = lens
    cam_data.sensor_width = 36
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam

    f0, f1 = frames
    for f, loc in ((f0, start), (f1, end)):
        cam.location = loc
        look_at(cam, target)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    # ドリーはゆっくり加減速（ベジェのまま）。手ブレは回転に低周波ノイズ、位置にごく小さいノイズ。
    if shake > 0:
        add_noise(cam, "rotation_euler", strength=0.006 * shake, scale=28)
        add_noise(cam, "location", strength=0.004 * shake, scale=40)

    if focus is not None:
        cam_data.dof.use_dof = True
        cam_data.dof.focus_object = focus
        cam_data.dof.aperture_fstop = 2.8
    return cam


def flutter(obj, base_rx=0.12, strength=0.18, scale=9, phase=0.0, frames=(1, 144)):
    """付箋: 蝶番（上端）まわりの x 回転に揺らぎ。窓からの風で手前にめくれる向きに偏らせる。"""
    obj.rotation_euler.x = base_rx
    obj.keyframe_insert("rotation_euler", index=0, frame=frames[0])
    obj.keyframe_insert("rotation_euler", index=0, frame=frames[1])
    add_noise(obj, "rotation_euler", strength=strength, scale=scale, phase=phase, index=0)
    # 小さな揺れが下端だけ大きく見えるよう、z 回転にも弱く
    obj.keyframe_insert("rotation_euler", index=2, frame=frames[0])
    add_noise(obj, "rotation_euler", strength=strength * 0.25, scale=scale * 1.3, phase=phase + 5, index=2)


def scroll(mat, start_y, end_y, frames=(1, 144)):
    """画面の年表を下へ送る。Mapping ノード "Scroll" の Location.y を線形に動かす。"""
    nt = mat.node_tree
    sock = nt.nodes["Scroll"].inputs["Location"]
    for f, y in ((frames[0], start_y), (frames[1], end_y)):
        sock.default_value[1] = y
        sock.keyframe_insert("default_value", index=1, frame=f)
    linear_keys(nt)


def typewriter(text_obj, lines, cps=1.6, start=1, cursor="_"):
    """推論ログ風のタイプ表示。1 フレームあたり cps 文字。カーソルは 12 フレーム周期で点滅。"""
    full = "\n".join(lines)

    def handler(scene, _depsgraph=None):
        f = scene.frame_current
        n = max(0, int((f - start) * cps))
        shown = full[:n]
        blink = cursor if (f // 6) % 2 == 0 else " "
        text_obj.data.body = shown + blink

    bpy.app.handlers.frame_change_pre.append(handler)
    handler(bpy.context.scene)
    return handler


def inference_lines(sites, clusters):
    """台帳（aw-data）から推論ログの行を組む。年代の扱いは台帳の値をそのまま出す（推測で埋めない）。"""
    def era(v):
        if v is None:
            return "  ?   "
        return f"BC{-v}" if v < 0 else f"AD{v}"

    by_cluster = {c["id"]: c["name_ja"] for c in clusters}
    picked = [s for s in sites if s.get("era_start") is not None][:7]
    lines = [
        "> aw-data を照合しています",
        f"  sites {len(sites)} / clusters {len(clusters)}",
        "",
    ]
    for s in picked:
        lines.append(f"  {era(s['era_start']):>7}  {s['name_ja']}")
        lines.append(f"           [{by_cluster.get(s['cluster'], s['cluster'])}]")
    lines += ["", "> 推論: 層位と年代の整合を確認中…"]
    return lines

