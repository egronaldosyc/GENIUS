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
from render3 import zoomc, rgbsplit, P, flash, cover
from render2 import hue_rgb

FPS, SR = 30, 44100
BPM = 145; BT = 60 / BPM
INK = (60, 50, 160)  # medical stamp ink
PAPER = (232, 240, 226)

# ---------------- sources (RGB 720x1280) ----------------
def V1(t): return cv2.cvtColor(R.src_frame(t * 30), cv2.COLOR_BGR2RGB)
def C(t): return R3.cframe(t)
def C2(t): return R4.c2(t)
def A(t): return R3.aframe(t)
def E(t): return R3.eframe(t)
SELFIE, SKUCHNO, GLASSES, BILL = R3.IMG_SELFIE, R3.IMG_SKUCHNO, R3.IMG_GLASSES, R3.IMG_BILL
FOODS = [R4.POST[k] for k in ('p0833', 'p1453', 'p2355', 'p1950', 'p1243')]

# ---------------- timeline ----------------
TRIP_N = 8; TRIP_SEC = 6 * BT
SEGS = [('card', 5.0), ('ror', 8.85), ('q_feel', 1.5 + 2.33), ('q_sleep', 1.0 + 1.35), ('q_who', 1.3 + 2.65), ('q_voice', 1.2 + 2.2),
        ('pill', 2.0), ('trip', TRIP_N * TRIP_SEC), ('verdict', 5.2), ('discharge', 4.0), ('end', 3.6)]
STARTS = {}; _t = 0
for k, d in SEGS: STARTS[k] = _t; _t += d
T_END = _t; N = int(round(T_END * FPS))
def seg_at(t):
    for k, d in SEGS:
        if t < STARTS[k] + d: return k, t - STARTS[k], d
    k, d = SEGS[-1]; return k, d - 1e-3, d
Q = {'q_feel': (1.5, 'Как вы себя\nчувствуете?', ('c2', 76.15, 78.95, 1.2)), 'q_sleep': (1.0, 'Сколько\nвы спите?', ('c2', 28.15, 29.5, 1.0)),
     'q_who': (1.3, 'Кто в этом\nвиноват?', ('c2', 181.45, 184.1, 1.0)), 'q_voice': (1.2, 'Вы слышите\nголоса?', ('e', 0.2, 1.36, 0.53))}
ROR = [(0.0, 1.0, ('e', 0.2, 1.36, 0.87), 'видит энергетик'), (2.33, 1.0, ('a', 0.2, 2.2, 1.0), 'видит магию'),
       (5.33, 1.0, ('c2', 92.5, 95.0, 1.0), 'видит гориллу')]

# ---------------- psychedelic fx ----------------
_YY, _XX = np.mgrid[0:H, 0:W].astype(np.float32)
_R = np.sqrt((_XX - W / 2) ** 2 + (_YY - H / 2) ** 2); _A = np.arctan2(_YY - H / 2, _XX - W / 2)
def kaleido(img, n, rot, zoom=1.0):
    wedge = 2 * np.pi / n
    a = np.mod(_A + rot, wedge); a = np.where(a > wedge / 2, wedge - a, a)
    r = _R / zoom
    mx = (W / 2 + r * np.cos(a - np.pi / 2 + 0.0)).astype(np.float32); my = (H * 0.42 + r * np.sin(a + np.pi / 2)).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def melt(img, t, amp=28, lam=180):
    mx = _XX + amp * np.sin(2 * np.pi * (_YY / lam + t * 0.9)); my = _YY + amp * 0.7 * np.sin(2 * np.pi * (_XX / (lam * 1.3) + t * 0.6))
    return cv2.remap(img, mx.astype(np.float32), my.astype(np.float32), cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def swirl(img, t, k=2.5):
    a = _A + k * np.exp(-_R / 350) * math.sin(t * 2)
    mx = (W / 2 + _R * np.cos(a)).astype(np.float32); my = (H / 2 + _R * np.sin(a)).astype(np.float32)
    return cv2.remap(img, mx, my, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def acid(img, t, levels=4, hue=0):
    x = (img // (256 // levels)) * (256 // levels) + (128 // levels)
    return hue_rgb(x.astype(np.uint8), hue + t * 240, 2.2)
def neon_edges(img, t):
    g = cv2.GaussianBlur(cv2.cvtColor(img, cv2.COLOR_RGB2GRAY), (5, 5), 0)
    e = cv2.dilate(cv2.Canny(g, 40, 110), np.ones((3, 3), np.uint8))
    hsv = np.zeros((H, W, 3), np.uint8)
    hsv[..., 0] = ((_YY / 6 + _XX / 9 + t * 160) % 180).astype(np.uint8); hsv[..., 1] = 255; hsv[..., 2] = e
    col = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    glow = cv2.GaussianBlur(col, (0, 0), 6)
    return np.clip(img * 0.18 + col.astype(np.float32) + glow * 1.4, 0, 255).astype(np.uint8)
def tunnel(img, t, depth=7, rot=12):
    out = np.zeros_like(img); z = (t * 0.9) % 1.0
    for k in range(depth, -1, -1):
        s = 0.62 ** (k - z)
        if s > 4: continue
        layer = zoomc(img, s, W / 2, H / 2, 0, 0, rot * (k - z) + t * 30)
        m = np.zeros((H, W), np.uint8)
        hw, hh = W * s / 2, H * s / 2
        cv2.rectangle(m, (int(W / 2 - hw), int(H / 2 - hh)), (int(W / 2 + hw), int(H / 2 + hh)), 255, -1)
        rotm = cv2.getRotationMatrix2D((W / 2, H / 2), rot * (k - z) + t * 30, 1.0); m = cv2.warpAffine(m, rotm, (W, H))
        layer = hue_rgb(layer, k * 45 + t * 200, 1.5)
        out[m > 0] = layer[m > 0]
    return out
def grid(frames, n, t, rot=0):
    out = np.zeros((H, W, 3), np.uint8); tw, th = W // n + 1, H // n + 1
    for j in range(n * n):
        gx, gy = j % n, j // n
        f = cv2.resize(frames(j), (tw, th))
        f = hue_rgb(f, j * 360 / (n * n) + t * 200, 1.6)
        if (gx + gy) % 2: f = f[:, ::-1]
        out[gy * th:(gy + 1) * th, gx * tw:(gx + 1) * tw] = f[:H - gy * th, :W - gx * tw][:th, :tw]
    return zoomc(out, 1.25 + 0.1 * math.sin(t * 5), W / 2, H / 2, 0, 0, rot) if rot else out
def slitscan(src, t0, bands=48, lag=0.035):
    out = np.zeros((H, W, 3), np.uint8); bh = H // bands + 1
    for b in range(bands):
        f = src(max(0, t0 - b * lag)); out[b * bh:(b + 1) * bh] = f[b * bh:(b + 1) * bh]
    return out

_prev = [None]
def feedback(img, amt=0.82, z=1.035, rot=1.2, hue=12):
    p = _prev[0]
    if p is None: return img
    p = zoomc(p, z, W / 2, H / 2, 0, 0, rot); p = hue_rgb(p, hue, 1.1)
    return np.maximum(img, (p * amt).astype(np.uint8))

def ror_blot(img, t, thr):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    g = cv2.GaussianBlur(g, (0, 0), 9)
    m = (g < thr).astype(np.uint8) * 255
    m[:, W // 2:] = m[:, :W // 2][:, ::-1]
    m = cv2.GaussianBlur(m, (0, 0), 3)
    ink = np.array(PAPER, np.float32) * (1 - m[..., None] / 255.0) + np.array((18, 14, 30), np.float32) * (m[..., None] / 255.0)
    return ink.astype(np.uint8)

def paper(t):
    rng = np.random.default_rng(int(t * 7) % 20)
    x = np.full((H, W, 3), PAPER, np.float32) + rng.normal(0, 5, (H, W, 1))
    for y in range(160, H, 52): x[y:y + 2] -= 18
    return np.clip(x, 0, 255).astype(np.uint8)

def ink_stamp(c, txt, cx, cy, tl, t0, rot=-10, size=56, col=INK):
    s = ease_pop(tl, t0, 0.12)
    if s <= 0: return
    im = text_img(txt, size, col, col, 0)
    fr = Image.new('RGBA', (im.width + 40, im.height + 30), (0, 0, 0, 0)); d = ImageDraw.Draw(fr)
    d.rounded_rectangle([4, 4, fr.width - 5, fr.height - 5], 16, outline=col + (255,), width=8)
    fr.alpha_composite(im, (20, 15))
    a = np.array(fr); noise = np.random.default_rng(len(txt)).random(a.shape[:2]) < 0.18; a[noise, 3] = (a[noise, 3] * 0.3).astype(np.uint8)
    paste(c, Image.fromarray(a), cx, cy, s * (1 + 0.5 * max(0, 1 - (tl - t0) / 0.12)), rot, 0.88)

def wobble_text(c, txt, x, y, tl, size=80, col=WHITE, stroke=BLACK, amp=8):
    # per-letter wavy psychedelic text
    fo = font(F_BLACK, size); d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    tw = d0.textlength(txt, font=fo); cx = x - tw / 2
    for k, ch in enumerate(txt):
        cw = d0.textlength(ch, font=fo)
        hue = (k * 30 + tl * 300) % 360
        colr = tuple(int(v) for v in cv2.cvtColor(np.uint8([[[hue / 2, 255, 255]]]), cv2.COLOR_HSV2RGB)[0, 0]) if col is None else col
        im = text_img(ch, size, colr, stroke, max(4, size // 12))
        paste(c, im, cx + cw / 2, y + amp * math.sin(tl * 9 + k * 0.7), 1 + 0.08 * math.sin(tl * 7 + k), 6 * math.sin(tl * 5 + k))
        cx += cw

def src_frame(spec, st):
    kind = spec[0]
    return {'c2': C2, 'e': E, 'a': A, 'c': C}[kind](st)

# ---------------- VIDEO ----------------
def render(fi):
    t = fi / FPS
    key, tl, dur = seg_at(t)
    rng = random.Random(fi * 911)
    c = None
    if key == 'card':
        img = paper(t)
        img = melt(img, t, 3 + 2 * tl, 260)
        c = P(img); d = ImageDraw.Draw(c)
        d.text((W / 2, 110), 'ПСИХОНЕВРОЛОГИЧЕСКИЙ', font=font(F_BLACK, 40), fill=(40, 40, 60), anchor='mm')
        d.text((W / 2, 160), 'ДИСПАНСЕР № 848', font=font(F_BLACK, 40), fill=(40, 40, 60), anchor='mm')
        d.text((W / 2, 230), 'КАРТА ПАЦИЕНТА', font=font(F_MONO, 34), fill=(40, 40, 60), anchor='mm')
        ph = Image.fromarray(cv2.resize(SELFIE[150:1000, 60:660], (260, 368))).convert('RGBA')
        paste(c, ph, W / 2, 470, ease_pop(tl, 0.2, 0.2), -4)
        rows = [('ФИО:', 'Энергичный'), ('Возраст:', '847 рабочих дней'), ('Жалобы:', 'хочет выходной'), ('Питание:', 'макароны, тортик'),
                ('Пьёт:', 'энергосики'), ('Диагноз:', 'хроническая'), ('', 'энергичность')]
        for j, (k_, v_) in enumerate(rows):
            if tl > 0.5 + j * 0.25:
                d.text((70, 690 + j * 52), k_, font=font(F_MONO, 28), fill=(60, 60, 80))
                d.text((280, 688 + j * 52), v_, font=font(F_BLACKI, 32), fill=(20, 20, 120))
        ink_stamp(c, 'ГОСПИТАЛИЗИРОВАН', W / 2, 1090, tl, 3.4, -9, 58)
        if tl > 4.2: wobble_text(c, 'ПАЛАТА №6½', W / 2, 1220, tl, 66, None, BLACK, 10)

    elif key == 'ror':
        idx = 0 if tl < 2.33 else (1 if tl < 5.33 else 2)
        t0, bl, spec, note = ROR[idx]; u = tl - t0
        if u < bl:
            base = [SELFIE, A(6.0), C2(93.0)][idx]
            thr = 70 + 50 * math.sin(u * 4 + idx)
            img = ror_blot(cv2.resize(base, (W, H)), t, thr)
            img = melt(img, t, 6, 300)
            c = P(img); d = ImageDraw.Draw(c)
            d.text((W / 2, 130), 'ТЕСТ РОРШАХА', font=font(F_BLACK, 54), fill=(30, 30, 50), anchor='mm')
            d.text((W / 2, 190), f'карточка № {idx+1}', font=font(F_MONO, 28), fill=(80, 80, 100), anchor='mm')
            d.text((W / 2, 1225), 'Что вы видите?', font=font(F_BLACKI, 50), fill=(30, 30, 50), anchor='mm')
        else:
            uu = u - bl; st = spec[1] + uu * spec[3]
            img = src_frame(spec, st)
            blot = ror_blot(img, t, 90)
            k = min(1, uu / 0.25)
            img = cv2.addWeighted(img, k, blot, 1 - k, 0)
            img = img.copy(); img[:, W // 2:] = img[:, :W // 2][:, ::-1]  # mirror symmetry like the blot
            img = hue_rgb(img, uu * 120, 1.4)
            c = P(img)
            ink_stamp(c, note.upper(), W / 2, 230, uu, 0.3, -6, 44, INK)
            if idx == 0: wobble_text(c, 'ЭНЕРГОСИК В РОТИК', W / 2, 1080, tl, 62, None, BLACK, 12)

    elif key in Q:
        qd, qtxt, spec = Q[key]
        if tl < qd:
            img = paper(t)
            img = swirl(img, t, 1.2 * tl)
            c = P(img)
            paste(c, text_img('ВРАЧ:', 50, (60, 60, 90), (232, 240, 226), 0, f=F_MONO), W / 2, 420)
            paste(c, text_img(qtxt, 96, (20, 20, 110), WHITE, 6, spacing=-4), W / 2, 620, ease_pop(tl, 0.05, 0.2), math.sin(tl * 6) * 3)
        else:
            u = tl - qd; st = spec[1] + u * spec[3]
            if key == 'q_voice':
                # many voices: grid of E clones with different speeds
                img = grid(lambda j: E(0.2 + (u * (0.5 + 0.12 * j)) % 1.16), 3, t, 8 * math.sin(t * 2))
                img = swirl(img, t, 2.0)
            else:
                img = src_frame(spec, st)
                if key == 'q_feel': img = melt(img, t, 10 + 25 * u, 220)
                if key == 'q_sleep': img = swirl(img, t, 1.5 + u * 2)
                if key == 'q_who': img = kaleido(img, 4, t * 0.6, 1.0 + 0.2 * u)
                img = hue_rgb(img, u * 90, 1.4)
            c = P(img)
            paste(c, text_img('ПАЦИЕНТ:', 44, WHITE, BLACK, 5, f=F_MONO), W / 2, 150)
            if key == 'q_feel' and st > 76.4: wobble_text(c, 'БЕЗ ЭНЕРГИИ Я УМРУ', W / 2, 380, tl, 58, None, BLACK, 10)
            if key == 'q_sleep': wobble_text(c, 'НЕ СПИТ С 2019', W / 2, 380, tl, 66, None, BLACK, 10)
            if key == 'q_who' and st > 181.5: wobble_text(c, 'СУДЬБА', W / 2, 380, tl, 120, None, BLACK, 14)
            if key == 'q_voice': wobble_text(c, 'ДА. ВСЕ ГОВОРЯТ ОДНО', W / 2, 640, tl, 54, None, BLACK, 12)

    elif key == 'pill':
        st = 93.2 + tl * 0.9
        img = C2(st); img = zoomc(img, 1.05 + 0.4 * (tl / dur) ** 2, W / 2, 640, 0, 0, tl * 40 * (tl / dur))
        img = hue_rgb(img, tl * 200, 1.4 + tl)
        c = P(img)
        paste(c, text_img('ПРИЁМ\nПРЕПАРАТА', 110, NEON, BLACK, 12, spacing=-8), W / 2, 330, ease_pop(tl, 0.1, 0.15), -4)
        paste(c, CAN, W / 2, 900, 1.6 * ease_pop(tl, 0.4, 0.2), tl * 400)
        if tl > dur - 0.12: flash(c, (tl - (dur - 0.12)) / 0.12)

    elif key == 'trip':
        sec = min(TRIP_N - 1, int(tl / TRIP_SEC)); u = tl - sec * TRIP_SEC
        bp = math.exp(-((tl % BT) / 0.07))
        if sec == 0:
            img = kaleido(V1(1.0 + u * 1.5), 6, t * 0.9, 1.0 + 0.25 * bp)
            img = hue_rgb(img, t * 90, 1.8)
        elif sec == 1:
            img = slitscan(lambda s: C(s), 46.0 + u, 48, 0.03)
            img = acid(img, t, 5)
        elif sec == 2:
            img = C(73.9 + u * 4); img = hue_rgb(img, t * 200, 1.8)
            img = feedback(img, 0.85, 1.04 + 0.03 * bp, 2.0, 25)
        elif sec == 3:
            img = grid(lambda j: A(6.5 + ((u * 1.0 + j * 0.13) % 3.8)), 4, t, 15 * math.sin(t * 3))
        elif sec == 4:
            img = melt(SELFIE, t, 30 + 20 * bp, 160); img = hue_rgb(img, t * 150, 1.5)
        elif sec == 5:
            img = tunnel(BILL, t, 7, 14)
        elif sec == 6:
            img = neon_edges(C2(128.2 + u), t)
        else:
            img = kaleido(E(0.2 + (u * 0.9) % 1.16), 8, -t * 1.5, 1.0 + 0.4 * bp)
            img = feedback(acid(img, t, 4), 0.8, 1.05, -3, 40)
        img = zoomc(img, 1.0 + 0.06 * bp)
        c = P(img)
        if sec == 4:
            for j, fp in enumerate(FOODS):
                a = t * 2.2 + j * 2 * math.pi / len(FOODS)
                fi_ = fp.copy(); fi_.thumbnail((200, 200)); fi_ = fi_.convert('RGBA')
                m = Image.new('L', fi_.size, 0); ImageDraw.Draw(m).ellipse([0, 0, fi_.width - 1, fi_.height - 1], fill=255); fi_.putalpha(m)
                paste(c, fi_, W / 2 + 270 * math.cos(a), 640 + 420 * math.sin(a) * 0.9, 1 + 0.2 * bp, math.degrees(a))
            wobble_text(c, 'ПИЩЕВАЯ ВСЕЛЕННАЯ', W / 2, 1180, tl, 58, None, BLACK, 10)
        labels = ['ВЗГЛЯД ИЗНУТРИ', 'ОН БЕЖИТ ОТДЫХАТЬ', 'ТРЕНИРОВКА ДУХА', 'АБРА × КАДАБРА', '', 'ОН ВЕЗДЕ И НИГДЕ', 'ОБЕД ДУШИ', 'ЭНЕРГОСИК В РОТИК']
        if labels[sec] and sec != 4: wobble_text(c, labels[sec], W / 2, 1150 if sec != 7 else 640, tl, 64 if sec != 7 else 80, None, BLACK, 12)
        if u < 0.06: flash(c, 0.6 * (1 - u / 0.06))
        R.rain(c, tl, 0, TRIP_N * TRIP_SEC, [CAN, CAN2, EMO['⚡'], EMO['🥟'], EMO['🍜']], 40, 777, (60, 140), (500, 1300)) if sec in (2, 5, 7) else None

    elif key == 'verdict':
        if tl < 1.5:
            img = paper(t); c = P(img); d = ImageDraw.Draw(c)
            d.text((W / 2, 300), 'ЗАКЛЮЧЕНИЕ', font=font(F_BLACK, 70), fill=(30, 30, 60), anchor='mm')
            d.text((W / 2, 370), 'КОНСИЛИУМА', font=font(F_BLACK, 70), fill=(30, 30, 60), anchor='mm')
            d.text((W / 2, 520), 'пациент утверждает, что занимался спортом', font=font(F_MONO, 24), fill=(60, 60, 80), anchor='mm')
            ink_stamp(c, 'СЛУШАЕМ', W / 2, 760, tl, 0.6, 8, 60)
        else:
            u = tl - 1.5; st = 84.3 + u
            img = C(min(87.95, st)); img = melt(img, t, 6, 260); img = hue_rgb(img, u * 60, 1.3)
            c = P(img)
            if st > 85.1: ink_stamp(c, 'СПОРТ: 10 СЕКУНД', W / 2, 260, u, 0.8, -8, 46)
            if st > 86.45: wobble_text(c, 'НУ ЕГО НАФИГ', W / 2, 470, tl, 88, None, BLACK, 12)
            if st > 87.2: ink_stamp(c, 'ЗДОРОВ', W / 2, 640, u, 2.9, 10, 80)

    elif key == 'discharge':
        st = 20.45 + min(3.0, tl)
        img = C2(st).copy(); img = melt(img, t, 8, 300)
        img[:, W // 2:] = img[:, :W // 2][:, ::-1]
        img = hue_rgb(img, tl * 50, 1.2)
        c = P(img)
        ink_stamp(c, 'ВЫПИСАН', W / 2, 230, tl, 0.2, -8, 80)
        if tl > 1.2: wobble_text(c, 'НАЗНАЧЕНИЕ: РАБОТА 5/2', W / 2, 400, tl, 42, None, BLACK, 10)

    elif key == 'end':
        img = paper(t); img = swirl(img, t, 0.8 + tl); c = P(img); d = ImageDraw.Draw(c)
        d.text((W / 2, 260), 'РЕЦЕПТ', font=font(F_BLACK, 90), fill=(30, 30, 60), anchor='mm')
        d.text((W / 2, 340), 'Rp.: Energosik in rotik', font=font(F_BLACKI, 38), fill=(20, 20, 120), anchor='mm')
        d.text((W / 2, 400), 'по 1 банке 3 раза в день', font=font(F_MONO, 30), fill=(60, 60, 80), anchor='mm')
        d.text((W / 2, 445), 'до, после и вместо еды', font=font(F_MONO, 30), fill=(60, 60, 80), anchor='mm')
        paste(c, CAN, W / 2, 700, 1.5 * ease_pop(tl, 0.2, 0.2), math.sin(tl * 6) * 15)
        ink_stamp(c, 'ДИСПАНСЕР № 848', W / 2, 1000, tl, 0.7, -12, 50)
        d.text((W / 2, 1200), 'хорошего вечера :)', font=font(F_BLACKI, 40), fill=(30, 30, 60), anchor='mm')
        if dur - tl < 0.3: flash(c, (0.3 - (dur - tl)) / 0.3, (232, 240, 226))

    out = np.array(c.convert('RGB'))
    _prev[0] = out
    return out

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(5)
    LW = R3.load_wav
    AU = {'c': LW(os.path.join(SP, 'v4', 'au_c.wav')), 'a': LW(os.path.join(SP, 'v4', 'au_a.wav')), 'e': LW(os.path.join(SP, 'v4', 'au_e.wav')),
          'c2': LW(os.path.join(SP, 'v5', 'au_c2.wav'))}
    VO = {k: LW(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['d0', 'd1', 'd2', 'd3', 'd4', 'd5', 'd6', 'd7', 'd8']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(src, s0, s1, speed=1.0, fade=0.008):
        a = AU[src] if isinstance(src, str) else src
        m = int((s1 - s0) / speed * SR); pos = s0 * SR + np.arange(m) * speed
        x = np.interp(pos, np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def tt(d): return np.arange(int(d * SR)) / SR
    def boing():
        t = tt(0.6); f = 220 + 160 * np.sin(2 * np.pi * 14 * t) * np.exp(-t * 4) + 120 * t
        return (0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)).astype(np.float32)
    def slide(d=0.6, up=True):
        t = tt(d); f = (400 + 1400 * t / d) if up else (1800 - 1400 * t / d)
        return (0.3 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / d)).astype(np.float32)
    def thud():
        t = tt(0.25); return (np.tanh(3 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 25)) + rng.standard_normal(len(t)) * 0.3 * np.exp(-t * 40)).astype(np.float32)
    # ---- carnival organ waltz (original melody), 3/4 at 150 bpm ----
    def organ(f, d):
        t = tt(d); vib = 1 + 0.004 * np.sin(2 * np.pi * 5.5 * t)
        ph = 2 * np.pi * f * np.cumsum(vib) / SR
        x = np.sin(ph) + 0.5 * np.sin(2 * ph) + 0.3 * np.sin(3 * ph) + 0.18 * np.sin(4 * ph) + 0.1 * np.sin(6 * ph)
        env = np.minimum(1, t / 0.01) * np.clip((d - t) / 0.05, 0, 1) * (0.85 + 0.15 * np.sin(2 * np.pi * 7 * t))
        return (x * env * 0.12).astype(np.float32)
    def waltz(dur, detune=0.0, warble=0.0):
        bt = 0.4; out = np.zeros(int(dur * SR) + SR, np.float32)
        nf = lambda semi: 293.66 * 2 ** (semi / 12)  # D
        mel = [7, 5, 3, 2, 3, 5, 7, 10, 8, 7, 5, 3, 2, 0, 2, 3, 5, 2, -2, 0, 2, 3, 2, 0]
        bass = [0, 0, -5, -5, -4, -4, -5, -5]
        k = 0
        while k * bt < dur:
            ts = k * bt; bar = k // 3; beat = k % 3
            i = int(ts * SR)
            if beat == 0: s = organ(nf(bass[bar % 8] - 24), bt * 0.9) * 1.4
            else:
                b0 = bass[bar % 8]; s = sum(organ(nf(b0 + iv - 12), bt * 0.5) for iv in (0, 3, 7)) * 0.5
            out[i:i + len(s)] += s
            m = organ(nf(mel[k % len(mel)] + detune * np.sin(k)), bt * 0.95); out[i:i + len(m)] += m * 0.9
            k += 1
        out = out[:int(dur * SR)]
        if warble:
            pos = np.arange(len(out)) + warble * SR * 0.004 * np.sin(2 * np.pi * 0.7 * np.arange(len(out)) / SR)
            out = np.interp(np.clip(pos, 0, len(out) - 1), np.arange(len(out)), out).astype(np.float32)
        return out
    # ---- psytrance 145 ----
    def psy(dur):
        out = np.zeros(int(dur * SR) + SR, np.float32); s16 = BT / 4
        def put(ts, sig, g): i = int(ts * SR); j = min(len(out), i + len(sig)); out[i:j] += g * sig[:j - i]
        t = tt(0.3); kick = np.tanh(3 * np.sin(2 * np.pi * np.cumsum(150 * np.exp(-t * 30) + 48) / SR) * np.exp(-t * 9)).astype(np.float32)
        t = tt(s16 * 0.9); notes = [41.2, 41.2, 41.2, 43.65, 41.2, 41.2, 46.25, 41.2]
        hat = (np.diff(np.concatenate([[0], rng.standard_normal(int(0.05 * SR))])) * np.exp(-np.arange(int(0.05 * SR)) / SR * 70) * 0.4).astype(np.float32)
        s = 0
        while s * s16 < dur:
            ts = s * s16; st = s % 4
            if st == 0: put(ts, kick, 0.9)
            else:
                f = notes[(s // 4) % 8]; ph = 2 * np.pi * f * np.arange(len(t)) / SR
                saw = ((ph % (2 * np.pi)) / np.pi - 1); saw = np.convolve(saw, np.ones(12) / 12, 'same')
                put(ts, (saw * np.exp(-np.arange(len(t)) / SR * 18) * 0.5).astype(np.float32), 1)
            if st == 2: put(ts, hat, 0.8)
            if s % 8 in (3, 6) and (s // 32) % 2: # acid squiggle
                tq = tt(s16 * 1.8); ff = 330 * (1 + 0.5 * np.sin(2 * np.pi * 9 * tq)); x = np.sign(np.sin(2 * np.pi * np.cumsum(ff) / SR))
                put(ts, (x * np.exp(-tq * 6) * 0.12).astype(np.float32), 1)
            s += 1
        return out[:int(dur * SR)]
    S = STARTS
    # music layout
    pre = S['trip'] - 0.0
    add(0, waltz(pre, warble=0.0) * np.linspace(0.8, 1.0, int(pre * SR)).astype(np.float32), 0.55)
    tr = SEGS[[k for k, _ in SEGS].index('trip')][1]
    add(S['trip'], psy(tr), 0.75)
    post = T_END - S['verdict']
    w2 = waltz(post, detune=0.6, warble=3.0)
    add(S['verdict'], w2, 0.5)
    # doctor voices
    add(S['card'] + 0.3, VO['d0'], 0.9)
    add(S['ror'] + 0.1, VO['d1'], 0.9)
    for k in ('q_feel', 'q_sleep', 'q_who', 'q_voice'): add(S[k] + 0.05, VO[{'q_feel': 'd2', 'q_sleep': 'd3', 'q_who': 'd4', 'q_voice': 'd5'}[k]], 0.9)
    add(S['pill'] + 0.05, VO['d6'], 0.9)
    add(S['verdict'] + 0.05, VO['d7'], 0.9)
    add(S['discharge'] + 0.1, VO['d8'], 0.8)
    # patient answers
    for t0, bl, spec, note in ROR:
        add(S['ror'] + t0 + bl, clip(spec[0], spec[1], spec[2], spec[3]), 1.1); add(S['ror'] + t0 + bl, boing(), 0.35)
    for k, (qd, qt, spec) in Q.items():
        if k == 'q_voice':
            for j, sp in enumerate((0.6, 0.8, 1.0, 1.25, 1.6)):
                x = clip('e', 0.2, 1.36, sp); reps = int(2.2 * SR / len(x)) + 1
                y = np.tile(x, reps)[:int(2.2 * SR)]; add(S[k] + qd + j * 0.07, y, 0.45)
        else:
            x = clip(spec[0], spec[1], spec[2], spec[3]); add(S[k] + qd, x, 1.1)
        add(S[k] + qd - 0.05, slide(0.4, k in ('q_feel', 'q_who')), 0.6)
    add(S['pill'], clip('c2', 93.2, 93.2 + 2.0 * 0.9, 0.9), 0.8); add(S['pill'] + 1.4, slide(0.6, True), 0.8)
    # trip voice chops per section
    T0 = S['trip']
    def chopper(src, s0, s1, t0, dur, pitch=1.0, stut=None, g=0.9):
        x = clip(src, s0, s1, pitch)
        if stut: x = np.tile(x[:int(stut * SR)], int(dur / stut) + 1)
        else: x = np.tile(x, int(dur * SR / max(1, len(x))) + 1)
        add(t0, x[:int(dur * SR)], g)
    chopper('c', 54.75, 55.3, T0 + 0 * TRIP_SEC, TRIP_SEC, 1.0, BT, 0.8)                       # кайф
    add(T0 + 1 * TRIP_SEC, clip('c', 46.0, 46.0 + TRIP_SEC), 0.9)                            # побежал отдыхать
    chopper('c', 71.75, 72.35, T0 + 2 * TRIP_SEC, TRIP_SEC, 1.3, BT, 0.8)                      # спортом
    chopper('a', 6.5, 6.9, T0 + 3 * TRIP_SEC, TRIP_SEC / 2, 1.0, BT, 0.9)                       # абра
    chopper('a', 8.75, 9.6, T0 + 3.5 * TRIP_SEC, TRIP_SEC / 2, 1.0, BT * 2, 0.9)                # кадабра
    add(T0 + 4 * TRIP_SEC, clip('c2', 150.75, 153.1, 1.25), 0.9)                              # тортик (pitched up)
    chopper('e', 0.2, 1.36, T0 + 5 * TRIP_SEC, TRIP_SEC, 0.7, None, 0.8)                        # energosik slow
    add(T0 + 6 * TRIP_SEC, clip('c2', 128.2, 128.2 + TRIP_SEC), 0.9)                          # иду на обед
    for j, sp in enumerate((0.7, 1.0, 1.4, 1.9)): chopper('e', 0.2, 1.36, T0 + 7 * TRIP_SEC + j * 0.05, TRIP_SEC, sp, None, 0.4)
    for k in range(TRIP_N): add(T0 + k * TRIP_SEC, slide(0.3, k % 2 == 0), 0.4)
    # verdict / discharge / end
    add(S['verdict'] + 1.5, clip('c', 84.3, 84.3 + 3.65), 1.1)
    add(S['verdict'] + 0.6, thud(), 0.9); add(S['verdict'] + 1.5 + 0.8 + 0.8, thud(), 0.8); add(S['verdict'] + 1.5 + 2.9, thud(), 1.0)
    add(S['discharge'], clip('c2', 20.45, 23.45), 1.0); add(S['discharge'] + 0.2, thud(), 0.9)
    add(S['end'] + 0.7, thud(), 0.9); add(S['end'] + 0.2, boing(), 0.6)
    add(S['end'] + 1.6, clip('c', 41.6, 42.95, 1.45), 0.9)  # 'хорошего вечера' chipmunk
    add(S['end'] + 3.0, boing(), 0.6)
    add(S['card'] + 3.4, thud(), 0.9)
    for k in ('ror',): pass
    mix = mix[:int(T_END * SR)]
    f = int(0.25 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.05) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for k, d in SEGS: print(f'{k:10s} {STARTS[k]:6.2f} {d:.2f}')
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
