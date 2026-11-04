import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import render as R  # helpers + video-1 frames
from render import (W, H, font, text_img, paste, ease_pop, emoji, hue_shift, deep_fry, rgb_split,
                    glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, NEON, RED, WHITE, BLACK, EMO, CAN, CAN2)

FPS = 30
SR = 44100
KFPS = 50 / 3
KSRC = os.path.join(HERE, 'src')
KN = 68

# ---------------- timeline ----------------
A0, B0, C0, D0, E0 = 0.0, 5.2, 9.5, 11.5, 15.6
BPM = 130; BT = 60 / BPM
F0 = 17.9; F1 = F0 + 16 * BT
G0 = 25.3; X0 = 28.2; X1 = 29.4; T_END = 32.0
N = int(T_END * FPS)
CAN_T, GLUG_T, CHG_T = 14.0, 14.6, 15.0
VO = {'n1': 0.5, 'n2': 4.45, 'n3': 5.4, 'r1': 11.6, 'n4': 25.5, 'n5': 29.75}

# phonk chop table: (mode, src_start, param)
CHOPS = [('norm', 2.3, 0), ('norm', 2.7, 0), ('stut', 2.3, .25), ('norm', 3.0, 0),
         ('down', 2.3, .72), ('down', 2.7, .72), ('rev', 3.35, 0), ('stut', 3.75, .125),
         ('norm', 3.35, 0), ('stut', 2.7, .25), ('norm', 3.75, 0), ('rev', 3.0, 0),
         ('stut', 2.3, .125), ('stut', 2.3, .0625), ('down', 3.35, .6), ('tape', 3.75, 0)]
WORDS = ['ТАУРИН', 'СМЕНА', 'ТАУРИН', 'ДОМОЙ', 'ПЕЛЬ-', '-МЕНИ', 'СОН?', 'НЕТ',
         'ТАУРИН', 'ЕЩЁ', 'БАНКУ', 'ПЖ', 'ТАУ', 'ТАУ', 'РИИИН', '...']

def chop_src(tl):
    """tl: time since F0 (scalar or array) -> src time in кружок"""
    tl = np.asarray(tl, float)
    k = np.clip((tl // BT).astype(int), 0, 15)
    ph = tl - k * BT
    out = np.zeros_like(tl)
    for i, (m, s, p) in enumerate(CHOPS):
        sel = k == i
        if not sel.any(): continue
        x = ph[sel]
        if m == 'norm': v = s + x
        elif m == 'stut': v = s + np.mod(x, BT * p)
        elif m == 'down': v = s + x * p
        elif m == 'rev': v = s + BT - x
        else: v = s + x - 0.45 * x * x / BT
        out[sel] = v
    return out

def k_src_time(t):
    """кружок source time for output time t (None = not shown live)"""
    if B0 <= t < C0: return 0.0
    if C0 <= t < D0: return t - C0
    if D0 <= t < E0: return 1.95
    if E0 <= t < F0: return 2.0 + (t - E0)
    if F0 <= t < F1: return float(chop_src(t - F0))
    if t >= F1: return 3.1
    return 0.0

# ---------------- кружок frames ----------------
_kc = {}
YY, XX = np.mgrid[0:384, 0:384]
KMASK = (((XX - 192) ** 2 + (YY - 192) ** 2) < 178 ** 2).astype(np.uint8) * 255
KMASK_S = cv2.GaussianBlur(KMASK, (5, 5), 0)
def kframe(st):
    i = int(np.clip(round(st * KFPS), 0, KN - 1))
    if i not in _kc:
        _kc[i] = cv2.cvtColor(cv2.imread(os.path.join(KSRC, f'{i+1:04d}.jpg')), cv2.COLOR_BGR2RGB)
    return _kc[i], i

def kimg(st, size, fx=None, ring=NEON, ring_w=8, sx=1.0, sy=1.0):
    rgb, i = kframe(st)
    rgb = rgb.copy()
    if fx: rgb = fx(rgb, i)
    im = Image.fromarray(rgb).convert('RGBA'); im.putalpha(Image.fromarray(KMASK_S))
    im = im.resize((max(1, int(size * sx)), max(1, int(size * sy))), Image.BICUBIC)
    if ring:
        pad = ring_w + 4
        out = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0))
        d = ImageDraw.Draw(out)
        d.ellipse([pad - ring_w, pad - ring_w, pad + im.width + ring_w, pad + im.height + ring_w], fill=ring + (255,))
        d.ellipse([pad - ring_w // 3, pad - ring_w // 3, pad + im.width + ring_w // 3, pad + im.height + ring_w // 3], fill=(0, 0, 0, 255))
        out.alpha_composite(im, (pad, pad))
        return out, i
    return im, i

def nv(rgb, i, amt=1.0):  # night vision
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    g = np.clip(g * 2.6 + 18, 0, 255)
    n = np.random.default_rng(i).normal(0, 14, g.shape)
    g = np.clip(g + n, 0, 255)
    o = np.stack([g * 0.35, g, g * 0.35], -1)
    o[::2] *= 0.8
    return (o * amt + rgb * (1 - amt)).astype(np.uint8)

def fry_rgb(rgb, i, amt=0.8):
    return cv2.cvtColor(deep_fry(cv2.cvtColor(cv2.resize(rgb, (720, 720)), cv2.COLOR_RGB2BGR)[:, :, :], amt) if False else rgb, cv2.COLOR_BGR2RGB) if False else _fry(rgb, amt)
def _fry(rgb, amt):
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    x = bgr.astype(np.float32); x = np.clip((x - 128) * (1 + .7 * amt) + 128 + 20 * amt, 0, 255).astype(np.uint8)
    x = hue_shift(x, 0, 1 + 1.5 * amt)
    x = cv2.filter2D(x, -1, np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]], np.float32))
    _, e = cv2.imencode('.jpg', x, [cv2.IMWRITE_JPEG_QUALITY, 8]); x = cv2.imdecode(e, 1)
    return cv2.cvtColor(x, cv2.COLOR_BGR2RGB)
def hue_rgb(rgb, deg, sat=1.3):
    return cv2.cvtColor(hue_shift(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR), deg, sat), cv2.COLOR_BGR2RGB)

_faces = {}
def kface(i):
    if i in _faces: return _faces[i]
    rgb, _ = kframe(i / KFPS)
    g = cv2.equalizeHist(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY))
    fs = R.CASC.detectMultiScale(g, 1.1, 4, minSize=(60, 60))
    _faces[i] = max(fs, key=lambda f: f[2] * f[3]).astype(float) if len(fs) else None
    return _faces[i]
_lastk = [np.array([110, 70, 170, 170], float)]
def keyes(i):
    f = kface(i)
    if f is None: f = _lastk[0]
    else: f = 0.6 * f + 0.4 * _lastk[0]; _lastk[0] = f
    x, y, w, h = f
    return (x + .32 * w, y + .42 * h), (x + .68 * w, y + .42 * h)

def lasers_at(c, pts, t, length=1600):
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fl = 0.75 + 0.25 * math.sin(t * 60)
    for j, (ex, ey) in enumerate(pts):
        ang = math.radians(118 if j == 0 else 62) + 0.2 * math.sin(t * 6)
        e2 = (ex + math.cos(ang) * length, ey + math.sin(ang) * length)
        for wd, col in ((40, (255, 0, 0, 90)), (22, (255, 40, 40, 170)), (8, (255, 235, 235, 255))):
            d.line([(ex, ey), e2], fill=col, width=int(wd * fl))
        for r_, col in ((40, (255, 0, 0, 110)), (22, (255, 80, 80, 200)), (9, WHITE + (255,))):
            d.ellipse([ex - r_, ey - r_, ex + r_, ey + r_], fill=col)
    c.alpha_composite(Image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(9)), layer))

# ---------------- backgrounds ----------------
def make_city():
    r = random.Random(5)
    bg = Image.new('RGB', (W, H)); d = ImageDraw.Draw(bg)
    for y in range(H):
        u = y / H; d.line([(0, y), (W, y)], fill=(int(8 + 14 * u), int(10 + 18 * u), int(30 + 30 * u)))
    stars = [(r.randint(0, W), r.randint(0, 700), r.random()) for _ in range(140)]
    bld = []
    x = -20
    while x < W:
        bw = r.randint(90, 180); bh = r.randint(380, 760)
        bld.append((x, H - bh, x + bw, H)); x += bw + r.randint(-10, 20)
    wins = []
    for (x0, y0, x1, y1) in bld:
        for wy in range(y0 + 20, y1 - 30, 34):
            for wx in range(x0 + 12, x1 - 20, 26):
                if r.random() < 0.28: wins.append((wx, wy, r.random()))
    return bg, stars, bld, wins
CITY = make_city()
def city(t, tint=None, dawn=0.0):
    bg, stars, bld, wins = CITY
    c = bg.copy().convert('RGBA'); d = ImageDraw.Draw(c)
    if dawn > 0:
        sky = Image.new('RGBA', (W, H)); sd = ImageDraw.Draw(sky)
        for y in range(H):
            u = y / H
            top = (int(40 + 60 * dawn), int(60 + 100 * dawn), int(120 + 100 * dawn))
            bot = (int(255 * dawn), int(140 * dawn + 40), int(80 * dawn + 40))
            sd.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * u) for a, b in zip(top, bot)) + (255,))
        c = Image.blend(c, sky, min(1, dawn)); d = ImageDraw.Draw(c)
        sy = 1100 - 700 * dawn
        for rr, al in ((260, 50), (180, 90), (110, 255)):
            d.ellipse([W / 2 - rr, sy - rr, W / 2 + rr, sy + rr], fill=(255, 210, 90, al))
    for sx, sy, ph in stars:
        a = int((120 + 120 * math.sin(t * 3 + ph * 20)) * (1 - dawn))
        if a > 0: d.point((sx, sy), fill=(255, 255, 255, a))
    for b in bld: d.rectangle(b, fill=(5, 6, 14, 255))
    for wx, wy, ph in wins:
        on = (math.sin(t * 0.7 + ph * 50) > -0.6)
        if on: d.rectangle([wx, wy, wx + 12, wy + 16], fill=(255, 200, 90, 230) if ph > 0.2 else (140, 200, 255, 230))
    if tint: c.alpha_composite(Image.new('RGBA', (W, H), tint))
    return c

def rays(t, cols, n=14, speed=40, cx=W / 2, cy=H / 2):
    c = Image.new('RGBA', (W, H), cols[1] + (255,)); d = ImageDraw.Draw(c)
    a0 = t * speed
    for k in range(n):
        a = math.radians(a0 + k * 360 / n); b = math.radians(a0 + (k + 0.5) * 360 / n)
        d.polygon([(cx, cy), (cx + 2000 * math.cos(a), cy + 2000 * math.sin(a)), (cx + 2000 * math.cos(b), cy + 2000 * math.sin(b))], fill=cols[0] + (255,))
    return c

def subtitle(c, txt, t, t0, y=1130):
    s = ease_pop(t, t0, 0.15)
    if s <= 0: return
    fo = font(F_BLACK, 34)
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    lines = txt.split('\n')
    lw = max(d0.textlength(l, font=fo) for l in lines)
    box = Image.new('RGBA', (int(lw) + 40, 52 * len(lines) + 20), (0, 0, 0, 0)); bd = ImageDraw.Draw(box)
    bd.rounded_rectangle([0, 0, box.width - 1, box.height - 1], 10, fill=(0, 0, 0, 190))
    for j, l in enumerate(lines):
        bd.text((box.width / 2, 36 + 52 * j), l, font=fo, fill=(255, 240, 120), anchor='ms')
    paste(c, box, W / 2, y, s)

def battery(c, x, y, frac, t, label=True):
    d = ImageDraw.Draw(c)
    w, h = 200, 84
    d.rounded_rectangle([x, y, x + w, y + h], 12, outline=WHITE, width=7, fill=(0, 0, 0, 160))
    d.rectangle([x + w + 2, y + 24, x + w + 16, y + h - 24], fill=WHITE)
    f = max(0, min(1, frac))
    col = RED if frac < 0.2 else (NEON if frac <= 1.0 else ((255, 0, 200) if int(t * 12) % 2 else NEON))
    if f > 0 and not (frac < 0.2 and int(t * 4) % 2): d.rounded_rectangle([x + 12, y + 12, x + 12 + (w - 24) * f, y + h - 12], 6, fill=col)
    if label:
        txt = f'{int(frac*100)}%' if frac < 9.99 else '∞%'
        d.text((x + w / 2, y + h + 44), txt, font=font(F_BLACK, 52), fill=col, anchor='mm', stroke_width=5, stroke_fill=BLACK)

def ff_tri(d, x, y, s, col):
    d.polygon([(x, y - s), (x, y + s), (x + s * 1.6, y)], fill=col)

# ---------------- AUDIO ----------------
def load_wav(p):
    w = wave.open(p); sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch == 2: a = a.reshape(-1, 2).mean(1)
    if sr != SR: a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)
    return a

def build_audio(out_path):
    n = int(T_END * SR); mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(3)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def tt(d): return np.arange(int(d * SR)) / SR
    K = load_wav(os.path.join(HERE, 'k.wav'))  # кружок audio
    V1 = load_wav(os.path.join(HERE, 'v1.wav'))
    # ambient pad (A-D)
    t = tt(E0)
    pad = sum(np.sin(2 * np.pi * f * t + 0.3 * np.sin(t * 0.5 + f)) for f in (110, 130.8, 164.8, 220)) * 0.04
    pad *= np.minimum(1, t / 1.5) * np.clip((E0 - t) / 0.3, 0, 1)
    pad[int(C0 * SR):] *= 0.5
    cr = (np.sin(2 * np.pi * 4300 * t) * (np.sin(2 * np.pi * 18 * t) > 0.6) * (np.sin(2 * np.pi * 0.8 * t) > 0.2)) * 0.02
    add(0, pad + cr * (t < C0))
    # voices
    for k, t0 in VO.items():
        v = load_wav(os.path.join(HERE, 'vo', f'{k}.wav'))
        if k == 'r1':
            v = np.sign(v) * np.abs(v) ** 0.8  # crunch
            v = np.concatenate([v, np.zeros(2000)]) + 0.35 * np.concatenate([np.zeros(2000), v])
        else:
            # pseudo-reverb room for narrator
            v2 = v.copy()
            for dl, g in ((0.043, .35), (0.071, .25), (0.11, .15)):
                v2[int(dl * SR):] += g * v[:-int(dl * SR)]
            v = v2
        add(t0, v / (np.abs(v).max() + 1e-6) * 0.85)
    # кружок original audio C & E
    add(C0, K[:int(2.0 * SR)])
    add(E0, K[int(2.0 * SR):int(4.3 * SR)])
    # whoosh on appear
    t = tt(0.5); wn = rng.standard_normal(len(t)) * np.sin(np.pi * t / 0.5) ** 2
    add(B0 - 0.1, np.convolve(wn, np.ones(8) / 8, 'same') * 0.4)
    for k in range(3):  # reticle beeps
        t = tt(0.07); add(B0 + 0.5 + k * 0.15, 0.15 * np.sin(2 * np.pi * 2400 * t))
    # D: low battery beeps
    for k in range(5):
        t = tt(0.12); add(D0 + 0.2 + k * 0.6, 0.18 * np.sign(np.sin(2 * np.pi * 880 * t)))
    # can open, glugs, charge
    t = tt(0.4); x = np.diff(np.concatenate([[0], rng.standard_normal(len(t))])); add(CAN_T, 0.5 * x * np.exp(-t * 8))
    for k in range(3):
        t = tt(0.18); f = 180 + 500 * t / 0.18
        add(GLUG_T + k * 0.18, 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.18))
    t = tt(0.6); f = 200 + 2400 * (t / 0.6) ** 2; add(CHG_T, 0.18 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)))
    def boom(d=1.0, f0=130):
        t = tt(d); f = f0 * np.exp(-t * 5) + 38
        return np.tanh(2.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3))
    add(E0, boom(1.2), 0.9)
    # ---------- PHONK ----------
    st16 = BT / 4
    def kick(): t = tt(0.55); f = 160 * np.exp(-t * 18) + 45; return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4))
    def snare(): t = tt(0.22); return (0.6 * rng.standard_normal(len(t)) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25))
    def hat(): t = tt(0.04); x = np.diff(np.concatenate([[0], rng.standard_normal(len(t))])); return 0.5 * x * np.exp(-t * 90)
    def bell(semi):
        t = tt(0.22); r = 2 ** (semi / 12)
        x = np.sign(np.sin(2 * np.pi * 540 * r * t)) + np.sign(np.sin(2 * np.pi * 800 * r * t))
        x = np.convolve(x, np.ones(4) / 4, 'same')
        return 0.25 * x * np.exp(-t * 14)
    mel = [0, 0, 3, 0, 7, 5, 3, 0, 0, 0, 3, 5, 7, 10, 7, 5]
    for bar in range(4):
        b0 = F0 + bar * 16 * st16
        for s in range(16):
            ts = b0 + s * st16
            last_beat = bar == 3 and s >= 12
            if s in (0, 6, 10) and not last_beat: add(ts, kick(), 0.85)
            if s in (4, 12) and not last_beat: add(ts, snare(), 0.5)
            if not last_beat:
                if s % 2 == 0 or (bar % 2 == 1 and s >= 12): add(ts, hat(), 0.35)
                if bar == 2 and s >= 14:
                    for q in range(3): add(ts + q * st16 / 3, hat(), 0.3)
            if s % 2 == 0 and not last_beat: add(ts, bell(mel[(s // 2) + (8 if bar % 2 else 0)] - (5 if bar == 3 else 0)), 0.6)
    # voice chops
    tl = np.arange(int((F1 - F0) * SR)) / SR
    srcs = chop_src(tl)
    ch = np.interp(srcs * SR, np.arange(len(K)), K)
    edge = np.ones_like(ch)  # declick at chop borders
    for k in range(16):
        i0 = int(k * BT * SR); edge[i0:i0 + 120] = np.linspace(0, 1, 120)[:len(edge[i0:i0 + 120])]
    add(F0, ch * edge * 1.1)
    add(F1, boom(0.8, 90), 0.6)
    # G: dawn shimmer, crossover clip audio from video 1, end
    t = tt(X0 - G0); sh = sum(np.sin(2 * np.pi * f * t) for f in (523, 659, 784, 1046)) * 0.03 * np.minimum(1, t) * np.clip((X0 - G0 - t) / 0.3, 0, 1)
    add(G0, sh)
    v1 = V1[:int((X1 - X0) * SR)].copy(); v1[-2000:] *= np.linspace(1, 0, 2000)
    add(X0, v1, 0.8)
    t = tt(T_END - X1); outro = sum(np.sin(2 * np.pi * f * t) for f in (110, 164.8, 220, 261.6)) * 0.05 * np.minimum(1, t / 0.5) * np.clip((T_END - X1 - t) / 0.8, 0, 1)
    add(X1, outro)
    add(X1, boom(1.0, 100), 0.5)
    # master
    mix = np.tanh(mix * 1.1) * 0.92
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(out_path, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

# ---------------- VIDEO ----------------
def render(fi):
    t = fi / FPS
    rng = random.Random(fi * 131)
    if t < C0:
        c = city(t)
    elif t < E0:
        c = city(t, tint=(0, 40, 0, 120) if t < D0 else (0, 0, 0, 150))
    elif t < F0:
        c = rays(t, [(255, 210, 0), (255, 90, 0)], 16, 120)
    elif t < F1:
        k = int((t - F0) // BT); bar = k // 4
        pal = [[(198, 255, 0), (20, 20, 20)], [(255, 0, 140), (30, 0, 60)], [(0, 230, 255), (0, 20, 60)], [(255, 40, 40), (0, 0, 0)]][bar]
        c = rays(t, pal, 12 + bar * 4, 90 * (1 if bar % 2 == 0 else -1))
    elif t < X0:
        u = (t - G0) / (X0 - G0)
        c = city(t, dawn=min(1, u * 1.2))
    elif t < X1:
        si = (t - X0) * 30
        bgr = R.src_frame(si)
        bgr = R.zoom(bgr, 1.0 + R.punch(t - X0 + R.BEAT0, 0.1, 0.08))
        c = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).convert('RGBA')
    else:
        c = rays(t, [(25, 25, 35), (12, 12, 18)], 20, 10)

    d = ImageDraw.Draw(c)
    st = k_src_time(t)

    # ===== A: doc intro
    if t < B0:
        a = ease_pop(t, 0.2, 0.4)
        ti = text_img('В МИРЕ\nЭНЕРГИЧНЫХ', 104, (255, 230, 150), (60, 30, 0), 8, spacing=-6)
        paste(c, ti, W / 2, 420, a * (1 + 0.02 * math.sin(t * 2)))
        if t > 0.9:
            paste(c, text_img('документальный фильм', 40, WHITE, BLACK, 4), W / 2, 580, ease_pop(t, 0.9, 0.3))
        if VO['n1'] <= t < VO['n2']: subtitle(c, 'Спальный район. Почти полночь.\nОбычные люди давно спят.', t, VO['n1'])
        if t >= VO['n2']:
            subtitle(c, 'Но не он.', t, VO['n2'])
        mins = 23 * 60 + 47 + int(t / 2.5)
        d.text((W - 40, 70), f'{mins//60:02d}:{mins%60:02d}', font=font(F_MONO, 40), fill=WHITE, anchor='rm')
        if t > 4.8: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (t - 4.8) / 0.4))))

    # ===== B: specimen detected
    elif t < C0:
        s = ease_pop(t, B0, 0.35)
        size = 520 * s * (1 + 0.015 * math.sin(t * 4))
        if size > 4:
            k, _ = kimg(0.0, int(size), lambda r, i: nv(r, i, 0.85), ring=(60, 255, 80))
            paste(c, k, W / 2, 560, 1.0, (1 - s) * 200)
        if t > B0 + 0.5:  # reticle
            cx, cy, rr = W / 2, 560, 300 + 10 * math.sin(t * 8)
            for sx_ in (-1, 1):
                for sy_ in (-1, 1):
                    x0, y0 = cx + sx_ * rr, cy + sy_ * rr
                    d.line([(x0, y0), (x0 - sx_ * 60, y0)], fill=(60, 255, 80), width=6)
                    d.line([(x0, y0), (x0, y0 - sy_ * 60)], fill=(60, 255, 80), width=6)
            d.text((W / 2, 220), '● ОБЪЕКТ ОБНАРУЖЕН', font=font(F_MONO, 34), fill=(60, 255, 80) if int(t * 4) % 2 else (20, 120, 30), anchor='mm')
        facts = [(B0 + 0.9, 'ВИД:', 'Energeticus vulgaris'), (B0 + 1.4, 'АРЕАЛ:', 'дом ⇄ работа'),
                 (B0 + 1.9, 'РАЦИОН:', 'пельмени, таурин'), (B0 + 2.4, 'СОН:', 'не обнаружен')]
        for j, (t0, kk, vv) in enumerate(facts):
            a = ease_pop(t, t0, 0.15)
            if a > 0:
                y = 900 + j * 52
                lbl = Image.new('RGBA', (640, 48), (0, 0, 0, 0)); ld = ImageDraw.Draw(lbl)
                ld.rectangle([0, 0, 639, 47], fill=(0, 0, 0, 170))
                ld.text((14, 24), kk, font=font(F_MONO, 26), fill=(60, 255, 80), anchor='lm')
                ld.text((180, 24), vv, font=font(F_SYM, 26) if '⇄' in vv else font(F_MONO, 26), fill=WHITE, anchor='lm')
                paste(c, lbl, W / 2 - (1 - a) * 300, y, 1.0, 0, a)
        if t >= VO['n3']: subtitle(c, 'Перед нами энергичный обыкновенный.\nОн возвращается с работы.', t, VO['n3'], 1160)

    # ===== C: live dark part
    elif t < D0:
        k, i = kimg(st, 560, lambda r, i: nv(r, i, 0.7), ring=(60, 255, 80))
        paste(c, k, W / 2 + rng.uniform(-3, 3), 600 + rng.uniform(-3, 3))
        d.ellipse([50, 60, 80, 90], fill=RED if int(t * 2) % 2 else (90, 0, 0))
        d.text((95, 75), 'REC  НОЧНОЕ ВИДЕНИЕ', font=font(F_MONO, 28), fill=WHITE, anchor='lm')
        battery(c, W - 250, 140, 0.03, t, False)
        d.text((W - 150, 270), 'ЗАРЯД 3%', font=font(F_BLACK, 34), fill=RED, anchor='mm', stroke_width=4, stroke_fill=BLACK)
        subtitle(c, '[неразборчивое бормотание\nуставшего энергичного]', t, C0 + 0.1, 1080)

    # ===== D: battery dying -> drink
    elif t < E0:
        droop = min(1, (t - D0) / 2.4)
        recov = ease_pop(t, CHG_T, 0.3)
        sy = 1 - 0.28 * droop * (1 - recov); sx = 1 + 0.1 * droop * (1 - recov)
        def fxd(r, i, dr=droop):
            g = cv2.cvtColor(cv2.cvtColor(r, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
            g = np.clip(g.astype(np.float32) * (2.0 - 0.8 * dr) + 10, 0, 255).astype(np.uint8)
            return g
        k, i = kimg(st, 560, fxd, ring=RED if int(t * 4) % 2 else (90, 0, 0), sx=sx, sy=sy)
        paste(c, k, W / 2, 600 + 560 * (1 - sy) / 2, 1.0, 8 * droop * (1 - recov))
        if t < CHG_T:
            frac = 0.03 * (1 - min(1, (t - D0) / 2.5)) + 0.001
        else:
            u = (t - CHG_T) / (E0 - CHG_T); frac = 0.05 + u ** 2 * 10
        battery(c, W / 2 - 100, 130, frac, t)
        if t < CAN_T:
            w = text_img('⚠ НИЗКИЙ ЗАРЯД', 64, RED, BLACK, 7, f=F_SYM)
            if int(t * 4) % 2: paste(c, w, W / 2, 1000)
            subtitle(c, 'ВНИМАНИЕ. КРИТИЧЕСКИ НИЗКИЙ ЗАРЯД.\nТРЕБУЕТСЯ ТАУРИН.', t, VO['r1'], 1130)
        # can fly-in and tilt
        if CAN_T <= t < CHG_T + 0.2:
            u = min(1, (t - CAN_T) / 0.55)
            cx = W + 120 - (W + 120 - 470) * (1 - (1 - u) ** 3); cy = 1150 - 430 * (1 - (1 - u) ** 2)
            tilt = 0 if t < GLUG_T else min(110, (t - GLUG_T) * 400)
            paste(c, CAN, cx, cy, 1.25, tilt)
            if t < CAN_T + 0.35: paste(c, text_img('*ПШШШ*', 70, WHITE, BLACK, 7), W / 2, 1080, ease_pop(t, CAN_T, 0.1), -6)
            if t >= GLUG_T: paste(c, text_img('*БУЛЬ БУЛЬ БУЛЬ*', 64, NEON, BLACK, 7), W / 2, 1080, ease_pop(t, GLUG_T, 0.1), rng.uniform(-4, 4))
        if t >= CHG_T + 0.2:
            paste(c, text_img('ЗАРЯЖАЕТСЯ…', 70, NEON, BLACK, 7), W / 2, 1080, 1, rng.uniform(-3, 3))

    # ===== E: resurrection
    elif t < F0:
        p = R.punch(t - E0 + 0.07, 1, 0.12)
        k, i = kimg(st, 600, lambda r, i: _fry(r, 0.5 + 0.5 * p), ring=NEON, ring_w=12)
        sc = 1 + 0.25 * math.exp(-(t - E0) / 0.15)
        paste(c, k, W / 2 + rng.uniform(-14, 14), 620 + rng.uniform(-14, 14), sc, rng.uniform(-4, 4))
        if t > E0 + 0.35:
            (lx, ly), (rx, ry) = keyes(i)
            scl = 600 * sc / 384; ox = W / 2 - 300 * sc; oy = 620 - 300 * sc
            lasers_at(c, [(ox + lx * scl, oy + ly * scl), (ox + rx * scl, oy + ry * scl)], t)
        R.rain(c, t, E0, F0, [EMO['⚡'], CAN, EMO['🔋'], CAN2], 16, 77, (80, 150), (1400, 2200))
        paste(c, text_img('ОН ВОСКРЕС', 104, WHITE, BLACK, 11), W / 2, 210, ease_pop(t, E0 + 0.05, 0.2) * (1 + 0.1 * p), rng.uniform(-3, 3))
        battery(c, W / 2 - 100, 990, 99.0, t)
        if t < E0 + 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - (t - E0) / 0.12)))))

    # ===== F: phonk remix
    elif t < F1:
        tl = t - F0; k = int(tl // BT); ph = tl - k * BT; bar = k // 4
        p = math.exp(-ph / 0.09)
        mode = CHOPS[k][0]
        def fxk(r, i, hue=0, fry=0.0):
            if fry: r = _fry(r, fry)
            if hue: r = hue_rgb(r, hue)
            return r
        if mode == 'rev': flip = True
        else: flip = False
        if bar == 0:
            # DVD bounce
            size = 470 * (1 + 0.15 * p)
            px = 60 + size / 2 + abs(((tl * 380) % (2 * (W - size - 120))) - (W - size - 120))
            py = 200 + size / 2 + abs(((tl * 520) % (2 * (H - size - 500))) - (H - size - 500))
            kk, _ = kimg(st, int(size), lambda r, i: fxk(r, i, (tl * 300) % 360), ring=[NEON, (255, 0, 140), (0, 230, 255), (255, 255, 255)][k % 4], ring_w=12)
            if flip: kk = kk.transpose(Image.FLIP_LEFT_RIGHT)
            paste(c, kk, px, py)
            paste(c, text_img('ЭНЕРГИЧНЫЙ\nPHONK', 96, NEON, BLACK, 10, f=F_BLACKI, spacing=-8), W / 2, 150, ease_pop(tl, 0, 0.2) * (1 + 0.12 * p), -4)
        elif bar == 1:
            for j in range(4):
                gx, gy = j % 2, j // 2
                sy = 0.7 if mode == 'down' else 1.0; sx = 1.25 if mode == 'down' else 1.0
                kk, _ = kimg(float(chop_src(max(0, tl - j * 0.06))), 320, lambda r, i, j=j: fxk(r, i, j * 90 + tl * 200), ring=[NEON, (255, 0, 140), (0, 230, 255), (255, 200, 0)][j], sx=sx, sy=sy)
                if flip: kk = kk.transpose(Image.FLIP_LEFT_RIGHT)
                paste(c, kk, 190 + gx * 340, 380 + gy * 390, 1 + 0.12 * p * (1 if (k + j) % 2 else -0.5))
        elif bar == 2:
            ang = math.sin(tl * 3) * 8
            layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
            for j in range(9):
                gx, gy = j % 3, j // 3
                kk, _ = kimg(float(chop_src(max(0, tl - j * 0.04))), 215, lambda r, i, j=j: fxk(r, i, j * 40, 0.4 if (j + k) % 3 == 0 else 0), ring=[NEON, (255, 0, 140), (0, 230, 255)][(j + k) % 3], ring_w=7)
                if flip and j % 2: kk = kk.transpose(Image.FLIP_LEFT_RIGHT)
                paste(layer, kk, 125 + gx * 235, 340 + gy * 245, 1 + 0.15 * p * ((j + k) % 2))
            layer = layer.rotate(ang, center=(W / 2, 585), resample=Image.BICUBIC)
            c.alpha_composite(layer)
        else:
            u = (tl - 12 * BT) / (4 * BT)
            size = int(560 + 900 * u ** 1.5)
            tape = mode == 'tape'
            kk, i = kimg(st, size, lambda r, i: fxk(r, i, 0 if tape else (tl * 500) % 360, 0 if tape else 0.7), ring=RED, ring_w=14)
            if tape:
                g = np.array(kk); g[..., :3] = (g[..., :3].mean(-1, keepdims=True) * (1 - 0.7 * ph / BT)).astype(np.uint8); kk = Image.fromarray(g)
            paste(c, kk, W / 2 + rng.uniform(-20, 20) * (not tape), 600 + rng.uniform(-20, 20) * (not tape), 1, (tl * 400) % 360 if mode == 'stut' else 0)
        # beat words
        wd = WORDS[k]
        wi = text_img(wd, 140 if len(wd) < 7 else 110, WHITE if k % 2 else NEON, BLACK, 13)
        paste(c, wi, W / 2 + rng.uniform(-6, 6), 1090, ease_pop(ph, 0, 0.08) * (1 + 0.2 * p), rng.uniform(-6, 6))
        if ph < 0.05 and bar >= 2:
            arr = np.array(c.convert('RGB'))
            arr = glitch_slices(arr, rng, 8, 80)
            c = Image.fromarray(arr).convert('RGBA'); d = ImageDraw.Draw(c)
        if mode == 'tape':
            c = Image.fromarray((np.array(c.convert('RGB')) * (1 - 0.6 * ph / BT)).astype(np.uint8)).convert('RGBA')

    # ===== G: dawn / time skip
    elif t < X0:
        u = (t - G0) / (X0 - G0)
        e = 1 - (1 - min(1, u * 1.15)) ** 3
        mins = int(12 + e * (7 * 60 + 40 - 12))
        clk = text_img(f'{mins//60:02d}:{mins%60:02d}', 170, WHITE, BLACK, 12, f=F_MONO)
        paste(c, clk, W / 2, 330 + rng.uniform(-2, 2) * (u < 0.85))
        ff = ImageDraw.Draw(c)
        if u < 0.85:
            for q in range(2): ff_tri(ff, W / 2 - 50 + q * 50, 480, 26, WHITE)
            ff.text((W / 2, 540), 'x 3600', font=font(F_MONO, 34), fill=WHITE, anchor='mm', stroke_width=3, stroke_fill=BLACK)
        sl = text_img('СОН: 4 ч 12 мин', 52, (255, 230, 150), BLACK, 5)
        paste(c, sl, W / 2, 640, ease_pop(t, G0 + 0.5, 0.2))
        kk, _ = kimg(3.1, 260, lambda r, i: r, ring=(255, 210, 90))
        paste(c, kk, W / 2 + 18 * math.sin(t * 2), 850 + 12 * math.sin(t * 3), 1, 10 * math.sin(t * 1.3))
        paste(c, text_img('z z Z', 56, WHITE, BLACK, 5), W / 2 + 170, 720 - 20 * ((t * 1.5) % 1), 1)
        if t >= VO['n4']: subtitle(c, 'Через семь часов он снова\nпойдёт на работу.', t, VO['n4'], 1130)
        if t > X0 - 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (t - (X0 - 0.12)) / 0.12))))

    # ===== X: crossover with video 1
    elif t < X1:
        paste(c, text_img('07:40', 150, NEON, BLACK, 12, f=F_MONO), W / 2, 800, ease_pop(t, X0, 0.15), -3)
        paste(c, text_img('ГАЗУЕМ', 120, WHITE, BLACK, 12), W / 2, 950, ease_pop(t, X0 + 0.4, 0.15), 3)
        battery(c, W / 2 - 100, 1040, 0.04, t, True)
        paste(c, text_img('(заряд с ночи не восстановился)', 34, WHITE, BLACK, 4), W / 2, 1225, ease_pop(t, X0 + 0.6, 0.15))

    # ===== H: end card
    else:
        lt = t - X1
        cx, cy, R_ = W / 2, 560, 230
        d.ellipse([cx - R_, cy - R_, cx + R_, cy + R_], outline=NEON, width=8)
        for q in range(4):  # arrowheads on the loop
            a = lt * 1.6 + q * math.pi / 2
            x, y = cx + R_ * math.cos(a), cy + R_ * math.sin(a)
            ta = a + math.pi / 2
            pts = [(x + 34 * math.cos(ta), y + 34 * math.sin(ta)),
                   (x + 22 * math.cos(ta + 2.4), y + 22 * math.sin(ta + 2.4)),
                   (x + 22 * math.cos(ta - 2.4), y + 22 * math.sin(ta - 2.4))]
            d.polygon(pts, fill=NEON)
        a = lt * 1.6
        # night кружок and day frame orbiting
        kk, _ = kimg(3.1, 190, lambda r, i: r, ring=(120, 140, 255))
        paste(c, kk, cx + R_ * math.cos(a + math.pi), cy + R_ * math.sin(a + math.pi))
        day = cv2.cvtColor(R.src_frame(5), cv2.COLOR_BGR2RGB)
        day = cv2.resize(day[200:200 + 720, :], (384, 384))
        di = Image.fromarray(day).convert('RGBA'); di.putalpha(Image.fromarray(KMASK_S)); di = di.resize((190, 190))
        ring = Image.new('RGBA', (214, 214), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, 213, 213], fill=(255, 210, 90, 255)); ring.alpha_composite(di, (12, 12))
        paste(c, ring, cx + R_ * math.cos(a), cy + R_ * math.sin(a))
        paste(c, CAN, cx, cy, 0.9, math.sin(lt * 5) * 20)
        ti = text_img('КРУГОВОРОТ\nЭНЕРГИЧНОГО\nВ ПРИРОДЕ', 86, WHITE, BLACK, 9, spacing=-4)
        paste(c, ti, W / 2, 1000, ease_pop(t, X1 + 0.15, 0.25))
        d.text((W / 2, 1210), 'СЕРИЯ №847½ · НОЧНАЯ', font=font(F_MONO, 28), fill=(170, 170, 170), anchor='mm')
        if t > T_END - 0.5: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (t - (T_END - 0.5)) / 0.5))))

    return np.array(c.convert('RGB'))

if __name__ == '__main__':
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:05.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--audio':
        build_audio(sys.argv[2]); sys.exit()
    out = sys.argv[1]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(N):
        p.stdin.write(render(fi).tobytes())
        if fi % 100 == 0: print(fi, flush=True)
    p.stdin.close(); p.wait()
