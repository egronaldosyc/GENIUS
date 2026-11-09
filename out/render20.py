# Покадровая переделка брейнрот-видоса на лор чата «Тропарево 8.6». Звук и тайминги оригинала не трогаем.
import os, sys, math, subprocess
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__)); SP = os.path.dirname(HERE)
sys.path[:0] = [os.path.join(SP, 'v17'), SP, os.path.join(SP, 'v13')]
from render13 import font, F_BLACK, F_BLACKI, F_BO, F_SB, F_MED, F_MONO, emoji_im, draw_rich, tokens
import render13 as R
from chars import puppet
U = '/root/.claude/uploads/26d127ed-d183-5535-9bf5-4686595d072f'
W, H, FPS = 720, 1280, 30
NF = 987
CL = {'egor0': '00666666-2986665846649675834', 'egor7': '43a1429f-8520356627320732753', 'egor22': 'ece686d9-2495122446782613016',
      'en1': '07d1802f-5170510698267840096', 'en21': 'd7a3851f-7308952817924020468', 'park18': 'caad1028-1929649060654770546',
      'park24': 'fac7bbfa-1929935253879752777', 'store': '78848c3e-IMG_2036'}
CIRC = {'egor0', 'egor7', 'egor22'}
_g = {}
def grab(key, t0, n):
    k = (key, t0, n)
    if k in _g: return _g[k]
    ext = '.MP4' if key == 'store' else '.mp4'
    sw, sh = (400, 400) if key in CIRC else (None, None)
    vf = 'fps=30'
    if key in CIRC: vf += ',crop=196:348:102:26,scale=720:1280:flags=lanczos'
    else: vf += ',scale=720:1280:force_original_aspect_ratio=increase:flags=lanczos,crop=720:1280'
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t0), '-i', os.path.join(U, CL[key] + ext), '-frames:v', str(n), '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    a = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
    if len(a) < n: a = np.concatenate([a, np.repeat(a[-1:], n - len(a), 0)])
    if key in CIRC: a = np.stack([cv2.addWeighted(x, 1.6, cv2.GaussianBlur(x, (0, 0), 3), -0.6, 0) for x in a])
    _g[k] = a; return a
def clipf(key, t0, f0, f): return grab(key, t0, 140)[min(139, f - f0)].copy()

# ---------- text helpers ----------
def cap_word(img, word, y=640, col=(255, 230, 40), size=96):
    """slip-n-slide style caption: bold italic yellow/white with thick black stroke"""
    c = Image.fromarray(img).convert('RGBA'); d = ImageDraw.Draw(c); fo = font(F_BLACKI, size)
    while fo.getlength(word) > W - 40: size -= 6; fo = font(F_BLACKI, size)
    x = (W - fo.getlength(word)) / 2
    d.text((x + 5, y + 6), word, font=fo, fill=(0, 0, 0, 160)); d.text((x, y), word, font=fo, fill=col, stroke_width=9, stroke_fill=(0, 0, 0))
    return np.array(c.convert('RGB'))
def tiktok_box(img, txt, y=300, size=40):
    c = Image.fromarray(img).convert('RGBA'); d = ImageDraw.Draw(c); fo = font(F_MED, size)
    lines = R.layout(txt, fo, W - 160); lh = int(size * 1.25); bw = int(max(fo.getlength(l) for l in lines)) + 40
    x0 = (W - bw) / 2; d.rounded_rectangle([x0, y, x0 + bw, y + lh * len(lines) + 24], 10, fill=(255, 255, 255))
    for j, l in enumerate(lines): d.text(((W - fo.getlength(l)) / 2, y + 12 + j * lh), l, font=fo, fill=(10, 10, 10))
    d.text((24, 30), '♪ TikTok', font=font(F_BO, 30), fill=(255, 255, 255), stroke_width=3, stroke_fill=(0, 0, 0)); d.text((24, 66), '@tropar_8.6', font=font(F_SB, 22), fill=(230, 230, 230))
    return np.array(c.convert('RGB'))
def small_caption(img, txt, y=1060, size=38):
    c = Image.fromarray(img).convert('RGBA'); d = ImageDraw.Draw(c); fo = font(F_BO, size)
    x = (W - sum(fo.getlength(v) if k == 't' else size * 1.12 for k, v in tokens(txt))) / 2
    sh = Image.new('RGBA', c.size, (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    for dx in (-3, 0, 3):
        for dy in (-3, 0, 3): draw_rich(sh, (x + dx, y + dy), txt, fo, (0, 0, 0, 255))
    c.alpha_composite(sh); draw_rich(c, (x, y), txt, fo, (255, 255, 255))
    return np.array(c.convert('RGB'))
def zoom(img, z, cx=0.5, cy=0.5):
    M = cv2.getRotationMatrix2D((W * cx, H * cy), 0, z); return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)
def solid(col): return np.full((H, W, 3), col, np.uint8)
def put_im(img, im, x, y, anchor='c'):
    c = Image.fromarray(img).convert('RGBA')
    if anchor == 'c': x -= im.width / 2; y -= im.height / 2
    c.alpha_composite(im, (int(x), int(y))) if x >= 0 and y >= 0 else c.paste(im, (int(x), int(y)), im)
    return np.array(c.convert('RGB'))
CASC = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
_face = {}
MANUAL = {'teacher': (80, 380, 620, 800), 'bateman': (46, 470, 588, 640)}
def face(img, key):
    if key in MANUAL: return MANUAL[key]
    if key in _face: return _face[key]
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY); fs = CASC.detectMultiScale(g, 1.15, 5, minSize=(160, 160))
    r = max(fs, key=lambda b: b[2] * b[3]) if len(fs) else (180, 380, 360, 360); _face[key] = tuple(int(v) for v in r); return _face[key]

# ---------- drawn assets ----------
def badge(f):
    def body():
        im = Image.new('RGBA', (640, 640), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.ellipse([20, 40, 620, 640], fill=(110, 60, 30)); d.ellipse([30, 30, 610, 610], fill=(255, 240, 200), outline=(90, 50, 20), width=14)
        d.ellipse([70, 70, 570, 570], fill=(70, 150, 230))
        return im
    im = body(); pose = ['wave', 'hype', 'drink', 'wave'][(f // 3) % 4]
    p = puppet('Егор', f / 30, pose, talk=True); im.alpha_composite(p.resize((400, 500)), (120, 110))
    for e, (x, y, s) in zip(['🥃', '🍕', '🍾', '🍺'], [(90, 330, 110), (470, 330, 120), (130, 470, 100), (440, 470, 100)]):
        im.alpha_composite(emoji_im(e, s), (x, y))
    d = ImageDraw.Draw(im)
    for txt, y, size, col in [('Егор', 30, 120, (40, 120, 240)), ('does шоты', 150, 70, (255, 200, 40))]:
        fo = font(F_BLACKI, size); x = (640 - fo.getlength(txt)) / 2
        d.text((x, y), txt, font=fo, fill=col, stroke_width=12, stroke_fill=(30, 20, 60)); d.text((x, y), txt, font=fo, fill=col)
    bg = solid((250, 250, 250)); return put_im(bg, im, W / 2, H / 2 + 20)
def moai_pizza():
    im = emoji_im('🍕', 420).copy(); d = ImageDraw.Draw(im); w, h = im.size
    d.rectangle([w * 0.32, h * 0.36, w * 0.46, h * 0.42], fill=(20, 20, 20)); d.rectangle([w * 0.54, h * 0.36, w * 0.68, h * 0.42], fill=(20, 20, 20))
    d.rectangle([w * 0.42, h * 0.6, w * 0.6, h * 0.64], fill=(20, 20, 20)); d.polygon([(w * 0.5, h * 0.38), (w * 0.44, h * 0.55), (w * 0.56, h * 0.55)], fill=(150, 60, 30))
    return im
def evil_bottle(f):
    bg = np.zeros((H, W, 3), np.float32); yy, xx = np.mgrid[0:H, 0:W]
    bg[:] = (np.array([255, 190, 40]) * (0.6 + 0.4 * np.sin(xx / 40 + f * 0.3)[..., None] * np.cos(yy / 50)[..., None])).clip(0, 255)
    c = Image.fromarray(bg.astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(c)
    cx, cy = 360, 650 + 6 * math.sin(f * 0.8)
    d.rounded_rectangle([cx - 130, cy - 200, cx + 130, cy + 260], 60, fill=(40, 120, 60), outline=(10, 30, 10), width=10)
    d.rectangle([cx - 40, cy - 330, cx + 40, cy - 190], fill=(40, 120, 60), outline=(10, 30, 10), width=10); d.rectangle([cx - 46, cy - 360, cx + 46, cy - 320], fill=(200, 30, 30))
    d.rectangle([cx - 110, cy - 60, cx + 110, cy + 120], fill=(245, 240, 220)); d.text((cx - 95, cy - 10), 'ЧЕКУШКА', font=font(F_BLACK, 40), fill=(180, 20, 20))
    for sx in (-1, 1):
        d.polygon([(cx + sx * 30, cy - 150), (cx + sx * 110, cy - 180), (cx + sx * 100, cy - 110)], fill=(255, 255, 255)); d.ellipse([cx + sx * 75 - 14, cy - 160, cx + sx * 75 + 14, cy - 132], fill=(200, 0, 0))
    d.chord([cx - 120, cy - 40, cx + 120, cy + 120], 0, 180, fill=(20, 0, 0));
    for k in range(9): d.rectangle([cx - 110 + k * 26, cy + 40, cx - 92 + k * 26, cy + 70], fill=(255, 255, 230))
    return np.array(c.convert('RGB'))
def chekushka(f):
    c = Image.new('RGBA', (W, H), (252, 252, 252, 255)); d = ImageDraw.Draw(c); j = 2 * math.sin(f * 1.7)
    cx, cy = 360 + j, 640
    sh = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(sh).ellipse([cx - 150, cy + 250, cx + 170, cy + 300], fill=(0, 0, 0, 60)); c.alpha_composite(sh.filter(ImageFilter.GaussianBlur(14)))
    d.rounded_rectangle([cx - 110, cy - 120, cx + 110, cy + 270], 50, fill=(230, 240, 245), outline=(140, 160, 170), width=6)
    d.rectangle([cx - 35, cy - 260, cx + 35, cy - 110], fill=(230, 240, 245), outline=(140, 160, 170), width=6); d.rectangle([cx - 40, cy - 290, cx + 40, cy - 250], fill=(200, 30, 30))
    d.rectangle([cx - 100, cy + 10, cx + 100, cy + 170], fill=(250, 250, 240), outline=(200, 30, 30), width=4); d.text((cx - 70, cy + 40), 'ВОДКА', font=font(F_BLACK, 44), fill=(200, 30, 30)); d.text((cx - 50, cy + 100), '0,25 л', font=font(F_BO, 30), fill=(60, 60, 60))
    d.line([cx - 70, cy - 100, cx - 70, cy + 240], fill=(255, 255, 255), width=10)
    return np.array(c.convert('RGB'))
def circle_letter(ch, bgc, fgc, circle=True, size=330):
    c = Image.new('RGBA', (W, H), (0, 0, 0, 255) if circle else bgc + (255,)); d = ImageDraw.Draw(c)
    if circle: d.ellipse([110, 390, 610, 890], fill=bgc)
    fo = font(F_MED, size); d.text(((W - fo.getlength(ch)) / 2, 640 - size * 0.62), ch, font=fo, fill=fgc)
    return np.array(c.convert('RGB'))
def outro(f):
    c = Image.new('RGBA', (W, H), (40, 10, 24, 255)); d = ImageDraw.Draw(c); fo = font(F_MED, 260)
    d.text(((W - fo.getlength('8.6')) / 2, 470), '8.6', font=fo, fill=(90, 50, 70))
    # telegram-ish plane icon
    cx, cy = 360, 620; d.ellipse([cx - 60, cy - 60, cx + 60, cy + 60], fill=(40, 160, 230)); d.polygon([(cx - 34, cy + 2), (cx + 38, cy - 30), (cx + 16, cy + 36), (cx + 2, cy + 10)], fill=(255, 255, 255))
    t = 'ТРОПАРЕВО 8.6'; fo2 = font(F_BO, 34); d.text(((W - fo2.getlength(t)) / 2, 700), t, font=fo2, fill=(240, 220, 230))
    return np.array(c.convert('RGB'))
def gta(i):
    p = os.path.join(SP, 'v13', 'sh', f'{i:03d}.jpg'); im = cv2.cvtColor(cv2.imread(p), cv2.COLOR_BGR2RGB)
    h, w = im.shape[:2]; cw = int(h * W / H); x0 = (w - cw) // 2; return cv2.resize(im[:, x0:x0 + cw], (W, H))
def glitch(img, f, amt=1.0):
    rng = np.random.default_rng(f); out = img.copy()
    for _ in range(int(14 * amt)):
        y0 = rng.integers(0, H - 80); hh = rng.integers(10, 90); out[y0:y0 + hh] = np.roll(img[y0:y0 + hh], rng.integers(-120, 120), 1)
    out[..., 0] = np.roll(out[..., 0], 10, 1); out[..., 2] = np.roll(out[..., 2], -10, 1); return out
def collage(f):
    rng = np.random.default_rng(f // 2); base = solid((240, 220, 240)).copy()
    for k in range(7):
        src = gta(int(rng.integers(0, 137))); s = rng.uniform(0.35, 0.6); im = cv2.resize(src, (int(W * s), int(H * s)))
        x, y = int(rng.uniform(-100, W - 100)), int(rng.uniform(-100, H - 200)); x0, y0 = max(0, x), max(0, y); x1, y1 = min(W, x + im.shape[1]), min(H, y + im.shape[0])
        base[y0:y1, x0:x1] = im[y0 - y:y1 - y, x0 - x:x1 - x]
    tint = np.array([255, 120, 220], np.float32); base = (base * 0.6 + tint * 0.4).astype(np.uint8)
    return glitch(base, f, 1.5)

WORDS = [(0.08, 'ВОТ'), (0.32, '4'), (0.42, 'СПОСОБА'), (0.62, 'ВЫЙТИ'), (0.78, 'ИЗ'), (0.95, 'БЕСЕДЫ'), (1.12, 'ТРОПАРЕВО'), (1.4, '8.6'), (1.62, 'И'),
         (1.82, 'ВЕРНУТЬСЯ'), (2.0, 'ЧЕРЕЗ'), (2.22, 'ДЕНЬ'), (2.5, 'НОМЕР'), (2.72, 'ОДИН')]
def render(f):  # f = 1..987
    t = (f - 1) / 30
    if f <= 4:
        img = clipf('en1', 36.0, 1, f); x, y, w, h = face(img, 'hulk')
        g = img.astype(np.float32); g[..., 1] *= 1.25; g[..., 0] *= 0.55; g[..., 2] *= 0.45
        c = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(c)
        d.chord([x - 10, y - h * 0.3, x + w + 10, y + h * 0.7], 180, 360, fill=(120, 40, 170)); d.rounded_rectangle([x + w * 0.88, y + h * 0.15, x + w * 1.05, y + h * 0.95], 20, fill=(120, 40, 170))
        return np.array(c.convert('RGB'))
    if f <= 105:
        img = clipf('park24', 24.0, 5, f)
        word = None
        for ts, w_ in WORDS:
            if t >= ts: word = w_
        last = [ts for ts, _ in WORDS if ts <= t]
        if word and (t - last[-1]) < (0.55 if word != 'ОДИН' else 0.7) and not (2.3 < t < 2.5):
            img = cap_word(img, word, 640, (255, 230, 40) if word in ('4', '8.6', 'ТРОПАРЕВО', 'НОМЕР') else (255, 255, 255))
        if 3.18 <= t < 3.45: img = cap_word(img, 'НЕ УХОДИ', 260, (255, 230, 40), 90)
        return img
    if f <= 121: return clipf('park18', 30.4, 106, f)
    if f <= 137:
        img = clipf('egor22', 12.0, 122, f); img = cv2.GaussianBlur(img, (0, 0), 6)
        r = emoji_im('🪳', 430); im = r.rotate(10 * math.sin(f), expand=True)
        return put_im(img, im, 360 + 20 * math.sin(f * 1.3), 640)
    if f <= 156:
        img = clipf('park18', 60.0, 138, f).astype(np.float32)
        if f <= 144:
            yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt((xx - 360) ** 2 + (yy - 700) ** 2) / 600
            boom = np.clip(1.4 - r, 0, 1)[..., None] * np.array([255, 200, 90]); img = np.clip(img * 0.4 + boom * 1.6, 0, 255)
        else:
            img = zoom(img.astype(np.uint8), 1.4 + 0.08 * (f - 145)).astype(np.float32); img = cv2.GaussianBlur(img, (0, 0), 14)
        return img.astype(np.uint8)
    if f <= 182: return badge(f)
    if f <= 215: return clipf('en21', 88.5, 183, f)
    if f <= 222: return zoom(clipf('en21', 36.0, 216, f), 1.15)
    if f <= 237: return clipf('egor0', 2.0, 223, f)
    if f <= 253: return clipf('en21', 200.0, 238, f) if False else clipf('en1', 36.0, 238, f)
    if f <= 271: return clipf('egor7', 0.2, 254, f)
    if f <= 273: return gta(60)
    if f <= 280:
        bg = solid((235, 230, 225)); return put_im(bg, moai_pizza(), 360, 640)
    if f <= 314: return clipf('store', 9.3, 281, f)
    if f <= 333: return small_caption(gta(85), 'зачем я придумал версии чата 😭', 1040)
    if f <= 357:
        bg = np.zeros((H, W, 3), np.uint8); bg[:] = (10, 25, 12); bg[380:900] = (20, 70, 30)
        im = emoji_im('🗿', 420); y = 640 + 30 * math.sin(f * 0.9)
        out = put_im(bg, im, 360, y); c = Image.fromarray(out); d = ImageDraw.Draw(c)
        for sx in (-1, 1): d.ellipse([360 + sx * 80 - 50, y - 120, 360 + sx * 80 + 50, y - 20], fill=(255, 255, 255), outline=(0, 0, 0), width=5); d.ellipse([360 + sx * 80 - 18 + 10 * math.sin(f), y - 88, 360 + sx * 80 + 18 + 10 * math.sin(f), y - 52], fill=(0, 0, 0))
        return np.array(c)
    if f <= 404:
        img = clipf('egor0', 4.0, 358, f); x, y, w, h = face(img, 'teacher')
        c = Image.fromarray(img).convert('RGBA'); d = ImageDraw.Draw(c)
        d.chord([x - w * 0.1, y - h * 0.35, x + w * 1.1, y + h * 0.5], 180, 360, fill=(230, 60, 40))
        d.rounded_rectangle([x - w * 0.12, y + h * 0.0, x + w * 0.06, y + h * 0.9], 30, fill=(230, 60, 40)); d.rounded_rectangle([x + w * 0.94, y + h * 0.0, x + w * 1.12, y + h * 0.9], 30, fill=(230, 60, 40))
        return tiktok_box(np.array(c.convert('RGB')), 'Учитель: «Что идёт после 8.5?»', 300)
    if f <= 431: return tiktok_box(clipf('en1', 20.0, 405, f), 'Ученик: «8.6»', 300)
    if f <= 454:
        img = zoom(clipf('egor7', 1.0, 432, f), 1.1); c = Image.fromarray(img).convert('RGBA'); d = ImageDraw.Draw(c); fo = font(F_BLACK, 56)
        for j in range(12):
            s = '59177'[:5 - (j % 5)]; d.text((4, 20 + j * 100), s, font=fo, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0)); d.text((W - fo.getlength(s) - 4, 20 + j * 100), s, font=fo, fill=(255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0))
        tk = 'Перешлите это в чат Тропарево ' * 3; off = (f - 432) * 18; d.text((-off, 1180), tk, font=font(F_BLACK, 60), fill=(255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0))
        return np.array(c.convert('RGB'))
    if f <= 469: return collage(f)
    if f <= 571:
        img = clipf('egor22', 20.0, 470, f)
        zin = [(531, 538), (542, 549), (553, 560), (564, 571)]
        if any(a <= f < b for a, b in zin): img = zoom(img, 1.6, 0.5, 0.55)
        if t < 16.1: img = small_caption(img, 'тебе нужно всего', 1000)
        elif t < 16.9: img = small_caption(img, 'два ингредиента', 1000)
        elif t < 17.42: img = small_caption(img, 'чтобы сделать прайм', 1000)
        else: img = small_caption(img, 'чтобы сделать прайм-прайм-прайм', 1000)
        return img
    if f <= 615: return evil_bottle(f)
    if f <= 674:
        img = clipf('egor0', 2.5, 616, f); x, y, w, h = face(img, 'bateman')
        g = img.astype(np.float32); m = np.zeros((H, W), np.float32); cv2.ellipse(m, (x + w // 2, y + h // 2), (int(w * 0.6), int(h * 0.75)), 0, 0, 360, 1, -1); m = cv2.GaussianBlur(m, (0, 0), 25)[..., None]
        orange = g * np.array([1.25, 0.75, 0.35]) + np.array([40, 10, 0]); g = g * (1 - m) + orange * m
        for ex in (x + w * 0.33, x + w * 0.67):
            ey = y + h * 0.42; yy, xx = np.mgrid[0:H, 0:W]; r = np.sqrt((xx - ex) ** 2 + (yy - ey) ** 2)
            g += (np.exp(-r / 22) * 330 + np.exp(-r / 70) * 90)[..., None] * np.array([1.0, 0.9, 0.6])
        img = np.clip(g, 0, 255).astype(np.uint8); return zoom(img, 1.0 + 0.02 * math.sin(f * 2.1))
    if f <= 720:
        if f <= 690: return collage(f) if f % 4 < 2 else glitch(zoom(clipf('en21', 200.0, 675, f), 1.8), f, 2)
        if f <= 712: return glitch((clipf('en21', 207.0, 691, f) * 0.25).astype(np.uint8), f, 1)
        return glitch(solid((250, 250, 250)) if f % 2 else collage(f), f, 2)
    if f <= 811:
        img = chekushka(f)
        if t >= 25.38: img = small_caption(img, 'чекушка.', 1060, 50)
        return img
    if f <= 822: return circle_letter('Т', (40, 110, 30), (255, 255, 255))
    if f <= 866: return circle_letter('8.6', (235, 60, 120), (255, 255, 255), circle=False, size=300)
    return outro(f)

if __name__ == '__main__':
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for f in [int(x) for x in sys.argv[2].split(',')]: Image.fromarray(render(f)).save(os.path.join(HERE, 'pv', f'{f:04d}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--all':
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', '30', '-i', '-',
                              '-i', os.path.join(HERE, 'src.mp4'), '-map', '0:v', '-map', '1:a', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p',
                              '-c:a', 'copy', '-movflags', '+faststart', os.path.join(HERE, 'tropar_brainrot.mp4')], stdin=subprocess.PIPE)
        for f in range(1, NF + 1): p.stdin.write(render(f).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
