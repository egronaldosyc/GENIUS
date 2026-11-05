import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, 'v2'), os.path.join(SP, 'v4'), os.path.join(SP, 'v5')): sys.path.insert(0, p)
import render as R
import render2 as R2
import render3 as R3
import render4 as R4
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, NEON, WHITE, BLACK, EMO, CAN, CAN2, emoji
from render3 import zoomc, rgbsplit, P, flash
from render2 import hue_rgb, _fry

FPS, SR = 30, 44100
BPM = 150; BT = 60 / BPM
F_MED = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
EMJ = {k: emoji(k, 150) for k in ['😭', '💀', '🗿', '🔥', '😱', '🍝', '🍜', '🥟', '🌊', '❤️', '✨', '🤯', '👁️', '🥫', '😋', '⚡']}

# ---------------- sources ----------------
_cache = {}
def _ld(d, i, key, fn=None):
    if key in _cache: return _cache[key]
    if len(_cache) > 300: _cache.pop(next(iter(_cache)))
    im = cv2.cvtColor(cv2.imread(os.path.join(HERE, d, i)), cv2.COLOR_BGR2RGB)
    if fn: im = fn(im)
    _cache[key] = im; return im
def M(t): i = int(np.clip(round(t * 30), 0, 2244)); return _ld('fm', f'{i+1:05d}.jpg', ('m', i))
def N2(t): i = int(np.clip(round(t * 30), 0, 1632)); return _ld('f2', f'{i+1:04d}.jpg', ('n2', i))
KM = None
def N1(t):
    i = int(np.clip(round(t * 30), 0, 445))
    def fx(im):
        global KM
        if KM is None:
            yy, xx = np.mgrid[0:720, 0:720]; KM = cv2.GaussianBlur((((xx - 360) ** 2 + (yy - 360) ** 2) < 330 ** 2).astype(np.float32), (7, 7), 0)[..., None]
        bg = cv2.GaussianBlur(cv2.resize(im, (W, H)), (0, 0), 30) * 0.5
        out = bg.copy(); out[280:1000] = out[280:1000] * (1 - KM) + im * KM
        return out.astype(np.uint8)
    return _ld('f1', f'{i+1:04d}.jpg', ('n1', i), fx)
C, C2, E = R3.cframe, R4.c2, R3.eframe
SELFIE, HOME = R3.IMG_SELFIE, R4.HOME
FOOD = [R4.POST[k] for k in ('p0833', 'p1453', 'p2355', 'p1950')]
SRC = {'m': M, 'n2': N2, 'n1': N1, 'c': C, 'c2': C2, 'e': E}

# ---------------- chunk list ----------------
CH = []
def m(a, b, **kw): CH.append(dict(k='m', a=a, b=b, d=b - a, **kw))
def e(kind, d, **kw): CH.append(dict(k=kind, d=d, **kw))
m(0.0, 0.5)
e('collage', 1.0, src='n2', st=0.3, n=[1, 2, 3])
m(0.5, 1.4)
e('clip', 1.9, src='n2', a=0.0, top='Он говорит это в понедельник 😭', caps=[])
m(1.5, 4.7)
e('clip', 4.6, src='n2', a=10.0, caps=[(0.3, 'ЕДА', 0), (0.75, 'ЗАКОНЧИЛАСЬ', 0), (3.6, 'ВЕРНЁТСЯ ДОМОЙ', 1)], food=(0.9, 3.4), freeze=(4.2, 4.6), boom=[0.3, 4.2])
m(5.0, 9.4)
e('clip', 2.5, src='c2', a=92.5, caps=[(0.4, 'ВЫБИРАЕТ\nКАК СОМЕЛЬЕ', 0)], boom=[1.6])
e('clip', 2.0, src='c2', a=96.0, caps=[(0.2, 'ДЕГУСТАЦИЯ 🍷', 0)], fx='fry', boom=[0.2])
m(12.5, 15.5)
e('collage', 2.0, src='n2', st=33.0, n=[1, 2, 3, 4, 5], stutter=(0.95, 1.4))
m(16.0, 17.0)
e('clip', 1.8, src='n2', a=26.8, caps=[(0.4, 'ЕМУ ПОФИГУ', 0)], fx='glitch')
m(18.6, 22.6)
e('clip', 2.06, src='c', a=73.9, sp=5.0, caps=[(0.1, 'ТЕМ ВРЕМЕНЕМ\nЕГО ТРЕНИРОВКА', 0)], fx='sat')
e('clip', 0.85, src='c', a=86.45, caps=[(0.0, 'НУ ЕГО НАФИГ', 0)], boom=[0.0])
m(24.5, 28.3)
e('nobody', 2.4)
m(28.6, 32.6)
e('clip', 2.0, src='n2', a=38.8, fx='psy', caps=[(0.3, 'Эээээ', 2)])
m(35.0, 39.5)
e('clip', 1.9, src='n2', a=41.0, fx='fry', caps=[(0.2, 'ВСЁ ЗАДУМАННОЕ', 0), (1.0, 'ПОЛУЧИТСЯ', 0)], boom=[1.0])
m(40.5, 42.9)
e('pyramid', 4.0, a=49.0)
e('clip', 1.5, src='n1', a=1.8, caps=[(0.2, 'СЕГОДНЯШНИЙ КРУЖОК', 3)])
m(9.6, 12.3)
e('clip', 5.3, src='n2', a=28.0, caps=[(2.9, 'УЛЬТРА', 0), (3.45, 'МЕГА', 0), (4.1, 'ВАЖНОЕ ДЕЛО', 1)], boom=[2.9, 3.45, 4.1], zoomhits=[2.9, 3.45, 4.1])
e('clip', 2.7, src='n2', a=35.9, caps=[(1.0, 'МОРЕ ПОЗИТИВА', 0)], rain=('🌊', '❤️', '✨'))
m(32.6, 35.0)
e('strobe', 7.0, a=67.8)
e('clip', 2.2, src='n2', a=43.0, caps=[(0.5, 'ПОБОЛЬШЕ ЕДЫ', 0)], food=(0.3, 2.2))
e('clip', 3.1, src='n2', a=45.2, fx='mirror', caps=[(0.4, 'ТЕПЛА И УЮТА', 1)])
e('clip', 1.4, src='n1', a=12.4, caps=[], fx='zoomin')
m(1.5, 2.6)
e('end', 1.6)
STARTS = []; _t = 0
for c in CH: STARTS.append(_t); _t += c['d']
T_END = _t; N = int(round(T_END * FPS))
def chunk_at(t):
    for i, c in enumerate(CH):
        if t < STARTS[i] + c['d']: return i, t - STARTS[i]
    return len(CH) - 1, CH[-1]['d'] - 1e-3

# ---------------- helpers ----------------
def meme_cap(c, txt, tl, t0, style=0, y=None, rng=None):
    s = ease_pop(tl, t0, 0.08)
    if s <= 0: return
    if style == 0:
        im = text_img(txt.upper(), 104 if len(txt) < 10 else 78, WHITE, BLACK, 11, spacing=-8)
        paste(c, im, W / 2 + (rng.uniform(-3, 3) if rng else 0), y or 1040, s * (1 + 0.35 * math.exp(-(tl - t0) / 0.06)), rng.uniform(-3, 3) if rng else 0)
    elif style == 1:
        im = text_img(txt.upper(), 92, (255, 230, 0), BLACK, 10)
        paste(c, im, W / 2, y or 1040, s * (1 + 0.35 * math.exp(-(tl - t0) / 0.06)), -4)
    elif style == 2:
        im = text_img(txt, 150, (255, 40, 200), (20, 0, 40), 10, f=F_BLACKI)
        paste(c, im, W / 2 + (rng.uniform(-8, 8) if rng else 0), y or 1100, s, -6)
    else:
        im = text_img(txt, 40, BLACK, WHITE, 0, f=F_MED); bg = Image.new('RGBA', (im.width + 30, im.height + 14), WHITE + (240,)); bg.alpha_composite(im, (15, 7))
        paste(c, bg, W / 2, y or 160, s)
def top_bar(c, txt, h=230):
    d = ImageDraw.Draw(c); d.rectangle([0, 0, W, h], fill=WHITE)
    lines = txt.split('\n'); fo = font(F_MED, 40)
    for j, l in enumerate(lines):
        em = [e_ for e_ in EMJ if e_ in l]
        clean = l
        for e_ in em: clean = clean.replace(e_, '').rstrip()
        lw = d.textlength(clean, font=fo) + (52 if em else 0)
        y = h / 2 + (j - (len(lines) - 1) / 2) * 54
        d.text((W / 2 - lw / 2, y), clean, font=fo, fill=BLACK, anchor='lm')
        if em: paste(c, EMJ[em[0]], W / 2 + lw / 2 - 22, y, 44 / 150)
def beat_punch(tl, amt=0.08, dec=0.07):
    p = tl % BT; return amt * math.exp(-p / dec)
_faces = {}
def face_eyes(img, key):
    if key in _faces: return _faces[key]
    g = cv2.equalizeHist(cv2.cvtColor(cv2.resize(img, (360, 640)), cv2.COLOR_RGB2GRAY))
    fs = R.CASC.detectMultiScale(g, 1.1, 4, minSize=(70, 70))
    if len(fs):
        x, y, w, h = [v * 2 for v in max(fs, key=lambda f: f[2] * f[3])]
        r = [(x + .32 * w, y + .42 * h), (x + .68 * w, y + .42 * h)], w
    else: r = None
    _faces[key] = r; return r
_lastf = [([(W * 0.4, H * 0.38), (W * 0.6, H * 0.38)], 300)]
def psy(img, t, key):
    x = (img // 64) * 64 + 32
    x = hue_rgb(x.astype(np.uint8), 280 + 40 * math.sin(t * 6), 2.2)
    x = rgbsplit(x, 12)
    f = face_eyes(img, key) or _lastf[0]; _lastf[0] = f
    c = P(x); layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    (eyes, fw) = f
    for ex, ey in eyes:
        for r, col in ((fw * 0.09, (60, 255, 60, 120)), (fw * 0.05, (120, 255, 120, 220)), (fw * 0.025, (230, 255, 230, 255))):
            d.ellipse([ex - r, ey - r, ex + r, ey + r], fill=col)
    c.alpha_composite(Image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(10)), layer))
    return c
def grid_bw(img, n, rng):
    g = cv2.cvtColor(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
    g = np.clip((g.astype(np.float32) - 40) * 1.4, 0, 255).astype(np.uint8)
    out = g.copy()
    r = random.Random(n * 7)
    for k in range(n - 1 if n > 1 else 0):
        for _ in range(2):
            s = r.uniform(0.5, 0.75); w = int(W * s); h = int(w * 1.3)
            x = r.randint(-60, W - w + 60); y = r.randint(-60, H - h + 60)
            tile = cv2.resize(g[int(H * 0.12):int(H * 0.12) + int(W * 1.3)], (w, h))
            x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + w), min(H, y + h)
            out[y0:y1, x0:x1] = tile[y0 - y:y1 - y, x0 - x:x1 - x]
            cv2.rectangle(out, (x0, y0), (x1 - 1, y1 - 1), (255, 255, 255), 8)
    return out
def flying_food(c, tl, t0, t1, seed):
    r = random.Random(seed)
    for k in range(10):
        st = t0 + r.uniform(0, t1 - t0); dt = tl - st
        if dt < 0 or dt > 1.2: continue
        fp = FOOD[k % len(FOOD)].copy(); fp.thumbnail((240, 240)); fp = fp.convert('RGBA')
        m_ = Image.new('L', fp.size, 0); ImageDraw.Draw(m_).ellipse([0, 0, fp.width - 1, fp.height - 1], fill=255); fp.putalpha(m_)
        x = r.uniform(80, W - 80); y = H + 150 - 1500 * dt + 900 * dt * dt
        paste(c, fp, x, y, 0.9 + 0.3 * math.sin(dt * 9), dt * 400 * (1 if k % 2 else -1))
def pyramid(tl, a):
    bg = np.zeros((H, W, 3), np.float32)
    for y in range(H): bg[y] = np.array([120, 190, 255]) * (1 - y / H) + np.array([200, 220, 255]) * (y / H)
    c = P(bg.astype(np.uint8)); d = ImageDraw.Draw(c)
    d.polygon([(W * 0.42, 260), (W * 0.58, 260), (W + 120, H), (-120, H)], fill=(150, 150, 160))
    for k in range(30):
        yy = 260 + (k / 30) ** 1.6 * (H - 260); d.line([(W / 2 - (40 + (yy - 260) * 0.5), yy), (W / 2 + (40 + (yy - 260) * 0.5), yy)], fill=(120, 120, 130), width=2)
    src = N2(a + tl)
    tile_src = src[380:1180, 200:520]
    rows = 5
    for row in range(rows):
        n = row + 1; sc = 0.28 + row * 0.12; ty = 360 + row * 190 + 60 * sc
        for j in range(n):
            tw, th = int(320 * sc), int(800 * sc)
            ti = cv2.resize(N2(a + tl + 0.1 * (row + j)) [380:1180, 200:520], (tw, th))
            im = Image.fromarray(ti).convert('RGBA')
            m_ = Image.new('L', (tw, th), 0); ImageDraw.Draw(m_).rounded_rectangle([0, 0, tw - 1, th - 1], int(20 * sc), fill=255); im.putalpha(m_)
            x = W / 2 + (j - (n - 1) / 2) * (tw + 10)
            paste(c, im, x, ty, 1.0 + 0.06 * math.sin(tl * 8 + j), 0)
        for j in range(n + 1):
            x = W / 2 + (j - n / 2) * (int(320 * sc) + 10)
            paste(c, CAN, x, ty - 30 * sc, 0.5 * sc + 0.15, math.sin(tl * 6 + j) * 10)
    return c

def apply_fx(img, fx, tl, t, rng):
    if fx == 'fry': return _fry(img, 0.8)
    if fx == 'glitch':
        img = rgbsplit(img, 18); return glitch_slices(img, rng, 10, 120) if rng.random() < 0.6 else img
    if fx == 'sat': return hue_rgb(img, tl * 300, 1.8)
    if fx == 'mirror': o = img.copy(); o[:, W // 2:] = img[:, :W // 2][:, ::-1]; return hue_rgb(o, tl * 90, 1.4)
    if fx == 'zoomin': return zoomc(img, 1.0 + 1.2 * tl, W / 2, 560)
    return img

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; i, tl = chunk_at(t); ch = CH[i]; k = ch['k']
    rng = random.Random(fi * 97); c = None
    if k == 'm':
        img = M(ch['a'] + tl); img = zoomc(img, 1.0 + 0.04 * math.exp(-tl / 0.08))
        c = P(img)
    elif k == 'collage':
        n_list = ch['n']; step = ch['d'] / len(n_list); j = min(len(n_list) - 1, int(tl / step))
        img = N2(ch['st'] + (tl if 'stutter' not in ch else 0))
        img = grid_bw(img, n_list[j], rng)
        img = zoomc(img, 1.0 + 0.1 * math.exp(-(tl - j * step) / 0.06))
        c = P(img)
    elif k == 'clip':
        sp = ch.get('sp', 1.0); st = ch['a'] + tl * sp
        if 'freeze' in ch and ch['freeze'][0] <= tl: st = ch['a'] + ch['freeze'][0] * sp
        img = SRC[ch['src']](st)
        z = 1.04 + beat_punch(tl, 0.06)
        for h in ch.get('zoomhits', []):
            if tl >= h: z = 1.04 + 0.18 * (ch['zoomhits'].index(h) + 1) * (0.6 + 0.4 * math.exp(-(tl - h) / 0.08))
        if 'freeze' in ch and ch['freeze'][0] <= tl: z = 1.3 + 0.6 * (tl - ch['freeze'][0])
        img = zoomc(img, z, W / 2, H * 0.42)
        fx = ch.get('fx')
        if fx == 'psy': c = psy(img, t, ('n2', int(st * 30)))
        else: c = P(apply_fx(img, fx, tl, t, rng))
        if 'top' in ch: top_bar(c, ch['top'])
        if 'food' in ch: flying_food(c, tl, ch['food'][0], ch['food'][1], i)
        if 'rain' in ch: R.rain(c, tl, 0.6, ch['d'], [EMJ[x] for x in ch['rain']], 24, i, (70, 130), (-1800, -1100))
        for ct, txt, sty in ch.get('caps', []):
            if tl >= ct: meme_cap(c, txt, tl, ct, sty, 1040 if sty != 3 else 160, rng)
        for b in ch.get('boom', []):
            if 0 <= tl - b < 0.06: flash(c, 0.5)
    elif k == 'nobody':
        if tl < 1.16:
            img = E(0.2 + tl)
        else:
            img = N2(32.0 + (tl - 1.16))
            img = zoomc(img, 1.15 + 0.4 * (tl - 1.16), W / 2, 520)
        c = P(zoomc(img, 1.0, W / 2, H / 2, 0, 110))
        top_bar(c, 'Никто:\nЭнергичный в 07:40:', 210)
        if tl > 1.16 and tl - 1.16 < 0.06: flash(c, 0.6)
    elif k == 'pyramid':
        c = pyramid(tl, ch['a'])
        meme_cap(c, 'ПОДПИШИСЬ', tl, 2.4, 1, 1150, rng)
    elif k == 'strobe':
        blk = int(tl * 30 / 5)
        faces = [SELFIE, N2(33.0), N2(1.0), C2(40.0), N1(13.3), E(0.9), HOME, N2(39.2), C2(242.0), N1(2.4)]
        if blk % 2 == 0:
            img = M(ch['a'] + tl)
        else:
            img = faces[(blk // 2) % len(faces)].copy()
            img = hue_rgb(img, 0, 1.3)
        img = zoomc(img, 1.05 + 0.15 * math.exp(-((tl * 30) % 5) / 2.0))
        c = P(img)
    elif k == 'end':
        img = E(0.2 + min(1.16, tl * 1.0)); img = hue_rgb(img, tl * 500, 2.0); c = P(zoomc(img, 1.1 + 0.4 * tl))
        if tl > 0.3: paste(c, text_img('ЭНЕРГОСИК\nВ РОТИК', 130, NEON, BLACK, 13, spacing=-10), W / 2, 640, ease_pop(tl, 0.3, 0.08), -5)
        if tl > 1.35: c = P(np.zeros((H, W, 3), np.uint8))
    if tl < 0.04 and i > 0: c = P(rgbsplit(np.array(c.convert('RGB')), 22))
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(13)
    LW = R3.load_wav
    AU = {'m': LW(os.path.join(HERE, 'au_n3.wav')), 'n2': LW(os.path.join(HERE, 'au_n2.wav')), 'n1': LW(os.path.join(HERE, 'au_n1.wav')),
          'c': LW(os.path.join(SP, 'v4', 'au_c.wav')), 'c2': LW(os.path.join(SP, 'v5', 'au_c2.wav')), 'e': LW(os.path.join(SP, 'v4', 'au_e.wav'))}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(src, s0, d, sp=1.0, fade=0.006):
        a = AU[src]; m_ = int(d * SR); pos = s0 * SR + np.arange(m_) * sp
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def norm(x, target=0.25):
        r = np.sqrt((x ** 2).mean()) + 1e-6; return x * min(4.0, target / r)
    def tt(d): return np.arange(int(d * SR)) / SR
    def vine():
        t = tt(1.2); f = 110 * np.exp(-t * 1.2) + 40
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) + 0.5 * np.sin(4 * np.pi * np.cumsum(f) / SR)
        x = np.tanh(2.5 * x * np.exp(-t * 2.2)); y = x.copy()
        for dl, g in ((0.07, .4), (0.15, .25)): k_ = int(dl * SR); y[k_:] += g * x[:-k_]
        return y.astype(np.float32)
    def whoosh(d=0.25):
        t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2; return (np.convolve(x, np.ones(8) / 8, 'same') * 0.5).astype(np.float32)
    def horn(d=0.7):
        t = tt(d); x = sum(((2 * np.pi * np.cumsum(np.full(len(t), 466 * m_)) / SR) % (2 * np.pi)) / np.pi - 1 for m_ in (1, 1.26, 1.5))
        env = np.minimum(1, t / 0.02) * np.clip((d - t) / 0.08, 0, 1); return np.tanh(1.4 * x * env * 0.3).astype(np.float32)
    def scratch():
        t = tt(0.3); f = 400 + 1800 * np.abs(np.sin(2 * np.pi * 5 * t))
        return (0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * rng.standard_normal(len(t)) * 0.6 * np.exp(-t * 4)).astype(np.float32)
    def beat(d, seed=1, lvl=1.0):
        r = np.random.default_rng(seed); out = np.zeros(int(d * SR) + SR, np.float32); s16 = BT / 4
        def put(ts, sig, g): i_ = int(ts * SR); j_ = min(len(out), i_ + len(sig)); out[i_:j_] += g * sig[:j_ - i_]
        t = tt(0.45); kick = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(160 * np.exp(-t * 18) + 45) / SR) * np.exp(-t * 4)).astype(np.float32)
        t = tt(0.2); snare = (0.6 * r.standard_normal(len(t)) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)).astype(np.float32)
        t = tt(0.04); hat = (np.diff(np.concatenate([[0], r.standard_normal(len(t))])) * np.exp(-t * 90) * 0.5).astype(np.float32)
        def bell(semi):
            t = tt(0.18); q = 2 ** (semi / 12); x = np.sign(np.sin(2 * np.pi * 540 * q * t)) + np.sign(np.sin(2 * np.pi * 800 * q * t))
            return (0.18 * np.convolve(x, np.ones(4) / 4, 'same') * np.exp(-t * 15)).astype(np.float32)
        mel = [0, 0, 3, 0, 7, 5, 3, 0, 0, 0, 3, 5, 7, 10, 7, 5]; s = 0
        while s * s16 < d:
            ts = s * s16; st = s % 16
            if st in (0, 6, 10): put(ts, kick, 0.9)
            if st in (4, 12): put(ts, snare, 0.5)
            if st % 2 == 0: put(ts, hat, 0.35); put(ts, bell(mel[(st // 2) + (8 if (s // 16) % 2 else 0)]), 0.6)
            s += 1
        return out[:int(d * SR)] * lvl
    for i, ch in enumerate(CH):
        s0 = STARTS[i]; d = ch['d']; k = ch['k']
        add(s0, whoosh(0.18), 0.35)
        if k == 'm':
            add(s0, norm(clip('m', ch['a'], d), 0.2), 1.0)
        else:
            add(s0, beat(d, seed=i), 0.38)
            if k == 'clip':
                sp = ch.get('sp', 1.0); src = ch['src']
                if 'freeze' in ch:
                    add(s0, norm(clip(src, ch['a'], ch['freeze'][1] * sp, sp), 0.22), 1.1)
                elif sp > 2: add(s0, norm(clip(src, ch['a'], d, sp), 0.12), 1)
                else: add(s0, norm(clip(src, ch['a'], d, sp), 0.22), 1.1)
                for b in ch.get('boom', []): add(s0 + b, vine(), 0.45)
                if ch.get('fx') == 'psy': add(s0, norm(clip('e', 0.2, d, 0.58), 0.15), 0.6)
            elif k == 'collage':
                if 'stutter' in ch:
                    a0, a1 = ch['stutter']; seg = clip('n2', a0, a1 - a0) if False else clip('n2', 0.95, 0.45)
                    step = d / len(ch['n'])
                    for j in range(len(ch['n'])): add(s0 + j * step, norm(seg, 0.22), 1.0); add(s0 + j * step, vine()[:6000], 0.3)
                else:
                    add(s0, norm(clip('n2', ch['st'], d), 0.22), 1.0)
            elif k == 'nobody':
                add(s0, norm(clip('e', 0.2, 1.16), 0.22), 1.2); add(s0 + 1.16, norm(clip('n2', 32.0, d - 1.16), 0.22), 1.1); add(s0 + 1.16, vine(), 0.5)
            elif k == 'pyramid':
                add(s0, norm(clip('n2', ch['a'], d), 0.22), 1.1); add(s0, horn(0.8), 0.4)
            elif k == 'strobe':
                mix_m = norm(clip('m', ch['a'], d), 0.2); add(s0, mix_m, 1.0)
                for b in range(int(d * 30 / 5)):
                    if b % 2: add(s0 + b * 5 / 30, scratch()[:int(5 / 30 * SR)], 0.25)
            elif k == 'end':
                add(s0, norm(clip('e', 0.2, 1.3), 0.25), 1.3); add(s0 + 0.3, vine(), 0.6)
        if i == 0: add(0, horn(0.6), 0.4)
    mix = mix[:int(T_END * SR)]; f = int(0.2 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.05) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        tm = te = 0
        for i, ch in enumerate(CH):
            print(f"{i:2d} {ch['k']:8s} {STARTS[i]:6.2f} {ch['d']:.2f}")
            if ch['k'] == 'm': tm += ch['d']
            elif ch['k'] == 'strobe': tm += ch['d'] / 2; te += ch['d'] / 2
            else: te += ch['d']
        print('total', round(T_END, 2), 'memes', round(tm, 1), 'energ', round(te, 1)); sys.exit()
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:06.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--audio':
        build_audio(sys.argv[2]); sys.exit()
    out = sys.argv[1]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(N):
        p.stdin.write(render(fi).tobytes())
        if fi % 300 == 0: print(fi, flush=True)
    p.stdin.close(); p.wait()
