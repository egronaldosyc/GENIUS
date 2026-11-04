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
from render2 import hue_rgb

FPS, SR = 30, 44100
GOLD = (255, 200, 40); RED = (235, 30, 40); BLUE = (40, 120, 255)
BPM = 150; BT = 60 / BPM

# ---------------- frames ----------------
_cache = {}
CL = cv2.createCLAHE(2.2, (8, 8))
def enhance(im):
    lab = cv2.cvtColor(im, cv2.COLOR_RGB2LAB); lab[..., 0] = CL.apply(lab[..., 0])
    im = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB).astype(np.float32)
    im = np.clip((im / 255.0) ** 0.8 * 255 * 1.08, 0, 255)
    g = im.mean(2, keepdims=True); im = np.clip(g + (im - g) * 1.35, 0, 255)
    return im.astype(np.uint8)
def blurfill(im):
    bg = cv2.resize(im, (W, H)); bg = cv2.GaussianBlur(bg, (0, 0), 25); bg = (bg * 0.55).astype(np.uint8)
    h = int(im.shape[0] * W / im.shape[1]) ; fg = cv2.resize(im, (W, h))
    fg = cv2.resize(fg, (int(W * 1.35), int(h * 1.35))); x0 = (fg.shape[1] - W) // 2
    fg = fg[:, x0:x0 + W]; y0 = (H - fg.shape[0]) // 2
    bg[y0:y0 + fg.shape[0]] = fg
    return bg
OFF = {'1': ('f1_0', 0, 889), '2': ('f2_0', 0, 266), '3': ('f3_120', 120, 1199), '4': ('f4_56', 56, 765), '5a': ('f5_22', 22, 781),
       '5b': ('f5_76', 76, 300), '5c': ('f5_166', 166, 441)}
def F(src, t):
    d, o, mx = OFF[src]
    i = int(np.clip(round((t - o) * 30), 0, mx)); k = (src, i)
    if k not in _cache:
        if len(_cache) > 300: _cache.pop(next(iter(_cache)))
        im = cv2.cvtColor(cv2.imread(os.path.join(HERE, d, f'{i+1:04d}.jpg')), cv2.COLOR_BGR2RGB)
        if src in ('2', '4'): im = blurfill(im)
        _cache[k] = enhance(im)
    return _cache[k]
def E(t): return R3.eframe(t)
def C2(t): return R4.c2(t)
def C(t): return R3.cframe(t)

# ---------------- timeline: list of shots ----------------
# shot: (key, dur, params)
SHOTS = []
def sh(key, dur, **kw): SHOTS.append((key, dur, kw))
sh('sponsor', 2.4)
sh('title', 3.2)
for name, src, t0, tf, stats, col in [
        ('РЫЖИЙ ТАЙФУН', '1', 0.4, 1.2, ['Приём: вертушка', 'Слабость: фонари'], RED),
        ('ПРИЗРАК В СВИТЕРЕ', '1', 12.9, 13.8, ['Приём: стоять красиво', 'Слабость: нет'], BLUE),
        ('ГОЛЫЙ ЭНТУЗИАЗМ', '5b', 79.6, 80.4, ['Приём: снять футболку', 'Холод: не чувствует'], GOLD),
        ('БЕЖЕВЫЙ ГРОМ', '3', 128.4, 129.0, ['Приём: лечь и думать', 'Сила: тайна'], (180, 255, 120))]:
    sh('intro', 2.5, name=name, src=src, t0=t0, tf=tf, stats=stats, col=col)
sh('comm', 3.65)
sh('round', 0.9, txt='РАУНД 1', vo='r1')
sh('play', 4.0, src='1', a=6.6, b=10.6, sp=1.0, fight=('РЫЖИЙ ТАЙФУН', 'ВОЗДУХ'), hits=[8.3, 8.9], cap=[(7.4, 'ВЕРТУШКА!!!')])
sh('replay', 3.4, src='1', a=7.3, b=8.9, sp=0.47, cap='ПОВТОР')
sh('round', 0.9, txt='РАУНД 2', vo='r2')
sh('play', 4.6, src='5a', a=24.5, b=31.4, sp=1.5, fight=('ГОЛЫЙ ЭНТУЗИАЗМ', 'ЧЕЛ В ШОРТАХ'), hits=[28.6, 30.2], cap=[(26.0, 'РАЗГОН...')])
sh('slowmo', 4.0, src='5a', a=31.4, b=32.8, sp=0.35, fight=('ГОЛЫЙ ЭНТУЗИАЗМ', 'ЧЕЛ В ШОРТАХ'), hits=[31.95], cap='БРОСОК ЧЕРЕЗ ВСЁ')
sh('play', 3.75, src='5a', a=36.0, b=42.0, sp=1.6, fight=('ГОЛЫЙ ЭНТУЗИАЗМ', 'ЧЕЛ В ШОРТАХ'), hits=[37.5, 40.0], cap=[(36.2, 'ПРИЁМ: ОБНИМАШКИ'), (39.5, 'ТЕХНИКА: «ПЛЕД»')])
sh('tired', 3.4, src='3', a=140.0, b=147.0, sp=2.06)
sh('need', 2.8)
sh('can', 1.6)
sh('rise', 3.0, src='3', a=147.0, b=139.0, sp=-2.67)
sh('play', 5.0, src='4', a=61.0, b=71.0, sp=2.0, fight=('РЫЖИЙ ТАЙФУН', 'СИДЯЧИЙ'), hits=[62.5, 64.5, 66.0, 67.6, 69.0, 70.3], cap=[(61.0, 'ПАРТЕР'), (65.5, 'КОМБО')], combo=True)
sh('cool', 3.6, src='2', a=2.9, b=6.5)
sh('round', 0.9, txt='ФИНАЛ', vo='rf')
sh('play', 3.0, src='5c', a=168.5, b=171.5, sp=1.0, fight=('ГОЛЫЙ ЭНТУЗИАЗМ', 'ПРИЗРАК В СВИТЕРЕ'), hits=[], cap=[(168.6, 'ДОБИВАЙ!')])
sh('slowmo', 3.6, src='5c', a=171.5, b=172.95, sp=0.4, fight=('ГОЛЫЙ ЭНТУЗИАЗМ', 'ПРИЗРАК В СВИТЕРЕ'), hits=[172.4], cap='')
sh('ko', 1.4, src='5c', at=172.95)
sh('count', 3.0, src='5c', a=173.0, b=176.0)
sh('winner', 3.6, src='1', a=17.6, b=21.2)
sh('outro', 3.4)
STARTS = []; _t = 0
for s in SHOTS: STARTS.append(_t); _t += s[1]
T_END = _t; N = int(round(T_END * FPS))
def shot_at(t):
    for i, s in enumerate(SHOTS):
        if t < STARTS[i] + s[1]: return i, t - STARTS[i]
    return len(SHOTS) - 1, SHOTS[-1][1] - 1e-3

# ---------------- graphics ----------------
def fire_bg(t, cols=((255, 120, 0), (120, 0, 0))):
    c = R2.rays(t, [cols[0], cols[1]], 18, 70)
    a = np.array(c.convert('RGB')).astype(np.float32)
    v = np.clip(1 - 0.9 * np.sqrt(((R3._XX - W / 2) / (W * 0.7)) ** 2 + ((R3._YY - H / 2) / (H * 0.6)) ** 2), 0.15, 1)[..., None]
    return P((a * v).astype(np.uint8))

def chrome(txt, size, c1=(255, 245, 200), c2=(255, 160, 0), stroke=(60, 0, 0), f=F_BLACKI):
    im = text_img(txt, size, WHITE, stroke, max(6, size // 9), f=f)
    a = np.array(im).astype(np.float32); hgt = a.shape[0]
    grad = np.linspace(0, 1, hgt)[:, None]
    for k in range(3): a[..., k] = np.where(a[..., k] > 200, c1[k] * (1 - grad) + c2[k] * grad, a[..., k])
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))

def health(c, t, names, hp):
    d = ImageDraw.Draw(c)
    for side in (0, 1):
        x0 = 24 if side == 0 else W / 2 + 12; w = W / 2 - 36
        d.polygon([(x0, 70), (x0 + w, 70), (x0 + w - (14 if side == 0 else -14), 104), (x0 + (0 if side == 0 else 14), 104)], fill=(0, 0, 0, 200))
        f = max(0, hp[side])
        col = (60, 230, 60) if f > 0.5 else ((255, 200, 0) if f > 0.25 else RED)
        if side == 0: d.rectangle([x0 + 4 + (w - 8) * (1 - f), 74, x0 + w - 4, 100], fill=col)
        else: d.rectangle([x0 + 4, 74, x0 + 4 + (w - 8) * f, 100], fill=col)
        d.text((x0 + (6 if side == 0 else w - 6), 116), names[side], font=font(F_BLACK, 24), fill=WHITE, anchor='la' if side == 0 else 'ra', stroke_width=3, stroke_fill=BLACK)
    d.ellipse([W / 2 - 34, 58, W / 2 + 34, 126], fill=(0, 0, 0, 230), outline=GOLD, width=4)
    d.text((W / 2, 92), str(max(0, 99 - int(t * 3) % 100)), font=font(F_BLACK, 34), fill=GOLD, anchor='mm')

def caption(c, txt, tl, t0, y=1060, size=92, col=GOLD, rng=None):
    s = ease_pop(tl, t0, 0.12)
    if s <= 0: return
    im = chrome(txt, size, (255, 255, 230), col)
    paste(c, im, W / 2 + (rng.uniform(-4, 4) if rng else 0), y, s * (1 + 0.25 * math.exp(-(tl - t0) / 0.08)), -4)

def boom_fx(c, tl, t0, x=W / 2, y=640, txt=None):
    u = tl - t0
    if u < 0 or u > 0.45: return
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    r = 80 + 900 * u; n = 14
    pts = []
    for k in range(2 * n):
        a = k * math.pi / n; rr = r * (1.0 if k % 2 == 0 else 0.55)
        pts.append((x + rr * math.cos(a), y + rr * math.sin(a) * 0.8))
    al = int(255 * (1 - u / 0.45))
    d.polygon(pts, fill=(255, 230, 60, al)); d.polygon([(x + (p[0] - x) * 0.6, y + (p[1] - y) * 0.6) for p in pts], fill=(255, 255, 255, al))
    c.alpha_composite(layer)
    if txt: paste(c, chrome(txt, 120, (255, 255, 255), RED), x, y, 1 + u, -8)

def speed_lines(c, t, amt=1.0):
    d = ImageDraw.Draw(c); rng = random.Random(int(t * 30))
    for k in range(int(28 * amt)):
        a = rng.uniform(0, 2 * math.pi); r0 = rng.uniform(260, 420); r1 = r0 + rng.uniform(200, 600)
        d.line([(W / 2 + r0 * math.cos(a), H / 2 + r0 * math.sin(a)), (W / 2 + r1 * math.cos(a), H / 2 + r1 * math.sin(a))], fill=(255, 255, 255, 150), width=rng.randint(2, 6))

def booth(c, t, src_fn, st, label='КОММЕНТАТОР', size=250, x=W - 160, y=H - 330):
    img = src_fn(st)
    s = min(img.shape[0], img.shape[1]); cy = img.shape[0] * 0.42
    sq = img[int(cy - s / 2):int(cy + s / 2), :] if img.shape[0] > s else img
    sq = cv2.resize(sq, (size, size))
    im = Image.fromarray(sq).convert('RGBA')
    m = Image.new('L', (size, size), 0); ImageDraw.Draw(m).ellipse([0, 0, size - 1, size - 1], fill=255); im.putalpha(m)
    ring = Image.new('RGBA', (size + 20, size + 20), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, size + 19, size + 19], fill=GOLD + (255,))
    ring.alpha_composite(im, (10, 10))
    paste(c, ring, x, y)
    lb = text_img(label, 28, BLACK, GOLD, 0); bg = Image.new('RGBA', (lb.width + 16, lb.height + 4), GOLD + (255,)); bg.alpha_composite(lb, (8, 2))
    paste(c, bg, x, y + size / 2 + 22)

def belt(c, x, y, s=1.0):
    b = Image.new('RGBA', (520, 220), (0, 0, 0, 0)); d = ImageDraw.Draw(b)
    d.rounded_rectangle([0, 70, 519, 150], 30, fill=(40, 20, 10, 255))
    d.ellipse([150, 10, 370, 210], fill=GOLD + (255,), outline=(150, 100, 0, 255), width=8)
    d.ellipse([185, 45, 335, 175], fill=(255, 235, 140, 255))
    for xx in (60, 110, 410, 460): d.ellipse([xx - 22, 88, xx + 22, 132], fill=GOLD + (255,))
    d.text((260, 110), 'ЧЕМПИОН\nЛЕСА', font=font(F_BLACK, 30), fill=(120, 60, 0), anchor='mm', align='center')
    paste(c, b, x, y, s)

def confetti(c, tl, n=80, seed=3):
    r = random.Random(seed); d = ImageDraw.Draw(c)
    for k in range(n):
        x0 = r.uniform(0, W); v = r.uniform(250, 600); ph = r.uniform(0, 6); col = r.choice([GOLD, RED, BLUE, NEON, WHITE])
        y = -40 + v * tl + r.uniform(-200, 0); x = x0 + 30 * math.sin(tl * 4 + ph)
        if 0 < y < H:
            w_ = 14 * abs(math.sin(tl * 8 + ph)) + 3
            d.rectangle([x - w_, y - 6, x + w_, y + 6], fill=col)

# ---------------- render ----------------
def render(fi):
    t = fi / FPS
    i, tl = shot_at(t); key, dur, kw = SHOTS[i]
    rng = random.Random(fi * 577)
    c = None
    if key == 'sponsor':
        img = E(0.2 + min(1.16, tl * 0.95)); img = zoomc(img, 1.05 + 0.03 * math.sin(tl * 20))
        c = P(img)
        paste(c, text_img('ГЕНЕРАЛЬНЫЙ СПОНСОР', 44, WHITE, BLACK, 5), W / 2, 200, ease_pop(tl, 0.05, 0.15))
        if tl > 0.35: paste(c, chrome('ЭНЕРГОСИК', 120), W / 2, 980, ease_pop(tl, 0.35, 0.12), -4)
        if tl > 0.95: paste(c, chrome('В РОТИК', 130, (255, 255, 230), RED), W / 2, 1120, ease_pop(tl, 0.95, 0.12), 3)
    elif key == 'title':
        c = fire_bg(t)
        paste(c, chrome('ЛЕСНАЯ', 150), W / 2 + rng.uniform(-4, 4), 480, ease_pop(tl, 0.0, 0.2) * (1 + 0.04 * math.sin(tl * 20)), -6)
        paste(c, chrome('ЛИГА', 220, (255, 255, 255), RED), W / 2 + rng.uniform(-4, 4), 660, ease_pop(tl, 0.25, 0.2), -6)
        if tl > 0.8: paste(c, text_img('FOREST FIGHT NIGHT', 52, WHITE, BLACK, 6), W / 2, 830, ease_pop(tl, 0.8, 0.15))
        if tl > 1.2: paste(c, text_img('прямая трансляция из леса', 36, GOLD, BLACK, 4), W / 2, 900, ease_pop(tl, 1.2, 0.15))
        if tl < 0.08: flash(c, 1 - tl / 0.08)
        R.rain(c, tl, 0, 3.2, [EMO['🔥'], EMO['⚡']], 14, 9, (60, 110), (-1600, -900))
    elif key == 'intro':
        src, t0, tf = kw['src'], kw['t0'], kw['tf']
        if tl < tf - t0:
            img = F(src, t0 + tl); c = P(img)
        else:
            u = tl - (tf - t0)
            img = F(src, tf); g = img.mean(2, keepdims=True)
            img = np.clip(g + (img - g) * 0.2, 0, 255).astype(np.uint8)
            img = zoomc(img, 1.05 + 0.08 * u, W / 2, H * 0.4)
            tint = np.array(kw['col'], np.float32) / 255
            img = np.clip(img * (0.5 + 0.7 * tint), 0, 255).astype(np.uint8)
            c = P(img)
            if u < 0.06: flash(c, 1 - u / 0.06)
            d = ImageDraw.Draw(c)
            sl = min(1, u / 0.18)
            x = -W + sl * W
            d.polygon([(x, 880), (x + W, 860), (x + W, 1010), (x, 1030)], fill=kw['col'] + (235,))
            paste(c, chrome(kw['name'], 76 if len(kw['name']) < 14 else 62, (255, 255, 255), (230, 230, 230), BLACK), W / 2 + x, 945, 1.0, -2)
            for j, stt in enumerate(kw['stats']):
                if u > 0.3 + j * 0.2:
                    paste(c, text_img(stt, 40, WHITE, BLACK, 5), W / 2, 1090 + j * 56, ease_pop(u, 0.3 + j * 0.2, 0.12))
            paste(c, text_img('БОЕЦ', 44, BLACK, kw['col'], 0), 120, 840 - 0, 1.0 * sl)
    elif key == 'comm':
        img = C(84.3 + tl); c = P(img)
        paste(c, text_img('СЛОВО ЭКСПЕРТУ', 64, WHITE, BLACK, 7), W / 2, 210, ease_pop(tl, 0.05, 0.15), -3)
        d = ImageDraw.Draw(c); d.rectangle([0, 260, W, 310], fill=(0, 0, 0, 200))
        d.text((W / 2, 285), 'ЭНЕРГИЧНЫЙ · комментатор, эксперт по спорту', font=font(F_MONO, 24), fill=GOLD, anchor='mm')
        if tl > 2.2: caption(c, 'ЛЕГЕНДА', tl, 2.2, 470, 100, GOLD, rng)
    elif key == 'round':
        c = fire_bg(t, ((200, 0, 0), (40, 0, 0)))
        paste(c, chrome(kw['txt'], 170 if len(kw['txt']) < 8 else 150), W / 2, 560, ease_pop(tl, 0, 0.12) * (1 + 0.3 * math.exp(-tl / 0.1)), -5)
        if tl > 0.4: paste(c, chrome('БОЙ!', 200, (255, 255, 255), RED), W / 2, 790, ease_pop(tl, 0.4, 0.1), 4)
        if tl < 0.06: flash(c, 1)
    elif key in ('play', 'slowmo', 'replay', 'tired', 'rise', 'cool', 'count', 'winner'):
        src = kw['src']; a, b = kw['a'], kw['b']
        sp = kw.get('sp', 1.0)
        st = a + tl * sp if sp > 0 else a + tl * sp
        img = F(src, st)
        hits = kw.get('hits', [])
        hp_hit = min([abs(st - h) for h in hits] + [9])
        shake = 18 * math.exp(-hp_hit / 0.06) if hits else 0
        z = 1.03 + 0.12 * math.exp(-hp_hit / 0.08) if hits else 1.03
        if key == 'slowmo': z = 1.1 + 0.15 * tl / dur
        if key == 'replay': z = 1.25
        img = zoomc(img, z, W / 2, H * 0.5, rng.uniform(-shake, shake), rng.uniform(-shake, shake))
        if key in ('slowmo', 'replay'):
            img = rgbsplit(img, 6)
        if key == 'replay':
            g = img.mean(2, keepdims=True); img = np.clip(g + (img - g) * 0.4, 0, 255).astype(np.uint8)
            img = (img * np.array([1.0, 0.92, 0.75])).astype(np.uint8)
        if key == 'tired':
            g = img.mean(2, keepdims=True); img = np.clip(g + (img - g) * 0.3, 0, 255).astype(np.uint8)
        if key == 'rise':
            img = hue_rgb(img, tl * 120, 1.6)
        c = P(img)
        if key in ('slowmo',): speed_lines(c, t, 0.7)
        if 'fight' in kw:
            hp0 = 1.0; hp1 = 1.0
            # damage over the whole fight group; deterministic decay per shot index
            base = {'РЫЖИЙ ТАЙФУН': 0, 'ГОЛЫЙ ЭНТУЗИАЗМ': 0}
            frac = tl / dur
            n_h = sum(1 for h in hits if st >= h)
            hp1 = max(0.02, 0.9 - 0.15 * n_h - 0.15 * frac)
            hp0 = max(0.3, 0.95 - 0.05 * frac)
            if key == 'slowmo' and kw['cap'] == '': hp1 = max(0.01, 0.2 - 0.5 * frac)
            health(c, t, kw['fight'], (hp0, hp1))
        for h in hits:
            if 0 <= st - h < 0.4:
                boom_fx(c, st - h, 0, W / 2 + rng.uniform(-60, 60), 620, rng.choice(['БАХ!', 'ХРЯСЬ!', 'БУМ!', 'ПАУ!', 'ТЫЩ!']))
        caps = kw.get('cap')
        if isinstance(caps, list):
            for ct, txt in caps:
                if st >= ct and (st - ct) < 2.0: caption(c, txt, st, ct, 1080 if 'ПРИЁМ' not in txt else 1000, 96 if len(txt) < 12 else 70, GOLD, rng)
        if key == 'play' and kw.get('combo'):
            n_h = sum(1 for h in hits if st >= h)
            if n_h >= 2:
                paste(c, chrome(f'{n_h} HIT', 96, (255, 255, 255), (255, 80, 0)), 190, 330, 1 + 0.2 * math.exp(-min([st - h for h in hits if st >= h]) / 0.1), -8)
                paste(c, text_img('COMBO', 46, GOLD, BLACK, 5), 190, 410)
        if key == 'slowmo':
            d = ImageDraw.Draw(c); d.text((W - 30, 160), '× 0.35' if sp < 0.38 else '× 0.4', font=font(F_MONO, 40), fill=WHITE, anchor='ra', stroke_width=4, stroke_fill=BLACK)
            if kw['cap']: caption(c, kw['cap'], tl, 0.4, 1080, 76, GOLD, rng)
            else: caption(c, 'ДОБИВАЙ!', tl, 0.1, 1080, 110, RED, rng)
        if key == 'replay':
            d = ImageDraw.Draw(c)
            if int(tl * 2) % 2 == 0: d.ellipse([30, 160, 58, 188], fill=RED)
            d.text((70, 174), 'ПОВТОР', font=font(F_BLACK, 44), fill=WHITE, anchor='lm', stroke_width=4, stroke_fill=BLACK)
            d.text((W - 30, 174), '× 0.5', font=font(F_MONO, 40), fill=WHITE, anchor='rm', stroke_width=4, stroke_fill=BLACK)
            # telestrator arrow
            if tl > 0.8:
                p = min(1, (tl - 0.8) / 0.6)
                pts = [(W * 0.2 + W * 0.55 * k / 20, 760 - 300 * math.sin(math.pi * k / 20)) for k in range(int(20 * p) + 1)]
                if len(pts) > 1: d.line(pts, fill=(255, 230, 0), width=10)
            if tl > 1.6: caption(c, 'НОГА ВЫШЕ ГОЛОВЫ', tl, 1.6, 1080, 66, GOLD, rng)
            booth(c, t, E, 0.2 + (tl * 0.7) % 1.16, 'ЭКСПЕРТ', 210, W - 140, H - 330)
        if key == 'tired':
            d = ImageDraw.Draw(c)
            R.bar(d, 40, 200, 400, 44, 0.03 if int(tl * 6) % 2 else 0.0, RED, 'ВЫНОСЛИВОСТЬ', '2%', False)
            caption(c, 'БОЕЦ УСТАЛ', tl, 0.3, 1060, 90, (200, 200, 200), rng)
        if key == 'rise':
            speed_lines(c, t, 1.0)
            caption(c, 'ОН ВОССТАЛ', tl, 0.15, 1060, 110, GOLD, rng)
            d = ImageDraw.Draw(c); R.bar(d, 40, 200, 400, 44, min(1, 0.1 + tl / 1.5), NEON, 'ВЫНОСЛИВОСТЬ', f'{min(999, int(10 + tl * 330))}%', False)
            if tl < 0.08: flash(c, 1 - tl / 0.08)
        if key == 'cool':
            caption(c, 'УХОДИТ КРАСИВО', tl, 0.6, 1060, 84, GOLD, rng)
            if tl > 1.3:
                u = tl - 1.3
                # explosion behind (comic)
                boom_fx(c, u % 0.9, 0, W * 0.3, 600, None) if u < 0.9 else None
                paste(c, text_img('НЕ ОБОРАЧИВАЕТСЯ', 46, WHITE, BLACK, 5), W / 2, 1160, ease_pop(u, 0.2, 0.15))
        if key == 'count':
            n = min(3, int(tl / 0.9) + 1); ph = tl - (n - 1) * 0.9
            paste(c, chrome(str(n), 330, (255, 255, 255), RED), W / 2, 600, ease_pop(ph, 0, 0.1) * (1 + 0.4 * math.exp(-ph / 0.08)))
            paste(c, text_img('СУДЬЯ СЧИТАЕТ', 50, WHITE, BLACK, 6), W / 2, 230)
            if n == 3 and ph > 0.4: caption(c, 'ВСЁ!', tl, 2.2, 1060, 140, RED, rng)
        if key == 'winner':
            confetti(c, tl)
            if tl > 0.3: paste(c, chrome('ПОБЕДИТЕЛЬ', 110), W / 2, 220, ease_pop(tl, 0.3, 0.15), -4)
            if tl > 0.9: belt(c, W / 2, 1000, ease_pop(tl, 0.9, 0.2))
            if tl > 1.7: paste(c, text_img('ПОБЕДИЛА ДРУЖБА', 60, WHITE, BLACK, 7), W / 2, 1180, ease_pop(tl, 1.7, 0.15))
    elif key == 'need':
        img = C2(76.15 + tl); c = P(img)
        paste(c, text_img('ЭКСПЕРТ ЗНАЕТ, ЧТО ДЕЛАТЬ', 44, WHITE, BLACK, 5), W / 2, 200, ease_pop(tl, 0.05, 0.12))
    elif key == 'can':
        img = F('3', 147.0); g = img.mean(2, keepdims=True); img = np.clip(g + (img - g) * 0.3, 0, 255).astype(np.uint8)
        c = P(img)
        u = min(1, tl / 0.5)
        paste(c, CAN, W + 100 - (W / 2 + 100) * (1 - (1 - u) ** 3), 300 + 320 * u, 1.6, tl * 900 * (1 - u))
        if tl > 0.5:
            boom_fx(c, tl, 0.5, W / 2, 620, None)
            caption(c, 'ЭНЕРГОСИК В РОТИК', tl, 0.55, 1060, 74, NEON, rng)
        if tl < 0.05: flash(c, 0.7)
    elif key == 'ko':
        img = F('5c', kw['at']); g = img.mean(2, keepdims=True); img = np.clip(g + (img - g) * 0.15, 0, 255).astype(np.uint8)
        img = zoomc(img, 1.25, W / 2, H * 0.55, rng.uniform(-10, 10) * math.exp(-tl / 0.3), rng.uniform(-10, 10) * math.exp(-tl / 0.3))
        c = P(img)
        if tl < 0.08: flash(c, 1)
        paste(c, chrome('K.O.', 300, (255, 255, 255), RED), W / 2 + rng.uniform(-6, 6) * math.exp(-tl / 0.4), 600, ease_pop(tl, 0, 0.12) * (1 + 0.5 * math.exp(-tl / 0.08)), -6)
        if tl > 0.5: paste(c, text_img('НОКАУТ', 80, WHITE, BLACK, 8), W / 2, 820, ease_pop(tl, 0.5, 0.1))
    elif key == 'outro':
        c = fire_bg(t, ((40, 40, 60), (10, 10, 20)))
        booth(c, t, C, 41.6 + min(1.35, tl * 0.9), 'ЭНЕРГИЧНЫЙ', 360, W / 2, 480)
        paste(c, text_img('ЛЕСНАЯ ЛИГА', 90, GOLD, BLACK, 9), W / 2, 830, ease_pop(tl, 0.2, 0.15), -3)
        paste(c, text_img('следующий бой: в пятницу', 44, WHITE, BLACK, 5), W / 2, 930, ease_pop(tl, 0.5, 0.15))
        paste(c, text_img('спонсор: энергосик в ротик', 36, (200, 200, 200), BLACK, 4), W / 2, 990, ease_pop(tl, 0.8, 0.15))
        if dur - tl < 0.3: flash(c, (0.3 - (dur - tl)) / 0.3, (0, 0, 0))
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(21)
    LW = R3.load_wav
    AU = {k: LW(os.path.join(HERE, f'au{k}.wav')) for k in '12345'}
    AU['e'] = LW(os.path.join(SP, 'v4', 'au_e.wav')); AU['c'] = LW(os.path.join(SP, 'v4', 'au_c.wav')); AU['c2'] = LW(os.path.join(SP, 'v5', 'au_c2.wav'))
    VO = {k: LW(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['a0', 'a1', 'a2', 'a3', 'a4', 'r1', 'r2', 'rf', 'ko', 'w', 'pw']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0 or i < 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(src, s0, s1, speed=1.0, fade=0.01):
        a = AU[src]
        m = int(abs(s1 - s0) / abs(speed) * SR); pos = s0 * SR + np.arange(m) * speed
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def tt(d): return np.arange(int(d * SR)) / SR
    def punch():
        t = tt(0.35)
        x = np.tanh(4 * np.sin(2 * np.pi * np.cumsum(120 * np.exp(-t * 20) + 50) / SR) * np.exp(-t * 10)) + rng.standard_normal(len(t)) * 0.6 * np.exp(-t * 30)
        return x.astype(np.float32)
    def whoosh(d=0.4):
        t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2; return (np.convolve(x, np.ones(10) / 10, 'same') * 0.6).astype(np.float32)
    def bell():
        t = tt(1.8); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dcy) for f, dcy in ((830, 2.5), (1245, 3), (1660, 4), (2210, 5), (3120, 7)))
        return (x * 0.25 * np.minimum(1, t / 0.002)).astype(np.float32)
    def horn(d=0.9):
        t = tt(d); f0 = 466 * (1 - 0.05 * (t > d * 0.75))
        x = sum(((2 * np.pi * np.cumsum(f0 * m) / SR) % (2 * np.pi)) / np.pi - 1 for m in (1, 1.26, 1.5, 2))
        env = np.minimum(1, t / 0.02) * np.clip((d - t) / 0.08, 0, 1) * (1 + 0.2 * np.sin(2 * np.pi * 9 * t))
        return np.tanh(1.5 * x * env * 0.3).astype(np.float32)
    def crowd(d):
        t = tt(d); x = rng.standard_normal(len(t))
        x = np.convolve(x, np.hanning(60) / 30, 'same') - 0.6 * np.convolve(x, np.ones(400) / 400, 'same')
        mod = 0.7 + 0.3 * np.convolve(rng.standard_normal(len(t)), np.ones(8000) / 8000 * 40, 'same')
        return (x * mod * 0.35).astype(np.float32)
    def boom(d=1.0, f0=130):
        t = tt(d); f = f0 * np.exp(-t * 5) + 38; return np.tanh(2.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)).astype(np.float32)
    def scratch():
        t = tt(0.35); f = 400 + 1800 * np.abs(np.sin(2 * np.pi * 4 * t))
        return (0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * rng.standard_normal(len(t)) * 0.6 * np.exp(-t * 4)).astype(np.float32)
    def rock(d, bpm=BPM, key=40, lvl=1.0, intense=1):
        out = np.zeros(int(d * SR) + SR, np.float32); b8 = 60 / bpm / 2
        def put(ts, sig, g): i = int(ts * SR); j = min(len(out), i + len(sig)); out[i:j] += g * sig[:j - i]
        t = tt(0.4); kick = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(140 * np.exp(-t * 25) + 50) / SR) * np.exp(-t * 8)).astype(np.float32)
        t = tt(0.25); snare = (rng.standard_normal(len(t)) * np.exp(-t * 14) * 0.7 + np.sin(2 * np.pi * 200 * t) * np.exp(-t * 20) * 0.5).astype(np.float32)
        t = tt(0.05); hat = (np.diff(np.concatenate([[0], rng.standard_normal(len(t))])) * np.exp(-t * 80) * 0.4).astype(np.float32)
        riff = [0, 0, 3, 0, 5, 0, 3, 6, 0, 0, 3, 0, 7, 6, 5, 3]
        def chug(semi, L):
            t = tt(L); f = 82.4 * 2 ** ((key - 40 + semi) / 12)
            x = sum(((2 * np.pi * f * m * t) % (2 * np.pi)) / np.pi - 1 for m in (1, 1.498, 2.0))
            x = np.tanh(6 * x) * np.exp(-t * 6) * np.minimum(1, t / 0.003)
            return (x * 0.22).astype(np.float32)
        s = 0
        while s * b8 < d:
            ts = s * b8; st = s % 8
            if st in (0, 3, 4) or (intense > 1 and st == 6): put(ts, kick, 0.9)
            if st in (2, 6): put(ts, snare, 0.6)
            put(ts, hat, 0.5)
            put(ts, chug(riff[s % 16], b8 * 0.95), 1.0)
            s += 1
        return out[:int(d * SR)] * lvl
    T = lambda k: [STARTS[i] for i, s in enumerate(SHOTS) if s[0] == k]
    # music bed: rock throughout fights, crowd bed
    add(0, crowd(T_END), 0.45)
    t_title = T('title')[0]
    add(t_title, rock(T_END - t_title - 3.4, lvl=0.55), 1)
    # sponsor
    add(0, clip('e', 0.2, 1.36, 0.95 * 1.0), 1.2); add(0.35, boom(0.7, 160), 0.5); add(0.95, boom(0.7, 160), 0.5)
    add(t_title, bell(), 0.9); add(t_title, boom(1.2), 0.9); add(t_title + 0.2, VO['a0'], 1.0); add(t_title, horn(), 0.5)
    for i, (k, dur, kw) in enumerate(SHOTS):
        s0 = STARTS[i]
        if k == 'intro':
            add(s0, clip(kw['src'][0], kw['t0'], kw['tf']), 0.9)
            add(s0 + kw['tf'] - kw['t0'], boom(0.6, 180), 0.7); add(s0 + kw['tf'] - kw['t0'], whoosh(0.3), 0.6)
            add(s0 + kw['tf'] - kw['t0'] + 0.15, VO[{'РЫЖИЙ ТАЙФУН': 'a1', 'ПРИЗРАК В СВИТЕРЕ': 'a2', 'ГОЛЫЙ ЭНТУЗИАЗМ': 'a3', 'БЕЖЕВЫЙ ГРОМ': 'a4'}[kw['name']]], 1.1)
        elif k == 'comm':
            add(s0, clip('c', 84.3, 84.3 + dur), 1.2); add(s0 + 2.2, boom(0.6, 150), 0.5)
        elif k == 'round':
            add(s0, bell(), 1.0); add(s0 + 0.05, VO[kw['vo']], 1.1); add(s0, horn(0.7), 0.4)
        elif k in ('play', 'slowmo', 'replay', 'tired', 'rise', 'cool', 'count', 'winner'):
            a, b, sp = kw['a'], kw['b'], kw.get('sp', 1.0)
            src = kw['src'][0]
            if sp > 0: x = clip(src, a, a + dur * sp, sp)
            else: x = clip(src, a, a + dur * sp, sp)
            add(s0, x, 1.0 if k not in ('slowmo', 'replay') else 0.8)
            for h in kw.get('hits', []):
                ht = s0 + (h - a) / sp
                if s0 <= ht < s0 + dur: add(ht, punch(), 0.9); add(ht, boom(0.4, 200), 0.4)
            if k in ('slowmo', 'replay'): add(s0, whoosh(0.6), 0.7)
            if k == 'replay': add(s0, VO['pw'], 1.0)
            if k == 'rise': add(s0, boom(1.0), 0.8); add(s0, horn(1.2), 0.5)
            if k == 'count':
                for j in range(3): add(s0 + j * 0.9, punch(), 1.0)
            if k == 'winner': add(s0, horn(1.4), 0.7); add(s0 + 0.2, VO['w'], 1.1); add(s0, crowd(3.6), 0.8)
            if k == 'cool': add(s0 + 1.3, boom(1.0, 90), 0.7)
        elif k == 'need':
            add(s0, clip('c2', 76.15, 76.15 + dur), 1.2)
        elif k == 'can':
            add(s0, whoosh(0.5), 0.8); add(s0 + 0.5, punch(), 0.8); add(s0 + 0.55, clip('e', 0.2, 1.36), 1.2)
        elif k == 'ko':
            add(s0, boom(1.4, 220), 1.0); add(s0, scratch(), 0.6); add(s0 + 0.05, VO['ko'], 1.2); add(s0, crowd(1.4), 0.9)
        elif k == 'outro':
            add(s0, clip('c', 41.6, 41.6 + 1.5, 0.9), 1.1); add(s0, bell(), 0.6)
    mix = mix[:int(T_END * SR)]
    f = int(0.3 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.0) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for i, s in enumerate(SHOTS): print(f'{i:2d} {s[0]:8s} {STARTS[i]:6.2f} {s[1]}')
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
