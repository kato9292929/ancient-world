# 名作家具・照明の「似せた」モデル。製品の正確な寸法図ではなく、公開されている外形の特徴
# （プロポーション、部材の構成）を手で起こしたもの。ロゴや商標は入れない。
# Tripo（画像→メッシュ）には回さない: 金属の細い部材・薄い板は自動生成が崩れやすく、
# 名作の形を学習データ由来の形状に頼るのも避けたいため（plan/objects.md の判定を参照）。
import math

import bpy

from room import H, Y1
from util import box, cylinder, lathe, plane, tube_along

# 机（オーク天板の簡素なワークテーブル）
DESK_W, DESK_D, DESK_H = 1.5, 0.72, 0.74
DESK_X, DESK_Y = -0.45, Y1 - 0.36 - 0.02
TOP = DESK_H


def desk(p):
    t = 0.03
    box("DeskTop", (DESK_W, DESK_D, t), (DESK_X, DESK_Y, TOP - t / 2), p.oak, bevel=0.004)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = DESK_X + sx * (DESK_W / 2 - 0.05)
            y = DESK_Y + sy * (DESK_D / 2 - 0.05)
            box(f"DeskLeg{sx}{sy}", (0.04, 0.04, TOP - t), (x, y, (TOP - t) / 2), p.oak, bevel=0.003)
    box("DeskApron", (DESK_W - 0.1, 0.02, 0.08), (DESK_X, DESK_Y + DESK_D / 2 - 0.06, TOP - t - 0.04), p.oak)


def vitsoe_606(p):
    """Dieter Rams の 606 ユニバーサル・シェルフ風。壁に E トラック（アルミの縦レール）を付け、
    ピンで棚板を掛ける構成。2ベイ。棚板は前縁を折り返した鋼板（粉体塗装の白）。"""
    x_left, bay, rail_w = 0.45, 0.75, 0.025
    rails = [x_left + i * bay for i in range(3)]
    z_lo, z_hi = 0.25, 2.25
    for i, x in enumerate(rails):
        box(f"606Rail{i}", (rail_w, 0.012, z_hi - z_lo), (x, Y1 - 0.006, (z_lo + z_hi) / 2), p.aluminium, bevel=0.002)
    shelves = []
    depth = 0.3
    for bi in range(2):
        cx = x_left + bay * (bi + 0.5)
        levels = [0.62, 1.02, 1.42, 1.82] if bi == 0 else [0.62, 1.12, 1.62, 2.02]
        for li, z in enumerate(levels):
            name = f"606Shelf{bi}{li}"
            w = bay - rail_w - 0.004
            box(name, (w, depth, 0.003), (cx, Y1 - depth / 2 - 0.015, z), p.steel_white)
            box(name + "Lip", (w, 0.003, 0.03), (cx, Y1 - depth - 0.015, z - 0.0135), p.steel_white)
            # 棚受けの腕木（左右のレールから出る）
            for sx in (-1, 1):
                box(name + f"Arm{sx}", (0.004, depth - 0.02, 0.025), (cx + sx * (w / 2 - 0.006), Y1 - depth / 2 - 0.01, z - 0.013), p.steel_white)
            shelves.append({"x": cx, "w": w - 0.02, "z": z + 0.0015, "y_back": Y1 - 0.025, "depth": depth})
    # 下段は引き出しキャビネット（606 の構成でよく見る形）
    cab_w = bay - rail_w - 0.004
    box("606Cabinet", (cab_w, 0.36, 0.4), (x_left + bay * 0.5, Y1 - 0.2, 0.25 + 0.2 - 0.12), p.steel_white, bevel=0.003)
    for k in range(2):
        z = 0.2 + k * 0.17
        box(f"606Drawer{k}", (cab_w - 0.02, 0.004, 0.15), (x_left + bay * 0.5, Y1 - 0.381, z + 0.08), p.steel_white, bevel=0.002)
    return shelves


def tolomeo(p, base, reach_to):
    """Artemide Tolomeo 風のデスクライト。円盤ベース、支柱、斜めのアーム、円錐シェード。
    ばね・ワイヤは省略。シェードの中にスポットライトを入れる。"""
    bx, by = base
    cylinder("TolomeoBase", 0.115, 0.02, (bx, by, TOP + 0.01), p.aluminium, segments=48)
    pivot_z = TOP + 0.48
    cylinder("TolomeoPost", 0.008, 0.48, (bx, by, TOP + 0.24), p.aluminium)
    elbow = (bx, by, pivot_z)
    tx, ty, tz = reach_to
    tube_along("TolomeoArm", [elbow, ((bx + tx) / 2, (by + ty) / 2, pivot_z + 0.12), (tx, ty, tz + 0.06)], 0.007, p.aluminium)
    cylinder("TolomeoJoint", 0.013, 0.03, elbow, p.aluminium, rot=(math.pi / 2, 0, 0))
    shade = lathe("TolomeoShade", [(0.012, 0.05), (0.03, 0.035), (0.075, -0.035), (0.077, -0.04)], mat=p.aluminium)
    shade.location = (tx, ty, tz)
    shade.rotation_euler = (math.radians(-18), math.radians(12), 0)
    sol = shade.modifiers.new("Solidify", "SOLIDIFY")
    sol.thickness = 0.0015
    bpy.ops.object.light_add(type="SPOT", location=(tx, ty, tz - 0.01))
    spot = bpy.context.object
    spot.name = "TolomeoSpot"
    spot.data.energy = 18
    spot.data.color = (1.0, 0.78, 0.52)  # 2700K 付近
    spot.data.spot_size = math.radians(110)
    spot.data.spot_blend = 0.6
    spot.data.shadow_soft_size = 0.02
    spot.rotation_euler = shade.rotation_euler


def ph5(p, loc):
    """Poul Henningsen の PH5 風ペンダント。大中小の反射板（シェード）を重ねて、光源が直接見えない構成。"""
    x, y, z = loc
    rings = [
        ("PH5Top", [(0.03, 0.17), (0.09, 0.12), (0.155, 0.04), (0.165, 0.02)]),
        ("PH5Mid", [(0.07, 0.035), (0.13, -0.01), (0.2, -0.075), (0.21, -0.085)]),
        ("PH5Low", [(0.04, -0.06), (0.1, -0.09), (0.145, -0.125), (0.15, -0.13)]),
    ]
    for name, prof in rings:
        o = lathe(name, prof, segments=64, mat=p.steel_white, loc=loc)
        s = o.modifiers.new("Solidify", "SOLIDIFY")
        s.thickness = 0.002
    lathe("PH5Bowl", [(0.0, -0.11), (0.04, -0.105), (0.06, -0.09)], mat=p.brass, loc=loc)
    cylinder("PH5Cord", 0.003, H - z - 0.17, (x, y, (H + z + 0.17) / 2), p.black_plastic, segments=8)
    bpy.ops.object.light_add(type="POINT", location=(x, y, z - 0.02))
    bulb = bpy.context.object
    bulb.name = "PH5Bulb"
    bulb.data.energy = 25
    bulb.data.color = (1.0, 0.8, 0.58)
    bulb.data.shadow_soft_size = 0.03


def thonet_14(p, loc, yaw=0.0):
    """Thonet No.14 風の曲げ木椅子。円座、4本脚、後脚から一続きの背の輪、脚をつなぐ輪。
    すべて丸棒（カーブにベベル）で組む。"""
    col = bpy.data.collections.new("Thonet14")
    bpy.context.scene.collection.children.link(col)
    seat_z, r = 0.46, 0.2
    lathe("ThonetSeat", [(0.0, seat_z), (r - 0.01, seat_z), (r, seat_z - 0.012), (r - 0.01, seat_z - 0.025), (0.0, seat_z - 0.025)], mat=p.bentwood, collection=col)
    lathe("ThonetCane", [(0.0, seat_z + 0.002), (r - 0.02, seat_z + 0.002)], mat=p.leather, collection=col)
    ring = [(r * math.cos(a), r * math.sin(a), seat_z - 0.03) for a in [i * math.pi / 6 for i in range(12)]]
    tube_along("ThonetSeatRing", ring, 0.012, p.bentwood, closed=True, collection=col)
    # 前脚（やや外に開く）
    for sx in (-1, 1):
        tube_along(f"ThonetFrontLeg{sx}", [(sx * 0.14, -0.13, seat_z - 0.03), (sx * 0.17, -0.17, 0.0)], 0.013, p.bentwood, collection=col)
    # 後脚と背の輪: 床 → 座の後ろ → 背の上 → 反対の後脚 という一続きの曲げ木
    back = [
        (-0.17, 0.2, 0.0),
        (-0.15, 0.17, seat_z - 0.03),
        (-0.16, 0.2, seat_z + 0.2),
        (-0.12, 0.24, seat_z + 0.4),
        (0.0, 0.25, seat_z + 0.44),
        (0.12, 0.24, seat_z + 0.4),
        (0.16, 0.2, seat_z + 0.2),
        (0.15, 0.17, seat_z - 0.03),
        (0.17, 0.2, 0.0),
    ]
    tube_along("ThonetBackLoop", back, 0.013, p.bentwood, collection=col)
    tube_along(
        "ThonetInnerLoop",
        [(-0.11, 0.19, seat_z + 0.03), (-0.12, 0.21, seat_z + 0.22), (0.0, 0.23, seat_z + 0.3), (0.12, 0.21, seat_z + 0.22), (0.11, 0.19, seat_z + 0.03)],
        0.01,
        p.bentwood,
        collection=col,
    )
    leg_ring = [(0.16 * math.cos(a), 0.16 * math.sin(a), 0.2) for a in [i * math.pi / 6 for i in range(12)]]
    tube_along("ThonetLegRing", leg_ring, 0.009, p.bentwood, closed=True, collection=col)
    # 部品をひとつの空オブジェクトにぶら下げて、位置と向きをまとめて決める
    root = bpy.data.objects.new("Thonet14Root", None)
    col.objects.link(root)
    for o in col.objects:
        if o is not root:
            o.parent = root
    root.location = loc
    root.rotation_euler = (0, 0, yaw)
    return root


def monitor(p, screen_mats):
    """27インチ相当のモニター。画面は左右2枚の発光面（左: 年表のスクロール、右: 推論ログ）。"""
    cx, cy = DESK_X, Y1 - 0.2
    sw, sh = 0.6, 0.34
    zc = TOP + 0.13 + sh / 2
    box("MonitorBody", (sw + 0.02, 0.02, sh + 0.02), (cx, cy + 0.012, zc), p.black_plastic, bevel=0.003)
    box("MonitorNeck", (0.04, 0.02, 0.17), (cx, cy + 0.06, TOP + 0.085), p.aluminium, bevel=0.004)
    box("MonitorFoot", (0.22, 0.18, 0.008), (cx, cy + 0.03, TOP + 0.004), p.aluminium, bevel=0.003)
    split = 0.56  # 左パネルの幅の比率
    lw, rw = sw * split, sw * (1 - split)
    left = plane("ScreenLeft", lw, sh, (cx - sw / 2 + lw / 2, cy, zc), mat=screen_mats["timeline"])
    right = plane("ScreenRight", rw, sh, (cx + sw / 2 - rw / 2, cy, zc), mat=screen_mats["bg"])
    return {"left": left, "right": right, "center": (cx, cy, zc), "w": sw, "h": sh, "right_x": cx + sw / 2 - rw, "right_w": rw}


def keyboard_and_mouse(p):
    cx, cy = DESK_X, DESK_Y - 0.04
    box("Keyboard", (0.36, 0.12, 0.012), (cx, cy, TOP + 0.006), p.aluminium, bevel=0.003)
    keys = box("Key", (0.016, 0.016, 0.004), (cx - 0.16, cy - 0.045, TOP + 0.014), p.black_plastic, bevel=0.001)
    a1 = keys.modifiers.new("ArrayX", "ARRAY")
    a1.count = 18
    a1.relative_offset_displace = (1.19, 0, 0)
    a2 = keys.modifiers.new("ArrayY", "ARRAY")
    a2.count = 5
    a2.relative_offset_displace = (0, 1.19, 0)
    m = lathe("Mouse", [(0.0, 0.0), (0.03, 0.0), (0.028, 0.012), (0.015, 0.02), (0.0, 0.022)], mat=p.black_plastic, loc=(cx + 0.3, cy, TOP))
    m.scale = (0.7, 1.0, 1.0)

