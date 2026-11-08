# ТРОПАРЕВО · спин-офф «38» — под Слава КПСС «Органы убийцы». Hotline-Miami-стиль. 1920x1080.
import os, sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path[:0] = [HERE, os.path.join(SP, 'v17'), SP, os.path.join(SP, 'v13')]
import render17 as A
from render17 import (put, scaled, rich_img, grad, P, say, narr, pill, stamp, clamp, eo, eio, lerp, fade, cached, vgrad_im,
                      F_SER, F_SERI, WHITE, BLACK, RED, GOLD, CREAM, COL)
from render13 import font, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO
import render13 as R
from scenes import park
from chars import puppet, CHAR
from hm import neon_bg, hm_text, wobble, vhs, forest_map, graves, draw_grave, goose, shovel, PINK, CYAN, PURP, YEL, ORNG

W, H, FPS = 1920, 1080, 30
TRACK = os.path.join(HERE, 'track.mp3'); T_END = 381.93; N = int(T_END * FPS)
CHAR['Врачиха'] = dict(col=(235, 240, 245), hair=(120, 60, 40), hs='bob', skin=1, glasses=True, acc='lips', prop='note')
for n in CHAR: COL[n] = CHAR[n]['col']

KP = os.path.join(HERE, 'kick.npy')
def build_kick():
    sr = 11025
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', TRACK, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    lo = np.convolve(x, np.ones(40) / 40, 'same'); hop = sr // FPS; n = len(lo) // hop
    e = np.sqrt(np.mean(lo[:n * hop].reshape(n, hop) ** 2, 1)); d = np.maximum(0, e - np.concatenate([[0], e[:-1]]))
    d = np.clip(d / (np.percentile(d, 99.5) + 1e-9), 0, 1); out = np.zeros_like(d); acc = 0
    for i in range(len(d)): acc = max(d[i], acc * 0.7); out[i] = acc
    np.save(KP, out.astype(np.float32))
KICK = np.load(KP) if os.path.exists(KP) else np.zeros(N + 10, np.float32)
def kick(t): i = int(t * FPS); return float(KICK[i]) if 0 <= i < len(KICK) else 0.0

# ---------------- assets ----------------
KR = [os.path.join(SP, 'v10', f'k{i}') for i in (1, 2, 3, 4, 5)] + [os.path.join(SP, 'v11', f'kb{i}') for i in (1, 2, 3, 4)] + [os.path.join(SP, 'v12', 'kc1')]
KRN = [len(os.listdir(p)) for p in KR]
def krug(k, rel, d):
    p = KR[k % len(KR)]; i = int(rel * 30) % KRN[k % len(KR)] + 1
    im = Image.open(os.path.join(p, f'{i:04d}.jpg')).convert('RGB').resize((d, d))
    m = cached(('cm', d), lambda: _cmask(d)); out = im.convert('RGBA'); out.putalpha(m); return out
def _cmask(d):
    m = Image.new('L', (d * 2, d * 2), 0); ImageDraw.Draw(m).ellipse([2, 2, d * 2 - 3, d * 2 - 3], fill=255); return m.resize((d, d), Image.LANCZOS)
def put_krug(c, k, rel, x, y, d, a=1.0, ring=PINK):
    put(c, krug(k, rel, d), x, y, a)
    dr = ImageDraw.Draw(c); r = d / 2 + 10; dr.ellipse([x - r, y - r, x + r, y + r], outline=ring, width=10)
PHOTO = Image.open(os.path.join(HERE, 'egor_photo.png')).convert('RGB')
def photo_card(w=520, tint=0.0, label=None):
    def mk():
        p = PHOTO.resize((w, int(w * PHOTO.height / PHOTO.width)), Image.LANCZOS).convert('RGBA')
        fr = Image.new('RGBA', (p.width + 30, p.height + 30), PINK + (255,)); fr.alpha_composite(p, (15, 15))
        ImageDraw.Draw(fr).rectangle([6, 6, fr.width - 7, fr.height - 7], outline=CYAN, width=5)
        return fr
    return cached(('photo', w), mk)

def gooseP(c, x, y, t, s=1.0, pose='idle', shov=True, flip=False, a=1.0, walk=0, rot=0):
    def ex(im):
        goose(im)
        if shov: shovel(im, -20 + 10 * math.sin(t * 2) if pose != 'hype' else 160)
    P(c, 'Егор', x, y, t, s, pose, flip=flip, a=a, walk=walk, rot=rot, extra=ex)

def hmt(c, t, t0, t1, txt, x, y, size, col=WHITE, glow=PINK, sh=CYAN, pop=1.6, wob=True, f=None):
    if not (t0 <= t < t1): return
    im = cached(('hmt', txt, size, col, glow, sh, f), lambda: hm_text(txt, size, col, glow, sh, f))
    if im.width > W - 60: im = scaled(im, (W - 60) / im.width)
    u = t - t0; s = 1 + (pop - 1) * max(0, 1 - u / 0.12) ** 2
    if wob: im = wobble(im, t)
    put(c, scaled(im, s), x, y, clamp(min(u / 0.05, (t1 - t) / 0.15)))
def strobe(c, t, cols=((255, 30, 60), (40, 80, 255)), a=0.35, hz=6):
    k = int(t * hz) % 2; col = cols[k]
    g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(g)
    x0 = 0 if k == 0 else W / 2; d.rectangle([x0, 0, x0 + W / 2, H], fill=col + (int(255 * a),)); c.alpha_composite(g)
def ecg(c, t, y=540, col=(60, 255, 140), flat=False):
    d = ImageDraw.Draw(c); pts = []
    for x in range(0, W, 6):
        ph = (x / 520 - t * 1.1) % 1
        v = 0 if flat else (-160 * math.exp(-((ph - 0.5) / 0.012) ** 2) + 50 * math.exp(-((ph - 0.53) / 0.01) ** 2) - 20 * math.exp(-((ph - 0.7) / 0.04) ** 2))
        pts.append((x, y + v))
    d.line(pts, fill=col, width=6)
def lamps(c, t, br):
    d = ImageDraw.Draw(c)
    for i in range(3):
        x = 560 + i * 400; r = 120
        g = Image.new('RGBA', (W, H), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
        for k in range(6): gd.ellipse([x - r - k * 40, 300 - r - k * 40, x + r + k * 40, 300 + r + k * 40], fill=(255, 255, 240, int(40 * br)))
        c.alpha_composite(g); d.ellipse([x - r, 300 - r, x + r, 300 + r], fill=(255, 255, 245), outline=(180, 200, 210), width=10)
def topdown_goose(c, x, y, ang, t):
    d = ImageDraw.Draw(c)
    ca, sa = math.cos(ang), math.sin(ang)
    def rp(px, py): return (x + px * ca - py * sa, y + px * sa + py * ca)
    d.ellipse([x - 42, y - 30, x + 42, y + 30], fill=(255, 70, 160), outline=(20, 0, 30), width=5)
    d.ellipse([x - 26, y - 26, x + 26, y + 26], fill=(250, 250, 245), outline=(20, 0, 30), width=4)
    d.polygon([rp(22, -10), rp(60, 0), rp(22, 10)], fill=(255, 150, 30), outline=(20, 0, 30))
    sw = math.sin(t * 8) * 0.5
    d.line([rp(10, 34), rp(70 + 20 * sw, 60)], fill=(150, 100, 60), width=8); d.ellipse([*rp(64 + 20 * sw, 52), *[v + 22 for v in rp(64 + 20 * sw, 52)]], fill=(180, 185, 200))

# ---------------- scenes ----------------
def s_intro(c, t):  # 0–28.5
    c.alpha_composite(neon_bg(t, (255, 40, 170), (30, 10, 70), (40, 240, 255), 'rings'))
    for i, (k, x, y, d) in enumerate([(0, 420, 560, 360), (6, 960, 600, 420), (9, 1500, 560, 360)]):
        if t > 1 + i * 1.5: put_krug(c, k, t, x + 20 * math.sin(t + i), y + 15 * math.cos(t * 1.3 + i), d, clamp((t - 1 - i * 1.5) / 0.5) * (0.35 if t > 12 else 1), [PINK, CYAN, YEL][i])
    hmt(c, t, 3.0, 12.0, 'ТРОПАРЕВО', W / 2, 200, 150)
    hmt(c, t, 12.0, 20.0, 'ОРГАНЫ УБИЙЦЫ', W / 2, 440, 160, WHITE, PINK, CYAN)
    hmt(c, t, 13.5, 20.0, 'спин-офф «38»', W / 2, 600, 70, YEL, PINK, PURP, wob=False)
    if t > 20:
        n = min(38, int((t - 20) * 9) + 1)
        hmt(c, t, 20, 28.4, f'ЗАПОЙ · ДЕНЬ {n}', W / 2, 180, 110, WHITE, ORNG, PURP)
        P(c, 'Егор', 960, 1020, t, 1.1, 'drink', rot=8 * math.sin(t * 3))
        put(c, R.emoji_im('🥃', 110), 1180, 760 + 20 * math.sin(t * 4))
    if t > 27.6: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - 27.6) / 0.6)))))
    if t < 0.8: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 0.8)))))

def s_crash(c, t):  # 28.5–42.2
    c.alpha_composite(Image.new('RGBA', (W, H), (6, 4, 10, 255))); strobe(c, t, a=0.28)
    d = ImageDraw.Draw(c); d.rounded_rectangle([560, 760, 1360, 820], 16, fill=(220, 220, 230), outline=BLACK, width=5)
    P(c, 'Егор', 960, 760, 0.0, 1.0, 'sad', mouth='flat', rot=90)
    put(c, R.emoji_im('🍾', 120).rotate(100, expand=True), 1500, 860)
    put(c, rich_img('04:12 · Тропарёвский парк', 44, WHITE, F_MONO, 4), W / 2, 120, fade(t, 29, 42, 0.3, 0.3))
    put(c, rich_img('пострадавший: Егор · причина: «последний шот»', 40, (255, 200, 210), F_MONO, 4), W / 2, 190, fade(t, 30, 42, 0.3, 0.3))
    hmt(c, t, 34.0, 38.3, 'ОТКЛЮЧИЛСЯ', W / 2, 460, 150, WHITE, RED, PURP)
    if t > 38.3: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - 38.3) / 2.5)))))

def s_void(c, t):  # 42.2–58
    c.alpha_composite(Image.new('RGBA', (W, H), (2, 2, 6, 255)))
    if t < 54.3:
        ecg(c, t, 640, flat=t < 47)
        P(c, 'Егор', 960, 560 + 20 * math.sin(t), t, 0.9, 'sad', mouth='flat', a=0.5, rot=6 * math.sin(t * 0.7))
        put(c, rich_img('пульс не прощупывается' if t < 47 else 'есть пульс', 40, (60, 255, 140), F_MONO, 0), W / 2, 820, fade(t, 43, 54.3, 0.3, 0.3))
    else:
        br = 0.6 + 0.4 * math.sin(t * 25)
        c.alpha_composite(Image.new('RGBA', (W, H), (200, 230, 235, 255))); lamps(c, t, br)
        P(c, 'Егор', 960, 1120, t, 1.2, 'sad', mouth='open')

ORG = [(67.6, '🫀 ПЕЧЕНЬ'), (68.6, '🫁 ЛЁГКИЕ'), (69.6, '❤️ СЕРДЦЕ'), (70.6, '🫘 ПОЧКИ'), (71.0, '…и что-то по мелочи')]
def s_transplant(c, t):  # 58–96.4
    c.alpha_composite(vgrad_im((20, 70, 80), (10, 30, 40)))
    d = ImageDraw.Draw(c); d.rectangle([0, 860, W, H], fill=(30, 60, 70)); d.rounded_rectangle([300, 760, 1100, 830], 16, fill=(230, 235, 240), outline=BLACK, width=5)
    P(c, 'Егор', 700, 760, 0.3, 1.0, 'idle', mouth='flat', rot=90 if t < 96 else 0)
    if t > 61.8: P(c, 'Врачиха', lerp(2100, 1400, eo((t - 61.8) / 1.5)), 1000, t, 1.15, 'point' if t > 64 else 'idle', walk=2 if t < 63.3 else 0, flip=True, talk=63.5 < t < 80)
    say(c, t, 63.8, 67.4, 'Очнулся? Старая печень не пережила прайм-форму: 0,4 виски + 0,3 водки', 1400, 560, 'Врачиха', 32, 640)
    for i, (ta, s_) in enumerate(ORG):
        if t >= ta and t < 79: pill(c, s_ + (' — заменено' if i < 4 else ''), 520, 120 + i * 80, clamp((t - ta) / 0.15), (0, 0, 0, 190), CYAN, 36)
    if 71.5 <= t < 79:
        for i, ta in enumerate([71.6, 73.4, 75.4, 77.2]):
            if t > ta: hmt(c, t, ta, 79, 'ФОНД «ПАНАМА»', 960 + (i - 1.5) * 120, 260 + i * 120, 90, YEL, PINK, PURP, pop=1.8)
        put(c, rich_img('(руководитель фонда — Кирилл)', 32, WHITE, F_SERI, 3), 1400, 860, fade(t, 74, 79, 0.3, 0.3))
    if t >= 79:
        dd = Image.new('RGBA', (900, 640), (245, 242, 230, 255)); ddr = ImageDraw.Draw(dd)
        put(dd, rich_img('ДОГОВОР № 38', 52, BLACK, F_BLACK, 0), 450, 60)
        for j, l in enumerate(['Клиника не несёт ответственности за', 'привычки, вкусы и желания органов.', 'Происхождение органов: не разглашается.', 'Побочные эффекты: тяга в лес.']):
            put(dd, rich_img(l, 30, (40, 40, 40), F_SER, 0), 450, 160 + j * 60)
        for j, ta in enumerate([90.8, 94.5, 95.1, 95.7]):
            if t > ta: ddr.line([(120 + j * 170, 520), (180 + j * 170, 490), (230 + j * 170, 540), (270 + j * 170, 500)], fill=(20, 40, 160), width=5)
        put(c, dd.rotate(-3, expand=True), 960, 470, fade(t, 79, 96.4, 0.3, 0.2))
        for j, ta in enumerate([94.5, 95.1, 95.7]):
            if t > ta: hmt(c, t, ta, 96.4, 'ПОДПИСЬ', 600 + j * 360, 860, 80, WHITE, PINK, CYAN, pop=2.0)

def s_donor(c, t):  # 96.4–126.3
    c.alpha_composite(vgrad_im((14, 10, 30), (40, 14, 50)))
    d = ImageDraw.Draw(c); d.rectangle([0, 860, W, H], fill=(30, 20, 40))
    P(c, 'Егор', 420, 1000, t, 1.05, 'idle', look=1, mouth='flat' if t < 106.8 else 'open')
    put(c, rich_img('день сменяется ночью · шрам заживает', 40, CREAM, F_SERI, 3), W / 2, 110, fade(t, 96.6, 106.6, 0.4, 0.3))
    hmt(c, t, 106.8, 114.4, 'КТО ЖЕ БЫЛ ДОНОРОМ?', W / 2, 260, 110, WHITE, PINK, CYAN)
    if t > 114.4:
        card = Image.new('RGBA', (1100, 640), (240, 232, 210, 255)); cd = ImageDraw.Draw(card)
        cd.rectangle([0, 0, 1099, 639], outline=(90, 60, 30), width=8); put(card, rich_img('ДЕЛО ДОНОРА', 54, (120, 20, 20), F_BLACK, 0), 550, 60)
        cd.rectangle([60, 130, 380, 520], fill=(20, 20, 20)); put(card, rich_img('?', 200, (200, 200, 200), F_BLACK, 0), 220, 320)
        rows = [(114.6, 'Кличка: «Тропарёвский маньяк»'), (116.0, 'Место: Тропарёвский лесопарк'), (118.0, 'Приговор: высшая мера'), (120.3, 'Доказанных эпизодов: 38'), (122.0, 'Орудие: лопата')]
        for j, (ta, s_) in enumerate(rows):
            if t > ta: put(card, rich_img(s_, 34, (30, 30, 30), F_SB, 0), 420, 150 + j * 74, 1.0, 'tl')
        put(c, card.rotate(2, expand=True), 1180, 520, clamp((t - 114.4) / 0.3))
    hmt(c, t, 125.6, 126.3, 'ЭКСПЕРИМЕНТ!', W / 2, 540, 170, WHITE, RED, YEL, pop=2.2)

THOUGHTS = ['печень помнит дорогу в лес', 'сердце знает тропу', 'почки тянет в Тропарёво', 'лёгкие дышат землёй']
def s_inside(c, t):  # 126.3–153.5
    c.alpha_composite(neon_bg(t, (120, 20, 80), (10, 6, 30), (255, 60, 120), 'waves'))
    k = kick(t)
    P(c, 'Егор', 960, 1060, t, 1.3, 'idle', mouth='flat')
    for i, e in enumerate(['🫀', '🫁', '🫘']):
        put(c, scaled(R.emoji_im(e, 70), 1 + 0.3 * k), 960 + (i - 1) * 80, 930, 0.95)
    put(c, rich_img('кто бы из вас отказался?', 44, WHITE, F_SERI, 3), W / 2, 130, fade(t, 131.9, 138, 0.3, 0.3))
    if t > 145.8:
        j = int((t - 145.8) / 1.95) % 4; ta = 145.8 + int((t - 145.8) / 1.95) * 1.95
        hmt(c, t, ta, ta + 1.95, THOUGHTS[j], W / 2, 300 + (j % 2) * 120, 84, WHITE, PINK, CYAN, pop=1.4)

def s_chorus(c, t, t0=153.4, t1=184.1, start=0, end=38):  # top-down forest
    c.alpha_composite(forest_map())
    d = ImageDraw.Draw(c); G = graves(); k = kick(t)
    prog = clamp((t - t0) / (t1 - t0 - 0.6)); n = start + int(prog * (end - start))
    for i in range(min(n, 38)): draw_grave(d, G[i][0], G[i][1], i)
    a = G[max(0, n - 1)]; b = G[min(n, 37)]; f = (prog * (end - start)) % 1
    x = lerp(a[0], b[0], eio(f)); y = lerp(a[1], b[1], eio(f)); ang = math.atan2(b[1] - a[1], b[0] - a[0])
    topdown_goose(c, x, y, ang, t)
    # HUD
    put(c, hm_text_cached(f'{n * 1000:,}'.replace(',', ' ') + ' PTS', 70, YEL), 1640, 80, 1.0)
    put(c, hm_text_cached(f'{n}/38', 90, WHITE), 200, 90, 1.0)
    if k > 0.6: put(c, hm_text_cached(f'COMBO x{n}', 60, PINK), x, y - 110, 0.9)
    if f < 0.25 and n > 0: put(c, hm_text_cached('+1000 · ЗАКОПАЛ', 46, CYAN), G[n - 1][0], G[n - 1][1] - 80 - 80 * f, clamp(1 - f / 0.25))
    # cutaways to front view every 4 seconds
    if int((t - t0) / 2.0) % 4 == 3:
        c.alpha_composite(neon_bg(t, (255, 40, 170), (20, 10, 60), (40, 240, 255), 'stripes'))
        gooseP(c, 960, 1080, t, 1.6, 'hype' if int(t * 2) % 2 else 'idle')
        hmt(c, t, t - 0.01, t + 1, 'ОРГАНЫ УБИЙЦЫ ВО МНЕ', W / 2, 180, 110, WHITE, PINK, CYAN, pop=1.0)
def hm_text_cached(txt, size, col): return cached(('hmc', txt, size, col), lambda: hm_text(txt, size, col, PINK if col != PINK else PURP, CYAN))

def s_office(c, t):  # 184.1–211.2
    if t < 193.8:
        c.alpha_composite(vgrad_im((240, 236, 225), (210, 200, 190)))
        pill(c, 'ВЫПИСКА · пациент стабилен', W / 2, 140, 1.0, (0, 0, 0, 200), WHITE, 40)
        P(c, 'Егор', 760, 1020, t, 1.1, 'wave'); put(c, R.emoji_im('🥀', 120), 1300, 820)
        put(c, rich_img('цветы дома сдохли. сам выжил — и ладно', 44, (60, 60, 60), F_SERI, 0), 1250, 640)
    else:
        fl = 1.0 if (int(t * 7) % 5) else 0.35
        c.alpha_composite(vgrad_im((int(70 * fl), int(80 * fl), int(90 * fl)), (int(30 * fl), int(36 * fl), int(40 * fl))))
        d = ImageDraw.Draw(c); d.rectangle([660, 40, 1260, 70], fill=(int(250 * fl), int(255 * fl), int(240 * fl)))
        d.rectangle([200, 820, 1100, 880], fill=(120, 90, 60)); d.rectangle([380, 600, 820, 820], fill=(20, 24, 30), outline=(80, 80, 90), width=8)
        put(c, rich_img('ВШЭ · отчёт.xlsx', 30, (120, 200, 255), F_MONO, 0), 600, 700)
        P(c, 'Егор', 600, 1080, t, 1.0, 'idle', mouth='flat', look=1)
        # mirror with goose reflection
        d.rectangle([1340, 180, 1760, 860], fill=(40, 50, 60), outline=(200, 200, 210), width=12)
        if t > 196.7:
            m = Image.new('RGBA', (400, 660), (0, 0, 0, 0)); gooseP(m, 200, 720, t, 1.05, shov=False)
            put(c, m, 1550, 520, 0.9)
        if t > 201.4:
            say(c, t, 201.4, 206.2, 'бухаем?', 600, 560, 'Егор', 44)
            say(c, t, 203.4, 211.2, 'В апреле побухаем', 1100, 420, 'Никита', 36)
        if t > 206.3: hmt(c, t, 206.3, 211.2, 'ПАРАНОЙЯ', 1550, 950, 90, WHITE, RED, PURP)

def s_whisper(c, t):  # 211.2–229.4
    c.alpha_composite(Image.new('RGBA', (W, H), (8, 4, 16, 255)))
    P(c, 'Егор', 960, 1060, t, 1.1, 'sad', mouth='flat', rot=-90 if t < 220 else 0)
    words = ['выпить', 'тропа', 'зайти в лес', 'рёва', 'лопата', '38']
    for i, w_ in enumerate(words):
        ph = (t * 0.4 + i / 6) % 1
        put(c, rich_img(w_, 50, (255, 80, 160), F_SERI, 3), 960 + 650 * math.cos(ph * 6.28 + i), 420 + 260 * math.sin(ph * 6.28 * 1.3 + i), 0.35 + 0.35 * math.sin(t * 2 + i))
    if t > 215.0:
        box = Image.new('RGBA', (980, 260), (10, 10, 14, 230)); bd = ImageDraw.Draw(box); bd.rectangle([0, 0, 979, 259], outline=CYAN, width=5)
        put(box, rich_img('📞 У ВАС 1 НОВОЕ СООБЩЕНИЕ', 40, CYAN, F_MONO, 0), 490, 60)
        msg = '«Привет, это печень. Пойдём выпьем и зайдём в лес.»'; nch = int((t - 216) * 30)
        if nch > 0: put(box, rich_img(msg[:nch], 34, WHITE, F_SERI, 0), 490, 160)
        put(c, box, W / 2, 260, clamp((t - 215) / 0.3))
    hmt(c, t, 224.1, 229.4, 'ГЛАВА 38: «ВЫПИТЬ, ЗАЙТИ В ЛЕС»', W / 2, 860, 76, WHITE, PINK, CYAN, pop=1.3)

def s_forest(c, t):  # 229.4–253.4
    c.alpha_composite(park(t, 0.6, True, (t - 229.4) * 40, False))
    c.alpha_composite(Image.new('RGBA', (W, H), (120, 0, 80, 50)))
    gooseP(c, lerp(300, 1100, clamp((t - 229.4) / 10)), 1020, t, 1.15, walk=2.2 if t < 239.4 else 0)
    put(c, R.emoji_im('🍾', 80), lerp(300, 1100, clamp((t - 229.4) / 10)) - 100, 900)
    if t > 233.7:
        d = ImageDraw.Draw(c)
        P(c, 'Кирилл', 1640, 1040, t, 0.95, 'point', look=-1)
        for k in range(9): d.ellipse([1440 + k * 50 - 80, 830 - (k % 3) * 40, 1440 + k * 50 + 80, 1000 - (k % 3) * 20], fill=(20, 60, 30), outline=(10, 30, 15), width=3)
        if int(t * 2) % 2 == 0: d.ellipse([1600, 760, 1630, 790], fill=RED)
        put(c, rich_img('REC · хронист фиксирует', 30, WHITE, F_MONO, 3), 1640, 720)
    hmt(c, t, 239.4, 247.5, 'ТЕБЕ НРАВИТСЯ', W / 2, 200, 120, WHITE, PINK, CYAN)
    hmt(c, t, 240.4, 247.5, 'ЗАКАПЫВАТЬ ДРУГИХ ЛЮДЕЙ?', W / 2, 340, 110, WHITE, PINK, CYAN)
    narr(c, t, 247.8, 253.3, 'Молитвы не помогают. Лопата помогает.', y=1040)

def s_takeover(c, t):  # 253.4–290.4
    c.alpha_composite(neon_bg(t, (60, 10, 90), (6, 4, 20), (255, 40, 170), 'stripes'))
    if t < 276:
        # photo vs goose split, glitching
        g = 0.5 + 0.5 * math.sin(t * 1.3)
        put(c, photo_card(420), 560, 520, 1.0)
        m = Image.new('RGBA', (520, 640), (0, 0, 0, 0)); gooseP(m, 260, 640, t, 1.3, shov=True); put(c, m, 1360, 540)
        if kick(t) > 0.6:
            for _ in range(3):
                y0 = np.random.randint(100, 900); band = c.crop((0, y0, W, y0 + 40)); c.paste(band, (np.random.randint(-60, 60), y0))
        hmt(c, t, 253.4, 262, 'ПАМЯТЬ УБИЙЦЫ', W / 2, 120, 100, WHITE, PINK, CYAN)
        hmt(c, t, 262.0, 276, 'ВЫТЕСНЯЕТ ЛИЧНОСТЬ', W / 2, 120, 100, WHITE, RED, CYAN)
        for i, (k_, x) in enumerate([(2, 960)]):
            if t > 268: put_krug(c, 7 + int((t - 268) / 3) % 3, t, 960, 820, 300, clamp((t - 268) / 0.4), YEL)
        if t > 273.2: put(c, rich_img('третьи сутки не сплю', 40, YEL, F_MONO, 3), 960, 1010)
    else:
        # 38 hearts turn into crosses
        n = int(clamp((t - 276.2) / 11.5) * 38)
        for i in range(38):
            x = 230 + (i % 13) * 120; y = 330 + (i // 13) * 170
            if i < n:
                dd = ImageDraw.Draw(c); dd.line([x, y - 40, x, y + 40], fill=PINK, width=12); dd.line([x - 26, y - 14, x + 26, y - 14], fill=PINK, width=12)
            else: put(c, R.emoji_im('🩷', 80), x, y)
        put(c, rich_img('Егор насчитал за жизнь 38 девушек.', 54, WHITE, F_BO, 5), W / 2, 130, fade(t, 276.2, 290.4, 0.3, 0.3))
        put(c, rich_img('О них больше ничего не слышно.', 54, (255, 170, 210), F_BO, 5), W / 2, 880, fade(t, 280.0, 290.4, 0.3, 0.3))

def s_arrest(c, t):  # 290.4–300.3
    c.alpha_composite(park(t, 0.2, False, 0, False, 'storm')); strobe(c, t, a=0.32, hz=8)
    d = ImageDraw.Draw(c); d.rectangle([1300, 300, 1700, 860], fill=(60, 50, 50), outline=BLACK, width=8); put(c, rich_img('ПОДЪЕЗД', 40, WHITE, F_MONO, 0), 1500, 340)
    gooseP(c, 900, 1020, t, 1.2, 'hype' if t > 294.3 else 'drink', shov=False)
    put(c, R.emoji_im('🍾', 90), 1040, 860)
    hmt(c, t, 294.3, 300.3, 'МАСКИ-ШОУ', W / 2, 200, 160, WHITE, RED, (40, 80, 255))
    if t > 296.7: hmt(c, t, 296.7, 300.3, 'ЛИЦОМ В ПОЛ', W / 2, 400, 90, YEL, RED, PURP)

def s_court(c, t):  # 300.3–334.4
    c.alpha_composite(vgrad_im((50, 10, 40), (14, 4, 20)))
    d = ImageDraw.Draw(c); d.rectangle([660, 360, 1260, 600], fill=(90, 50, 40), outline=BLACK, width=8)
    P(c, 'Фрол', 960, 460, t, 0.9, 'point' if t > 325.9 else 'idle'); d.rectangle([660, 360, 1260, 600], outline=(255, 205, 90), width=6)
    put(c, rich_img('СУД ЧАТА · дело № 38', 40, GOLD, F_BLACK, 3), 960, 400)
    put(c, rich_img(f'ДЕЯНИЙ: 38', 50, WHITE, F_MONO, 4), 960, 130, fade(t, 300.5, 334.4, 0.3, 0.3))
    if 302.6 <= t < 318.6:
        put(c, photo_card(400), 960, 760)
        for j, ta in enumerate([302.7, 304.2, 306.2, 308.3]):
            if t > ta: hmt(c, t, ta, 318.6, 'ЭТО НЕ Я', [420, 1500, 420, 1500][j], [620, 620, 900, 900][j], 100, WHITE, RED, CYAN, pop=1.8)
        if t > 308.4:
            P(c, 'Врачиха', 1700, 1080, t, 0.8, 'shrug', flip=True)
            put(c, rich_img('это всё врачиха и фонд «Панама»!', 40, YEL, F_BO, 4), 960, 1040)
    else:
        P(c, 'Егор', 520, 1060, t, 1.0, 'shrug', mouth='open')
        P(c, 'Кирилл', 1400, 1060, t, 1.0, 'point', flip=True, talk=318.7 < t < 325.8)
        if 318.7 <= t < 325.9:
            pill(c, '📹 улика №1: видео из-за куста (с) Кирилл', 1400, 640, 1.0, (0, 0, 0, 200), CYAN, 32)
            if t > 323: pill(c, '🧪 улика №2: земля на лопате', 1400, 720, 1.0, (0, 0, 0, 200), CYAN, 32)
        if t >= 325.9:
            j = min(2, int((t - 325.9) / 2.6))
            hmt(c, t, 325.9 + j * 2.6, 325.9 + (j + 1) * 2.6 + 0.01, 'ЧТО СКАЖЕШЬ В ОПРАВДАНИЕ?', W / 2, 220, 80, WHITE, PINK, CYAN, pop=1.3)
            ans = ['я статусом повыше', 'я выше в воинском звании и ученой степени', 'Это не я!']
            say(c, t, 326.6 + j * 2.6, 326.6 + (j + 1) * 2.6, ans[j], 520, 640, 'Егор', 36, 640)

def s_final(c, t):  # 334.4–360
    if t < 340.3:
        c.alpha_composite(neon_bg(t, (255, 40, 170), (20, 6, 50), (40, 240, 255), 'rings'))
        put(c, hm_text_cached('ИТОГ', 110, WHITE), W / 2, 160)
        rows = [('ЗАКОПАНО', '38/38'), ('КОМБО', 'x38'), ('ВРЕМЯ', '465 дней'), ('РАНГ', 'S')]
        for j, (a_, b_) in enumerate(rows):
            if t > 334.6 + j * 1.2:
                put(c, hm_text_cached(a_, 64, CYAN), 720, 330 + j * 140); put(c, hm_text_cached(b_, 80 if b_ != 'S' else 130, YEL), 1220, 330 + j * 140)
    else:
        c.alpha_composite(forest_map()); d = ImageDraw.Draw(c); G = graves()
        for i in range(38): draw_grave(d, G[i][0], G[i][1], i)
        if t > 352:
            a = clamp((t - 352) / 1.5); x, y = G[38]
            draw_grave(d, x, y, 38, (255, 255, 255), 1.0 + 0.4 * (1 - a))
            put(c, hm_text_cached('39?', 90, WHITE), x, y - 110, a)
        topdown_goose(c, 960 + 500 * math.cos(t * 0.6), 560 + 300 * math.sin(t * 0.8), t * 0.6 + 1.57, t)
        hmt(c, t, 340.3, 352, 'ТРОПАРЁВСКИЙ МАНЬЯК', W / 2, 120, 110, WHITE, PINK, CYAN, pop=1.4)
        if kick(t) > 0.7: c.alpha_composite(Image.new('RGBA', (W, H), (255, 40, 170, 50)))

def s_outro(c, t):  # 360–end
    c.alpha_composite(Image.new('RGBA', (W, H), (8, 4, 14, 255)))
    a = fade(t, 360.2, T_END, 0.6, 1.5)
    put(c, rich_img('По легенде, Егор насчитал за жизнь 38 девушек.', 50, WHITE, F_SERI, 3), W / 2, 330, a)
    put(c, rich_img('О них ничего не слышно.', 50, WHITE, F_SERI, 3), W / 2, 410, a)
    put(c, rich_img('Говорят, они где-то в Тропарёвском лесу.', 50, (255, 170, 210), F_SERI, 3), W / 2, 490, a * clamp((t - 363) / 0.8))
    if t > 367: put(c, hm_text_cached('НАЖМИ R, ЧТОБЫ НАЧАТЬ ЗАПОЙ ЗАНОВО', 56, YEL), W / 2, 700, a * (0.6 + 0.4 * math.sin(t * 4)))
    if t > 370: put(c, rich_img('тропарево · спин-офф «38»', 34, (200, 190, 200), F_MONO, 0), W / 2, 960, a)

SCENES = [(0, 28.5, s_intro), (28.5, 42.2, s_crash), (42.2, 58.0, s_void), (58.0, 96.4, s_transplant), (96.4, 126.3, s_donor), (126.3, 153.4, s_inside),
          (153.4, 184.1, s_chorus), (184.1, 211.2, s_office), (211.2, 229.4, s_whisper), (229.4, 253.4, s_forest), (253.4, 290.4, s_takeover),
          (290.4, 300.3, s_arrest), (300.3, 334.4, s_court), (334.4, 360.0, s_final), (360.0, 999, s_outro)]
CUTS = [a for a, b, f in SCENES[1:]]
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.3 - 0.6 * np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2), 0.5, 1)[..., None].astype(np.float32)
def render(fi):
    t = fi / FPS
    c = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for a, b, f in SCENES:
        if a <= t < b: f(c, t); break
    out = np.asarray(c.convert('RGB')).astype(np.float32)
    k = kick(t); hot = s_is_hot(t)
    z = 1 + (0.025 if hot else 0.008) * k
    if z > 1.001: M_ = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); out = cv2.warpAffine(out, M_, (W, H), borderMode=cv2.BORDER_REFLECT)
    out = vhs(out, t, k if hot else 0.0, 3 if hot else 1)
    out = out * VIG
    for cu in CUTS:
        dt = t - cu
        if 0 <= dt < 0.12: out = out + 255 * 0.45 * (1 - dt / 0.12)
    r = np.random.default_rng(fi); out += r.normal(0, 5, (H // 3, W // 3, 1)).astype(np.float32).repeat(3, 0).repeat(3, 1)
    return np.clip(out, 0, 255).astype(np.uint8)
def s_is_hot(t): return (0 <= t < 28.5) or (126.3 <= t < 184.1) or (229.4 <= t < 300.3) or (334.4 <= t < 360)

if __name__ == '__main__':
    if sys.argv[1] == '--kick': build_kick(); sys.exit()
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:06.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--part':
        out, a, b = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '21', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, b): p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
