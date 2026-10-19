# カメラのカット、タイトル、ロゴのエンドカード。
import math

import bpy
from mathutils import Vector

import anim
import plan as P
from city import HILL_TOP, TEMPLE_Z
from util import add_noise, look_at

FONT_JP = "/usr/share/fonts/opentype/ipafont-mincho/ipam.ttf"
FONT_LATIN = "/usr/share/fonts/truetype/freefont/FreeSerif.ttf"


def _cam(name, lens, clip_end=60000):
    d = bpy.data.cameras.new(name)
    d.lens = lens
    d.sensor_width = 36
    d.clip_start = 1.0
    d.clip_end = clip_end
    o = bpy.data.objects.new(name, d)
    bpy.context.scene.collection.objects.link(o)
    return o


def _path(cam, keys, shake=0.0):
    """keys = [(frame, 位置, 注視点)]。間はベジェで滑らかに。"""
    for f, loc, tgt in keys:
        cam.location = loc
        look_at(cam, tgt)
        cam.keyframe_insert("location", frame=f)
        cam.keyframe_insert("rotation_euler", frame=f)
    if shake:
        add_noise(cam, "rotation_euler", strength=0.0025 * shake, scale=35)


def cameras(scene):
    cams = {}
    tx, ty = P.TEMPLE_CENTER
    temple = (tx, ty, TEMPLE_Z + 20)

    # 巻物の縦長を横長の画面に収めるため、南の上空から斜めに見下ろす
    c = cams["CamScroll"] = _cam("CamScroll", 42)
    _path(c, [(1, (0, -10400, 8200), (0, -250, 0)), (59, (-300, -9400, 7000), (0, -150, 0))], shake=0.3)

    c = cams["CamRise"] = _cam("CamRise", 32)
    _path(c, [(60, (-2600, -8200, 3300), (0, -200, 0)), (120, (-1700, -6300, 2200), (0, 0, 0)), (179, (-700, -3600, 1150), (0, 60, 40))], shake=0.6)

    c = cams["CamTemple"] = _cam("CamTemple", 30)
    _path(c, [(180, (210, -330, TEMPLE_Z + 70), temple), (221, (150, -230, TEMPLE_Z + 40), temple)], shake=0.8)

    # 正面の低い位置から、三叉の矛の柱越しに神殿を見上げる
    trx, try_ = P.TRIDENT_COLUMN
    c = cams["CamTrident"] = _cam("CamTrident", 24)
    eye = HILL_TOP + 1.6
    _path(c, [(222, (trx + 7, try_ - 34, eye), (tx, ty, TEMPLE_Z + 40)), (269, (trx + 3, try_ - 26, eye - 0.4), (tx, ty, TEMPLE_Z + 46))], shake=0.8)
    c.data.dof.use_dof = True
    c.data.dof.focus_distance = 120.0
    c.data.dof.aperture_fstop = 8.0

    # 情景が変わるところで引きの全景へ
    c = cams["CamWide"] = _cam("CamWide", 28)
    _path(c, [(270, (380, -820, 160), (0, 0, 40)), (310, (-900, -4200, 1300), (0, 0, 0)), (349, (-2600, -8600, 2300), (0, 800, 0))], shake=0.5)

    # 最後は運河の沖から、同心円の都と夕焼けの空
    c = cams["CamOffshore"] = _cam("CamOffshore", 26)
    # 南東の沖から北西を向く: 左手（西）に夕焼け、正面に同心円の都、奥に北の山並み
    _path(c, [(350, (3300, P.COAST_Y_3D - 900, 640), (-700, -400, 60)), (P.MAIN_END, (2900, P.COAST_Y_3D - 600, 540), (-650, -350, 80))], shake=0.5)

    for f, name in P.CUTS:
        m = scene.timeline_markers.new(name, frame=f)
        m.camera = cams[name]
    scene.camera = cams["CamScroll"]
    return cams


def _text(name, body, font, size, loc, mat, parent, spacing=1.0):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = "CENTER"
    cu.align_y = "CENTER"
    cu.space_character = spacing
    try:
        cu.font = bpy.data.fonts.load(font, check_existing=True)
    except RuntimeError:
        pass
    o = bpy.data.objects.new(name, cu)
    cu.materials.append(mat)
    bpy.context.scene.collection.objects.link(o)
    o.parent = parent
    o.location = loc
    o.color = (1, 1, 1, 0)
    o.visible_shadow = False
    return o


def title(M, cam):
    """タイトル: アトランティス／ATLANTIS／海の彼方に、ポセイドンの都があった。カメラの前 10m に置く。"""
    f0, f1 = P.CUES["title"]
    items = [
        _text("TitleJP", "アトランティス", FONT_JP, 0.62, (0, 2.45, -10), M.title, cam, 1.15),
        _text("TitleEN", "A T L A N T I S", FONT_LATIN, 0.32, (0, 1.95, -10), M.title, cam, 1.2),
        _text("TitleSub", "海の彼方に、ポセイドンの都があった", FONT_JP, 0.2, (0, 1.6, -10), M.title, cam, 1.05),
    ]
    for k, o in enumerate(items):
        s = f0 + k * 6
        anim.alpha(o, [(1, 0.0), (s, 0.0), (s + 14, 1.0), (P.MAIN_END, 1.0)])
    return items


def end_card(main_scene):
    """ロゴのエンドカード（別シーン）: 黒地に柔らかく現れ、光の筋が走ってフェードアウト。"""
    sc = bpy.data.scenes.new("EndCard")
    sc.render.resolution_x, sc.render.resolution_y = main_scene.render.resolution_x, main_scene.render.resolution_y
    w = bpy.data.worlds.new("Black")
    w.node_tree.nodes["Background"].inputs["Color"].default_value = (0, 0, 0, 1)
    sc.world = w
    n = P.END_CARD[1] - P.END_CARD[0] + 1
    sc.frame_start, sc.frame_end = 1, n
    cd = bpy.data.cameras.new("EndCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 16
    cam = bpy.data.objects.new("EndCam", cd)
    sc.collection.objects.link(cam)
    cam.location = (0, 0, 10)
    sc.camera = cam

    def mat(name, color, strength):
        m = bpy.data.materials.new(name)
        b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (0, 0, 0, 1)
        b.inputs["Emission Color"].default_value = (*color, 1)
        b.inputs["Emission Strength"].default_value = strength
        import mats as MM

        return MM.fadeable(m)

    logo_m = mat("LogoInk", (0.95, 0.86, 0.68), 1.6)

    def text(body, font, size, y, spacing=1.0):
        cu = bpy.data.curves.new(body[:8], "FONT")
        cu.body = body
        cu.size = size
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.space_character = spacing
        try:
            cu.font = bpy.data.fonts.load(font, check_existing=True)
        except RuntimeError:
            pass
        cu.materials.append(logo_m)
        o = bpy.data.objects.new("Logo_" + body[:6], cu)
        sc.collection.objects.link(o)
        o.location = (0, y, 0)
        o.color = (1, 1, 1, 0)
        return o

    logo = text("ancient world", FONT_LATIN, 1.5, 0.3, 1.1)
    sub = text("古代世界を、データと絵で。", FONT_JP, 0.42, -0.9, 1.1)
    line_cu = bpy.data.meshes.new("LogoRule")
    import bmesh

    bm = bmesh.new()
    g = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in g["verts"]:
        v.co = Vector((v.co.x * 6.0, v.co.y * 0.02, 0))
    bm.to_mesh(line_cu)
    bm.free()
    line_cu.materials.append(logo_m)
    rule = bpy.data.objects.new("LogoRule", line_cu)
    sc.collection.objects.link(rule)
    rule.location = (0, -0.35, 0)
    rule.color = (1, 1, 1, 0)
    # 光の筋: 斜めの細い発光帯が左から右へ走る
    # 光の筋は「足す」光にする（透明 + 発光の加算）。幅方向は中心が明るく縁で 0
    streak_m = bpy.data.materials.new("Streak")
    snt = streak_m.node_tree
    for node in list(snt.nodes):
        snt.nodes.remove(node)
    out = snt.nodes.new("ShaderNodeOutputMaterial")
    tr = snt.nodes.new("ShaderNodeBsdfTransparent")
    em = snt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (1.0, 0.85, 0.6, 1)
    add = snt.nodes.new("ShaderNodeAddShader")
    gen = snt.nodes.new("ShaderNodeTexCoord")
    sep = snt.nodes.new("ShaderNodeSeparateXYZ")
    info = snt.nodes.new("ShaderNodeObjectInfo")
    snt.links.new(gen.outputs["Generated"], sep.inputs[0])

    def op(kind, a, b=None):
        n = snt.nodes.new("ShaderNodeMath")
        n.operation = kind
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = v
            else:
                snt.links.new(v, n.inputs[i])
        return n.outputs[0]

    falloff = op("POWER", op("SUBTRACT", 1.0, op("ABSOLUTE", op("SUBTRACT", op("MULTIPLY", sep.outputs["X"], 2.0), 1.0))), 3.0)
    snt.links.new(op("MULTIPLY", op("MULTIPLY", falloff, info.outputs["Alpha"]), 6.0), em.inputs["Strength"])
    snt.links.new(tr.outputs[0], add.inputs[0])
    snt.links.new(em.outputs[0], add.inputs[1])
    snt.links.new(add.outputs[0], out.inputs["Surface"])
    sm = bpy.data.meshes.new("Streak")
    bm = bmesh.new()
    g = bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=0.5)
    for v in g["verts"]:
        v.co = Vector((v.co.x * 0.9, v.co.y * 16.0, 0.1))
    bm.to_mesh(sm)
    bm.free()
    sm.materials.append(streak_m)
    streak = bpy.data.objects.new("Streak", sm)
    sc.collection.objects.link(streak)
    streak.rotation_euler = (0, 0, math.radians(-18))
    for o in (logo, sub, rule):
        anim.alpha(o, [(1, 0.0), (14, 1.0), (n - 10, 1.0), (n, 0.0)])
    anim.alpha(streak, [(1, 0.0), (16, 0.0), (20, 0.9), (30, 0.9), (34, 0.0)])
    anim.loc(streak, [(16, (-7.5, 0, 0)), (34, (7.5, 0, 0))], linear=True)
    sc.view_settings.view_transform = "AgX"
    return sc
