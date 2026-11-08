# Hotline-Miami-ish neon visuals
import math
import numpy as np, cv2
from PIL import Image, ImageDraw
W, H = 1920, 1080
_c = {}
def cache(k, fn):
    if k not in _c: _c[k] = fn()
    return _c[k]
PINK = (255, 40, 170); CYAN = (40, 240, 255); PURP = (120, 30, 200); YEL = (255, 230, 60); ORNG = (255, 120, 40)
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)

def neon_bg(t, c1=(255, 40, 170), c2=(40, 20, 120), c3=(30, 230, 255), mode='waves'):
    """animated hotline-miami style gradient with diagonal wave stripes"""
    u = (_X / W) * 0.9 + (_Y / H) * 0.6
    if mode == 'waves':
        s = 0.5 + 0.5 * np.sin((_X * 0.6 + _Y) / 90 - t * 3 + np.sin(_X / 300 + t) * 1.5)
    elif mode == 'rings':
        r = np.sqrt((_X - W / 2) ** 2 + (_Y - H / 2) ** 2); s = 0.5 + 0.5 * np.sin(r / 60 - t * 4)
    else:
        s = 0.5 + 0.5 * np.sin(_Y / 40 - t * 5)
    k1 = np.array(c1, np.float32); k2 = np.array(c2, np.float32); k3 = np.array(c3, np.float32)
    base = k2 * (1 - u[..., None]) * 0.9 + k1 * u[..., None] * 0.9
    img = base * (0.55 + 0.45 * s[..., None]) + k3 * (s[..., None] ** 8) * 0.35
    return Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).convert('RGBA')

def hm_text(txt, size, col=(255, 255, 255), glow=PINK, shadow=CYAN, f=None, t=0.0, wob=True):
    """big italic text with offset colored shadows; returns RGBA"""
    from render13 import font, F_BLACKI
    fo = font(f or F_BLACKI, size)
    bb = ImageDraw.Draw(Image.new('L', (1, 1))).textbbox((0, 0), txt, font=fo)
    w, h = bb[2] - bb[0] + 60, bb[3] - bb[1] + 60
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    o = max(4, size // 22)
    d.text((30 - bb[0] + o, 30 - bb[1] + o), txt, font=fo, fill=shadow + (255,))
    d.text((30 - bb[0] - o // 2, 30 - bb[1] - o // 2), txt, font=fo, fill=glow + (255,))
    d.text((30 - bb[0], 30 - bb[1]), txt, font=fo, fill=col + (255,), stroke_width=max(2, size // 30), stroke_fill=(20, 0, 30))
    return im

def wobble(im, t, amp=4, ang=4):
    a = ang * math.sin(t * 2.3); s = 1 + 0.03 * math.sin(t * 3.1)
    out = im.rotate(a, expand=True, resample=Image.BICUBIC)
    return out.resize((int(out.width * s), int(out.height * s)), Image.BILINEAR)

def vhs(arr, t, k=0.0, ab=4):
    """arr float32 HxWx3 -> scanlines + chromatic aberration"""
    sh = int(ab + 10 * k)
    if sh:
        arr[..., 0] = np.roll(arr[..., 0], sh, 1); arr[..., 2] = np.roll(arr[..., 2], -sh, 1)
    arr[::3] *= 0.84
    y0 = int((t * 220) % H); arr[y0:y0 + 6] += 25
    return arr

# ---------- top-down Тропарёвский лес ----------
def forest_map(seed=3):
    def mk():
        rng = np.random.default_rng(seed)
        im = Image.new('RGBA', (W, H), (18, 6, 30, 255)); d = ImageDraw.Draw(im)
        for x in range(0, W, 60): d.line([x, 0, x, H], fill=(60, 20, 90), width=1)
        for y in range(0, H, 60): d.line([0, y, W, y], fill=(60, 20, 90), width=1)
        # path (тропа)
        pts = [(0, 620), (300, 560), (600, 640), (900, 520), (1200, 600), (1500, 480), (1920, 560)]
        d.line(pts, fill=(120, 60, 40), width=70, joint='curve'); d.line(pts, fill=(160, 90, 60), width=50, joint='curve')
        # lake
        d.ellipse([1180, 140, 1680, 400], fill=(20, 60, 120), outline=CYAN, width=5)
        trees = []
        for _ in range(170):
            x, y = rng.uniform(0, W), rng.uniform(0, H)
            if abs(y - (560 + 60 * math.sin(x / 300))) < 90: continue
            if 1150 < x < 1710 and 110 < y < 430: continue
            r = rng.uniform(26, 52); trees.append((x, y, r))
        for x, y, r in trees:
            d.ellipse([x - r + 6, y - r + 8, x + r + 6, y + r + 8], fill=(0, 0, 0, 120))
            d.ellipse([x - r, y - r, x + r, y + r], fill=(30, 120, 60), outline=(120, 255, 140), width=4)
            d.ellipse([x - r * 0.45, y - r * 0.55, x + r * 0.1, y - r * 0.05], fill=(70, 180, 90))
        return im
    return cache(('map', seed), mk)
GRAVES = None
def graves():
    global GRAVES
    if GRAVES is None:
        rng = np.random.default_rng(38); g = []
        while len(g) < 39:
            x, y = rng.uniform(80, W - 80), rng.uniform(80, H - 80)
            if 1150 < x < 1710 and 110 < y < 430: continue
            if abs(y - (560 + 60 * math.sin(x / 300))) < 70: continue
            if all((x - a) ** 2 + (y - b) ** 2 > 90 ** 2 for a, b in g): g.append((x, y))
        GRAVES = g
    return GRAVES
def draw_grave(d, x, y, n, col=PINK, s=1.0):
    d.ellipse([x - 34 * s, y - 20 * s, x + 34 * s, y + 20 * s], fill=(70, 40, 30), outline=(20, 10, 10), width=3)
    d.line([x, y - 46 * s, x, y + 6 * s], fill=col, width=int(8 * s)); d.line([x - 18 * s, y - 30 * s, x + 18 * s, y - 30 * s], fill=col, width=int(8 * s))

# ---------- props on puppet ----------
def goose(im):
    """goose mask over the puppet head (puppet canvas 320x400, head centre ~ (160,138))"""
    d = ImageDraw.Draw(im)
    cx, cy = 160, 140
    d.ellipse([cx - 72, cy - 78, cx + 72, cy + 70], fill=(250, 250, 245), outline=(20, 18, 30), width=6)
    d.polygon([(cx + 40, cy - 6), (cx + 128, cy + 10), (cx + 40, cy + 34)], fill=(255, 150, 30), outline=(20, 18, 30), width=5)
    d.line([(cx + 46, cy + 14), (cx + 118, cy + 12)], fill=(160, 70, 10), width=3)
    d.ellipse([cx - 4, cy - 36, cx + 26, cy - 6], fill=(15, 15, 20)); d.ellipse([cx + 6, cy - 30, cx + 14, cy - 22], fill=(255, 255, 255))
    d.ellipse([cx - 52, cy - 36, cx - 26, cy - 10], fill=(15, 15, 20))
    # headphones stay (pink)
    d.rounded_rectangle([cx - 86, cy - 20, cx - 62, cy + 30], 8, fill=(255, 70, 160), outline=(20, 18, 30), width=4)
def shovel(im, ang=0):
    sh = Image.new('RGBA', (60, 300), (0, 0, 0, 0)); d = ImageDraw.Draw(sh)
    d.rectangle([24, 0, 36, 220], fill=(140, 90, 50), outline=(20, 18, 30), width=3)
    d.polygon([(6, 214), (54, 214), (50, 280), (30, 298), (10, 280)], fill=(170, 175, 190), outline=(20, 18, 30), width=4)
    sh = sh.rotate(ang, expand=True, resample=Image.BICUBIC)
    im.alpha_composite(sh, (int(250 - sh.width / 2), int(190 - 60)))
