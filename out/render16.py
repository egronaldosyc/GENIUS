# ТРОПАРЕВО 8.6 — пилот. Хук (IMG_2036, 18.48 c) + Justice «Pusher» (7:01). Патч-ноут чата друзей.
import os, sys, math, json, subprocess, wave, re, pickle
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path[:0] = [SP, os.path.join(SP, 'v13'), os.path.join(SP, 'v14')]
import render13 as R
import render14 as R14
from render import text_img
from render13 import font, tokens, draw_rich, grad_text, fitw, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO, shot_img, FOCUS
from render14 import fade, alpha_im, F_SER, F_SERI, CREAM
def put(c, im, x, y, a=1.0, anchor='c'):
    if a <= 0.003: return
    im = alpha_im(im, a)
    if anchor == 'c': x -= im.width / 2; y -= im.height / 2
    x, y = int(x), int(y); sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height or x >= c.width or y >= c.height: return
    if sx or sy: im = im.crop((sx, sy, im.width, im.height))
    c.alpha_composite(im, (x + sx, y + sy))

W, H, FPS, SR = 720, 1280, 30, 44100
TI = 18.48; TP = 421.2244; T_END = TI + TP; N = int(round(T_END * FPS))
BAR = 4 * 60 / 113.35; OFF = 0.10
def B(x): return OFF + BAR * x
def G(x): return TI + B(x)
WHITE = (255, 255, 255); BLACK = (0, 0, 0); GREY = (150, 150, 162); NEON = (120, 255, 150); RED = (255, 60, 70); GOLD = (255, 205, 90)
COL = {'Егор': (255, 70, 160), 'Никита': (70, 150, 255), 'Фрол': (110, 230, 110), 'Кирилл': (255, 205, 90), 'Илья': (170, 110, 255),
       'Юрий': (255, 150, 60), 'Коля': (60, 210, 200), 'Полина': (255, 130, 200), 'Анфиса': (255, 160, 120), 'Настя': (200, 160, 255), 'Раед': (200, 200, 210)}
def short(w):
    for k, v in [('Егор', 'Егор'), ('Никита', 'Никита'), ('Фрол', 'Фрол'), ('Kirill', 'Кирилл'), ('Кирилл', 'Кирилл'), ('Илья', 'Илья'), ('Юр', 'Юрий'),
                 ('PG', 'Полина'), ('Никола', 'Коля'), ('анфиса', 'Анфиса'), ('хто', 'Настя')]:
        if w.startswith(k): return v
    return w
def lerp(a, b, u): return a + (b - a) * u
def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def eo(u): u = clamp(u); return 1 - (1 - u) ** 3

# ---------------- messages (real chat text, verified on load) ----------------
MSGS = json.load(open(os.path.join(HERE, 't.json')))
def M(sub, who=None, date=None, text=None):
    for m in MSGS:
        tx = m.get('text') or ''
        if sub.lower() in tx.lower() and (who is None or short(m.get('from') or '') == who) and (date is None or m['date'].startswith(date)):
            return dict(who=short(m.get('from') or ''), date=m['date'][:10], text=text or tx)
    raise KeyError(sub)

# ---------------- sections (pusher bars) ----------------
SECB = [('install', 0), ('title', 21), ('people', 23), ('break', 36), ('prime', 43), ('otsev', 65), ('tropa', 71), ('heart', 85),
        ('zapoy', 100), ('exits', 119), ('larp', 127), ('storm', 137), ('credits', 169), ('final', 186), ('end', 999)]
def sec_at(t):
    if t < TI: return 'hook', 0, TI
    for (k, a), (_, b) in zip(SECB, SECB[1:]):
        if t < G(b): return k, G(a), G(b)
    return 'final', G(186), T_END
def pbar(t): return (t - TI - OFF) / BAR

# ---------------- voices ----------------
VC = json.load(open(os.path.join(HERE, 'vclips.json')))
VDIR = os.path.join(HERE, 'vz', 'ChatExport_2026-11-08 (2)')
VO = []
def vo(key, t, a=None, b=None, sub=True, mini=False, trim=None):
    v = VC[key]; fa = v['t0'] + (a or 0); fb = v['t0'] + b if b is not None else v['t1']
    if trim: fb = min(fb, fa + trim)
    VO.append(dict(key=key, t=t, fa=fa, fb=fb, d=fb - fa, who=short(v['who']), date=v['date'], file=v['file'], sub=sub, mini=mini))
# hook stabs
vo('ebanutye', 9.22, a=0.6, b=1.38, mini=True)
vo('goyda_s', 9.98, a=0.5, b=1.22, mini=True, sub=False)
vo('vodyanoy', 10.5, a=1.35, b=2.55, mini=True)
vo('burbur', 11.75, a=0, b=0.95, mini=True)
# install
vo('9min', G(2.0)); vo('ugu', G(13.3))
# people / break
vo('ebanutye', G(23.45)); vo('vodyanoy', G(26.5)); vo('frol_tupost', G(29.7)); vo('kir_mashina', G(32.85))
vo('ilya_staro', G(36.7)); vo('kolya_gospoda', G(39.6))
# prime
_t = G(44.0)
for k, tr in [('pol_8let', 7.95), ('ilya_vodka', None), ('pol_vizitka', 7.9), ('kolya_dengi', None), ('kolya_dr', None), ('pol_banya', None), ('galochka', 3.9)]:
    vo(k, _t, trim=tr); _t = VO[-1]['t'] + VO[-1]['d'] + 0.3
# otsev
vo('cheki', G(65.4), trim=7.9); vo('zavalili', G(69.2))
# tropa / dnd
vo('tropa', G(71.5)); vo('pizza1', G(78.6)); vo('pizza2', G(81.0))
# heart
vo('tarakany', G(85.4), trim=11.6); vo('styrayus', G(91.2), trim=16.6)
# zapoy
vo('peak_drink', G(100.4), b=13.95 - 1.3 + 0.0 + 0.6); vo('filtr', G(106.7)); vo('barsa', G(112.7))
# exits
vo('ne_smeshno', G(119.2)); vo('odin_pit', G(121.6), trim=6.85); vo('pokiday', G(124.9))
# larp
vo('matrix', G(127.1), trim=8.4); vo('larp_egor', G(131.5)); vo('trolli', G(134.2))
# storm
_t = G(138.0)
for k, tr, sb in [('dep', None, True), ('ilya_loh', None, True), ('manalit', None, True), ('gta6', 7.0, True), ('rpp', None, False), ('growup', None, True),
                  ('panama', None, True), ('aaa', None, False), ('kir_knizhki', 7.9, True), ('ne_ya', None, True), ('burbur', None, True)]:
    vo(k, _t, trim=tr, sub=sb); _t = VO[-1]['t'] + VO[-1]['d'] + 0.3
# credits
vo('uvazhayus', G(169.7)); vo('nik_horosho', G(171.8)); vo('frol_energ', G(173.6), trim=6.3); vo('ilya_luchshe', G(177.7))
vo('kolya_dengi', G(181.2)); vo('pol_gora', G(183.3))
# final
vo('final', G(186.6)); vo('zdorovie', G(195.6))

VOP = os.path.join(HERE, 'vo.pkl')
def prep():
    TR = {}
    for f in ['tr_0.json', 'tr_1.json']: TR.update(json.load(open(os.path.join(HERE, f))))
    cache = {}; out = []
    for v in VO:
        if v['file'] not in cache:
            raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', os.path.join(VDIR, v['file']), '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
            cache[v['file']] = np.frombuffer(raw, np.float32)
        x = cache[v['file']][int(v['fa'] * SR):int(v['fb'] * SR)].copy()
        x -= x.mean()
        rms = np.sqrt(np.mean(x ** 2) + 1e-9); x = x * (0.13 / rms)
        x = np.tanh(x * 1.6) / 1.6 * 1.25
        fi = int(0.012 * SR); x[:fi] *= np.linspace(0, 1, fi); x[-fi:] *= np.linspace(1, 0, fi)
        nb = 46; seg = np.array_split(np.abs(x), nb); env = np.array([s.max() if len(s) else 0 for s in seg]); env = env / (env.max() + 1e-6)
        ws = [w for s in TR[v['file']] for w in s['words']]
        words = [(max(0, w[0] - v['fa']), min(v['d'], w[1] - v['fa']), w[2].strip()) for w in ws if w[0] >= v['fa'] - 0.05 and w[0] < v['fb'] - 0.08]
        out.append(dict(v, audio=x.astype(np.float32), env=env, words=words))
    pickle.dump(out, open(VOP, 'wb'))
    for v in out: print(f"{v['key']:12s} {v['t']:7.2f} -> {v['t'] + v['d']:7.2f}  {v['who']:7s} | {' '.join(w[2] for w in v['words'])[:90]}")
if os.path.exists(VOP) and '--prep' not in sys.argv:
    VO = pickle.load(open(VOP, 'rb'))

# ---------------- onset envelope (for punches) ----------------
KP = os.path.join(HERE, 'kick.npy')
def build_kick():
    def load(p, sr):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '1', '-ar', str(sr), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32)
    sr = 11025
    a = load(os.path.join(HERE, 'intro.mp4'), sr); b = load(os.path.join(SP, 'v14', 'track.mp3'), sr)
    x = np.zeros(int(T_END * sr) + sr, np.float32); x[:len(a)] = a[:len(x)]; i0 = int(TI * sr); x[i0:i0 + len(b)] = b[:len(x) - i0]
    # low band
    k = np.ones(40) / 40; lo = np.convolve(x, k, 'same')
    hop = sr // FPS; n = len(lo) // hop
    e = np.sqrt(np.mean(lo[:n * hop].reshape(n, hop) ** 2, 1))
    d = np.maximum(0, e - np.concatenate([[0], e[:-1]]))
    d = d / (np.percentile(d, 99.5) + 1e-9); d = np.clip(d, 0, 1)
    out = np.zeros_like(d); acc = 0
    for i in range(len(d)): acc = max(d[i], acc * 0.72); out[i] = acc
    np.save(KP, out.astype(np.float32))
KICK = np.load(KP) if os.path.exists(KP) else np.zeros(N + 10, np.float32)
def kick(t): i = int(t * FPS); return float(KICK[i]) if 0 <= i < len(KICK) else 0.0

# ---------------- primitives ----------------
_cache = {}
def cached(key, fn):
    if key not in _cache:
        if len(_cache) > 900: _cache.clear()
        _cache[key] = fn()
    return _cache[key]
def T(txt, size, fill=WHITE, f=F_BLACK, sw=None, stroke=BLACK):
    if R.EMO_RE.search(txt): return cached(('TR', txt, size, fill, f), lambda: rich_block_img(txt, size, fill, f))
    return cached(('T', txt, size, fill, f, sw, stroke), lambda: text_img(txt, size, fill, stroke, sw, f=f))
def GT(txt, size, c1, c2, f=F_BLACKI, stroke=8): return cached(('GT', txt, size, c1, c2, f, stroke), lambda: grad_text(txt, size, c1, c2, f, stroke))
def scaled(im, s):
    if abs(s - 1) < 0.01: return im
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.BILINEAR)
def rot(im, deg): return im.rotate(deg, expand=True, resample=Image.BICUBIC) if deg else im
def slam(c, t, t0, t1, im, x, y, pop=1.6, rotd=0, fi=0.12, fo_=0.2, shake=0):
    if not (t0 <= t < t1): return
    u = t - t0; s = 1 + (pop - 1) * max(0, 1 - u / fi) ** 2
    a = min(1, u / 0.06) * clamp((t1 - t) / fo_)
    im2 = cached(('rot', id(im), rotd), lambda: rot(im, rotd)) if rotd else im
    dx = shake * math.sin(u * 90) * max(0, 1 - u / 0.4)
    put(c, scaled(im2, s), x + dx, y, a)
def pill_im(txt, size=24, bg=(0, 0, 0, 165), fg=WHITE):
    def mk():
        fo = font(F_SB, size); w = int(sum(fo.getlength(v) if k == 't' else size * 1.12 for k, v in tokens(txt))) + 40
        im = Image.new('RGBA', (w, size + 22), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, size + 21], (size + 22) // 2, fill=bg); draw_rich(im, (20, 8), txt, fo, fg); return im
    return cached(('pill', txt, size, bg, fg), mk)
def bub_im(who, text, date=None, fs=30, maxw=560, hl=False):
    def mk():
        fo = font(F_MED, fs); lines = R.layout(text, fo, maxw - 44); lh = int(fs * 1.28)
        wid = lambda l: sum(fo.getlength(v) if k == 't' else fs * 1.12 for k, v in tokens(l))
        nfo = font(F_BO, 23); dfo = font(F_MONO, 17)
        nw = nfo.getlength(who) + (dfo.getlength(date) + 22 if date else 0)
        bw = int(min(maxw, max(max(wid(l) for l in lines) + 44, nw + 44, 200))); h = 50 + lh * len(lines) + 14
        col = COL.get(who, (220, 220, 230))
        im = Image.new('RGBA', (bw + 8, h + 8), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([4, 6, bw + 3, h + 5], 24, fill=(0, 0, 0, 90))
        d.rounded_rectangle([0, 0, bw - 1, h - 1], 24, fill=(24, 26, 34, 238), outline=(col + (200,)) if hl else (255, 255, 255, 40), width=3 if hl else 2)
        d.text((22, 13), who, font=nfo, fill=col)
        if date: d.text((bw - 22 - dfo.getlength(date), 17), date, font=dfo, fill=(140, 140, 155))
        for j, l in enumerate(lines): draw_rich(im, (22, 46 + lh * j), l, fo, WHITE)
        return im
    return cached(('bub', who, text, date, fs, maxw, hl), mk)
def chat_stack(c, t, items, bottom=800, top=160, side_x=None):
    # items: list of (t_appear, who, text, date, side, fs)
    y = float(bottom)
    vis = [x for x in items if x[0] <= t]
    for it in reversed(vis):
        ta, who, text, date, side = it[:5]; fs = it[5] if len(it) > 5 else 30
        im = bub_im(who, text, date, fs); u = t - ta; ein = easeback(min(1, u / 0.3))
        yy = y - im.height; a = min(1, ein * 1.5) * clamp((yy + im.height - top) / 120)
        if a <= 0: break
        xx = {'L': 22, 'R': W - 22 - im.width, 'C': (W - im.width) / 2}[side]
        put(c, im, xx, yy + (1 - ein) * 60, a, 'tl')
        y -= (im.height + 14) * ein
def stamp_im(txt, col, size=46):
    def mk():
        tx = text_img(txt, size, col, col, 0, f=F_BLACK)
        fr = Image.new('RGBA', (tx.width + 40, tx.height + 24), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle([3, 3, fr.width - 4, fr.height - 4], 12, outline=col + (255,), width=7)
        fr.alpha_composite(tx, (20, 12)); a = np.array(fr); m = np.random.default_rng(len(txt)).random(a.shape[:2]) < 0.16; a[m, 3] = (a[m, 3] * 0.3).astype(np.uint8)
        return Image.fromarray(a)
    return cached(('stamp', txt, col, size), mk)
def caption(c, t, t0, t1, lines, y, size=46, f=F_SER, col=WHITE, gap=12, fi=0.5):
    a = fade(t, t0, t1, fi, 0.4)
    if a <= 0: return
    yy = y
    for l in lines:
        im = fitw(T(l, size, col, f, 3)); put(c, im, W / 2, yy + 10 * (1 - a), a); yy += im.height + gap
def mono(c, x, y, txt, size=24, col=NEON, a=1.0, anchor='tl'):
    im = cached(('mono', txt, size, col), lambda: text_img(txt, size, col, BLACK, 2, f=F_MONO)); put(c, im, x, y, a, anchor); return im
def chip(c, t, t0, t1, txt, y=118, col=WHITE):
    a = fade(t, t0, t1, 0.3, 0.3)
    if a > 0: put(c, pill_im(txt, 24, (0, 0, 0, 175), col), W / 2, y, a)

# ---------------- voice plaque + karaoke ----------------
def pages(words, fo, maxw=640):
    pg, cur, line, lw = [], [], [], 0
    for w in words:
        ww = fo.getlength(w[2] + ' ')
        if line and lw + ww > maxw:
            cur.append(line); line, lw = [], 0
            if len(cur) == 2: pg.append(cur); cur = []
        line.append(w); lw += ww
    if line: cur.append(line)
    if cur: pg.append(cur)
    return pg
def plaque_base(v):
    def mk():
        col = COL.get(v['who'], GREY); w, h = 660, 116
        im = Image.new('RGBA', (w + 10, h + 10), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([5, 8, w + 4, h + 7], 30, fill=(0, 0, 0, 110))
        d.rounded_rectangle([0, 0, w - 1, h - 1], 30, fill=(16, 18, 26, 236), outline=col + (170,), width=3)
        d.ellipse([18, 18, 98, 98], fill=col); ini = v['who'][0]
        fo = font(F_BLACK, 44); d.text((58 - fo.getlength(ini) / 2, 30), ini, font=fo, fill=(15, 15, 20))
        d.text((118, 14), v['who'], font=font(F_BO, 29), fill=col)
        d.text((118 + font(F_BO, 29).getlength(v['who']) + 14, 22), '· голосовое · ' + v['date'], font=font(F_MONO, 18), fill=(150, 150, 165))
        return im
    return cached(('plq', v['who'], v['date']), mk)
def draw_voice(c, t, v, y=1118):
    u = t - v['t']
    if u < -0.05 or u > v['d'] + 0.25: return
    col = COL.get(v['who'], GREY)
    if v['mini']:
        a = clamp(min((u + 0.05) / 0.05, (v['d'] + 0.12 - u) / 0.12))
        tag = pill_im('🎤 ' + v['who'] + ' · ' + v['date'], 22, (0, 0, 0, 190), col); put(c, tag, W / 2, 330, a)
        txt = ' '.join(w[2] for w in v['words']).upper() if v['sub'] else ''
        if not txt: return
        im = fitw(T(txt, 96, col, F_BLACK, 8), W - 50); s = 1 + 0.35 * max(0, 1 - (u + 0.05) / 0.12) ** 2
        put(c, scaled(im, s), W / 2 + 6 * math.sin(u * 70), 430, a); return
    ein = easeback(clamp((u + 0.05) / 0.3)); aout = clamp((v['d'] + 0.25 - u) / 0.25)
    a = min(1, ein * 1.4) * aout; yy = y + (1 - ein) * 80 + (1 - aout) * 40
    base = plaque_base(v).copy(); d = ImageDraw.Draw(base)
    prog = clamp(u / v['d']); env = v['env']; nb = len(env); x0, x1, cy = 118, 590, 80
    bw = (x1 - x0) / nb; lv = kick(t)
    for i in range(nb):
        hh = 4 + 26 * env[i]
        if abs(i / nb - prog) < 1.5 / nb and 0 < u < v['d']: hh = min(34, hh + 10 * lv + 4)
        played = i / nb <= prog
        d.rounded_rectangle([x0 + i * bw + 1, cy - hh / 2, x0 + i * bw + bw - 3, cy + hh / 2], 2, fill=(col if played else (90, 92, 108)))
    sec = int(clamp(u, 0, v['d'])); d.text((604, 66), f'0:{sec:02d}', font=font(F_MONO, 22), fill=(200, 200, 210))
    # live dot
    if 0 < u < v['d'] and int(u * 4) % 2 == 0: d.ellipse([622, 22, 640, 40], fill=RED)
    put(c, base, W / 2, yy, a)
    if not v['sub'] or not v['words']: return
    fo = font(F_BLACK, 42 if v['d'] > 2 else 50)
    pg = cached(('pg', v['key'], v['t']), lambda: pages(v['words'], fo))
    cur = None
    for p in pg:
        if u >= p[0][0][0] - 0.25: cur = p
    if cur is None: return
    p0 = cur[0][0][0]; ap = a * clamp((u - p0 + 0.25) / 0.12)
    lh = 54; ybase = yy - 70 - lh * len(cur)
    sub = Image.new('RGBA', (W, lh * len(cur) + 20), (0, 0, 0, 0)); sd = ImageDraw.Draw(sub)
    for li, line in enumerate(cur):
        lw = sum(fo.getlength(w[2] + ' ') for w in line) - fo.getlength(' '); x = (W - lw) / 2
        for w in line:
            if u >= w[1]: f_ = WHITE
            elif u >= w[0]: f_ = col
            else: f_ = (255, 255, 255, 110)
            sd.text((x, 6 + li * lh), w[2], font=fo, fill=f_, stroke_width=5, stroke_fill=(0, 0, 0, 230 if len(f_) == 3 else 110))
            x += fo.getlength(w[2] + ' ')
    put(c, sub, 0, ybase, ap, 'tl')

# ---------------- backgrounds ----------------
def shot_bg(idx, u, z0=1.0, z1=1.08, kz=0.0, panf=1.0):
    img = shot_img(idx); cx = FOCUS.get(idx, 1138)
    pan = 150 * panf * (1 if idx % 2 else -1); z = lerp(z0, z1, u) + kz
    cw, ch = 720 / z, 1280 / z
    x0 = cx - cw / 2 + pan * (u - 0.5); x0 = min(max(0, x0), 2276 - cw); y0 = (1280 - ch) / 2
    M_ = np.float32([[z, 0, -x0 * z], [0, z, -y0 * z]])
    return cv2.warpAffine(img, M_, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
def seq_bg(t, t0, shots, ln, **kw):
    rel = max(0, t - t0) / ln; j = int(rel); u = rel - j
    return shot_bg(shots[j % len(shots)], u, **kw), j, u
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.18 - 0.8 * np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2), 0.25, 1)[..., None]
TINT = {'neutral': (0, 0, 0), 'prime': (40, -10, 40), 'cold': (-12, 0, 18), 'green': (-10, 22, -6), 'warm': (35, 12, -20), 'storm': (10, 0, 15), 'red': (60, -20, -20)}
def grade(img, mode='neutral', dark=0.6, sat=1.0, t=0.0):
    x = img.astype(np.float32)
    if sat != 1.0: g = x.mean(2, keepdims=True); x = g + (x - g) * sat
    x = x + np.array(TINT[mode], np.float32)
    x = x * dark * VIG
    r = np.random.default_rng(int(t * 30)); x += r.normal(0, 5, (H // 4, W // 4, 1)).repeat(4, 0).repeat(4, 1)
    return np.clip(x, 0, 255).astype(np.uint8)
# watermark blur on intro
WM = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'wm.json'))).items()}
def intro_frame(t):
    idx = max(1, min(554, int(t * 30) + 1))
    img = cv2.cvtColor(cv2.imread(os.path.join(HERE, 'if', f'{idx:04d}.jpg')), cv2.COLOR_BGR2RGB)
    boxes = []
    if idx <= 278 or idx >= 540: boxes.append((520, 380, 141, 20))
    if 266 <= idx <= 556: boxes.append((53, 780, 141, 20))
    s = WM.get(idx)
    if s and s[0] > 0.55: boxes.append(tuple(s[1:5]))
    for (x, y, w, h) in boxes:
        x0, y0, x1, y1 = max(0, x - 20), max(0, y - 84), min(W, x + w + 20), min(H, y + h + 14)
        roi = img[y0:y1, x0:x1].astype(np.float32); bl = cv2.GaussianBlur(roi, (0, 0), 16)
        mk = np.zeros(roi.shape[:2], np.float32); mk[12:-12, 12:-12] = 1; mk = cv2.GaussianBlur(mk, (0, 0), 6)[..., None]
        img[y0:y1, x0:x1] = (roi * (1 - mk) + bl * mk).astype(np.uint8)
    return img
# кружки (Egor's alcohol-series circles)
KR = [(os.path.join(SP, 'v10', f'k{i}'), n) for i, n in [(1, 0), (2, 0), (3, 0), (4, 0), (5, 0)]] + \
     [(os.path.join(SP, 'v11', f'kb{i}'), 0) for i in (1, 2, 3, 4)] + [(os.path.join(SP, 'v12', 'kc1'), 0)]
KR = [(p, len(os.listdir(p))) for p, _ in KR]
def krug_frame(k, rel, size):
    p, n = KR[k % len(KR)]; i = int(rel * 30) % n + 1
    im = cv2.imread(os.path.join(p, f'{i:04d}.jpg')); im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
    return cv2.resize(im, (size, size), interpolation=cv2.INTER_AREA)
_cm = {}
def circ_mask(d):
    if d not in _cm:
        m = Image.new('L', (d * 2, d * 2), 0); ImageDraw.Draw(m).ellipse([2, 2, d * 2 - 3, d * 2 - 3], fill=255); _cm[d] = m.resize((d, d), Image.LANCZOS)
    return _cm[d]
def put_circle(c, arr, cx, cy, d, a=1.0, ring=None, prog=0.0):
    im = Image.fromarray(cv2.resize(arr, (d, d), interpolation=cv2.INTER_AREA)).convert('RGBA'); im.putalpha(circ_mask(d))
    put(c, im, cx, cy, a)
    if ring:
        dr = ImageDraw.Draw(c); r = d / 2 + 9
        dr.arc([cx - r, cy - r, cx + r, cy + r], -90, -90 + 360 * prog, fill=ring, width=7)
# matrix rain
_MX = None
def matrix_layer(t):
    global _MX
    if _MX is None:
        rng = np.random.default_rng(7); chars = 'ТРОПАРЕВО86ЛАРПЛОР01'; fo = font(F_MONO, 26); cols = []
        for i in range(24):
            strip = Image.new('L', (30, 2600), 0); d = ImageDraw.Draw(strip)
            for j in range(0, 2600, 30):
                if rng.random() < 0.8: d.text((4, j), chars[rng.integers(len(chars))], font=fo, fill=int(rng.uniform(60, 255)))
            cols.append((np.array(strip), rng.uniform(140, 420), rng.uniform(0, 2600)))
        _MX = cols
    out = np.zeros((H, W), np.uint8)
    for i, (s, sp, o) in enumerate(_MX):
        y = int((o + sp * t) % 2600); st = np.vstack([s, s])[2600 - y: 2600 - y + H] if y > 0 else s[:H]
        out[:, i * 30:i * 30 + 30] = st[:H]
    return out

# ---------------- content: chat messages ----------------
def m_(sub, who=None, date=None, text=None): return M(sub, who, date, text)
PRIME_B = [(44.6, m_('егора я попускаю жоска', 'Анфиса', text='чисто предупреждение, вдруг кто не понял, егора я попускаю жоска только здесь, чтобы не расслаблялся'), 'L'),
           (47.6, m_('хоть бы спс кто сказал', 'Егор', '19.08.2025', text='хоть бы спс кто сказал...'), 'R'),
           (50.6, m_('отпустил чечню', 'Анфиса'), 'L'),
           (53.4, m_('опять Егора забулили', 'Никита'), 'L'),
           (56.2, m_('за пиццу и водку кстати с тебя 3000', 'Егор'), 'R'),
           (59.0, m_('слоты в желудке', 'Фрол', '24.08.2025', text='Если ты будешь есть корки то просто слоты в желудке забиваешь'), 'L'),
           (63.2, m_('А че вы его опять забулили', 'Никита'), 'L')]
OTSEV_B = [(66.9, m_('Егор опять забулил человека', 'Никита', text='Пиздец\nЕгор опять забулил человека\nСначала Илья\nПотом раед\nТеперь полина'), 'L'),
           (69.55, m_('Компания мертва ровно 33', 'Егор', text='Компания мертва ровно 33 дня'), 'R'),
           (69.95, m_('компания мертва ровно 34', 'Егор'), 'R'),
           (70.35, m_('компания мертва ровно 35', 'Егор'), 'R'),
           (70.75, m_('В апреле побухаем', 'Никита', '06.02.2026'), 'L')]
DND_B = [(78.5, m_('Кто последний тот фурри друид', 'Фрол', text='Кто последний тот фурри друид'), 'L'),
         (79.6, m_('шансы стать фурри друидом', 'Фрол'), 'L'),
         (82.2, m_('отбой нету мячика', 'Илья'), 'L'), (82.55, m_('отбой нету мячика', 'Фрол'), 'L'), (82.9, m_('отбой нету мячика', 'Егор'), 'R')]
HEART_B = [(97.2, m_('Мы уже 10 лет друг друга ненавидим', 'Кирилл'), 'L'), (98.0, m_('Добро пожаловать в клуб', 'Кирилл', '30.08.2025'), 'L'),
           (98.8, dict(who='Егор', date='30.08.2025', text='11'), 'R')]
EXIT_B = [(121.0, m_('вернется в компанию только в 2032', 'Никита'), 'L'), (121.9, m_('Ставь лайк если читаешь это до 2032', 'Фрол'), 'L')]
EXIT_K = [(123.0 + 0.25 * i, dict(who='Кирилл', date='29.03.2026', text=str(y)), 'L') for i, y in enumerate(range(2019, 2027))]
LARP_B = [(129.0, m_('ограничителем реальности', 'Никита', text='Понимаешь Фрол, ты мнишь себя гг, но тебя ограничивает реальность. А в моем случае - я являюсь ограничителем реальности🤌'), 'L'),
          (132.6, m_('ты сейчас ларпишь предъяву по ларпу', 'Егор'), 'R'),
          (135.1, m_('а че такое кубики фэри', 'Фрол'), 'L')]
STORM_M = [m_('Угу-угу', 'Никита', text='Угу-угу продолжай 🗿'), m_('ваше здоровье', 'Егор', text='Ваше здоровье 🍻'),
           m_('купил 1 акцию Газпрома', 'Никита'), m_('Понял, вычеркиваю из списка', 'Никита'), m_('Ирина, здравствуйте!', 'Никита', text='Ирина, здравствуйте! 🙏🙏🙏🙏'),
           m_('слоты в желудке', 'Фрол', text='слоты в желудке забиваешь'), m_('компания мертва ровно 35', 'Егор'), m_('В апреле побухаем', 'Никита'),
           m_('Кто последний тот фурри друид', 'Фрол', text='Кто последний тот фурри друид'), m_('отбой нету мячика', 'Илья'),
           m_('я контентмейкер и сммщик', 'Егор', text='я контентмейкер и сммщик данного чата\nгде зп кст'),
           m_('Ураааааа', 'Юрий'), m_('а че такое кубики фэри', 'Фрол'), m_('ты сейчас ларпишь предъяву по ларпу', 'Егор'),
           m_('Ставь лайк если читаешь это до 2032', 'Фрол'), m_('Добро пожаловать в клуб', 'Кирилл'), m_('опять Егора забулили', 'Никита'),
           m_('за пиццу и водку кстати с тебя 3000', 'Егор'), m_('отпустил чечню', 'Анфиса'), m_('Необязательно придерживаться документального', 'Егор', text='Ирина, здравствуйте! Необязательно придерживаться документального направления 🙏🏼'),
           m_('опарыши заведутся в пасте', 'Никита'), m_('у меня дежурство 5 декабря', 'Кирилл'), m_('ноябрь месяц трезвости', 'Егор'),
           m_('если тебя приглашают', 'Егор', text='если тебя приглашают\nзначит тебя ждут\nвопрос закрыт'),
           m_('Мы уже 10 лет друг друга ненавидим', 'Кирилл'), m_('КАК ЖЕ Я ВАС ВСЕХ СУКА НЕНАВИЖУ', 'Никита', text='КАК ЖЕ Я ВАС ВСЕХ СУКА НЕНАВИЖУ'),
           m_('сказал вернется в компанию только в 2032', 'Никита'), m_('Ураа', 'Юрий', '01.10.2025'), m_('Угу-угу', 'Никита', text='Угу-угу'), m_('пора сделать 8 минутный видос', 'Егор')]
VERS = [('1.0–1.9', 'эра до Егора: мемы про ахмеда'), ('2.0–2.5', 'дэдпул, гражданская война, кюрпек и огэ'), ('2.6–3.0', 'до апреля 2017'),
        ('3.0–4.0', 'золотая эпоха лета 2017 и 11 класса'), ('4.0–5.0', 'стагнация, но по сравнению с сейчас — движ'), ('5.0–5.5', 'пандемийная, говядина со сгущёнкой'),
        ('5.5–6.0', 'ваш прайм, дача Кирилла, я в армии'), ('6.0–6.5', 'своеобразный, но прайм с частыми сборами'), ('6.5–7.0', 'было славно, но кукуха начинала слетать'),
        ('8.1–8.2', 'эра анфисы'), ('8.5', 'появился днд')]
PEOPLE = [  # name, role, stats, shots, t0(bar), t1(bar)
    ('Егор', 'мотор, радио и основатель', ['30 815 сообщений · 52% чата', 'писал в 443 днях из 465'], [0, 2], 23, 26.25),
    ('Никита', 'спарринг-партнёр и стабилизатор', ['15 833 сообщения · 27%', 'фирменное: «Угу-угу продолжай» 🗿'], [8, 10], 26.25, 29.5),
    ('Фрол', 'совесть группы и мастер игры', ['3 759 сообщений', 'ведёт ДнД · говорит как есть'], [4, 6], 29.5, 32.75),
    ('Кирилл', 'снайпер-хронист из Панамы', ['3 726 сообщений', 'ведёт статистику уходов Егора'], [69, 71], 32.75, 36),
    ('Илья', 'отсутствующий центр', ['1 872 сообщения', 'о нём пишут чаще, чем он сам'], [12, 14], 36, 38),
    ('Юрий', 'голос простоты и моральный компас', ['912 сообщений', 'на любую новость об уходе Егора:'], [73, 75], 38, 39.5),
    ('Коля', 'хозяин площадки', ['128 сообщений', 'пишет редко, но по делу'], [91, 93], 39.5, 43)]
CRED = [('Егор Гусев', 'Егор', 'мотор, радио и основатель', 169, 171.5), ('Никита Куприяшин', 'Никита', 'спарринг-партнёр и стабилизатор', 171.5, 173.5),
        ('Фрол', 'Фрол', 'совесть группы и мастер игры', 173.5, 175.5), ('Кирилл Рустамов', 'Кирилл', 'снайпер-хронист из Панамы', 175.5, 177.5),
        ('Илья', 'Илья', 'отсутствующий центр', 177.5, 179.5), ('Юрий', 'Юрий', 'голос простоты и моральный компас', 179.5, 181),
        ('Николай Турусов', 'Коля', 'хозяин площадки', 181, 183), ('Анфиса · Полина · Настя · Раед', 'Полина', 'приглашённые звёзды прайма', 183, 186)]
CRED_X = {'Егор': '«Я уважаюсь»', 'Никита': 'угу-угу 🗿', 'Фрол': 'приготовьте себе что-нибудь вкусненькое', 'Кирилл': '«Добро пожаловать в клуб»',
          'Илья': '«Я бы лучше не придумал»', 'Юрий': '«Ураааааа»', 'Коля': 'гонорар: «мне деньги не нужны»', 'Полина': 'август 2025 · прайм с 11 людьми'}

# ---------------- section renderers (draw on PIL canvas c) ----------------
def card(c, t, t0, t1, num, name, role, stats, y=250):
    if not (t0 - 0.05 <= t < t1): return
    u = t - t0; ein = easeback(clamp(u / 0.35)); aout = clamp((t1 - t) / 0.22); a = min(1, ein * 1.5) * aout
    dx = (1 - ein) * 260 - (1 - aout) * 200; col = COL[name]
    mono(c, 40 + dx, y, f'УЧАСТНИК {num:02d}/07', 22, col, a)
    im = GT(name.upper(), 118, col, tuple(min(255, int(v * 0.55 + 110)) for v in col)); put(c, im, 40 + dx, y + 34, a, 'tl')
    r = fitw(T('«' + role + '»', 40, CREAM, F_SERI, 3), W - 70); put(c, r, 40 + dx, y + 40 + im.height, a, 'tl')
    yy = y + 50 + im.height + r.height
    for j, s in enumerate(stats):
        aj = a * clamp((u - 0.25 - 0.12 * j) / 0.2)
        put(c, fitw(T(s, 30, WHITE, F_SB, 3), W - 70), 44 + dx, yy + j * 46, aj, 'tl')

def hook(t):
    # base frame
    img = intro_frame(t).astype(np.float32)
    k = kick(t)
    if 5.96 <= t < 8.1:  # punch zoom
        z = 1 + 0.22 * eo((t - 5.96) / 0.5) + 0.03 * k
    else: z = 1 + 0.04 * k
    if 1.74 <= t < 2.92:
        j = int((t - 1.74) / 0.168); col = list(COL.values())[j % 7]; img = img * 0.7 + np.array(col) * 0.3
    if 12.26 <= t < 14.45: img = img + np.array([30, 10, -25]) * fade(t, 12.26, 14.45, 0.2, 0.2)
    if 8.16 <= t < 9.22: g = img.mean(2, keepdims=True); img = g * 0.8 + img * 0.2
    img = np.clip(img, 0, 255).astype(np.uint8)
    if z != 1: M_ = cv2.getRotationMatrix2D((W / 2, H * 0.45), 0, z); img = cv2.warpAffine(img, M_, (W, H), borderMode=cv2.BORDER_REFLECT)
    if 9.22 <= t < 10.4 or 11.45 <= t < 11.6:  # glitch
        rng = np.random.default_rng(int(t * 30)); out = img.copy()
        for _ in range(9):
            y0 = rng.integers(0, H - 60); hh = rng.integers(10, 70); out[y0:y0 + hh] = np.roll(img[y0:y0 + hh], rng.integers(-80, 80), 1)
        out[..., 0] = np.roll(out[..., 0], 9, 1); out[..., 2] = np.roll(out[..., 2], -9, 1); img = out
    # chat shrink
    if t >= 15.7:
        u = eo((t - 15.7) / 0.6)
        bgc = np.full((H, W, 3), (14, 17, 24), np.uint8)
        c = Image.fromarray(bgc).convert('RGBA')
        chat_stack(c, t, [(15.75, 'Егор', 'смотрите что нашёл', '08.11.2026', 'R'), (15.95, 'Никита', 'Угу-угу продолжай 🗿', '08.11.2026', 'L')], bottom=420, top=120)
        d = int(lerp(W * 1.4, 430, u)); cy = lerp(H / 2, 760, u)
        sq = img[int(H * 0.45 - W / 2):int(H * 0.45 + W / 2)] if True else img
        put_circle(c, sq, W / 2, cy, d, 1.0, ring=COL['Егор'] if u > 0.95 else None, prog=clamp((t - 16.2) / 1.0))
        if t >= 16.52: slam(c, t, 16.52, 17.22, stamp_im('ВЕРСИЯ 8.6', RED, 64), W / 2, 1080, pop=2.2, rotd=-8, shake=10)
    else:
        c = Image.fromarray(img).convert('RGBA')
    # REC
    if t < 15.7:
        if int(t * 2) % 2 == 0: ImageDraw.Draw(c).ellipse([28, 48, 48, 68], fill=RED)
        mono(c, 58, 44, 'REC  tropar_8.6.exe', 22, WHITE)
    # receipt
    if 0.5 <= t < 1.72:
        def mk():
            im = Image.new('RGBA', (430, 270), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
            d.rectangle([0, 0, 429, 269], fill=(246, 244, 236)); fo = font(F_MONO, 24)
            for i in range(0, 430, 20): d.polygon([(i, 269), (i + 10, 255), (i + 20, 269)], fill=(0, 0, 0, 0))
            for j, (l, f_) in enumerate([('ЧЕК № 1 · 24.08.2025', 22), ('пицца + водка', 26), ('ИТОГО ...... 3000 ₽', 30), ('оплачено: НЕТ', 26), ('(с) Егор', 22)]):
                d.text((24, 18 + j * 46), l, font=font(F_MONO, f_), fill=(20, 20, 20) if j != 3 else (200, 20, 30))
            return rot(im, -5)
        slam(c, t, 0.5, 1.72, cached('receipt', mk), W / 2, 860, pop=1.5)
    if 1.74 <= t < 2.92:
        names = ['ЕГОР', 'НИКИТА', 'ФРОЛ', 'КИРИЛЛ', 'ИЛЬЯ', 'ЮРИЙ', 'КОЛЯ']; j = int((t - 1.74) / 0.168) % 7
        col = list(COL.values())[j]; slam(c, t, 1.74 + j * 0.168, 1.74 + (j + 1) * 0.168, T(names[j], 150, col, F_BLACK, 10), W / 2, 640, pop=1.35, fi=0.08, fo_=0.03)
    if 2.92 <= t < 4.3:
        evs = ['Илья покинул группу', 'Никита вышел из беседы', 'Егор Гусев вышел из беседы', 'Фрол вышел из беседы',
               'Егор Гусев вернулся в группу', 'Егор Гусев вернулся в группу', 'Егор Гусев вернулся в группу', 'Егор Гусев вернулся в группу']
        for i, e in enumerate(evs):
            ta = 2.92 + i * 0.16
            if t >= ta: slam(c, t, ta, 4.3, pill_im(e, 28, (0, 0, 0, 185)), W / 2, 380 + i * 62, pop=1.3, fi=0.08)
    if 4.2 <= t < 5.95:
        u = eo((t - 4.2) / 1.1); a = fade(t, 4.2, 5.95, 0.1, 0.2)
        for j, (val, lab) in enumerate([(59177, 'сообщений'), (501, 'голосовое'), (465, 'дней')]):
            v = int(val * u); s = f'{v:,}'.replace(',', ' ')
            put(c, T(s, 118, NEON, F_MONO, 8), W / 2, 420 + j * 210, a); put(c, T(lab, 40, WHITE, F_BO, 4), W / 2, 500 + j * 210, a)
    if 5.96 <= t < 8.12:
        a = fade(t, 5.96, 8.12, 0.15, 0.2)
        put(c, GT('ЭРГОНОМИКА ЧАТА', 70, COL['Егор'], GOLD), W / 2, 230, a)
        for j, (nm, pc) in enumerate([('Егор', 52), ('Никита', 27), ('ещё 8 человек', 21)]):
            col = COL.get(nm, GREY); w = int(560 * pc / 100 * eo((t - 6.1 - 0.2 * j) / 0.6)); y = 330 + j * 90
            d = ImageDraw.Draw(c); d.rounded_rectangle([80, y, 80 + max(8, w), y + 54], 14, fill=col + (int(225 * a),))
            put(c, T(f'{nm} {pc}%', 34, WHITE, F_BLACK, 4), 96, y + 4, a, 'tl')
    if 8.12 <= t < 9.22:
        im = bub_im('Егор', 'Компания мертва ровно 35 дней', '05.03.2026', 44, 640, True); slam(c, t, 8.14, 9.22, im, W / 2, 640, pop=1.25)
    if 10.4 <= t < 12.24:
        memes = [('УГУ-УГУ 🗿', 'Никита'), ('ВАШЕ ЗДОРОВЬЕ 🍻', 'Егор'), ('ПОНЯЛ, ВЫЧЕРКИВАЮ', 'Никита'), ('ИРИНА, ЗДРАВСТВУЙТЕ 🙏', 'Никита'),
                 ('СЛОТЫ В ЖЕЛУДКЕ', 'Фрол'), ('ОТБОЙ НЕТУ МЯЧИКА', 'Илья'), ('ФУРРИ ДРУИД', 'Фрол'), ('В АПРЕЛЕ ПОБУХАЕМ', 'Никита')]
        j = min(7, int((t - 10.4) / 0.23)); txt, who = memes[j]
        im = cached(('hm', j), lambda: rot(fitw(rich_block_img(txt, 74, COL[who]), W - 40), [-6, 5, -3, 7, -5, 4, -7, 3][j]))
        slam(c, t, 10.4 + j * 0.23, 10.4 + (j + 1) * 0.23, im, W / 2, 900 if j % 2 else 760, pop=1.5, fi=0.07, fo_=0.03)
    if 12.26 <= t < 14.45:
        caption(c, t, 12.26, 14.45, ['Тропарёвский парк', '24.04.2026 · возвращение прайма'], 880, 50, F_SERI, CREAM)
    if 14.46 <= t < 15.72:
        q = ['Егор Гусев вышел из беседы', 'Илья покинул группу', 'Никита вышел из беседы', 'Раед покинул группу', 'Егор Гусев вышел из беседы',
             'Полина покинула группу', 'Илья покинул группу', 'Егор Гусев вышел из беседы', 'Фрол вышел из беседы', 'Егор Гусев вышел из беседы',
             'Илья покинул группу', 'Егор Гусев вышел из беседы']
        n_ = int((t - 14.46) / 0.1) + 1
        for i in range(min(n_, len(q))):
            put(c, pill_im(q[i], 26, (0, 0, 0, 190)), W / 2 + (14 if i % 2 else -14), 1180 - i * 70, 1.0)
        put(c, T('ОЧЕРЕДЬ НА ВЫХОД', 60, RED, F_BLACK, 6), W / 2, 200, fade(t, 14.46, 15.72, 0.1, 0.1))
    for v in VO:
        if v['mini'] and v['t'] - 0.1 <= t < v['t'] + v['d'] + 0.2: draw_voice(c, t, v)
    if t >= 17.2:
        c = Image.new('RGBA', (W, H), (4, 6, 8, 255)); u = t - 17.2
        lines = ['> поиск обновлений...', '> найдено: ТРОПАРЕВО 8.6', '> 59 177 сообщений · 501 голосовое', '> установить? [Y/N] ']
        for j, l in enumerate(lines):
            tj = j * 0.16
            if u >= tj: mono(c, 40, 470 + j * 56, l[:int((u - tj) * 90)], 28, NEON)
        if u >= 0.85: mono(c, 40 + font(F_MONO, 28).getlength(lines[3]) + 2, 470 + 3 * 56, 'Y', 28, WHITE)
        if int(u * 4) % 2 == 0: ImageDraw.Draw(c).rectangle([40, 720, 56, 748], fill=NEON)
        if u > 1.1: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * clamp((u - 1.1) / 0.18)))))
    return c

def rich_block_img(txt, size, col, f=F_BLACK):
    fo = font(f, size); w = int(sum(fo.getlength(v) if k == 't' else size * 1.12 for k, v in tokens(txt))) + 30
    im = Image.new('RGBA', (w + 20, int(size * 1.4) + 20), (0, 0, 0, 0))
    sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    for dx in range(-6, 7, 3):
        for dy in range(-6, 7, 3): draw_rich(sh, (15 + dx, 10 + dy), txt, fo, (0, 0, 0, 255))
    im.alpha_composite(sh); draw_rich(im, (15, 10), txt, fo, col); return im

def render(fi):
    t = fi / FPS
    if t < TI: return np.array(hook(t).convert('RGB'))
    s, a0, a1 = sec_at(t); br = pbar(t); k = kick(t); fl = 0.0
    # ---------- background ----------
    if s == 'install':
        b, j, u = seq_bg(t, a0, [120, 125, 113, 91, 101], BAR * 4); bg = grade(b, 'cold', 0.22, 0.4, t)
    elif s == 'title':
        b = shot_bg(111, clamp((t - a0) / (a1 - a0)), 1.15, 1.0, 0.03 * k); bg = grade(b, 'storm', 0.75, 1.1, t)
    elif s in ('people', 'break'):
        p = next(p for p in PEOPLE if t < G(p[5])); u = clamp((t - G(p[4])) / (G(p[5]) - G(p[4])))
        idx = p[3][0] if u < 0.5 else p[3][1]
        b = shot_bg(idx, (u * 2) % 1, 1.04, 1.12, 0.025 * k); bg = grade(b, 'neutral', 0.55, 0.9, t)
    elif s == 'prime':
        b, j, u = seq_bg(t, a0, [112, 116, 123, 127, 131, 120, 135, 52, 45, 41, 114, 129, 37, 133, 47, 118, 125, 54, 121, 136, 130, 117], BAR)
        bg = grade(b, 'prime', 0.55, 1.15, t); fl = 0.22 * max(0, 1 - u * BAR / 0.12)
    elif s == 'otsev':
        b, j, u = seq_bg(t, a0, [80, 100, 109, 85], BAR * 1.5); bg = grade(b, 'cold', 0.45, 0.2, t)
    elif s == 'tropa':
        b, j, u = seq_bg(t, a0, [83, 84, 86, 87, 88, 89, 90, 85], BAR * 2 if br < 78 else BAR); bg = grade(b, 'green', 0.5, 0.95, t)
    elif s == 'heart':
        b, j, u = seq_bg(t, a0, [104, 106, 108], BAR * 5, z0=1.0, z1=1.05, panf=0.5); bg = grade(b, 'cold', 0.38, 0.15, t)
    elif s == 'zapoy':
        kk = int((br - 100) / 2); fr = krug_frame(kk, t - G(100 + kk * 2), 360)
        b = cv2.resize(cv2.GaussianBlur(fr, (0, 0), 9), (W * 2, W * 2))[(W * 2 - H) // 2:(W * 2 - H) // 2 + H, W // 2:W // 2 + W]
        bg = grade(b, 'warm', 0.42, 1.0, t)
    elif s == 'exits':
        b, j, u = seq_bg(t, a0, [118, 109], BAR * 4, panf=0.4); bg = grade(b, 'cold', 0.35, 0.1, t)
    elif s == 'larp':
        b, j, u = seq_bg(t, a0, [30, 34, 18, 70], BAR * 2.5); g = grade(b, 'green', 0.3, 0.2, t).astype(np.float32)
        mx = matrix_layer(t - a0).astype(np.float32)[..., None] / 255
        bg = np.clip(g + mx * np.array([60, 255, 110]) * 0.55, 0, 255).astype(np.uint8)
    elif s == 'storm':
        b, j, u = seq_bg(t, a0, R14.FAST, BAR / 2, z0=1.06, z1=1.12, kz=0.05 * k); bg = grade(b, 'storm', 0.62, 1.2, t)
        fl = 0.3 * max(0, 1 - u * BAR / 2 / 0.1)
    elif s == 'credits':
        b, j, u = seq_bg(t, a0, [47, 112, 42, 109, 71, 100, 50, 137], BAR * 2.125); bg = grade(b, 'neutral', 0.42, 0.8, t)
    else:
        b = shot_bg(137, clamp((t - a0) / (T_END - a0)), 1.0, 1.12); bg = grade(b, 'storm', 0.5 * clamp((T_END - t) / 2.0), 1.0, t)
    c = Image.fromarray(bg).convert('RGBA')
    # ---------- overlays ----------
    if s == 'install':
        d = ImageDraw.Draw(c)
        mono(c, 36, 96, 'TROPAREVO UPDATE MANAGER  v8.6', 26, NEON); d.line([36, 138, W - 36, 138], fill=NEON + (140,), width=2)
        for i, (vv, txt) in enumerate(VERS):
            ta = G(1.0 + i * 1.3)
            if t >= ta:
                n_ = int((t - ta) * 60); line = f'[OK] v{vv}'; full = line + '  ' + txt
                mono(c, 36, 156 + i * 42, full[:n_], 19, NEON if n_ < len(full) else (170, 255, 190))
        ta = G(1.0 + len(VERS) * 1.3)
        if t >= ta:
            blink = (int(t * 3) % 2 == 0) or br > 20
            if blink: mono(c, 36, 156 + len(VERS) * 42, '[..] v8.6  устанавливается…' if br < 20 else '[OK] v8.6  УСТАНОВЛЕНО', 19, GOLD if br < 20 else NEON)
        # progress
        if br < 13: pr = 0.86 * br / 13
        elif br < 15.6: pr = 0.86
        else: pr = 0.86 + 0.14 * clamp((br - 15.6) / 4.4)
        y0 = 772; d.rounded_rectangle([36, y0, W - 36, y0 + 34], 8, outline=NEON, width=3)
        segs = int(pr * 40)
        for q in range(segs): d.rectangle([44 + q * 15.8, y0 + 7, 44 + q * 15.8 + 11, y0 + 27], fill=NEON if not (13 <= br < 15.6 and q == segs - 1 and int(t * 6) % 2) else BLACK)
        mono(c, 36, 668, f'{int(pr * 100):3d}%', 72, WHITE)
        sub = 'ожидание ответа от Никиты…' if 13 <= br < 15.6 else ('осталось: примерно до 2032 года' if br < 20 else 'готово. перезапуск чата')
        mono(c, 36, 822, sub, 22, GOLD if 13 <= br < 15.6 else (180, 180, 190))
        mono(c, 36, 858, '59 177 сообщений · 501 голосовое · 465 дней', 20, (150, 150, 160))
        if 16 <= br < 20.5:
            warn = ['⚠ 19.08.2025: 1 886 сообщений за день', '⚠ голосовых: 180 минут', '⚠ компания мертва: 35 дней']
            for i, wv in enumerate(warn):
                if br >= 16 + i * 1.1 and int(t * 5) % 3 != 0: put(c, pill_im(wv, 30, (150, 10, 20, 235)), W / 2, 380 + i * 72)
    elif s == 'title':
        u = t - a0
        slam(c, t, a0, a1, GT('ТРОПАРЕВО', 128, COL['Егор'], GOLD), W / 2, 470, pop=2.0, shake=14, fi=0.15)
        slam(c, t, a0 + 0.35, a1, GT('8.6', 300, GOLD, (255, 120, 60)), W / 2, 700, pop=2.4, shake=18, fi=0.15)
        if u > 0.9: put(c, T('пилот · патч-ноут чата · 16.07.2025 — 08.11.2026', 22, (220, 220, 230), F_MONO, 3), W / 2, 920, clamp((u - 0.9) / 0.3))
        fl = max(fl, max(0, 1 - u / 0.25) * 0.9)
    elif s in ('people', 'break'):
        for i, p in enumerate(PEOPLE):
            card(c, t, G(p[4]), G(p[5]), i + 1, p[0], p[1], p[2])
        if G(38) <= t < G(39.5): chat_stack(c, t, [(G(38.5), 'Юрий', 'Ураааааа', '13.09.2025', 'L', 40)], bottom=760, top=500)
        if G(36) <= t < G(38): caption(c, t, G(36.6), G(38), ['ушёл из чата после фразы', '«Жаль я тебе чувство такта не могу купить»'], 720, 30, F_SERI, (220, 210, 200))
    elif s == 'prime':
        u = t - a0
        if u < BAR * 1.0:
            slam(c, t, a0, a0 + BAR, GT('ПРАЙМ', 210, COL['Егор'], (255, 160, 60)), W / 2, 520, pop=2.0, shake=12)
            put(c, T('АВГУСТ 2025', 54, WHITE, F_BLACK, 5), W / 2, 700, clamp(u / 0.2))
            fl = max(fl, max(0, 1 - u / 0.2) * 0.8)
        else:
            chip(c, t, a0 + BAR, a1, '19.08.2025 · ночь голосовых · 1 886 сообщений', 112, GOLD)
            chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in PRIME_B], bottom=820, top=160)
            if G(60.0) <= t < G(63.2): slam(c, t, G(60.0), G(63.2), stamp_im('ДР ФРОЛА · 23.08', GOLD, 50), W / 2, 260, pop=2.0, rotd=6)
    elif s == 'otsev':
        caption(c, t, a0, G(66.8), ['после 23.08 —', 'ни одного сбора'], 300, 64, F_SERI, CREAM)
        for i, (bb, tx) in enumerate([(65.4, 'Раед покинул группу'), (65.9, 'Полина покинула группу')]):
            if G(bb) <= t < G(68.5): slam(c, t, G(bb), G(68.5), pill_im(tx, 26, (0, 0, 0, 190)), W / 2, 520 + i * 64, pop=1.3)
        chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in OTSEV_B if G(b_) <= t and (b_ > 69 or t < G(69.3))], bottom=880, top=420)
    elif s == 'tropa':
        if br < 78.3:
            v = next(v for v in VO if v['key'] == 'tropa'); u = t - v['t']
            chip(c, t, a0, G(78.3), '30.03.2026 · теория Егора', 112, COL['Егор'])
            spl = eo((u - 6.9) / 0.4) if u > 6.9 else 0
            pulse = 0
            for w in v['words']:
                if w[2].lower().startswith(('тропа', 'рева', 'рёва')) and w[0] <= u < w[0] + 0.25: pulse = 1 - (u - w[0]) / 0.25
            if spl <= 0:
                put(c, GT('ТРОПАРЁВО', 120, COL['Фрол'], GOLD), W / 2, 460, fade(t, a0, G(78.3), 0.3, 0.3))
            else:
                put(c, scaled(GT('ТРОПА', 150, COL['Фрол'], GOLD), 1 + 0.12 * pulse), W / 2 - 40 * spl, 400 - 30 * spl)
                put(c, scaled(GT('РЁВА', 150, (120, 200, 255), COL['Егор']), 1 + 0.12 * pulse), W / 2 + 40 * spl, 560 + 30 * spl)
                put(c, T('лесопарк, специально предназначенный для рёва', 26, CREAM, F_SERI, 3), W / 2, 720, spl)
            if u < 4: caption(c, t, a0, v['t'] + 4, ['24.04.2026 · Тропарёвский парк', 'большой сбор · возвращение прайма'], 250, 34, F_SERI, CREAM)
        else:
            chip(c, t, G(78.3), a1, 'май 2026 · ДнД · мастер игры — Фрол 🎲', 112, COL['Фрол'])
            chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in DND_B], bottom=780, top=160)
            v = next(v for v in VO if v['key'] == 'pizza2')
            if G(78.6) <= t < v['t'] + v['d'] + 0.3:
                pz = R.emoji_im('🍕', 150); u = t - G(78.6)
                gone = t > v['t'] + 1.0
                im = pz if not gone else cached('pzx', lambda: Image.fromarray((np.array(pz) * np.array([1, 1, 1, 0.35])).astype(np.uint8)))
                put(c, scaled(im, 1 + 0.06 * k), W - 120, 890 - 20 * math.sin(u * 3), 0.95)
                if gone: put(c, R.emoji_im('❌', 120), W - 120, 890, 1.0)
    elif s == 'heart':
        d = ImageDraw.Draw(c); d.rectangle([0, 0, W, 90], fill=BLACK); d.rectangle([0, H - 60, W, H], fill=BLACK)
        caption(c, t, G(85.1), G(90.5), ['июль 2026', 'безработное лето'], 330, 58, F_SERI, CREAM, fi=1.0)
        v = next(v for v in VO if v['key'] == 'tarakany')
        if v['t'] + 4.5 <= t < v['t'] + v['d'] + 0.4:
            u = t - v['t']; a = fade(t, v['t'] + 4.5, v['t'] + v['d'] + 0.4, 0.4, 0.4)
            put(c, T('дом 59 года · жильцов: 2', 34, WHITE, F_SB, 3), W / 2, 560, a)
            if u > 5.9: put(c, R.emoji_im('🪳', 70), W / 2 - 80, 670, a); put(c, R.emoji_im('🪳', 115), W / 2 + 80, 655, a)
            if u > 9.6: put(c, T('поменьше', 26, WHITE, F_SB, 3), W / 2 - 80, 740, a)
            if u > 11.0: put(c, T('побольше', 26, WHITE, F_SB, 3), W / 2 + 80, 740, a)
        chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in HEART_B], bottom=760, top=200)
    elif s == 'zapoy':
        u = t - a0
        if u < BAR: slam(c, t, a0, a0 + BAR, GT('ПАТЧ 8.6.1', 120, GOLD, (255, 110, 60)), W / 2, 330, pop=2.0, shake=12); fl = max(fl, max(0, 1 - u / 0.2) * 0.7)
        if u < BAR: put(c, T('ВАШЕ ЗДОРОВЬЕ 🍻', 50, WHITE, F_BLACK, 5), W / 2, 470, clamp(u / 0.2))
        kk = int((br - 100) / 2); rel = t - G(100 + kk * 2)
        if u >= BAR * 0.6:
            put_circle(c, krug_frame(kk, rel, 400), W / 2, 420, int(400 + 12 * k), clamp((u - BAR * 0.6) / 0.3), ring=COL['Егор'], prog=clamp(rel / (2 * BAR)))
            mono(c, W / 2, 650, 'архив кружков · серия «Алкоголь — зло»', 18, (220, 200, 200), clamp((u - BAR * 0.6) / 0.3), 'c')
        for key, items in [('peak_drink', [('виски', '0,4 виски'), ('водки', '0,3 водки')]), ('filtr', [('вода', 'вода ❌'), ('жидкость', 'жидкость ❌'), ('добавки', 'добавки ❌')]),
                           ('barsa', [('выиграет', 'ПОБЕДА — нахуяюсь'), ('проиграет', 'ПОРАЖЕНИЕ — нахуяюсь'), ('ничья', 'НИЧЬЯ — нахуяюсь')])]:
            v = next(v for v in VO if v['key'] == key); uu = t - v['t']
            if not (0 <= uu < v['d'] + 0.3): continue
            head = {'peak_drink': 'ПРАЙМ-ФОРМА', 'filtr': 'ФИЛЬТР-СИСТЕМА', 'barsa': 'СТАВКА НА БАРСУ'}[key]
            put(c, T(head, 40, GOLD, F_BLACK, 4), W / 2, 692)
            for j, (wk, lab) in enumerate(items):
                tw = next((w[0] for w in v['words'] if w[2].lower().startswith(wk)), None)
                if tw is not None and uu >= tw: slam(c, t, v['t'] + tw, v['t'] + v['d'] + 0.3, pill_im(lab, 28, (0, 0, 0, 200), WHITE), W / 2, 748 + j * 54, pop=1.4)
            if key == 'filtr' and uu > 10.6: slam(c, t, v['t'] + 10.6, v['t'] + v['d'] + 0.3, T('→ 100% АЛКОГОЛЬ', 50, NEON, F_BLACK, 5), W / 2, 906, pop=1.6)
            if key == 'barsa' and uu > 11.4:
                slam(c, t, v['t'] + 11.4, v['t'] + v['d'] + 0.3, T('АААААААААА!!', 96, RED, F_BLACK, 8), W / 2, 560, pop=2.0, shake=26); fl = max(fl, 0.5 * max(0, 1 - (uu - 11.4) / 0.2))
    elif s == 'exits':
        ev = [(120.4, 'Егор Гусев вышел из беседы'), (126.3, 'Егор Гусев вышел из беседы'), (126.75, 'Егор Гусев вернулся в группу')]
        for i, (bb, tx) in enumerate(ev):
            if G(bb) <= t: slam(c, t, G(bb), a1, pill_im(tx, 26, (0, 0, 0, 200), RED if 'вышел' in tx else NEON), W / 2, 200 + i * 62, pop=1.3)
        if t < G(123): chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in EXIT_B], bottom=820, top=300)
        else:
            if t < G(126.2):
                put(c, T('статистика уходов Егора (с) Кирилл', 26, GOLD, F_SB, 3), W / 2, 330, fade(t, G(123), G(126.2), 0.2, 0.2))
                for i, (b_, x, sd) in enumerate(EXIT_K):
                    if G(b_) <= t: slam(c, t, G(b_), G(126.2), bub_im('Кирилл', x['text'], None, 34, 300), 150 + (i % 2) * 240 + 60 * (i // 2 % 2), 420 + (i // 2) * 120, pop=1.4)
    elif s == 'larp':
        chip(c, t, a0, a1, '26.10.2026 · великий спор о ларпе', 112, NEON)
        chat_stack(c, t, [(G(b_), x['who'], x['text'], x['date'], sd) for b_, x, sd in LARP_B], bottom=800, top=170)
        for key, wk, txt, col in [('larp_egor', 'ларп', 'ЛАРП', RED), ('larp_egor', 'лор', 'ЛОР', GOLD), ('trolli', 'база', 'БАЗА', NEON)]:
            v = next(v for v in VO if v['key'] == key); tw = next((w[0] for w in v['words'] if w[2].lower().startswith(wk)), None)
            if tw is not None: slam(c, t, v['t'] + tw, v['t'] + tw + 1.1, stamp_im(txt, col, 70), W / 2 + (120 if txt == 'ЛОР' else -60), 330, pop=2.3, rotd=-7, shake=8)
    elif s == 'storm':
        u = t - a0
        if u < BAR: slam(c, t, a0, a0 + BAR, GT('ШТОРМ', 200, RED, GOLD), W / 2, 520, pop=2.4, shake=20); put(c, T('лучшее за 465 дней', 44, WHITE, F_BLACK, 5), W / 2, 690, clamp(u / 0.2)); fl = max(fl, max(0, 1 - u / 0.25))
        else:
            j0 = int(br - 138)
            for j in (j0 - 1, j0):
                if j < 0: continue
                x = STORM_M[j % len(STORM_M)]; ta = G(138 + j)
                im = cached(('sm', j), lambda: rot(bub_im(x['who'], x['text'], x['date'], 34, 600, True), [-4, 3, -2, 5, -5, 2][j % 6]))
                slam(c, t, ta, ta + BAR * 1.6, im, W / 2 + (-30 if j % 2 else 30), 300 + (j % 2) * 250, pop=1.5, fi=0.1, fo_=0.15)
            chip(c, t, a0 + BAR, a1, f'шторм · {int(clamp((t - a0 - BAR) / (a1 - a0 - BAR)) * 59177):,} / 59 177'.replace(',', ' '), 112, RED)
    elif s == 'credits':
        mono(c, W / 2, 130, 'ТРОПАРЕВО 8.6 · В РОЛЯХ', 24, GOLD, fade(t, a0, a1, 0.4, 0.4), 'c')
        for full, who, role, b0, b1 in CRED:
            t0, t1 = G(b0), G(b1)
            if not (t0 <= t < t1): continue
            a = fade(t, t0, t1, 0.3, 0.3); u = t - t0; col = COL[who]
            nm = fitw(GT(full.upper(), 84 if len(full) < 20 else 52, col, WHITE), W - 50); put(c, nm, W / 2, 430 + 20 * (1 - eo(u / 0.4)), a)
            put(c, fitw(T('в роли: ' + role, 36, CREAM, F_SERI, 3), W - 60), W / 2, 430 + nm.height / 2 + 44, a)
            put(c, fitw(T(CRED_X[who], 30, WHITE, F_SB, 3), W - 60), W / 2, 430 + nm.height / 2 + 104, a * clamp((u - 0.4) / 0.3))
    else:  # final
        u = t - a0
        if u < BAR * 0.6: slam(c, t, a0, a0 + BAR * 0.6 + 0.3, T('[OK] ПАТЧ 8.6 УСТАНОВЛЕН', 40, NEON, F_MONO, 4), W / 2, 600, pop=1.6)
        v = next(v for v in VO if v['key'] == 'final')
        if v['t'] - 0.3 <= t < v['t'] + v['d'] + 0.3:
            put(c, T('📢 ОБЪЯВЛЕНИЕ', 46, GOLD, F_BLACK, 5), W / 2, 380, fade(t, v['t'] - 0.3, v['t'] + v['d'] + 0.3, 0.3, 0.3))
            put(c, T('режим тишины: пт 18:00 — пн 9:00', 28, WHITE, F_SB, 3), W / 2, 450, fade(t, v['t'] - 0.3, v['t'] + v['d'] + 0.3, 0.3, 0.3))
        if t >= G(193.9):
            slam(c, t, G(193.9), T_END, GT('ВЕРСИЯ 9.0', 150, GOLD, COL['Егор']), W / 2, 470, pop=2.0, shake=10)
            put(c, T('COMING SOON', 60, WHITE, F_BLACK, 5), W / 2, 620, clamp((t - G(194.3)) / 0.3))
            put(c, T('серия 1 из 8 · пилот', 28, (200, 200, 210), F_MONO, 3), W / 2, 700, clamp((t - G(194.8)) / 0.3))
        if t >= G(196.4):
            caption(c, t, G(196.4), T_END - 0.2, ['«пора сделать 8 минутный видос»', '(с) Егор, 08.11.2026'], 880, 36, F_SERI, CREAM)
    # voices
    for v in VO:
        if not v['mini'] and v['t'] - 0.1 <= t < v['t'] + v['d'] + 0.3: draw_voice(c, t, v)
    out = np.array(c.convert('RGB'))
    # punch zoom on beats
    amp = {'install': 0.008, 'title': 0.04, 'people': 0.02, 'break': 0.015, 'prime': 0.03, 'otsev': 0.01, 'tropa': 0.02, 'heart': 0.0, 'zapoy': 0.025,
           'exits': 0.0, 'larp': 0.02, 'storm': 0.045, 'credits': 0.012, 'final': 0.015}[s]
    z = 1 + amp * k
    if z > 1.002: M_ = cv2.getRotationMatrix2D((W / 2, H / 2), 0, z); out = cv2.warpAffine(out, M_, (W, H), borderMode=cv2.BORDER_REFLECT)
    if s == 'storm' and k > 0.7:
        out[..., 0] = np.roll(out[..., 0], int(8 * k), 1); out[..., 2] = np.roll(out[..., 2], -int(8 * k), 1)
    if s == 'storm' and int(br) % 4 == 3 and (br % 1) > 0.85:
        rng = np.random.default_rng(fi); o2 = out.copy()
        for _ in range(8):
            y0 = rng.integers(0, H - 60); hh = rng.integers(10, 60); o2[y0:y0 + hh] = np.roll(out[y0:y0 + hh], rng.integers(-70, 70), 1)
        out = o2
    # section-cut flash
    for _, b_ in SECB[1:-1]:
        dt = t - G(b_)
        if 0 <= dt < 0.15: fl = max(fl, 0.55 * (1 - dt / 0.15))
    if fl > 0: out = np.clip(out.astype(np.float32) + 255 * fl, 0, 255).astype(np.uint8)
    if t < TI + 0.25: out = np.clip(out.astype(np.float32) * 0 + 255 * (1 - (t - TI) / 0.25) + out * ((t - TI) / 0.25), 0, 255).astype(np.uint8)
    return out

# ---------------- audio ----------------
def build_audio(outp):
    def load(p):
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', p, '-ac', '2', '-ar', str(SR), '-f', 'f32le', '-'], capture_output=True, check=True).stdout
        return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()
    n = int(T_END * SR) + SR
    intro = load(os.path.join(HERE, 'intro.mp4')); trk = load(os.path.join(SP, 'v14', 'track.mp3'))
    ia = np.zeros((n, 2), np.float32); ia[:len(intro)] = intro[:n]
    tt = np.arange(n) / SR; ia *= np.clip((18.3 - tt) / 0.8, 0, 1)[:, None]
    ta = np.zeros((n, 2), np.float32); i0 = int(TI * SR); ta[i0:i0 + len(trk)] = trk[:n - i0]
    vox = np.zeros(n, np.float32); act = np.zeros(n, np.float32)
    for v in VO:
        i = int(v['t'] * SR); x = v['audio']; j = min(n, i + len(x)); vox[i:j] += x[:j - i] * (1.45 if v['mini'] else 1.3); act[i:j] = 1
    # smooth ducking envelope (attack 60ms, release 350ms) on a decimated grid
    hop = 441; m = n // hop; a_ = act[:m * hop].reshape(m, hop).max(1); env = np.zeros(m, np.float32); e = 0
    for q in range(m):
        tgt = a_[q]; e = e + (tgt - e) * (0.35 if tgt > e else 0.03); env[q] = e
    env = np.repeat(env, hop); env = np.concatenate([env, np.zeros(n - len(env), np.float32)])
    depth = np.full(n, 0.7, np.float32)
    for k_, a, b in [('storm', G(137), G(169)), ('heart', G(85), G(100)), ('exits', G(119), G(127))]:
        ia_, ib_ = int(a * SR), int(b * SR); depth[ia_:ib_] = {'storm': 0.62, 'heart': 0.55, 'exits': 0.55}[k_]
    depth[:int(TI * SR)] = 0.62
    g = 1 - depth * env
    mus = (ia + ta) * g[:, None]
    # sfx
    fx = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    def add(t0, sig, gn=1.0):
        i = int(t0 * SR)
        if i < 0 or i >= n: return
        j = min(n, i + len(sig)); fx[i:j] += gn * sig[:j - i]
    def tv(d): return np.arange(int(d * SR)) / SR
    def whoosh(d=0.5):
        x = rng.standard_normal(len(tv(d))) * np.sin(np.pi * tv(d) / d) ** 2; return (np.convolve(x, np.ones(18) / 18, 'same') * 0.35).astype(np.float32)
    def boom(d=1.4, f0=85):
        t_ = tv(d); f = f0 * np.exp(-t_ * 3.5) + 30; return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t_ * 2.2)).astype(np.float32)
    def pop(f=1200, d=0.07):
        t_ = tv(d); return (np.sin(2 * np.pi * (f + 900 * t_ / d) * t_) * np.exp(-t_ * 60) * 0.25).astype(np.float32)
    def key_():
        t_ = tv(0.03); return (rng.standard_normal(len(t_)) * np.exp(-t_ * 260) * 0.14).astype(np.float32)
    def ding():
        t_ = tv(0.4); return ((np.sin(2 * np.pi * 1760 * t_) + 0.5 * np.sin(2 * np.pi * 2640 * t_)) * np.exp(-t_ * 9) * 0.12).astype(np.float32)
    for _, b_ in SECB[1:-1]: add(G(b_) - 0.45, whoosh(), 0.8)
    add(G(21), boom(), 0.55); add(G(137), boom(1.8, 70), 0.6); add(G(43), boom(1.2, 95), 0.4); add(G(100), boom(1.2, 95), 0.4); add(G(193.9), boom(2.0, 65), 0.5)
    for i in range(len(VERS) + 1):
        for q in range(30): add(G(1.0 + i * 1.3) + q / 60, key_(), 0.8)
    for q in range(60): add(17.2 + q / 90, key_(), 0.7)
    add(18.05, key_(), 2.0)
    for lst in (PRIME_B, OTSEV_B, DND_B, HEART_B, EXIT_B, EXIT_K, LARP_B):
        for b_, x, sd in lst: add(G(b_), pop(), 1.0)
    for j in range(30): add(G(138 + j), pop(1500), 0.8)
    for i in range(8): add(2.92 + i * 0.16, ding(), 0.6)
    for i in range(12): add(14.46 + i * 0.1, ding(), 0.35)
    for b_ in (120.4, 126.3, 126.75, 65.4, 65.9): add(G(b_), ding(), 0.8)
    mix = mus + (vox + fx)[:, None]
    f = int(1.5 * SR); end = int(T_END * SR); mix = mix[:end]; mix[-f:] *= np.linspace(1, 0, f)[:, None]
    mix = np.tanh(mix * 1.05) * 0.96
    st = (mix * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--prep': prep(); build_kick(); sys.exit()
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:06.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--audio': build_audio(sys.argv[2]); sys.exit()
    if sys.argv[1] == '--part':
        out, a, b = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, b): p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
