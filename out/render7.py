import os, sys, math, random, subprocess, wave
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
for p in (SP, os.path.join(SP, 'v2'), os.path.join(SP, 'v4'), os.path.join(SP, 'v5')): sys.path.insert(0, p)
import render as R
import render3 as R3
import render4 as R4
from render import W, H, font, text_img, paste, ease_pop, glitch_slices, F_BLACK, F_MONO, F_SYM, WHITE, BLACK, CAN
from render3 import zoomc, rgbsplit, P, flash

FPS, SR = 30, 44100
AMBER = (255, 176, 60); TERM = (210, 225, 210); REDC = (220, 30, 30); PAPER = (236, 233, 222); INKC = (25, 25, 28)
FM = lambda s: font(F_MONO, s)

def V1(t): return cv2.cvtColor(R.src_frame(t * 30), cv2.COLOR_BGR2RGB)
C, C2, A, E = R3.cframe, R4.c2, R3.aframe, R3.eframe
SELFIE, BILL, POST = R3.IMG_SELFIE, R3.IMG_BILL, R4.POST

SHOTS = [('boot', 4.0), ('doc', 6.5), ('cctv', 6.0), ('evid', 4.5), ('ihead', 1.2),
         ('iq', 2.65, dict(q='Сколько часов в сутки\nвы спите?', src='c2', a=28.15, b=29.5)),
         ('iq', 5.05, dict(q='Что означает слово\n«абракадабра»?', src='a', a=6.5, b=10.35)),
         ('iq', 4.2, dict(q='Чего вы хотите?', src='c2', a=20.45, b=23.45)),
         ('exp', 7.67), ('inc', 9.2), ('add', 6.6), ('end', 4.0)]
SHOTS = [s if len(s) == 3 else (s[0], s[1], {}) for s in SHOTS]
STARTS = []; _t = 0
for s in SHOTS: STARTS.append(_t); _t += s[1]
T_END = _t; N = int(round(T_END * FPS))
def shot_at(t):
    for i, s in enumerate(SHOTS):
        if t < STARTS[i] + s[1]: return i, t - STARTS[i]
    return len(SHOTS) - 1, SHOTS[-1][1] - 1e-3

# ---------------- visual helpers ----------------
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 1.0 * (np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2) - 0.5), 0.25, 1)[..., None]
def crt(img, t, amt=1.0, green=False):
    x = img.astype(np.float32)
    if green: g = x.mean(2, keepdims=True); x = np.concatenate([g * 0.75, g * 1.0, g * 0.8], 2)
    x[::2] *= 1 - 0.22 * amt
    x *= VIG
    rng = np.random.default_rng(int(t * 1000))
    x += rng.normal(0, 7 * amt, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return np.clip(x, 0, 255).astype(np.uint8)
def cctv(img, t, cam='CAM-03', sector='СЕКТОР-19', ts='07:40:00'):
    g = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY); g = cv2.equalizeHist(g)
    x = cv2.cvtColor(g, cv2.COLOR_GRAY2RGB).astype(np.float32) * np.array([0.85, 1.0, 0.9])
    x = cv2.resize(cv2.resize(x, (W // 2, H // 2)), (W, H))
    return crt(x, t, 1.2)
def emblem(size, col=(235, 235, 235), bg=(0, 0, 0, 0)):
    s = size; im = Image.new('RGBA', (s, s), bg); d = ImageDraw.Draw(im); c = s / 2
    d.ellipse([s * 0.03, s * 0.03, s * 0.97, s * 0.97], outline=col, width=int(s * 0.07))
    d.ellipse([s * 0.36, s * 0.36, s * 0.64, s * 0.64], outline=col, width=int(s * 0.05))
    for k in range(3):
        a = math.radians(-90 + k * 120)
        def pt(r, da=0): return (c + r * math.cos(a + da), c + r * math.sin(a + da))
        d.polygon([pt(s * 0.45, -0.13), pt(s * 0.45, 0.13), pt(s * 0.33, 0.13), pt(s * 0.33, 0.27), pt(s * 0.19, 0), pt(s * 0.33, -0.27), pt(s * 0.33, -0.13)], fill=col)
    return im
EMB = emblem(300); EMB_S = emblem(90); EMB_DARK = emblem(110, INKC)

def redline(d, x, y, line, fo, col, shown=None, bar=None):
    """draw line where segments wrapped in ‹…› are redaction bars"""
    parts = []; buf = ''; red = False
    for ch in line:
        if ch == '‹': parts.append((buf, red)); buf = ''; red = True
        elif ch == '›': parts.append((buf, red)); buf = ''; red = False
        else: buf += ch
    parts.append((buf, red))
    total = 0; cx = x
    for txt, rd in parts:
        if shown is not None and total >= shown: break
        n = len(txt) if shown is None else min(len(txt), shown - total)
        seg = txt[:n]; wdt = d.textlength(seg, font=fo)
        if rd: d.rectangle([cx, y - 2, cx + wdt, y + fo.size + 4], fill=bar or ((0, 0, 0) if sum(col) < 200 else (215, 215, 215)))
        else: d.text((cx, y), seg, font=fo, fill=col)
        cx += wdt; total += len(txt)
    return total
def typed(d, x, y, lines, tl, t0, cps, fo, col, lh):
    budget = int(max(0, tl - t0) * cps)
    for j, l in enumerate(lines):
        if budget <= 0: break
        L = len(l.replace('‹', '').replace('›', ''))
        redline(d, x, y + j * lh, l, fo, col, budget)
        budget -= L
    return budget
def stamp(c, txt, cx, cy, tl, t0, rot=-12, col=REDC, size=64):
    s = ease_pop(tl, t0, 0.1)
    if s <= 0: return
    im = text_img(txt, size, col, col, 0, f=F_BLACK)
    fr = Image.new('RGBA', (im.width + 40, im.height + 26), (0, 0, 0, 0))
    ImageDraw.Draw(fr).rectangle([4, 4, fr.width - 5, fr.height - 5], outline=col + (255,), width=7); fr.alpha_composite(im, (20, 13))
    a = np.array(fr); m = np.random.default_rng(len(txt)).random(a.shape[:2]) < 0.2; a[m, 3] = (a[m, 3] * 0.35).astype(np.uint8)
    paste(c, Image.fromarray(a), cx, cy, s * (1 + 0.6 * max(0, 1 - (tl - t0) / 0.1)), rot, 0.9)
def deleted_block(c, cx, cy, tl, t0, w=620, size=58):
    s = ease_pop(tl, t0, 0.08)
    if s <= 0: return
    b = Image.new('RGBA', (w, size + 44), (0, 0, 0, 255)); d = ImageDraw.Draw(b)
    d.text((w / 2, (size + 44) / 2), '[ДАННЫЕ УДАЛЕНЫ]', font=font(F_BLACK, size), fill=WHITE, anchor='mm')
    paste(c, b, cx, cy, s)
def term_bg(t):
    x = np.full((H, W, 3), (10, 14, 12), np.uint8); return x
def paper(t):
    rng = np.random.default_rng(3)
    x = np.full((H, W, 3), PAPER, np.float32) + rng.normal(0, 4, (H, W, 1))
    x *= (0.92 + 0.08 * VIG)
    return np.clip(x, 0, 255).astype(np.uint8)
def doc_header(c, title, sub=None):
    d = ImageDraw.Draw(c)
    c.alpha_composite(EMB_DARK, (36, 40))
    d.text((165, 52), 'ФОНД SCP', font=font(F_BLACK, 44), fill=INKC)
    d.text((165, 104), 'ОБЕСПЕЧИТЬ · УДЕРЖАТЬ · СОХРАНИТЬ', font=FM(20), fill=(80, 80, 80))
    d.rectangle([36, 170, W - 36, 174], fill=INKC)
    d.text((36, 190), title, font=font(F_BLACK, 40), fill=INKC)
    if sub: d.text((36, 240), sub, font=FM(24), fill=(70, 70, 70))
def ui_badge(c, txt, x, y, col=REDC):
    t = text_img(txt, 26, WHITE, col, 0, f=F_MONO); b = Image.new('RGBA', (t.width + 16, t.height + 4), col + (255,)); b.alpha_composite(t, (8, 2)); paste(c, b, x + b.width / 2, y)
def monitor(c, img, t, label):
    # CRT monitor with clip inside
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([30, 330, W - 30, 1030], 30, fill=(40, 42, 40), outline=(90, 92, 90), width=6)
    sx, sy, sw, shh = 60, 360, W - 120, 640
    h0 = img.shape[0]; crop = img[int(h0 * 0.12):int(h0 * 0.12) + int(img.shape[1] * shh / sw)]
    scr = cv2.resize(crop, (sw, shh))
    g = cv2.cvtColor(scr, cv2.COLOR_RGB2GRAY).astype(np.float32)
    scr = np.stack([g * 0.9, g * 1.0, g * 0.92], -1); scr[::2] *= 0.8
    scr = np.clip(scr * (0.95 + 0.05 * math.sin(t * 50)), 0, 255).astype(np.uint8)
    m = Image.new('L', (sw, shh), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, sw - 1, shh - 1], 40, fill=255)
    c.paste(Image.fromarray(scr), (sx, sy), m)
    d.text((W / 2, 1000), label, font=FM(22), fill=(200, 200, 200), anchor='mm')

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; i, tl = shot_at(t); key, dur, kw = SHOTS[i]
    rng = random.Random(fi * 41); c = None
    if key == 'boot':
        c = P(term_bg(t)); d = ImageDraw.Draw(c)
        lines = ['> SCP FOUNDATION SECURE TERMINAL v4.8.48', '> ПОДКЛЮЧЕНИЕ К ЗОНЕ-19 ......... OK', '> ЗАПРОС: ФАЙЛ SCP-848',
                 '> УРОВЕНЬ ДОПУСКА: 4', '> ПРОВЕРКА ДОПУСКА ...']
        typed(d, 40, 120, lines, tl, 0.1, 55, FM(24), TERM, 40)
        if tl > 2.4:
            ok = text_img('ДОСТУП РАЗРЕШЁН', 60, (120, 255, 140), BLACK, 0, f=F_MONO)
            if int(tl * 6) % 2 or tl > 3.0: paste(c, ok, W / 2, 470)
            paste(c, EMB, W / 2, 820, ease_pop(tl, 2.6, 0.25))
            d.text((W / 2, 1010), 'ОБЕСПЕЧИТЬ · УДЕРЖАТЬ · СОХРАНИТЬ', font=FM(26), fill=TERM, anchor='mm')
        if int(tl * 2) % 2 == 0 and tl < 2.4: d.rectangle([40, 120 + 40 * 5, 56, 150 + 40 * 5], fill=TERM)
        c = P(crt(np.array(c.convert('RGB')), t, 0.8))
    elif key == 'doc':
        c = P(paper(t)); doc_header(c, 'Объект №: SCP-848', 'Класс объекта: ЕВКЛИД')
        ph = cv2.cvtColor(cv2.cvtColor(SELFIE[120:1000, 60:660], cv2.COLOR_RGB2GRAY), cv2.COLOR_GRAY2RGB)
        ph = Image.fromarray(cv2.resize(ph, (220, 322))).convert('RGBA')
        d = ImageDraw.Draw(c)
        d.rectangle([W - 266, 280, W - 34, 614], fill=(255, 255, 255), outline=INKC, width=3); c.alpha_composite(ph, (W - 260, 286))
        d.text((W - 150, 632), 'SCP-848, фото ‹1›'.replace('‹1›', '19██ г.'), font=FM(18), fill=(70, 70, 70), anchor='mm')
        d.text((36, 300), 'Особые условия', font=font(F_BLACK, 32), fill=INKC); d.text((36, 340), 'содержания:', font=font(F_BLACK, 32), fill=INKC)
        lines = ['SCP-848 должен ежедневно', 'получать 1 (одну) банку', 'энергетика объёмом ‹0.45› л.', 'Персоналу запрещено', 'отвечать на пожелания',
                 'объекта «хорошего вечера».', '', 'При задержке поставки', 'объект произносит фразу', '«без энергии я умру»,', 'после чего ']
        typed(d, 36, 670, lines[:6], tl, 0.4, 48, FM(28), INKC, 42)
        typed(d, 36, 670 + 42 * 6, lines[6:], tl, 0.4 + sum(len(l) for l in lines[:6]) / 48, 48, FM(28), INKC, 42)
        if tl > 5.2: deleted_block(c, W / 2, 1200, tl, 5.2, 600, 50)
        stamp(c, 'СОВЕРШЕННО\nСЕКРЕТНО', 190, 500, tl, 1.0, -10, REDC, 38)
    elif key == 'cctv':
        cams = [(V1, 1.0 + tl, 'CAM-01 · ПОДЪЕЗД'), (C2, 3.0 + tl, 'CAM-02 · ДВОР'), (C2, 88.75 + tl * 0.8, 'CAM-03 · МАГАЗИН'), (C, 16.0 + tl, 'CAM-04 · ДОРОГА')]
        full = tl > 3.6
        out = np.zeros((H, W, 3), np.uint8)
        if not full:
            for j, (fn, st, lab) in enumerate(cams):
                f = cv2.resize(fn(st), (W // 2, H // 2)); out[(j // 2) * (H // 2):(j // 2 + 1) * (H // 2), (j % 2) * (W // 2):(j % 2 + 1) * (W // 2)] = f
        else:
            out = V1(1.0 + tl)
        c = P(cctv(out, t)); d = ImageDraw.Draw(c)
        if not full:
            for j, (_, _, lab) in enumerate(cams):
                d.text(((j % 2) * W / 2 + 12, (j // 2) * H / 2 + 12), lab, font=FM(20), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
                d.text(((j % 2) * W / 2 + 12, (j // 2) * H / 2 + 38), f'07:4{j}:{int(tl*10)%60:02d}', font=FM(20), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
            d.line([(W / 2, 0), (W / 2, H)], fill=(0, 0, 0), width=4); d.line([(0, H / 2), (W, H / 2)], fill=(0, 0, 0), width=4)
        else:
            d.text((20, 20), 'CAM-01 · ПОДЪЕЗД · 07:40:00', font=FM(24), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
            # target box
            bx, by = W / 2, 560
            d.rectangle([bx - 160, by - 230, bx + 160, by + 230], outline=REDC, width=4)
            d.text((bx - 160, by - 262), 'SCP-848 · ОБНАРУЖЕН', font=FM(26), fill=REDC, stroke_width=2, stroke_fill=BLACK)
        box = Image.new('RGBA', (W - 40, 230), (0, 0, 0, 215)); bd = ImageDraw.Draw(box)
        bd.text((20, 14), 'ОПИСАНИЕ:', font=font(F_BLACK, 30), fill=AMBER)
        typed(bd, 20, 58, ['Ежедневно в 07:40 объект совершает', 'перемещение «дом → работа → дом».', 'Попытки прервать маршрут привели', 'к ‹████████› и ‹██████████›.'], tl, 0.3, 48, FM(24), WHITE, 38)
        c.alpha_composite(box, (20, H - 270))
    elif key == 'evid':
        c = P(paper(t)); doc_header(c, 'Вещественные доказательства', 'изъято при обыске места обитания')
        items = [('p0833', '848-A', 'макароны, чай, таблетки'), ('p1453', '848-B', 'тортик (1 шт.)'), ('p2355', '848-C', 'лапша быстр. пригот.'), ('p1243', '848-D', 'банка «банановый вайб»')]
        for j, (k, tag, desc) in enumerate(items):
            t0 = 0.3 + j * 0.7
            s = ease_pop(tl, t0, 0.15)
            if s <= 0: continue
            im = POST[k].copy(); im.thumbnail((300, 360))
            card = Image.new('RGBA', (im.width + 20, im.height + 90), (255, 255, 255, 255)); card.paste(im, (10, 10))
            cd = ImageDraw.Draw(card); cd.text((14, im.height + 18), f'ОБРАЗЕЦ {tag}', font=font(F_BLACK, 26), fill=INKC); cd.text((14, im.height + 52), desc, font=FM(18), fill=(60, 60, 60))
            x = 190 + (j % 2) * 340; y = 520 + (j // 2) * 450
            paste(c, card, x, y, s * 0.95, (-1) ** j * 3)
        if tl > 3.4: stamp(c, 'ОПАСНО ДЛЯ ЖКТ', W / 2, 1210, tl, 3.4, -6, REDC, 44)
    elif key == 'ihead':
        c = P(paper(t)); doc_header(c, 'Протокол интервью 848-3')
        d = ImageDraw.Draw(c)
        for j, l in enumerate(['Опрашиваемый: SCP-848', 'Интервьюер: д-р ‹███████›', 'Дата: ‹██.██.20██›']):
            redline(d, 36, 320 + j * 50, l, FM(30), INKC)
        d.text((36, 520), '<Начало записи>', font=FM(30), fill=(90, 90, 90))
    elif key == 'iq':
        q = kw['q']; qd = 1.2
        c = P(paper(t)); d = ImageDraw.Draw(c)
        d.text((36, 60), 'ПРОТОКОЛ 848-3 · АУДИОВИДЕОЗАПИСЬ', font=FM(24), fill=(90, 90, 90))
        redline(d, 36, 140, 'Д-р ‹██████›:', font(F_BLACK, 34), INKC)
        typed(d, 36, 195, q.split('\n'), tl, 0.0, 70, font(F_BLACK, 40), INKC, 52)
        if tl > qd:
            st = kw['a'] + (tl - qd); img = {'c2': C2, 'a': A}[kw['src']](min(kw['b'], st))
            monitor(c, img, t, 'АРХИВ ЗОНЫ-19 · ЗАПИСЬ ' + f'{int((tl-qd)*100):05d}')
            d.text((36, 1060), 'SCP-848:', font=font(F_BLACK, 34), fill=INKC)
            d.text((36, 1110), '[ответ приобщён к делу]', font=FM(28), fill=(90, 90, 90))
        c = P(np.array(c.convert('RGB')))
    elif key == 'exp':
        if tl < 1.0:
            c = P(paper(t)); doc_header(c, 'Журнал экспериментов'); d = ImageDraw.Draw(c)
            for j, l in enumerate(['Эксперимент 848-7', 'Процедура: объекту предложено', 'заняться спортом.', 'Наблюдатель: ‹███████›']):
                redline(d, 36, 320 + j * 50, l, FM(30) if j else font(F_BLACK, 36), INKC)
        else:
            u = tl - 1.0
            if u < 1.72: st = 73.9 + u * 6; spd = '×6'
            elif u < 1.72 + 3.65: st = 84.3 + (u - 1.72); spd = '×1'
            else: st = 87.9; spd = 'ПАУЗА'
            img = C(st); c = P(cctv(img, t)); d = ImageDraw.Draw(c)
            d.text((20, 20), f'НАБЛЮДЕНИЕ · ЭКСП. 848-7 · {spd}', font=FM(24), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
            el = min(10.3, u * 6) if u < 1.72 else 10.3
            d.text((W - 20, 20), f'00:{int(el):02d}.{int(el*10)%10}', font=FM(30), fill=AMBER, anchor='ra', stroke_width=2, stroke_fill=BLACK)
            if u > 1.72 + 3.65:
                box = Image.new('RGBA', (W - 40, 200), (0, 0, 0, 225)); bd = ImageDraw.Draw(box)
                bd.text((20, 16), 'РЕЗУЛЬТАТ:', font=font(F_BLACK, 32), fill=AMBER)
                bd.text((20, 64), 'Продолжительность: 10 с.', font=FM(28), fill=WHITE)
                redline(bd, 20, 108, 'Объект ‹███████████› и ушёл есть.', FM(28), WHITE)
                c.alpha_composite(box, (20, H - 260))
    elif key == 'inc':
        alarm = (int(tl * 3) % 2 == 0)
        if tl < 1.0:
            c = P(term_bg(t)); d = ImageDraw.Draw(c)
            d.text((W / 2, 560), 'ИНЦИДЕНТ 848-Б', font=font(F_BLACK, 64), fill=REDC, anchor='mm')
            d.text((W / 2, 640), 'запись камеры объекта, 21:47', font=FM(28), fill=TERM, anchor='mm')
            c = P(crt(np.array(c.convert('RGB')), t))
        else:
            u = tl - 1.0
            if u < 4.0: st = 195.0 + u
            elif u < 7.0: st = 207.5 + (u - 4.0)
            else: st = None
            if st is not None:
                img = C2(st); x = cctv(img, t)
                if rng.random() < 0.15: x = glitch_slices(x, rng, 6, 60)
                c = P(x)
            else:
                nz = np.random.default_rng(fi).integers(0, 200, (H // 4, W // 4, 1), dtype=np.uint8).repeat(4, 0).repeat(4, 1).repeat(3, 2)
                c = P(nz); d = ImageDraw.Draw(c); d.rectangle([0, H / 2 - 60, W, H / 2 + 60], fill=(0, 0, 0))
                d.text((W / 2, H / 2), 'СИГНАЛ ПОТЕРЯН', font=FM(56), fill=WHITE, anchor='mm')
            d = ImageDraw.Draw(c)
            if alarm: c.alpha_composite(Image.new('RGBA', (W, H), (220, 0, 0, 55)))
            bar = Image.new('RGBA', (W, 70), (180, 0, 0, 230)); ImageDraw.Draw(bar).text((W / 2, 35), '⚠ НАРУШЕНИЕ УСЛОВИЙ СОДЕРЖАНИЯ ⚠', font=font(F_SYM, 30), fill=WHITE, anchor='mm')
            c.alpha_composite(bar, (0, 110))
            ImageDraw.Draw(c).text((20, 20), 'SCP-848 · НОЧНАЯ ФАЗА', font=FM(24), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
            if 4.0 <= u < 7.0 and u > 5.0:
                box = Image.new('RGBA', (W - 40, 120), (0, 0, 0, 220)); bd = ImageDraw.Draw(box)
                redline(bd, 20, 20, 'Камера уронена. Местонахождение', FM(26), WHITE); redline(bd, 20, 60, 'объекта: ‹██████████████›', FM(26), WHITE)
                c.alpha_composite(box, (20, H - 200))
    elif key == 'add':
        if tl < 3.5:
            img = BILL.copy(); z = 1.6 - 0.5 * min(1, tl / 2.5)
            img = zoomc(img, z, 520 - 66, 600)
            c = P(cctv(img, t)); d = ImageDraw.Draw(c)
            d.text((20, 20), 'СПУТНИК-7 · ███-ЙОРК', font=FM(26), fill=WHITE, stroke_width=2, stroke_fill=BLACK)
            cx, cy = W / 2, 640; r = 140 + 20 * math.sin(tl * 6)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=REDC, width=4); d.line([(cx - r - 40, cy), (cx + r + 40, cy)], fill=REDC, width=2); d.line([(cx, cy - r - 40), (cx, cy + r + 40)], fill=REDC, width=2)
            box = Image.new('RGBA', (W - 40, 220), (0, 0, 0, 220)); bd = ImageDraw.Draw(box)
            bd.text((20, 14), 'ДОПОЛНЕНИЕ 848-1:', font=font(F_BLACK, 30), fill=AMBER)
            typed(bd, 20, 60, ['Изображение объекта обнаружено', 'на рекламном щите, ‹███-Йорк›.', 'Объект не покидал Зону-19.'], tl, 0.4, 40, FM(26), WHITE, 40)
            c.alpha_composite(box, (20, H - 260))
        elif tl < 3.5 + 1.93:
            u = tl - 3.5; img = E(0.2 + u * 0.6)
            img = rgbsplit(img, 20 + 30 * rng.random()); img = glitch_slices(img, rng, 12, 160)
            x = img.astype(np.float32); g = x.mean(2, keepdims=True); x = np.clip((g - 80) * 2.2 + 110, 0, 255)
            c = P(np.concatenate([x, x * 0.3, x * 0.3], 2).astype(np.uint8) if int(t * 15) % 2 else x.repeat(3, 2).astype(np.uint8))
            bar = Image.new('RGBA', (W, 120), (0, 0, 0, 235)); bd = ImageDraw.Draw(bar)
            bd.text((W / 2, 36), 'ВНИМАНИЕ: МЕМЕТИЧЕСКАЯ УГРОЗА', font=font(F_BLACK, 34), fill=REDC, anchor='mm')
            bd.text((W / 2, 84), 'не повторяйте услышанную фразу', font=FM(26), fill=WHITE, anchor='mm')
            c.alpha_composite(bar, (0, 100))
        else:
            u = tl - 3.5 - 1.93
            c = P(term_bg(t)); deleted_block(c, W / 2, H / 2, u, 0.0, 680, 62)
            c = P(crt(np.array(c.convert('RGB')), t))
    elif key == 'end':
        c = P(term_bg(t)); d = ImageDraw.Draw(c)
        typed(d, 40, 160, ['> ФАЙЛ SCP-848 ЗАКРЫТ', '> ОСТАЛЬНЫЕ МАТЕРИАЛЫ:', '  [ДАННЫЕ УДАЛЕНЫ]', '> ДОПУСК ДЛЯ ПРОСМОТРА:', '  НЕДОСТАТОЧЕН'], tl, 0.1, 40, FM(30), TERM, 50)
        paste(c, EMB, W / 2, 780, ease_pop(tl, 1.4, 0.25))
        if tl > 2.2: d.text((W / 2, 1000), 'объект желает вам хорошего вечера', font=FM(26), fill=(150, 150, 150), anchor='mm')
        if tl > 2.6: d.text((W / 2, 1050), '[не отвечать]', font=FM(26), fill=REDC, anchor='mm')
        c = P(crt(np.array(c.convert('RGB')), t))
        if dur - tl < 0.25: c = P(np.zeros((H, W, 3), np.uint8))
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    n = int(T_END * SR) + SR; mix = np.zeros(n, np.float32); rng = np.random.default_rng(8)
    LW = R3.load_wav
    AU = {'c': LW(os.path.join(SP, 'v4', 'au_c.wav')), 'a': LW(os.path.join(SP, 'v4', 'au_a.wav')), 'e': LW(os.path.join(SP, 'v4', 'au_e.wav')),
          'c2': LW(os.path.join(SP, 'v5', 'au_c2.wav')), 'v1': LW(os.path.join(SP, 'v4', 'v1.wav'))}
    VO = {k: LW(os.path.join(HERE, 'vo', f'{k}.wav')) for k in ['open', 'cls', 'del', 'int', 'exp', 'pa', 'add', 'meme', 'end']}
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or len(sig) == 0: return
        j = min(n, i + len(sig)); mix[i:j] += g * sig[:j - i]
    def clip(src, s0, s1, sp=1.0, fade=0.01):
        a = AU[src]; m = int((s1 - s0) / sp * SR); pos = s0 * SR + np.arange(m) * sp
        x = np.interp(np.clip(pos, 0, len(a) - 1), np.arange(len(a)), a).astype(np.float32); f = int(fade * SR)
        if len(x) > 2 * f: x[:f] *= np.linspace(0, 1, f); x[-f:] *= np.linspace(1, 0, f)
        return x
    def tt(d): return np.arange(int(d * SR)) / SR
    def archive(x):  # telephone-band + hiss
        X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1 / SR); X[(f < 300) | (f > 3400)] *= 0.08
        y = np.fft.irfft(X, len(x)).astype(np.float32); y = np.tanh(y * 2.0) * 0.6
        return y + rng.standard_normal(len(y)).astype(np.float32) * 0.012
    def pa(x):
        y = archive(x); z = y.copy()
        for dl, g in ((0.09, .45), (0.19, .3), (0.31, .2)): k = int(dl * SR); z[k:] += g * y[:-k]
        return z
    def beep(f=1200, d=0.07): t = tt(d); return (0.25 * np.sin(2 * np.pi * f * t) * np.minimum(1, (d - t) / 0.005)).astype(np.float32)
    def click(): t = tt(0.012); return (rng.standard_normal(len(t)) * np.exp(-t * 600) * 0.25).astype(np.float32)
    def siren(d):
        t = tt(d); f = 600 + 300 * np.sin(2 * np.pi * 0.75 * t)
        return (0.16 * np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * np.minimum(1, t / 0.2)).astype(np.float32)
    def boom(d=1.0, f0=90):
        t = tt(d); f = f0 * np.exp(-t * 4) + 32; return np.tanh(2.5 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.5)).astype(np.float32)
    def thunk():
        t = tt(0.2); return (np.tanh(3 * np.sin(2 * np.pi * 70 * t) * np.exp(-t * 30)) + rng.standard_normal(len(t)) * 0.2 * np.exp(-t * 50)).astype(np.float32)
    # facility hum bed
    t = tt(T_END); hum = (np.sin(2 * np.pi * 50 * t) * 0.05 + np.sin(2 * np.pi * 100 * t) * 0.03 + np.sin(2 * np.pi * 150 * t) * 0.015)
    vent = np.convolve(rng.standard_normal(len(t)), np.ones(200) / 200, 'same') * 0.35
    bed = (hum + vent).astype(np.float32); f = int(0.5 * SR); bed[:f] *= np.linspace(0, 1, f); bed[-f:] *= np.linspace(1, 0, f)
    add(0, bed)
    S = {};
    for i, s in enumerate(SHOTS): S.setdefault(s[0], []).append(STARTS[i])
    # boot: clicks + beeps
    for k in range(int(2.3 * 55 / 3)): add(0.1 + k * 3 / 55, click(), 0.8)
    add(2.4, beep(880, 0.1), 1); add(2.52, beep(1320, 0.14), 1); add(2.6, boom(1.2, 70), 0.6); add(2.7, VO['open'], 0.9)
    s0 = S['doc'][0]; add(s0 + 0.2, VO['cls'], 0.9)
    for k in range(int(4.8 * 42 / 3)): add(s0 + 0.4 + k * 3 / 42, click(), 0.5)
    add(s0 + 1.0, thunk(), 0.9); add(s0 + 5.2, thunk(), 1.0); add(s0 + 5.3, VO['del'], 1.0)
    s0 = S['cctv'][0]; add(s0, archive(clip('v1', 1.0, 4.6)) * 0.4, 1); add(s0 + 3.6, beep(1000, 0.08), 1)
    for k in range(int(4.5 * 48 / 3)): add(s0 + 0.3 + k * 3 / 48, click(), 0.4)
    s0 = S['evid'][0]
    for j in range(4): add(s0 + 0.3 + j * 0.7, thunk(), 0.6)
    add(s0 + 3.4, thunk(), 1.0)
    add(S['ihead'][0] + 0.1, VO['int'], 0.9)
    for i, (k, d, kw) in enumerate(SHOTS):
        if k == 'iq':
            s0 = STARTS[i]
            for q in range(int(1.0 * 40 / 3)): add(s0 + q * 3 / 40, click(), 0.4)
            add(s0 + 1.2, archive(clip(kw['src'], kw['a'], kw['b'])), 1.3); add(s0 + 1.2, beep(1500, 0.05), 0.7)
    s0 = S['exp'][0]; add(s0 + 0.05, VO['exp'], 0.9)
    add(s0 + 1.0, archive(clip('c', 73.9, 73.9 + 1.72 * 6, 6.0)) * 0.6, 1)
    add(s0 + 2.72, archive(clip('c', 84.3, 87.95)), 1.3); add(s0 + 6.4, thunk(), 0.8)
    s0 = S['inc'][0]; add(s0 + 1.0, siren(8.2), 1.0); add(s0 + 1.1, pa(VO['pa']), 1.0)
    add(s0 + 1.0, archive(clip('c2', 195.0, 199.0)), 1.1); add(s0 + 5.0, archive(clip('c2', 207.5, 210.5)), 1.1); add(s0 + 5.6, boom(0.8, 120), 0.7)
    add(s0 + 8.0, rng.standard_normal(int(1.2 * SR)).astype(np.float32) * 0.25, 1)
    s0 = S['add'][0]; add(s0 + 0.1, VO['add'], 0.9)
    for q in range(int(2.6 * 40 / 3)): add(s0 + 0.4 + q * 3 / 40, click(), 0.4)
    x = clip('e', 0.2, 1.36, 0.6); add(s0 + 3.5, np.tanh(3 * x).astype(np.float32), 0.9); add(s0 + 3.5, pa(VO['meme']), 0.8); add(s0 + 3.5, boom(1.5, 60), 0.7)
    add(s0 + 3.5 + 1.93, thunk(), 1.2); add(s0 + 3.5 + 1.93 + 0.1, VO['del'], 1.1)
    s0 = S['end'][0]
    for q in range(int(1.4 * 40 / 3)): add(s0 + 0.1 + q * 3 / 40, click(), 0.5)
    add(s0 + 1.4, VO['end'], 0.9); add(s0 + 2.2, archive(clip('c', 41.6, 42.95)) * 0.6, 1)
    mix = mix[:int(T_END * SR)]; f = int(0.25 * SR); mix[-f:] *= 0
    mix = np.tanh(mix * 1.1) * 0.93
    st = (np.repeat(mix[:, None], 2, 1) * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for i, s in enumerate(SHOTS): print(f'{i:2d} {s[0]:6s} {STARTS[i]:6.2f} {s[1]}')
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
