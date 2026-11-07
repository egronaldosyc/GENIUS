import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, 'v2'), os.path.join(SP, 'v10'), os.path.join(SP, 'v11')): sys.path.insert(0, p)
import render as R
import render2 as R2
import render10 as T
import render11 as U
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, WHITE, BLACK
from render2 import hue_rgb
from render10 import P, flash, CREAM, F_SER, rain, sad

FPS, SR = 30, 44100
U.DIRS['c1'] = (os.path.join(HERE, 'kc1'), 292); U.AUF['c1'] = os.path.join(HERE, 'au.wav')
for k, (d, n) in list(U.DIRS.items()): pass
U.DIRS['a5'] = (os.path.join(SP, 'v10', 'k5'), 1342); U.AUF['a5'] = os.path.join(SP, 'v10', 'au5.wav')
U.DIRS['a2'] = (os.path.join(SP, 'v10', 'k2'), 1337); U.AUF['a2'] = os.path.join(SP, 'v10', 'au2.wav')
kr, kf = U.kr, U.kf
GOLD = (255, 215, 120); BLUE = (120, 170, 255)
def bw(img): g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY); return cv2.cvtColor(g, cv2.COLOR_GRAY2RGB)
def sepia(img):
    x = bw(img).astype(np.float32); x = x * np.array([1.07, 0.9, 0.7]) + np.array([20, 10, 0]); return np.clip(x, 0, 255).astype(np.uint8)
def blue(img): return T.sad(img)
def red(img): x = img.astype(np.float32); g = x.mean(2, keepdims=True); x = g + (x - g) * 0.6; x *= np.array([1.35, 0.7, 0.7]); return np.clip(x, 0, 255).astype(np.uint8)

# ---------------- shots ----------------
SH = []
def s(k, d, **kw): SH.append((k, d, kw))
s('pro1', 3.2, v='a3', a=0.5)
s('pro2', 3.0, v='a1', a=4.4)
s('pro3', 2.6, v='a1', a=24.8)
s('fate', 1.6)
s('spill', 3.6, v='c1', a=2.0, sp=0.5)
s('noo', 4.4, v='c1', a=0.0, sp=0.42)
s('csi', 6.5, v='c1', a=5.6, sp=0.35)
s('time', 2.2, v='b4', a=25.5)
s('stages', 1.8)
s('stage', 3.0, n=1, name='ОТРИЦАНИЕ', v='b1', a=0.0, fx='bw', sub='«это не она… это вода»')
s('stage', 3.0, n=2, name='ГНЕВ', v='b1', a=10.0, fx='red', sub='«КТО ПОСТАВИЛ ЕЁ ТАК БЛИЗКО К КРАЮ?!»')
s('stage', 3.2, n=3, name='ТОРГ', v='b2', a=0.5, fx='sep', sub='«верни её, и я больше никогда…»')
s('stage', 3.4, n=4, name='ДЕПРЕССИЯ', v='a4', a=0.0, fx='blue', sub='«250 мл… просто ушли в стол»')
s('stage', 3.4, n=5, name='ПРИНЯТИЕ', v='b3', a=0.0, fx='none', sub='«теперь только вода»')
s('funeral', 5.5)
s('mourners', 4.0)
s('eulogy', 4.0, v='b2', a=4.5)
s('choco', 3.8, v='c1', a=4.6)
s('end', 4.0)
STARTS = []; _t = 0
for x in SH: STARTS.append(_t); _t += x[1]
T_END = _t; N = int(round(T_END * FPS))
def at(t):
    for i, x in enumerate(SH):
        if t < STARTS[i] + x[1]: return i, t - STARTS[i]
    return len(SH) - 1, SH[-1][1] - 1e-3

# ---------------- helpers ----------------
def vignette_bg(col=(20, 14, 10)):
    a = np.full((H, W, 3), col, np.float32); a *= (0.4 + 0.6 * T_vig())
    return P(np.clip(a, 0, 255).astype(np.uint8))
_v = None
def T_vig():
    global _v
    if _v is None:
        yy, xx = np.mgrid[0:H, 0:W].astype(np.float32); _v = np.clip(1.2 - np.sqrt(((xx - W / 2) / (W * 0.6)) ** 2 + ((yy - H / 2) / (H * 0.55)) ** 2), 0, 1)[..., None]
    return _v
def film(c, t, amt=1.0):
    a = np.array(c.convert('RGB')).astype(np.float32)
    r = np.random.default_rng(int(t * 30))
    a += r.normal(0, 10 * amt, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    for _ in range(2):
        x = r.integers(0, W); a[:, x:x + 2] *= 0.75
    return P(np.clip(a, 0, 255).astype(np.uint8))
def title(c, txt, y, size, tl, t0, col=WHITE, f=F_SER, stroke=(0, 0, 0), sw=None, fade=0.5):
    a = min(1, max(0, (tl - t0) / fade))
    if a <= 0: return
    paste(c, text_img(txt, size, col, stroke, sw if sw is not None else max(2, size // 20), f=f, spacing=-4), W / 2, y - 8 * (1 - a), 1.0, 0, a)
def slam(c, txt, size, y, tl, t0, col=WHITE, stroke=BLACK, rot=-3):
    s_ = ease_pop(tl, t0, 0.1)
    if s_ <= 0: return
    paste(c, text_img(txt, size, col, stroke, max(6, size // 10), spacing=-8), W / 2, y, s_ * (1 + 0.3 * math.exp(-(tl - t0) / 0.07)), rot)
def candle(c, x, y, t, s=1.0):
    d = ImageDraw.Draw(c)
    d.rectangle([x - 18 * s, y, x + 18 * s, y + 120 * s], fill=(240, 230, 210))
    fl = 1 + 0.15 * math.sin(t * 17) + 0.1 * math.sin(t * 29)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.ellipse([x - 60 * s, y - 120 * s, x + 60 * s, y + 10 * s], fill=(255, 180, 60, 70))
    lay = lay.filter(ImageFilter.GaussianBlur(20)); c.alpha_composite(lay)
    d.ellipse([x - 12 * s, y - 50 * s * fl, x + 12 * s, y - 2], fill=(255, 210, 90)); d.ellipse([x - 6 * s, y - 30 * s * fl, x + 6 * s, y - 4], fill=(255, 255, 220))
def tape(c, y, rot, txt='НЕ ПЕРЕСЕКАТЬ · МЕСТО ТРАГЕДИИ · '):
    band = Image.new('RGBA', (W + 400, 70), (255, 210, 0, 255)); d = ImageDraw.Draw(band)
    x = 0
    while x < band.width:
        d.text((x, 35), txt, font=font(F_BLACK, 30), fill=BLACK, anchor='lm'); x += d.textlength(txt, font=font(F_BLACK, 30))
    paste(c, band, W / 2, y, 1.0, rot)

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; i, tl = at(t); k, dur, kw = SH[i]; rng = random.Random(fi * 31); c = None
    if k in ('pro1', 'pro2', 'pro3'):
        c = vignette_bg((40, 28, 16))
        img = kr(kw['v'], kw['a'] + tl * 0.8, 560, GOLD, 8, sepia); paste(c, img, W / 2, 640, 1.0 + 0.02 * tl)
        if k == 'pro1':
            title(c, 'Это была обычная чекушка.', 230, 54, tl, 0.2)
            title(c, 'ЧЕКУШКА', 1050, 110, tl, 1.2, GOLD, F_BLACK, (60, 30, 0), 6)
            title(c, '0,25 л · 40°', 1150, 40, tl, 1.6, CREAM, F_MONO, (0, 0, 0), 0)
        if k == 'pro2':
            title(c, 'Она была рядом', 230, 58, tl, 0.1); title(c, 'все 9 рюмок.', 300, 58, tl, 0.5)
            title(c, '250 мл надежды', 1080, 64, tl, 1.0, GOLD)
        if k == 'pro3':
            title(c, 'Они были счастливы.', 230, 58, tl, 0.1)
            title(c, 'Он даже не догадывался…', 1090, 52, tl, 1.0, CREAM)
        c = film(c, t)
    elif k == 'fate':
        c = P(np.zeros((H, W, 3), np.uint8))
        title(c, 'НО СУДЬБА', H / 2 - 60, 90, tl, 0.0, WHITE, F_BLACK, (120, 0, 0), 6, 0.2)
        title(c, 'РАСПОРЯДИЛАСЬ ИНАЧЕ', H / 2 + 50, 56, tl, 0.4, (230, 60, 60), F_BLACK, (0, 0, 0), 4, 0.2)
        if 0.9 < tl < 1.0: flash(c, 0.8)
    elif k == 'spill':
        c = vignette_bg((10, 10, 18))
        img = kr('c1', kw['a'] + tl * kw['sp'], 640, (200, 200, 220), 8, blue); paste(c, img, W / 2, 640, 1.0 + 0.08 * tl / dur)
        rain(c, t, 120, 120)
        if rng.random() < 0.06: flash(c, 0.6, (200, 210, 255))
        title(c, 'ОНА РАЗЛИЛАСЬ.', 1100, 80, tl, 0.8, WHITE, F_BLACK, (0, 0, 40), 6)
        slam(c, '22:51', 70, 220, tl, 0.2, (200, 210, 255), BLACK, 0)
    elif k == 'noo':
        c = vignette_bg((30, 5, 5))
        z = 1.0 + 0.35 * tl / dur
        img = kr('c1', kw['a'] + tl * kw['sp'], 640, (220, 40, 40), 10, lambda im: hue_rgb(im, 0, 1.2)); paste(c, img, W / 2 + rng.uniform(-6, 6), 640, z, 4 * math.sin(tl * 3))
        letters = 'НЕЕЕЕЕЕЕТ!'
        n = min(len(letters), int(tl / dur * len(letters) * 1.3) + 1)
        paste(c, text_img(letters[:n], 120, WHITE, (140, 0, 0), 10), W / 2 + rng.uniform(-8, 8), 1120, 1.0 + 0.05 * math.sin(tl * 20), rng.uniform(-3, 3))
        if tl < 0.1: flash(c, 1.0)
        rain(c, t, 80, 90)
    elif k == 'csi':
        c = vignette_bg((10, 16, 24))
        img = kr('c1', kw['a'] + tl * kw['sp'], 640, (255, 210, 0), 8, None); paste(c, img, W / 2, 640)
        d = ImageDraw.Draw(c)
        # chalk outline of a bottle over the puddle
        if tl > 0.8:
            u = min(1, (tl - 0.8) / 1.0); cx, cy = W / 2 + 10, 700
            pts = [(cx - 40, cy - 170), (cx + 40, cy - 170), (cx + 40, cy - 110), (cx + 85, cy - 60), (cx + 85, cy + 180), (cx - 85, cy + 180), (cx - 85, cy - 60), (cx - 40, cy - 110), (cx - 40, cy - 170)]
            seg = int(u * (len(pts) - 1)); d.line(pts[:seg + 1], fill=(255, 255, 255), width=7)
        tape(c, 300, -6); tape(c, 1010, 5)
        if tl > 1.8:
            box = Image.new('RGBA', (W - 60, 200), (0, 0, 0, 210)); bd = ImageDraw.Draw(box)
            for j, (a_, b_) in enumerate([('ЖЕРТВА:', 'чекушка, 0,25 л'), ('ПРИЧИНА:', 'рука дрогнула'), ('СВИДЕТЕЛЬ:', 'пачка сигарет')]):
                if tl > 1.8 + j * 0.5:
                    bd.text((20, 22 + j * 58), a_, font=font(F_MONO, 30), fill=(255, 210, 0)); bd.text((250, 22 + j * 58), b_, font=font(F_MONO, 30), fill=WHITE)
            c.alpha_composite(box, (30, 1060))
        if tl > 3.6:
            d.ellipse([W / 2 - 260, 360, W / 2 - 60, 520], outline=(255, 60, 60), width=6)
            d.text((W / 2 - 160, 345), 'СВИДЕТЕЛЬ', font=font(F_MONO, 24), fill=(255, 80, 80), anchor='ms', stroke_width=2, stroke_fill=BLACK)
        if int(tl * 8) % 7 == 0: flash(c, 0.15, (255, 255, 255))
        d.text((30, 170), 'МЕСТО ТРАГЕДИИ · ДЕЛО №848', font=font(F_MONO, 28), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
    elif k == 'time':
        c = vignette_bg((5, 20, 10))
        img = kr('b4', kw['a'] + tl * 0.5, 560, (80, 255, 120), 8, None); paste(c, img, W / 2, 620)
        title(c, 'время смерти: 22:51', 1060, 60, tl, 0.3, (120, 255, 150), F_SER)
    elif k == 'stages':
        c = P(np.zeros((H, W, 3), np.uint8))
        title(c, 'ПЯТЬ СТАДИЙ', H / 2 - 50, 100, tl, 0.0, WHITE, F_BLACK, (0, 0, 0), 0, 0.2)
        title(c, 'ПРИНЯТИЯ', H / 2 + 60, 80, tl, 0.3, (200, 200, 200), F_BLACK, (0, 0, 0), 0, 0.2)
    elif k == 'stage':
        fx = {'bw': bw, 'red': red, 'sep': sepia, 'blue': blue, 'none': None}[kw['fx']]
        bgcol = {'bw': (25, 25, 25), 'red': (60, 0, 0), 'sep': (40, 28, 16), 'blue': (10, 14, 30), 'none': (30, 40, 60)}[kw['fx']]
        c = vignette_bg(bgcol)
        shake = 10 if kw['fx'] == 'red' else 0
        img = kr(kw['v'], kw['a'] + tl, 600, CREAM, 8, fx); paste(c, img, W / 2 + rng.uniform(-shake, shake), 660, 1.0 + 0.02 * tl)
        paste(c, text_img(f'СТАДИЯ {kw["n"]}', 40, (200, 200, 200), BLACK, 3, f=F_MONO), W / 2, 200, ease_pop(tl, 0.0, 0.12))
        slam(c, kw['name'], 100 if len(kw['name']) < 9 else 84, 290, tl, 0.05, WHITE, BLACK, -2)
        if tl > 0.7: title(c, kw['sub'], 1090, 44 if len(kw['sub']) < 30 else 36, tl, 0.7, CREAM, F_SER)
        if kw['fx'] == 'blue': rain(c, t, 90, 100)
        if kw['fx'] == 'red' and rng.random() < 0.3: c = P(glitch_slices(np.array(c.convert('RGB')), rng, 6, 60))
        if tl < 0.05: flash(c, 0.6)
    elif k == 'funeral':
        c = vignette_bg((14, 14, 14))
        fr = Image.new('RGBA', (440, 520), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
        d.rectangle([0, 0, 439, 519], fill=(120, 90, 40)); d.rectangle([22, 22, 417, 497], fill=(30, 30, 30))
        ph = cv2.resize(bw(kf('c1', 6.2))[40:360, 60:340], (396, 476)); fr.paste(Image.fromarray(ph), (22, 22))
        d.polygon([(439 - 130, 0), (439, 0), (439, 130)], fill=(0, 0, 0)); d.line([(439 - 150, 0), (439, 150)], fill=(0, 0, 0), width=34)
        paste(c, fr, W / 2, 560, ease_pop(tl, 0.0, 0.4))
        candle(c, 150, 900, t); candle(c, W - 150, 900, t + 1)
        title(c, 'ЧЕКУШКА', 210, 90, tl, 0.5, WHITE, F_SER)
        title(c, '2026 — 2026', 920, 46, tl, 1.2, (200, 200, 200), F_SER)
        title(c, 'разлита, но не забыта', 1060, 50, tl, 2.0, WHITE, F_SER)
        title(c, 'покойся с миром', 1150, 40, tl, 3.0, (170, 170, 170), F_SER)
        c = film(c, t, 0.8)
    elif k == 'mourners':
        c = vignette_bg((14, 14, 14))
        title(c, 'Проститься пришли все:', 210, 50, tl, 0.0, WHITE, F_SER)
        people = [('a1', 21.0), ('a3', 35.0), ('a4', 3.0), ('a2', 4.0), ('b1', 1.0), ('b2', 2.0), ('b3', 2.0), ('a5', 36.0), ('b1', 56.0)]
        for j, (v, st) in enumerate(people):
            t0 = 0.3 + j * 0.25
            if tl < t0: continue
            gx, gy = j % 3, j // 3
            g = kr(v, st + tl * 0.5, 180, (90, 90, 90), 5, bw)
            paste(c, g, W / 2 + (gx - 1) * 210, 450 + gy * 220, ease_pop(tl, t0, 0.15))
        title(c, 'даже Егор из всех прошлых кружков', 1160, 36, tl, 2.6, (180, 180, 180), F_SER)
        c = film(c, t, 0.8)
    elif k == 'eulogy':
        c = vignette_bg((14, 14, 14))
        img = kr('b2', kw['a'] + tl, 560, (140, 140, 140), 8, bw); paste(c, img, W / 2, 620)
        candle(c, 110, 980, t, 0.8); candle(c, W - 110, 980, t + 2, 0.8)
        title(c, 'ПРОЩАЛЬНАЯ РЕЧЬ', 230, 60, tl, 0.0, WHITE, F_SER)
        title(c, '«она была лучшей из нас»', 1080, 46, tl, 1.2, CREAM, F_SER)
        c = film(c, t, 0.8)
    elif k == 'choco':
        c = vignette_bg((60, 50, 20))
        img = kf('c1', kw['a'] + tl * 0.2); img = cv2.warpAffine(img, cv2.getRotationMatrix2D((90, 70), 0, 1.0 + 1.2 * min(1, tl / 1.2)), (400, 400), borderMode=cv2.BORDER_REFLECT)
        im = Image.fromarray(img).convert('RGBA'); im.putalpha(Image.fromarray(T.CM)); im = im.resize((620, 620))
        lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
        for q in range(16):
            a = q * math.pi / 8 + tl * 0.4; d.polygon([(W / 2, 640), (W / 2 + 900 * math.cos(a), 640 + 900 * math.sin(a)), (W / 2 + 900 * math.cos(a + 0.12), 640 + 900 * math.sin(a + 0.12))], fill=(255, 240, 160, 70))
        c.alpha_composite(lay.filter(ImageFilter.GaussianBlur(4)))
        ring = Image.new('RGBA', (640, 640), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, 639, 639], fill=(255, 230, 120, 255)); ring.alpha_composite(im, (10, 10))
        paste(c, ring, W / 2, 640)
        d = ImageDraw.Draw(c); d.ellipse([W / 2 - 120, 260, W / 2 + 120, 300], outline=(255, 240, 140), width=8)
        slam(c, 'А СИГАРЕТЫ', 90, 1040, tl, 0.5, (255, 240, 170), (90, 60, 0), -2)
        slam(c, 'ВЫЖИЛИ', 120, 1150, tl, 1.0, WHITE, (90, 60, 0), 3)
        if tl > 2.2: title(c, '(они тоже зло)', 1240, 40, tl, 2.2, (255, 220, 200), F_SER)
    elif k == 'end':
        c = vignette_bg((20, 6, 6))
        img = kr('c1', 0.3 + tl * 0.3, 300, CREAM, 6, bw); paste(c, img, W / 2, 780)
        title(c, 'берегите водку.', 330, 64, tl, 0.0, WHITE, F_SER)
        title(c, 'а лучше — себя.', 420, 64, tl, 0.8, (255, 200, 120), F_SER)
        title(c, 'АЛКОГОЛЬ — ЗЛО · ЧАСТЬ 3', 1080, 44, tl, 1.6, CREAM, F_BLACK, (0, 0, 0), 4)
        d = ImageDraw.Draw(c); d.text((W / 2, H - 40), 'ЧРЕЗМЕРНОЕ УПОТРЕБЛЕНИЕ АЛКОГОЛЯ ВРЕДИТ ВАШЕМУ ЗДОРОВЬЮ', font=font(F_MONO, 16), fill=(180, 180, 180), anchor='mm')
        if dur - tl < 0.35: flash(c, (0.35 - (dur - tl)) / 0.35, (0, 0, 0))
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(12)
    AU = {k: T.load(p) for k, p in U.AUF.items()}
    VO = {k: T.load(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(v, s0, d, sp=1.0, fade=0.03, target=0.12):
        a = AU[v]; m = int(d * SR); pos = s0 * SR + np.arange(m) * sp
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        r = np.sqrt((x ** 2).mean()) + 1e-6; return x * min(5.0, target / r)
    def tt(d): return np.arange(int(d * SR)) / SR
    def reverb(x, g=0.6):
        y = x.copy()
        for dl, gg in ((0.041, .5), (0.067, .42), (0.101, .35), (0.149, .28), (0.211, .22), (0.307, .16), (0.43, .1)):
            k = int(dl * SR); y[k:] += g * gg * x[:-k]
        return y
    def piano(f, d=2.5, g=0.16):
        t = tt(d); x = sum(np.sin(2 * np.pi * f * m * t) * (0.55 ** (m - 1)) * np.exp(-t * (1.0 + m * 0.7)) for m in range(1, 6))
        return (x * np.minimum(1, t / 0.004) * g).astype(np.float32)
    def organ(f, d, g=0.1):
        t = tt(d); x = sum(np.sin(2 * np.pi * f * m * t) * a for m, a in ((1, 1), (2, .5), (3, .3), (4, .2), (0.5, .4)))
        env = np.minimum(1, t / 0.05) * np.clip((d - t) / 0.15, 0, 1); return (x * env * g).astype(np.float32)
    def choir(freqs, d, g=0.06):
        t = tt(d); x = 0
        for f in freqs:
            for det in (-0.4, 0.0, 0.4):
                ph = 2 * np.pi * (f + det) * t + 0.3 * np.sin(2 * np.pi * 5 * t); x = x + (((ph % (2 * np.pi)) / np.pi - 1))
        X = np.fft.rfft(x); fr = np.fft.rfftfreq(len(x), 1 / SR); X *= np.exp(-((fr - 700) / 500) ** 2) + 0.6 * np.exp(-((fr - 1200) / 400) ** 2) + 0.2
        y = np.fft.irfft(X, len(x)); env = np.minimum(1, t / 0.5) * np.clip((d - t) / 0.6, 0, 1)
        y = y / (np.abs(y).max() + 1e-6); return (y * env * g * 4).astype(np.float32)
    def boom(d=1.4, f0=70):
        t = tt(d); f = f0 * np.exp(-t * 3) + 30; return np.tanh(2.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2)).astype(np.float32)
    def thunder(d=2.0):
        x = rng.standard_normal(int(d * SR)); x = np.convolve(x, np.ones(300) / 300, 'same'); t = tt(d)
        return (x * np.exp(-t * 1.5) * 6 * np.minimum(1, t / 0.02)).astype(np.float32)
    def rainnoise(d):
        x = rng.standard_normal(int(d * SR)).astype(np.float32); x = np.diff(np.concatenate([[0], x])) * 0.5
        f = int(0.5 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); return x * 0.07
    def shutter():
        t = tt(0.08); return (rng.standard_normal(len(t)) * np.exp(-t * 80) * 0.35).astype(np.float32)
    def siren(d):
        t = tt(d); f = 700 + 250 * np.sign(np.sin(2 * np.pi * 1.2 * t)); return (0.06 * np.sin(2 * np.pi * np.cumsum(f) / SR)).astype(np.float32)
    def hit(): t = tt(0.25); return (np.tanh(3 * np.sin(2 * np.pi * 60 * t) * np.exp(-t * 15)) * 0.8).astype(np.float32)
    S = {}
    for i, x in enumerate(SH): S.setdefault(x[0], []).append((STARTS[i], x))
    # prologue: tender major piano
    p0 = 0; p1 = S['fate'][0][0]
    prog = [(261.6, [130.8, 196.0, 261.6, 329.6]), (196.0, [98.0, 146.8, 196.0, 246.9]), (220.0, [110.0, 164.8, 220.0, 261.6]), (174.6, [87.3, 130.8, 174.6, 220.0])]
    mel = [659.3, 587.3, 523.3, 587.3, 659.3, 659.3, 659.3, 587.3, 587.3, 659.3, 784.0, 784.0]
    t = 0.0; q = 0
    while t < p1 - 0.3:
        root, ch = prog[(q // 2) % 4]
        if q % 2 == 0:
            for j, f in enumerate(ch): add(t + j * 0.05, piano(f, 2.4, 0.12), 1.0)
        add(t, piano(mel[q % len(mel)], 1.4, 0.16), 1.0); t += 0.7; q += 1
    add(0.2, VO['n1'], 1.0); add(3.4, VO['n2'], 1.0)
    for (st, (k, d, kw)) in S['pro1'] + S['pro2'] + S['pro3']: add(st, clip(kw['v'], kw['a'], d, 0.8, target=0.05), 1.0)
    # fate
    st = S['fate'][0][0]; add(st, boom(1.6, 55), 1.0); add(st + 0.05, VO['n3'], 1.0); add(st + 0.9, thunder(1.5), 0.6)
    # spill + noo
    st, (k, d, kw) = S['spill'][0]; add(st, rainnoise(T_END - st - 4), 1.0); add(st, choir([233.1, 277.2, 349.2], d + S['noo'][0][1][1], 0.06), 1.0)
    add(st, reverb(clip('c1', kw['a'], d, kw['sp'], target=0.08)), 1.0); add(st + 0.1, thunder(2.0), 0.7)
    st, (k, d, kw) = S['noo'][0]; add(st, reverb(clip('c1', kw['a'], d, kw['sp'], target=0.2), 0.7), 1.3); add(st, boom(1.6, 80), 0.9)
    # csi
    st, (k, d, kw) = S['csi'][0]; add(st, siren(d), 1.0)
    for j in range(7): add(st + 0.4 + j * 0.85, shutter(), 1.0)
    t_ = tt(d); add(st, (np.sin(2 * np.pi * 55 * t_) * 0.08 + np.sin(2 * np.pi * 58 * t_) * 0.06).astype(np.float32), 1.0)
    for j in range(3): add(st + 1.8 + j * 0.5, hit()[:4000], 0.5)
    st, (k, d, kw) = S['time'][0]; add(st, clip('b4', kw['a'], d, 0.5, target=0.08), 1.0); add(st, piano(98.0, 2.2, 0.2), 1.0)
    # stages
    st = S['stages'][0][0]; add(st, VO['n4'], 1.0); add(st, boom(1.2, 60), 0.6)
    stage_notes = [(233.1, [116.5, 138.6, 174.6]), (220.0, [110.0, 130.8, 164.8]), (207.7, [103.8, 123.5, 155.6]), (196.0, [98.0, 116.5, 146.8]), (261.6, [130.8, 164.8, 196.0])]
    for (st, (k, d, kw)) in S['stage']:
        n_ = kw['n']; add(st, hit(), 0.9)
        root, ch = stage_notes[n_ - 1]
        for f in ch: add(st, organ(f, d, 0.06 if n_ < 5 else 0.05), 1.0)
        x = clip(kw['v'], kw['a'], d, 1.0, target=0.1)
        if n_ == 2: x = np.tanh(x * 4) * 0.2
        add(st, reverb(x, 0.4), 0.9)
    # funeral march (Chopin, public domain): Bb minor
    f0 = S['funeral'][0][0]; f1 = S['choco'][0][0]
    beat = 0.62
    melody = [(233.1, 1), (233.1, 0.75), (233.1, 0.25), (233.1, 2), (277.2, 1), (261.6, 0.75), (261.6, 0.25), (233.1, 0.75), (233.1, 0.25), (220.0, 0.75), (233.1, 2.25)]
    bass = [(58.27, [116.5, 138.6, 174.6]), (46.25, [92.5, 116.5, 138.6])]
    t = f0; mi = 0; bi = 0
    while t < f1 - 0.3:
        f, dur_b = melody[mi % len(melody)]; d_ = dur_b * beat
        add(t, organ(f, d_ * 0.95, 0.09), 1.0)
        mi += 1; t += d_
    t = f0; bi = 0
    while t < f1 - 0.3:
        root, ch = bass[(bi // 2) % 2]
        add(t, organ(root, beat * 0.9, 0.12), 1.0)
        for f in ch: add(t + beat, organ(f, beat * 0.8, 0.04), 1.0)
        t += 2 * beat; bi += 1
    add(f0 + 3.0, VO['n5'], 0.9)
    st, (k, d, kw) = S['eulogy'][0]; add(st, reverb(clip('b2', kw['a'], d, 1.0, target=0.1), 0.6), 0.9)
    # chocolate: angelic choir major
    st, (k, d, kw) = S['choco'][0]; add(st, choir([523.3, 659.3, 784.0, 1046.5], d, 0.08), 1.0); add(st + 0.5, VO['n6'], 1.0)
    t_ = tt(1.0); add(st + 1.0, (np.sin(2 * np.pi * 1568 * t_) * np.exp(-t_ * 3) * 0.15).astype(np.float32), 1.0)
    st, (k, d, kw) = S['end'][0]
    for j, f in enumerate([233.1, 277.2, 349.2]): add(st + j * 0.05, piano(f, 3.5, 0.14), 1.0)
    add(st, piano(116.5, 3.5, 0.2), 1.0)
    mix = mix[:int(T_END * SR)]; f = int(0.4 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.2) * 0.93
    stt = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(stt.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for i, x in enumerate(SH): print(f'{i:2d} {x[0]:9s} {STARTS[i]:6.2f} {x[1]}')
        print('total', T_END); sys.exit()
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
