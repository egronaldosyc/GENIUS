import os, sys, math, random, subprocess, io
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

D = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(D, 'src')
W, H, FPS = 720, 1280, 30
N = 453
T_END = N / FPS
PREVIEW = '--preview' in sys.argv

F_BLACK = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
F_BLACKI = '/usr/share/fonts/opentype/inter/Inter-BlackItalic.otf'
F_MONO = '/usr/share/fonts/truetype/jetbrains-mono/JetBrainsMono-ExtraBold.ttf'
F_EMOJI = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
F_SYM = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]

NEON = (198, 255, 0)
RED = (255, 40, 60)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

BEAT0, BEAT = 0.07, 0.5
def beat_phase(t):
    k = math.floor((t - BEAT0) / BEAT)
    return k, t - (BEAT0 + k * BEAT)
def punch(t, amt=0.10, dec=0.09):
    k, p = beat_phase(t)
    if p < 0: return 0
    return amt * math.exp(-p / dec)

# ---------- source frames ----------
_cache = {}
def src_frame(i):
    i = int(max(0, min(320, i)))
    if i not in _cache:
        if len(_cache) > 80: _cache.pop(next(iter(_cache)))
        _cache[i] = cv2.imread(os.path.join(SRC, f'{i+1:04d}.jpg'))
    return _cache[i]

FREEZE_T = 10.88
REW_A, REW_B = 11.44, 13.30
def src_index(t):
    if t < 7.07:
        return t * FPS
    if t < 8.07:  # stutter: repeat each quarter-beat
        k, p = beat_phase(t)
        b = BEAT0 + k * BEAT
        q = 0.125 if k % 2 else 0.25
        return (b + (p % q)) * FPS
    if t < FREEZE_T:
        return t * FPS
    if t < REW_A:
        return FREEZE_T * FPS
    if t < REW_B:
        u = (t - REW_A) / (REW_B - REW_A)
        return (1 - u) ** 1.3 * 320
    return 0

# ---------- face tracking (for laser eyes) ----------
CASC = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
_face = {}
def face_box(i):
    i = int(max(0, min(320, i)))
    if i in _face: return _face[i]
    g = cv2.cvtColor(cv2.resize(src_frame(i), (360, 640)), cv2.COLOR_BGR2GRAY)
    fs = CASC.detectMultiScale(g, 1.1, 5, minSize=(80, 80))
    r = None
    if len(fs):
        x, y, w, h = max(fs, key=lambda f: f[2] * f[3])
        r = np.array([x, y, w, h], float) * 2
    _face[i] = r
    return r
_last_face = [np.array([200, 300, 320, 320], float)]
def eyes(i):
    fb = face_box(i)
    if fb is None: fb = _last_face[0]
    else:
        fb = 0.5 * fb + 0.5 * _last_face[0]
        _last_face[0] = fb
    x, y, w, h = fb
    return (x + 0.32 * w, y + 0.42 * h), (x + 0.68 * w, y + 0.42 * h), w

# ---------- image fx (numpy BGR) ----------
def zoom(img, s, cx=0.5, cy=0.45, dx=0, dy=0):
    if s <= 1.0001 and dx == 0 and dy == 0: return img
    M = np.float32([[s, 0, (1 - s) * cx * W + dx], [0, s, (1 - s) * cy * H + dy]])
    return cv2.warpAffine(img, M, (W, H), borderMode=cv2.BORDER_REFLECT)

def rgb_split(img, d):
    if d < 1: return img
    d = int(d)
    b, g, r = cv2.split(img)
    r = np.roll(r, d, axis=1); b = np.roll(b, -d, axis=1)
    return cv2.merge([b, g, r])

def hue_shift(img, deg, sat=1.0):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.int16)
    hsv[..., 0] = (hsv[..., 0] + int(deg / 2)) % 180
    hsv[..., 1] = np.clip(hsv[..., 1] * sat, 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

def deep_fry(img, amt=1.0):
    x = img.astype(np.float32)
    x = (x - 128) * (1 + 0.6 * amt) + 128 + 15 * amt
    x = np.clip(x, 0, 255).astype(np.uint8)
    x = hue_shift(x, 0, 1 + 1.4 * amt)
    k = np.array([[0, -1, 0], [-1, 5 + 0 * amt, -1], [0, -1, 0]], np.float32)
    x = cv2.filter2D(x, -1, k)
    q = int(max(4, 30 - 25 * amt))
    _, enc = cv2.imencode('.jpg', cv2.resize(x, (W // 2, H // 2)), [cv2.IMWRITE_JPEG_QUALITY, q])
    x = cv2.resize(cv2.imdecode(enc, 1), (W, H), interpolation=cv2.INTER_NEAREST)
    # warm cast
    x = x.astype(np.int16); x[..., 2] += 25; x[..., 0] -= 20
    return np.clip(x, 0, 255).astype(np.uint8)

def glitch_slices(img, rng, n=8, maxd=60):
    out = img.copy()
    for _ in range(n):
        y = rng.randint(0, H - 40); h = rng.randint(8, 70); d = rng.randint(-maxd, maxd)
        out[y:y + h] = np.roll(out[y:y + h], d, axis=1)
        if rng.random() < 0.4:
            c = rng.randint(0, 2); out[y:y + h, :, c] = 255 - out[y:y + h, :, c]
    return out

def mirror(img):
    out = img.copy(); out[:, W // 2:] = img[:, :W // 2][:, ::-1]; return out

def vhs(img, t, rng):
    x = img.copy()
    x = cv2.GaussianBlur(x, (5, 1), 0)
    x = rgb_split(x, 6)
    # tracking band
    by = int((t * 900) % (H + 200)) - 100
    for y in range(max(0, by), min(H, by + 90), 2):
        x[y] = np.roll(x[y], rng.randint(-40, 40), axis=0)
    x[max(0, by):min(H, by + 90)] = np.clip(x[max(0, by):min(H, by + 90)].astype(np.int16) + 40, 0, 255).astype(np.uint8)
    x[::3] = (x[::3] * 0.65).astype(np.uint8)
    noise = np.random.default_rng(int(t * 1000)).integers(0, 40, (H, W, 1), dtype=np.uint8)
    x = cv2.add(x, np.repeat(noise, 3, axis=2))
    return x

def bw(img):
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(g, cv2.COLOR_GRAY2BGR)

def vignette(img, k=0.8):
    yy, xx = np.mgrid[0:H, 0:W]
    r = np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2)
    m = np.clip(1 - k * (r - 0.4), 0, 1)[..., None]
    return (img * m).astype(np.uint8)
_vig = None

# ---------- sprites ----------
def emoji(ch, size):
    f = font(F_EMOJI, 109)
    im = Image.new('RGBA', (160, 160), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((10, 10), ch, font=f, embedded_color=True)
    bb = im.getbbox(); im = im.crop(bb)
    s = size / max(im.size)
    return im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)

def make_can(label='ВОЛЬТ'):
    w, h = 110, 210
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    body = np.zeros((h - 20, w, 4), np.uint8)
    xs = np.linspace(-1, 1, w)
    shade = (0.35 + 0.65 * np.sqrt(np.clip(1 - xs ** 2, 0, 1)))
    shade = shade + 0.5 * np.exp(-((xs + 0.45) / 0.12) ** 2)
    for c, v in enumerate((20, 20, 25)):
        body[..., c] = np.clip(v + 40 * shade, 0, 255)
    body[..., 3] = 255
    b = Image.fromarray(body)
    d = ImageDraw.Draw(b)
    # neon band
    band = Image.new('RGBA', (w, h - 20), (0, 0, 0, 0)); bd = ImageDraw.Draw(band)
    bd.polygon([(0, 40), (w, 20), (w, 150), (0, 170)], fill=NEON + (255,))
    bnp = np.array(band).astype(np.float32); bnp[..., :3] *= np.clip(shade, 0, 1.3)[None, :, None]
    band = Image.fromarray(np.clip(bnp, 0, 255).astype(np.uint8))
    b.alpha_composite(band)
    # lightning
    d = ImageDraw.Draw(b)
    d.polygon([(62, 45), (38, 100), (56, 100), (44, 150), (76, 88), (58, 88), (70, 45)], fill=(10, 10, 10, 255))
    # label text rotated
    tl = Image.new('RGBA', (170, 40), (0, 0, 0, 0))
    ImageDraw.Draw(tl).text((85, 20), label, font=font(F_BLACK, 30), fill=(10, 10, 10, 255), anchor='mm')
    tl = tl.rotate(90, expand=True)
    b.alpha_composite(tl, (w - 40, 10))
    im.paste(b, (0, 12))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 0, w - 4, 22], 8, fill=(190, 190, 200, 255), outline=(120, 120, 130, 255), width=2)
    d.rounded_rectangle([4, h - 16, w - 4, h - 1], 6, fill=(170, 170, 180, 255))
    d.ellipse([w // 2 - 14, 4, w // 2 + 14, 16], outline=(90, 90, 100, 255), width=3)
    return im

CAN = make_can()
CAN2 = make_can('ТАУРИН')
EMO = {k: emoji(k, 150) for k in ['⚡', '🥟', '🔋', '💀', '🫀', '🧃', '😵', '🔥', '🍜', '🚶', '🏢', '🏠', '🥫', '😎', '🤡']}

# ---------- text helpers ----------
def text_img(txt, size, fill=WHITE, stroke=BLACK, sw=None, f=F_BLACK, spacing=0):
    fo = font(f, size)
    sw = int(size * 0.09) if sw is None else sw
    dummy = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    bb = dummy.multiline_textbbox((0, 0), txt, font=fo, stroke_width=sw, align='center', spacing=spacing)
    im = Image.new('RGBA', (int(bb[2] - bb[0]) + 20, int(bb[3] - bb[1]) + 20), (0, 0, 0, 0))
    ImageDraw.Draw(im).multiline_text((10 - bb[0], 10 - bb[1]), txt, font=fo, fill=fill, stroke_width=sw,
                                      stroke_fill=stroke, align='center', spacing=spacing)
    return im

def paste(canvas, im, cx, cy, scale=1.0, rot=0.0, alpha=1.0):
    if im.width > 400 and im.width * scale > W - 60: scale = (W - 60) / im.width
    if scale != 1.0:
        im = im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.BILINEAR)
    if rot: im = im.rotate(rot, expand=True, resample=Image.BICUBIC)
    if alpha < 1:
        a = im.getchannel('A').point(lambda v: int(v * alpha)); im = im.copy(); im.putalpha(a)
    canvas.alpha_composite(im, (int(cx - im.width / 2), int(cy - im.height / 2))) if (
        0 <= int(cx - im.width / 2) and 0 <= int(cy - im.height / 2) and
        int(cx - im.width / 2) + im.width <= canvas.width and int(cy - im.height / 2) + im.height <= canvas.height
    ) else _paste_clip(canvas, im, int(cx - im.width / 2), int(cy - im.height / 2))

def _paste_clip(canvas, im, x, y):
    layer = Image.new('RGBA', canvas.size, (0, 0, 0, 0))
    layer.paste(im, (x, y), im)
    canvas.alpha_composite(layer)

def pop(t, t0, dur=0.18):
    """scale-in bounce"""
    u = (t - t0) / dur
    if u < 0: return 0
    if u >= 1: return 1
    return 1 + 0.35 * math.sin(u * math.pi) * (1 - u) + (u - 1) * 0 if u > 0.5 else 0.2 + 1.6 * u * (1.35 - 0.7 * u)

def ease_pop(t, t0, dur=0.2):
    u = (t - t0) / dur
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    c1 = 2.4; c3 = c1 + 1
    return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2

# ---------- HUD ----------
def bar(d, x, y, w, h, frac, col, label, valtxt, blink=False):
    d.rounded_rectangle([x, y, x + w, y + h], 6, fill=(0, 0, 0, 170), outline=(255, 255, 255, 200), width=2)
    fw = int((w - 6) * max(0, min(1, frac)))
    if fw > 0 and not blink:
        d.rounded_rectangle([x + 3, y + 3, x + 3 + fw, y + h - 3], 4, fill=col + (255,))
    fo = font(F_MONO, 19)
    d.text((x + 8, y + h / 2), label, font=fo, fill=WHITE, anchor='lm', stroke_width=2, stroke_fill=BLACK)
    d.text((x + w - 8, y + h / 2), valtxt, font=fo, fill=WHITE, anchor='rm', stroke_width=2, stroke_fill=BLACK)

def draw_hud(c, t, rng):
    d = ImageDraw.Draw(c)
    # energy: overflows
    if t < 4.07: e = 0.55 + 0.45 * min(1, (t - 2.07) / 1.5); et = f'{int(e*100)}%'
    elif t < 10.88: e = 1.0; et = ['147%', '312%', '999%', 'ERR', '∞%', 'ДА'][int(t * 6) % 6] if t > 4.07 else '100%'
    else: e = 0; et = '0%'
    blink = (t > 6.07 and int(t * 12) % 2 == 0)
    bar(d, 24, 60, 300, 34, e, NEON, 'ЭНЕРГИЯ', et, blink)
    liver = max(0.0, 0.31 - 0.31 * (t - 2.07) / 8.5)
    lt = f'{int(liver*100)}%' if liver > 0.02 else 'НЕТ'
    bar(d, 24, 102, 300, 34, liver, RED, 'ПЕЧЕНЬ', lt, liver < 0.1 and int(t * 8) % 2 == 0)
    pulse = int(96 + min(1, max(0, (t - 2) / 6)) * 140 + rng.randint(-9, 9))
    if t > 10.88: pulse = 0
    d.rounded_rectangle([24, 144, 196, 178], 6, fill=(0, 0, 0, 170), outline=(255, 255, 255, 200), width=2)
    d.text((36, 161), f'ПУЛЬС {pulse}', font=font(F_MONO, 19), fill=(255, 120, 140), anchor='lm', stroke_width=2, stroke_fill=BLACK)
    # heart emoji beating
    hs = 34 * (1 + 2.5 * punch(t, 0.12, 0.08))
    paste(c, EMO['🫀'], 220, 161, hs / 150)
    # clock + steps bottom
    mins = 7 * 60 + 41 + int((t - 2.07) * 1.9)
    clk = f'{mins//60:02d}:{mins%60:02d}'
    d.rounded_rectangle([W - 180, H - 92, W - 24, H - 46], 8, fill=(0, 0, 0, 170), outline=(255, 255, 255, 200), width=2)
    d.text((W - 102, H - 69), ('● ' if int(t * 2) % 2 == 0 else '  ') + clk, font=font(F_MONO, 26), fill=(255, 70, 70), anchor='mm')
    steps = int(max(0, 2517 - (t - 2.07) * 260))
    d.rounded_rectangle([24, H - 92, 380, H - 46], 8, fill=(0, 0, 0, 170), outline=(255, 255, 255, 200), width=2)
    d.text((40, H - 69), f'ДО РАБОТЫ: {steps} ШАГ.', font=font(F_MONO, 22), fill=WHITE, anchor='lm')

# ---------- particles ----------
def rain(c, t, t0, t1, sprites, n, seed, size=(70, 120), speed=(900, 1600), spin=True):
    if t < t0 or t > t1 + 1.5: return
    r = random.Random(seed)
    for i in range(n):
        st = t0 + r.random() * (t1 - t0)
        x0 = r.uniform(30, W - 30); v = r.uniform(*speed); sz = r.uniform(*size)
        rot0 = r.uniform(0, 360); rs = r.uniform(-400, 400) if spin else 0
        spr = sprites[i % len(sprites)]
        dt = t - st
        if dt < 0: continue
        y = -150 + v * dt + 600 * dt * dt
        if y > H + 150: continue
        x = x0 + math.sin(dt * 3 + i) * 30
        paste(c, spr, x, y, sz / max(spr.size), rot0 + rs * dt)

def lasers(c, t, si):
    (lx, ly), (rx, ry), fw = eyes(si)
    layer = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(layer)
    fl = 0.75 + 0.25 * math.sin(t * 60)
    for ex, ey, sgn in ((lx, ly, -1), (rx, ry, 1)):
        ang = math.radians(115 if sgn < 0 else 65) + 0.15 * math.sin(t * 7)
        ex2, ey2 = ex + math.cos(ang) * 2000 * sgn * 0 + math.cos(ang) * 2000, ey + math.sin(ang) * 2000
        for wdt, col in ((44, (255, 0, 0, 90)), (24, (255, 40, 40, 170)), (9, (255, 230, 230, 255))):
            d.line([(ex, ey), (ex2, ey2)], fill=col, width=int(wdt * fl))
        for r_, col in ((46, (255, 0, 0, 110)), (26, (255, 80, 80, 200)), (11, (255, 255, 255, 255))):
            d.ellipse([ex - r_, ey - r_, ex + r_, ey + r_], fill=col)
    layer = Image.alpha_composite(layer.filter(ImageFilter.GaussianBlur(10)), layer)
    c.alpha_composite(layer)

def chat(c, t):
    msgs = [
        (8.07, 'Печень', '🫀', 'я увольняюсь. это не обсуждается', (255, 120, 120)),
        (8.57, 'Желудок', '🥟', 'опять пельмени из морозилки??', (255, 200, 90)),
        (9.07, 'Сердце', '🫀', 'пульс 228 это норм вообще?', (255, 90, 160)),
        (9.57, 'Почки', '💀', 'почки покинули чат', (170, 170, 170)),
    ]
    d = ImageDraw.Draw(c)
    # header
    hx, hy = 40, 700
    hdr_a = ease_pop(t, 8.07, 0.15)
    if hdr_a <= 0: return
    d.rounded_rectangle([hx, hy, W - 40, hy + 56], 14, fill=(30, 36, 48, 235))
    d.text((hx + 20, hy + 28), 'ОРГАНЫ ЭНЕРГИЧНОГО (4)', font=font(F_BLACK, 24), fill=WHITE, anchor='lm')
    d.text((W - 60, hy + 28), 'онлайн?', font=font(F_MONO, 18), fill=(140, 200, 140), anchor='rm')
    y = hy + 70
    for t0, who, em, msg, col in msgs:
        s = ease_pop(t, t0, 0.18)
        if s <= 0: break
        fo = font(F_BLACK, 26) if who != 'Почки' else font(F_BLACKI, 26)
        tw = ImageDraw.Draw(Image.new('RGBA', (1, 1))).textlength(msg, font=fo)
        bw_ = int(min(W - 150, tw + 40)); bh = 86
        bub = Image.new('RGBA', (bw_ + 70, bh + 4), (0, 0, 0, 0)); bd = ImageDraw.Draw(bub)
        bub.alpha_composite(EMO[em].resize((48, 48)) if EMO[em].size[0] == EMO[em].size[1] else EMO[em].resize((48, int(48 * EMO[em].height / EMO[em].width))), (0, bh - 52))
        bd.rounded_rectangle([60, 0, 60 + bw_, bh], 18, fill=(255, 255, 255, 245))
        bd.text((78, 10), who, font=font(F_BLACK, 20), fill=col)
        bd.text((78, 38), msg, font=fo, fill=(20, 20, 20))
        sc = s
        paste(c, bub, 40 + (bub.width * sc) / 2, y + bh / 2, sc)
        y += bh + 12

def label_box(c, t):
    rows = [(2.07, 'СОСТАВ:', ''), (2.32, 'Энергетик', '64%'), (2.57, 'Пельмени (ларёк)', '27%'),
            (2.82, 'Доширак', '8%'), (3.07, 'Сон', '1%'), (3.32, 'Овощи', 'НЕ НАЙДЕНЫ'), (3.57, 'Срок годности', 'ИСТЁК')]
    a = ease_pop(t, 2.07, 0.2)
    if a <= 0: return
    bx, by, bw_, rh = 70, 690, W - 140, 50
    n = sum(1 for r in rows if t >= r[0])
    box = Image.new('RGBA', (bw_, 30 + rh * len(rows)), (0, 0, 0, 0)); d = ImageDraw.Draw(box)
    d.rectangle([0, 0, bw_ - 1, 20 + rh * n], fill=(255, 255, 255, 248), outline=BLACK, width=5)
    for i, (t0, k, v) in enumerate(rows[:n]):
        yy = 12 + i * rh
        if i == 0:
            d.text((18, yy), k, font=font(F_BLACK, 36), fill=BLACK)
            d.text((bw_ - 18, yy + 6), 'ЭНЕРГИЧНЫЙ, 1 шт.', font=font(F_MONO, 20), fill=(90, 90, 90), anchor='ra')
            d.rectangle([10, yy + rh - 6, bw_ - 10, yy + rh - 2], fill=BLACK)
        else:
            d.text((18, yy + 6), k, font=font(F_BLACK, 30), fill=BLACK)
            red = v in ('НЕ НАЙДЕНЫ', 'ИСТЁК')
            d.text((bw_ - 18, yy + 6), v, font=font(F_BLACK, 30), fill=(220, 0, 30) if red else BLACK, anchor='ra')
            if i < n - 1: d.line([18, yy + rh - 2, bw_ - 18, yy + rh - 2], fill=(0, 0, 0), width=1)
    rot = -3 + 2 * punch(t, 1, 0.1)
    paste(c, box, W / 2, by + box.height / 2, a, rot)

def ff_arrows(d, x, y, s, col):
    for k in range(2):
        ox = x + k * s * 0.9
        d.polygon([(ox + s, y - s * 0.6), (ox + s, y + s * 0.6), (ox, y)], fill=col, outline=BLACK)

# ---------- main frame ----------
def render(fi):
    t = fi / FPS
    rng = random.Random(fi * 7919)
    si = src_index(t)
    img = src_frame(si).copy()
    k, ph = beat_phase(t)

    # ---- base image effects by section
    if t < 0.07:
        img[:] = 0
    elif t < 2.07:
        img = zoom(img, 1.0 + punch(t, 0.16, 0.08))
        img = rgb_split(img, 40 * punch(t, 1, 0.06))
        if ph < 0.05 and k >= 0: img = glitch_slices(img, rng, 6, 50)
    elif t < 4.07:
        img = zoom(img, 1.03 + punch(t, 0.08, 0.1))
        img = rgb_split(img, 20 * punch(t, 1, 0.06))
    elif t < 6.07:
        sh = 18 * (0.4 + punch(t, 1, 0.12))
        img = zoom(img, 1.08 + punch(t, 0.10, 0.1), dx=rng.uniform(-sh, sh), dy=rng.uniform(-sh, sh))
        img = rgb_split(img, 8 + 30 * punch(t, 1, 0.08))
        img = hue_shift(img, 0, 1.5)
    elif t < 8.07:
        amt = 0.6 + 0.4 * punch(t, 1, 0.15)
        sh = 26
        img = zoom(img, 1.1 + punch(t, 0.14, 0.08), dx=rng.uniform(-sh, sh), dy=rng.uniform(-sh, sh))
        img = deep_fry(img, amt)
        img = hue_shift(img, (t - 6.07) * 180)
        if ph < 0.06: img = glitch_slices(img, rng, 10, 90)
    elif t < 10.07:
        img = zoom(img, 1.05 + punch(t, 0.07, 0.1))
        if 9.07 <= t < 9.57: img = mirror(img)
        if t >= 9.57: img = hue_shift(img, 180 * (int(t * 8) % 2), 1.3)
    elif t < FREEZE_T:
        u = (t - 10.07) / (FREEZE_T - 10.07)
        img = zoom(img, 1.1 + 0.5 * u + punch(t, 0.1, 0.06), dx=rng.uniform(-30, 30) * u, dy=rng.uniform(-30, 30) * u)
        img = deep_fry(img, 0.5 + 0.5 * u) if int(t * 15) % 2 else hue_shift(255 - img, rng.uniform(0, 360), 2)
        img = rgb_split(img, 30 * u + 10)
        if rng.random() < 0.6: img = glitch_slices(img, rng, 14, 140)
    elif t < REW_A:
        u = (t - FREEZE_T) / (REW_A - FREEZE_T)
        img = bw(zoom(img, 1.6 + 0.15 * u))
        img = vignette(img, 1.2)
    elif t < REW_B:
        img = vhs(zoom(img, 1.04), t, rng)
    else:
        img = cv2.GaussianBlur(img, (0, 0), 18)
        img = (img * 0.35).astype(np.uint8)
        img = hue_shift(img, (t - 13.3) * 120, 1.6)

    c = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)).convert('RGBA')

    # ---- overlays
    if 6.07 <= t < 8.07:
        lasers(c, t, si)
    if 2.07 <= t < 10.88 or (FREEZE_T <= t < REW_A):
        draw_hud(c, t, rng)

    if 0.07 <= t < 2.07:
        s = ease_pop(t, 0.07, 0.22)
        title = text_img('ЭНЕРГИЧНЫЙ', 112, NEON, BLACK, 12)
        sc = s * (0.98 + 1.2 * punch(t, 0.1, 0.07)) * (W - 30) / title.width
        jx, jy = rng.uniform(-4, 4), rng.uniform(-4, 4)
        # chromatic ghost
        if punch(t, 1, 0.06) > 0.3:
            g = text_img('ЭНЕРГИЧНЫЙ', 112, (255, 0, 120), (255, 0, 120), 12)
            paste(c, g, W / 2 + 14 + jx, 560 + jy, sc, -4, 0.6)
        paste(c, title, W / 2 + jx, 560 + jy, sc, -4)
        subs = [(0.57, 'ИДЁТ НА РАБОТУ', WHITE), (1.07, 'СЕРИЯ №847', WHITE), (1.57, '(ОПЯТЬ)', RED)]
        y = 680
        for t0, tx, col in subs:
            ss = ease_pop(t, t0, 0.16)
            if ss > 0:
                im = text_img(tx, 58, col, BLACK, 7)
                paste(c, im, W / 2, y, ss, rng.uniform(-2, 2))
            y += 78
        if t < 0.6:
            paste(c, EMO['⚡'], 110, 450, 1.0 * s, -20); paste(c, EMO['⚡'], W - 110, 670, 0.9 * s, 25)

    if 2.07 <= t < 4.07:
        label_box(c, t)

    if 4.07 <= t < 6.6:
        rain(c, t, 4.07, 6.0, [CAN, CAN2, EMO['⚡'], CAN, EMO['🔋']], 26, 11, (110, 190))
    if 4.07 <= t < 6.07:
        n = int((t - 4.07) / 0.5)
        lines = ['ЭНЕРГЕТИК №1', 'ЭНЕРГЕТИК №2', 'ЭНЕРГЕТИК №3', 'ЭНЕРГЕТИК №4']
        t0 = 4.07 + n * 0.5
        s = ease_pop(t, t0, 0.14)
        im = text_img(lines[n], 84, NEON, BLACK, 9)
        paste(c, im, W / 2, 820, s * (1 + punch(t, 0.08, 0.1)), rng.uniform(-3, 3))
        sub = ['доброе утро', 'а ещё даже не 8:00', 'это ещё завтрак', 'вода? не слышал'][n]
        paste(c, text_img(sub, 46, WHITE, BLACK, 6), W / 2, 920, ease_pop(t, t0 + 0.08, 0.14))

    if 6.07 <= t < 8.07:
        rain(c, t, 6.07, 8.0, [EMO['⚡'], EMO['🔥']], 18, 23, (70, 130), (1400, 2200))
        p = 1 + 0.15 * punch(t, 1, 0.1)
        a = text_img('ТАУРИНОВЫЙ\nРЕЖИМ', 104, (255, 255, 0), (200, 0, 0), 12, spacing=-4)
        paste(c, a, W / 2 + rng.uniform(-8, 8), 900 + rng.uniform(-8, 8), p * min(1, (W - 40) / a.width) * ease_pop(t, 6.07, 0.2), rng.uniform(-4, 4))
        if t >= 7.07:
            b = text_img('АКТИВИРОВАН', 60, WHITE, BLACK, 7)
            paste(c, b, W / 2, 1060, ease_pop(t, 7.07, 0.15) * (1 + 0.2 * punch(t, 1, 0.06)))

    if 8.07 <= t < 10.07:
        rain(c, t, 8.07, 9.9, [EMO['🥟'], EMO['🍜'], EMO['🥟']], 14, 37, (60, 100), (500, 900))
        chat(c, t)

    if 10.07 <= t < FREEZE_T:
        u = (t - 10.07) / (FREEZE_T - 10.07)
        rain(c, t, 10.07, 10.8, [CAN, EMO['🥟'], EMO['⚡'], CAN2, EMO['💀'], EMO['🤡']], 30, 51, (80, 170), (1600, 2600))
        im = text_img('ПОЧТИ\nДОШЁЛ', 120, WHITE if int(t * 15) % 2 else NEON, BLACK, 13, spacing=-6)
        paste(c, im, W / 2 + rng.uniform(-14, 14), 760 + rng.uniform(-14, 14), (0.8 + 0.5 * u) * min(1, (W - 40) / im.width), rng.uniform(-8, 8))
        if 10.57 <= t < 10.63:
            c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 200)))

    if FREEZE_T <= t < REW_A:
        d = ImageDraw.Draw(c)
        # flatline
        pts = []
        for x in range(0, W, 6):
            yy = 900
            if 300 < x < 330: yy = 900 - 120 * math.sin((x - 300) / 30 * math.pi) * (1 if t < FREEZE_T + 0.08 else 0)
            pts.append((x, yy))
        d.line(pts, fill=(255, 30, 50), width=8)
        a = text_img('ЭНЕРГИЯ: 0%', 92, RED, BLACK, 10)
        paste(c, a, W / 2, 760, ease_pop(t, FREEZE_T, 0.12))
        b = text_img('…и это только дорога\nНА работу', 58, WHITE, BLACK, 6)
        paste(c, b, W / 2, 1040, ease_pop(t, FREEZE_T + 0.2, 0.15))

    if REW_A <= t < REW_B:
        d = ImageDraw.Draw(c)
        if int(t * 3) % 2 == 0 or t < REW_A + 0.3:
            ff_arrows(d, 50, 95, 34, WHITE)
        d.text((140, 95), 'REW', font=font(F_MONO, 54), fill=WHITE, anchor='lm', stroke_width=3, stroke_fill=BLACK)
        u = (t - REW_A) / (REW_B - REW_A)
        mins = 18 * 60 + 5 + int(u * 22)
        d.text((W - 40, 95), f'{mins//60:02d}:{mins%60:02d}', font=font(F_MONO, 44), fill=WHITE, anchor='rm', stroke_width=3, stroke_fill=BLACK)
        a = text_img('А ТЕПЕРЬ\nС РАБОТЫ', 110, NEON, BLACK, 12, spacing=-6)
        paste(c, a, W / 2 + rng.uniform(-3, 3), 760, ease_pop(t, REW_A, 0.18) * min(1, (W - 40) / a.width), -3)
        if t > REW_A + 0.5:
            b = text_img('(маршрут тот же,\nэнергетик новый)', 46, WHITE, BLACK, 6)
            paste(c, b, W / 2, 960, ease_pop(t, REW_A + 0.5, 0.15))
        d.text((W / 2, H - 70), 'PLAY ◀◀ SP', font=font(F_SYM, 30), fill=WHITE, anchor='mm', stroke_width=2, stroke_fill=BLACK)

    if t >= REW_B:
        lt = t - REW_B
        # loop diagram: home <-> work with walking guy orbiting
        cx, cy, R = W / 2, 520, 200
        d = ImageDraw.Draw(c)
        d.ellipse([cx - R, cy - R * 0.55, cx + R, cy + R * 0.55], outline=(255, 255, 255, 220), width=6)
        paste(c, EMO['🏠'], cx - R, cy, 0.85 * (1 + 2 * punch(t, 0.1, 0.1)))
        paste(c, EMO['🏢'], cx + R, cy, 0.85 * (1 + 2 * punch(t + 0.25, 0.1, 0.1)))
        for j in range(3):
            ang = lt * 5 + j * 2.094
            paste(c, EMO['🚶'], cx + R * math.cos(ang), cy + R * 0.55 * math.sin(ang), 0.6)
            paste(c, CAN, cx + R * math.cos(ang + 1.0) * 0.6, cy + R * 0.33 * math.sin(ang + 1.0), 0.45, math.degrees(ang) * 3)
        a = text_img('ЗАВТРА В 7:40', 96, WHITE, BLACK, 10)
        paste(c, a, W / 2, 820, ease_pop(t, REW_B, 0.2) * min(1, (W - 40) / a.width))
        b = text_img('ОПЯТЬ', 130, NEON, BLACK, 13)
        paste(c, b, W / 2, 950, ease_pop(t, REW_B + 0.25, 0.2) * (1 + 0.06 * math.sin(lt * 20)), -4)
        if lt > 0.6:
            e = text_img('энергетик уже в холодильнике 🥫', 36, WHITE, BLACK, 4)
            e = text_img('энергетик уже ждёт в холодильнике', 36, WHITE, BLACK, 4)
            paste(c, e, W / 2, 1075, ease_pop(t, REW_B + 0.6, 0.15))
        if lt > 0.95:
            m = text_img('*бип-бип-бип* пельмени готовы', 38, (255, 200, 90), BLACK, 4)
            paste(c, m, W / 2, 1135, ease_pop(t, REW_B + 0.95, 0.15), rng.uniform(-2, 2))
        d.text((W / 2, H - 60), 'оригинал: @bor.edka', font=font(F_MONO, 22), fill=(200, 200, 200), anchor='mm')
        if t > T_END - 0.45:
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 255)))
            im = text_img('▶ СЕРИЯ №848', 80, NEON, BLACK, 8, f=F_SYM)
            paste(c, im, W / 2, H / 2, ease_pop(t, T_END - 0.45, 0.12))

    out = np.array(c.convert('RGB'))
    return out

if __name__ == '__main__':
    if PREVIEW:
        ts = [float(x) for x in sys.argv[2].split(',')]
        for t in ts:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(D, 'pv', f'{t:05.2f}.jpg'), quality=85)
        sys.exit()
    out = sys.argv[1]
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                          '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    for fi in range(N):
        p.stdin.write(render(fi).tobytes())
        if fi % 50 == 0: print(fi, flush=True)
    p.stdin.close(); p.wait()
