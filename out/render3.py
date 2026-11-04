import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
sys.path.insert(0, SP); sys.path.insert(0, os.path.join(SP, 'v2'))
import render as R
import render2 as R2
from render import (W, H, font, text_img, paste, ease_pop, hue_shift, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM,
                    NEON, RED, WHITE, BLACK, EMO, CAN, CAN2, emoji)
from render2 import _fry, hue_rgb, battery

FPS, SR = 30, 44100
UP = '/root/.claude/uploads/26d127ed-d183-5535-9bf5-4686595d072f/'
EMO2 = {k: emoji(k, 150) for k in ['💪', '🏆', '👍', '❤️', '✨', '📢', '🔮', '🍝', '👁️', '🥵', '😈', '🧪']}
EMO.update(EMO2)

# ---------------- timeline ----------------
SEGS = [('open', 3.6), ('morning', 6.0), ('skuchno', 2.0), ('lunch', 7.7), ('sport', 10.2), ('food', 5.4),
        ('lecture', 15.0), ('night', 7.6),
        ('c_title', 3.5), ('c_walk', 2.5), ('c_mono', 6.9), ('c_znaesh', 1.0), ('c_selfie', 3.5), ('c_sub', 2.6),
        ('c_evid', 2.0), ('c_energo', 4.2), ('c_fridge', 2.5),
        ('f_bam', 2.5), ('f_like', 1.6), ('f_end', 2.4)]
STARTS = {}; _t = 0
for k, d in SEGS: STARTS[k] = _t; _t += d
T_END = _t; N = int(round(T_END * FPS))
def seg_at(t):
    for k, d in SEGS:
        if t < STARTS[k] + d: return k, t - STARTS[k], d
    k, d = SEGS[-1]; return k, d - 1e-3, d

# pieces: (src_start, src_end, speed)
P_LUNCH = [(51.75, 52.75, 1), (53.0, 55.3, 1), (55.35, 57.35, 1), (59.9, 62.3, 1)]
P_SPORT = [(69.3, 73.8, 1), (73.9, 84.2, 5), (84.3, 87.95, 1)]
P_FOOD = [(88.2, 92.4, 1), (128.0, 129.2, 1)]
P_NIGHT = [(14.0, 17.9, 1), (17.9, 19.746, 1), (23.44, 25.285, 1)]
# lecture: (kind, s0, s1, speed)
P_LECT = [('A', 0.2, 2.2, 1), ('A', 3.75, 6.45, 1), ('A', 6.5, 10.35, 1), ('A', 13.0, 14.65, 1), ('G', 0, 0.8, 1),
          ('A', 14.75, 17.35, 1), ('E', 0.2, 1.36, 0.83)]
def pmap(pieces, tl):
    """-> (piece index, src time, local time in piece, piece out-duration)"""
    acc = 0
    for i, p in enumerate(pieces):
        s0, s1, sp = p[-3], p[-2], p[-1]
        d = (s1 - s0) / sp
        if tl < acc + d or i == len(pieces) - 1:
            u = tl - acc
            return i, s0 + u * sp, u, d
        acc += d
def pdur(pieces): return sum((p[-2] - p[-3]) / p[-1] for p in pieces)

# ---------------- frame sources (RGB 720x1280) ----------------
_cache = {}
def _load(path, key, fn=None):
    if key in _cache: return _cache[key]
    if len(_cache) > 250: _cache.pop(next(iter(_cache)))
    im = cv2.imread(path)
    im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    if fn: im = fn(im)
    _cache[key] = im
    return im
def cframe(t):
    i = int(np.clip(round(t * 30), 0, 4518))
    return _load(os.path.join(HERE, 'fc', f'{i+1:05d}.jpg'), ('c', i), lambda im: cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC))
def aframe(t):
    i = int(np.clip(round(t * 30), 0, 608)); return _load(os.path.join(HERE, 'fa', f'{i+1:04d}.jpg'), ('a', i))
def eframe(t):
    i = int(np.clip(round(max(t, 0.36) * 120), 0, 163))
    def fx(im):
        im = im[75:750]  # 384x675
        s = max(W / im.shape[1], H / im.shape[0]); im = cv2.resize(im, (int(im.shape[1] * s) + 1, int(im.shape[0] * s) + 1), interpolation=cv2.INTER_CUBIC)
        y0 = (im.shape[0] - H) // 2; x0 = (im.shape[1] - W) // 2
        return im[y0:y0 + H, x0:x0 + W]
    return _load(os.path.join(HERE, 'fe', f'{i+1:04d}.jpg'), ('e', i), fx)
def sframe(t):
    i = int(np.clip(round(t * 30), 0, 452)); return _load(os.path.join(HERE, 'fs', f'{i+1:04d}.jpg'), ('s', i))
def nframe(t):
    i = int(np.clip(round(t * 30), 0, 959)); return _load(os.path.join(HERE, 'fn', f'{i+1:04d}.jpg'), ('n', i))
def v1frame(t):
    return cv2.cvtColor(R.src_frame(t * 30), cv2.COLOR_BGR2RGB)

def cover(im, cx=None, cy=None):
    h, w = im.shape[:2]; s = max(W / w, H / h)
    im = cv2.resize(im, (int(w * s + 0.999), int(h * s + 0.999)), interpolation=cv2.INTER_AREA if s < 1 else cv2.INTER_CUBIC)
    h, w = im.shape[:2]
    x0 = int(np.clip((cx * s if cx is not None else w / 2) - W / 2, 0, w - W)); y0 = int(np.clip((cy * s if cy is not None else h / 2) - H / 2, 0, h - H))
    return im[y0:y0 + H, x0:x0 + W].copy()
def rd(p): return cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
IMG_SELFIE_RAW = rd(UP + 'f6ffa779-image.jpg')
IMG_SKUCHNO = cover(rd(UP + '774f5107-image.jpg')[110:1165])
IMG_GLASSES = cover(rd(UP + 'a338e5ee-image.jpg')[115:860])
IMG_BILL = cover(rd(UP + 'f8b2873e-image.jpg'))
# selfie framed on the face (9:16 crop)
_s = IMG_SELFIE_RAW[0:1956, 310:1410]
IMG_SELFIE = cv2.resize(_s, (W, H), interpolation=cv2.INTER_AREA)
SC = W / 1100
SEYE = [((784 - 310) * SC, 810 * SC), ((936 - 310) * SC, 798 * SC)]
SMOUTH = ((875 - 310) * SC, 985 * SC)

# ---------------- image fx ----------------
def zoomc(img, s, cx=W / 2, cy=H / 2, dx=0, dy=0, rot=0):
    if abs(s - 1) < 1e-3 and dx == 0 and dy == 0 and rot == 0: return img
    M = cv2.getRotationMatrix2D((cx, cy), rot, s); M[0, 2] += dx; M[1, 2] += dy
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
def rgbsplit(img, d):
    d = int(d)
    if d < 1: return img
    o = img.copy(); o[..., 0] = np.roll(img[..., 0], d, 1); o[..., 2] = np.roll(img[..., 2], -d, 1); return o
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_VIG = np.clip(1 - 1.15 * (np.sqrt(((_XX - W / 2) / (W / 2)) ** 2 + ((_YY - H / 2) / (H / 2)) ** 2) - 0.45), 0.08, 1)[..., None]
def creepy(img, t, amt=1.0, tint=(0.75, 0.9, 1.1)):
    x = img.astype(np.float32)
    g = x.mean(2, keepdims=True)
    x = g + (x - g) * (1 - 0.8 * amt)
    x = (x - 30) * 1.25
    x = x * np.array(tint, np.float32)
    x = x * (1 - amt + amt * _VIG)
    rng = np.random.default_rng(int(t * 997))
    x += rng.normal(0, 14 * amt, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    x[::3] *= (1 - 0.18 * amt)
    if rng.random() < 0.08 * amt: x *= rng.uniform(0.5, 0.8)
    return np.clip(x, 0, 255).astype(np.uint8)
def warp_face(img, eyes, mouth, eye_amt, smile_amt, eye_r=55):
    mx = _XX.copy(); my = _YY.copy()
    for ex, ey in eyes:
        dx, dy = _XX - ex, _YY - ey; r = np.sqrt(dx * dx + dy * dy)
        m = np.clip(1 - r / eye_r, 0, 1) ** 2 * eye_amt
        mx -= dx * m; my -= dy * m
    cx, cy = mouth
    wgt = np.exp(-(((_XX - cx) / 90) ** 2 + ((_YY - cy) / 45) ** 2)) * smile_amt
    mx -= (_XX - cx) * wgt * 0.55
    my += np.abs(_XX - cx) / 90 * wgt * -14  # corners pulled up
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def black_eyes(img, eyes, r=34, amt=1.0):
    m = np.zeros((H, W), np.float32)
    for ex, ey in eyes: cv2.ellipse(m, (int(ex), int(ey)), (int(r * 1.15), int(r * 0.8)), 0, 0, 360, 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), 7)[..., None] * amt
    return (img * (1 - m * 0.97)).astype(np.uint8)
def invert_red(img):
    x = 255 - img; x = x.astype(np.float32); g = x.mean(2)
    return np.clip(np.stack([g * 1.3, g * 0.15, g * 0.15], -1), 0, 255).astype(np.uint8)

def P(img): return Image.fromarray(img).convert('RGBA')
def flash(c, a, col=(255, 255, 255)):
    if a > 0: c.alpha_composite(Image.new('RGBA', (W, H), col + (int(255 * min(1, a)),)))
def bpunch(tl, bpm=130, amt=1.0, dec=0.09, off=0.0):
    b = 60 / bpm; p = (tl - off) % b
    return amt * math.exp(-p / dec) if tl >= off else 0

def chapter(c, tl, txt, dur=1.0):
    if tl > dur: return
    a = ease_pop(tl, 0, 0.15)
    im = text_img(txt, 46, BLACK, NEON, 0)
    bg = Image.new('RGBA', (im.width + 30, im.height + 6), NEON + (255,)); bg.alpha_composite(im, (15, 3))
    paste(c, bg, 40 + bg.width / 2 * a, 150, a, -2)

def his_sub(c, ru_lines, hi, en, y=900, en_col=(60, 255, 60)):
    """subtitle in the blogger's style: white bold lines on dark box, highlighted word yellow, green english below"""
    fo = font(F_BLACK, 40)
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    yy = y; wi = 0
    for line in ru_lines:
        words = line.split(' ')
        widths = [d0.textlength(w_ + ' ', font=fo) for w_ in words]
        lw = sum(widths); x = W / 2 - lw / 2
        d = ImageDraw.Draw(c)
        d.rounded_rectangle([x - 14, yy - 8, x + lw + 4, yy + 50], 8, fill=(30, 30, 30, 200))
        for w_, ww in zip(words, widths):
            if wi == hi:
                d.rounded_rectangle([x - 6, yy - 4, x + ww - 6, yy + 48], 12, fill=(0, 0, 0, 255))
                d.text((x, yy), w_, font=fo, fill=(255, 210, 40))
            else:
                d.text((x, yy), w_, font=fo, fill=WHITE)
            x += ww; wi += 1
        yy += 58
    ImageDraw.Draw(c).text((W / 2, yy + 18), en, font=font(F_BLACK, 28), fill=en_col, anchor='mm', stroke_width=3, stroke_fill=BLACK)

def osd(c, t, day=848):
    d = ImageDraw.Draw(c)
    if int(t * 2) % 2 == 0: d.ellipse([40, 62, 66, 88], fill=(220, 0, 0))
    d.text((80, 75), f'REC  ДЕНЬ {day}', font=font(F_MONO, 30), fill=(230, 230, 230), anchor='lm')
    s = int(t * 100)
    d.text((W - 40, 75), f'{(s//6000)%24+3:02d}:{(s//100)%60:02d}:{s%100:02d}', font=font(F_MONO, 28), fill=(230, 230, 230), anchor='rm')

def typewriter(c, txt, tl, t0, cps, y, size=44, col=(235, 235, 235)):
    n = int(max(0, (tl - t0)) * cps)
    if n <= 0: return
    s = txt[:n]
    cur = '▌' if int(tl * 3) % 2 == 0 and n < len(txt) + 6 else ''
    ImageDraw.Draw(c).text((W / 2, y), s + cur, font=font(F_MONO, size), fill=col, anchor='mm')

def label_rows(c, tl, rows, t_each, title, x=60, y=760, w=600, rot=-3):
    n = sum(1 for i in range(len(rows)) if tl >= i * t_each)
    if n <= 0: return
    rh = 50
    box = Image.new('RGBA', (w, 70 + rh * n), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
    d.rectangle([0, 0, w - 1, 70 + rh * n - 1], fill=(255, 255, 255, 248), outline=BLACK, width=5)
    d.text((16, 12), title, font=font(F_BLACK, 36), fill=BLACK)
    d.rectangle([10, 60, w - 10, 64], fill=BLACK)
    for i, (k, v, red) in enumerate(rows[:n]):
        yy = 72 + i * rh
        d.text((18, yy), k, font=font(F_BLACK, 30), fill=BLACK)
        d.text((w - 18, yy), v, font=font(F_BLACK, 30), fill=(220, 0, 30) if red else BLACK, anchor='ra')
    paste(c, box, x + w / 2, y + box.height / 2, ease_pop(tl, 0, 0.2), rot)

def stamp(c, txt, cx, cy, tl, t0, rot=-12, col=(230, 20, 40), size=64):
    s = ease_pop(tl, t0, 0.12)
    if s <= 0: return
    im = text_img(txt, size, col, (255, 255, 255), 0)
    fr = Image.new('RGBA', (im.width + 30, im.height + 20), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rounded_rectangle([3, 3, fr.width - 4, fr.height - 4], 10, outline=col + (255,), width=7)
    fr.alpha_composite(im, (15, 10))
    paste(c, fr, cx, cy, s * (1 + 0.6 * max(0, 1 - (tl - t0) / 0.12)), rot, 0.92)

def hearts(c, tl, n, seed):
    R.rain(c, tl + 0.0, 0, 1.4, [EMO['❤️'], EMO['👍'], EMO['❤️']], n, seed, (60, 120), (-1800, -1000))

# ---------------- VIDEO ----------------
def render(fi):
    t = fi / FPS
    key, tl, dur = seg_at(t)
    rng = random.Random(fi * 7717)
    c = None

    if key == 'open':
        if tl < 1.6:
            if tl < 0.6:
                st = 0.26 + (tl % 0.15); k = int(tl / 0.15)
                img = eframe(st)
                img = zoomc(img, 1.0 + 0.12 * k + 0.25 * math.exp(-(tl % 0.15) / 0.05))
                img = rgbsplit(img, 30 * math.exp(-(tl % 0.15) / 0.04))
                if k % 2: img = hue_rgb(img, 120 * k, 1.6)
            else:
                st = 0.26 + (tl - 0.6); img = eframe(st)
                img = zoomc(img, 1.08 + bpunch(tl, 130, 0.12, 0.08, 0.6))
            c = P(img)
            if tl < 0.6:
                paste(c, text_img('ЭН-', 170, NEON, BLACK, 14), W / 2 + rng.uniform(-10, 10), 640 + rng.uniform(-10, 10), 1 + 0.1 * (int(tl / 0.15)), rng.uniform(-8, 8))
            else:
                st = 0.26 + (tl - 0.6)
                if st > 0.3: paste(c, text_img('ЭНЕРГОСИК', 118, NEON, BLACK, 12), W / 2, 520, ease_pop(st, 0.3, 0.14), -4)
                if st > 0.84: paste(c, text_img('В РОТИК', 140, WHITE, BLACK, 14), W / 2, 680, ease_pop(st, 0.84, 0.14), 3)
        else:
            u = tl - 1.6
            z = 1 + 1.6 * (1 - min(1, u / 0.55)) ** 3 + 0.02 * u
            img = zoomc(IMG_BILL, z, 520 - 66, 330)
            img = rgbsplit(img, 25 * math.exp(-u / 0.1))
            c = P(img)
            flash(c, 1 - u / 0.15)
            if u > 0.45: paste(c, text_img('ВЕСЬ МИР ЖДАЛ ЭТОГО', 60, WHITE, BLACK, 7), W / 2, 140, ease_pop(u, 0.45, 0.15))
            if u > 1.0:
                paste(c, text_img('ЭНЕРГИЧНЫЙ', 104, NEON, BLACK, 11), W / 2, 1110, ease_pop(u, 1.0, 0.18) * (1 + bpunch(u, 130, 0.06)), -3)
                paste(c, text_img('ВСЕЛЕННАЯ', 70, WHITE, BLACK, 8), W / 2, 1215, ease_pop(u, 1.15, 0.18), 2)

    elif key == 'morning':
        c = P(sframe(2.07 + tl))
        chapter(c, tl, 'ГЛАВА 1 · УТРО')

    elif key == 'skuchno':
        k = min(3, int(tl / 0.5)); ph = tl - k * 0.5
        z = [1.0, 1.45, 2.1, 3.0][k] * (1 + 0.12 * math.exp(-ph / 0.08))
        img = zoomc(IMG_SKUCHNO, z, 404, 424, rng.uniform(-6, 6) * k, rng.uniform(-6, 6) * k)
        img = rgbsplit(img, 6 + 20 * math.exp(-ph / 0.06))
        if k == 3: img = _fry(img, 0.6)
        c = P(img)
        txt = ['ЕМУ СКУЧНО', 'ИДТИ НА РАБОТУ', 'ПОЭТОМУ ОН\nСНИМАЕТ ЭТО', 'КАЖДЫЙ.\nДЕНЬ.'][k]
        paste(c, text_img(txt, 96, NEON if k % 2 else WHITE, BLACK, 10, spacing=-6), W / 2, 950, ease_pop(ph, 0, 0.1), rng.uniform(-3, 3))
        day = int(1 + 847 * min(1, (tl / 1.9) ** 2))
        d = ImageDraw.Draw(c)
        d.rounded_rectangle([W / 2 - 170, 120, W / 2 + 170, 190], 12, fill=(0, 0, 0, 200))
        d.text((W / 2, 155), f'ДЕНЬ {day}', font=font(F_MONO, 44), fill=RED, anchor='mm')

    elif key == 'lunch':
        i, st, u, pd = pmap(P_LUNCH, tl)
        img = cframe(st)
        img = zoomc(img, 1.04 + bpunch(tl, 130, 0.06) + (0.15 * u / pd if i == 3 else 0))
        c = P(img)
        chapter(c, tl, 'ГЛАВА 2 · ОБЕД', 1.2)
        d = ImageDraw.Draw(c)
        R.bar(d, 24, 210, 300, 34, 1.0, RED, 'ГОЛОД', '100%' if int(tl * 6) % 2 else '!!!', int(tl * 6) % 2 == 0)
        if i == 1 and st > 54.75:
            kk = text_img('КАЙФ', 190, NEON, BLACK, 16)
            paste(c, kk.rotate(0), W / 2, 560, ease_pop(st, 54.75, 0.12) * (1 + 0.1 * math.sin(tl * 30)), rng.uniform(-5, 5))
        if i == 2:
            R.rain(c, u, 0.0, 1.6, [EMO['🥟'], EMO['🍜'], EMO['🍝'], EMO['🥟']], 18, 91, (70, 120), (700, 1100))
        if i == 3:
            b = text_img('📢 ОБРАЩЕНИЕ К НАРОДУ', 50, WHITE, BLACK, 6, f=F_BLACK)
            b = text_img('ОБРАЩЕНИЕ К НАРОДУ', 54, WHITE, (200, 0, 0), 7)
            paste(c, b, W / 2, 300, ease_pop(u, 0, 0.15), -2)
            paste(c, EMO['📢'], W / 2, 410, 0.7 * ease_pop(u, 0.1, 0.15), 10 * math.sin(tl * 9))

    elif key == 'sport':
        i, st, u, pd = pmap(P_SPORT, tl)
        img = cframe(st)
        if i == 1:
            img = zoomc(img, 1.05 + bpunch(tl, 130 * 2, 0.05, 0.06), dx=rng.uniform(-6, 6), dy=rng.uniform(-6, 6))
            img = hue_rgb(img, 0, 1.6)
        elif i == 2:
            img = zoomc(img, 1.0 + 0.25 * min(1, u / 2.5) + (0.15 if st > 86.45 and st < 87.3 else 0))
        else:
            img = zoomc(img, 1.03 + bpunch(tl, 130, 0.05))
        c = P(img)
        chapter(c, tl, 'ГЛАВА 3 · СПОРТ', 1.2)
        if i == 0 and st > 71.75:
            paste(c, text_img('РЕЖИМ: КАЧОК', 92, NEON, BLACK, 10), W / 2, 330, ease_pop(st, 71.75, 0.15), -4)
            paste(c, EMO['💪'], W / 2, 470, 0.9 * ease_pop(st, 71.9, 0.15), math.sin(tl * 12) * 15)
        if i == 1:
            el = st - 73.9
            d = ImageDraw.Draw(c)
            d.rounded_rectangle([W / 2 - 200, 240, W / 2 + 200, 360], 16, fill=(0, 0, 0, 200), outline=NEON, width=5)
            d.text((W / 2, 300), f'00:{int(el):02d}.{int(el*10)%10}', font=font(F_MONO, 80), fill=NEON, anchor='mm')
            d.text((W / 2, 410), '▶▶ x5', font=font(F_SYM, 50), fill=WHITE, anchor='mm', stroke_width=4, stroke_fill=BLACK)
            kc = el * 0.04
            paste(c, text_img(f'СОЖЖЕНО: {kc:.2f} ККАЛ', 52, (255, 150, 40), BLACK, 6), W / 2, 1150)
            paste(c, EMO['🔥'], 120, 1050, 0.6, rng.uniform(-10, 10)); paste(c, EMO['🔥'], W - 120, 1050, 0.6, rng.uniform(-10, 10))
            paste(c, text_img('ТРЕНИРОВКА\nЧЕМПИОНА', 84, WHITE, BLACK, 9, spacing=-6), W / 2, 560, 1 + bpunch(tl, 260, 0.08, 0.06), rng.uniform(-3, 3))
        if i == 2:
            if u < 0.08: flash(c, 1 - u / 0.08)
            stamp(c, 'ТРЕНИРОВКА ОКОНЧЕНА', W / 2, 260, u, 0.0, -6, (230, 20, 40), 50)
            if u > 0.45 and st < 87.2: paste(c, text_img('ДЛИТЕЛЬНОСТЬ: 10 СЕК', 50, WHITE, BLACK, 6), W / 2, 380, ease_pop(u, 0.45, 0.15))
            if st > 86.45:
                paste(c, text_img('НУ ЕГО\nНАФИГ', 140, NEON, BLACK, 14, spacing=-10), W / 2, 620, ease_pop(st, 86.45, 0.12) * (1 + 0.05 * math.sin(tl * 25)), rng.uniform(-6, 6))
            if st > 87.2:
                paste(c, EMO['🏆'], W - 110, 880, 0.9 * ease_pop(st, 87.2, 0.15), 10)
                paste(c, text_img('НОВЫЙ РЕКОРД', 60, (255, 210, 40), BLACK, 7), W / 2, 380, ease_pop(st, 87.2, 0.15))

    elif key == 'food':
        i, st, u, pd = pmap(P_FOOD, tl)
        img = cframe(st)
        if i == 0:
            img = zoomc(img, 1.05 + 0.2 * u / pd + bpunch(tl, 130, 0.06), 360, 700)
            img = hue_rgb(img, 0, 1.4)
        else:
            img = zoomc(img, 1.2 + 0.4 * u, 300, 400, rng.uniform(-8, 8), rng.uniform(-8, 8))
        c = P(img)
        chapter(c, tl, 'ГЛАВА 3½ · ПИТАНИЕ', 1.2)
        if i == 0:
            label_rows(c, u - 0.4, [('Макароны', '31%', False), ('Кетчуп', '69%', False), ('Овощи', 'НЕТ', True),
                                    ('Сон после еды', 'ОБЯЗАТЕЛЕН', True)], 0.45, 'ПИЩЕВАЯ ЦЕННОСТЬ:', 60, 230, 600, -3)
        else:
            paste(c, text_img('*переваривает*', 80, WHITE, BLACK, 9, f=F_BLACKI), W / 2, 1050, ease_pop(u, 0, 0.15), -4)

    elif key == 'lecture':
        i, st, u, pd = pmap(P_LECT, tl)
        kind = P_LECT[i][0]
        if kind == 'A':
            img = aframe(st)
            img = zoomc(img, 1.03 + bpunch(tl, 130, 0.04))
            if i == 3: img = hue_rgb(img, (u * 300) % 360, 1.3)
        elif kind == 'G':
            img = zoomc(IMG_GLASSES, 1.15 - 0.1 * u, 369, 550, rng.uniform(-5, 5), rng.uniform(-5, 5))
            img = _fry(img, 0.3)
        else:
            img = eframe(st)
            img = hue_rgb(img, (u * 600) % 360, 1.8)
            img = zoomc(img, 1.05 + bpunch(u, 130, 0.1, 0.07))
        c = P(img)
        if kind == 'A':
            d = ImageDraw.Draw(c)
            d.rectangle([0, 40, W, 112], fill=(20, 60, 40, 235)); d.rectangle([0, 112, W, 118], fill=(150, 100, 40, 255))
            d.text((W / 2, 76), 'ЛЕКЦИЯ · ПРОФ. ЭНЕРГИЧНЫЙ', font=font(F_BLACK, 38), fill=WHITE, anchor='mm')
        if i == 0:
            chapter(c, tl, 'ГЛАВА 4 · НАУКА', 1.4)
            if st > 1.2: paste(c, EMO['🔮'], W - 110, 330, 0.7 * ease_pop(st, 1.2, 0.15), math.sin(tl * 5) * 10)
        if i == 1:
            paste(c, text_img('אַבְּרָא כְּדַבְּרָא', 70, (255, 230, 150), BLACK, 6, f=F_SYM), W / 2, 260, ease_pop(u, 0.3, 0.2))
            stamp(c, 'ИСТОЧНИК:\nМАМОЙ КЛЯНУСЬ', W / 2, 480, u, 1.0, -8, (230, 20, 40), 46)
        if i == 2:
            board = Image.new('RGBA', (620, 230), (0, 0, 0, 0)); bd = ImageDraw.Draw(board)
            bd.rectangle([0, 0, 619, 229], fill=(25, 55, 40, 240), outline=(150, 100, 40, 255), width=10)
            if st >= 7.95: bd.text((30, 40), 'АБРА = я создам', font=font(F_BLACKI, 50), fill=(245, 245, 235))
            if st >= 8.75: bd.text((30, 130), 'КАДАБРА = как говорю', font=font(F_BLACKI, 46), fill=(245, 245, 235))
            paste(c, board, W / 2, 290, ease_pop(u, 0, 0.2), -1)
        if i == 3:
            R.rain(c, u, 0, 1.4, [CAN, EMO['✨'], CAN2, EMO['⚡']], 18, 17, (80, 150), (-1900, -1200))
            paste(c, text_img('МАГИЯ ТАУРИНА', 88, NEON, (90, 0, 160), 10), W / 2, 300, ease_pop(u, 0, 0.15) * (1 + 0.05 * math.sin(tl * 25)), -3)
        if kind == 'G':
            if u < 0.06: flash(c, 1 - u / 0.06)
            paste(c, text_img('ДЕЛАЮ\nЧТО ХОЧУ', 130, WHITE, BLACK, 13, spacing=-8), W / 2, 1000, ease_pop(u, 0, 0.1), -5)
            paste(c, EMO['😎'], W - 120, 200, 0.9, 15)
        if i == 5:
            d = ImageDraw.Draw(c)
            p = min(1, u / (pd - 0.2))
            d.rounded_rectangle([60, 250, W - 60, 330], 14, fill=(0, 0, 0, 210), outline=WHITE, width=4)
            d.rounded_rectangle([70, 260, 70 + (W - 140) * p, 320], 10, fill=NEON)
            d.text((W / 2, 290), f'ПЕРЕВОД НА ЗУМЕРСКИЙ… {int(p*100)}%', font=font(F_MONO, 30), fill=WHITE, anchor='mm', stroke_width=3, stroke_fill=BLACK)
        if kind == 'E':
            if u < 0.08: flash(c, 1 - u / 0.08)
            paste(c, text_img('АБРАКАДАБРА =', 90, WHITE, BLACK, 10), W / 2, 200, ease_pop(u, 0, 0.12), -3)
            if st > 0.3: paste(c, text_img('ЭНЕРГОСИК', 124, NEON, BLACK, 13), W / 2, 960, ease_pop(st, 0.3, 0.1))
            if st > 0.84: paste(c, text_img('В РОТИК', 124, NEON, BLACK, 13), W / 2, 1100, ease_pop(st, 0.84, 0.1))
            stamp(c, 'НАУЧНО\nДОКАЗАНО', 560, 400, u, 0.5, 14, (230, 20, 40), 44)

    elif key == 'night':
        i, st, u, pd = pmap(P_NIGHT, tl)
        c = P(nframe(st))
        chapter(c, tl, 'ГЛАВА 5 · НОЧЬ', 1.0)

    # ===================== CREEPYPASTA =====================
    elif key == 'c_title':
        c = Image.new('RGBA', (W, H), (0, 0, 0, 255))
        arr = np.array(c.convert('RGB')); arr = creepy(arr + 8, t, 1.0); c = P(arr)
        typewriter(c, 'Он снимает это', tl, 0.25, 16, 540)
        typewriter(c, 'каждый день.', tl, 1.25, 16, 600)
        typewriter(c, '848 дней подряд.', tl, 2.2, 18, 720, 48, (220, 40, 40))
        if 3.1 < tl < 3.17:
            c = P(black_eyes(IMG_SELFIE, SEYE, 36))

    elif key == 'c_walk':
        st = 0.3 + tl * 0.4
        img = creepy(v1frame(st), t, 0.9)
        sub = (0.95 < tl < 1.02) or (1.95 < tl < 2.02)
        if sub: img = black_eyes(warp_face(IMG_SELFIE, SEYE, SMOUTH, 0.35, 0.8), SEYE, 36)
        c = P(img); osd(c, t)
        d = ImageDraw.Draw(c)
        steps = 2517 + int(tl * 1.6)
        d.rounded_rectangle([24, H - 140, 470, H - 80], 8, fill=(0, 0, 0, 190))
        d.text((44, H - 110), f'ДО РАБОТЫ: {steps} ШАГ. ↑', font=font(F_MONO, 28), fill=(220, 60, 60), anchor='lm')
        typewriter(c, 'он идёт на работу.', tl, 0.3, 14, 1000, 38)
        typewriter(c, 'он всегда идёт на работу.', tl, 1.4, 16, 1050, 38)

    elif key == 'c_mono':
        st = 35.0 + tl * 0.9
        img = cframe(st)
        if st > 37.85:
            ghost = cframe(st - 0.25)
            img = cv2.addWeighted(img, 0.6, ghost, 0.4, 0)
        img = zoomc(img, 1.0 + 0.22 * tl / 6.9, W / 2, 520)
        img = creepy(img, t, 0.85, (0.8, 0.95, 1.15))
        if rng.random() < 0.06: img = glitch_slices(img, rng, 5, 40)
        c = P(img); osd(c, t)
        if st > 37.85 and int(tl * 7) % 5 == 0:
            for j in range(3):
                ImageDraw.Draw(c).text((W / 2 + rng.uniform(-60, 60), 300 + j * 70 + rng.uniform(-10, 10)), 'растворились в ночи', font=font(F_MONO, 40), fill=(200, 0, 0, 160), anchor='mm')

    elif key == 'c_znaesh':
        st = 27.9 + tl
        img = invert_red(cframe(st))
        img = zoomc(img, 1.15 + 0.3 * tl, W / 2, 600, rng.uniform(-25, 25), rng.uniform(-25, 25))
        img = glitch_slices(img, rng, 10, 120)
        c = P(img)
        if tl < 0.05: flash(c, 1)
        paste(c, text_img('ЗНАЕШЬ ЧЁ', 120, (255, 255, 255), (150, 0, 0), 12), W / 2 + rng.uniform(-10, 10), 900, 1 + 0.2 * tl, rng.uniform(-6, 6))

    elif key == 'c_selfie':
        u = tl / dur
        img = warp_face(IMG_SELFIE, SEYE, SMOUTH, 0.05 + 0.4 * u ** 1.5, 0.15 + 1.3 * u ** 1.5)
        if u > 0.75: img = black_eyes(img, SEYE, 36, min(1, (u - 0.75) / 0.1))
        cx, cy = SMOUTH[0], 700
        img = zoomc(img, 1.0 + 0.55 * u ** 1.2, cx, cy)
        img = creepy(img, t, 0.7, (1.05, 0.9, 0.85))
        c = P(img); osd(c, t)
        words = ['хорошего', 'вечера']
        hi = 0 if tl < 1.4 else 1
        en = 'have a good evening' if u < 0.6 else ('have a good evening have a good' if u < 0.8 else 'the evening never ends')
        his_sub(c, ['хорошего вечера'], hi, en, 1020, (60, 255, 60) if u < 0.8 else (255, 40, 40))

    elif key == 'c_sub':
        st = 96.9 + tl * 0.8
        img = cframe(st)
        img = zoomc(img, 1.15 + 0.15 * tl / dur, W / 2, 600)
        img = creepy(img, t, 0.8, (1.1, 0.85, 0.85))
        c = P(img); osd(c, t)
        typewriter(c, 'он знает, что ты не подписан.', tl, 0.4, 20, 300, 34, (230, 50, 50))

    elif key == 'c_evid':
        st = 145.0 + tl * 0.3
        img = cframe(st)
        u = tl / dur
        z = 1 + 0.8 * min(1, u * 1.5)
        cx, cy = 150, 480
        img = zoomc(img, z, cx, cy)
        img = creepy(img, t, 0.75, (1.0, 0.95, 0.9))
        c = P(img); osd(c, t)
        d = ImageDraw.Draw(c)
        def tr(x, y): return (cx + (x - cx) * z, cy + (y - cy) * z)
        if tl > 0.5:
            x, y = tr(235, 553); d.ellipse([x - 55, y - 80, x + 55, y + 80], outline=(230, 30, 30), width=6)
            d.text((x + 70, y), 'УЛИКА №1', font=font(F_MONO, 30), fill=(230, 30, 30), anchor='lm', stroke_width=3, stroke_fill=BLACK)
        if tl > 1.0:
            x, y = tr(72, 287); d.ellipse([x - 75, y - 70, x + 75, y + 70], outline=(230, 30, 30), width=6)
            d.text((x + 90, y - 10), 'УЛИКА №2', font=font(F_MONO, 30), fill=(230, 30, 30), anchor='lm', stroke_width=3, stroke_fill=BLACK)
        typewriter(c, 'банки. везде банки.', tl, 0.3, 14, 1080, 40)

    elif key == 'c_energo':
        if tl < 3.03:
            st = 0.26 + tl / 3
            img = eframe(st)
            img = zoomc(img, 1.1 + 0.25 * tl / 3, W / 2, 520)
            img = creepy(img, t, 0.9, (1.15, 0.75, 0.75))
            if tl > 1.8: img = black_eyes(img, [(305, 470), (425, 470)], 30, min(1, (tl - 1.8) / 0.3)) if False else img
            c = P(img); osd(c, t)
            typewriter(c, 'он желает вам всего хорошего.', tl, 0.3, 22, 260, 34)
            typewriter(c, 'каждый день.', tl, 1.8, 16, 320, 34, (230, 50, 50))
        else:
            u = tl - 3.03
            img = IMG_BILL.astype(np.float32) * (0.35 + 0.3 * (rng.random() < 0.7))
            img = creepy(img.astype(np.uint8), t, 0.8, (0.8, 0.9, 1.2))
            c = P(img)
            d = ImageDraw.Draw(c)
            d.rectangle([130 - 66, 760, 740 - 66, 1060], fill=(5, 5, 10, 255))
            if rng.random() < 0.85:
                d.text((W / 2 + 10, 850), 'ХОРОШЕГО', font=font(F_BLACKI, 96), fill=(240, 240, 240), anchor='mm')
                d.text((W / 2 + 10, 975), 'ВЕЧЕРА', font=font(F_BLACKI, 110), fill=(255, 190, 0), anchor='mm')
            osd(c, t)

    elif key == 'c_fridge':
        c = P(creepy(np.full((H, W, 3), 6, np.uint8), t, 1.0))
        typewriter(c, 'проверьте холодильник.', tl, 0.3, 16, 620, 46)
        if tl > 1.95: typewriter(c, '*пшшш*', tl, 1.95, 30, 760, 40, (120, 120, 120))

    # ===================== FINALE =====================
    elif key == 'f_bam':
        st = 0.2 + tl if tl < 1.16 else 0.82 + ((tl - 1.16) % 0.45)
        img = eframe(st)
        img = hue_rgb(img, (tl * 900) % 360, 2.0)
        img = zoomc(img, 1.1 + bpunch(tl, 130, 0.18, 0.07), dx=rng.uniform(-15, 15), dy=rng.uniform(-15, 15))
        img = rgbsplit(img, 15 + 20 * bpunch(tl, 130, 1, 0.06))
        c = P(img)
        # clone tiles of everything
        thumbs = [IMG_SELFIE, IMG_SKUCHNO, IMG_GLASSES, IMG_BILL, aframe(7.0), cframe(16.0), cframe(85.5), nframe(16.5)]
        k = int(tl / (60 / 130))
        for j in range(4):
            th = thumbs[(k + j * 2) % len(thumbs)]
            ti = Image.fromarray(cv2.resize(th, (180, 320))).convert('RGBA')
            pos = [(110, 180), (W - 110, 180), (110, H - 180), (W - 110, H - 180)][j]
            paste(c, ti, pos[0], pos[1], 1 + 0.15 * bpunch(tl, 130, 1, 0.08), (-1) ** j * 8)
        if tl < 0.06: flash(c, 1)
        paste(c, text_img('ЭНЕРГОСИК\nВ РОТИК!!!', 132, NEON, BLACK, 14, spacing=-10), W / 2 + rng.uniform(-8, 8), 640 + rng.uniform(-8, 8), 1 + bpunch(tl, 130, 0.12, 0.08), rng.uniform(-5, 5))
        R.rain(c, tl, 0, 2.2, [CAN, CAN2, EMO['⚡'], EMO['🥟']], 24, 303, (80, 160), (1500, 2500))

    elif key == 'f_like':
        st = 23.1 + tl
        img = zoomc(cframe(st), 1.15 + bpunch(tl, 130, 0.05), W / 2, 560)
        c = P(img)
        r2 = random.Random(404)
        for j in range(26):
            t0_ = r2.uniform(0, 1.2); x0 = r2.uniform(40, W - 40); v = r2.uniform(700, 1300); sz = r2.uniform(60, 120)
            if tl > t0_:
                y = H + 80 - v * (tl - t0_)
                paste(c, EMO['❤️'] if j % 3 else EMO['👍'], x0 + 30 * math.sin(tl * 4 + j), y, sz / 150, 15 * math.sin(tl * 5 + j))
        paste(c, EMO['👍'], W - 150, 300, 1.2 * ease_pop(tl, 0.3, 0.15), math.sin(tl * 10) * 10)

    elif key == 'f_end':
        c = R2.rays(t, [(25, 25, 35), (12, 12, 18)], 20, 15)
        paste(c, text_img('ЭНЕРГИЧНЫЙ', 116, NEON, BLACK, 12), W / 2, 520, ease_pop(tl, 0.05, 0.2), -3)
        paste(c, text_img('ВСЕЛЕННАЯ', 80, WHITE, BLACK, 9), W / 2, 650, ease_pop(tl, 0.2, 0.2), 2)
        paste(c, CAN, W / 2, 870, 1.1 * ease_pop(tl, 0.3, 0.2), math.sin(tl * 4) * 12)
        if tl > 0.6: paste(c, text_img('день 848 · хорошего вечера :)', 40, (220, 220, 220), BLACK, 4), W / 2, 1080, ease_pop(tl, 0.6, 0.2))
        ImageDraw.Draw(c).text((W / 2, H - 60), 'оригинал: @bor.edka', font=font(F_MONO, 22), fill=(160, 160, 160), anchor='mm')
        if dur - tl < 0.5:
            if dur - tl < 0.18:
                c = P(black_eyes(warp_face(IMG_SELFIE, SEYE, SMOUTH, 0.4, 1.4), SEYE, 36))
            else:
                flash(c, (0.5 - (dur - tl)) / 0.32, (0, 0, 0))

    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def load_wav(p):
    w = wave.open(p); sr = w.getframerate(); ch = w.getnchannels()
    a = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32) / 32768
    if ch == 2: a = a.reshape(-1, 2).mean(1)
    if sr != SR: a = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a).astype(np.float32)
    return a

def build_audio(out):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(7)
    A = {k: load_wav(os.path.join(HERE, f'au_{k}.wav')) for k in 'caens'}
    A['v1'] = load_wav(os.path.join(HERE, 'v1.wav'))
    VO = {k: load_wav(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['w1', 'w2', 'w3', 'w4', 'w5']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(src, s0, s1, speed=1.0, fade=0.006):
        a = A[src] if isinstance(src, str) else src
        m = int((s1 - s0) / speed * SR)
        pos = s0 * SR + np.arange(m) * speed
        x = np.interp(pos, np.arange(len(a)), a).astype(np.float32)
        f = int(fade * SR)
        if f and len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def pieces(src, pcs, t0, g=1.0):
        acc = 0
        for p in pcs:
            s0, s1, sp = p[-3], p[-2], p[-1]
            add(t0 + acc, clip(src, s0, s1, sp), g); acc += (s1 - s0) / sp
    def tt(d): return np.arange(int(d * SR)) / SR
    def boom(d=1.0, f0=130):
        t = tt(d); f = f0 * np.exp(-t * 5) + 38
        return np.tanh(2.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)).astype(np.float32)
    def whoosh(d=0.35):
        t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2
        return np.convolve(x, np.ones(6) / 6, 'same').astype(np.float32) * 0.5
    def scratch():
        t = tt(0.35); f = 400 + 1800 * np.abs(np.sin(2 * np.pi * 4 * t))
        return (0.4 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * rng.standard_normal(len(t)) * 0.6 * np.exp(-t * 4)).astype(np.float32)
    def stab():
        t = tt(0.9)
        x = np.tanh(4 * (rng.standard_normal(len(t)) * 0.6 + np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 58 * t))) * np.exp(-t * 3)
        return x.astype(np.float32)
    def pshh():
        t = tt(0.45); x = np.diff(np.concatenate([[0], rng.standard_normal(len(t))])); return (0.55 * x * np.exp(-t * 7)).astype(np.float32)
    def tick():
        t = tt(0.025); return (rng.standard_normal(len(t)) * np.exp(-t * 300) * 0.35).astype(np.float32)
    def drone(d, base=48):
        t = tt(d)
        x = sum(np.sin(2 * np.pi * f * t + np.sin(t * 0.3 + f)) for f in (base, base * 1.06, base * 1.5, base * 2.03)) * 0.08
        nz = np.convolve(rng.standard_normal(len(t)), np.ones(40) / 40, 'same') * 0.25
        x = (x + nz) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.25 * t))
        fd = int(0.4 * SR); x[:fd] *= np.linspace(0, 1, fd); x[-fd:] *= np.linspace(1, 0, fd)
        return x.astype(np.float32)
    def reverb(x, g=0.5):
        y = x.copy()
        for dl, gg in ((0.031, .5), (0.053, .42), (0.079, .35), (0.113, .3), (0.167, .25), (0.241, .2), (0.33, .15)):
            k = int(dl * SR); y[k:] += g * gg * x[:-k]
        return y
    def phonk(d, bpm=130, lvl=1.0, seed=1, drums=True, bell=True):
        r = np.random.default_rng(seed)
        out = np.zeros(int(d * SR) + SR, np.float32)
        s16 = 60 / bpm / 4
        def put(ts, sig, g):
            i = int(ts * SR); j = min(len(out), i + len(sig)); out[i:j] += g * sig[:j - i]
        def kick(): t = tt(0.5); f = 160 * np.exp(-t * 18) + 45; return np.tanh(3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4))
        def snare(): t = tt(0.2); return 0.6 * r.standard_normal(len(t)) * np.exp(-t * 18) + 0.4 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 25)
        def hat(): t = tt(0.04); x = np.diff(np.concatenate([[0], r.standard_normal(len(t))])); return 0.5 * x * np.exp(-t * 90)
        def bl(semi):
            t = tt(0.2); q = 2 ** (semi / 12)
            x = np.sign(np.sin(2 * np.pi * 540 * q * t)) + np.sign(np.sin(2 * np.pi * 800 * q * t))
            return 0.22 * np.convolve(x, np.ones(4) / 4, 'same') * np.exp(-t * 14)
        mel = [0, 0, 3, 0, 7, 5, 3, 0, 0, 0, 3, 5, 7, 10, 7, 5]
        s = 0
        while s * s16 < d:
            ts = s * s16; st = s % 16; bar = (s // 16)
            if drums:
                if st in (0, 6, 10): put(ts, kick(), 0.85)
                if st in (4, 12): put(ts, snare(), 0.5)
                if st % 2 == 0: put(ts, hat(), 0.35)
            if bell and st % 2 == 0: put(ts, bl(mel[(st // 2) + (8 if bar % 2 else 0)]), 0.6)
            s += 1
        return out[:int(d * SR)] * lvl

    S = STARTS
    # OPEN
    t0 = S['open']
    for k in range(4): add(t0 + k * 0.15, clip('e', 0.26, 0.41), 1.0)
    add(t0 + 0.6, clip('e', 0.26, 1.27), 1.0)
    for k in range(4): add(t0 + k * 0.15, boom(0.15, 200), 0.3)
    add(t0 + 1.6, boom(1.2), 0.9); add(t0 + 1.6, phonk(2.0, lvl=0.55), 1)
    # MORNING + SKUCHNO (shiza audio continuous 2.07 -> 10.07)
    add(S['morning'], clip('s', 2.07, 10.07), 0.95)
    add(S['skuchno'], whoosh(), 0.6)
    for k in range(4): add(S['skuchno'] + k * 0.5, boom(0.3, 160), 0.35)
    # LUNCH
    t0 = S['lunch']; add(t0, whoosh(), 0.6)
    pieces('c', P_LUNCH, t0, 1.1); add(t0, phonk(7.7, lvl=0.22, seed=2), 1)
    # SPORT
    t0 = S['sport']; add(t0, whoosh(), 0.6)
    d0 = (P_SPORT[0][1] - P_SPORT[0][0]); d1 = (P_SPORT[1][1] - P_SPORT[1][0]) / 5
    add(t0, clip('c', P_SPORT[0][0], P_SPORT[0][1]), 1.1); add(t0, phonk(d0, lvl=0.22, seed=3), 1)
    add(t0 + d0, phonk(d1, bpm=160, lvl=0.75, seed=4), 1)
    add(t0 + d0 + d1, scratch(), 1.0)
    add(t0 + d0 + d1 + 0.05, clip('c', P_SPORT[2][0], P_SPORT[2][1]), 1.1)
    add(t0 + d0 + d1 + (87.2 - 84.3), boom(0.6, 150), 0.5)
    # FOOD
    t0 = S['food']; add(t0, whoosh(), 0.5)
    pieces('c', P_FOOD, t0, 1.05); add(t0, phonk(5.4, lvl=0.2, seed=5, drums=True), 1)
    # LECTURE
    t0 = S['lecture']; acc = 0
    for kind, s0, s1, sp in P_LECT:
        dd = (s1 - s0) / sp
        if kind == 'A': add(t0 + acc, clip('a', s0, s1, sp), 1.1)
        elif kind == 'E': add(t0 + acc, clip('e', s0, s1, sp), 1.2); add(t0 + acc, boom(1.0), 0.8)
        else: add(t0 + acc, boom(0.8, 90), 0.8); add(t0 + acc, whoosh(0.3), 0.6)
        acc += dd
    t = tt(15.0); pad = sum(np.sin(2 * np.pi * f * t + 0.4 * np.sin(t * 0.7 + f)) for f in (220, 261.6, 329.6, 440)) * 0.025
    add(t0, pad.astype(np.float32)); add(t0, phonk(15.0, lvl=0.14, seed=6, bell=False), 1)
    # NIGHT
    pieces('n', P_NIGHT, S['night'], 0.95)
    # ===== CREEPY =====
    c0 = S['c_title']; cd = T_END - c0
    add(c0, drone(S['f_bam'] - c0), 1.0)
    for k in range(int(3.5 * 16)):
        if 0.25 + k / 16 < 1.2 or 1.25 + (k - 15) / 16 < 2.0: pass
    for (t_a, cnt, cps) in ((0.25, 14, 16), (1.25, 12, 16), (2.2, 16, 18)):
        for k in range(cnt): add(c0 + t_a + k / cps, tick(), 1.0)
    add(c0 + 0.2, reverb(VO['w1'] * 0.9, 0.6), 0.8)
    add(c0 + 2.25, reverb(VO['w2'] * 0.9, 0.6), 0.6)
    add(c0 + 3.1, stab(), 0.25)
    # walk: V1 music slowed 0.4
    add(S['c_walk'], reverb(clip('v1', 0.3, 0.3 + 2.5 * 0.4, 0.4), 0.7), 0.6)
    add(S['c_walk'] + 0.95, stab()[:3000], 0.4); add(S['c_walk'] + 1.95, stab()[:3000], 0.4)
    # monologue slowed 0.9
    add(S['c_mono'], reverb(clip('c', 35.0, 35.0 + 6.9 * 0.9, 0.9), 0.55), 1.0)
    add(S['c_znaesh'], stab(), 0.9); add(S['c_znaesh'], clip('c', 27.9, 28.9), 1.2)
    # selfie: 'хорошего вечера' from C slowed + whisper
    add(S['c_selfie'] + 0.2, reverb(clip('c', 41.6, 42.95, 0.62), 0.6), 1.1)
    add(S['c_selfie'] + 2.3, reverb(VO['w3'], 0.7), 0.9)
    add(S['c_sub'], reverb(clip('c', 96.9, 96.9 + 2.6 * 0.8, 0.8), 0.6), 1.0)
    add(S['c_evid'], reverb(clip('c', 145.0, 145.6, 0.3), 0.7), 0.35)
    for k in range(2): add(S['c_evid'] + 0.5 + k * 0.5, stab()[:4000], 0.35)
    add(S['c_energo'], reverb(clip('e', 0.26, 1.27, 1 / 3), 0.7), 1.2)
    add(S['c_energo'] + 0.2, reverb(VO['w5'], 0.6), 0.5)
    add(S['c_energo'] + 3.03, stab(), 0.5)
    add(S['c_fridge'] + 0.3, reverb(VO['w4'], 0.8), 1.0)
    add(S['c_fridge'] + 1.95, pshh(), 0.9)
    # ===== FINALE =====
    t0 = S['f_bam']
    add(t0, boom(1.4), 1.0); add(t0, phonk(2.5 + 1.6 + 2.4, lvl=0.6, seed=9), 1)
    add(t0, clip('e', 0.2, 1.36), 1.3)
    for k in range(3): add(t0 + 1.16 + k * 0.45, clip('e', 0.82, 1.27), 1.2)
    add(S['f_like'], clip('c', 23.1, 24.7), 1.2)
    add(S['f_end'] + 2.22, stab()[:8000], 0.6)
    add(S['f_end'] + 2.2, reverb(VO['w3'], 0.6), 0.9)
    mix = mix[:int(T_END * SR)]
    mix = np.tanh(mix * 1.05) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for k, d in SEGS: print(f'{k:10s} {STARTS[k]:6.2f} {d}')
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
