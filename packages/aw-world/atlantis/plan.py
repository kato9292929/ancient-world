"""アトランティスの都の寸法と、動画の進行表。図面（DXF）・巻物の絵・3D シーン・音がすべてここを参照する。

寸法はプラトン『クリティアス』の記述を、1 スタディオン = 185m として換算した**想像図のための値**。
実測図ではない。記述に無い値（高さ、塔の数、建物の大きさなど）は「仮」と書いてある。
座標: 原点 = 中央島の中心、+X = 東、+Y = 北、単位 m。
"""
import math

STADION = 185.0
PLETHRON = STADION / 6  # 約 30.8m
FOOT = PLETHRON / 100  # 約 0.31m

# ---------------------------------------------------------------- 同心円の環（記述あり）
# 中央島 直径 5 スタディオン。そこから外へ: 水の環 1、陸の環 2、水の環 2、陸の環 3、水の環 3（スタディオン）
R_ISLAND = 2.5 * STADION
RINGS = []  # (種類, 内半径, 外半径, 名前)
_r = R_ISLAND
for kind, width, name in [
    ("water", 1, "内側の水の環"),
    ("land", 2, "内側の陸の環"),
    ("water", 2, "中の水の環"),
    ("land", 3, "外側の陸の環"),
    ("water", 3, "外側の水の環"),
]:
    RINGS.append((kind, _r, _r + width * STADION, name))
    _r += width * STADION
R_OUTER = _r  # 外側の水の環の外縁（13.5 スタディオン ≒ 2497.5m）

# 大運河: 幅 3 プレトロン、深さ 100 フィート、海から外側の環まで 50 スタディオン（記述あり）
CANAL_W = 3 * PLETHRON
CANAL_DEPTH = 100 * FOOT
CANAL_LEN = 50 * STADION
# 3D では運河を縮める（50 スタディオン = 9.25km だと都が遠景の点になるため）。図面は省略線で実長を示す
CANAL_LEN_3D = 1400.0
COAST_Y_3D = -(R_OUTER + CANAL_LEN_3D)

# 外壁: 最も外の環から 50 スタディオン離れて、海から海へ円を描く（記述あり）。3D では市街を手前で切る
R_CITY_WALL = R_OUTER + 50 * STADION
R_CITY_3D = R_OUTER + 1700.0

# 橋: 幅 1 プレトロン（記述あり）。方位は仮に東西南北の4本。南の橋の下には三段櫂船が通れる水路（記述あり）
BRIDGE_W = PLETHRON
BRIDGE_AXES = [90.0, 0.0, 270.0, 180.0]  # 度。0 = 東、90 = 北
PASSAGE_W = 25.0  # 仮: 櫂船 1 隻が通れる幅

# 城壁（記述あり: 外の環の壁は青銅、次は錫、アクロポリスはオリハルコンで覆う）。高さは仮
WALLS = [
    # (半径, 素材, 高さ, 厚さ, 塔の数)
    (RINGS[3][2], "bronze", 14.0, 6.0, 48),  # 外側の陸の環の外周
    (RINGS[1][2], "tin", 14.0, 6.0, 32),  # 内側の陸の環の外周
    (R_ISLAND, "orichalcum", 16.0, 6.0, 20),  # 中央島の外周
]
TOWER_W, TOWER_H = 14.0, 24.0  # 仮

# ---------------------------------------------------------------- 中央島（アクロポリス）
# ポセイドン神殿: 長さ 1 スタディオン、幅 3 プレトロン、高さは釣り合った大きさ（記述あり）。高さと柱割りは仮
TEMPLE_L = STADION  # 南北方向の長さ
TEMPLE_W = 3 * PLETHRON  # 東西方向の幅
TEMPLE_CENTER = (0.0, 40.0)
TEMPLE_PODIUM_H = 6.0  # 仮
TEMPLE_COL_H = 30.0  # 仮
TEMPLE_COL_R = 1.7  # 仮
TEMPLE_COLS_FRONT = 10  # 仮: 正面（南北の短辺）の柱の数
TEMPLE_COLS_SIDE = 19  # 仮: 側面（東西の長辺）の柱の数
TEMPLE_ENTAB_H = 6.0  # 仮
TEMPLE_ROOF_H = 10.0  # 仮
GOLD_ENCLOSURE = (TEMPLE_CENTER[0], TEMPLE_CENTER[1] + 15, 26.0, 40.0)  # 仮: 黄金の囲い（クレイトとポセイドンの聖所）
PALACES = [(-260.0, 30.0, "西の王宮"), (260.0, 30.0, "東の王宮")]  # 仮の位置
PALACE_SIZE = (120.0, 80.0, 18.0)  # 仮
SPRINGS = [(-150.0, -250.0, "冷泉"), (150.0, -250.0, "温泉")]  # 仮
TRIDENT_COLUMN = (0.0, -95.0)  # 仮: 神殿の南正面に立つ三叉の矛の記念柱（演出）
TRIDENT_COL_H = 22.0

# ---------------------------------------------------------------- 陸の環の建物（記述あり: 神殿・庭・体育場・兵舎・競馬場。配置と大きさは仮）
HIPPODROME = (RINGS[3][1] + 0.5 * STADION, RINGS[3][1] + 1.5 * STADION)  # 外側の陸の環に 1 スタディオン幅の競馬場
ROUND_TEMPLES = [(RINGS[1][1] + STADION, a) for a in (45.0, 135.0, 225.0, 315.0)]  # (半径, 角度)
ROUND_TEMPLE_R = 22.0
STOAS = [(RINGS[1][1] + 1.4 * STADION, a) for a in (20.0, 160.0, 200.0, 340.0)]
STOA_SIZE = (140.0, 22.0, 12.0)
BARRACKS_RING1 = [(RINGS[1][1] + 0.55 * STADION, a) for a in range(0, 360, 30) if a % 90 != 0]
BARRACKS_RING2 = [(RINGS[3][1] + 2.4 * STADION, a) for a in range(10, 360, 20) if abs(((a - 270) + 180) % 360 - 180) > 12]
BARRACKS_SIZE = (70.0, 24.0, 10.0)

# ---------------------------------------------------------------- 港・灯台（外港と灯台は記述の「港」を演出として具体化）
HARBOR_Y = COAST_Y_3D
LIGHTHOUSE = (CANAL_W * 0.5 + 130.0, COAST_Y_3D - 260.0)
LIGHTHOUSE_H = 60.0
SHIPYARD = (CANAL_W / 2 + 40.0, -R_OUTER - 140.0)  # 運河の東岸の船台（仮）

# ---------------------------------------------------------------- 貨幣（創作。クリティアスに貨幣の記述は無い）
COINS = [
    # (名前, 素材, 直径mm, 表の図柄, 裏の図柄)
    ("オリハルコン貨", "orichalcum", 28.0, "三叉の矛と銘 ΑΤΛΑΝΤΙΣ", "同心円の都（水の環3重・陸の環2重）"),
    ("銀貨", "silver", 22.0, "ポセイドンの横顔（略画）", "三段櫂船"),
    ("青銅貨", "bronze", 16.0, "雄牛", "三叉の矛"),
]

# ---------------------------------------------------------------- 動画の進行表（24fps）
FPS = 24
MAIN_END = 432  # 本編 18 秒
END_CARD = (433, 480)  # ロゴのエンドカード 2 秒
CUES = {
    "scroll_unroll": (1, 30),  # 巻物が上から広がる（冒頭はすでに広がり始めた所から）
    "ink_glow": (24, 46),  # インクが光る
    "wire_rise": (36, 72),  # 線が立ち上がる
    "coins_away": (40, 58),  # 巻物の上の貨幣と封蝋が退く
    "rings": (72, 96),  # 中央島と陸の環
    "walls": (96, 120),  # 城壁と塔
    "bridges": (120, 138),
    "buildings": (138, 162),  # 兵舎・王宮・円形神殿・柱廊・競馬場
    "trees": (162, 180),
    "podium": (180, 195),
    "columns": (195, 245),  # 柱を一本ずつ
    "roof": (245, 258),
    "gold": (258, 270),
    "wire_fade": (96, 270),  # 実体ができた要素から順に線が消える
    "scroll_away": (270, 286),
    "sea_fill": (276, 312),
    "rings_glow": (296, 330),
    "mountains": (282, 326),
    "city_spread": (292, 344),
    "lights": (318, 350),
    "trireme_launch": (322, 346),
    "trireme_sail": (346, 432),
    "title": (384, 404),
}
# カメラのカット（開始フレーム, カメラ名）
CUTS = [
    (1, "CamScroll"),
    (60, "CamRise"),
    (180, "CamTemple"),
    (222, "CamTrident"),
    (270, "CamWide"),
    (350, "CamOffshore"),
]


def polar(r, deg):
    a = math.radians(deg)
    return (r * math.cos(a), r * math.sin(a))


def smooth(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)
