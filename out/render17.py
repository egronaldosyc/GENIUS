# ТРОПАРЕВО — серия 1 «Кто убил компанию?». 2D-анимация под Oxxxymiron «Кто убил Марка?». 1920x1080.
import os, sys, math, json, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path[:0] = [HERE, SP, os.path.join(SP, 'v13')]
import render13 as R
from render import text_img
from render13 import font, tokens, draw_rich, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO
import scenes as SC
from scenes import park, tentacles, eye, cork, polaroid, pin, string, void, ice_block, snow, tv, flat, table
from chars import puppet, CHAR

W, H, FPS = 1920, 1080, 30
TRACK = os.path.join(HERE, 'track.mp3')
T_END = 567.066; N = int(T_END * FPS)
F_SER = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
F_SERI = '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
WHITE = (255, 255, 255); BLACK = (0, 0, 0); RED = (220, 30, 45); GOLD = (255, 205, 90); NEON = (120, 255, 150); CREAM = (245, 235, 215)
COL = {n: CHAR[n]['col'] for n in CHAR}
NAMES = ['Егор', 'Никита', 'Фрол', 'Кирилл', 'Илья', 'Юрий', 'Коля']
ROLE = {'Егор': 'мотор, радио и основатель', 'Никита': 'спарринг-партнёр и стабилизатор', 'Фрол': 'совесть группы и мастер игры',
        'Кирилл': 'снайпер-хронист из Панамы', 'Илья': 'отсутствующий центр', 'Юрий': 'голос простоты и моральный компас', 'Коля': 'хозяин площадки'}

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(u): u = clamp(u); return 1 - (1 - u) ** 3
def eio(u): u = clamp(u); return u * u * (3 - 2 * u)
def lerp(a, b, u): return a + (b - a) * u
def fade(t, t0, t1, fi=0.4, fo=0.4): return clamp(min((t - t0) / max(fi, 1e-3), (t1 - t) / max(fo, 1e-3)))
_cache = {}
def cached(k, fn):
    if k not in _cache:
        if len(_cache) > 1500: _cache.clear()
        _cache[k] = fn()
    return _cache[k]
def alpha_im(im, a):
    if a >= 0.999: return im
    ar = np.array(im); ar[..., 3] = (ar[..., 3] * max(0, a)).astype(np.uint8); return Image.fromarray(ar)
def put(c, im, x, y, a=1.0, anchor='c'):
    if a <= 0.003: return
    im = alpha_im(im, a)
    if anchor == 'c': x -= im.width / 2; y -= im.height / 2
    elif anchor == 'b': x -= im.width / 2; y -= im.height
    x, y = int(x), int(y); sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height or x >= c.width or y >= c.height: return
    if sx or sy: im = im.crop((sx, sy, im.width, im.height))
    c.alpha_composite(im, (x + sx, y + sy))
def scaled(im, s):
    if abs(s - 1) < 0.01: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
def rich_img(txt, size, col=WHITE, f=F_BLACK, shadow=6, maxw=None, align='c', lh=1.22):
    def mk():
        fo = font(f, size); mw = maxw or 4000
        lines = R.layout(txt, fo, mw); lhp = int(size * lh)
        wid = lambda l: sum(fo.getlength(v) if k == 't' else size * 1.12 for k, v in tokens(l))
        ww = int(max(wid(l) for l in lines)) + 40
        im = Image.new('RGBA', (ww, lhp * len(lines) + 30), (0, 0, 0, 0))
        if shadow:
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0))
            for j, l in enumerate(lines):
                x = (ww - wid(l)) / 2 if align == 'c' else 20
                for dx in (-shadow, 0, shadow):
                    for dy in (-shadow, 0, shadow): draw_rich(sh, (x + dx, 12 + j * lhp + dy), l, fo, (0, 0, 0, 255))
            im.alpha_composite(sh)
        for j, l in enumerate(lines):
            x = (ww - wid(l)) / 2 if align == 'c' else 20
            draw_rich(im, (x, 12 + j * lhp), l, fo, col)
        return im
    return cached(('ri', txt, size, col, f, shadow, maxw, align), mk)
def grad(txt, size, c1, c2, f=F_BLACKI, stroke=10):
    def mk():
        base = text_img(txt, size, WHITE, (20, 0, 30), stroke, f=f, spacing=-6)
        a = np.array(base).astype(np.float32); g = np.linspace(0, 1, a.shape[0])[:, None]
        m = (a[..., 0] > 200) & (a[..., 1] > 200)
        for ch in range(3): a[..., ch] = np.where(m, c1[ch] * (1 - g) + c2[ch] * g, a[..., ch])
        return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))
    return cached(('gr', txt, size, c1, c2, f, stroke), mk)

# ---------------- primitives ----------------
def P(c, name, x, y, t, s=1.0, pose='idle', talk=False, mouth=None, flip=False, a=1.0, walk=0.0, look=0.0, prop=True, rot=0, extra=None):
    im = puppet(name, t, pose, talk, mouth, look, walk, prop, NAMES.index(name) if name in NAMES else 0)
    if extra: extra(im)
    if flip: im = im.transpose(Image.FLIP_LEFT_RIGHT)
    if rot: im = im.rotate(rot, resample=Image.BICUBIC, expand=False)
    im = scaled(im, s)
    put(c, im, x - im.width / 2, y - 392 * s, a, 'tl')
def bubble_im(text, who=None, fs=34, maxw=620):
    def mk():
        fo = font(F_MED, fs); lines = R.layout(text, fo, maxw - 50); lh = int(fs * 1.26)
        wid = lambda l: sum(fo.getlength(v) if k == 't' else fs * 1.12 for k, v in tokens(l))
        nh = 36 if who else 0
        bw = int(max(max(wid(l) for l in lines) + 50, (font(F_BO, 26).getlength(who) + 50) if who else 0, 120)); bh = nh + lh * len(lines) + 34
        im = Image.new('RGBA', (bw + 10, bh + 40), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([4, 8, bw + 6, bh + 6], 28, fill=(0, 0, 0, 90))
        d.rounded_rectangle([0, 0, bw, bh], 28, fill=(255, 255, 255, 250), outline=(20, 18, 30), width=5)
        d.polygon([(bw * 0.5 - 22, bh - 3), (bw * 0.5 + 18, bh - 3), (bw * 0.5 - 4, bh + 34)], fill=(255, 255, 255, 250))
        d.line([(bw * 0.5 - 22, bh - 1), (bw * 0.5 - 4, bh + 34), (bw * 0.5 + 18, bh - 1)], fill=(20, 18, 30), width=5)
        if who: d.text((25, 14), who, font=font(F_BO, 26), fill=tuple(int(v * 0.8) for v in COL.get(who, (90, 90, 90))))
        for j, l in enumerate(lines): draw_rich(im, (25, 16 + nh + j * lh), l, fo, (20, 18, 30))
        return im
    return cached(('bub', text, who, fs, maxw), mk)
def say(c, t, t0, t1, text, x, y, who=None, fs=34, maxw=620):
    """bubble whose tail tip is at (x, y)"""
    if not (t0 <= t < t1): return
    u = t - t0; e = easeback(clamp(u / 0.28)); a = clamp(min(u / 0.1, (t1 - t) / 0.2))
    im = bubble_im(text, who, fs, maxw); im2 = scaled(im, 0.6 + 0.4 * e)
    bx = clamp(x - im2.width / 2, 20, W - 20 - im2.width)
    put(c, im2, bx, y - im2.height, a, 'tl')
def narr(c, t, t0, t1, text, y=990, size=42, col=CREAM):
    if not (t0 <= t < t1): return
    a = fade(t, t0, t1, 0.3, 0.4); n = int((t - t0) * 45)
    full = rich_img(text, size, col, F_SERI, 4, 1700)
    # typewriter via crop mask by characters: approximate with width share
    frac = clamp(n / max(1, len(text)))
    band = Image.new('RGBA', (full.width + 60, full.height + 10), (0, 0, 0, 150))
    put(c, band, W / 2, y, a * 0.9)
    vis = full.crop((0, 0, max(1, int(full.width * frac)), full.height)) if frac < 1 and '\n' not in text else full
    if frac < 1 and '\n' not in text: put(c, vis, W / 2 - full.width / 2, y - full.height / 2, a, 'tl')
    else: put(c, full, W / 2, y, a)
def title(c, t, t0, t1, text, y=420, size=150, c1=(255, 70, 160), c2=GOLD, pop=1.8, shake=0, sub=None, subsize=46):
    if not (t0 <= t < t1): return
    u = t - t0; s = 1 + (pop - 1) * max(0, 1 - u / 0.14) ** 2; a = clamp(min(u / 0.06, (t1 - t) / 0.25))
    im = grad(text, size, c1, c2);
    if im.width > W - 80: im = scaled(im, (W - 80) / im.width)
    dx = shake * math.sin(u * 90) * max(0, 1 - u / 0.5)
    put(c, scaled(im, s), W / 2 + dx, y, a)
    if sub: put(c, rich_img(sub, subsize, WHITE, F_BO, 4), W / 2, y + im.height / 2 + 50, a * clamp((u - 0.2) / 0.25))
def pill(c, text, x, y, a=1.0, bg=(0, 0, 0, 190), fg=WHITE, size=30):
    def mk():
        fo = font(F_SB, size); w = int(sum(fo.getlength(v) if k == 't' else size * 1.12 for k, v in tokens(text))) + 50
        im = Image.new('RGBA', (w, size + 26), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, size + 25], (size + 26) // 2, fill=bg); draw_rich(im, (25, 10), text, fo, fg); return im
    put(c, cached(('pill', text, bg, fg, size), mk), x, y, a)
def stamp(c, t, t0, t1, text, col, x, y, rot=-8, size=80):
    if not (t0 <= t < t1): return
    def mk():
        tx = text_img(text, size, col, col, 0, f=F_BLACK)
        fr = Image.new('RGBA', (tx.width + 50, tx.height + 30), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle([4, 4, fr.width - 5, fr.height - 5], 14, outline=col + (255,), width=9)
        fr.alpha_composite(tx, (25, 15)); a = np.array(fr); m = np.random.default_rng(len(text)).random(a.shape[:2]) < 0.16; a[m, 3] = (a[m, 3] * 0.3).astype(np.uint8)
        return Image.fromarray(a).rotate(rot, expand=True, resample=Image.BICUBIC)
    u = t - t0; s = 1 + 1.4 * max(0, 1 - u / 0.12) ** 2
    put(c, scaled(cached(('st', text, col, rot, size), mk), s), x, y, clamp(min(u / 0.05, (t1 - t) / 0.2)))
def cap_small(c, text, x, y, a=1.0, size=30, col=WHITE, f=F_SB): put(c, rich_img(text, size, col, f, 3), x, y, a)
def bg_fill(col): return Image.new('RGBA', (W, H), col + (255,))
def vgrad_im(c0, c1): return Image.fromarray(SC.vgrad(c0, c1).astype(np.uint8)).convert('RGBA')

# ---------------- beat / kick ----------------
BEAT = 60 / 120.25; OFF = 0.28
KP = os.path.join(HERE, 'kick.npy')
def build_kick():
    sr = 11025
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', TRACK, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32); lo = np.convolve(x, np.ones(40) / 40, 'same')
    hop = sr // FPS; n = len(lo) // hop; e = np.sqrt(np.mean(lo[:n * hop].reshape(n, hop) ** 2, 1))
    d = np.maximum(0, e - np.concatenate([[0], e[:-1]])); d = np.clip(d / (np.percentile(d, 99.5) + 1e-9), 0, 1)
    out = np.zeros_like(d); acc = 0
    for i in range(len(d)): acc = max(d[i], acc * 0.72); out[i] = acc
    np.save(KP, out.astype(np.float32))
KICK = np.load(KP) if os.path.exists(KP) else np.zeros(N + 10, np.float32)
def kick(t): i = int(t * FPS); return float(KICK[i]) if 0 <= i < len(KICK) else 0.0

# ---------------- extra props ----------------
def cape(im):  # superhero cape behind body (drawn on puppet canvas, before flip)
    d = ImageDraw.Draw(im, 'RGBA')
    cp = Image.new('RGBA', im.size, (0, 0, 0, 0)); dd = ImageDraw.Draw(cp)
    dd.polygon([(115, 215), (205, 215), (250, 380), (70, 380)], fill=(200, 20, 60), outline=(22, 18, 30), width=5)
    cp.alpha_composite(im); im.paste(cp)
def furry(im):
    d = ImageDraw.Draw(im)
    for x0 in (98, 192):
        d.polygon([(x0, 82), (x0 + 30, 82), (x0 + 15, 40)], fill=(200, 150, 90), outline=(22, 18, 30), width=4)
    d.ellipse([228, 300, 300, 330], fill=(200, 150, 90), outline=(22, 18, 30), width=4)
def crown(im):
    d = ImageDraw.Draw(im); d.polygon([(110, 70), (130, 30), (150, 62), (160, 22), (170, 62), (190, 30), (210, 70)], fill=(255, 205, 60), outline=(22, 18, 30), width=4)
def tears(im, t):
    d = ImageDraw.Draw(im)
    for k, x0 in enumerate((128, 192)):
        y = 120 + ((t * 120 + k * 40) % 80); d.ellipse([x0 - 6, y - 6, x0 + 6, y + 10], fill=(120, 190, 255), outline=(30, 60, 120), width=2)

# ---------------- scenes ----------------
L = lambda: None
def chalk(c, a=1.0):
    d = ImageDraw.Draw(c); col = (240, 240, 240, int(220 * a)); cx, cy = 960, 960
    d.ellipse([cx - 230, cy - 60, cx - 150, cy + 20], outline=col, width=6)
    d.line([(cx - 150, cy - 20), (cx + 60, cy - 30), (cx + 160, cy - 80), (cx + 230, cy - 60)], fill=col, width=6)
    d.line([(cx + 60, cy - 30), (cx + 170, cy + 20), (cx + 250, cy + 60)], fill=col, width=6)
    d.line([(cx - 80, cy - 24), (cx - 40, cy - 100), (cx + 10, cy - 120)], fill=col, width=6)
    d.line([(cx - 60, cy - 22), (cx - 110, cy + 70)], fill=col, width=6)
def tape(c, y, ang, a=1.0, txt='НЕ ПЕРЕСЕКАТЬ · ТРОПАРЕВО 8.6 · '):
    def mk():
        im = Image.new('RGBA', (2600, 70), (250, 210, 40, 255)); d = ImageDraw.Draw(im); fo = font(F_BLACK, 38)
        x = 10
        while x < 2600: d.text((x, 10), txt, font=fo, fill=(15, 15, 15)); x += fo.getlength(txt)
        return im.rotate(ang, expand=True, resample=Image.BICUBIC)
    put(c, cached(('tape', ang, txt), mk), W / 2, y, a)

def s_cold(c, t):  # 0–30
    u = t
    bg = park(t, mood=0.15); c.alpha_composite(bg)
    chalk(c, fade(t, 6, 40, 2, 1)); put(c, rich_img('КОМПАНИЯ', 34, (240, 240, 240), F_MONO, 0), 960, 1040, fade(t, 7, 40, 1.5, 1))
    tape(c, 760, 4, fade(t, 9, 40, 0.6, 1)); tape(c, 820, -3, fade(t, 9.4, 40, 0.6, 1))
    # detective walks in
    if t > 12:
        x = lerp(-150, 640, eio((t - 12) / 6)); walking = t < 18
        P(c, 'Кирилл', x, 1000, t, 1.15, 'idle' if not walking else 'idle', walk=2.2 if walking else 0, look=0.6)
        if t > 19: say(c, t, 19.5, 26.5, 'Так. Записываю.', 640, 560, 'Кирилл')
    a = fade(t, 1.5, 11.5, 1.2, 1.0)
    put(c, rich_img('«Самое древнее и сильное чувство человечества — страх.\nСамый древний и сильный вид страха —\nстрах перед фразой «в апреле побухаем»»', 46, CREAM, F_SERI, 3, 1600), W / 2, 330, a)
    put(c, rich_img('— почти Г. Ф. Лавкрафт', 32, (200, 190, 170), F_SERI, 3), W / 2 + 420, 520, a)
    narr(c, t, 13, 21.5, 'Тропарёвский лесопарк. 04:12. Обнаружено тело. Личность установлена: КОМПАНИЯ.')
    narr(c, t, 21.6, 28.4, 'Свидетели: 7 человек. Улики: 59 177 сообщений. Подозреваемые: все.')
    if t >= 28.3:
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(200 * clamp((t - 28.3) / 0.4)))))
        title(c, t, 28.6, 31, 'КТО УБИЛ КОМПАНИЮ?', 470, 140, RED, GOLD, 2.2, 18, 'ТРОПАРЕВО · серия 1')
    if t < 1.5: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 1.5)))))

def s_cinema(c, t):  # 30–43
    u = t - 30; c.alpha_composite(vgrad_im((14, 10, 20), (30, 20, 30)))
    d = ImageDraw.Draw(c)
    # projector beam
    beam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam); bd.polygon([(960, 1080), (420, 520), (1500, 520)], fill=(255, 250, 220, 26)); c.alpha_composite(beam)
    d.rectangle([410, 60, 1510, 540], fill=(235, 232, 220), outline=(90, 70, 50), width=10)
    scr = Image.new('RGBA', (1080, 460), (20, 20, 24, 255)); sd = ImageDraw.Draw(scr)
    k = int(u / (BEAT * 2))
    if u < 4.2:
        n = 3 - int(u / 1.4); sd.ellipse([390, 80, 690, 380], outline=(220, 220, 220), width=8)
        ang = (u % 1.4) / 1.4 * 360; sd.pieslice([390, 80, 690, 380], -90, -90 + ang, fill=(90, 90, 90))
        sd.line([540, 40, 540, 420], fill=(200, 200, 200), width=3); sd.line([340, 230, 740, 230], fill=(200, 200, 200), width=3)
        fo = font(F_BLACK, 200); sd.text((540 - fo.getlength(str(max(1, n))) / 2, 110), str(max(1, n)), font=fo, fill=WHITE)
    else:
        put(scr, rich_img('ДЕЛО № 8.6', 90, GOLD, F_BLACK, 0), 540, 150); put(scr, rich_img('РЕТРОСПЕКТИВА', 64, WHITE, F_BLACK, 0), 540, 260)
        put(scr, rich_img('16.07.2025 — 08.11.2026', 38, (200, 200, 210), F_MONO, 0), 540, 350)
    c.alpha_composite(scr, (420, 70))
    # seats row + audience
    for i, n in enumerate(NAMES):
        x = 330 + i * 210; P(c, n, x, 1090, t, 1.0, 'idle', look=0, mouth='open' if u > 8 and i < 2 else None)
    for i in range(9):
        x = 230 + i * 190; d.rounded_rectangle([x - 90, 880, x + 90, 1080], 30, fill=(120, 20, 40), outline=(40, 6, 14), width=6)
    # popcorn
    pc = R.emoji_im('🍿', 90); put(c, pc, 330 + 3 * 210 + 90, 860); put(c, R.emoji_im('🍕', 80), 330 + 0 * 210 + 90, 860)
    say(c, t, 35.5, 40, 'че', 330, 700, 'Егор', 44)
    say(c, t, 36.6, 40.5, 'и зачем папки', 330, 560, 'Егор', 34)
    say(c, t, 38.2, 43, 'А вот что это за говно нерусское', 540, 700, 'Никита', 34)
    narr(c, t, 31, 35.3, 'Запаситесь терпением и попкорном. Фильм идёт 465 дней.')
    put(c, rich_img('16.07.2025 · первое сообщение', 28, (200, 200, 210), F_MONO, 3), 960, 600, fade(t, 35.3, 43, 0.3, 0.3))

TL = [('2014', 'v1.0', 'эра до Егора: мемы про ахмеда'), ('', 'v2.0', 'дэдпул, гражданская война, кюрпек и огэ'), ('2017', 'v3.0', 'золотая эпоха лета 2017'),
      ('', 'v4.0', 'стагнация, но по сравнению с сейчас — движ'), ('2020', 'v5.0', 'пандемийная: говядина со сгущёнкой'), ('', 'v5.5', 'ваш прайм, дача Кирилла, я в армии'),
      ('2021', 'v6.0', 'прайм с частыми сборами'), ('', 'v8.1', 'эра анфисы'), ('2025', 'v8.5', 'появился ДнД'), ('2026', 'v8.6', '← ВЫ ЗДЕСЬ')]
def s_timeline(c, t):  # 43–56
    u = t - 43; c.alpha_composite(vgrad_im((20, 30, 60), (60, 40, 80)))
    if u < 5: snow(c, t, 220, 120)
    off = 1100 - u * 560; d = ImageDraw.Draw(c)
    d.line([0, 760, W, 760], fill=(255, 255, 255, 200), width=8)
    for i, (yr, v, txt) in enumerate(TL):
        x = off + i * 560
        if -400 < x < W + 400:
            d.ellipse([x - 22, 738, x + 22, 782], fill=GOLD if v != 'v8.6' else RED, outline=BLACK, width=5)
            put(c, rich_img(v, 70, GOLD if v != 'v8.6' else RED, F_BLACK, 5), x, 660)
            if yr: put(c, rich_img(yr, 40, WHITE, F_MONO, 3), x, 590)
            put(c, rich_img(txt, 30, WHITE, F_SB, 3, 480), x, 840)
    P(c, 'Егор', 860, 1060, t, 0.62, walk=2.3); P(c, 'Никита', 1060, 1060, t, 0.62, walk=2.3)
    if u < 5: put(c, rich_img('ICE AGE · эпоха «до чата»', 44, (200, 230, 255), F_BLACK, 5), W / 2, 200, fade(t, 43.2, 48, 0.3, 0.4))
    else: put(c, rich_img('ИСТОРИЯ ВЕРСИЙ (с) Егор, 10.08.2026', 40, WHITE, F_BLACK, 5), W / 2, 200, fade(t, 48, 56, 0.3, 0.3))

def s_doors(c, t):  # 56–66
    u = t - 56; c.alpha_composite(vgrad_im((10, 10, 16), (40, 34, 50)))
    d = ImageDraw.Draw(c); d.polygon([(0, 1080), (560, 760), (1360, 760), (1920, 1080)], fill=(50, 44, 60))
    labels = ['СДАТЬСЯ', 'ИЗМЕНИТЬСЯ', 'СОЗДАТЬ ЧАТ']; sel = -1
    if t > 58.4: sel = 0
    if t > 60.9: sel = 1
    if t > 63.2: sel = 2
    for i, lb in enumerate(labels):
        x = 480 + i * 480; op = eo((t - 63.4) / 0.6) if i == 2 else 0
        glow = (i == sel)
        d.rectangle([x - 130, 300, x + 130, 760], fill=(255, 240, 200) if (i == 2 and op > 0) else (70, 50, 40), outline=(255, 220, 120) if glow else (20, 14, 10), width=10 if glow else 6)
        if op < 1: d.rectangle([x - 120 + 240 * op * 0.8, 310, x + 120, 750], fill=(110, 76, 52), outline=(30, 20, 14), width=4); d.ellipse([x + 80, 520, x + 100, 540], fill=GOLD)
        put(c, rich_img(lb, 44 if i < 2 else 46, GOLD if glow else (200, 190, 180), F_BLACK, 4), x, 250)
        if i < 2 and sel > i: put(c, R.emoji_im('❌', 120), x, 520, 0.9)
    ex = lerp(960, 1440, eo((t - 63.8) / 1.6)) if t > 63.8 else 960; ey = lerp(1000, 820, eo((t - 63.8) / 1.6)) if t > 63.8 else 1000
    sc = lerp(1.0, 0.6, eo((t - 63.8) / 1.6)) if t > 63.8 else 1.0
    lookx = -1 if sel == 0 else (0 if sel == 1 else 1)
    P(c, 'Егор', ex, ey, t, sc, 'point' if sel == 2 else 'idle', look=lookx, walk=2.2 if t > 63.8 else 0)
    narr(c, t, 56.2, 63, 'У каждого есть выбор: сдаться, измениться… или')
    if t > 64.6: pill(c, '«Тропарево 8.6» converted a basic group to this supergroup', W / 2, 140, fade(t, 64.6, 66, 0.2, 0.2), size=30)

def s_hero(c, t):  # 66–84
    u = t - 66; c.alpha_composite(vgrad_im((40, 30, 90), (255, 130, 120)))
    d = ImageDraw.Draw(c)
    rng = np.random.default_rng(4)
    xo = (u * 160) % 300
    for i in range(16):
        bw_ = 80 + (i * 37) % 70; bh_ = 160 + (i * 53) % 260; x = i * 130 - xo
        d.rectangle([x, 1080 - bh_, x + bw_, 1080], fill=(30, 22, 50))
        for wy in range(1080 - bh_ + 20, 1060, 40):
            for wx in range(int(x) + 12, int(x + bw_) - 12, 26):
                if (wx * 7 + wy * 3 + i) % 5: d.rectangle([wx, wy, wx + 10, wy + 16], fill=(255, 220, 120))
    x = 760 + 120 * math.sin(u * 0.8); y = 640 + 50 * math.sin(u * 1.7)
    P(c, 'Егор', x, y, t, 1.1, 'hype', rot=-14, extra=cape)
    for k in range(5): d.line([x - 260 - k * 40, y - 200 + k * 30, x - 120 - k * 40, y - 200 + k * 30], fill=(255, 255, 255, 120), width=4)
    title(c, t, 66.3, 72, 'МОТОР И РАДИО ЧАТА', 150, 100, (255, 70, 160), GOLD, 1.8)
    stats = [(68.6, '30 815 сообщений'), (70.0, 'писал в 443 днях из 465'), (71.4, 'начал 462 разговора из 856')]
    for i, (ta, s_) in enumerate(stats):
        if t >= ta and t < 76: pill(c, s_, 1550, 360 + i * 80, fade(t, ta, 76, 0.2, 0.3), (0, 0, 0, 170), GOLD, 34)
    lines = [(76.4, 'ты еблан?'), (77.4, 'А ПОМНИТЕ…'), (78.4, 'смета? с руководителем (Сашей) согласовано?'), (79.5, 'АХАХАХ ПОНЯЛИ ТИПА'),
             (80.6, 'я контентмейкер и сммщик данного чата'), (81.8, 'я выше в воинском звании и ученой степени')]
    for i, (ta, s_) in enumerate(lines):
        if ta <= t < 84:
            px = [1350, 1450, 1250, 1480, 1300, 1420][i]; py = [360, 520, 680, 300, 820, 460][i]
            say(c, t, ta, 84, s_, px, py + 20 * math.sin(t + i), 'Егор', 36, 560)
    narr(c, t, 76.2, 84, 'Костюм супергероя есть. Инструкции, как отвечать за свои слова, — нет.', y=1010, size=38)

def imp(c, x, y, lab, t, k):
    d = ImageDraw.Draw(c); d.ellipse([x - 34, y - 34, x + 34, y + 34], fill=(120, 40, 160), outline=(22, 10, 30), width=5)
    d.polygon([(x - 30, y - 20), (x - 20, y - 60), (x - 8, y - 30)], fill=(120, 40, 160)); d.polygon([(x + 30, y - 20), (x + 20, y - 60), (x + 8, y - 30)], fill=(120, 40, 160))
    d.ellipse([x - 16, y - 10, x - 4, y + 2], fill=(255, 230, 60)); d.ellipse([x + 4, y - 10, x + 16, y + 2], fill=(255, 230, 60))
    d.arc([x - 14, y + 4, x + 14, y + 20], 20, 160, fill=(22, 10, 30), width=4)
    cap_small(c, lab, x, y + 60, 1.0, 26, (230, 190, 255))
def s_partner(c, t):  # 84–95
    u = t - 84; c.alpha_composite(vgrad_im((10, 20, 50), (20, 50, 110)))
    d = ImageDraw.Draw(c)
    sp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sp); sd.polygon([(1180, 0), (1500, 0), (1700, 1000), (980, 1000)], fill=(255, 255, 230, 40)); c.alpha_composite(sp)
    d.ellipse([960, 940, 1720, 1060], fill=(255, 255, 220, 60))
    put(c, R.emoji_im('🗿', 520), 1340, 420, 0.22)
    P(c, 'Никита', 1340, 1000, t, 1.3, 'idle' if u < 9 else 'point', talk=t > 92.5)
    P(c, 'Егор', 420, 1000, t, 0.9, 'idle', look=1, a=0.85)
    title(c, t, 84.2, 95, 'НАПАРНИК', 210, 110, (70, 150, 255), (180, 220, 255), 1.6, sub='Никита · спарринг-партнёр и стабилизатор', subsize=40)
    if t > 86.8: pill(c, '83% его ответов — Егору', 420, 420, fade(t, 86.8, 95, 0.2, 0.3), (0, 0, 0, 170), (140, 190, 255), 34)
    if t > 89.2:
        labs = ['дэп', 'додэп', 'ластдэп', 'ультрамегаластдэп']
        for i, lb in enumerate(labs):
            if t > 89.2 + i * 0.5:
                a_ = u * 1.3 + i * math.pi / 2; imp(c, 1340 + 330 * math.cos(a_), 640 + 120 * math.sin(a_), lb, t, i)
    say(c, t, 92.6, 95, 'Угу-угу продолжай 🗿', 1340, 560, 'Никита', 40)

def s_duo(c, t):  # 95–112
    u = t - 95; c.alpha_composite(vgrad_im((10, 6, 20), (40, 10, 50)))
    d = ImageDraw.Draw(c); k = kick(t)
    for i in range(6):
        ang = math.sin(t * 1.2 + i) * 0.5; x0 = 160 + i * 320
        L_ = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(L_)
        col = [(255, 70, 160), (70, 150, 255), (255, 205, 90)][i % 3]
        ld.polygon([(x0, 0), (x0 + 900 * math.sin(ang) - 140, 1080), (x0 + 900 * math.sin(ang) + 140, 1080)], fill=col + (int(30 + 40 * k),)); c.alpha_composite(L_)
    d.rectangle([0, 820, W, 1080], fill=(26, 20, 34)); d.rectangle([0, 820, W, 836], fill=(255, 205, 90))
    # LED banner
    d.rectangle([360, 70, 1560, 300], fill=(10, 10, 14), outline=(60, 60, 70), width=8)
    if u < 7: put(c, rich_img('АЛЬЯНС', 120, (255, 70, 160) if int(t * 4) % 2 else GOLD, F_BLACK, 0), 960, 185)
    elif u < 12.7: put(c, rich_img('53% + 27% = 80% ВСЕЙ ПЕРЕПИСКИ', 62, GOLD, F_BLACK, 0), 960, 185)
    else: put(c, rich_img('КУЛЬТОВЫЙ ЧАТ ЮГО-ЗАПАДА', 66, NEON, F_BLACK, 0), 960, 185)
    hy = int((t - OFF) / BEAT) % 2
    P(c, 'Егор', 760, 830, t, 1.25, 'hype' if hy else 'point', talk=True); P(c, 'Никита', 1160, 830, t, 1.25, 'hype' if not hy else 'idle', talk=False, flip=True)
    for i, n in enumerate(['Фрол', 'Кирилл', 'Илья', 'Юрий', 'Коля']):
        P(c, n, 260 + i * 350, 1150, t + i * 0.2, 0.75, 'hype' if (int(t * 2 + i) % 2) else 'wave')
    if t > 109.4:
        pill(c, 'ВШЭ · звание · топ 80 из 2600', 760, 330, fade(t, 109.4, 112, 0.2, 0.2), (0, 0, 0, 180), (255, 140, 200), 30)
        pill(c, 'Угу-угу 🗿', 1160, 330, fade(t, 109.9, 112, 0.2, 0.2), (0, 0, 0, 180), (140, 190, 255), 30)

def chat_panel(c, x0, y0, w, h):
    d = ImageDraw.Draw(c); d.rounded_rectangle([x0, y0, x0 + w, y0 + h], 30, fill=(20, 24, 32), outline=(60, 70, 90), width=5)
    d.rounded_rectangle([x0, y0, x0 + w, y0 + 90], 30, fill=(32, 40, 56)); put(c, rich_img('Тропарево 8.6', 34, WHITE, F_BO, 0), x0 + w / 2, y0 + 45)
def s_exits(c, t):  # 112–124
    u = t - 112; c.alpha_composite(vgrad_im((14, 16, 24), (26, 30, 44)))
    chat_panel(c, 120, 80, 900, 920)
    evs = [(112.3, 'Егор Гусев вышел из беседы', RED), (113.6, 'Егор Гусев вернулся в группу', NEON), (114.9, 'Егор Гусев вышел из беседы', RED),
           (116.2, 'Егор Гусев вернулся в группу', NEON), (117.5, 'Егор Гусев вышел из беседы', RED), (118.6, 'Егор Гусев вернулся в группу', NEON),
           (119.9, 'Егор Гусев вышел из беседы', RED), (121.0, 'Егор Гусев вернулся в группу', NEON), (122.3, 'Егор Гусев вышел из беседы', RED)]
    vis = [e for e in evs if e[0] <= t][-10:]
    for i, (ta, s_, col) in enumerate(reversed(vis)):
        pill(c, s_, 570, 930 - i * 78, clamp((t - ta) / 0.15), (0, 0, 0, 200), col, 30)
    # door
    d = ImageDraw.Draw(c); d.rectangle([1500, 330, 1760, 900], fill=(80, 56, 40), outline=(20, 12, 8), width=8)
    put(c, rich_img('ВЫХОД', 40, (120, 255, 120), F_BLACK, 0), 1630, 300)
    ph = (u % 2.6) / 2.6; ex = 1300 + 300 * math.sin(ph * math.pi)
    P(c, 'Егор', ex, 900, t, 0.95, walk=2.4, flip=ph > 0.5)
    P(c, 'Кирилл', 1180, 1060, t, 0.7, 'idle', look=1)
    yrs = ['2019', '2020', '2021', '2022', '2023', '2024', '2025', '2026']
    for i, y_ in enumerate(yrs):
        if t > 113 + i * 1.2: put(c, rich_img(y_, 34, GOLD, F_MONO, 3), 1080 + (i % 2) * 120, 520 + (i // 2) * 60)
    put(c, rich_img('статистика уходов (с) Кирилл', 28, (200, 200, 210), F_SB, 3), 1140, 470, fade(t, 113, 124, 0.3, 0.3))
    narr(c, t, 117.6, 124, 'Токсичная дружба. Уйти нельзя остаться.')

def s_storm(c, t):  # 124–143
    u = t - 124; c.alpha_composite(park(t, 0.0, False, u * 20, True, 'storm'))
    k = kick(t); d = ImageDraw.Draw(c)
    rng = np.random.default_rng(int(t * 30))
    for i in range(140):
        x = rng.uniform(0, W); y = rng.uniform(0, H); d.line([x, y, x - 14, y + 50], fill=(170, 190, 230, 150), width=2)
    if k > 0.75 and int(t * 10) % 3 == 0: c.alpha_composite(Image.new('RGBA', (W, H), (220, 230, 255, 90)))
    P(c, 'Никита', 560, 1000, t, 1.2, 'point' if u > 6 else 'idle', talk=4 < u < 9)
    P(c, 'Егор', 1360, 1000, t, 1.2, 'shrug' if u > 9 else 'idle', flip=True, talk=9 < u < 14)
    title(c, t, 124.2, 127.8, 'ЖАНР СМЕНИЛСЯ', 260, 140, (255, 255, 255), (160, 170, 190), 2.0, 14, 'теперь это боевик')
    title(c, t, 128.0, 136, 'ПАРК В ШТОРМ', 220, 150, (255, 210, 90), (255, 90, 40), 1.8, 10, '03—05.09.2026')
    say(c, t, 128.4, 133, 'водку в парке?', 560, 560, 'Никита', 40)
    say(c, t, 133.2, 140, 'я в такую погоду в парк не пойду, я статусом повыше', 1360, 560, 'Егор', 36, 640)
    for i, (ta, w_) in enumerate([(129.9, 'БАМ!'), (131.4, 'ХРЯСЬ!'), (132.9, 'ЛЕЩ!'), (134.9, 'БДЫЩ!'), (136.9, 'ВЖУХ!'), (138.9, 'ЛЕЩ!!')]):
        if ta <= t < ta + 1.4:
            im = grad(w_, 150, (255, 230, 60), (255, 80, 40), F_BLACKI, 12); s = 1 + 0.8 * max(0, 1 - (t - ta) / 0.12) ** 2
            put(c, scaled(im, s).rotate([-10, 8, -6, 12, -8, 6][i], expand=True), [960, 760, 1160, 900, 1060, 960][i], [640, 380, 700, 420, 600, 380][i], clamp((ta + 1.4 - t) / 0.3))
    narr(c, t, 138.9, 143, 'Первый урок: в шторм в парк не ходят. Даже за водкой.')

def s_court(c, t):  # 143–172
    u = t - 143; c.alpha_composite(vgrad_im((60, 40, 30), (30, 20, 16)))
    d = ImageDraw.Draw(c)
    for x in range(0, W, 160): d.rectangle([x, 0, x + 12, 700], fill=(80, 56, 40))
    d.rectangle([0, 700, W, H], fill=(70, 46, 32))
    P(c, 'Фрол', 960, 560, t, 1.1, 'point' if 150 < t < 158 else 'idle', talk=150 < t < 158)
    d.rectangle([660, 470, 1260, 720], fill=(110, 70, 44), outline=(40, 24, 14), width=8)
    put(c, rich_img('СОВЕСТЬ ГРУППЫ', 40, GOLD, F_BLACK, 3), 960, 560)
    # gavel
    hit = (t - OFF) % (BEAT * 4) < 0.12 and (143 < t < 147 or 164.5 < t < 168)
    gx, gy = 1180, 420 + (40 if hit else 0)
    d.rounded_rectangle([gx - 50, gy - 25, gx + 50, gy + 25], 8, fill=(120, 70, 40), outline=BLACK, width=4); d.line([gx, gy, gx + 60, gy - 80], fill=(100, 60, 30), width=12)
    P(c, 'Егор', 420, 1060, t, 1.05, 'shrug' if 158 < t < 166 else 'idle', look=1, talk=158 < t < 164)
    P(c, 'Никита', 1500, 1060, t, 1.05, 'idle', look=-1, flip=True)
    title(c, t, 143.2, 148.5, 'СУД ЧАТА', 150, 120, GOLD, (255, 140, 60), 1.6, sub='дело о троллинге статусом', subsize=38)
    say(c, t, 149.3, 157.5, 'мне похуй на твою очередную попытку задеть кого-то по признаку зарплат и социального статуса', 960, 330, 'Фрол', 32, 820)
    put(c, rich_img('Фрол, 04.02.2026', 26, (230, 220, 200), F_MONO, 3), 1500, 80, fade(t, 149.3, 157.5, 0.2, 0.2))
    narr(c, t, 157.8, 164.5, 'Варианты: извиниться публично — или сгинуть в чате навсегда.')
    say(c, t, 159, 164, 'ладно', 420, 620, 'Егор', 40)
    stamp(c, t, 165, 172, 'ИЗВИНЕНИЕ ПРИНЯТО', (60, 200, 90), 960, 860, -7, 90)
    narr(c, t, 168.5, 172, 'Конфликт исчерпан. Видео в сеть не попало.')

def s_ice(c, t):  # 172–191
    u = t - 172; c.alpha_composite(flat(t, 0)); c.alpha_composite(Image.new('RGBA', (W, H), (120, 170, 230, 70)))
    snow(c, t, 260, 60)
    xs = [260, 500, 740, 980, 1220, 1460, 1700]
    for i, n in enumerate(NAMES):
        if n == 'Коля' and t < 179: continue
        P(c, n, xs[i], 1020, 0.3 + i, 0.8, 'idle', mouth='flat')
        put(c, ice_block(250, 360), xs[i] - 125, 1020 - 350, clamp((t - 172.5 - i * 0.3) / 0.5), 'tl')
    if t < 179:
        x = lerp(1660, 1880, eo((t - 175.6) / 2)) if t > 175.6 else 1660
        P(c, 'Коля', x, 1020, t, 0.8, 'point' if t < 176.8 else 'idle', walk=2 if t > 175.6 else 0, flip=t > 175.6)
        if 175.6 < t < 178.6:
            kx = lerp(1700, 2000, (t - 175.6) / 1.5); ky = 600 - 300 * math.sin(clamp((t - 175.6) / 1.5) * math.pi)
            put(c, R.emoji_im('🔑', 70).rotate(t * 400 % 360, expand=True), kx, ky)
    n = int(clamp((t - 172.5) / 12) * 34) + 1
    put(c, rich_img(f'КОМПАНИЯ МЕРТВА РОВНО {n} {"день" if n % 10 == 1 and n != 11 else ("дня" if n % 10 in (2, 3, 4) and n not in (12, 13, 14) else "дней")}', 74, (200, 230, 255), F_BLACK, 6), W / 2, 160)
    say(c, t, 182.5, 186.5, 'В апреле побухаем', 500, 600, 'Никита', 40)
    narr(c, t, 175.7, 181, 'Хозяин площадки закрыл калитку. Ключи — в сугроб.')
    narr(c, t, 186.3, 191, 'Молчание — золото. Или кляп.')

def s_spring(c, t):  # 191–207
    u = t - 191; c.alpha_composite(park(t, 0, False, 0, True, 'day'))
    d = ImageDraw.Draw(c)
    for i in range(30):
        x = (i * 173 + t * 30) % W; y = (i * 97 + t * 40) % 1080; d.ellipse([x, y, x + 10, y + 7], fill=(255, 200, 220))
    title(c, t, 191.3, 197, '24.04.2026', 150, 120, (255, 255, 255), (255, 220, 120), 1.6, sub='большой сбор · возвращение прайма', subsize=40)
    xs = [380, 560, 740, 960, 1180, 1360, 1540]
    for i, n in enumerate(NAMES):
        st = 191.6 + i * 0.6; side = -1 if i % 2 == 0 else 1
        x = lerp(W / 2 + side * 1200, xs[i], eo((t - st) / 2.2)) if t > st else -500
        if n == 'Юрий' and t > 205: pose = 'shrug'
        else: pose = 'hype' if t > 199.6 and int(t * 2 + i) % 2 else 'idle'
        P(c, n, x, 1000, t, 0.85, pose, walk=2.2 if st < t < st + 2.2 else 0, flip=side > 0, extra=furry if (n == 'Юрий' and t > 204.6) else None)
    if t > 199.6:
        title(c, t, 199.6, 207, 'МАЙ 2026 · ДнД', 150, 110, (110, 230, 110), (60, 50, 160), 1.6, sub='мастер игры — Фрол', subsize=38)
        a_ = (t - 199.6) * 300 if t < 201.5 else 0; dd = scaled(Image.open(os.devnull) if False else _d20(), 1.0)
        put(c, dd.rotate(a_, expand=True), 960, 620, 1.0)
    say(c, t, 201.6, 206, 'Кто последний тот фурри друид', 740, 600, 'Фрол', 36)
    if t > 204.6: stamp(c, t, 204.6, 207, 'ФУРРИ ДРУИД', (200, 120, 40), 1360, 560, 8, 60)
def _d20():
    def mk():
        im = Image.new('RGBA', (240, 240), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        pts = [(120 + 110 * math.cos(math.pi / 6 + i * math.pi / 3), 120 + 110 * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]
        d.polygon(pts, fill=(200, 40, 50), outline=BLACK); d.polygon([(120, 30), (205, 170), (35, 170)], outline=(255, 210, 210))
        fo = font(F_BLACK, 70); d.text((120 - fo.getlength('20') / 2, 90), '20', font=fo, fill=WHITE); return im
    return cached('d20', mk)

def s_lovecraft(c, t):  # 207–226
    u = t - 207; mood = clamp((t - 210) / 10)
    c.alpha_composite(park(t, mood, True, 0, True))
    tentacles(c, t, clamp((t - 213) / 4), 7)
    if t > 218: eye(c, t, 960, 230, 150, clamp((t - 218) / 1.5))
    P(c, 'Егор', 700, 1010, t, 1.05, 'drink', mouth='sad', extra=(lambda im: tears(im, t)) if t > 209 else None)
    title(c, t, 207.3, 213, 'ТРОПА · РЁВА', 380, 150, (110, 230, 160), (60, 120, 200), 1.6)
    narr(c, t, 208, 215.5, 'В Тропарёвском лесопарке есть тропа, специально предназначенная для рёва.')
    narr(c, t, 215.6, 220.5, 'Название — не случайность. Это предупреждение.')
    if t > 220.5:
        put(c, rich_img("Пх'нглуи мглв'нафх ТРОПАРЁВ Р'льех вгах'нагл фхтагн", 52, (150, 255, 170), F_SERI, 5), W / 2, 980, fade(t, 220.5, 226, 0.3, 0.3))
        put(c, rich_img('— почти Г. Ф. Лавкрафт', 30, (200, 220, 200), F_SERI, 3), W / 2 + 420, 1040, fade(t, 221, 226, 0.3, 0.3))

TVS = [('🧠 IQ 125–135', 'архитектор смысла (с) нейросеть'), ('GAZP 94.11 ₽', '29.07 купил 1 акцию'), ('ЭНЕРГИЧНЫЙ', 'дежурства за Энергичного'),
       ('где зп кст', 'я контентмейкер и сммщик'), ('ТОП 80 / 2600', 'попал. все топ 80'), ('ПРОСТЫНЯ', 'нейросетевой аргумент на 4 экрана')]
def tv_inner(i, t):
    def mk(j):
        im = Image.new('RGBA', (400, 260), [(40, 20, 80), (20, 60, 40), (90, 30, 30), (30, 40, 90), (80, 60, 10), (40, 40, 40)][j] + (255,))
        a, b = TVS[j]; put(im, rich_img(a, 52, WHITE, F_BLACK, 3, 380), 200, 100); put(im, rich_img(b, 24, (220, 220, 230), F_SB, 2, 380), 200, 190); return im
    return cached(('tvi', i), lambda: mk(i))
def s_genp(c, t):  # 226–256
    u = t - 226; c.alpha_composite(vgrad_im((10, 8, 18), (30, 24, 40)))
    k = kick(t)
    for i in range(6):
        x = 250 + (i % 3) * 480 + 140; y = 90 + (i // 3) * 340
        g = 0.8 if (k > 0.7 and (i + int(t * 2)) % 3 == 0) else 0
        put(c, tv(400, 260, tv_inner(i, t), t, g), x, y, 1.0, 'tl')
    P(c, 'Егор', 960, 1080, t, 1.0, 'hype' if 244 < t < 252 else 'point', talk=True)
    title(c, t, 226.4, 236, 'GENERATION П', 790, 120, (255, 220, 80), (255, 90, 60), 1.6, sub='П — переписка', subsize=44)
    narr(c, t, 236.5, 244, 'Поколение, назначившее нейросеть третейским судьёй.', y=1000)
    narr(c, t, 244.4, 251.4, 'Пространство чата контролируется не людьми, а простынями.', y=1000)
    put(c, rich_img('— почти В. О. Пелевин', 30, (210, 200, 180), F_SERI, 3), 1500, 1050, fade(t, 236.5, 256, 0.3, 0.3))
    narr(c, t, 251.6, 256, 'Когнитивный диссонанс: Никита купил ещё одну акцию Газпрома.', y=1000)

def s_prime(c, t):  # 256–275
    u = t - 256; c.alpha_composite(flat(t, 1.0))
    d = ImageDraw.Draw(c)
    table(c, 960, 860)
    put(c, R.emoji_im('🍕', 110), 820, 830); put(c, R.emoji_im('🍾', 110), 960, 820); put(c, R.emoji_im('🎂', 110), 1100, 830)
    xs = [260, 480, 700, 1220, 1440, 1660, 1860]
    for i, n in enumerate(NAMES):
        hy = int((t - OFF) / BEAT + i) % 2
        P(c, n, xs[i], 1000 + (i % 2) * 50, t, 0.85, 'hype' if hy else 'wave', talk=hy and i < 3)
    # guests silhouettes
    for i in range(4):
        x = 360 + i * 400; d.ellipse([x - 40, 380, x + 40, 460], fill=(30, 20, 40)); d.rounded_rectangle([x - 60, 450, x + 60, 640], 40, fill=(30, 20, 40))
    title(c, t, 256.3, 262, 'ПРАЙМ · АВГУСТ 2025', 140, 110, (255, 70, 160), GOLD, 1.6, 12, sub='прайм с 11 людьми · 1 886 сообщений за день', subsize=38)
    stamp(c, t, 262.6, 267, 'ДР ФРОЛА · 23.08', GOLD, 1100, 680, 8, 56)
    if t > 267.2:
        a = fade(t, 267.2, 275, 0.3, 0.3)
        mag = cached('mag', lambda: _forbes())
        put(c, scaled(mag, 0.9 + 0.1 * eo((t - 267.2) / 0.4)), 960, 520, a)
def _forbes():
    im = Image.new('RGBA', (560, 760), (245, 240, 230, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 559, 759], outline=BLACK, width=6)
    fo = font(F_SER, 120); d.text((280 - fo.getlength('Forbes') / 2, 10), 'Forbes', font=fo, fill=(20, 20, 20))
    put(im, puppet('Егор', 0.5, 'hype'), 280, 450)
    put(im, rich_img('ТРОПАРЁВО', 44, RED, F_BLACK, 0), 280, 640); put(im, rich_img('ТОП-1 чат юго-запада', 30, BLACK, F_BO, 0), 280, 700)
    return im

def s_cens(c, t):  # 275–309
    u = t - 275
    if t < 288:
        c.alpha_composite(vgrad_im((240, 236, 225), (210, 205, 190)))
        d = ImageDraw.Draw(c); d.rectangle([520, 80, 1400, 1000], fill=(255, 255, 250), outline=(60, 60, 60), width=6)
        put(c, rich_img('ПРАВИЛА ЧАТА', 64, BLACK, F_BLACK, 0), 960, 170); put(c, rich_img('с пятницы 18:00 до понедельника 9:00', 34, (60, 60, 60), F_SERI, 0), 960, 245)
        items = [(276.0, 'мемы'), (278.3, 'приколы'), (281.0, 'содержание вашей работы'), (283.6, 'в нейросетях'), (285.6, 'вообще всё')]
        for i, (ta, s_) in enumerate(items):
            if t >= ta:
                put(c, rich_img('— ' + s_, 50, (30, 30, 30), F_SB, 0), 700, 360 + i * 120, 1.0, 'tl')
                stamp(c, t, ta + 0.4, 288, 'НЕЛЬЗЯ', RED, 1220, 400 + i * 120, -8, 44)
        P(c, 'Егор', 300, 1060, t, 0.95, 'point', talk=True)
        put(c, rich_img('(с) Егор, 07.11.2026', 28, (90, 90, 90), F_MONO, 0), 960, 960)
    elif t < 303:
        c.alpha_composite(flat(t, 0)); c.alpha_composite(Image.new('RGBA', (W, H), (255, 160, 60, 30)))
        cal = cached('cal', lambda: _calendar()); put(c, cal, 1440, 380)
        if t > 291.7: stamp(c, t, 291.7, 303, 'ОТМЕНЕНО', RED, 1440, 400, 12, 60)
        P(c, 'Егор', 640, 1020, t, 1.1, 'drink', mouth='smile')
        rows = [(294.8, '0,4 виски'), (296.6, '0,3 водки'), (298.4, '1,5 л пива'), (300.2, 'коктейли — ещё полтора')]
        put(c, rich_img('ПРАЙМ-ФОРМА', 56, GOLD, F_BLACK, 5), 1100, 640, fade(t, 294.5, 303, 0.2, 0.2))
        for i, (ta, s_) in enumerate(rows):
            if t >= ta: pill(c, s_, 1100, 720 + i * 72, clamp((t - ta) / 0.2), (0, 0, 0, 190), WHITE, 34)
        narr(c, t, 288.2, 294.6, '01.11.2026: «ноябрь — месяц трезвости». Ноябрь продлился до 03.11.', y=1020)
    else:
        c.alpha_composite(vgrad_im((30, 26, 22), (14, 12, 10)))
        put(c, R.emoji_im('🪳', 220), 760, 560); put(c, R.emoji_im('🪳', 320), 1180, 520)
        put(c, rich_img('«Проснувшись однажды утром после беспокойного сна,\nЕгор обнаружил, что в его доме 59 года\nживут ровно два таракана»', 50, CREAM, F_SERI, 4, 1700), W / 2, 220, fade(t, 303.2, 309, 0.3, 0.3))
        put(c, rich_img('— почти Ф. Кафка', 32, (200, 190, 170), F_SERI, 3), W / 2 + 500, 920, fade(t, 304, 309, 0.3, 0.3))
        put(c, rich_img('один поменьше · другой побольше', 36, WHITE, F_SB, 3), W / 2, 820, fade(t, 305.5, 309, 0.3, 0.3))
def _calendar():
    im = Image.new('RGBA', (440, 420), (255, 255, 255, 255)); d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 439, 110], fill=(200, 30, 40)); fo = font(F_BLACK, 60); d.text((220 - fo.getlength('НОЯБРЬ') / 2, 20), 'НОЯБРЬ', font=fo, fill=WHITE)
    put(im, rich_img('месяц\nтрезвости', 54, BLACK, F_BLACK, 0), 220, 270); d.rectangle([0, 0, 439, 419], outline=BLACK, width=5); return im

def s_battle(c, t):  # 309–327
    u = t - 309; c.alpha_composite(vgrad_im((4, 14, 8), (10, 30, 16)))
    mx = cached(('mxl', int(t * 15)), lambda: None)
    d = ImageDraw.Draw(c)
    for i in range(48):
        x = i * 40; sp = 120 + (i * 53) % 240; y0 = (t * sp + i * 177) % 1300 - 200
        for j in range(8):
            ch = 'ЛАРП01ЛОР86'[(i + j + int(t * 6)) % 11]
            d.text((x, y0 - j * 34), ch, font=font(F_MONO, 30), fill=(60, 255, 120, max(0, 230 - j * 30)))
    c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 120)))
    put(c, rich_img('ЛАРП-БАТЛ · 26.10.2026', 70, NEON, F_BLACK, 6), W / 2, 110)
    rnd = 1 + int(clamp(u / 6) * 2.99)
    pill(c, f'РАУНД {rnd}', W / 2, 200, 1.0, (0, 0, 0, 200), GOLD, 40)
    P(c, 'Фрол', 520, 1020, t, 1.15, 'point' if rnd != 2 else 'idle', talk=rnd != 2)
    P(c, 'Никита', 1400, 1020, t, 1.15, 'point' if rnd == 2 else 'idle', talk=rnd == 2, flip=True)
    P(c, 'Егор', 960, 1080, t, 0.75, 'idle', mouth='flat')
    say(c, t, 309.6, 315, 'чел, ты же буквально программа из матрицы', 520, 560, 'Фрол', 34)
    say(c, t, 315.2, 321, 'я являюсь ограничителем реальности🤌', 1400, 560, 'Никита', 36)
    say(c, t, 321.2, 327, 'ты сейчас ларпишь предъяву по ларпу', 960, 680, 'Егор', 36)
    if t > 319.5: title(c, t, 319.5, 323, 'PRIME TIME', 380, 110, NEON, (200, 255, 200), 1.8, 10)
    stamp(c, t, 324.9, 327, 'ПОБЕДИЛ ЛОР', GOLD, 960, 420, -6, 70)

def s_dorian(c, t):  # 327–354
    u = t - 327; c.alpha_composite(vgrad_im((30, 22, 18), (12, 8, 6)))
    d = ImageDraw.Draw(c)
    d.polygon([(0, 0), (960, 0), (0, 500)], fill=(46, 34, 26)); d.polygon([(1920, 0), (960, 0), (1920, 500)], fill=(46, 34, 26))
    for x in range(-200, W + 200, 260): d.line([x, 0, x + 300, 500], fill=(60, 44, 32), width=14)
    # portrait
    age = clamp((t - 330) / 22)
    def port():
        im = Image.new('RGBA', (760, 520), (90, 70, 60, 255))
        for i, n in enumerate(NAMES): put(im, scaled(puppet(n, 0.4 + i, 'idle'), 0.62), 70 + i * 103, 440, 1.0, 'b')
        return im
    p = cached('port', port).copy()
    a = np.array(p).astype(np.float32)
    g = a[..., :3].mean(2, keepdims=True); a[..., :3] = g + (a[..., :3] - g) * (1 - 0.8 * age); a[..., :3] *= (1 - 0.35 * age); a[..., 0] += 25 * age; a[..., 1] += 12 * age
    p = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); pd = ImageDraw.Draw(p)
    rng = np.random.default_rng(9)
    for k in range(int(age * 30)):
        x0, y0 = rng.uniform(0, 760), rng.uniform(0, 520); pts = [(x0, y0)]
        for _ in range(4): x0 += rng.uniform(-40, 40); y0 += rng.uniform(-40, 40); pts.append((x0, y0))
        pd.line(pts, fill=(30, 20, 14), width=3)
    fr = Image.new('RGBA', (860, 620), (0, 0, 0, 0)); fd = ImageDraw.Draw(fr); fd.rectangle([0, 0, 859, 619], fill=(190, 150, 60), outline=(90, 60, 20), width=10)
    fd.rectangle([30, 30, 829, 589], fill=(130, 100, 40)); fr.alpha_composite(p, (50, 50))
    put(c, fr, 960, 380)
    yr = 2017 + int(age * 9); put(c, rich_img(f'{yr}', 40, GOLD, F_MONO, 3), 960, 720)
    for i, n in enumerate(NAMES): P(c, n, 330 + i * 210, 1070, t + i * 0.3, 0.62, 'wave' if 341.8 < t < 346 else 'idle')
    title(c, t, 327.3, 333, 'ПОРТРЕТ КОМПАНИИ', 860, 90, GOLD, (200, 140, 60), 1.4, sub='— почти О. Уайльд', subsize=30)
    narr(c, t, 333.5, 341.5, 'Мы не стареем. Стареет портрет на чердаке.', y=860)
    narr(c, t, 341.8, 349, 'Снаружи всё окей. Старые не помнят, новые не знают.', y=860)
    narr(c, t, 349.2, 354, 'Время отпустить. Но ёкает.', y=860)

def s_throne(c, t):  # 354–374
    u = t - 354; c.alpha_composite(vgrad_im((60, 10, 20), (20, 4, 10)))
    d = ImageDraw.Draw(c)
    d.rectangle([760, 300, 1160, 980], fill=(170, 130, 40), outline=(80, 50, 10), width=10); d.rectangle([800, 640, 1120, 980], fill=(140, 20, 40))
    baby = t > 360.4
    s = 0.45 if baby else 1.05
    P(c, 'Егор', 960, 900, t, s, 'hype' if not baby else 'sad', mouth='open' if baby else None, extra=crown)
    meds = ['ВШЭ', 'звание', 'топ 80 из 2600', 'учёная степень', 'зп']
    for i, m in enumerate(meds):
        if t > 354.5 + i * 0.8 and not baby: pill(c, '🏅 ' + m, 400 if i % 2 == 0 else 1520, 300 + i * 110, 1.0, (0, 0, 0, 180), GOLD, 34)
    title(c, t, 354.3, 360.3, 'ИМПЕРИЯ', 150, 130, GOLD, (255, 120, 40), 1.6, 10)
    if baby: title(c, t, 360.4, 363.5, 'НЕУВЕРЕННОСТЬ МЛАДЕНЦА', 150, 90, (255, 200, 220), (200, 160, 255), 1.6)
    if t > 363.6:
        pill(c, 'Егор Гусев вышел из беседы · 10.10.2026', W / 2, 140, 1.0, (0, 0, 0, 200), RED, 34)
        say(c, t, 364.6, 374, 'сказал вернется в компанию только в 2032 году', 420, 560, 'Никита', 34, 560)
        say(c, t, 367.7, 374, 'Ставь лайк если читаешь это до 2032ого года', 1500, 560, 'Фрол', 34, 560)
        if t > 369: pill(c, f'❤️ {min(7, int((t - 369) * 3) + 1)}', 1500, 620, 1.0, (0, 0, 0, 180), WHITE, 34)

def s_void(c, t):  # 374–396
    u = t - 374; c.alpha_composite(void(t))
    fl = 30 * math.sin(t * 0.9)
    P(c, 'Илья', 960, 760 + fl, t, 1.1, 'idle', rot=8 * math.sin(t * 0.5))
    for i, n in enumerate(['Егор', 'Никита', 'Фрол', 'Кирилл', 'Юрий', 'Коля']):
        a_ = t * 0.35 + i * math.pi / 3; x = 960 + 760 * math.cos(a_); y = 860 + 120 * math.sin(a_)
        P(c, n, x, y, t, 0.6, 'idle', walk=2, flip=math.sin(a_) > 0, a=0.9)
    title(c, t, 374.4, 381, 'ЧАПАЕВ И ПУСТОТА', 150, 110, (60, 60, 70), (140, 140, 160), 1.4, sub='— почти В. О. Пелевин', subsize=30)
    say(c, t, 381.5, 386, '— Где ты, Илья?', 600, 420, None, 36)
    say(c, t, 384, 389, '— В Пустоте.', 1300, 420, None, 36)
    say(c, t, 388.9, 395.5, '— А где Пустота? — Там, где о нём пишут чаще, чем пишет он.', 960, 300, None, 34, 760)
    narr(c, t, 391.9, 396, 'Отсутствующий центр. Четыре ухода. Каждый раз — возвращение.', y=1030, col=(40, 40, 50))

def s_board(c, t):  # 396–416
    u = t - 396; c.alpha_composite(cork()); d = ImageDraw.Draw(c)
    pos = [(300, 230), (300, 620), (700, 160), (1220, 160), (1620, 230), (1620, 620), (960, 800)]
    for i, n in enumerate(NAMES):
        if t > 396.3 + i * 0.6:
            x, y = pos[i]; p = polaroid(cached(('pp', n), lambda: puppet(n, 0.5, 'idle')), n.upper(), 230, [-5, 4, 3, -6, 5, -3, 2][i])
            put(c, p, x, y)
    for i in range(7):
        if t > 399 + i * 0.5:
            a = pos[i]; b = (960, 470)
            string(d, (a[0], a[1] - 120), b, clamp((t - 399 - i * 0.5) / 0.5), 30)
    for i in range(7):
        if t > 396.3 + i * 0.6: pin(d, pos[i][0], pos[i][1] - 125)
    # missing center piece
    gl = 0.5 + 0.5 * math.sin(t * 6) if t > 409.8 else 0.3
    d.rounded_rectangle([830, 360, 1090, 580], 20, outline=(255, 255, 255, int(255 * gl)), width=8)
    put(c, rich_img('?', 160, (255, 255, 255), F_BLACK, 6), 960, 470, gl)
    P(c, 'Кирилл', 1320 + 200 * math.sin(u * 0.9) if 412.5 < t < 414 else 1320, 1090, t, 0.9, 'point' if t < 412.5 else 'idle', look=-1, walk=2 if 412.5 < t < 414 else 0)
    if t > 414.3: put(c, R.emoji_im('💡', 120), 1320, 650, clamp((t - 414.3) / 0.2))
    narr(c, t, 407, 412.4, 'В пазле не хватает центральной части.', y=1030)
    narr(c, t, 412.5, 416, 'Хожу кругами. И тут я вспоминаю…', y=1030)

def s_book(c, t):  # 416–443
    u = t - 416; bw = 427.3 <= t < 437.8
    c.alpha_composite(park(t, 1.0, True, 0, True))
    tentacles(c, t, 1.0, 7)
    rise = eo((t - 418) / 6)
    def book():
        im = Image.new('RGBA', (520, 380), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 519, 379], 20, fill=(70, 30, 26), outline=(20, 8, 6), width=8)
        d.ellipse([170, 80, 350, 260], outline=(200, 170, 80), width=8); d.polygon([(260, 95), (335, 225), (185, 225)], outline=(200, 170, 80), width=6)
        put(im, rich_img('ChatExport_2026-11-08', 30, (220, 190, 110), F_MONO, 0), 260, 320); return im
    if not bw:
        put(c, cached('book', book), 960, lerp(900, 420, rise), clamp((t - 418) / 1))
    else:
        pg = Image.new('RGBA', (1300, 760), (240, 236, 220, 255)); pd = ImageDraw.Draw(pg); pd.line([650, 0, 650, 760], fill=(160, 150, 130), width=6)
        put(pg, rich_img('16 July 2025', 34, (40, 40, 40), F_SERI, 0), 325, 60)
        for j, (who, tx) in enumerate([('Егор', 'че'), ('Егор', 'и зачем папки'), ('Никита', 'А вот что это за говно нерусское'), ('Егор', 'я хуй знает')]):
            if t > 428.4 + j * 1.6: put(pg, bubble_im(tx, who, 32, 560), 325 + (0 if j % 2 == 0 else 0), 170 + j * 140)
        put(pg, rich_img('стр. 1 из 59 177', 30, (90, 90, 90), F_MONO, 0), 975, 680)
        put(pg, rich_img('НЕКРОНОМИКОН', 64, (110, 20, 20), F_BLACK, 0), 975, 300); put(pg, rich_img('написан кровью и капсом', 34, (60, 30, 30), F_SERI, 0), 975, 380)
        put(c, pg, 960, 520)
        a = np.array(c); g = a[..., :3].mean(2, keepdims=True).astype(np.uint8); a[..., :3] = np.repeat(g, 3, 2); c.paste(Image.fromarray(a))
    narr(c, t, 416.6, 423, 'Дрожащими пальцами — в переписку. То, что лежит на дне.', y=1030)
    if t > 437.9:
        for i, n in enumerate(NAMES): P(c, n, 330 + i * 210, 1080, t, 0.6, 'idle', look=0)
        narr(c, t, 437.9, 443, '2026. Хватит убегать от собственного лора.', y=1030)

def s_curtain(c, t):  # 443–466
    u = t - 443; c.alpha_composite(vgrad_im((50, 6, 14), (20, 2, 6)))
    d = ImageDraw.Draw(c)
    for x in range(0, W, 90): d.rectangle([x, 0, x + 70, 120], fill=(150, 16, 30)); d.rectangle([x + 70, 0, x + 90, 120], fill=(100, 8, 20))
    d.rectangle([0, 900, W, H], fill=(90, 56, 30))
    times = [443.2, 445.7, 448.7, 451.6, 453.5, 456.2, 459.2]
    cur = -1
    for i, ta in enumerate(times):
        if t >= ta: cur = i
    sp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); spd = ImageDraw.Draw(sp)
    for i, n in enumerate(NAMES):
        x = 300 + i * 220; front = (i == cur and t < 462.9)
        if front: spd.polygon([(x - 60, 0), (x + 60, 0), (x + 220, 960), (x - 220, 960)], fill=(255, 250, 220, 50))
    c.alpha_composite(sp)
    for i, n in enumerate(NAMES):
        x = 300 + i * 220; front = (i == cur and t < 462.9)
        bow = (t > 462.9) or front and (t - times[i]) > 1.2
        y = 960 + (30 if front else 0)
        P(c, n, x, y, t, 0.95 if front else 0.8, 'wave' if front and not bow else 'idle', rot=(-18 if bow else 0))
    if 0 <= cur and t < 462.9:
        n = NAMES[cur]
        put(c, grad(n.upper(), 110, COL[n], WHITE), W / 2, 230, 1.0); put(c, rich_img('в роли: ' + ROLE[n], 46, CREAM, F_SERI, 4), W / 2, 340)
    if t > 462.9:
        title(c, t, 462.9, 466.6, 'КАЖДЫЙ СВОЮ РОЛЬ ОТЫГРАЛ', 260, 90, GOLD, (255, 120, 60), 1.6)
        cl = eo((t - 465.2) / 1.2); d.rectangle([0, 0, W / 2 * cl, H], fill=(140, 14, 28)); d.rectangle([W - W / 2 * cl, 0, W, H], fill=(140, 14, 28))

def s_dawn(c, t):  # 466–490.7
    u = t - 466; c.alpha_composite(park(t, 0, False, 0, True, 'dawn'))
    d = ImageDraw.Draw(c); d.rounded_rectangle([660, 900, 1260, 940], 10, fill=(120, 80, 50), outline=BLACK, width=4)
    for x in (700, 1220): d.rectangle([x - 10, 940, x + 10, 1010], fill=(90, 60, 40))
    P(c, 'Егор', 960, 1000, t, 1.0, 'sad' if t < 476 else 'idle', mouth='sad' if t < 476 else 'smile')
    order = [('Кирилл', 1180, 469.8), ('Никита', 760, 472.6), ('Фрол', 1380, 474.9), ('Илья', 560, 477.5), ('Юрий', 1580, 480.3), ('Коля', 360, 482.9)]
    for n, x, ta in order:
        if t > ta:
            side = 1 if x > 960 else -1; xx = lerp(960 + side * 1200, x, eo((t - ta) / 2)); P(c, n, xx, 1000, t, 0.95, 'idle', walk=2 if t < ta + 2 else 0, flip=side > 0)
    say(c, t, 471.5, 476, 'Мы уже 10 лет друг друга ненавидим', 1180, 560, 'Кирилл', 34)
    say(c, t, 476.2, 480, 'Добро пожаловать в клуб', 1180, 560, 'Кирилл', 36)
    say(c, t, 478.4, 482.5, '11', 960, 560, 'Егор', 60)
    say(c, t, 482.9, 488.2, 'если тебя приглашают / значит тебя ждут / вопрос закрыт', 960, 560, 'Егор', 34, 600)
    narr(c, t, 488.3, 490.7, 'Главное — сегодня я прощаю себя. И долг за пиццу.', y=1040, size=38)

QS = [(490.76, 'Тропарёво, куда несёшься ты?', 'почти Н. В. Гоголь', 'Егор', 'wave'),
      (492.4, 'Кто виноват и что делать?', 'почти Герцен и Чернышевский', 'Фрол', 'shrug'),
      (494.48, 'Тварь ли я дрожащая — или в звании повыше?', 'почти Ф. М. Достоевский', 'Егор', 'point'),
      (497.38, 'Из чего сделаны наши мальчишки? Из пиццы, водки и голосовых', 'народное', 'Никита', 'idle'),
      (499.96, 'Почему все молчат после 18:00 пятницы?', 'регламент', 'Коля', 'shrug'),
      (503.86, 'За что Никита вычеркнул из списка?', 'почти капитан Кук', 'Никита', 'point'),
      (507.82, 'У вас продаётся славянский шкаф? — Только акции Газпрома', 'почти «17 мгновений весны»', 'Никита', 'idle'),
      (509.96, 'Кто мы и откуда? — Тропарево 8.6. Из 2014-го', 'вечный вопрос', 'Кирилл', 'idle'),
      (513.34, 'Кому нужен ломтик последней маленькой пиццы?', 'Фрол, 16.05.2026', 'Фрол', 'hype'),
      (515.52, 'Отчего люди не летают? Оттого что «в апреле побухаем»', 'почти А. Н. Островский', 'Никита', 'shrug'),
      (518.16, 'Где твои семнадцать лет? — На даче у Кирилла', 'почти В. С. Высоцкий', 'Кирилл', 'wave'),
      (521.02, 'Есть ли жизнь в чате после 18:00 пятницы?', 'почти Д. Боуи', 'Юрий', 'shrug'),
      (524.26, 'Что день грядущий мне готовит? — Компания мертва ровно 36 дней', 'почти А. С. Пушкин', 'Егор', 'sad'),
      (526.84, 'Сколько стоит твоя свобода? — 3000 ₽ за пиццу', 'долг не погашен', 'Егор', 'point'),
      (529.6, 'С чего начинается Родина? С тропы рёва', 'почти М. Матусовский', 'Егор', 'drink'),
      (532.4, 'Почём Газпром для народа? — 94.11 ₽', 'Никита, 29.07', 'Никита', 'hype'),
      (534.26, 'Есть кто живой? Стой, кто идёт?', 'прочитано: 7', 'Илья', 'idle'),
      (536.82, 'В чём сила, брат? — В голосовых', 'почти «Брат 2»', 'Кирилл', 'point'),
      (537.88, 'Сколько ты зарабатываешь? — Я выше в звании и учёной степени', 'Егор, 18.10.2026', 'Егор', 'hype'),
      (542.08, 'Что? Где? Когда? — Во сколько мы завтра встречаемся и где?', 'Коля, 29.05.2026', 'Коля', 'shrug'),
      (543.4, 'Кто хочет стать миллионером? — дэп, додэп, ластдэп', 'Никита', 'Никита', 'hype'),
      (544.64, 'Где лучшие тусовки? — Бирюлёвская хата, август 2025', 'прайм с 11 людьми', 'Егор', 'hype'),
      (547.66, 'Кому добавки? — 0,4 виски, 0,3 водки', 'прайм-форма', 'Егор', 'drink'),
      (550.36, 'Who let the furry druid out?', 'Фрол, 04.05.2026', 'Юрий', 'hype'),
      (552.98, 'Кого ты больше любишь: Егора или Никиту?', '53% / 27%', 'Никита', 'shrug'),
      (555.52, 'What is love? — «Добро пожаловать в клуб»', 'Кирилл', 'Кирилл', 'wave'),
      (557.9, 'Что в имени тебе моём? — ТРОПАРЕВО 8.6. Кто, если не мы?', 'почти А. С. Пушкин', 'Фрол', 'hype'),
      (560.54, 'Загнанные компании пристреливают, не так ли?', 'почти Х. Маккой', 'Кирилл', 'idle')]
QBG = [((40, 10, 30), (120, 20, 60)), ((10, 30, 50), (20, 90, 140)), ((30, 40, 10), (90, 120, 20)), ((50, 30, 10), (150, 90, 20)), ((20, 10, 50), (80, 40, 150)), ((10, 40, 40), (20, 120, 110))]
def s_questions(c, t):  # 490.76–563.5
    i = max(0, [k for k, q in enumerate(QS) if q[0] <= t][-1] if any(q[0] <= t for q in QS) else 0)
    ta, q, att, who, pose = QS[i]; tb = QS[i + 1][0] if i + 1 < len(QS) else 563.5
    c.alpha_composite(vgrad_im(*QBG[i % len(QBG)]))
    d = ImageDraw.Draw(c); k = kick(t)
    for r in range(6):
        rr = (t * 300 + r * 200) % 1400; d.ellipse([1400 - rr, 640 - rr, 1400 + rr, 640 + rr], outline=(255, 255, 255, int(40 * (1 - rr / 1400))), width=4)
    u = t - ta; e = easeback(clamp(u / 0.25))
    im = rich_img(q, 76 if len(q) < 40 else 62, WHITE, F_BLACK, 7, 1100, 'l')
    put(c, im, 80 - (1 - e) * 300, 300 - im.height / 2 + 60, clamp(u / 0.08), 'tl')
    put(c, rich_img('— ' + att, 34, (230, 220, 200), F_SERI, 3), 130 + 300, 300 + im.height / 2 + 120, clamp((u - 0.2) / 0.2))
    P(c, who, 1450, 1060, t, 1.25 + 0.03 * k, pose, talk=True, extra=furry if 'furry' in q else None)
    put(c, rich_img(f'{i + 1:02d}/{len(QS)}', 30, (255, 255, 255), F_MONO, 3), 1820, 60)

def s_final(c, t):  # 563.5–end
    u = t - 563.5; c.alpha_composite(vgrad_im((10, 4, 8), (40, 8, 16)))
    xs = [300, 520, 740, 960, 1180, 1400, 1620]
    for i, n in enumerate(NAMES):
        P(c, n, xs[i], 1050, t, 0.95, 'point', flip=(i % 2 == 1), look=(-1 if i % 2 else 1))
    title(c, t, 563.6, 566.5, 'НО ГЛАВНОЕ —', 200, 90, WHITE, (200, 200, 210), 1.4)
    title(c, t, 564.1, 566.5, 'КТО УБИЛ КОМПАНИЮ?', 380, 140, RED, GOLD, 2.0, 16)
    if t >= 566.0:
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - 566.0) / 0.3)))))
        put(c, rich_img('серия 2 — скоро', 50, WHITE, F_MONO, 0), W / 2, H / 2, clamp((t - 566.2) / 0.2))

SCENES = [(0, 30, s_cold), (30, 43, s_cinema), (43, 56, s_timeline), (56, 66, s_doors), (66, 84, s_hero), (84, 95, s_partner), (95, 112, s_duo),
          (112, 124, s_exits), (124, 143, s_storm), (143, 172, s_court), (172, 191, s_ice), (191, 207, s_spring), (207, 226, s_lovecraft),
          (226, 256, s_genp), (256, 275, s_prime), (275, 309, s_cens), (309, 327, s_battle), (327, 354, s_dorian), (354, 374, s_throne),
          (374, 396, s_void), (396, 416, s_board), (416, 443, s_book), (443, 466, s_curtain), (466, 490.76, s_dawn), (490.76, 563.5, s_questions), (563.5, 999, s_final)]
CUTS = [a for a, b, f in SCENES[1:]] + [q[0] for q in QS[1:]] + [288, 303]
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.25 - 0.55 * np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2), 0.55, 1)[..., None].astype(np.float32)
def render(fi):
    t = fi / FPS
    c = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for a, b, f in SCENES:
        if a <= t < b: f(c, t); break
    out = np.asarray(c.convert('RGB')).astype(np.float32)
    k = kick(t); z = 1 + 0.008 * k
    if z > 1.001: M_ = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); out = cv2.warpAffine(out, M_, (W, H), borderMode=cv2.BORDER_REFLECT)
    fl = 0
    for cu in CUTS:
        dt = t - cu
        if 0 <= dt < 0.14: fl = max(fl, 0.5 * (1 - dt / 0.14))
    out = out * VIG
    r = np.random.default_rng(fi); out += r.normal(0, 4, (H // 4, W // 4, 1)).astype(np.float32).repeat(4, 0).repeat(4, 1)
    if fl: out = out + 255 * fl
    return np.clip(out, 0, 255).astype(np.uint8)

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
                              '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '19', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, b): p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
