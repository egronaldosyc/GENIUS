import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, 'v2'), os.path.join(SP, 'v10')): sys.path.insert(0, p)
import render as R
import render2 as R2
import render10 as T
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_BLACKI, F_MONO, F_SYM, WHITE, BLACK
from render2 import hue_rgb
from render10 import P, flash, poster_bg, CREAM, RED, F_SER, cursive, sad

FPS, SR = 30, 44100
GOLD = (255, 220, 90); ACID = (120, 255, 80); PURP = (170, 60, 255)
DIRS = {'a1': (os.path.join(SP, 'v10', 'k1'), 1581), 'a3': (os.path.join(SP, 'v10', 'k3'), 1711), 'a4': (os.path.join(SP, 'v10', 'k4'), 783),
        'b1': (os.path.join(HERE, 'kb1'), 1725), 'b2': (os.path.join(HERE, 'kb2'), 295), 'b3': (os.path.join(HERE, 'kb3'), 841), 'b4': (os.path.join(HERE, 'kb4'), 1122)}
AUF = {'a1': os.path.join(SP, 'v10', 'au1.wav'), 'a3': os.path.join(SP, 'v10', 'au3.wav'), 'a4': os.path.join(SP, 'v10', 'au4.wav'),
       'b1': os.path.join(HERE, 'aub1.wav'), 'b2': os.path.join(HERE, 'aub2.wav'), 'b3': os.path.join(HERE, 'aub3.wav'), 'b4': os.path.join(HERE, 'aub4.wav')}
_c = {}
def kf(v, t):
    d, n = DIRS[v]; i = int(np.clip(round(t * 30), 0, n - 1)); k = (v, i)
    if k not in _c:
        if len(_c) > 250: _c.pop(next(iter(_c)))
        _c[k] = cv2.cvtColor(cv2.imread(os.path.join(d, f'{i+1:04d}.jpg')), cv2.COLOR_BGR2RGB)
    return _c[k]
def kr(v, t, size, ring=CREAM, rw=10, fx=None):
    img = kf(v, t)
    if fx: img = fx(img)
    im = Image.fromarray(img).convert('RGBA'); im.putalpha(Image.fromarray(T.CM)); im = im.resize((size, size), Image.BICUBIC)
    if not ring: return im
    out = Image.new('RGBA', (size + 2 * rw, size + 2 * rw), (0, 0, 0, 0)); ImageDraw.Draw(out).ellipse([0, 0, size + 2 * rw - 1, size + 2 * rw - 1], fill=ring + (255,))
    out.alpha_composite(im, (rw, rw)); return out
def warm(img): return hue_rgb(img, 0, 1.2)

# ---------------- timeline ----------------
SH = []
def s(k, d, **kw): SH.append((k, d, kw))
s('open', 3.0, v='b2', a=0.0)
RUM = [('a1', 4.5, 2.0, 1.0, '«ЗА ЗДОРОВЬЕ»'), ('a1', 24.8, 3.8, 1.0, 'ПОШЛА РОДИМАЯ'), ('a3', 15.5, 3.0, 1.0, 'НАЛИВАЕТ С ДУШОЙ'),
       ('a1', 38.0, 2.5, 1.0, 'ПРЯМО ИЗ ГОРЛА?!'), ('a1', 47.5, 3.3, 1.0, 'УЖЕ НЕ ЧУВСТВУЕТ ВКУСА'), ('a4', 16.0, 2.0, 1.0, 'ЗА МЕЛИССУ'),
       ('b1', 15.8, 2.0, 1.0, 'ЗА КСЮШУ'), ('b1', 33.0, 2.8, 1.0, 'ЕЩЁ ОДНУ И ВСЁ'), ('b1', 35.8, 4.2, 0.67, 'ДЕВЯТАЯ.')]
SCH = [None, ('b1', 0.0, 3.0, 'ЕГОР ОСОЗНАЁТ', 'что-то пошло не так'), None, ('b1', 10.0, 3.0, 'ГРАВИТАЦИЯ', 'включилась без предупреждения'),
       ('b3', 0.0, 5.0, 'СИСТЕМА ОХЛАЖДЕНИЯ', 'процессор перегрелся'), ('b4', 0.5, 5.0, 'ПОРТАЛ В ЗИМУ', 'Егор ищет выход'),
       ('b4', 25.0, 4.0, 'ВРЕМЯ ОСТАНОВИЛОСЬ', '22:51. уже третий час'), ('b1', 48.8, 3.5, 'ПРЯЧЕТСЯ', 'вдруг Мелисса увидит'), None]
for i, (v, a, d, sp, cap) in enumerate(RUM):
    s('rum', d, n=i + 1, v=v, a=a, sp=sp, cap=cap)
    if SCH[i]: s('sch', SCH[i][2], lvl=i + 1, v=SCH[i][0], a=SCH[i][1], cap=SCH[i][3], sub=SCH[i][4])
s('score', 4.5)
s('end', 4.0)
STARTS = []; _t = 0
for x in SH: STARTS.append(_t); _t += x[1]
T_END = _t; N = int(round(T_END * FPS))
def at(t):
    for i, x in enumerate(SH):
        if t < STARTS[i] + x[1]: return i, t - STARTS[i]
    return len(SH) - 1, SH[-1][1] - 1e-3
def count_at(t):
    n = 0
    for i, x in enumerate(SH):
        if x[0] == 'rum' and STARTS[i] <= t: n = x[2]['n']
    return n

# ---------------- HUD ----------------
def glass_icon(full, size=54):
    im = Image.new('RGBA', (size, size), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    pts = [(size * 0.18, size * 0.1), (size * 0.82, size * 0.1), (size * 0.68, size * 0.9), (size * 0.32, size * 0.9)]
    if full: d.polygon([(size * 0.22, size * 0.32), (size * 0.78, size * 0.32), (size * 0.68, size * 0.9), (size * 0.32, size * 0.9)], fill=(255, 200, 60, 255))
    d.line(pts + [pts[0]], fill=(255, 255, 255, 255), width=4)
    return im
GL = [glass_icon(False), glass_icon(True)]
def hud(c, t):
    n = count_at(t); d = ImageDraw.Draw(c)
    d.rounded_rectangle([18, 48, W - 18, 128], 18, fill=(0, 0, 0, 170))
    for j in range(9):
        g = GL[1 if j < n else 0]; x = 50 + j * 70
        sc = 1.0
        for i, xx in enumerate(SH):
            if xx[0] == 'rum' and xx[2]['n'] == j + 1: sc = 1 + 0.6 * math.exp(-max(0, t - STARTS[i]) / 0.12) if t >= STARTS[i] else 1.0
        paste(c, g, x + 20, 88, sc)
    prom = 0.35 * n + 0.05 * math.sin(t * 3) * (n > 0)
    d.rounded_rectangle([18, 140, 300, 190], 12, fill=(0, 0, 0, 170))
    d.text((34, 165), f'ПРОМИЛЛЕ: {max(0, prom):.2f}‰', font=font(F_MONO, 24), fill=GOLD, anchor='lm')
    sh = min(1, n / 9 + 0.03)
    d.rounded_rectangle([320, 140, W - 18, 190], 12, fill=(0, 0, 0, 170))
    d.rounded_rectangle([326, 146, 326 + (W - 18 - 332) * sh, 184], 9, fill=PURP)
    d.text((340, 165), f'ШИЗА {int(sh*100)}%', font=font(F_MONO, 24), fill=WHITE, anchor='lm', stroke_width=2, stroke_fill=BLACK)

def acid_bg(t, lvl):
    c = R2.rays(t, [(40 + lvl * 10, 0, 70 + lvl * 8), (0, 30 + lvl * 8, 20)], 10 + lvl * 2, 40 + lvl * 15)
    a = np.array(c.convert('RGB')); a = hue_rgb(a, t * 60 * lvl, 1.4); return P(a)

def slam(c, txt, size, y, tl, t0, col=CREAM, stroke=BLACK, rot=-4):
    s = ease_pop(tl, t0, 0.1)
    if s <= 0: return
    paste(c, text_img(txt, size, col, stroke, max(6, size // 10), spacing=-8), W / 2, y, s * (1 + 0.35 * math.exp(-(tl - t0) / 0.07)), rot)

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; i, tl = at(t); k, dur, kw = SH[i]; rng = random.Random(fi * 23); c = None
    if k == 'open':
        c = poster_bg(t)
        paste(c, kr('b2', kw['a'] + tl, 560, CREAM, 10, warm), W / 2, 720, ease_pop(tl, 0.0, 0.2))
        slam(c, 'АЛКОГОЛЬ — ЗЛО', 76, 300, tl, 0.0, CREAM)
        slam(c, 'ЧАСТЬ 2', 90, 410, tl, 0.3, GOLD)
        if tl > 1.0: slam(c, 'СКОЛЬКО РЮМОК\nВЫПЬЕТ ЕГОР?', 66, 1120, tl, 1.0, CREAM, BLACK, 0)
    elif k == 'rum':
        n = kw['n']; st = kw['a'] + tl * kw['sp']
        hue = n * 8
        c = poster_bg(t, (min(255, 140 + n * 12), 15, 20), (60, 0, 0))
        if n >= 5:
            a = np.array(c.convert('RGB')); c = P(hue_rgb(a, (t * 40 * (n - 4)) % 360, 1.2))
        wob = (n - 1) * 3.5
        x = W / 2 + wob * math.sin(t * (2 + n * 0.4)); rot = wob * 0.5 * math.sin(t * 1.7)
        img = kr(kw['v'], st, 600, CREAM, 10, warm)
        if n >= 4:  # double vision grows
            gh = kr(kw['v'], st - 0.12, 600, None, 0, warm); arr = np.array(gh); arr[..., 3] = (arr[..., 3] * min(0.5, 0.1 * (n - 3))).astype(np.uint8)
            paste(c, Image.fromarray(arr), x + 10 * (n - 3), 720, 1.0, rot + 3)
        paste(c, img, x, 720, 1.0 + 0.02 * n, rot)
        slam(c, f'№{n}', 220, 390, tl, 0.0, GOLD, BLACK, -8)
        if tl > 0.45: slam(c, kw['cap'], 66 if len(kw['cap']) < 15 else 52, 1110, tl, 0.45, CREAM, BLACK, -2)
        if tl < 0.05: flash(c, 0.7)
        if n == 9 and tl > 1.0:
            a = np.array(c.convert('RGB')); a = R3_shake(a, rng, 6); c = P(a)
        hud(c, t)
    elif k == 'sch':
        lvl = kw['lvl']
        c = acid_bg(t, lvl)
        st = kw['a'] + tl
        if kw['v'] == 'b4' and kw['a'] < 5 and tl > 2.8: st = 13.5 + (tl - 2.8)
        fx = (lambda im: hue_rgb(im, (t * 90) % 360, 1.6)) if lvl >= 5 else warm
        img = kr(kw['v'], st, 640, ACID, 10, fx)
        x = W / 2 + 12 * math.sin(t * 9) * (lvl / 8); rot = 6 * math.sin(t * 3)
        paste(c, img, x, 700, 1.0 + 0.03 * math.sin(t * 7), rot)
        d = ImageDraw.Draw(c)
        stamp = text_img(f'⚠ ШИЗА: УРОВЕНЬ {min(9, lvl)}', 40, BLACK, ACID, 0, f=F_SYM)
        bg = Image.new('RGBA', (stamp.width + 24, stamp.height + 10), ACID + (255,)); bg.alpha_composite(stamp, (12, 5))
        paste(c, bg, W / 2, 330, ease_pop(tl, 0.05, 0.12), -3)
        slam(c, kw['cap'], 70 if len(kw['cap']) < 14 else 56, 1090, tl, 0.3, WHITE, (90, 0, 140), -3)
        if tl > 0.9: paste(c, text_img(kw['sub'], 38, ACID, BLACK, 4), W / 2, 1180, ease_pop(tl, 0.9, 0.12))
        if kw['cap'] == 'СИСТЕМА ОХЛАЖДЕНИЯ':
            temp = max(36.6, 98 - tl * 18)
            d.rounded_rectangle([W - 260, 400, W - 30, 470], 12, fill=(0, 0, 0, 200))
            d.text((W - 145, 435), f'ЦП: {temp:.1f}°C', font=font(F_MONO, 32), fill=(255, 80, 80) if temp > 60 else ACID, anchor='mm')
        if kw['cap'] == 'ПОРТАЛ В ЗИМУ' and tl > 2.8:
            d.rounded_rectangle([W - 230, 400, W - 30, 470], 12, fill=(0, 0, 0, 200)); d.text((W - 130, 435), '−18°C', font=font(F_MONO, 36), fill=(140, 220, 255), anchor='mm')
        if rng.random() < 0.12:
            a = np.array(c.convert('RGB')); a = glitch_slices(a, rng, 6, 80); c = P(a)
        if tl < 0.05: flash(c, 0.5, ACID)
        hud(c, t)
    elif k == 'score':
        c = poster_bg(t, (170, 20, 25), (70, 0, 0))
        slam(c, 'ИТОГО:', 80, 300, tl, 0.0, CREAM)
        cell = 190
        for j, (v, a, d_, sp, cap) in enumerate(RUM):
            t0 = 0.2 + j * 0.16
            if tl < t0: continue
            gx, gy = j % 3, j // 3
            th = kr(v, a + d_ * sp * 0.5, cell - 20, CREAM, 5, warm)
            x = W / 2 + (gx - 1) * (cell + 10); y = 560 + gy * (cell + 10)
            paste(c, th, x, y, ease_pop(tl, t0, 0.12))
            paste(c, text_img(str(j + 1), 52, GOLD, BLACK, 6), x - 62, y - 62, ease_pop(tl, t0, 0.12))
        if tl > 1.9: slam(c, '9 РЮМОК', 120, 1150, tl, 1.9, GOLD, BLACK, -4)
        if tl > 2.8: paste(c, text_img('Мелисса и Ксюша всё ещё не ответили', 32, WHITE, BLACK, 4, f=F_SER), W / 2, 1240, ease_pop(tl, 2.8, 0.12))
        hud(c, t)
    elif k == 'end':
        c = acid_bg(t, 9)
        paste(c, kr('b1', 55.0 + tl * 0.6, 420, ACID, 8, warm), W / 2, 740)
        slam(c, 'АЛКОГОЛЬ — ЗЛО', 82, 330, tl, 0.0, CREAM, BLACK)
        slam(c, 'А ШИЗА — НАВСЕГДА', 64, 440, tl, 0.6, ACID, (60, 0, 90))
        if tl > 1.6: paste(c, text_img('берегите себя', 50, WHITE, BLACK, 5, f=F_SER), W / 2, 1060, ease_pop(tl, 1.6, 0.15))
        d = ImageDraw.Draw(c); d.text((W / 2, H - 40), 'ЧРЕЗМЕРНОЕ УПОТРЕБЛЕНИЕ АЛКОГОЛЯ ВРЕДИТ ВАШЕМУ ЗДОРОВЬЮ', font=font(F_MONO, 16), fill=WHITE, anchor='mm', stroke_width=2, stroke_fill=BLACK)
        if dur - tl < 0.35: flash(c, (0.35 - (dur - tl)) / 0.35, (0, 0, 0))
    return np.array(c.convert('RGB'))
def R3_shake(a, rng, amp):
    M = np.float32([[1, 0, rng.uniform(-amp, amp)], [0, 1, rng.uniform(-amp, amp)]]); return cv2.warpAffine(a, M, (W, H), borderMode=cv2.BORDER_REFLECT)

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(9)
    AU = {k: T.load(p) for k, p in AUF.items()}
    VO = {f'r{i}': T.load(os.path.join(HERE, 'vo', f'r{i}.wav')) for i in range(1, 10)}
    for k in ('q', 'tot', 'end'): VO[k] = T.load(os.path.join(HERE, 'vo', f'{k}.wav'))
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(v, s0, d, sp=1.0, fade=0.02, target=0.12):
        a = AU[v]; m = int(d * SR); pos = s0 * SR + np.arange(m) * sp
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        r = np.sqrt((x ** 2).mean()) + 1e-6; return x * min(5.0, target / r)
    def tt(d): return np.arange(int(d * SR)) / SR
    def boom(d=1.0, f0=110):
        t = tt(d); f = f0 * np.exp(-t * 4) + 36; return np.tanh(2.6 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.6)).astype(np.float32)
    def clink():
        t = tt(0.7); return (sum(np.sin(2 * np.pi * f * t) * np.exp(-t * dd) for f, dd in ((2637, 6), (3520, 8), (4186, 10), (5274, 12))) * 0.13).astype(np.float32)
    def gulp():
        t = tt(0.16); f = 250 + 500 * t / 0.16; return (0.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t / 0.16)).astype(np.float32)
    def theremin(d, base=440):
        t = tt(d); f = base * (1 + 0.25 * np.sin(2 * np.pi * 0.7 * t)) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR); env = np.minimum(1, t / 0.2) * np.clip((d - t) / 0.2, 0, 1); return (x * env * 0.12).astype(np.float32)
    def horn(d=0.8):
        t = tt(d); x = sum(((2 * np.pi * np.cumsum(np.full(len(t), 233 * m)) / SR) % (2 * np.pi)) / np.pi - 1 for m in (1, 1.26, 1.5))
        env = np.minimum(1, t / 0.02) * np.clip((d - t) / 0.08, 0, 1); return np.tanh(1.4 * x * env * 0.3).astype(np.float32)
    # accelerating beat across the film: bpm 96 -> 168
    t = tt(T_END); bpm = 96 + 72 * (t / T_END) ** 1.3; ph = np.cumsum(bpm / 60 / SR); beat_idx = np.floor(ph).astype(int)
    starts = np.flatnonzero(np.diff(beat_idx) > 0) + 1
    kick = boom(0.35, 150); hat_t = tt(0.04); hat = (np.diff(np.concatenate([[0], rng.standard_normal(len(hat_t))])) * np.exp(-hat_t * 90) * 0.35).astype(np.float32)
    snare_t = tt(0.18); snare = (rng.standard_normal(len(snare_t)) * np.exp(-snare_t * 18) * 0.5).astype(np.float32)
    for q, s0 in enumerate(starts):
        tt0 = s0 / SR
        if tt0 > T_END - 4.2: break
        add(tt0, kick, 0.55)
        if q % 2 == 1: add(tt0, snare, 0.35)
        add(tt0 + (60 / bpm[s0]) / 2, hat, 0.6)
    for i, (k, d, kw) in enumerate(SH):
        s0 = STARTS[i]
        if k == 'open':
            add(s0, clip(kw['v'], kw['a'], d), 1.0); add(s0, boom(1.2, 80), 0.8); add(s0 + 1.0, VO['q'], 1.0); add(s0, horn(), 0.4)
        elif k == 'rum':
            add(s0, clink(), 1.0); add(s0, boom(0.7, 130), 0.7); add(s0 + 0.05, VO[f"r{kw['n']}"], 1.2)
            add(s0 + 0.3, clip(kw['v'], kw['a'] + 0.3 * kw['sp'], d - 0.3, kw['sp']), 0.8); add(s0 + d * 0.6, gulp(), 0.6)
            if kw['n'] == 9: add(s0, horn(1.4), 0.6)
        elif k == 'sch':
            st = kw['a']; x = clip(kw['v'], st, d, 1.0)
            if kw['v'] == 'b4' and kw['a'] < 5: x = np.concatenate([clip('b4', st, 2.8), clip('b4', 13.5, d - 2.8)])
            pitched = np.interp(np.arange(0, len(x), 0.85), np.arange(len(x)), x).astype(np.float32)[:len(x)]
            add(s0, pitched, 0.8); add(s0, theremin(d, 330 + kw['lvl'] * 30), 1.0)
        elif k == 'score':
            for j in range(9): add(s0 + 0.2 + j * 0.16, clink()[:8000], 0.5)
            add(s0 + 1.9, boom(1.0, 90), 0.9); add(s0 + 1.95, VO['tot'], 1.1)
        elif k == 'end':
            add(s0, boom(1.2, 70), 0.8); add(s0 + 0.1, VO['end'], 1.0); add(s0, theremin(3.6, 300), 0.8)
    mix = mix[:int(T_END * SR)]; f = int(0.35 * SR); mix[-f:] *= np.linspace(1, 0, f)
    mix = np.tanh(mix * 1.1) * 0.93
    stt = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(stt.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for i, x in enumerate(SH): print(f'{i:2d} {x[0]:6s} {STARTS[i]:6.2f} {x[1]}')
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
