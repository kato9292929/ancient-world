"""音楽と効果音を、外部素材なしで合成する（numpy / scipy）。動画の進行表（plan.CUES）に合わせて鳴らす。

    python atlantis/audio/synth.py out/atlantis/audio/atlantis.wav

音楽: 古代ギリシャ風（リラ＝撥弦、アウロス＝二本の葦笛、枠太鼓）、ニのドリア旋法（D E F G A B C）。
効果音: 巻物、光の線、石を据える音、城壁の金属音、柱を立てる音、水が流れ込む音、波、かもめ、篝火、
神殿の鐘、タイトルの合唱、ロゴのエンドカード。
"""
import os
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, lfilter, sosfilt

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import plan as P  # noqa: E402

SR = 48000
DUR = P.END_CARD[1] / P.FPS  # 20 秒
N = int(SR * DUR)
rng = np.random.default_rng(7)


def t_of(frame):
    return (frame - 1) / P.FPS


def note_hz(name):
    names = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    n, octave = name[:-1], int(name[-1])
    return 440.0 * 2 ** ((names[n] + 12 * (octave - 4)) / 12)


class Bus:
    def __init__(self):
        self.x = np.zeros((N, 2))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(t * SR)
        if i >= N:
            return
        sig = sig[: N - i]
        l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
        self.x[i : i + len(sig), 0] += sig * gain * l
        self.x[i : i + len(sig), 1] += sig * gain * r


def env(n, a, d, sustain=1.0, release=None):
    e = np.ones(n) * sustain
    na = max(1, int(a * SR))
    e[:na] = np.linspace(0, 1, na)
    if release:
        nr = min(n, int(release * SR))
        e[-nr:] *= np.linspace(1, 0, nr)
    if d:
        e *= np.exp(-np.arange(n) / (d * SR))
    return e


def bp(x, lo, hi, order=2):
    sos = butter(order, [lo, hi], btype="band", fs=SR, output="sos")
    return sosfilt(sos, x)


def lp(x, hi, order=2):
    sos = butter(order, hi, btype="low", fs=SR, output="sos")
    return sosfilt(sos, x)


def hp(x, lo, order=2):
    sos = butter(order, lo, btype="high", fs=SR, output="sos")
    return sosfilt(sos, x)


# ---------------------------------------------------------------- 楽器
def lyre(hz, dur=2.5, bright=0.5):
    """リラ: カープラス・ストロング（雑音の一撃を遅延線で回す）。"""
    n = int(dur * SR)
    period = int(SR / hz)
    buf = rng.uniform(-1, 1, period)
    buf = lfilter([1 - bright, bright], [1], buf)
    out = np.empty(n)
    decay = 0.996
    for i in range(n):
        j = i % period
        out[i] = buf[j]
        buf[j] = decay * 0.5 * (buf[j] + buf[(j + 1) % period])
    out = hp(out, 80)
    return out * env(n, 0.002, 0, release=0.2)


def aulos(hz, dur, vib=5.2, breath=0.06):
    """アウロス: 奇数倍音の強い葦笛の音をフォルマントで絞り、ビブラートと息の音を足す。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = hz * (1 + 0.006 * np.sin(2 * np.pi * vib * t) * np.clip(t / 0.4, 0, 1))
    ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum((1 / k) * np.sin(k * ph) * (1.0 if k % 2 else 0.35) for k in range(1, 12))
    s = bp(s, 300, 3500) + breath * bp(rng.standard_normal(n), 1500, 6000)
    return s * env(n, 0.06, 0, release=0.15) * 0.35


def frame_drum(strength=1.0, low=True):
    n = int(0.6 * SR)
    t = np.arange(n) / SR
    f = (95 if low else 180) * np.exp(-t * 8) + (58 if low else 120)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * (7 if low else 14))
    slap = bp(rng.standard_normal(n), 800, 4000) * np.exp(-t * 60) * 0.5
    return (body + slap) * strength


def choir(hzs, dur, vowel=(800, 1150, 2900)):
    """合唱: 一音につき 6 声（少しずつずらしたのこぎり波）をフォルマント（「あ」）に通す。"""
    n = int(dur * SR)
    t = np.arange(n) / SR
    out = np.zeros(n)
    for hz in hzs:
        for v in range(6):
            det = 1 + rng.uniform(-0.006, 0.006)
            vib = 1 + 0.004 * np.sin(2 * np.pi * rng.uniform(4.5, 6) * t + rng.uniform(0, 6))
            ph = np.cumsum(hz * det * vib) / SR
            out += 2 * (ph % 1) - 1
    y = sum(bp(out, f * 0.85, f * 1.15) * g for f, g in zip(vowel, (1.0, 0.6, 0.25)))
    return y * env(n, 1.2, 0, release=1.5) / (len(hzs) * 6) * 3.0


# ---------------------------------------------------------------- 効果音
def thud(depth=1.0):
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    s = np.sin(2 * np.pi * np.cumsum(70 * np.exp(-t * 6) + 38) / SR) * np.exp(-t * 6)
    grit = lp(rng.standard_normal(n), 900) * np.exp(-t * 18) * 0.6
    return (s + grit) * depth


def clang(hz):
    """城壁の金属音: 非調和な倍音が長く残る。"""
    n = int(2.6 * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * hz * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.5), (2.76, 0.6, 2.5), (5.4, 0.35, 4), (8.93, 0.2, 6), (13.3, 0.1, 9)))
    hit = bp(rng.standard_normal(n), 2000, 9000) * np.exp(-t * 80)
    return (s * 0.5 + hit * 0.4) * 0.6


def column_set():
    n = int(0.7 * SR)
    t = np.arange(n) / SR
    knock = np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t * 10) + 90) / SR) * np.exp(-t * 14)
    scrape = bp(rng.standard_normal(n), 400, 2500) * np.exp(-((t - 0.12) ** 2) / 0.004) * 0.25
    return knock + scrape


def bell(hz, dur=5.0):
    n = int(dur * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * hz * r * t) * np.exp(-t * d) for r, a, d in ((0.5, 0.6, 0.6), (1, 1, 0.8), (1.19, 0.5, 1.0), (1.56, 0.4, 1.4), (2.0, 0.35, 1.6), (2.51, 0.2, 2.2), (3.0, 0.15, 3)))
    return s * 0.35


def rustle(dur):
    n = int(dur * SR)
    flutter = np.abs(lp(rng.standard_normal(n), 25)) * 6
    return bp(rng.standard_normal(n), 1500, 7000) * np.clip(flutter, 0, 1) * env(n, 0.05, 0, release=0.3) * 0.5


def shimmer(dur, f0=600, f1=2400):
    """光の線が立ち上がる音: 上がっていく鈴のきらめき。"""
    n = int(dur * SR)
    out = np.zeros(n)
    for k in range(40):
        st = int(rng.uniform(0, 0.85) * n)
        ln = int(0.5 * SR)
        tt = np.arange(ln) / SR
        frac = st / n
        hz = f0 * (f1 / f0) ** frac * rng.choice([1, 1.5, 2])
        ping = np.sin(2 * np.pi * hz * tt) * np.exp(-tt * 9) * 0.12
        out[st : st + ln] += ping[: n - st]
    return out


def water_rush(dur):
    n = int(dur * SR)
    noise = rng.standard_normal(n)
    swell = np.clip(np.linspace(0, 1.4, n), 0, 1) * np.clip(np.linspace(1.6, 0, n), 0, 1)
    lo = lp(noise, 600) * 1.4
    hi = bp(noise, 800, 5000) * 0.4
    return (lo + hi) * swell * 0.6


def waves(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    surge = 0.55 + 0.45 * np.sin(2 * np.pi * t / 3.4) ** 2
    return lp(rng.standard_normal(n), 900) * surge * 0.25 + bp(rng.standard_normal(n), 2000, 6000) * surge**3 * 0.06


def gull():
    n = int(0.55 * SR)
    t = np.arange(n) / SR
    f = 1700 + 900 * np.sin(np.pi * t / 0.55) - 600 * t
    s = np.sin(2 * np.pi * np.cumsum(f) / SR + 2.5 * np.sin(2 * np.pi * 310 * t))
    return bp(s, 900, 4500) * env(n, 0.03, 0, release=0.2) * 0.18


def crackle(dur, density=30):
    n = int(dur * SR)
    out = lp(rng.standard_normal(n), 400) * 0.05
    for _ in range(int(density * dur)):
        i = rng.integers(0, n - 400)
        out[i : i + 300] += bp(rng.standard_normal(300), 1500, 8000) * np.exp(-np.arange(300) / 40) * rng.uniform(0.1, 0.4)
    return out


def coin_clink():
    n = int(1.2 * SR)
    t = np.arange(n) / SR
    s = sum(a * np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, a, d in ((3150, 1, 5), (4870, 0.6, 7), (7020, 0.4, 9)))
    return s * 0.12


def whoosh(dur):
    n = int(dur * SR)
    t = np.arange(n) / SR
    e = np.sin(np.pi * t / dur) ** 2
    return bp(rng.standard_normal(n), 400, 3000) * e * 0.4


def reverb(x, mix=0.25):
    """シュレーダー型の残響（櫛形 4 本 + オールパス 2 本）。"""
    out = np.zeros_like(x)
    for ch in range(2):
        s = x[:, ch]
        acc = np.zeros_like(s)
        for d, g in ((1557, 0.84), (1617, 0.83), (1491, 0.82), (1422, 0.81)):
            d = int(d * SR / 25000) + ch * 23
            acc += lfilter([1], np.r_[1, np.zeros(d - 1), -g], s)
        for d, g in ((225, 0.5), (556, 0.5)):
            d = int(d * SR / 25000)
            acc = lfilter(np.r_[-g, np.zeros(d - 1), 1], np.r_[1, np.zeros(d - 1), -g], acc)
        out[:, ch] = acc / 4
    return x * (1 - mix) + out * mix


# ---------------------------------------------------------------- 構成
def music(bus):
    beat = 60 / 88
    C = P.CUES
    # ドローン（アウロスの低い管）: D3 と A3
    d0 = 0.0
    drone_end = t_of(P.MAIN_END) + 0.6
    bus.add(aulos(note_hz("D3"), drone_end - d0, breath=0.03) * 0.5, d0, 0.55, -0.3)
    bus.add(aulos(note_hz("A3"), drone_end - t_of(C["walls"][0]), breath=0.02) * 0.4, t_of(C["walls"][0]), 0.4, 0.3)
    # リラの分散和音（冒頭から）。ドリアの B（第6音）を効かせる
    arps = [["D4", "A4", "D5", "F5"], ["C4", "G4", "C5", "E5"], ["D4", "A4", "B4", "F5"], ["G3", "D4", "G4", "B4"]]
    t = 0.0
    k = 0
    end_lyre = t_of(P.MAIN_END)
    while t < end_lyre:
        chord = arps[k % len(arps)]
        for j, nm in enumerate(chord):
            bus.add(lyre(note_hz(nm), 2.2), t + j * beat / 2, 0.35, -0.5 + j * 0.3)
        t += beat * 2
        k += 1
    # アウロスの旋律（肉付けが始まってから）
    melody = [("D5", 1), ("E5", 0.5), ("F5", 0.5), ("G5", 1), ("A5", 1.5), ("G5", 0.5), ("F5", 1), ("E5", 1), ("D5", 2),
              ("A4", 1), ("B4", 1), ("C5", 1), ("D5", 1), ("E5", 1.5), ("C5", 0.5), ("D5", 2),
              ("F5", 1), ("G5", 1), ("A5", 1), ("B5", 1), ("A5", 2), ("G5", 1), ("F5", 1), ("E5", 1), ("D5", 3)]
    t = t_of(C["rings"][0])
    for nm, b in melody:
        if t > t_of(C["title"][0]):
            break
        bus.add(aulos(note_hz(nm), b * beat * 0.95), t, 0.5, 0.15)
        t += b * beat
    # 枠太鼓: 肉付けから一定の拍、海が満ちる所で連打、タイトルで一打
    t = t_of(C["rings"][0])
    i = 0
    while t < t_of(C["title"][0]):
        strong = i % 4 == 0
        bus.add(frame_drum(1.0 if strong else 0.55, low=strong or i % 2 == 0), t, 0.55, 0.0)
        if t_of(C["sea_fill"][0]) < t < t_of(C["sea_fill"][1]):
            bus.add(frame_drum(0.35, low=False), t + beat / 2, 0.5, 0.2)
        t += beat
        i += 1
    bus.add(frame_drum(1.4), t_of(C["title"][0]), 0.8)
    # タイトルの合唱: ニのドリアの和音（D F A B）
    bus.add(choir([note_hz("D3"), note_hz("A3"), note_hz("D4"), note_hz("F4"), note_hz("B4")], t_of(P.MAIN_END) - t_of(C["title"][0]) + 0.8), t_of(C["title"][0]), 0.9)


def effects(bus):
    C = P.CUES
    bus.add(rustle(t_of(C["scroll_unroll"][1]) + 0.3), 0.0, 0.8, -0.2)
    bus.add(coin_clink(), t_of(C["coins_away"][0]), 0.9, -0.5)
    bus.add(coin_clink(), t_of(C["coins_away"][0]) + 0.12, 0.6, -0.4)
    bus.add(shimmer(t_of(C["wire_rise"][1]) - t_of(C["wire_rise"][0]) + 0.6), t_of(C["wire_rise"][0]), 1.0, 0.1)
    for k in range(3):  # 中央島と陸の環を据える
        bus.add(thud(1.0), t_of(C["rings"][0]) + k * 0.33, 0.9, -0.3 + k * 0.3)
    for k, hz in enumerate((196.0, 233.0, 262.0)):  # 青銅・錫・オリハルコンの城壁
        bus.add(clang(hz), t_of(C["walls"][0]) + k * 0.33, 0.55, -0.4 + k * 0.4)
    for k in range(2):
        bus.add(thud(0.7), t_of(C["bridges"][0]) + k * 0.35, 0.7, 0.2)
    for k in range(4):
        bus.add(thud(0.5), t_of(C["buildings"][0]) + k * 0.25, 0.6, -0.5 + k * 0.33)
    bus.add(thud(1.1), t_of(C["podium"][0]), 0.9)
    c0, c1 = C["columns"]
    for k in range(18):  # 柱を立てる（全 54 本のうち 3 本に 1 回鳴らす）
        bus.add(column_set(), t_of(c0) + (t_of(c1) - t_of(c0)) * k / 18, 0.45, -0.6 + 1.2 * (k % 6) / 5)
    bus.add(thud(0.8), t_of(C["roof"][0]), 0.8)
    bus.add(bell(330.0), t_of(C["gold"][0]), 0.8, 0.1)
    bus.add(water_rush(t_of(C["sea_fill"][1]) - t_of(C["sea_fill"][0]) + 1.5), t_of(C["sea_fill"][0]) - 0.3, 1.0)
    w0 = t_of(C["sea_fill"][0])
    bus.add(waves(DUR - w0), w0, 0.8)
    for k in range(5):
        bus.add(gull(), t_of(C["mountains"][1]) + k * 1.1 + rng.uniform(0, 0.4), 0.7, rng.uniform(-0.8, 0.8))
    l0 = t_of(C["lights"][0])
    bus.add(crackle(t_of(P.MAIN_END) - l0 + 0.5), l0, 0.7, -0.2)
    bus.add(bell(220.0, 6.0), t_of(C["title"][0]) + 0.4, 0.5, 0.0)


def end_card(bus):
    t0 = t_of(P.END_CARD[0])
    n = int((DUR - t0) * SR)
    tt = np.arange(n) / SR
    pad = sum(np.sin(2 * np.pi * f * tt) for f in (note_hz("D3"), note_hz("A3"), note_hz("D4"))) * np.sin(np.pi * tt / (DUR - t0)) * 0.08
    bus.add(pad, t0, 1.0)
    bus.add(whoosh(0.9), t0 + 15 / P.FPS, 0.9, -0.6)
    bus.add(shimmer(0.9, 1200, 3600), t0 + 17 / P.FPS, 0.8, 0.4)
    bus.add(bell(587.0, 2.0) * 0.6, t0 + 0.25, 0.5)


def main(out):
    mus, sfx = Bus(), Bus()
    music(mus)
    effects(sfx)
    end_card(sfx)
    # 本編の終わりで音楽を絞り切り、エンドカードは専用の音だけにする
    t_end = t_of(P.END_CARD[0])
    fade = np.ones(N)
    i0, i1 = int((t_end - 0.7) * SR), int((t_end + 0.4) * SR)
    fade[i0:i1] = np.linspace(1, 0, i1 - i0)
    fade[i1:] = 0.0
    mix = reverb(mus.x, 0.28) * 0.9 * fade[:, None] + reverb(sfx.x, 0.15)
    mix /= np.max(np.abs(mix)) / 0.89
    tail = int(0.4 * SR)
    mix[-tail:] *= np.linspace(1, 0, tail)[:, None]
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    wavfile.write(out, SR, (mix * 32767).astype(np.int16))
    print("wrote", out, f"{DUR:.1f}s")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.dirname(HERE)), "out", "atlantis", "audio", "atlantis.wav"))
