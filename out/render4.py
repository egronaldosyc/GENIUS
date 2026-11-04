import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
sys.path.insert(0, SP); sys.path.insert(0, os.path.join(SP, 'v2')); sys.path.insert(0, os.path.join(SP, 'v4'))
import render as R
import render3 as R3
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, NEON, RED, WHITE, BLACK, EMO, emoji
from render3 import zoomc, rgbsplit, creepy, warp_face, black_eyes, invert_red, P, flash, typewriter, stamp, cover
from render2 import hue_rgb, _fry

FPS, SR = 30, 44100
EM = {k: emoji(k, 150) for k in ['✊', '😨', '🤬', '😋', '👁️', '⏰', '🍌']}

# ---------------- scenes ----------------
# pieces: (kind, s0, s1, speed)  kind: 'c' = C2 video, 'card' etc handled by scene
PC = {
    'p0739': [('card', 0, 1.6, 1), ('c', 3.0, 5.8, 1), ('c', 20.45, 23.45, 1), ('txt', 0, 0.6, 1)],
    'boss': [('c', 28.15, 29.5, 1), ('frz', 0, 1.85, 1)],
    'die': [('c', 76.15, 78.95, 0.8), ('c', 82.6, 85.3, 1), ('c', 85.45, 86.25, 1)],
    'magnit': [('c', 87.25, 88.6, 1), ('c', 88.75, 90.4, 1), ('c', 92.5, 95.0, 1)],
    'p1243': [('card', 0, 2.0, 1), ('e', 0.2, 1.36, 0.83), ('bill', 0, 1.0, 1)],
    'lunch': [('c', 128.2, 130.6, 1), ('c', 143.0, 144.75, 1), ('c', 116.0, 117.85, 1)],
    'p1453': [('card', 0, 1.5, 1), ('c', 150.75, 153.1, 1), ('frz', 0, 0.65, 1)],
    'p1608': [('card', 0, 2.2, 1), ('c', 153.4, 154.95, 1), ('c', 155.25, 156.1, 1), ('c', 175.25, 177.65, 1), ('c', 181.45, 186.45, 0.85)],
    'p1949': [('card', 0, 1.8, 1), ('card2', 0, 1.8, 1), ('c', 224.25, 227.4, 1), ('c', 231.5, 233.2, 1)],
    'night': [('c', 195.0, 197.0, 1), ('c', 198.0, 199.6, 1), ('c', 200.0, 201.0, 1), ('c', 201.5, 205.5, 0.6), ('c', 207.5, 210.5, 1),
              ('static', 0, 1.5, 1), ('c', 210.5, 214.0, 0.7)],
    'eye': [('c', 241.5, 243.95, 0.7), ('c', 244.0, 245.95, 1)],
}
def pdur(pcs): return sum((p[2] - p[1]) / p[3] for p in pcs)
SEGS = [('intro', 7.0), ('p0739', pdur(PC['p0739'])), ('boss', pdur(PC['boss'])), ('p0833', 5.0), ('die', pdur(PC['die'])),
        ('magnit', pdur(PC['magnit'])), ('p1243', pdur(PC['p1243'])), ('lunch', pdur(PC['lunch'])), ('p1453', pdur(PC['p1453'])),
        ('p1608', pdur(PC['p1608'])), ('p1826', 4.0), ('p1949', pdur(PC['p1949'])), ('night', pdur(PC['night'])), ('p2211', 3.0),
        ('p2237', 8.0), ('eye', pdur(PC['eye'])), ('p2355', 7.2)]
STARTS = {}; _t = 0
for k, d in SEGS: STARTS[k] = _t; _t += d
T_END = _t; N = int(round(T_END * FPS))
def seg_at(t):
    for k, d in SEGS:
        if t < STARTS[k] + d: return k, t - STARTS[k], d
    k, d = SEGS[-1]; return k, d - 1e-3, d
def pmap(pcs, tl):
    acc = 0
    for i, p in enumerate(pcs):
        d = (p[2] - p[1]) / p[3]
        if tl < acc + d or i == len(pcs) - 1:
            u = tl - acc
            return i, p[0], p[1] + u * p[3], u, d
        acc += d
def pstart(key, idx): return STARTS[key] + sum((p[2] - p[1]) / p[3] for p in PC[key][:idx])

# screamers (global time, dur, base)
SCREAMS = [(pstart('p1608', 4) + (5.0 / 0.85) - 0.38, 0.38, 'c:185.6'),
           (pstart('night', 2), 0.3, 'c:200.3'),
           (pstart('night', 6), 0.32, 'c:211.0'),
           (STARTS['p2237'] + 8.0 - 0.45, 0.45, 'home'),
           (STARTS['p2355'] + 7.2 - 0.7, 0.42, 'c:242.0')]
SUBLIM = [STARTS['p0739'] + 3.3, STARTS['die'] + 2.2, STARTS['lunch'] + 4.5, STARTS['p1949'] + 5.0, STARTS['night'] + 8.0, STARTS['eye'] + 1.6]

# ---------------- sources ----------------
_cache = {}
LOGO_M = np.zeros((626, 352), np.uint8); LOGO_M[34:74, 0:32] = 255
KRUG = [(0, 19.0), (114.0, 128.0), (195.0, 224.0)]
_yy, _xx = np.mgrid[0:626, 0:352]
KRUG_M = cv2.GaussianBlur((((_xx - 176) ** 2 + (_yy - 314) ** 2) < 168 ** 2).astype(np.float32), (5, 5), 0)[..., None]
def c2(t):
    i = int(np.clip(round(t * 30), 0, 7438)); k = ('c2', i)
    if k not in _cache:
        if len(_cache) > 200: _cache.pop(next(iter(_cache)))
        im = cv2.cvtColor(cv2.imread(os.path.join(HERE, 'fc', f'{i+1:05d}.jpg')), cv2.COLOR_BGR2RGB)
        im = cv2.inpaint(im, LOGO_M, 4, cv2.INPAINT_TELEA)
        if any(a <= t < b for a, b in KRUG): im = (im * KRUG_M).astype(np.uint8)
        _cache[k] = cv2.resize(im, (W, H), interpolation=cv2.INTER_CUBIC)
    return _cache[k]
POST = {k: Image.open(os.path.join(HERE, 'posts', k + '.png')).convert('RGB') for k in ['p0833', 'p1243', 'p1453', 'p1949', 'p1950', 'p2237', 'p2355']}
HOME = cover(np.array(POST['p2237']))
def face_box(img):
    g = cv2.equalizeHist(cv2.cvtColor(cv2.resize(img, (360, 640)), cv2.COLOR_RGB2GRAY))
    fs = R.CASC.detectMultiScale(g, 1.1, 4, minSize=(60, 60))
    if len(fs):
        x, y, w, h = [v * 2 for v in max(fs, key=lambda f: f[2] * f[3])]
    else:
        x, y, w, h = W * 0.25, H * 0.3, W * 0.5, W * 0.5
    return [(x + .32 * w, y + .42 * h), (x + .68 * w, y + .42 * h)], (x + .5 * w, y + .8 * h), w
HOME_F = face_box(HOME)
_fb = {}
def fbox(key, img):
    if key not in _fb: _fb[key] = face_box(img)
    return _fb[key]

# ---------------- helpers ----------------
DING_TIMES = []
def card(c, tl, tstr, caption, photo=None, emo=None, views=None, glitch=0.0, rng=None):
    a = ease_pop(tl, 0.05, 0.22)
    if a <= 0: return
    bw = 600
    fo = font(F_BLACK, 34)
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    # wrap caption
    words = caption.split(' '); lines = ['']
    for w_ in words:
        tst = (lines[-1] + ' ' + w_).strip()
        if d0.textlength(tst, font=fo) > bw - 60: lines.append(w_)
        else: lines[-1] = tst
    ph = None
    if photo is not None:
        ph = photo.copy(); s = (bw - 16) / ph.width; ph = ph.resize((bw - 16, int(ph.height * s)))
        if ph.height > 720: ph = ph.crop((0, (ph.height - 720) // 2, ph.width, (ph.height - 720) // 2 + 720))
    hh = (ph.height + 16 if ph else 12) + 46 * len(lines) + 70
    b = Image.new('RGBA', (bw, hh), (0, 0, 0, 0)); bd = ImageDraw.Draw(b)
    bd.rounded_rectangle([0, 0, bw - 1, hh - 1], 26, fill=(36, 30, 52, 245))
    y = 8
    if ph:
        m = Image.new('L', ph.size, 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, ph.width - 1, ph.height - 1], 20, fill=255)
        b.paste(ph, (8, 8), m); y = ph.height + 16
    for j, l in enumerate(lines):
        if glitch > 0 and rng and rng.random() < glitch:
            l = ''.join(ch if rng.random() > 0.3 else rng.choice('#@!%&?*') for ch in l)
        bd.text((24, y + 6 + 46 * j), l, font=fo, fill=WHITE)
    if emo:
        lw = d0.textlength(lines[-1], font=fo)
        e = EM.get(emo) or EMO.get(emo)
        if e: b.alpha_composite(e.resize((40, 40)), (int(28 + lw + 6), int(y + 8 + 46 * (len(lines) - 1))))
    bd.text((bw - 24, hh - 26), f'👁 {views}  {tstr}' if False else f'{views}  {tstr}', font=font(F_MONO, 24), fill=(160, 150, 190), anchor='rm')
    paste(c, b, W / 2, 210 + hh / 2 + 60, a * (1 + 0.012 * tl), -1)
    big = text_img(tstr, 90, (230, 230, 230), BLACK, 6, f=F_MONO)
    paste(c, big, W / 2, 175, a)

def dark_bg(t, tint=(0.8, 0.9, 1.1)):
    return creepy(np.full((H, W, 3), 14, np.uint8), t, 1.0, tint)

def hud_energy(c, t, val, label='ЭНЕРГИЯ'):
    d = ImageDraw.Draw(c)
    x, y, w, h = 30, H - 120, 330, 40
    d.rounded_rectangle([x, y, x + w, y + h], 6, fill=(0, 0, 0, 180), outline=(200, 200, 200, 200), width=2)
    if val > 0 and not (val < 0.15 and int(t * 4) % 2): d.rounded_rectangle([x + 4, y + 4, x + 4 + (w - 8) * val, y + h - 4], 4, fill=(220, 30, 30) if val < 0.3 else (200, 200, 60))
    d.text((x + 10, y + h / 2), label, font=font(F_MONO, 20), fill=WHITE, anchor='lm', stroke_width=2, stroke_fill=BLACK)
    d.text((x + w - 10, y + h / 2), f'{int(val*100)}%', font=font(F_MONO, 20), fill=WHITE, anchor='rm', stroke_width=2, stroke_fill=BLACK)

def osd(c, t, clock):
    d = ImageDraw.Draw(c)
    if int(t * 2) % 2 == 0: d.ellipse([34, 40, 58, 64], fill=(220, 0, 0))
    d.text((72, 52), 'REC  ПЯТНИЦА · ДЕНЬ 5', font=font(F_MONO, 26), fill=(230, 230, 230), anchor='lm')
    d.text((W - 34, 52), clock, font=font(F_MONO, 26), fill=(230, 230, 230), anchor='rm')

def energy_at(t):
    return float(np.interp(t, [0, STARTS['die'], STARTS['magnit'] + 4, STARTS['p1243'] + 3, STARTS['p1608'], STARTS['night'], STARTS['night'] + 16, T_END],
                           [0.22, 0.04, 0.03, 0.85, 0.35, 0.12, 0.0, 0.01]))
CLOCKS = [('intro', '07:38'), ('p0739', '07:39'), ('boss', '07:51'), ('p0833', '08:33'), ('die', '10:14'), ('magnit', '10:21'), ('p1243', '12:43'),
          ('lunch', '13:02'), ('p1453', '14:53'), ('p1608', '16:08'), ('p1826', '18:26'), ('p1949', '19:49'), ('night', '21:47'), ('p2211', '22:11'),
          ('p2237', '22:37'), ('eye', '23:14'), ('p2355', '23:55')]
CLK = dict(CLOCKS)

def screamer(t, ts, d, base, rng):
    u = (t - ts) / d
    if base == 'home':
        img, (eyes, mouth, fw) = HOME, HOME_F
    else:
        st = float(base.split(':')[1]); img = c2(st); eyes, mouth, fw = fbox(base, img)
    img = warp_face(img, eyes, mouth, 0.55, 1.9, eye_r=fw * 0.17)
    img = black_eyes(img, eyes, fw * 0.11)
    cx = (eyes[0][0] + eyes[1][0]) / 2; cy = (eyes[0][1] + mouth[1]) / 2
    z = 1.4 + 1.6 * u ** 0.7
    img = zoomc(img, z, cx, cy, W / 2 - cx + rng.uniform(-40, 40), H / 2 - cy + rng.uniform(-40, 40), rng.uniform(-6, 6))
    x = img.astype(np.float32); g = x.mean(2, keepdims=True)
    x = np.clip((g - 90) * 2.4 + 110, 0, 255)
    x = np.concatenate([x * 1.25, x * 0.15, x * 0.15], 2) if int(t * 30) % 2 else np.concatenate([x, x * 0.85, x * 0.85], 2)
    img = rgbsplit(glitch_slices(np.clip(x, 0, 255).astype(np.uint8), rng, 12, 150), 35)
    c = P(img)
    if u < 0.12: flash(c, 1 - u / 0.12)
    return c

def meme(c, txt, tl, t0, y=1050, size=96, col=WHITE, rot=-3, rng=None):
    s = ease_pop(tl, t0, 0.12)
    if s <= 0: return
    paste(c, text_img(txt, size, col, BLACK, max(6, size // 10), spacing=-6), W / 2 + (rng.uniform(-3, 3) if rng else 0), y, s, rot)

# ---------------- VIDEO ----------------
def render(fi):
    t = fi / FPS
    key, tl, dur = seg_at(t)
    rng = random.Random(fi * 3301)
    c = None
    clock = CLK.get(key, '')
    if key in PC:
        i, kind, st, u, pd = pmap(PC[key], tl)
    else:
        i, kind, st, u, pd = 0, None, 0, tl, dur

    def vid(st, z=1.0, cx=W / 2, cy=H / 2, amt=0.85, tint=(0.8, 0.95, 1.12)):
        img = zoomc(c2(st), z, cx, cy)
        return creepy(img, t, amt, tint)

    if key == 'intro':
        c = P(dark_bg(t))
        typewriter(c, 'Эти записи появились', tl, 0.3, 18, 520, 40)
        typewriter(c, 'в его канале в пятницу.', tl, 1.4, 18, 575, 40)
        typewriter(c, 'Это был его пятый рабочий день.', tl, 3.0, 20, 680, 36, (220, 40, 40))
        if tl > 5.0:
            a = text_img('ПЯТЫЙ\nРАБОЧИЙ\nДЕНЬ', 128, (235, 235, 235), (120, 0, 0), 10, spacing=-10)
            cc = P(dark_bg(t)); paste(cc, a, W / 2 + rng.uniform(-6, 6), 640, 1.0)
            arr = np.array(cc.convert('RGB'))
            if rng.random() < 0.5: arr = glitch_slices(arr, rng, 8, 60)
            c = P(rgbsplit(arr, 10 + 10 * rng.random()))

    elif key == 'p0739':
        if kind == 'card':
            c = P(dark_bg(t)); card(c, u, '07:39', 'Просыпаемся потихоньку ребзи', None, '✊', 160)
        elif kind == 'c':
            if st < 10:
                c = P(vid(st, 1.0 + 0.05 * u)); meme(c, '"хорошее" утро', u, 0.6, 1150, 54, (220, 220, 220), 0)
            else:
                c = P(vid(st, 1.05 + 0.06 * u))
        else:
            c = P(dark_bg(t)); paste(c, text_img('ВЫХОДНОГО\nНЕ БУДЕТ', 110, (220, 30, 30), BLACK, 10, spacing=-8), W / 2 + rng.uniform(-5, 5), 640, ease_pop(u, 0, 0.1))

    elif key == 'boss':
        if kind == 'c':
            c = P(vid(st, 1.08))
        else:
            img = c2(29.45); img = zoomc(img, 1.1 + 0.25 * u / pd, W / 2, 520)
            img = creepy(img, t, 0.95, (0.9, 0.9, 1.0)); c = P(img)
        meme(c, 'Я ТАК УСТАЛ,\nБОСС', tl, 0.55, 360, 104, WHITE, -2, rng)

    elif key == 'p0833':
        img = dark_bg(t); c = P(img)
        if tl < 2.2:
            card(c, tl, '08:33', 'Завтракаю', POST['p0833'], None, 162)
        else:
            u2 = tl - 2.2
            pim = POST['p0833']; pim = pim.resize((W, int(pim.height * W / pim.width)))
            ph = np.zeros((H, W, 3), np.uint8); ph[150:150 + pim.height] = np.array(pim)[:H - 150]
            z = 1 + 1.4 * min(1, u2 / 0.8)
            px, py = W * 0.86, 150 + pim.height * 0.24
            img = creepy(zoomc(ph, z, px, py, (W / 2 - px) * min(1, u2 / 0.8), (H / 2 - py) * min(1, u2 / 0.8)), t, 0.6, (1.0, 0.95, 0.9))
            c = P(img); d = ImageDraw.Draw(c)
            if u2 > 0.8:
                d.ellipse([W / 2 - 150, H / 2 - 190, W / 2 + 150, H / 2 + 190], outline=(230, 30, 30), width=7)
                typewriter(c, 'а это что за таблетки?', u2, 0.9, 20, H / 2 + 260, 36, (230, 50, 50))
            stamp(c, 'ЗАВТРАК\nЧЕМПИОНА', W / 2, 260, u2, 1.6, -8, (230, 20, 40), 50)
        osd(c, t, clock)

    elif key == 'die':
        if i == 0:
            hb = math.exp(-((tl % 0.75) / 0.08))
            img = vid(st, 1.1 + 0.15 * u / pd + 0.03 * hb, W / 2, 560, 0.9, (1.2, 0.7, 0.7))
            c = P(img)
            typewriter(c, 'БЕЗ ЭНЕРГИИ Я УМРУ', u, 0.25, 14, 300, 50, (230, 40, 40))
        elif i == 1:
            c = P(vid(st, 1.05))
            d = ImageDraw.Draw(c)
            left = max(0, 3 * 3600 + 12 * 60 + 44 - int(u * 2400))
            d.rounded_rectangle([W / 2 - 230, 230, W / 2 + 230, 320], 12, fill=(0, 0, 0, 200))
            d.text((W / 2, 275), f'ДОЖИТЬ ДО ОБЕДА: {left//3600}:{(left//60)%60:02d}:{left%60:02d}', font=font(F_MONO, 30), fill=(230, 60, 60), anchor='mm')
        else:
            c = P(vid(st, 1.0, amt=0.7, tint=(1.1, 0.8, 0.8)))
            typewriter(c, 'закрывается в 22:30.', u, 0.1, 30, 1000, 40, (240, 240, 240))
        hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'magnit':
        fl = 0.75 + 0.25 * (rng.random() < 0.85)
        img = vid(st, 1.04, amt=0.75, tint=(0.95 * fl, 1.05 * fl, 0.95 * fl))
        c = P(img)
        if i == 2 and st > 94.15:
            if st < 94.25: flash(c, 0.7)
            meme(c, 'ОКАК', tl, (94.15 - 92.5) + pstart('magnit', 2) - STARTS['magnit'], 330, 170, (255, 230, 40), -6, rng)
            paste(c, EM['🍌'], W - 120, 470, 0.8 * ease_pop(st, 94.3, 0.12), math.sin(tl * 9) * 15)
        hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'p1243':
        if kind == 'card':
            c = P(dark_bg(t)); card(c, u, '12:43', 'Банановый вайб у меня сегодня', POST['p1243'], None, 212)
        elif kind == 'e':
            img = R3.eframe(st); img = zoomc(img, 1.15 + 0.1 * u, W / 2, 520)
            img = creepy(img, t, 0.85, (1.2, 0.75, 0.7)); c = P(img)
            meme(c, 'ЭНЕРГОСИК\nВ РОТИК', u, 0.15, 1000, 110, (255, 230, 40), -3, rng)
        else:
            img = R3.IMG_BILL.astype(np.float32) * (0.4 + 0.35 * (rng.random() < 0.7))
            c = P(creepy(img.astype(np.uint8), t, 0.8, (0.8, 0.9, 1.2)))
            typewriter(c, 'он везде.', u, 0.1, 18, 200, 44, (230, 50, 50))
        if kind != 'card': hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'lunch':
        c = P(vid(st, 1.05, amt=0.8))
        d = ImageDraw.Draw(c)
        if i == 1:
            left = max(0, 3599 - int(u * 2000))
            d.rounded_rectangle([W / 2 - 180, 230, W / 2 + 180, 330], 12, fill=(0, 0, 0, 210))
            d.text((W / 2, 280), f'ОБЕД {left//60:02d}:{left%60:02d}', font=font(F_MONO, 50), fill=(230, 60, 60), anchor='mm')
        if i == 2:
            typewriter(c, 'он жуёт.', u, 0.3, 12, 1100, 40)
            typewriter(c, 'он всегда жуёт.', u, 1.0, 16, 1150, 40)
        hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'p1453':
        if kind == 'card':
            c = P(dark_bg(t)); card(c, u, '14:53', 'Мой обед', POST['p1453'], None, 204)
        elif kind == 'c':
            c = P(vid(st, 1.05, amt=0.75)); hud_energy(c, t, energy_at(t)); osd(c, t, clock)
        else:
            img = creepy(zoomc(c2(153.0), 1.2 + 0.2 * u), t, 1.0); c = P(img)
            typewriter(c, 'это была его единственная', u, 0.0, 60, 600, 38)
            typewriter(c, 'еда за день.', u, 0.25, 60, 650, 38, (230, 50, 50))

    elif key == 'p1608':
        if kind == 'card':
            c = P(dark_bg(t))
            g = max(0, (u - 0.9) / 1.3)
            card(c, u, '16:08', 'Загружен я сегодня прям сильно. Вообще ничего не успеваю, всё бесит', None, '🤬', 190, g * 0.8, rng)
        else:
            if i == 4:
                img = vid(st, 1.1 + 0.25 * u / pd, W / 2, 600, 0.9, (1.15, 0.75, 0.75))
                if rng.random() < 0.08: img = glitch_slices(img, rng, 6, 60)
                c = P(img)
                if st > 181.5: paste(c, text_img('СУДЬБА', 140, (200, 0, 0), BLACK, 10), W / 2 + rng.uniform(-8, 8), 330, ease_pop(st, 181.5, 0.3) * (1 + 0.04 * math.sin(tl * 14)))
            elif i == 2:
                img = vid(st, 1.15 + 0.1 * u, amt=0.9, tint=(1.3, 0.6, 0.6)); img = rgbsplit(img, 14); c = P(img)
                meme(c, 'БЕСИТ', u, 0.05, 380, 150, (230, 30, 30), 4, rng)
            elif i == 3:
                c = P(vid(st, 1.05, amt=0.8))
                meme(c, 'ЭТО ФИАСКО,\nБРАТАН', u, 0.5, 330, 90, WHITE, -3, rng)
                d = ImageDraw.Draw(c); d.text((W / 2, 470), 'ОЧЕРЕДЬ: ∞', font=font(F_SYM, 44), fill=(230, 60, 60), anchor='mm', stroke_width=4, stroke_fill=BLACK)
            else:
                c = P(vid(st, 1.08, amt=0.85))
            hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'p1826':
        c = P(dark_bg(t))
        if tl < 1.8: card(c, tl, '18:26', 'Ура второй видос получилось смонтировать', None, None, 172)
        else:
            typewriter(c, 'второй видос —', tl, 1.9, 20, 560, 42)
            typewriter(c, 'это то, что ты сейчас смотришь.', tl, 2.6, 26, 620, 34, (230, 50, 50))

    elif key == 'p1949':
        if kind == 'card':
            c = P(dark_bg(t)); card(c, u, '19:49', 'Чтобы с голода не умереть решил чуточку еды взять', POST['p1949'], None, 176)
        elif kind == 'card2':
            c = P(dark_bg(t)); card(c, u, '19:50', 'Со мной решили ещё поделиться', POST['p1950'], None, 175)
            if u > 1.0: paste(c, text_img('КТО?', 120, (230, 30, 30), BLACK, 10), W / 2 + rng.uniform(-4, 4), 1150, ease_pop(u, 1.0, 0.1))
        else:
            c = P(vid(st, 1.06 + 0.1 * u / pd, amt=0.85))
            if i == 3:
                d = ImageDraw.Draw(c)
                R.bar(d, 30, 230, 420, 40, 1.0 if int(tl * 8) % 2 else 0.7, (230, 30, 30), 'ЖЕЛУДОК', 'СХОДИТ С УМА', False)
            hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'night':
        if kind == 'static':
            nz = np.random.default_rng(fi).integers(0, 255, (H // 4, W // 4, 1), dtype=np.uint8).repeat(4, 0).repeat(4, 1).repeat(3, 2)
            c = P((nz * 0.6).astype(np.uint8))
            d = ImageDraw.Draw(c); d.rectangle([0, H / 2 - 60, W, H / 2 + 60], fill=(0, 0, 0, 230))
            d.text((W / 2, H / 2), 'СВЯЗЬ ПОТЕРЯНА', font=font(F_MONO, 54), fill=(230, 230, 230), anchor='mm')
        else:
            amt = 0.8
            if i == 3:
                img = c2(st); gh = c2(st - 0.3); img = cv2.addWeighted(img, 0.6, gh, 0.4, 0)
                img = creepy(zoomc(img, 1.1 + 0.2 * u / pd, W / 2, 600), t, 0.85, (0.75, 1.0, 0.85))
            elif i == 6:
                img = creepy(zoomc(c2(st), 1.2 + 0.4 * u / pd, W / 2, 620), t, 0.9, (0.8, 1.0, 0.8))
            else:
                img = vid(st, 1.08, amt=amt, tint=(0.75, 1.0, 0.85))
            c = P(img)
            if i == 4 and u > 1.0: typewriter(c, 'что-то упало.', u, 1.0, 14, 1050, 40, (230, 50, 50))
            if i == 6: typewriter(c, 'он вернулся.', u, 0.8, 12, 1080, 44, (230, 50, 50))
        hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'p2211':
        c = P(dark_bg(t))
        if tl < 1.6: card(c, tl, '22:11', 'Стрим', None, None, 183)
        else: typewriter(c, 'стрим так и не начался.', tl, 1.6, 20, 640, 40)

    elif key == 'p2237':
        if tl < 1.8:
            c = P(dark_bg(t)); card(c, tl, '22:37', 'Вот я и дома', POST['p2237'], None, 216)
        else:
            u2 = (tl - 1.8) / (dur - 1.8)
            eyes, mouth, fw = HOME_F
            img = HOME
            if u2 > 0.45: img = black_eyes(img, eyes, fw * 0.11, min(1, (u2 - 0.45) / 0.2))
            cx = (eyes[0][0] + eyes[1][0]) / 2; cy = eyes[0][1] + 60
            img = zoomc(img, 1.0 + 1.3 * u2 ** 1.4, cx, cy, (W / 2 - cx) * u2, (H / 2 - cy) * u2)
            img = creepy(img, t, 0.75, (1.0, 0.92, 0.85)); c = P(img)
            typewriter(c, 'вот я и дома.', tl - 1.8, 0.4, 10, 1120, 44)
            osd(c, t, clock)

    elif key == 'eye':
        if i == 0:
            img = vid(st, 1.15, W / 2, 560, 0.9, (0.9, 0.85, 1.1)); c = P(img)
            typewriter(c, 'никогда не голодай.', u, 0.9, 12, 300, 44, (230, 50, 50))
        else:
            c = P(vid(st, 1.04, amt=0.5, tint=(1.05, 1.0, 0.95)))
            stamp(c, '*НЕ РЕКЛАМА*', W / 2, 300, u, 0.4, -8, (230, 20, 40), 60)
        hud_energy(c, t, energy_at(t)); osd(c, t, clock)

    elif key == 'p2355':
        c = P(dark_bg(t))
        if tl < 2.4:
            card(c, tl, '23:55', 'Ура я ужинаю', POST['p2355'], '😋', 209)
        else:
            u2 = tl - 2.4
            typewriter(c, 'до будильника: 7 ч 44 мин.', u2, 0.1, 30, 520, 36)
            typewriter(c, 'это был его пятый рабочий день.', u2, 1.2, 30, 600, 34)
            if u2 > 2.4: paste(c, text_img('ЗАВТРА —\nШЕСТОЙ', 120, (220, 30, 30), BLACK, 10, spacing=-8), W / 2 + rng.uniform(-4, 4), 820, ease_pop(u2, 2.4, 0.12))
        if dur - tl < 0.28: c = P(np.zeros((H, W, 3), np.uint8))

    for ts in SUBLIM:
        if ts <= t < ts + 2 / FPS:
            c = P(black_eyes(warp_face(R3.IMG_SELFIE, R3.SEYE, R3.SMOUTH, 0.35, 1.0), R3.SEYE, 36))
    for ts, d, base in SCREAMS:
        if ts <= t < ts + d: c = screamer(t, ts, d, base, rng)
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def load_wav(p): return R3.load_wav(p)
def build_audio(out):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32)
    rng = np.random.default_rng(11)
    C = load_wav(os.path.join(HERE, 'au_c2.wav'))
    E = load_wav(os.path.join(SP, 'v4', 'au_e.wav'))
    VO = {k: load_wav(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['n1', 'n2', 'n3', 'n4', 'n5', 'n6']}
    W3 = load_wav(os.path.join(SP, 'v4', 'vo', 'w3.wav'))
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(a, s0, s1, speed=1.0, fade=0.008):
        m = int((s1 - s0) / speed * SR); pos = s0 * SR + np.arange(m) * speed
        x = np.interp(pos, np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def tt(d): return np.arange(int(d * SR)) / SR
    def reverb(x, g=0.5):
        y = x.copy()
        for dl, gg in ((0.031, .5), (0.053, .42), (0.079, .35), (0.113, .3), (0.167, .25), (0.241, .2), (0.33, .15)):
            k = int(dl * SR); y[k:] += g * gg * x[:-k]
        return y
    def boom(d=1.0, f0=130):
        t = tt(d); f = f0 * np.exp(-t * 5) + 38
        return np.tanh(2.8 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3)).astype(np.float32)
    def stab(d=0.9):
        t = tt(d); x = np.tanh(4 * (rng.standard_normal(len(t)) * 0.6 + np.sin(2 * np.pi * 55 * t) + np.sin(2 * np.pi * 58 * t))) * np.exp(-t * 3)
        return x.astype(np.float32)
    def ding():
        t = tt(0.5); e = np.exp(-t * 9)
        return (0.35 * (np.sin(2 * np.pi * 1046 * t) + 0.6 * np.sin(2 * np.pi * 1568 * np.clip(t - 0.09, 0, None)) * (t > 0.09)) * e).astype(np.float32)
    def tick():
        t = tt(0.03); return (rng.standard_normal(len(t)) * np.exp(-t * 250) * 0.3).astype(np.float32)
    def heart():
        t = tt(0.35); x = np.sin(2 * np.pi * 50 * t) * np.exp(-t * 18) + 0.7 * np.sin(2 * np.pi * 45 * np.clip(t - 0.16, 0, None)) * np.exp(-np.clip(t - 0.16, 0, None) * 18) * (t > 0.16)
        return np.tanh(2.5 * x).astype(np.float32)
    def static(d):
        x = rng.standard_normal(int(d * SR)).astype(np.float32) * 0.35; return x
    def scream(d):
        t = tt(d + 0.25); f = 620 + 380 * np.minimum(1, t / d) + 45 * np.sin(2 * np.pi * 7.5 * t)
        ph = 2 * np.pi * np.cumsum(f) / SR
        x = sum(((ph * m) % (2 * np.pi)) / np.pi - 1 for m in (1, 1.49, 2.03, 2.97)) * 0.3 + rng.standard_normal(len(t)) * 0.7
        env = np.minimum(1, t / 0.004) * np.clip((d + 0.25 - t) / 0.2, 0, 1)
        return np.tanh(5 * x * env).astype(np.float32)
    # drone bed (whole film), with slow evolving pitch
    t = tt(T_END)
    base = 46 + 4 * np.sin(2 * np.pi * t / 40)
    ph = 2 * np.pi * np.cumsum(base) / SR
    dr = (np.sin(ph) + np.sin(ph * 1.06) * 0.8 + np.sin(ph * 1.5) * 0.5 + np.sin(ph * 2.03) * 0.3) * 0.07
    nz = np.convolve(rng.standard_normal(len(t)), np.ones(60) / 60, 'same') * 0.3
    bed = ((dr + nz) * (0.75 + 0.25 * np.sin(2 * np.pi * 0.2 * t))).astype(np.float32)
    f = int(1.0 * SR); bed[:f] *= np.linspace(0, 1, f); bed[-f:] *= np.linspace(1, 0, f)
    add(0, bed)
    # clock ticks under cards & intro
    for k, d in SEGS:
        s0 = STARTS[k]
        if k.startswith('p') or k == 'intro':
            for j in range(int(d)): add(s0 + j + 0.5, tick(), 0.8)
    # per-scene source audio
    for k, pcs in PC.items():
        acc = STARTS[k]
        for kind, s0, s1, sp in pcs:
            dd = (s1 - s0) / sp
            if kind == 'c':
                x = clip(C, s0, s1, sp)
                g = 1.05
                if sp < 0.95: x = reverb(x, 0.6); g = 1.1
                if k == 'eye' and sp == 1: g = 1.0
                add(acc, x, g)
            elif kind == 'e':
                add(acc, reverb(clip(E, s0, s1, sp), 0.6), 1.2)
            elif kind == 'static':
                add(acc, static(dd), 0.8)
            elif kind in ('card', 'card2'):
                add(acc + 0.05, ding(), 0.9)
            acc += dd
    for k in ('p0833', 'p1826', 'p2211', 'p2237', 'p2355'): add(STARTS[k] + 0.05, ding(), 0.9)
    # heartbeats in 'die' and 'p2237'
    for j in range(int(PC and pdur(PC['die'][:1]) / 0.75) + 1): add(STARTS['die'] + j * 0.75, heart(), 0.8)
    for j in range(int(6.2 / 0.6)): add(STARTS['p2237'] + 1.8 + j * (0.6 - 0.02 * j), heart(), 0.7 + 0.03 * j)
    # meme hits
    for tm in (STARTS['boss'] + 0.55, STARTS['p1243'] + 2.0 + 0.15, pstart('magnit', 2) + (94.15 - 92.5), pstart('p1608', 2), pstart('p1608', 3) + 0.5,
               STARTS['eye'] + pdur(PC['eye'][:1]) + 0.4):
        add(tm, boom(0.7, 150), 0.55)
    # voices
    add(STARTS['intro'] + 3.0, reverb(VO['n1'], 0.6), 0.9)
    add(STARTS['p0739'] + pdur(PC['p0739'][:3]) - 0.05, reverb(VO['n2'], 0.7), 1.0)
    add(STARTS['p2237'] + 2.2, reverb(VO['n3'], 0.7), 1.0)
    add(pstart('night', 6) + 0.7, reverb(VO['n6'], 0.7), 0.9)
    add(STARTS['p2355'] + 4.8, reverb(VO['n4'], 0.6), 1.0)
    add(STARTS['p2355'] + 6.2, reverb(W3, 0.7), 0.8)
    add(STARTS['p1453'] + pdur(PC['p1453'][:2]), stab(0.6), 0.3)
    add(STARTS['p1826'] + 1.8, stab(0.5), 0.3)
    add(STARTS['p2211'] + 1.6, stab(0.5), 0.3)
    add(pstart('night', 4) + 0.6, boom(1.0, 90), 0.8)  # camera falls
    for ts in SUBLIM: add(ts, stab()[:3500], 0.45)
    # screamers: dip before, scream
    e_rev = clip(E, 0.82, 1.27)[::-1].copy()
    for ts, d, base in SCREAMS:
        i0, i1 = int((ts - 0.5) * SR), int(ts * SR)
        mix[i0:i1] *= np.linspace(1, 0.06, i1 - i0) ** 0.5
        add(ts, scream(d), 0.78); add(ts, boom(0.8, 200), 0.8)
        er = np.interp(np.arange(0, len(e_rev), 1.6), np.arange(len(e_rev)), e_rev).astype(np.float32)
        add(ts, np.tanh(4 * er), 0.5)
    i0 = int((T_END - 0.28) * SR); mix[i0:] *= 0.0
    add(T_END - 0.28, stab(0.28), 0.0)
    mix = mix[:int(T_END * SR)]
    mix = np.tanh(mix * 1.05) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(out, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for k, d in SEGS: print(f'{k:8s} {STARTS[k]:7.2f} {d:.2f}')
        print('total', T_END, 'screams', [round(s[0], 2) for s in SCREAMS]); sys.exit()
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
