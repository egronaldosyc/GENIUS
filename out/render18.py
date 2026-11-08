# ТРОПАРЕВО · серия 2 «Прайм» (8.1 — прайм с девушками). 2D под FACE — «Лиза». 1920x1080.
import os, sys, math, json, subprocess, pickle, wave
import numpy as np, cv2
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(SP, 'v17'), SP, os.path.join(SP, 'v13')]
import render17 as A
from render17 import (put, scaled, rich_img, grad, P, say, narr, title, pill, stamp, clamp, eo, eio, lerp, fade, cached, vgrad_im, bubble_im,
                      F_SER, F_SERI, WHITE, BLACK, RED, GOLD, CREAM, COL)
from render13 import font, tokens, draw_rich, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO
import render13 as R
from scenes import park, flat, table, snow
from chars import puppet, CHAR

W, H, FPS, SR = 1920, 1080, 30, 44100
TRACK = os.path.join(HERE, 'track.mp3'); T_END = 198.06; N = int(T_END * FPS)
for n in CHAR: COL[n] = CHAR[n]['col']
BOYS = ['Егор', 'Никита', 'Фрол', 'Кирилл', 'Илья', 'Юрий', 'Коля']
GIRLS = ['Анфиса', 'Полина', 'Настя']
NOW = 'Раед'

# ---------------- kick ----------------
KP = os.path.join(HERE, 'kick.npy')
def build_kick():
    sr = 11025
    x = np.frombuffer(subprocess.run(['ffmpeg', '-v', 'error', '-i', TRACK, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout, np.float32)
    lo = np.convolve(x, np.ones(40) / 40, 'same'); hop = sr // FPS; n = len(lo) // hop
    e = np.sqrt(np.mean(lo[:n * hop].reshape(n, hop) ** 2, 1)); d = np.maximum(0, e - np.concatenate([[0], e[:-1]]))
    d = np.clip(d / (np.percentile(d, 99.5) + 1e-9), 0, 1); out = np.zeros_like(d); acc = 0
    for i in range(len(d)): acc = max(d[i], acc * 0.8); out[i] = acc
    np.save(KP, out.astype(np.float32))
KICK = np.load(KP) if os.path.exists(KP) else np.zeros(N + 10, np.float32)
def kick(t): i = int(t * FPS); return float(KICK[i]) if 0 <= i < len(KICK) else 0.0

# ---------------- voices (from pilot prep) ----------------
_V16 = pickle.load(open(os.path.join(SP, 'v16', 'vo.pkl'), 'rb'))
def vget(key):
    for v in _V16:
        if v['key'] == key and not v['mini']: return v
    raise KeyError(key)
VO = []
def vo(key, t, trim=None):
    v = dict(vget(key)); a = v['audio']
    if trim: a = a[:int(trim * SR)]; v['words'] = [w for w in v['words'] if w[0] < trim - 0.1]
    fi = int(0.02 * SR); a = a.copy(); a[-fi:] *= np.linspace(1, 0, fi)
    v.update(t=t, audio=a, d=len(a) / SR); VO.append(v)
vo('pol_vizitka', 119.7); vo('kolya_dengi', 127.9); vo('ilya_vodka', 130.4); vo('pol_8let', 141.4, trim=7.7)
def voice_card(c, t, v):
    u = t - v['t']
    if u < -0.1 or u > v['d'] + 0.4: return
    a = clamp(min((u + 0.1) / 0.3, (v['d'] + 0.4 - u) / 0.4)); col = COL.get(v['who'], (200, 200, 200))
    def base():
        im = Image.new('RGBA', (1000, 150), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, 999, 149], 40, fill=(18, 20, 28, 230), outline=col + (200,), width=4)
        d.ellipse([24, 25, 124, 125], fill=col); fo = font(F_BLACK, 54); d.text((74 - fo.getlength(v['who'][0]) / 2, 36), v['who'][0], font=fo, fill=(15, 15, 20))
        d.text((150, 20), v['who'], font=font(F_BO, 36), fill=col); d.text((150 + font(F_BO, 36).getlength(v['who']) + 18, 32), '· голосовое · ' + v['date'], font=font(F_MONO, 22), fill=(160, 160, 175))
        return im
    im = cached(('vc', v['who'], v['date']), base).copy(); d = ImageDraw.Draw(im)
    env = v['env']; nb = len(env); prog = clamp(u / v['d'])
    for i in range(nb):
        hh = 6 + 34 * env[i]; x = 150 + i * 17
        d.rounded_rectangle([x, 105 - hh / 2, x + 11, 105 + hh / 2], 3, fill=col if i / nb <= prog else (90, 92, 108))
    put(c, im, W / 2, 900, a)
    # subtitles: current ~9 words window
    ws = v['words']; cur = [w for w in ws if w[0] <= u]
    if not cur: return
    i = len(cur) - 1; s0 = (i // 9) * 9; win = ws[s0:s0 + 9]
    fo = font(F_BLACK, 48); line = Image.new('RGBA', (W, 80), (0, 0, 0, 0)); ld = ImageDraw.Draw(line)
    tw = sum(fo.getlength(w[2] + ' ') for w in win); x = (W - tw) / 2
    for w in win:
        f_ = col if w[0] <= u < w[1] else (WHITE if u >= w[1] else (255, 255, 255, 110))
        ld.text((x, 8), w[2], font=fo, fill=f_, stroke_width=5, stroke_fill=(0, 0, 0, 220)); x += fo.getlength(w[2] + ' ')
    put(c, line, W / 2, 770, a)

# ---------------- helpers ----------------
def tg(who, text, date=None, fs=32, maxw=760):
    def mk():
        fo = font(F_MED, fs); lines = R.layout(text, fo, maxw - 50); lh = int(fs * 1.3)
        wid = lambda l: sum(fo.getlength(v) if k == 't' else fs * 1.12 for k, v in tokens(l))
        nfo = font(F_BO, 26); dfo = font(F_MONO, 19); nw = nfo.getlength(who) + (dfo.getlength(date) + 30 if date else 0)
        bw = int(min(maxw, max(max(wid(l) for l in lines) + 50, nw + 50, 220))); h = 56 + lh * len(lines) + 16
        col = COL.get(who, (220, 220, 230))
        im = Image.new('RGBA', (bw + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([4, 6, bw + 3, h + 5], 26, fill=(0, 0, 0, 90))
        d.rounded_rectangle([0, 0, bw - 1, h - 1], 26, fill=(26, 28, 38, 240), outline=(255, 255, 255, 40), width=2)
        d.text((25, 14), who, font=nfo, fill=col)
        if date: d.text((bw - 25 - dfo.getlength(date), 19), date, font=dfo, fill=(140, 140, 155))
        for j, l in enumerate(lines): draw_rich(im, (25, 52 + lh * j), l, fo, WHITE)
        return im
    return cached(('tg', who, text, date, fs, maxw), mk)
def stack(c, t, items, x, bottom, top, align='l'):
    y = float(bottom)
    for it in reversed([i for i in items if i[0] <= t]):
        ta, who, text, date = it[:4]; im = tg(who, text, date); u = t - ta; e = easeback(clamp(u / 0.35))
        yy = y - im.height; a = min(1, e * 1.5) * clamp((yy + im.height - top) / 120)
        if a <= 0: break
        xx = x if align == 'l' else x - im.width
        put(c, im, xx, yy + (1 - e) * 60, a, 'tl'); y -= (im.height + 16) * e
def svc(c, text, x, y, a=1.0, col=WHITE): pill(c, text, x, y, a, (0, 0, 0, 180), col, 30)
def chip(c, t, t0, t1, text, y=70, col=CREAM):
    a = fade(t, t0, t1, 0.4, 0.4)
    if a > 0: pill(c, text, W / 2, y, a, (0, 0, 0, 170), col, 32)
def glow_dot(c, x, y, r, col, a):
    def mk():
        g = np.zeros((2 * r, 2 * r, 4), np.uint8); yy, xx = np.mgrid[0:2 * r, 0:2 * r]; dd = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
        g[..., :3] = col; g[..., 3] = (np.clip(1 - dd, 0, 1) ** 2 * 255).astype(np.uint8); return Image.fromarray(g)
    put(c, cached(('gd', r, col), mk), x, y, a)
def bench(c, x, y, w=900):
    d = ImageDraw.Draw(c); d.rounded_rectangle([x - w / 2, y, x + w / 2, y + 34], 10, fill=(110, 74, 46), outline=BLACK, width=4)
    d.rounded_rectangle([x - w / 2, y - 90, x + w / 2, y - 60], 10, fill=(110, 74, 46), outline=BLACK, width=4)
    for xx in (x - w / 2 + 40, x + w / 2 - 40): d.rectangle([xx - 10, y + 34, xx + 10, y + 110], fill=(70, 46, 30))
def garland(c, t, on=1.0, n=14):
    d = ImageDraw.Draw(c); pts = [(i * W / (n - 1), 90 + 50 * math.sin(i / (n - 1) * math.pi)) for i in range(n)]
    d.line(pts, fill=(40, 30, 30), width=4)
    cols = [(255, 200, 90), (255, 120, 160), (120, 200, 255), (160, 255, 160)]
    for i, (x, y) in enumerate(pts):
        lit = on > (i + 0.5) / n
        glow_dot(c, x, y + 14, 40, cols[i % 4], (0.5 + 0.3 * math.sin(t * 3 + i)) if lit else 0.0)
        d.ellipse([x - 9, y + 5, x + 9, y + 23], fill=cols[i % 4] if lit else (60, 60, 60))
def polaroid_of(img, w=640, cap=''):
    fr = Image.new('RGBA', (w + 40, int(w * 0.62) + 130), (245, 242, 232, 255)); ph = img.resize((w, int(w * 0.5625)))
    fr.paste(ph, (20, 20)); put(fr, rich_img(cap, 34, (40, 40, 40), F_SERI, 0), fr.width / 2, fr.height - 52); return fr

# ---------------- scenes ----------------
def s_quiet(c, t):  # 0–25.2
    c.alpha_composite(flat(t, 0)); c.alpha_composite(Image.new('RGBA', (W, H), (20, 30, 60, 90)))
    d = ImageDraw.Draw(c)
    rng = np.random.default_rng(1)
    for i in range(60):  # rain on window
        x = 1400 + (i * 37) % 300; y = (i * 91 + t * 400) % 320 + 120; d.line([x, y, x - 4, y + 18], fill=(150, 170, 220, 160), width=2)
    xs = [260, 470, 690, 900, 1110, 1320, 1700]
    for i, n in enumerate(BOYS):
        P(c, n, xs[i], 1010, t * 0.6 + i, 0.8, 'idle', mouth='flat', look=(-1 if i % 2 else 1) * 0.5)
    chip(c, t, 1.0, 25, 'ВЕРСИЯ 8.1 · АВГУСТ 2025', 70, GOLD)
    days = [(1, 93), (2, 20), (3, 10), (4, 143), (5, 111), (6, 77), (7, 35), (8, 155), (9, 6), (10, 8)]
    a = fade(t, 2, 17, 0.5, 0.5)
    if a > 0:
        for i, (dd, v) in enumerate(days):
            if t > 2.5 + i * 0.6:
                hgt = v * 0.9; x = 140 + i * 50
                d.rectangle([x, 560 - hgt, x + 34, 560], fill=(120, 160, 220, int(220 * a)))
                put(c, rich_img(f'{dd:02d}', 18, (200, 200, 210), F_MONO, 2), x + 17, 580, a)
        put(c, rich_img('сообщений в день', 24, (200, 200, 210), F_SB, 2), 380, 620, a)
    narr(c, t, 3, 10.5, 'Август 2025. В чате — семь парней и тишина.')
    narr(c, t, 11, 17, 'Чат называется «Божьи твари Тропарево». Твари скучают.')
    if t > 17.5:
        a = fade(t, 17.5, 25, 0.8, 0.6)
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(150 * a))))
        put(c, rich_img('ТРОПАРЕВО', 110, CREAM, F_SER, 6), W / 2, 420, a)
        put(c, rich_img('серия 2 · «Прайм»', 54, (230, 210, 190), F_SERI, 4), W / 2, 540, a)
    if t < 1.2: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - t / 1.2)))))

def s_join(c, t):  # 25.2–33.2
    u = t - 25.2; c.alpha_composite(flat(t, 0)); c.alpha_composite(Image.new('RGBA', (W, H), (20, 30, 60, int(90 * (1 - eo(u / 8))))))
    d = ImageDraw.Draw(c)
    d.rectangle([80, 220, 380, 900], fill=(255, 230, 170), outline=(40, 28, 20), width=10)  # open door with light
    beam = Image.new('RGBA', (W, H), (0, 0, 0, 0)); bd = ImageDraw.Draw(beam); bd.polygon([(380, 220), (380, 900), (1300, 1080), (900, 600)], fill=(255, 220, 150, 50)); c.alpha_composite(beam)
    xs = [700, 880, 1060, 1240, 1420, 1600, 1780]
    for i, n in enumerate(BOYS): P(c, n, xs[i], 1010, t + i, 0.8, 'idle', look=-1, mouth='open' if u > 3 else None)
    chip(c, t, 25.3, 33.2, '15.08.2025', 70, GOLD)
    for i, (ta, s_) in enumerate([(25.6, 'хто я🚬🗿 joined group by link'), (27.4, 'анфиса joined group by link'), (29.2, 'Никита Куприяшин invited PG (Pigeon)')]):
        if t >= ta: svc(c, s_, W / 2, 200 + i * 80, clamp((t - ta) / 0.2), (255, 220, 160))

def s_arrive(c, t):  # 33.2–52.6
    u = t - 33.2; c.alpha_composite(flat(t, 0.15 * clamp(u / 10)))
    c.alpha_composite(Image.new('RGBA', (W, H), (255, 170, 90, int(30 * clamp(u / 8)))))
    xs = [700, 880, 1060, 1240, 1420, 1600, 1780]
    for i, n in enumerate(BOYS): P(c, n, xs[i], 1010, t + i, 0.8, 'wave' if 1 < u < 4 and i < 3 else 'idle', look=-1)
    for j, n in enumerate(GIRLS):
        st = 33.4 + j * 1.2; x = lerp(230, 220 + j * 150, eo((t - st) / 2.2)) if t > st else -400
        P(c, n, x, 1030, t + j, 0.85, 'wave' if t > st + 2.4 and j == 1 else 'idle', walk=2.2 if st < t < st + 2.2 else 0)
    say(c, t, 34.6, 39.6, 'Где в этом чате кнопка «налить всем пива»?', 370, 600, 'Полина', 34, 560)
    say(c, t, 39.8, 43, 'Окак', 520, 600, 'Настя', 44)
    say(c, t, 41.0, 47.4, 'Я 7 лет хотела вступить в эту беседу', 370, 560, 'Полина', 36, 560)
    say(c, t, 47.6, 52.4, 'Я больше не пью', 520, 600, 'Настя', 40)
    chip(c, t, 33.4, 52.6, '15—18.08.2025', 70, GOLD)

def s_bench(c, t):  # 52.6–68.7
    u = t - 52.6; c.alpha_composite(park(t, 0, True, 0, True))
    for i in range(26):
        x = (i * 151 + 60 * math.sin(t * 0.7 + i)) % W; y = 520 + (i * 73) % 380 + 20 * math.sin(t * 1.3 + i * 2)
        glow_dot(c, x, y, 26, (255, 230, 120), 0.4 + 0.4 * math.sin(t * 3 + i))
    bench(c, 960, 930, 1100)
    order = ['Настя', 'Никита', 'Егор', 'Анфиса', 'Фрол', 'Полина', 'Илья', 'Кирилл', 'Юрий', 'Коля']
    for i, n in enumerate(order):
        x = 290 + i * 150; P(c, n, x, 1010 + (i % 2) * 20, t * 0.8 + i, 0.72, 'idle', look=math.sin(t * 0.4 + i) * 0.6)
    days = [('11', 174), ('12', 423), ('13', 364), ('14', 593), ('15', 251), ('16', 238), ('17', 97), ('18', 155), ('19', 1886)]
    d = ImageDraw.Draw(c); a = fade(t, 53, 68.7, 0.5, 0.5)
    for i, (dd, v) in enumerate(days):
        ta = 53.2 + i * 0.75
        if t > ta:
            hgt = v * 0.2 * eo((t - ta) / 0.5); x = 120 + i * 64
            d.rectangle([x, 470 - hgt, x + 46, 470], fill=(255, 140, 180, int(230 * a)) if dd == '19' else (255, 210, 150, int(200 * a)))
            put(c, rich_img(dd + '.08', 20, (230, 230, 240), F_MONO, 2), x + 23, 492, a)
    if t > 59.9:
        put(c, rich_img('19.08.2025', 70, (255, 160, 200), F_BLACK, 5), 1360, 180, fade(t, 59.9, 68.7, 0.3, 0.4))
        put(c, rich_img('1 886 сообщений за один день', 44, WHITE, F_BO, 4), 1360, 260, fade(t, 60.4, 68.7, 0.3, 0.4))
        put(c, rich_img('прайм с 11 людьми', 36, CREAM, F_SERI, 3), 1360, 320, fade(t, 61.4, 68.7, 0.3, 0.4))

CHAT1 = [(68.9, 'Анфиса', 'чисто предупреждение, вдруг кто не понял, егора я попускаю жоска только здесь, чтобы не расслаблялся', '19.08 12:30'),
         (72.4, 'Настя', 'Тиха не пали контору', '12:30'), (74.0, 'Анфиса', 'отпустил чечню. твёрдо и чётко.', '12:23'),
         (76.3, 'Настя', 'Ну милая ну давай не при всех', '12:33'), (78.4, 'Полина', 'Мне нравится 👍', '12:53'),
         (80.0, 'Полина', 'А по какому адресу торжество? Фрол, мы у тебя собираемся?', '17.08'),
         (82.8, 'Полина', 'А какого тогда мы будем поздравлять Фрола? Если хата Егора, а алкашка с нас?', '17.08'),
         (85.6, 'Анфиса', 'короче вот ещё один пункт в программу на др фрола', '19.08'),
         (88.6, 'Егор', 'хоть бы спс кто сказал...', '19.08'), (90.6, 'Полина', 'Не благодарите 🙂', '19.08')]
def s_chat(c, t):  # 68.7–93.1
    u = t - 68.7; c.alpha_composite(vgrad_im((40, 26, 40), (80, 46, 60)))
    d = ImageDraw.Draw(c); d.rounded_rectangle([80, 60, 940, 1040], 40, fill=(14, 16, 22), outline=(70, 70, 90), width=6)
    d.rounded_rectangle([80, 60, 940, 160], 40, fill=(30, 34, 48)); put(c, rich_img('Божьи твари Тропарево', 34, WHITE, F_BO, 0), 510, 98)
    put(c, rich_img('11 участников · печатает…', 22, (150, 160, 190), F_SB, 0), 510, 136)
    stack(c, t, CHAT1, 110, 1010, 180)
    last = [x for x in CHAT1 if x[0] <= t]
    who = last[-1][1] if last else 'Анфиса'
    ppl = ['Анфиса', 'Полина', 'Настя', 'Егор', 'Фрол']
    for i, n in enumerate(ppl):
        x = 1130 + (i % 3) * 300 + (150 if i >= 3 else 0); y = 640 if i < 3 else 1060
        P(c, n, x, y, t + i, 0.8 if i < 3 else 0.85, 'point' if n == who else 'idle', talk=(n == who and (t - last[-1][0]) < 2.2) if last else False)
    chip(c, t, 78.3, 93.1, 'план на 23.08: ДР Фрола', 40, GOLD) if t > 79.5 else None

def s_party(c, t):  # 93.1–119.3
    u = t - 93.1; frozen = t >= 109.8
    tt = min(t, 109.8)
    c.alpha_composite(flat(tt, 0.6)); garland(c, tt)
    c.alpha_composite(Image.new('RGBA', (W, H), (255, 150, 80, 34)))
    table(c, 960, 860); put(c, R.emoji_im('🎂', 130), 960, 810)
    for k in range(3): A.glow_dot if False else glow_dot(c, 930 + k * 30, 735, 22, (255, 200, 100), 0.7 + 0.3 * math.sin(tt * 9 + k))
    ppl = ['Коля', 'Юрий', 'Настя', 'Никита', 'Егор', 'Фрол', 'Анфиса', 'Полина', 'Кирилл', 'Илья', 'Раед']
    xs = [170, 330, 490, 650, 800, 960, 1120, 1270, 1430, 1590, 1750]
    for i, n in enumerate(ppl):
        sway = 'wave' if (n == 'Фрол' and 100.8 < tt < 107) else ('hype' if 96.4 < tt < 100.5 and i % 3 == 0 else 'idle')
        P(c, n, xs[i], 1040 + (0 if n == 'Фрол' else 10 * (i % 2)), tt + i * 0.4, 0.8 if n != 'Фрол' else 0.95, sway, look=(1 if xs[i] < 960 else -1) * 0.7)
    if not frozen:
        a = fade(t, 96.4, 109.6, 0.8, 0.5)
        if a > 0:
            put(c, rich_img('23.08.2025', 80, CREAM, F_SER, 5), W / 2, 230, a)
            put(c, rich_img('день рождения Фрола · хата Егора', 46, (255, 220, 200), F_SERI, 4), W / 2, 320, a)
    else:
        # camera flash and polaroid
        fl = clamp(1 - (t - 109.8) / 0.4)
        if fl > 0: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * fl))))
        if t > 110.2:
            snap = cached('snap', lambda: c.copy().convert('RGB'))
            dark = Image.new('RGBA', (W, H), (10, 8, 12, 255)); c.paste(dark)
            p = cached('pol', lambda: polaroid_of(snap, 1100, '23.08.2025 · последний общий сбор'))
            rr = lerp(-14, -4, eo((t - 110.2) / 1.5)); s = lerp(1.15, 0.92, eo((t - 110.2) / 1.5))
            put(c, scaled(p.rotate(rr, expand=True, resample=Image.BICUBIC), s), W / 2, 520)
    if t < 109.8: narr(c, t, 100.9, 108.5, 'Хата Егора. Алкашка — с гостей. «Хоть бы спс кто сказал».', y=1000)

def s_voices(c, t):  # 119.3–149.5
    u = t - 119.3; c.alpha_composite(flat(t, 0.3)); garland(c, t)
    c.alpha_composite(Image.new('RGBA', (W, H), (20, 10, 30, 150)))
    cur = None
    for v in VO:
        if v['t'] - 0.2 <= t < v['t'] + v['d'] + 0.4: cur = v
    chip(c, t, 119.4, 149.5, '19.08.2025 · ночь голосовых · 47 голосовых за сутки', 70, (255, 200, 220))
    ppl = ['Полина', 'Коля', 'Илья', 'Никита', 'Фрол', 'Егор']
    for i, n in enumerate(ppl):
        x = 260 + i * 280; speaking = cur is not None and cur['who'] == n and 0 < t - cur['t'] < cur['d']
        P(c, n, x, 640 if not speaking else 620, t + i, 0.95 if speaking else 0.7, 'point' if speaking else 'idle', talk=speaking, a=1.0 if speaking else 0.55)
    for v in VO: voice_card(c, t, v)
    if t > 148.6: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * clamp((t - 148.6) / 0.9)))))

def s_leave(c, t):  # 149.5–179.2
    u = t - 149.5
    c.alpha_composite(park(t, 0, False, 0, True, 'dawn'))
    c.alpha_composite(Image.new('RGBA', (W, H), (40, 30, 50, int(80 + 60 * clamp(u / 30)))))
    d = ImageDraw.Draw(c)
    for i in range(30):  # falling leaves
        x = (i * 157 + 60 * math.sin(t + i)) % W; y = (i * 83 + t * 90) % H
        d.ellipse([x, y, x + 18, y + 10], fill=[(220, 120, 40), (200, 80, 30), (230, 170, 60)][i % 3])
    bench(c, 960, 930, 1100)
    gone = {'Кирилл': 161.0, 'Раед': 171.4, 'Полина': 175.8}
    seat = ['Настя', 'Никита', 'Егор', 'Анфиса', 'Фрол', 'Полина', 'Илья', 'Кирилл', 'Юрий', 'Раед', 'Коля']
    for i, n in enumerate(seat):
        x = 220 + i * 148; a = 1.0
        if n in gone and t > gone[n] - 1.6: a = clamp((gone[n] - t) / 1.6)
        if n == 'Кирилл' and 156 < t: x += (t - 156) * 60
        if t > 176.4: a *= clamp((179.2 - t) / 2.8) if i % 2 else 1.0
        P(c, n, x, 1010, t * 0.7 + i, 0.7, 'sad' if t > 168 else 'idle', mouth='flat', a=a, walk=1.5 if (n == 'Кирилл' and 156 < t < 161) else 0)
    if 156 < t < 161: put(c, rich_img('→ Панама', 30, GOLD, F_BO, 3), 220 + 7 * 148 + (t - 156) * 60, 620, fade(t, 156, 161, 0.3, 0.5))
    chip(c, t, 149.6, 155.3, '24.08.2025', 70, GOLD); chip(c, t, 155.5, 171.3, '30.08.2025', 70, GOLD); chip(c, t, 171.5, 179.2, '03.09.2025', 70, GOLD)
    say(c, t, 150.0, 155.3, 'за пиццу и водку кстати с тебя 3000', 220 + 2 * 148, 640, 'Егор', 34)
    say(c, t, 155.6, 161.6, 'Кирюша, ты не скучай по родине, мы здесь все в полном порядке. Ждём тебя, верим в тебя, любим, но не по-гейски, а по-дружески.', 220 + 5 * 148, 600, 'Полина', 30, 760)
    say(c, t, 162.0, 164.8, 'А где сбор?', 220 + 5 * 148, 640, 'Полина', 38)
    say(c, t, 164.9, 167.4, 'Я тут, никого нет :(', 220 + 5 * 148, 640, 'Полина', 38)
    say(c, t, 167.5, 171.8, 'к сожалению, я уже не обладаю прежним скилом убеждать людей и более не являюсь мотиватором для сборов, поэтому покидаю эту прекрасную беседу 🥹🫂', 220 + 9 * 148, 600, 'Раед', 30, 760)
    if t > 171.4: svc(c, 'Раед покинул группу', W / 2, 170, fade(t, 171.4, 179.2, 0.2, 0.5), (255, 140, 140))
    say(c, t, 172.0, 175.8, 'Так, у меня много работы, я вас всех ненавижу. Прощайте.', 220 + 5 * 148, 640, 'Полина', 34, 640)
    if t > 175.8: svc(c, 'PG (Pigeon) покинула группу', W / 2, 250, fade(t, 175.8, 179.2, 0.2, 0.5), (255, 140, 140))
    narr(c, t, 176.5, 179.2, 'Сидим. И встаём.', y=1040)

def s_end(c, t):  # 179.2–end
    u = t - 179.2; c.alpha_composite(flat(t, 0))
    c.alpha_composite(Image.new('RGBA', (W, H), (20, 26, 40, 120)))
    garland(c, t, 1 - clamp(u / 8))
    g = np.array(c).astype(np.float32); m = g[..., :3].mean(2, keepdims=True); g[..., :3] = m + (g[..., :3] - m) * 0.35; c.paste(Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)))
    P(c, 'Никита', 1300, 1010, t, 0.85, 'idle', mouth='flat'); P(c, 'Егор', 700, 1010, t, 0.85, 'sad', mouth='flat')
    evs = [(179.6, '14.10.2025 · анфиса покинула группу'), (181.4, '19.10.2025 · Никита Куприяшин удалил хто я🚬🗿')]
    for i, (ta, s_) in enumerate(evs):
        if t > ta: svc(c, s_, W / 2, 140 + i * 80, fade(t, ta, 192, 0.2, 0.6), (255, 160, 160))
    say(c, t, 183.0, 187.4, 'ну че, теперь ждем новую партию людей', 1300, 600, 'Никита', 36)
    narr(c, t, 186.6, 192.0, 'После 23.08 — ни одного сбора.', y=1000)
    if t > 191.5:
        a = clamp((t - 191.5) / 0.8)
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(230 * a))))
        put(c, rich_img('ТРОПАРЕВО · серия 2 · «Прайм»', 64, CREAM, F_SER, 4), W / 2, 470, a * clamp((T_END - 0.4 - t) / 1.2))
        put(c, rich_img('далее: серия 3 — «Отсев»', 40, (200, 190, 180), F_SERI, 3), W / 2, 560, clamp((t - 192.6) / 0.6) * clamp((T_END - 0.4 - t) / 1.2))

SCENES = [(0, 25.2, s_quiet), (25.2, 33.2, s_join), (33.2, 52.6, s_arrive), (52.6, 68.7, s_bench), (68.7, 93.1, s_chat), (93.1, 119.3, s_party),
          (119.3, 149.5, s_voices), (149.5, 179.2, s_leave), (179.2, 999, s_end)]
CUTS = [a for a, b, f in SCENES[1:]]
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.3 - 0.65 * np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2), 0.45, 1)[..., None].astype(np.float32)
def warmth(t):  # film warmth: rises through prime, fades after
    if t < 33: return 0.0
    if t < 120: return clamp((t - 33) / 20)
    return clamp(1 - (t - 149) / 30)
def render(fi):
    t = fi / FPS
    c = Image.new('RGBA', (W, H), (0, 0, 0, 255))
    for a, b, f in SCENES:
        if a <= t < b: f(c, t); break
    out = np.asarray(c.convert('RGB')).astype(np.float32)
    w = warmth(t); out = out + np.array([18, 6, -14], np.float32) * w
    # light leak
    if w > 0:
        lx = W * (0.5 + 0.45 * math.sin(t * 0.21)); ly = H * (0.3 + 0.2 * math.cos(t * 0.17))
        leak = np.exp(-(((_X - lx) / 700) ** 2 + ((_Y - ly) / 500) ** 2))[..., None] * np.array([60, 30, 10], np.float32) * w
        out = out + leak
    if t > 149.5:
        s = clamp(1 - (t - 149.5) / 40) * 0.6 + 0.4; m = out.mean(2, keepdims=True); out = m + (out - m) * s
    z = 1 + 0.004 * kick(t)
    if z > 1.001: M_ = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); out = cv2.warpAffine(out, M_, (W, H), borderMode=cv2.BORDER_REFLECT)
    out = out * VIG
    r = np.random.default_rng(fi); out += r.normal(0, 6, (H // 3, W // 3, 1)).astype(np.float32).repeat(3, 0).repeat(3, 1)
    for cu in CUTS:
        dt = t - cu
        if 0 <= dt < 0.5: out = out * (0.55 + 0.45 * dt / 0.5)  # soft dip
    return np.clip(out, 0, 255).astype(np.uint8)

def build_audio(outp):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', TRACK, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    tr = np.frombuffer(raw, np.float32).reshape(-1, 2).copy(); n = len(tr)
    vox = np.zeros(n, np.float32); act = np.zeros(n, np.float32)
    for v in VO:
        i = int(v['t'] * SR); x = v['audio'] * 1.15; j = min(n, i + len(x)); vox[i:j] += x[:j - i]; act[i:j] = 1
    hop = 441; m = n // hop; a_ = act[:m * hop].reshape(m, hop).max(1); env = np.zeros(m, np.float32); e = 0
    for q in range(m): tg_ = a_[q]; e = e + (tg_ - e) * (0.2 if tg_ > e else 0.02); env[q] = e
    env = np.concatenate([np.repeat(env, hop), np.zeros(n - m * hop, np.float32)])
    mix = tr * (1 - 0.6 * env)[:, None] + vox[:, None]
    mix = np.tanh(mix * 1.0) * 0.97
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix * 32767).astype(np.int16).tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--kick': build_kick(); sys.exit()
    if sys.argv[1] == '--audio': build_audio(sys.argv[2]); sys.exit()
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
