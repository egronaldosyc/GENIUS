# Background painters for episode 1 ("Кто убил компанию?")
import math
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
W, H = 1920, 1080
_c = {}
def cache(k, fn):
    if k not in _c: _c[k] = fn()
    return _c[k]

def vgrad(c0, c1, h=H, w=W):
    g = np.linspace(0, 1, h)[:, None, None]
    return (np.array(c0) * (1 - g) + np.array(c1) * g).repeat(w, 1).astype(np.float32)

# ---------- night park (Тропарёво) ----------
def _trees(seed, n, ybase, hmin, hmax, col):
    rng = np.random.default_rng(seed); im = Image.new('RGBA', (W * 2, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(n):
        x = rng.uniform(-40, W * 2 + 40); h = rng.uniform(hmin, hmax); w = h * rng.uniform(0.28, 0.42)
        if rng.random() < 0.65:  # pine
            for k in range(5):
                yy = ybase - h + k * h * 0.17; ww = w * (0.35 + 0.16 * k)
                d.polygon([(x, yy), (x - ww, yy + h * 0.28), (x + ww, yy + h * 0.28)], fill=col)
            d.rectangle([x - 5, ybase - h * 0.12, x + 5, ybase], fill=col)
        else:  # birch-ish round
            d.rectangle([x - 4, ybase - h * 0.5, x + 4, ybase], fill=col)
            for k in range(6):
                d.ellipse([x - w * 0.6 + rng.uniform(-20, 20), ybase - h + k * 18 + rng.uniform(-10, 10), x + w * 0.6 + rng.uniform(-20, 20), ybase - h * 0.45 + k * 6], fill=col)
    d.rectangle([0, ybase - 2, W * 2, H], fill=col)
    return im
def _side_trees(seed):
    rng = np.random.default_rng(seed); im = Image.new('RGBA', (W * 2, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for i in range(16):
        side = i % 2; x = (rng.uniform(-60, 200) if side == 0 else rng.uniform(W - 200, W + 60)) + (W if i % 4 >= 2 else 0)
        h = rng.uniform(560, 820); w = h * 0.3; yb = 860
        for k in range(6):
            yy = yb - h + k * h * 0.14; ww = w * (0.3 + 0.14 * k)
            d.polygon([(x, yy), (x - ww, yy + h * 0.26), (x + ww, yy + h * 0.26)], fill=(10, 12, 22, 255))
        d.rectangle([x - 7, yb - h * 0.1, x + 7, yb], fill=(10, 12, 22, 255))
    return im
SKIES = {'day': ((110, 170, 235), (200, 225, 245)), 'dawn': ((60, 50, 110), (255, 160, 110)), 'storm': ((20, 22, 30), (60, 64, 80))}
def park(t, mood=0.0, moon=True, pan=0.0, lake=True, sky_kind=None):
    """mood 0 = calm night, 1 = eldritch (green/red sky)."""
    if sky_kind: sky = cache(('skyk', sky_kind), lambda: vgrad(*SKIES[sky_kind], 640))
    else: sky = cache(('sky', round(mood, 2)), lambda: vgrad((int(8 + 20 * mood), int(10 + 30 * mood), int(30 - 10 * mood)), (int(40 + 40 * mood), int(30 + 60 * mood), int(70 - 30 * mood)), 640))
    img = np.zeros((H, W, 3), np.float32); img[:640] = sky
    rng = np.random.default_rng(3)
    stars = cache('stars', lambda: [(rng.uniform(0, W), rng.uniform(0, 520), rng.uniform(0.5, 2.4), rng.uniform(0, 6)) for _ in range(260)])
    c = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(c)
    for (x, y, r, p) in (stars if sky_kind in (None, 'storm') else []):
        a = int(140 + 110 * math.sin(t * 2 + p)); d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 230, a))
    if sky_kind in ('day', 'dawn'):
        sx_, sy_ = (1500, 160) if sky_kind == 'day' else (960, 600)
        c.alpha_composite(cache(('sun', sky_kind), lambda: _glow(260, (255, 230, 150))), (sx_ - 260, sy_ - 260))
        d.ellipse([sx_ - 80, sy_ - 80, sx_ + 80, sy_ + 80], fill=(255, 240, 180))
    elif moon:
        mx, my = 1450 - pan * 0.05, 170
        glow = cache(('glow', mood > 0.5), lambda: _glow(160, (255, 240, 200) if mood < 0.5 else (140, 255, 160)))
        c.alpha_composite(glow, (int(mx - 160), int(my - 160)))
        d.ellipse([mx - 62, my - 62, mx + 62, my + 62], fill=(250, 245, 220) if mood < 0.5 else (170, 255, 170))
        d.ellipse([mx - 30, my - 20, mx - 10, my], fill=(225, 220, 195) if mood < 0.5 else (140, 225, 140))
        d.ellipse([mx + 10, my + 14, mx + 34, my + 36], fill=(225, 220, 195) if mood < 0.5 else (140, 225, 140))
    far = cache('t_far', lambda: _trees(11, 90, 600, 140, 240, (26, 30, 52, 255)))
    near = cache('t_near', lambda: _side_trees(12))
    if sky_kind in ('day', 'dawn'):
        far = cache(('t_far_d', sky_kind), lambda: _trees(11, 90, 600, 140, 240, (40, 90, 60, 255) if sky_kind == 'day' else (60, 40, 70, 255)))
        near = cache(('t_near_d', sky_kind), lambda: _recolor(_side_trees(12), (30, 70, 45) if sky_kind == 'day' else (35, 25, 45)))
    c.alpha_composite(far.crop((int(100 + pan * 0.3) % W, 0, int(100 + pan * 0.3) % W + W, H)))
    if lake:
        lk = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); ld = ImageDraw.Draw(lk)
        ld.ellipse([-200, 0, W + 200, 260], fill={'day': (70, 125, 190, 255), 'dawn': (110, 80, 120, 255)}.get(sky_kind, (18, 26, 50, 255) if mood < 0.5 else (20, 50, 35, 255)))
        for k in range(10):
            yy = 30 + k * 20; x0 = 300 + 160 * k + 40 * math.sin(t * 1.3 + k); ld.line([x0, yy, x0 + 220 + 30 * math.sin(t + k), yy], fill=(120, 140, 200, 70), width=2)
        c.alpha_composite(lk, (0, 590))
    c.alpha_composite(near.crop((int(pan) % W, 0, int(pan) % W + W, H)))
    # ground
    gcol = {'day': (60, 110, 60), 'dawn': (50, 40, 50)}.get(sky_kind, (14, 16, 26))
    d = ImageDraw.Draw(c); d.rectangle([0, 850, W, H], fill=gcol)
    d.polygon([(700, 1080), (900, 850), (1020, 850), (1220, 1080)], fill=(36, 34, 40))  # path = тропа
    return c
def _recolor(im, col):
    a = np.array(im); m = a[..., 3] > 0; a[m, 0], a[m, 1], a[m, 2] = col; return Image.fromarray(a)
def _glow(r, col):
    g = np.zeros((2 * r, 2 * r, 4), np.uint8); yy, xx = np.mgrid[0:2 * r, 0:2 * r]; dd = np.sqrt((xx - r) ** 2 + (yy - r) ** 2) / r
    g[..., :3] = col; g[..., 3] = (np.clip(1 - dd, 0, 1) ** 2 * 160).astype(np.uint8); return Image.fromarray(g)

def tentacles(c, t, rise, n=7, col=(40, 120, 70), base=760, x0s=300, span=1320):
    """Lovecraft: tentacles rising out of the lake. rise 0..1"""
    if rise <= 0: return
    d = ImageDraw.Draw(c)
    for i in range(n):
        x0 = x0s + i * (span / max(1, n - 1)); L = (300 + 130 * ((i * 37) % 3)) * rise
        pts = []
        for k in range(26):
            s = k / 25; y = base - L * s; x = x0 + 50 * math.sin(t * 1.6 + i * 1.7 + s * 4) * s
            pts.append((x, y, 26 * (1 - s) + 4))
        for (x, y, r) in pts: d.ellipse([x - r - 3, y - r - 3, x + r + 3, y + r + 3], fill=(10, 20, 14))
        for (x, y, r) in pts: d.ellipse([x - r, y - r, x + r, y + r], fill=col)
        for j, (x, y, r) in enumerate(pts[2:20:3]): d.ellipse([x - r * 0.35, y - r * 0.35, x + r * 0.35, y + r * 0.35], fill=(200, 160, 170))

def eye(c, t, cx, cy, r, open_=1.0, col=(255, 210, 60)):
    d = ImageDraw.Draw(c); h = r * 0.55 * open_
    if h < 2: d.line([cx - r, cy, cx + r, cy], fill=(0, 0, 0), width=6); return
    d.ellipse([cx - r, cy - h, cx + r, cy + h], fill=(240, 230, 200), outline=(20, 10, 10), width=6)
    pr = h * 0.85; px = cx + r * 0.2 * math.sin(t * 0.8)
    d.ellipse([px - pr, cy - pr, px + pr, cy + pr], fill=col)
    d.ellipse([px - pr * 0.18, cy - pr * 0.9, px + pr * 0.18, cy + pr * 0.9], fill=(10, 0, 0))

# ---------- detective board ----------
def cork():
    def mk():
        rng = np.random.default_rng(5); n = rng.normal(0, 1, (H // 4, W // 4)); n = cv2.resize(n, (W, H)) + rng.normal(0, 0.6, (H, W))
        base = np.array([150, 105, 65], np.float32)
        img = base[None, None, :] + n[..., None] * 14
        yy, xx = np.mgrid[0:H, 0:W]; v = np.clip(1.2 - 0.7 * np.sqrt(((xx - W / 2) / (W / 2)) ** 2 + ((yy - H / 2) / (H / 2)) ** 2), 0.35, 1)[..., None]
        return Image.fromarray(np.clip(img * v, 0, 255).astype(np.uint8)).convert('RGBA')
    return cache('cork', mk).copy()
def polaroid(pim, label, w=200, rot=0, col=(30, 30, 30), cross=False):
    k = ('pol', id(pim), label, w, rot, cross)
    def mk():
        fr = Image.new('RGBA', (w, int(w * 1.22)), (245, 242, 232, 255)); d = ImageDraw.Draw(fr)
        inner = Image.new('RGBA', (w - 24, w - 24), (60, 64, 80, 255))
        p = pim.copy(); s = (w - 24) * 1.35 / p.height; p = p.resize((int(p.width * s), int(p.height * s)), Image.LANCZOS)
        inner.alpha_composite(p, (int((w - 24 - p.width) / 2), int(-(w - 24) * 0.02)))
        fr.alpha_composite(inner, (12, 12))
        from render13 import font, F_BO
        fo = font(F_BO, int(w * 0.11)); d.text(((w - fo.getlength(label)) / 2, w - 6), label, font=fo, fill=col)
        if cross:
            d.line([20, 20, w - 20, w - 20], fill=(200, 20, 30), width=10); d.line([w - 20, 20, 20, w - 20], fill=(200, 20, 30), width=10)
        return fr.rotate(rot, expand=True, resample=Image.BICUBIC)
    return cache(k, mk)
def pin(d, x, y): d.ellipse([x - 9, y - 9, x + 9, y + 9], fill=(210, 30, 40), outline=(90, 0, 10), width=2); d.ellipse([x - 4, y - 6, x, y - 2], fill=(255, 160, 160))
def string(d, a, b, prog=1.0, sag=40):
    pts = []
    for k in range(21):
        s = k / 20 * prog; x = a[0] + (b[0] - a[0]) * s; y = a[1] + (b[1] - a[1]) * s + sag * math.sin(math.pi * s)
        pts.append((x, y))
    d.line(pts, fill=(200, 20, 30), width=4)

# ---------- void (Пелевин: Пустота) ----------
def void(t, inv=False):
    def mk():
        g = vgrad((245, 245, 240), (215, 215, 225)); return g
    g = cache('void', mk).copy()
    if inv: g = 255 - g
    c = Image.fromarray(g.astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(c)
    for k in range(6):
        r = (t * 80 + k * 180) % 1080; a = int(70 * (1 - r / 1080))
        d.ellipse([W / 2 - r, 540 - r, W / 2 + r, 540 + r], outline=(150, 150, 170, a) if not inv else (90, 90, 120, a), width=2)
    return c

# ---------- ice ----------
def ice_block(w, h):
    def mk():
        im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
        d.rounded_rectangle([0, 0, w - 1, h - 1], 18, fill=(170, 220, 255, 110), outline=(220, 245, 255, 220), width=5)
        for k in range(5): d.line([20 + k * 30, 14, 60 + k * 30, 60], fill=(255, 255, 255, 140), width=4)
        d.line([w - 40, h - 80, w - 16, h - 30], fill=(255, 255, 255, 120), width=4)
        return im
    return cache(('ice', w, h), mk)
def snow(c, t, n=120, speed=80, seed=2):
    rng = np.random.default_rng(seed); d = ImageDraw.Draw(c)
    fl = cache(('snow', seed, n), lambda: [(rng.uniform(0, W), rng.uniform(0, H), rng.uniform(1.5, 4.5), rng.uniform(0, 6)) for _ in range(n)])
    for (x, y, r, p) in fl:
        yy = (y + t * speed * r / 3) % H; xx = (x + 20 * math.sin(t + p)) % W
        d.ellipse([xx - r, yy - r, xx + r, yy + r], fill=(240, 248, 255, 200))

# ---------- TV wall (Generation П) ----------
def tv(w, h, inner, t, glitch=0.0):
    im = Image.new('RGBA', (w + 30, h + 50), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, w + 29, h + 29], 22, fill=(50, 45, 40), outline=(15, 12, 10), width=5)
    scr = inner.resize((w, h)).convert('RGBA')
    a = np.array(scr).astype(np.float32); a[::3, :, :3] *= 0.82
    if glitch > 0:
        rng = np.random.default_rng(int(t * 30));
        for _ in range(int(6 * glitch)):
            y0 = rng.integers(0, h - 10); a[y0:y0 + 8] = np.roll(a[y0:y0 + 8], rng.integers(-40, 40), 1)
    scr = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)); im.alpha_composite(scr, (15, 15))
    d.line([(w + 30) * 0.3, h + 30, (w + 30) * 0.2, h + 48], fill=(15, 12, 10), width=6); d.line([(w + 30) * 0.7, h + 30, (w + 30) * 0.8, h + 48], fill=(15, 12, 10), width=6)
    return im

# ---------- apartment (хата) ----------
def flat(t, party=0.0):
    def mk():
        img = vgrad((60, 48, 70), (40, 30, 45)); c = Image.fromarray(img.astype(np.uint8)).convert('RGBA'); d = ImageDraw.Draw(c)
        for x in range(0, W, 60): d.line([x, 0, x, 720], fill=(70, 56, 82), width=3)  # wallpaper
        d.rectangle([0, 720, W, H], fill=(90, 62, 44))
        for y in range(740, H, 50): d.line([0, y, W, y], fill=(78, 54, 38), width=3)
        d.rectangle([1400, 120, 1700, 440], fill=(20, 26, 50), outline=(200, 190, 170), width=12); d.line([1550, 120, 1550, 440], fill=(200, 190, 170), width=10)
        d.ellipse([1600, 170, 1650, 220], fill=(250, 245, 220))
        return c
    c = cache('flat', mk).copy()
    if party > 0:
        d = ImageDraw.Draw(c)
        for k in range(7):
            x = 200 + k * 250; ph = t * 3 + k
            col = [(255, 70, 160), (70, 150, 255), (110, 230, 110), (255, 205, 90), (170, 110, 255), (255, 150, 60), (60, 210, 200)][k]
            d.line([x, 0, x + 30 * math.sin(ph), 60], fill=col, width=3)
            d.ellipse([x + 30 * math.sin(ph) - 10, 55, x + 30 * math.sin(ph) + 10, 75], fill=col)
        g = Image.new('RGBA', (W, H), (255, 60, 160, int(40 * party * (0.5 + 0.5 * math.sin(t * 8)))))
        c.alpha_composite(g)
    return c
def table(c, x, y, items=('pizza', 'bottle')):
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([x - 220, y, x + 220, y + 40], 10, fill=(120, 80, 50), outline=(40, 25, 15), width=4)
    d.rectangle([x - 200, y + 40, x - 180, y + 170], fill=(100, 66, 40)); d.rectangle([x + 180, y + 40, x + 200, y + 170], fill=(100, 66, 40))
