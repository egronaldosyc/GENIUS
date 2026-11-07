import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, 'v2'), os.path.join(SP, 'v4')): sys.path.insert(0, p)
import render as R
import render2 as R2
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, WHITE, BLACK, emoji
from render2 import hue_rgb

FPS, SR = 30, 44100
F_SER = '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
F_MED = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
RED = (200, 20, 25); CREAM = (240, 225, 190); PINK = (255, 140, 190); ROSE = (255, 200, 220)
EMJ = {k: emoji(k, 150) for k in ['💔', '💗', '🌸', '🥀', '😢', '❤️', '✓', '🍷']}
NFR = {1: 1581, 2: 1337, 3: 1711, 4: 783, 5: 1342}

# ---------------- кружок ----------------
_c = {}
YY, XX = np.mgrid[0:400, 0:400]
CM = cv2.GaussianBlur((((XX - 200) ** 2 + (YY - 200) ** 2) < 192 ** 2).astype(np.uint8) * 255, (5, 5), 0)
def kf(v, t):
    i = int(np.clip(round(t * 30), 0, NFR[v] - 1)); k = (v, i)
    if k not in _c:
        if len(_c) > 250: _c.pop(next(iter(_c)))
        _c[k] = cv2.cvtColor(cv2.imread(os.path.join(HERE, f'k{v}', f'{i+1:04d}.jpg')), cv2.COLOR_BGR2RGB)
    return _c[k]
def kr(v, t, size, ring=(255, 255, 255), rw=8, fx=None, zoom=1.0, cy=0.5):
    img = kf(v, t)
    if zoom != 1.0:
        M = cv2.getRotationMatrix2D((200, 400 * cy), 0, zoom); img = cv2.warpAffine(img, M, (400, 400), borderMode=cv2.BORDER_REFLECT)
    if fx: img = fx(img)
    im = Image.fromarray(img).convert('RGBA'); im.putalpha(Image.fromarray(CM)); im = im.resize((size, size), Image.BICUBIC)
    if not ring: return im
    out = Image.new('RGBA', (size + 2 * rw, size + 2 * rw), (0, 0, 0, 0)); d = ImageDraw.Draw(out)
    d.ellipse([0, 0, size + 2 * rw - 1, size + 2 * rw - 1], fill=ring + (255,)); out.alpha_composite(im, (rw, rw)); return out
def warm(img): return hue_rgb(img, 0, 1.15)
def sad(img):
    x = img.astype(np.float32); g = x.mean(2, keepdims=True); x = g + (x - g) * 0.35; x = x * np.array([0.85, 0.9, 1.12]); return np.clip(x, 0, 255).astype(np.uint8)
def dreamy(img):
    x = img.astype(np.float32); b = cv2.GaussianBlur(img, (0, 0), 6).astype(np.float32)
    x = x * 0.6 + b * 0.6; x = x * np.array([1.12, 0.95, 1.05]) + 10; return np.clip(x, 0, 255).astype(np.uint8)

# ---------------- backgrounds ----------------
def poster_bg(t, c1=RED, c2=(120, 0, 0)):
    c = R2.rays(t, [c1, c2], 14, 18)
    d = ImageDraw.Draw(c); d.rectangle([0, 0, W, 34], fill=CREAM); d.rectangle([0, H - 34, W, H], fill=CREAM)
    return c
_pink = None
def pink_bg(t):
    global _pink
    if _pink is None:
        y = np.linspace(0, 1, H)[:, None, None]
        _pink = (np.array([60, 20, 50]) * (1 - y) + np.array([200, 90, 140]) * y).astype(np.float32) * np.ones((H, W, 3))
    x = _pink.copy()
    c = P(np.clip(x, 0, 255).astype(np.uint8))
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); r = random.Random(7)
    for k in range(26):  # bokeh
        bx = (r.uniform(0, W) + 12 * math.sin(t * 0.5 + k)) % W; by = (r.uniform(0, H) - t * r.uniform(8, 25)) % H; br = r.uniform(18, 60)
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=(255, 200, 230, int(r.uniform(25, 70))))
    c.alpha_composite(layer.filter(ImageFilter.GaussianBlur(6)))
    return c
def rain(c, t, n=110, alpha=110):
    d = ImageDraw.Draw(c); r = random.Random(3)
    for k in range(n):
        x = r.uniform(-100, W + 100); sp = r.uniform(900, 1500); L = r.uniform(30, 70)
        y = (r.uniform(0, H) + t * sp) % (H + 100) - 50; x2 = x - 0.25 * (y % 2000)
        xx = (x + t * sp * 0.2) % (W + 200) - 100
        d.line([(xx, y), (xx - L * 0.25, y + L)], fill=(220, 230, 255, alpha), width=2)
def hearts(c, t, n=12, seed=1, emo='💗', size=(50, 100), alpha=1.0):
    r = random.Random(seed)
    for k in range(n):
        x0 = r.uniform(40, W - 40); sp = r.uniform(60, 140); ph = r.uniform(0, 10)
        y = H + 60 - ((t + ph) * sp) % (H + 160); x = x0 + 30 * math.sin(t * 1.5 + k)
        paste(c, EMJ[emo], x, y, r.uniform(*size) / 150, 15 * math.sin(t + k), alpha)
def P(a): return Image.fromarray(a).convert('RGBA')
def flash(c, a, col=(255, 255, 255)):
    if a > 0: c.alpha_composite(Image.new('RGBA', (W, H), col + (int(255 * min(1, a)),)))
def cursive(c, txt, x, y, size, tl, t0, col=WHITE, fade=0.5):
    a = min(1, max(0, (tl - t0) / fade))
    if a <= 0: return
    im = text_img(txt, size, col, (90, 20, 60), max(2, size // 22), f=F_SER)
    paste(c, im, x, y - 10 * (1 - a), 1.0, 0, a)
def poster_text(c, txt, y, size, tl, t0, col=CREAM, rot=-3):
    s = ease_pop(tl, t0, 0.15)
    if s <= 0: return
    paste(c, text_img(txt, size, col, BLACK, max(6, size // 10), spacing=-8), W / 2, y, s, rot)
def counter(c, n, tl):
    im = text_img(f'РЮМКА №{n}', 70, CREAM, BLACK, 7)
    paste(c, im, W / 2, 210, ease_pop(tl, 0, 0.12) * (1 + 0.3 * math.exp(-tl / 0.08)), -4)
def liver(c, val, t):
    d = ImageDraw.Draw(c); x, y, w, h = 60, H - 170, 600, 46
    d.rounded_rectangle([x, y, x + w, y + h], 8, fill=(0, 0, 0, 190), outline=CREAM, width=3)
    if val > 0 and not (val < 0.2 and int(t * 6) % 2): d.rounded_rectangle([x + 5, y + 5, x + 5 + (w - 10) * val, y + h - 5], 5, fill=(220, 50, 40))
    d.text((x + 14, y + h / 2), 'ПЕЧЕНЬ ЕГОРА', font=font(F_MONO, 22), fill=WHITE, anchor='lm', stroke_width=2, stroke_fill=BLACK)
    d.text((x + w - 14, y + h / 2), f'{int(val*100)}%', font=font(F_MONO, 22), fill=WHITE, anchor='rm', stroke_width=2, stroke_fill=BLACK)

# ---------------- timeline ----------------
SH = []
def s(k, d, **kw): SH.append((k, d, kw))
s('title', 3.2)
s('shot', 4.0, v=3, a=0.0, n=1, cap='ВСЁ НАЧАЛОСЬ НЕВИННО', liv=(1.0, 0.85))
s('shot', 4.0, v=1, a=20.0, n=2, cap='«ЗА ЗДОРОВЬЕ»', liv=(0.85, 0.6))
s('shot', 2.5, v=1, a=38.0, n=3, cap='ИРОНИЯ', liv=(0.6, 0.42))
s('shot', 3.0, v=1, a=47.0, n=4, cap='ОСТАНОВИСЬ', liv=(0.42, 0.18), sp=1.25)
s('fall', 1.2, v=1, a=42.9)
s('remember', 1.8)
s('melissa', 6.0, v=4, a=0.0)
s('chat', 4.4)
s('ksusha', 4.0, v=4, a=8.0)
s('chudo', 4.0, v=2, a=2.0)
s('scales', 3.4, v=3, a=34.0)
s('vape', 4.0, v=5, a=33.0, sp=0.7)
s('names', 4.0, v=3, a=40.0)
s('speech', 3.6, v=1, a=13.0)
s('tear', 3.0, v=4, a=1.0)
s('heart', 2.4, v=4, a=10.0)
s('end', 4.6)
STARTS = []; _t = 0
for x in SH: STARTS.append(_t); _t += x[1]
T_END = _t; N = int(round(T_END * FPS))
def at(t):
    for i, x in enumerate(SH):
        if t < STARTS[i] + x[1]: return i, t - STARTS[i]
    return len(SH) - 1, SH[-1][1] - 1e-3

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; i, tl = at(t); k, dur, kw = SH[i]; rng = random.Random(fi * 17); c = None
    if k == 'title':
        c = poster_bg(t)
        g = kr(1, 5.0 + tl * 0.4, 430, CREAM, 10, warm)
        paste(c, g, W / 2, 720, ease_pop(tl, 0.0, 0.25))
        poster_text(c, 'АЛКОГОЛЬ', 250, 130, tl, 0.15)
        poster_text(c, '— ЗЛО', 390, 150, tl, 0.45, (255, 230, 120))
        if tl > 1.2:
            d = ImageDraw.Draw(c); u = min(1, (tl - 1.2) / 0.25)
            d.line([(W / 2 - 230, 950), (W / 2 - 230 + 460 * u, 490)], fill=(255, 255, 255), width=26)
            d.line([(W / 2 - 230, 950), (W / 2 - 230 + 460 * u, 490)], fill=RED, width=16)
        if tl > 1.6: poster_text(c, 'ИСТОРИЯ ОДНОГО ВЕЧЕРА', 1060, 44, tl, 1.6, CREAM, 0)
        if tl > 2.0: paste(c, text_img('в главной роли: ЕГОР', 36, (255, 230, 120), BLACK, 4), W / 2, 1130, ease_pop(tl, 2.0, 0.15))
    elif k == 'shot':
        sp = kw.get('sp', 1.0); st = kw['a'] + tl * sp
        dz = 1.0 + 0.04 * kw['n']
        c = poster_bg(t, (150 + 20 * kw['n'], 15, 20), (60, 0, 0))
        wob = 3 * kw['n'] * math.sin(t * (2 + kw['n']))
        g = kr(kw['v'], st, 600, CREAM, 10, warm if kw['n'] < 4 else (lambda im: hue_rgb(im, 0, 1.5)))
        paste(c, g, W / 2 + wob, 680, dz, wob * 0.6)
        counter(c, kw['n'], tl)
        if tl > 0.6: poster_text(c, kw['cap'], 1060, 62 if len(kw['cap']) < 14 else 50, tl, 0.6)
        a, b = kw['liv']; liver(c, a + (b - a) * min(1, tl / dur), t)
        if tl < 0.05: flash(c, 0.6)
        if kw['n'] >= 3:
            a_ = np.array(c.convert('RGB'))
            if kw['n'] == 4: a_ = R3_ghost(a_, kw['v'], st, t)
            c = P(a_)
    elif k == 'fall':
        img = kf(1, kw['a'] + tl * 0.6); img = cv2.resize(img, (W, W)); full = np.zeros((H, W, 3), np.uint8); full[(H - W) // 2:(H + W) // 2] = img
        full = glitch_slices(full, rng, 10, 120)
        c = P(full); poster_text(c, 'РЮМКА №5', 220, 90, tl, 0.0, (255, 80, 80), -6)
        if tl > 0.6: c = P(np.zeros((H, W, 3), np.uint8))
    elif k == 'remember':
        c = P(np.zeros((H, W, 3), np.uint8))
        cursive(c, 'а потом он вспомнил…', W / 2, H / 2, 64, tl, 0.2, WHITE, 0.6)
    elif k == 'melissa':
        c = pink_bg(t)
        z = 1.0 + 0.04 * tl
        g = kr(4, kw['a'] + tl, 620, ROSE, 10, sad)
        paste(c, g, W / 2, 640, z)
        rain(c, t)
        hearts(c, t, 8, 2, '💗', (40, 80), 0.8)
        cursive(c, 'Мелисса…', W / 2, 1120, 110, tl, 1.2, (255, 220, 235), 0.8)
        if tl > 3.0: cursive(c, 'он помнит её смех', W / 2, 1220, 44, tl, 3.0, WHITE, 0.6)
    elif k == 'chat':
        c = P(np.full((H, W, 3), (18, 18, 24), np.uint8)); d = ImageDraw.Draw(c)
        half = tl < 2.2; name = 'Мелисса' if half else 'Ксюша'; u = tl if half else tl - 2.2
        d.rectangle([0, 0, W, 150], fill=(32, 32, 42))
        d.ellipse([30, 40, 100, 110], fill=PINK if half else (200, 160, 255))
        d.text((65, 75), name[0], font=font(F_BLACK, 40), fill=WHITE, anchor='mm')
        d.text((125, 55), name, font=font(F_BLACK, 36), fill=WHITE)
        status = 'была в сети давно' if half else ('печатает…' if 1.0 < u < 1.7 else 'была в сети 3 часа назад')
        d.text((125, 100), status, font=font(F_MED, 24), fill=(140, 200, 255) if 'печатает' in status else (150, 150, 160))
        msgs = (['Мелисса привет', 'как ты?', 'я тут подумал', 'мелисса??'] if half else ['Ксюш', 'ксюша ты спишь', 'я скучаю 🥀'])
        y = 260
        for j, m in enumerate(msgs):
            if u < 0.15 + j * 0.42: break
            fo = font(F_MED, 34); wdt = d.textlength(m.replace('🥀', ''), font=fo) + (50 if '🥀' in m else 0) + 120
            x1 = W - 30; x0 = x1 - wdt
            d.rounded_rectangle([x0, y, x1, y + 70], 22, fill=(70, 110, 220))
            d.text((x0 + 24, y + 35), m.replace('🥀', ''), font=fo, fill=WHITE, anchor='lm')
            if '🥀' in m: paste(c, EMJ['🥀'], x1 - 110, y + 35, 40 / 150)
            d.text((x1 - 20, y + 50), '✓', font=font(F_SYM, 24), fill=(200, 220, 255), anchor='rm')
            y += 92
        if not half and u > 1.7:
            cursive(c, 'не ответила.', W / 2, 1050, 70, u, 1.75, (255, 160, 190), 0.4)
        if half and u > 1.8: cursive(c, 'не ответила.', W / 2, 1050, 70, u, 1.8, (255, 160, 190), 0.3)
        d.rounded_rectangle([30, H - 120, W - 30, H - 50], 35, fill=(40, 40, 52)); d.text((70, H - 85), 'Сообщение', font=font(F_MED, 30), fill=(120, 120, 130), anchor='lm')
    elif k == 'ksusha':
        c = pink_bg(t + 10)
        g = kr(4, kw['a'] + tl * 0.8, 600, (220, 190, 255), 10, sad)
        paste(c, g, W / 2, 640, 1.03 + 0.03 * tl, -2)
        rain(c, t + 5)
        hearts(c, t, 7, 4, '🌸', (40, 80), 0.85)
        cursive(c, 'а Ксюша…', W / 2, 1110, 110, tl, 0.4, (235, 220, 255), 0.6)
        if tl > 2.0: cursive(c, '…так и не узнала', W / 2, 1220, 50, tl, 2.0, WHITE, 0.5)
    elif k == 'chudo':
        c = pink_bg(t + 20)
        g = kr(2, kw['a'] + tl, 600, ROSE, 10, sad); paste(c, g, W / 2, 620)
        rain(c, t + 9, 70, 80)
        cursive(c, 'он заедает тоску', W / 2, 1050, 66, tl, 0.3, WHITE, 0.5)
        if tl > 1.8: poster_text(c, 'ЕДИНСТВЕННОЕ ЧУДО\nЭТОГО ВЕЧЕРА', 1180, 48, tl, 1.8, (255, 230, 240), -2)
    elif k == 'scales':
        c = pink_bg(t + 30); d = ImageDraw.Draw(c)
        ang = 0.25 * math.sin(tl * 3.2); cx, cy = W / 2, 470
        d.rectangle([cx - 8, cy, cx + 8, 900], fill=(230, 200, 120)); d.polygon([(cx - 90, 920), (cx + 90, 920), (cx, 880)], fill=(230, 200, 120))
        L = 270; lx, ly = cx - L * math.cos(ang), cy - L * math.sin(ang); rx, ry = cx + L * math.cos(ang), cy + L * math.sin(ang)
        d.line([(lx, ly), (rx, ry)], fill=(240, 210, 130), width=12)
        for (px, py, nm, col) in ((lx, ly, 'Мелисса', PINK), (rx, ry, 'Ксюша', (200, 160, 255))):
            d.line([(px, py), (px - 70, py + 160)], fill=(230, 200, 120), width=4); d.line([(px, py), (px + 70, py + 160)], fill=(230, 200, 120), width=4)
            d.chord([px - 110, py + 110, px + 110, py + 230], 0, 180, fill=(240, 210, 130))
            paste(c, text_img(nm, 52, WHITE, col, 5, f=F_SER), px, py + 90)
            paste(c, EMJ['💗' if nm == 'Мелисса' else '🌸'], px, py + 150, 0.5)
        g = kr(3, kw['a'] + tl, 300, CREAM, 8, sad); paste(c, g, cx, 300)
        cursive(c, 'он так и не смог выбрать', W / 2, 1100, 58, tl, 0.6, WHITE, 0.5)
    elif k == 'vape':
        c = pink_bg(t + 40)
        g = kr(5, kw['a'] + tl * kw['sp'], 620, (200, 200, 220), 10, lambda im: dreamy(sad(im))); paste(c, g, W / 2, 640)
        layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer); r = random.Random(5)
        for q in range(14):
            sx = W / 2 + 200 * math.sin(tl * 0.7 + q) ; sy = 900 - ((tl * 90 + q * 60) % 700); rr = 50 + q * 6
            d.ellipse([sx - rr, sy - rr, sx + rr, sy + rr], fill=(255, 255, 255, 30))
        c.alpha_composite(layer.filter(ImageFilter.GaussianBlur(18)))
        cursive(c, 'дым уносит воспоминания…', W / 2, 1100, 56, tl, 0.4, WHITE, 0.6)
        if tl > 2.4: paste(c, text_img('(вейп — тоже зло)', 34, (255, 220, 230), BLACK, 3), W / 2, 1190, ease_pop(tl, 2.4, 0.15))
    elif k == 'names':
        c = pink_bg(t + 50)
        g = kr(3, kw['a'] + tl * 0.7, 600, ROSE, 10, sad); paste(c, g, W / 2, 640)
        rain(c, t + 13)
        r = random.Random(11)
        for q in range(9):
            nm = 'Мелисса' if q % 2 == 0 else 'Ксюша'; t0 = q * 0.38
            if tl < t0: continue
            a = max(0, 1 - (tl - t0) / 2.2)
            x = r.uniform(120, W - 120); y = r.uniform(180, 1180) - (tl - t0) * 40
            paste(c, text_img(nm, int(r.uniform(44, 80)), (255, 220, 240) if q % 2 == 0 else (225, 210, 255), (90, 20, 60), 3, f=F_SER), x, y, 1.0, r.uniform(-12, 12), a)
    elif k == 'speech':
        c = pink_bg(t + 60)
        g = kr(1, kw['a'] + tl, 600, ROSE, 10, sad); paste(c, g, W / 2, 600)
        cursive(c, 'он всё им высказал…', W / 2, 1060, 64, tl, 0.3, WHITE, 0.5)
        if tl > 1.6: paste(c, text_img('в кружке, который никто не посмотрит', 36, (255, 220, 235), BLACK, 3), W / 2, 1150, ease_pop(tl, 1.6, 0.15))
    elif k == 'tear':
        c = pink_bg(t + 70)
        g = kr(4, kw['a'] + tl * 0.5, 640, ROSE, 10, sad, zoom=1.0 + 0.3 * min(1, tl / 2.0), cy=0.2); paste(c, g, W / 2, 620)
        d = ImageDraw.Draw(c)
        for q in range(2):
            ty = 420 + ((tl * 260 + q * 180) % 420); tx = W / 2 - 60 + q * 120
            d.ellipse([tx - 14, ty - 10, tx + 14, ty + 22], fill=(170, 210, 255, 230)); d.polygon([(tx - 13, ty), (tx + 13, ty), (tx, ty - 28)], fill=(170, 210, 255, 230))
        rain(c, t + 17)
        poster_text(c, 'ЕГОР ПЛАЧЕТ', 1100, 100, tl, 0.6, (255, 220, 235), -2)
    elif k == 'heart':
        c = pink_bg(t + 80); d = ImageDraw.Draw(c)
        split = min(1, max(0, (tl - 0.8) / 0.5)) * 60
        hrt = EMJ['💗'].resize((520, 520))
        if split <= 0: paste(c, hrt, W / 2, 600)
        else:
            lft = hrt.crop((0, 0, 260, 520)); rgt = hrt.crop((260, 0, 520, 520))
            paste(c, lft, W / 2 - 130 - split, 600 + split * 0.6, 1.0, split * 0.3)
            paste(c, rgt, W / 2 + 130 + split, 600 + split * 0.6, 1.0, -split * 0.3)
        paste(c, text_img('М', 130, WHITE, (140, 20, 70), 8, f=F_SER), W / 2 - 110 - split, 600 + split * 0.6)
        paste(c, text_img('К', 130, WHITE, (90, 20, 140), 8, f=F_SER), W / 2 + 110 + split, 600 + split * 0.6)
        g = kr(4, kw['a'] + tl * 0.5, 200, ROSE, 6, sad); paste(c, g, W / 2, 1000)
        if tl < 0.85 or True: paste(c, text_img('+', 120, WHITE, BLACK, 0), W / 2, 600, 1.0 if split <= 0 else 0.01)
        if tl > 1.3: paste(c, text_img('одно сердце. два имени.', 58, WHITE, (90, 20, 60), 5, f=F_SER), W / 2, 1180, ease_pop(tl, 1.3, 0.2))
    elif k == 'end':
        c = poster_bg(t, (170, 20, 25), (70, 0, 0))
        poster_text(c, 'АЛКОГОЛЬ', 300, 120, tl, 0.0)
        poster_text(c, 'НЕ ВЕРНЁТ', 430, 100, tl, 0.3, (255, 230, 120))
        poster_text(c, 'МЕЛИССУ И КСЮШУ', 560, 74, tl, 0.6)
        if tl > 1.5:
            g = kr(4, 1.0 + tl * 0.3, 300, CREAM, 8, sad); paste(c, g, W / 2, 830, ease_pop(tl, 1.5, 0.2))
        if tl > 2.4: poster_text(c, 'БЕРЕГИТЕ СЕБЯ', 1060, 64, tl, 2.4, CREAM, 0)
        if tl > 3.0: paste(c, text_img('Егор, мы с тобой', 40, WHITE, BLACK, 4, f=F_SER), W / 2, 1150, ease_pop(tl, 3.0, 0.15))
        d = ImageDraw.Draw(c); d.text((W / 2, H - 17), 'ЧРЕЗМЕРНОЕ УПОТРЕБЛЕНИЕ АЛКОГОЛЯ ВРЕДИТ ВАШЕМУ ЗДОРОВЬЮ', font=font(F_MONO, 16), fill=(60, 0, 0), anchor='mm')
        if dur - tl < 0.35: flash(c, (0.35 - (dur - tl)) / 0.35, (0, 0, 0))
    return np.array(c.convert('RGB'))

def R3_ghost(a_, v, st, t):
    g = kr(v, st - 0.25, 600, None, 0, None)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); lay.alpha_composite(g, (W // 2 - 300 + 30, 680 - 300))
    base = Image.fromarray(a_).convert('RGBA'); arr = np.array(lay); arr[..., 3] = (arr[..., 3] * 0.35).astype(np.uint8)
    base.alpha_composite(Image.fromarray(arr)); return np.array(base.convert('RGB'))

# ---------------- AUDIO ----------------
def load(p):
    w = wave.open(p); sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch == 2: a = a.reshape(-1, 2).mean(1)
    if sr != SR: a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
    return a
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(4)
    AU = {v: load(os.path.join(HERE, f'au{v}.wav')) for v in range(1, 6)}
    VO = {k: load(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['t0', 't1', 't2', 't3']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(v, s0, d, sp=1.0, fade=0.02):
        a = AU[v]; m = int(d * SR); pos = s0 * SR + np.arange(m) * sp
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        r = np.sqrt((x ** 2).mean()) + 1e-6; return x * min(5.0, 0.12 / r)
    def tt(d): return np.arange(int(d * SR)) / SR
    def reverb(x, g=0.5):
        y = x.copy()
        for dl, gg in ((0.037, .5), (0.061, .4), (0.093, .33), (0.137, .27), (0.2, .2), (0.29, .14)):
            k = int(dl * SR); y[k:] += g * gg * x[:-k]
        return y
    def piano(f, d=2.5):
        t = tt(d); x = sum(np.sin(2 * np.pi * f * m * t) * (0.6 ** (m - 1)) * np.exp(-t * (1.2 + m * 0.8)) for m in range(1, 6))
        return (x * np.minimum(1, t / 0.004) * 0.16).astype(np.float32)
    def clink():
        t = tt(0.6); x = sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dd) for f, dd in ((2637, 6), (3520, 8), (4186, 10), (5274, 12)))
        return (x * 0.12).astype(np.float32)
    def gulp():
        t = tt(0.16); f = 250 + 500 * t / 0.16; return (0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.16)).astype(np.float32)
    def boom(d=1.0, f0=90):
        t = tt(d); f = f0 * np.exp(-t * 4) + 34; return np.tanh(2.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.4)).astype(np.float32)
    def brass(f0, d=0.8):
        t = tt(d); x = sum(((2 * np.pi * np.cumsum(np.full(len(t), f0 * m)) / SR) % (2 * np.pi)) / np.pi - 1 for m in (1, 1.5, 2))
        env = np.minimum(1, t / 0.03) * np.exp(-t * 2.5); return np.tanh(1.6 * x * env * 0.25).astype(np.float32)
    def pop():
        t = tt(0.08); return (0.3 * np.sin(2 * np.pi * (900 + 1200 * t / 0.08) * t) * np.exp(-t * 40)).astype(np.float32)
    def rainnoise(d):
        x = rng.standard_normal(int(d * SR)).astype(np.float32); x = np.diff(np.concatenate([[0], x])) * 0.5
        x = np.convolve(x, np.ones(3) / 3, 'same'); f = int(1.0 * SR); x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f); return x * 0.08
    def heartbeat(d, bpm=70):
        out = np.zeros(int(d * SR), np.float32); b = 60 / bpm; t = tt(0.3)
        lub = np.tanh(2.5 * np.sin(2 * np.pi * 50 * t) * np.exp(-t * 18)).astype(np.float32)
        k = 0
        while k * b < d:
            i0 = int(k * b * SR); out[i0:i0 + len(lub)] += lub[:len(out) - i0]; i1 = int((k * b + 0.18) * SR)
            out[i1:i1 + len(lub)] += 0.7 * lub[:max(0, len(out) - i1)]; k += 1
        return out
    S = {}
    for i, x in enumerate(SH): S.setdefault(x[0], []).append((STARTS[i], x))
    # ---- alcohol part
    t_title = S['title'][0][0]
    add(t_title, boom(1.4, 70), 0.9); add(t_title + 0.15, brass(110, 1.2), 0.8); add(t_title + 0.45, brass(98, 1.4), 0.8)
    add(t_title + 0.4, reverb(VO['t0'], 0.5), 1.0)
    alc_end = S['remember'][0][0]
    add(S['shot'][0][0][0] if False else STARTS[1], heartbeat(alc_end - STARTS[1], 72), 0.5)
    for (st, (k, d, kw)) in S['shot']:
        add(st, clip(kw['v'], kw['a'], d, kw.get('sp', 1.0)), 1.0)
        add(st, clink(), 0.9); add(st + 0.05, boom(0.6, 120), 0.5); add(st + 0.05, brass(110 - 8 * kw['n'], 0.6), 0.5)
        add(st + d * 0.55, gulp(), 0.6)
    st, (k, d, kw) = S['fall'][0]
    add(st, clip(1, kw['a'], 0.6, 0.6), 1.0); add(st, boom(1.0, 160), 0.8)
    st = S['remember'][0][0]; add(st + 0.2, reverb(VO['t1'], 0.6), 0.9)
    # ---- sad piano for M&K part (Am F C G), 66 bpm-ish
    p0 = S['melissa'][0][0]; p1 = S['end'][0][0] + SH[-1][1]
    chords = [(220.0, [110.0, 164.8, 220.0, 261.6]), (174.6, [87.3, 130.8, 174.6, 220.0]), (130.8, [65.4, 130.8, 164.8, 196.0]), (196.0, [98.0, 146.8, 196.0, 246.9])]
    mel = [659.3, 587.3, 523.3, 493.9, 523.3, 440.0, 392.0, 440.0, 349.2, 392.0, 440.0, 523.3, 493.9, 440.0, 392.0, 329.6]
    bar = 2.4; t = p0; k = 0
    while t < p1 - 0.5:
        root, ch = chords[k % 4]
        for j, f in enumerate(ch): add(t + j * 0.07, piano(f, 3.0), 0.8)
        for q in range(2):
            add(t + q * bar / 2, piano(mel[(k * 2 + q) % len(mel)], 2.0), 0.9)
        t += bar; k += 1
    add(p0, rainnoise(p1 - p0), 1.0)
    for (st, (k_, d, kw)) in [(a, b) for kk in ('melissa', 'ksusha', 'chudo', 'scales', 'vape', 'names', 'speech', 'tear', 'heart') for (a, b) in S[kk]]:
        v = kw['v']; sp = kw.get('sp', 1.0)
        if k_ in ('ksusha', 'names', 'tear', 'heart'): sp = {'ksusha': 0.8, 'names': 0.7, 'tear': 0.5, 'heart': 0.5}[k_]
        x = clip(v, kw['a'], d, sp); add(st, reverb(x, 0.6) if sp < 1 else x, 0.6)
    st, (k_, d, kw) = S['chat'][0]
    for j in range(4): add(st + 0.15 + j * 0.42, pop(), 0.9)
    for j in range(3): add(st + 2.2 + 0.15 + j * 0.42, pop(), 0.9)
    for q in range(6): add(st + 2.2 + 1.0 + q * 0.11, (rng.standard_normal(400) * 0.05).astype(np.float32), 1)
    st, (k_, d, kw) = S['heart'][0]; add(st + 0.8, boom(0.8, 100), 0.6)
    t3 = (rng.standard_normal(int(0.12 * SR)) * np.exp(-np.arange(int(0.12 * SR)) / SR * 30) * 0.4).astype(np.float32); add(st + 0.8, t3, 1)
    st, (k_, d, kw) = S['end'][0]
    add(st, boom(1.2, 70), 0.7); add(st + 0.1, reverb(VO['t2'], 0.5), 1.0); add(st + 2.5, reverb(VO['t3'], 0.5), 1.0)
    mix = mix[:int(T_END * SR)]; f = int(0.35 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.1) * 0.93
    stt = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(stt.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for i, x in enumerate(SH): print(f'{i:2d} {x[0]:9s} {STARTS[i]:6.2f} {x[1]}')
        mk = sum(x[1] for x in SH if x[0] in ('melissa', 'chat', 'ksusha', 'chudo', 'scales', 'vape', 'names', 'speech', 'tear', 'heart'))
        print('total', T_END, 'M&K', round(mk, 1), round(mk / T_END * 100)); sys.exit()
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
