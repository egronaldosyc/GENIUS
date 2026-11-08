# 2D flat "puppet" characters for ТРОПАРЕВО series. Parts are drawn at 2x and cached; per-frame we compose.
import math
import numpy as np
from PIL import Image, ImageDraw

SS = 2  # supersample
OUT = (22, 18, 30)
SKIN = [(242, 200, 170), (236, 190, 160), (230, 186, 150), (245, 210, 180), (226, 178, 145), (240, 196, 166), (232, 192, 158)]

def shade(c, k): return tuple(max(0, min(255, int(v * k))) for v in c)

CHAR = {
    'Егор':   dict(col=(255, 70, 160), hair=(70, 45, 30), hs='mop', skin=0, glasses=True, acc='headphones', prop='shot'),
    'Никита': dict(col=(70, 150, 255), hair=(30, 25, 25), hs='buzz', skin=1, glasses=False, acc='shades', prop='chart'),
    'Фрол':   dict(col=(110, 230, 110), hair=(150, 100, 50), hs='side', skin=3, glasses=False, acc='wizard', prop='d20'),
    'Кирилл': dict(col=(255, 205, 90), hair=(40, 30, 25), hs='short', skin=4, glasses=False, acc='panama', prop='note'),
    'Илья':   dict(col=(170, 110, 255), hair=(60, 40, 30), hs='curly', skin=2, glasses=False, acc=None, prop=None, ghost=True),
    'Юрий':   dict(col=(255, 150, 60), hair=(200, 170, 110), hs='short', skin=5, glasses=True, acc=None, prop='flag'),
    'Коля':   dict(col=(60, 210, 200), hair=(35, 30, 30), hs='side', skin=6, glasses=False, acc='cap', prop='key'),
}

_pc = {}
def _canvas(w, h): return Image.new('RGBA', (w * SS, h * SS), (0, 0, 0, 0))
def _down(im): return im.resize((im.width // SS, im.height // SS), Image.LANCZOS)
def S(*v): return [x * SS for x in v]

def body_im(name):
    k = ('body', name)
    if k in _pc: return _pc[k]
    c = CHAR[name]; col = c['col']; im = _canvas(170, 190); d = ImageDraw.Draw(im)
    # legs
    d.rounded_rectangle(S(52, 130, 80, 188), 10 * SS, fill=(40, 40, 52), outline=OUT, width=4 * SS)
    d.rounded_rectangle(S(90, 130, 118, 188), 10 * SS, fill=(40, 40, 52), outline=OUT, width=4 * SS)
    d.rounded_rectangle(S(46, 176, 84, 190), 6 * SS, fill=(235, 235, 240), outline=OUT, width=3 * SS)
    d.rounded_rectangle(S(86, 176, 124, 190), 6 * SS, fill=(235, 235, 240), outline=OUT, width=3 * SS)
    # torso (hoodie)
    d.rounded_rectangle(S(30, 10, 140, 146), 34 * SS, fill=col, outline=OUT, width=5 * SS)
    d.line(S(85, 40, 85, 140), fill=shade(col, 0.75), width=3 * SS)
    d.rounded_rectangle(S(52, 96, 118, 128), 10 * SS, outline=shade(col, 0.7), width=3 * SS)  # pocket
    d.ellipse(S(60, 4, 110, 30), fill=shade(col, 0.8), outline=OUT, width=4 * SS)  # hood collar
    _pc[k] = _down(im); return _pc[k]

def arm_im(name):
    k = ('arm', name)
    if k in _pc: return _pc[k]
    c = CHAR[name]; col = c['col']; skin = SKIN[c['skin']]
    im = _canvas(40, 110); d = ImageDraw.Draw(im)
    d.rounded_rectangle(S(6, 4, 34, 86), 14 * SS, fill=col, outline=OUT, width=4 * SS)
    d.ellipse(S(4, 76, 36, 108), fill=skin, outline=OUT, width=4 * SS)
    _pc[k] = _down(im); return _pc[k]

def head_im(name, blink=0.0, mouth='smile', look=0.0):
    k = ('head', name, round(blink, 1), mouth, round(look, 1))
    if k in _pc: return _pc[k]
    c = CHAR[name]; skin = SKIN[c['skin']]; hair = c['hair']
    im = _canvas(180, 190); d = ImageDraw.Draw(im)
    cx, cy, r = 90, 108, 62
    hs = c['hs']
    if hs in ('mop', 'curly'):  # back hair
        d.ellipse(S(cx - r - 8, cy - r - 10, cx + r + 8, cy + r - 10), fill=hair, outline=OUT, width=4 * SS)
    # ears
    d.ellipse(S(cx - r - 10, cy - 8, cx - r + 14, cy + 22), fill=skin, outline=OUT, width=4 * SS)
    d.ellipse(S(cx + r - 14, cy - 8, cx + r + 10, cy + 22), fill=skin, outline=OUT, width=4 * SS)
    d.ellipse(S(cx - r, cy - r, cx + r, cy + r), fill=skin, outline=OUT, width=5 * SS)
    # hair front
    if hs == 'mop':
        d.chord(S(cx - r - 4, cy - r - 6, cx + r + 4, cy + 30), 180, 360, fill=hair, outline=OUT, width=4 * SS)
        for i in range(6):
            x = cx - r + 10 + i * 21; d.polygon(S(x, cy - 12, x + 22, cy - 12, x + 11, cy + 8), fill=hair)
    elif hs == 'buzz':
        d.chord(S(cx - r + 2, cy - r + 2, cx + r - 2, cy + 10), 190, 350, fill=hair)
    elif hs == 'side':
        d.chord(S(cx - r - 2, cy - r - 4, cx + r + 2, cy + 20), 180, 360, fill=hair, outline=OUT, width=4 * SS)
        d.polygon(S(cx - r + 6, cy - 14, cx + 30, cy - 30, cx + r - 2, cy - 4, cx + r - 4, cy - 30), fill=hair)
    elif hs == 'short':
        d.chord(S(cx - r, cy - r - 2, cx + r, cy + 6), 185, 355, fill=hair, outline=OUT, width=4 * SS)
    elif hs == 'curly':
        for i in range(8):
            a = math.pi + i * math.pi / 7; x = cx + (r - 6) * math.cos(a); y = cy - 12 + (r - 10) * math.sin(a)
            d.ellipse(S(x - 18, y - 18, x + 18, y + 18), fill=hair, outline=OUT, width=3 * SS)
    # eyes
    ex = 24; ey = cy + 4; lx = look * 6
    for sx in (-1, 1):
        x = cx + sx * ex
        h = max(2, int(17 * (1 - blink)))
        d.ellipse(S(x - 13, ey - h, x + 13, ey + h), fill=(255, 255, 255), outline=OUT, width=3 * SS)
        if blink < 0.7: d.ellipse(S(x - 6 + lx, ey - 6, x + 6 + lx, ey + 6), fill=OUT)
    if c['glasses']:
        for sx in (-1, 1):
            x = cx + sx * ex; d.ellipse(S(x - 20, ey - 20, x + 20, ey + 20), outline=OUT, width=4 * SS)
        d.line(S(cx - 4, ey - 2, cx + 4, ey - 2), fill=OUT, width=4 * SS)
    if c.get('acc') == 'shades':
        d.rounded_rectangle(S(cx - 48, ey - 14, cx - 6, ey + 14), 8 * SS, fill=(15, 15, 25), outline=OUT, width=3 * SS)
        d.rounded_rectangle(S(cx + 6, ey - 14, cx + 48, ey + 14), 8 * SS, fill=(15, 15, 25), outline=OUT, width=3 * SS)
        d.line(S(cx - 6, ey - 6, cx + 6, ey - 6), fill=OUT, width=4 * SS)
        d.line(S(cx - 40, ey - 8, cx - 28, ey - 8), fill=(120, 120, 150), width=3 * SS)
    # cheeks
    d.ellipse(S(cx - 46, cy + 22, cx - 30, cy + 32), fill=(255, 150, 150, 120))
    d.ellipse(S(cx + 30, cy + 22, cx + 46, cy + 32), fill=(255, 150, 150, 120))
    # mouth
    my = cy + 34
    if mouth == 'smile': d.arc(S(cx - 18, my - 14, cx + 18, my + 8), 20, 160, fill=OUT, width=4 * SS)
    elif mouth == 'flat': d.line(S(cx - 14, my, cx + 14, my), fill=OUT, width=4 * SS)
    elif mouth == 'sad': d.arc(S(cx - 16, my, cx + 16, my + 18), 200, 340, fill=OUT, width=4 * SS)
    elif mouth == 'open': d.ellipse(S(cx - 12, my - 8, cx + 12, my + 12), fill=(120, 30, 40), outline=OUT, width=3 * SS)
    elif mouth == 'shout': d.ellipse(S(cx - 18, my - 12, cx + 18, my + 18), fill=(120, 30, 40), outline=OUT, width=4 * SS)
    elif mouth == 'moai': d.rectangle(S(cx - 16, my - 3, cx + 16, my + 3), fill=OUT)
    # hats
    acc = c.get('acc')
    if acc == 'headphones':
        d.arc(S(cx - r - 6, cy - r - 12, cx + r + 6, cy + r - 20), 190, 350, fill=(40, 40, 50), width=9 * SS)
        d.rounded_rectangle(S(cx - r - 16, cy - 16, cx - r + 6, cy + 30), 8 * SS, fill=(255, 70, 160), outline=OUT, width=4 * SS)
        d.rounded_rectangle(S(cx + r - 6, cy - 16, cx + r + 16, cy + 30), 8 * SS, fill=(255, 70, 160), outline=OUT, width=4 * SS)
    elif acc == 'wizard':
        d.polygon(S(cx - 70, cy - 40, cx + 70, cy - 40, cx + 14, cy - 150), fill=(60, 50, 160), outline=OUT, width=4 * SS)
        d.ellipse(S(cx - 80, cy - 52, cx + 80, cy - 30), fill=(60, 50, 160), outline=OUT, width=4 * SS)
        for (sx, sy) in [(-10, -90), (20, -70), (0, -120)]:
            d.regular_polygon((SS * (cx + sx), SS * (cy + sy), 7 * SS), 5, fill=(255, 220, 90))
    elif acc == 'panama':
        d.ellipse(S(cx - 86, cy - 50, cx + 86, cy - 24), fill=(240, 225, 180), outline=OUT, width=4 * SS)
        d.rounded_rectangle(S(cx - 50, cy - 92, cx + 50, cy - 36), 18 * SS, fill=(240, 225, 180), outline=OUT, width=4 * SS)
        d.rectangle(S(cx - 48, cy - 54, cx + 48, cy - 42), fill=(40, 40, 40))
    elif acc == 'cap':
        d.chord(S(cx - r, cy - r - 8, cx + r, cy + 10), 180, 360, fill=(60, 210, 200), outline=OUT, width=4 * SS)
        d.ellipse(S(cx - 6, cy - 46, cx + 76, cy - 30), fill=shade((60, 210, 200), 0.7), outline=OUT, width=4 * SS)
    _pc[k] = _down(im)
    return _pc[k]

def prop_im(kind):
    k = ('prop', kind)
    if k in _pc: return _pc[k]
    im = _canvas(90, 110); d = ImageDraw.Draw(im)
    if kind == 'shot':
        d.polygon(S(22, 30, 68, 30, 62, 100, 28, 100), fill=(220, 240, 255, 170), outline=OUT, width=4 * SS)
        d.polygon(S(25, 50, 65, 50, 62, 96, 28, 96), fill=(255, 190, 60, 220))
    elif kind == 'chart':
        d.rounded_rectangle(S(4, 20, 86, 96), 8 * SS, fill=(250, 250, 250), outline=OUT, width=4 * SS)
        d.line(S(12, 80, 30, 66, 46, 74, 62, 46, 78, 36), fill=(30, 170, 80), width=5 * SS)
        d.text((SS * 12, SS * 24), 'GAZP', fill=(40, 90, 200))
    elif kind == 'd20':
        pts = [(45 + 40 * math.cos(math.pi / 6 + i * math.pi / 3), 60 + 40 * math.sin(math.pi / 6 + i * math.pi / 3)) for i in range(6)]
        d.polygon([(SS * x, SS * y) for x, y in pts], fill=(200, 40, 50), outline=OUT, width=4 * SS)
        d.polygon(S(45, 28, 76, 78, 14, 78), outline=(255, 200, 200), width=3 * SS)
    elif kind == 'note':
        d.rounded_rectangle(S(14, 16, 78, 100), 6 * SS, fill=(250, 245, 225), outline=OUT, width=4 * SS)
        for j in range(5): d.line(S(22, 34 + j * 13, 70, 34 + j * 13), fill=(120, 140, 200), width=2 * SS)
    elif kind == 'flag':
        d.line(S(20, 6, 20, 106), fill=OUT, width=5 * SS)
        d.polygon(S(22, 8, 88, 22, 22, 46), fill=(255, 150, 60), outline=OUT, width=3 * SS)
    elif kind == 'key':
        d.ellipse(S(16, 20, 52, 56), outline=(230, 190, 60), width=8 * SS)
        d.line(S(48, 50, 80, 88), fill=(230, 190, 60), width=8 * SS); d.line(S(68, 76, 60, 84), fill=(230, 190, 60), width=6 * SS)
    _pc[k] = _down(im); return _pc[k]

def _paste_rot(c, im, px, py, ang, ax, ay):
    # rotate im about its local anchor (ax, ay) and paste so the anchor lands at (px, py)
    if abs(ang) < 0.5:
        c.alpha_composite(im, (int(px - ax), int(py - ay))) if px - ax >= 0 and py - ay >= 0 else _safe(c, im, px - ax, py - ay); return
    w, h = im.size; R = int(math.hypot(max(ax, w - ax), max(ay, h - ay))) + 2
    big = Image.new('RGBA', (2 * R, 2 * R), (0, 0, 0, 0)); big.alpha_composite(im, (int(R - ax), int(R - ay)))
    big = big.rotate(ang, resample=Image.BICUBIC)
    _safe(c, big, px - R, py - R)

def _safe(c, im, x, y):
    x, y = int(x), int(y); sx, sy = max(0, -x), max(0, -y)
    if sx >= im.width or sy >= im.height or x >= c.width or y >= c.height: return
    if sx or sy: im = im.crop((sx, sy, im.width, im.height))
    c.alpha_composite(im, (x + sx, y + sy))

def puppet(name, t, pose='idle', talk=False, mouth=None, look=0.0, walk=0.0, prop=True, seed=0):
    """Return RGBA image (220x380) of the character; feet at bottom center (110, 372)."""
    c = CHAR[name]; im = Image.new('RGBA', (320, 400), (0, 0, 0, 0))
    ph = t * 2 * math.pi
    bob = 3 * math.sin(ph * 0.9 + seed)
    if walk: bob = 6 * abs(math.sin(ph * walk))
    bl = 0.0; bt = (t * 0.7 + seed * 0.37) % 3.1
    if bt < 0.14: bl = 1 - abs(bt - 0.07) / 0.07
    if mouth is None:
        mouth = 'smile'
        if talk: mouth = ['open', 'flat', 'shout', 'open', 'flat'][int(t * 11 + seed) % 5]
        if name == 'Никита' and not talk: mouth = 'moai'
    body = body_im(name); arm = arm_im(name); head = head_im(name, bl, mouth, look)
    bx, by = 75, 400 - 8 - 190  # body top-left
    # arm angles
    if pose == 'idle': la, ra = 8 + 4 * math.sin(ph * 0.9), -8 - 4 * math.sin(ph * 0.9 + 1)
    elif pose == 'wave': la, ra = 8, -150 + 25 * math.sin(ph * 2.2)
    elif pose == 'hype': la, ra = 150 + 20 * math.sin(ph * 2), -150 - 20 * math.sin(ph * 2)
    elif pose == 'point': la, ra = 8, -95
    elif pose == 'drink': la, ra = 8, -130 + 10 * math.sin(ph * 0.5)
    elif pose == 'shrug': la, ra = 60, -60
    elif pose == 'sad': la, ra = 2, -2
    else: la, ra = 8, -8
    if walk: la, ra = 25 * math.sin(ph * walk), -25 * math.sin(ph * walk)
    la, ra = -la, -ra
    oy = -bob
    _paste_rot(im, arm, bx + 34, by + 40 + oy, la, 20, 12)                    # left arm (behind)
    _safe(im, body, bx, by + oy)
    hy = by - 150 + oy + (4 if pose == 'sad' else 0)
    _safe(im, head, bx + 85 - 90, hy)
    # right arm with prop
    ang = ra; sx, sy = bx + 136, by + 40 + oy
    if prop and c.get('prop'):
        p = prop_im(c['prop'])
        hx = sx + 80 * math.sin(math.radians(ang)); hy2 = sy + 80 * math.cos(math.radians(ang))
        _safe(im, p, hx - 30, hy2 - 78)
    _paste_rot(im, arm, sx, sy, ang, 20, 12)
    if c.get('ghost'):
        a = np.array(im); a[..., 3] = (a[..., 3] * (0.55 + 0.2 * math.sin(ph * 0.6))).astype(np.uint8); im = Image.fromarray(a)
    return im

if __name__ == '__main__':
    W, H = 1500, 460
    c = Image.new('RGBA', (W, H), (30, 32, 44, 255))
    poses = ['idle', 'wave', 'point', 'hype', 'drink', 'shrug', 'idle']
    for i, n in enumerate(CHAR):
        p = puppet(n, 0.3 + i * 0.1, poses[i], talk=(i % 2 == 0), seed=i)
        c.alpha_composite(p, (i * 210 - 40, 40))
    c.convert('RGB').save('lineup.jpg', quality=90)
