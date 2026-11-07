import os, sys, math, random, subprocess, wave, json, re, datetime
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
V13 = os.path.join(SP, 'v13')
sys.path.insert(0, SP); sys.path.insert(0, V13)
import render13 as R
from render import text_img, glitch_slices
from render13 import font, tokens, draw_rich, grad_text, fitw, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO, PINK, ORANGE, GOLD, WHITE, BLACK, shot_img, FOCUS

W, H, FPS, SR = 720, 1280, 30, 44100
T_END = 421.2244; N = int(round(T_END * FPS))
BAR = 4 * 60 / 113.35; OFF = 0.10
def B(x): return OFF + BAR * x
F_SER = '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'
F_SERI = '/usr/share/fonts/truetype/liberation/LiberationSerif-BoldItalic.ttf'
CREAM = (245, 235, 215)

# ---------------- timeline (bars) ----------------
SEG = []
def seg(k, a, b, **kw): SEG.append(dict(k=k, a=a, b=b, **kw))
seg('pro0', 0, 11); seg('pro1', 11, 21, shots=[120, 125, 113, 91, 101], ln=2); seg('title', 21, 23, shots=[111], ln=2)
PEOPLE = [
    ('Ржавый Светлячок', 'Jason Duval', [19, 26], ['Автор канала и хозяин чата', '362 поста · с 6 августа'], ('Приятного просмотра друзья) LFG', 'Ржавый Светлячок'), 23, 27),
    ('Егор Гусев', 'Boobie Ike', [0, 2], ['2532 сообщения — №1 в чате', 'окончил школу и два универа, пока ждал'], ('28 лет эволюции гта ради волос джейсона', 'Егор Гусев'), 27, 31),
    ('Ром🅰️', 'Cal Hampton', [8, 10], ['эксперт по сливам · 1241 сообщение', 'видел каждый кадр. дважды'], ('ну или они пёрнут в лужу и это будет главный провал 21го века', 'Ром🅰️'), 31, 36),
    ('Deleted Account', '???', [58], ['776 сообщений', 'личность не установлена'], ('Вот это слив🔥🥶', 'Deleted Account'), 36, 39.5),
    ('Киберлик', 'главный злодей', [49, 39], ['10 утечек за 4 дня', 'или главный маркетолог?'], None, 39.5, 43),
    ('Кубањ Шайтан', 'DreQuan Priest', [14, 15], ['пришёл за 25 дней до релиза', 'и сразу собрал сетап за 150к'], ('Вердикт таков: кто ноет про 30ФПС - долбаёбы.', 'Кубањ Шайтан'), 43, 47),
    ('Димочка Орлов', 'Brian Heder', [4, 6], ['главный скептик · 476 сообщений', '«Самый ленивый филлиал»'], ('Ставьте лайкос на сообщение если хотите перенос гта 6 ещё на год', 'Димочка Орлов'), 47, 51),
    ('finik', 'Raul Bautista', [69, 71], ['стратег и дипломат · 722 сообщения', 'победитель спора о возврате в Steam'], ('да, там как покажуууут, а мы как все со стулов попадаем, уххх!!!', 'finik'), 51, 55),
]
for p in PEOPLE: seg('person', p[5], p[6], p=p)
seg('also', 55, 60, shots=[75, 76, 73], ln=2)
seg('ch', 60, 61.5, num='ГЛАВА 2', title='КИБЕРЛИК', sub='18 — 25 августа', shots=[22], ln=2)
seg('leak', 61.5, 70, shots=[20, 26, 28, 61, 22], ln=2)
seg('ch', 70, 71.5, num='ГЛАВА 3', title='РАСКОЛ', sub='Extended Look · 27 августа', shots=[35], ln=2)
seg('split', 71.5, 85, shots=[37, 45, 31, 51, 66, 67, 38], ln=2)
seg('ch', 85, 87, num='ГЛАВА 4', title='ПОТЕРЯ', sub='16 сентября', shots=[80], ln=2)
seg('loss', 87, 100, shots=[80, 100, 109], ln=4.5)
seg('ch', 100, 101.5, num='ГЛАВА 5', title='БРАТСТВО', sub='сентябрь — октябрь', shots=[52], ln=2)
seg('bro', 101.5, 119, shots=[82, 83, 95, 115, 123, 12, 3, 9, 56], ln=2)
seg('imp', 119, 127, shots=[118], ln=8)
seg('howto', 127, 137, shots=[134, 30, 70, 34, 18], ln=2)
seg('ch', 137, 138, num='ГЛАВА 6', title='ФИНИШНАЯ\nПРЯМАЯ', sub='', shots=[111], ln=1)
FAST = [121, 91, 99, 127, 119, 110, 128, 129, 135, 133, 132, 136, 94, 97, 96, 85, 77, 98, 117, 1, 24, 2, 14, 74, 113, 16, 18, 19, 20, 21, 23, 25, 27, 29,
        32, 33, 36, 40, 41, 42, 43, 44, 46, 48, 53, 54, 55, 57, 60, 62, 63, 64, 65, 67, 68, 72, 78, 79, 81, 84, 86, 87, 88, 89, 90, 92, 93, 102, 103, 104]
seg('fast', 138, 169, shots=FAST, ln=0.5)
seg('credits', 169, 186, shots=[47, 112, 42, 109, 71, 100, 50, 137], ln=2.125)
seg('vi', 186, 999, shots=[137], ln=99)
def seg_at(t):
    for s in SEG:
        if t < B(s['b']): return s
    return SEG[-1]

# ---------------- background ----------------
def bg(t, s):
    if s['k'] == 'person':
        sh = s['p'][2]; ln = (s['b'] - s['a']) / len(sh)
    else:
        sh = s.get('shots', [50]); ln = s.get('ln', 2)
    rel = (t - B(s['a'])) / BAR; j = min(len(sh) - 1, int(rel / ln)); u = (rel - j * ln) / ln
    idx = sh[j]; img = shot_img(idx); cx = FOCUS.get(idx, 1138)
    pan = (40 if ln <= 1 else 120 + 40 * ln) * (1 if idx % 2 else -1)
    zoom = 1.0 + 0.06 * u
    if s['k'] == 'fast': zoom = 1.04 + 0.06 * math.exp(-(((t - OFF) % (BAR / 4)) / 0.09))
    x0 = cx - 360 + pan * (u - 0.5)
    cw, ch = 720 / zoom, 1280 / zoom
    x0 = min(max(0, x0 + (720 - cw) / 2), 2276 - cw); y0 = (1280 - ch) / 2
    M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT), u, j, ln
_Y, _X = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1.15 - 0.75 * np.sqrt(((_X - W / 2) / (W / 2)) ** 2 + ((_Y - H / 2) / (H / 2)) ** 2), 0.3, 1)[..., None]
BOT = np.clip((_Y - 700) / 500, 0, 1)[..., None] ** 1.3
def grade(img, k, t):
    x = img.astype(np.float32)
    # teal/orange documentary grade
    lum = x.mean(2, keepdims=True) / 255
    x = x + (np.array([18, 4, -14]) * lum + np.array([-10, 4, 14]) * (1 - lum))
    g = x.mean(2, keepdims=True); x = g + (x - g) * 1.08
    if k in ('loss', 'imp'): g = x.mean(2, keepdims=True); x = (g + (x - g) * 0.25) * 0.7
    if k in ('person', 'also', 'credits'): x = x * 0.85
    x = x * VIG * (1 - 0.55 * BOT)
    r = np.random.default_rng(int(t * 30)); x += r.normal(0, 5, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return np.clip(x, 0, 255).astype(np.uint8)

# ---------------- typography ----------------
def P(a): return Image.fromarray(a).convert('RGBA')
def alpha_im(im, a):
    if a >= 1: return im
    ar = np.array(im); ar[..., 3] = (ar[..., 3] * max(0, a)).astype(np.uint8); return Image.fromarray(ar)
def put(c, im, x, y, a=1.0, anchor='c'):
    im = alpha_im(im, a)
    if anchor == 'c': c.alpha_composite(im, (int(x - im.width / 2), int(y - im.height / 2)))
    else: c.alpha_composite(im, (int(x), int(y)))
def fade(t, t0, t1, fi=0.5, fo=0.5): return max(0, min(1, (t - t0) / fi, (t1 - t) / fo))
def rich_block(text, fo, maxw, fill=WHITE, align='c', lh=1.28, shadow=True):
    lines = R.layout(text, fo, maxw); lhp = int(fo.size * lh)
    wid = lambda l: sum(fo.getlength(v) if k == 't' else fo.size * 1.12 for k, v in tokens(l))
    im = Image.new('RGBA', (maxw + 40, lhp * len(lines) + 30), (0, 0, 0, 0))
    for j, l in enumerate(lines):
        x = (im.width - wid(l)) / 2 if align == 'c' else 20
        if shadow:
            sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); draw_rich(sh, (x + 2, 10 + lhp * j + 3), l, fo, (0, 0, 0, 200)); im.alpha_composite(sh)
        draw_rich(im, (x, 10 + lhp * j), l, fo, fill)
    return im
_qc = {}
def quote(c, t, t0, t1, text, who, role=None, y=930):
    a = fade(t, t0, t1, 0.4, 0.4)
    if a <= 0: return
    k = (text, who, role)
    if k not in _qc:
        q = rich_block('«' + text + '»', font(F_SERI, 46 if len(text) < 60 else 40), W - 110, WHITE)
        nm = Image.new('RGBA', (W, 60), (0, 0, 0, 0)); fo = font(F_BO, 26)
        s = '— ' + who + (', ' + role if role else '')
        wdt = sum(fo.getlength(v) if kk == 't' else 30 for kk, v in tokens(s))
        draw_rich(nm, ((W - wdt) / 2, 12), s, fo, (255, 200, 120))
        _qc[k] = (q, nm)
    q, nm = _qc[k]
    put(c, q, W / 2, y + 8 * (1 - a), a); put(c, nm, W / 2, y + q.height / 2 + 26, a)
def caption(c, t, t0, t1, lines, y=600, size=48, f=F_SER, col=WHITE, gap=16):
    a = fade(t, t0, t1, 0.6, 0.5)
    if a <= 0: return
    yy = y
    for l in lines:
        im = fitw(text_img(l, size, col, BLACK, 3, f=f)); put(c, im, W / 2, yy, a); yy += im.height + gap
def letterbox(c, h=70):
    d = ImageDraw.Draw(c); d.rectangle([0, 0, W, h], fill=BLACK); d.rectangle([0, H - h, W, H], fill=BLACK)

# ---------------- data ----------------
DAILY = json.load(open(os.path.join(V13, 'daily.json')))
def chart(c, t, t0, dur):
    u = min(1, max(0, (t - t0) / dur))
    x0, x1, y0, y1 = 60, W - 60, 470, 820
    d = ImageDraw.Draw(c)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
    ld.rounded_rectangle([x0 - 30, y0 - 110, x1 + 30, y1 + 70], 24, fill=(0, 0, 0, 170)); c.alpha_composite(lay)
    d.text((x0, y0 - 80), 'сообщений в день', font=font(F_BO, 28), fill=WHITE)
    vals = [v for _, v in DAILY]; mx = max(vals); n = len(vals)
    pts = [(x0 + (x1 - x0) * i / (n - 1), y1 - (y1 - y0) * v / mx) for i, v in enumerate(vals)]
    k = max(2, int(n * u))
    d.line(pts[:k], fill=PINK, width=5)
    poly = pts[:k] + [(pts[k - 1][0], y1), (pts[0][0], y1)]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(lay).polygon(poly, fill=PINK + (60,)); c.alpha_composite(lay)
    d.line([(x0, y1), (x1, y1)], fill=(200, 200, 200), width=2)
    for lab, i in (('6 авг', 0), ('19 авг', [s for s, _ in DAILY].index('19.08.2026')), ('7 ноя', n - 1)):
        d.text((pts[i][0], y1 + 14), lab, font=font(F_MED, 22), fill=(200, 200, 200), anchor='ma')
    ip = [s for s, _ in DAILY].index('19.08.2026')
    if k > ip:
        px, py = pts[ip]; d.ellipse([px - 9, py - 9, px + 9, py + 9], fill=WHITE)
        d.text((px + 16, py - 6), '1472', font=font(F_BLACK, 44), fill=WHITE, anchor='lm', stroke_width=3, stroke_fill=BLACK)
        d.text((px + 16, py + 34), 'рекорд чата · день второго слива', font=font(F_MED, 22), fill=(230, 230, 230), anchor='lm')

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; s = seg_at(t); k = s['k']; ta, tb = B(s['a']), B(s['b'])
    rng = random.Random(fi)
    if k == 'pro0':
        c = P(np.zeros((H, W, 3), np.uint8))
        L = [(B(0.5), B(3.0), ['17 сентября 2013 года', 'вышла GTA V']), (B(3.2), B(5.6), ['её купили', 'больше 200 миллионов раз']),
             (B(5.8), B(8.2), ['а потом наступили', '13 лет ожидания']), (B(8.4), B(11.0), ['декабрь 2023.', 'первый трейлер GTA VI'])]
        for a_, b_, lines in L: caption(c, t, a_, b_, lines, 600, 50, F_SER, CREAM)
        letterbox(c)
    else:
        img, u, j, ln = bg(t, s); img = grade(img, k, t); c = P(img)
        if k not in ('vi',) and j > 0 and u * ln * BAR < 0.08 and k not in ('loss', 'imp'): c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 40)))
        if k == 'pro1':
            L = [(B(11.2), B(13.8), ['карта вдвое больше GTA V']), (B(13.9), B(15.8), ['170+ видов животных', 'в GTA V их было 28']),
                 (B(15.9), B(17.8), ['80 часов на прохождение']), (B(17.9), B(21.0), [])]
            for a_, b_, lines in L[:3]: caption(c, t, a_, b_, lines, 560, 50, F_SER, WHITE)
            quote(c, t, B(17.9), B(21.0), 'родители сидели в 2013 году смотрели ради чего они пол зп мне на подарок потратили (хвох 360 и гта 5)… а щас батьку показываю трейлер шестерки, он уже и игры там не узнает, говорит бля че за фильм', 'Ром🅰️', y=760)
        if k == 'title':
            u2 = t - ta
            caption(c, t, ta, tb + 1, ['пока весь мир ждал,'], 380, 42, F_SER, CREAM)
            caption(c, t, ta + 0.8, tb + 1, ['в одном Telegram-чате собрались те,', 'кто ждал громче всех'], 450, 36, F_SER, CREAM, 8)
            if u2 > 1.8:
                g = grad_text('ЛЮМЕНЫ', 170, (255, 255, 255), PINK, F_BLACKI, 10); sc = 1 + 0.6 * math.exp(-(u2 - 1.8) / 0.15)
                g2 = g.resize((int(g.width * sc), int(g.height * sc))); put(c, fitw(g2, W + 200), W / 2, 700)
                caption(c, t, ta + 2.3, tb + 1, ['документальный фильм о 105 днях ожидания GTA VI'], 830, 28, F_SB, WHITE)
                if u2 - 1.8 < 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(220 * (1 - (u2 - 1.8) / 0.12)))))
        if k == 'person':
            name, role, shots, facts, qt, a_, b_ = s['p']; u2 = t - ta; dur = tb - ta
            if name == 'Deleted Account':
                ar = np.array(c.convert('RGB')).astype(np.float32); ar = (ar.mean(2, keepdims=True) * np.array([0.35, 0.35, 0.4])); c = P(np.clip(ar, 0, 255).astype(np.uint8))
            if name == 'Киберлик' and rng.random() < 0.25:
                c = P(glitch_slices(np.array(c.convert('RGB')), rng, 8, 60))
            sm = text_img('ЛЮДИ ЛЕОНИДЫ' if name != 'Киберлик' else 'АНТАГОНИСТ', 26, (255, 200, 120), BLACK, 2, f=F_BO)
            put(c, sm, W / 2, 175, fade(t, ta, tb, 0.3, 0.3))
            a = fade(t, ta + 0.1, tb, 0.25, 0.35); sc = easeback(min(1, (u2 - 0.1) / 0.35)) if u2 > 0.1 else 0
            nm = Image.new('RGBA', (W + 400, 170), (0, 0, 0, 0)); fo = font(F_BLACKI, 92)
            wdt = sum(fo.getlength(v) if kk == 't' else 100 for kk, v in tokens(name)); draw_rich(nm, (200 + (W - wdt) / 2, 20), name, fo, WHITE)
            arr = np.array(nm).astype(np.float32); hh = arr.shape[0]; gr = np.linspace(0, 1, hh)[:, None]
            msk = (arr[..., 0] > 200) & (arr[..., 1] > 200) & (arr[..., 2] > 200)
            for ch_, (c1, c2) in enumerate(zip((255, 255, 255), PINK)): arr[..., ch_] = np.where(msk, c1 * (1 - gr) + c2 * gr, arr[..., ch_])
            nm = Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.SMOOTH)
            shd = Image.new('RGBA', nm.size, (0, 0, 0, 0)); sa = np.array(nm.getchannel('A')); sh_ = np.zeros((*sa.shape, 4), np.uint8); sh_[..., 3] = (sa * 0.8).astype(np.uint8)
            shd = Image.fromarray(sh_).filter(ImageFilter.GaussianBlur(6)); nm2 = Image.new('RGBA', nm.size, (0, 0, 0, 0)); nm2.alpha_composite(shd, (4, 6)); nm2.alpha_composite(nm)
            nm2 = fitw(nm2.crop(nm2.getbbox() or (0, 0, 1, 1)).resize((max(1, int(nm2.crop(nm2.getbbox()).width * (0.7 + 0.3 * sc))), max(1, int(nm2.crop(nm2.getbbox()).height * (0.7 + 0.3 * sc))))), W - 40)
            put(c, nm2, W / 2, 270, a)
            rl = text_img(('в роли: ' + role) if name not in ('Киберлик', 'Deleted Account') else role, 30, WHITE, BLACK, 3, f=F_SB); put(c, rl, W / 2, 355, a)
            for jj, fct in enumerate(facts):
                fa = fade(t, ta + 0.6 + jj * 0.4, tb, 0.3, 0.35)
                fim = text_img(fct, 30, (230, 230, 230), BLACK, 3, f=F_MED); put(c, fitw(fim), W / 2, 420 + jj * 48, fa)
            if qt: quote(c, t, ta + dur * 0.42, tb - 0.1, qt[0], qt[1], y=930)
        if k == 'also':
            caption(c, t, ta, tb, ['а также'], 260, 40, F_SERI, (255, 200, 120))
            names = ['Александр · 1163', '^Sonnyk^ · 831', 'morinos · 773', 'Nikola · 601', 'Udo · 456', 'Lumens Chat · 251', 'wwrtuyi', 'GH05T', 'Max', 'Zefir', 'dooma', 'Какой-то Хрен С Горы']
            for jj, nmx in enumerate(names):
                a = fade(t, ta + 0.3 + jj * 0.45, tb, 0.3, 0.4)
                im = text_img(nmx, 40 if jj < 6 else 34, WHITE, BLACK, 3, f=F_BO); put(c, im, W / 2, 340 + jj * 62, a)
            caption(c, t, ta + 6, tb, ['и ещё сотни Люменов'], 1120, 34, F_SERI, (255, 200, 120))
        if k == 'ch':
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 150)))
            a = fade(t, ta, tb, 0.3, 0.3)
            put(c, text_img(s['num'], 32, (255, 200, 120), BLACK, 2, f=F_BO), W / 2, 520, a)
            g = grad_text(s['title'], 110, (255, 255, 255), PINK, F_BLACKI, 8); put(c, g, W / 2, 640 if '\n' not in s['title'] else 660, a)
            if s['sub']: put(c, text_img(s['sub'], 32, WHITE, BLACK, 3, f=F_SER), W / 2, 760 if '\n' not in s['title'] else 820, a)
        if k == 'leak':
            chart(c, t, ta + 0.2, (tb - ta) * 0.55)
            quote(c, t, ta + 0.3, ta + 5.5, 'СУКА ТАМ НОВЫЕ СЛИВЫ ПОЯВЛЯЮТСЯ УЖЕ', 'Какой-то Хрен С Горы', y=1000)
            quote(c, t, ta + 6.0, ta + 11.5, 'сливы льются через край / сайберлик ебет рокстар', 'Ром🅰️', y=1000)
            quote(c, t, ta + 12.0, tb - 0.2, 'За 4 дня мы получили 10 утечек от cyberleak и 0 постов от Rockstar.', 'Ржавый Светлячок', y=1000)
        if k == 'split':
            pairs = [('Ебать графон, говорил же гта6 не разочарует', 'Ostonaev.1', 'Я вот как раз не увидел другого уровня. Это ГТА 5 с модами', 'Serge Bolshakov'),
                     ('пусть лучше будет реализм, а не дебилизм', 'GH05T', 'Бляя 30 фпс', 'Alexander'),
                     ('Вердикт таков: кто ноет про 30ФПС - долбаёбы.', 'Кубањ Шайтан', '28 лет эволюции гта ради волос джейсона', 'Егор Гусев')]
            seg_l = 2.5 * BAR
            jx = int((t - ta) / seg_l)
            d = ImageDraw.Draw(c)
            if jx < 3:
                a1, n1, a2, n2 = pairs[jx]; t0 = ta + jx * seg_l
                lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
                ld.rectangle([0, 200, W, 600], fill=(20, 120, 60, 120)); ld.rectangle([0, 680, W, 1080], fill=(150, 20, 30, 120)); c.alpha_composite(lay)
                put(c, text_img('ФАНАТЫ', 34, (140, 255, 160), BLACK, 3, f=F_BLACK), W / 2, 240, fade(t, t0, t0 + seg_l, 0.2, 0.2))
                put(c, text_img('ХЕЙТЕРЫ' if jx < 2 else 'ИРОНИЯ', 34, (255, 140, 140), BLACK, 3, f=F_BLACK), W / 2, 720, fade(t, t0, t0 + seg_l, 0.2, 0.2))
                quote(c, t, t0 + 0.2, t0 + seg_l - 0.1, a1, n1, y=400)
                quote(c, t, t0 + 1.2, t0 + seg_l - 0.1, a2, n2, y=880)
            else:
                t0 = ta + 3 * seg_l
                caption(c, t, t0, tb, ['12 сентября', 'спор о возврате в Steam'], 330, 46, F_SER, WHITE, 8)
                caption(c, t, t0 + 0.6, tb, ['1137 сообщений за день'], 470, 40, F_BO, (255, 200, 120))
                quote(c, t, t0 + 1.4, tb - 0.1, 'я думаю мы победили, задавили аргументами наших оппонентов, и вышли абсолютными победителями', 'finik', y=860)
        if k == 'loss':
            text = 'Друзья, всем привет)\n\nИз-за сложившейся жизненной ситуации мне пришлось продать свою PlayStation и, к сожалению, к огромному моему сожалению, всю свою игровую коллекцию.'
            u2 = t - ta; nchar = int(max(0, u2 - 0.6) * 22)
            shown = text[:nchar]
            if shown:
                im = rich_block(shown, font(F_SER, 40), W - 120, CREAM, 'l', 1.35)
                put(c, im, W / 2, 360, 1.0, 'c') if False else c.alpha_composite(im, (40, 260))
            caption(c, t, ta + 9.5, tb, ['— Ржавый Светлячок'], 760, 30, F_BO, (255, 200, 120))
            caption(c, t, ta + 15.5, tb, ['Но одно обещание осталось в силе:'], 900, 34, F_SERI, WHITE)
            quote(c, t, ta + 18.0, tb - 0.2, 'розыгрыш GTA 6 остаётся в силе. Он никуда не денется)', 'Ржавый Светлячок', y=1020)
        if k == 'bro':
            dur = tb - ta; Q = [('Завёл бы стрим, там шейхи бы накидали', 'Дударчик Шизин'), ('сделай возможность кидать тебе донаты, и так мы все вместе тебе на пс-ку накидаем', 'Даниил | Коуч'),
                                ('поскорее желаю преодолеть все жизненные препятствия и вернуть себе возможность пройти эту легендарную игру 19 ноября!', 'Какой-то Хрен С Горы'),
                                ('Баляяяя) Собрал ПК. Рад как 10 летний пацан. Поздравьте парни.', 'Max'), ('Красивый пк, даже завидно, поздравляю', 'Димочка Орлов'),
                                ('Вот такой сэтап себе замутил для ГТА за 150к рублей…', 'Кубањ Шайтан'), ('Я лично извиняюсь за оскорбления с моей стороны.', 'Александр')]
            sl = dur / len(Q)
            for jj, (qq, ww) in enumerate(Q): quote(c, t, ta + jj * sl + 0.2, ta + (jj + 1) * sl - 0.1, qq, ww, y=760)
            caption(c, t, ta, ta + 3, ['Люмены своих не бросают'], 300, 44, F_SERI, (255, 200, 120))
        if k == 'imp':
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, 90)))
            caption(c, t, ta + 0.3, tb, ['24 октября'], 420, 40, F_SER, (255, 200, 120))
            u2 = t - ta
            if u2 > 2.0:
                g = text_img('Важное сообщение)', 70, WHITE, BLACK, 5, f=F_SERI); put(c, fitw(g), W / 2, 620, fade(t, ta + 2.0, tb, 1.0, 0.6))
                caption(c, t, ta + 4.5, tb, ['— Ржавый Светлячок · #GTA6'], 720, 30, F_BO, (255, 200, 120))
                caption(c, t, ta + 9.0, tb, ['(чат замер в ожидании)'], 860, 30, F_SERI, (200, 200, 200))
        if k == 'howto':
            day = 30 - int(18 * min(1, (t - ta) / (tb - ta)))
            g = grad_text(f'{day}', 200, (255, 255, 255), PINK, F_BLACKI, 10); put(c, g, W / 2, 330)
            put(c, text_img('ДНЕЙ ДО РЕЛИЗА', 40, WHITE, BLACK, 4, f=F_BLACK), W / 2, 460)
            items = ['Оглянитесь по сторонам перед переходом дороги', 'Пристегните ремень безопасности', 'Высыпайтесь', 'Пейте воду',
                     'Избегайте всего, что начинается с «смотри, как я»', 'Ни в коем случае «одна последняя безумная вещь перед GTA 6»']
            caption(c, t, ta + 0.2, tb, ['Как дожить до 19 ноября:'], 560, 38, F_SERI, (255, 200, 120))
            yy = 610
            for jj, it in enumerate(items):
                a = fade(t, ta + 1.2 + jj * 2.2, tb, 0.3, 0.4)
                im = rich_block('— ' + it, font(F_SB, 30), W - 100, WHITE); put(c, im, W / 2, yy + im.height / 2, a, 'c'); yy += im.height - 14
            caption(c, t, tb - 4.5, tb, ['— Nik, 18 октября'], 1160, 28, F_BO, (255, 200, 120))
        if k == 'fast':
            rel = (t - ta) / BAR
            words = [(1, 'НОВЫЙ ТРЕЙЛЕР', '15.10'), (3, 'ВОЗРАСТНОЙ РЕЙТИНГ', '«это всё ещё GTA)»'), (5, '210 ГБ', ''), (7, 'SOUTH PARK', 'тоже ждёт'),
                     (9, 'ОБЗОРЫ', '18 ноября'), (11, 'ВЫВЕСКА VICE BEACH', 'Майами'), (13, 'РАДИО GTA VI', 'представлено 8 октября'),
                     (17, 'Подъехали новые кадры)', ''), (18, 'Их очень много)', ''), (19, 'Просто кайф))', ''), (20, 'Ещееее)', ''), (21, 'У меня разбегаются глаза))', ''), (22.5, 'Ааа, по ходу, все)', ''),
                     (25, '17 924', 'сообщения'), (27, '105', 'дней'), (29, '1', 'чат')]
            for st, w1, w2 in words:
                if st <= rel < st + (1.0 if st >= 17 and st < 23 else 1.8):
                    tt0 = B(s['a'] + st); u2 = t - tt0; sc = 1 + 0.4 * math.exp(-u2 / 0.08)
                    im = grad_text(w1, 96 if len(w1) < 14 else 64, (255, 255, 255), PINK, F_BLACKI, 8) if st < 17 or st >= 25 else text_img(w1, 62, WHITE, BLACK, 5, f=F_SERI)
                    im = fitw(im.resize((int(im.width * sc), int(im.height * sc))))
                    put(c, im, W / 2, 620)
                    if w2: put(c, text_img(w2, 36, WHITE, BLACK, 4, f=F_SB), W / 2, 620 + im.height / 2 + 30)
                    if st >= 17 and st < 23: put(c, text_img('— Ржавый Светлячок, 5 ноября', 26, (255, 200, 120), BLACK, 2, f=F_BO), W / 2, 720)
        if k == 'credits':
            CR = [('Ржавый Светлячок', 'Jason Duval', 19), ('Егор Гусев', 'Boobie Ike', 0), ('Ром🅰️', 'Cal Hampton', 8), ('Кубањ Шайтан', 'DreQuan Priest', 14),
                  ('Димочка Орлов', 'Brian Heder', 4), ('finik', 'Raul Bautista', 69), ('Deleted Account', '???', 58), ('все Люмены', 'Леонида', 113)]
            rel = (t - ta) / BAR; jj = min(len(CR) - 1, int(rel / 2.125)); u2 = (rel - jj * 2.125) / 2.125
            nm, rl, img_i = CR[jj]; a = min(1, u2 * 6) * min(1, (1 - u2) * 6)
            put(c, text_img('В РОЛЯХ', 34, (255, 200, 120), BLACK, 2, f=F_BO), W / 2, 330, 1.0)
            th = shot_img(img_i); cx = int(FOCUS.get(img_i, 1138)); th = th[160:1120, max(0, cx - 480):max(0, cx - 480) + 960]
            th = cv2.resize(th, (360, 360)); ti = Image.fromarray(th).convert('RGBA'); mk = Image.new('L', (360, 360), 0); ImageDraw.Draw(mk).ellipse([0, 0, 359, 359], fill=255); ti.putalpha(mk)
            ring = Image.new('RGBA', (380, 380), (0, 0, 0, 0)); ImageDraw.Draw(ring).ellipse([0, 0, 379, 379], fill=PINK + (255,)); ring.alpha_composite(ti, (10, 10))
            put(c, ring, W / 2, 600, a)
            ni = Image.new('RGBA', (W, 100), (0, 0, 0, 0)); fo = font(F_BLACKI, 60); wdt = sum(fo.getlength(v) if kk == 't' else 66 for kk, v in tokens(nm)); draw_rich(ni, ((W - wdt) / 2, 10), nm, fo, WHITE)
            put(c, ni, W / 2, 850, a); put(c, text_img(rl, 34, (255, 200, 120), BLACK, 3, f=F_SERI), W / 2, 920, a)
        if k == 'vi':
            R.final(c, t - (B(186) - B(85)) if False else t, ) if False else vi_final(c, t)
    letterbox(c)
    if T_END - t < 1.5: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * min(1, (1.5 - (T_END - t)) / 1.5)))))
    return np.array(c.convert('RGB'))

def vi_final(c, t):
    ta = B(186); u = t - ta
    c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(160 * min(1, u / 1.0)))))
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    sun_y = 1000 - 260 * min(1, u / 2.0)
    sun = Image.new('RGBA', (520, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    for yy in range(520):
        g = yy / 520
        if yy > 260 and (yy // 14) % 3 == 0: continue
        sd.line([(0, yy), (520, yy)], fill=(255, int(70 + 150 * g), int(160 - 120 * g), 255))
    mk = Image.new('L', (520, 520), 0); ImageDraw.Draw(mk).ellipse([0, 0, 519, 519], fill=255)
    sun.putalpha(Image.fromarray(np.minimum(np.array(sun.getchannel('A')), np.array(mk))))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([W / 2 - 360, sun_y - 360, W / 2 + 360, sun_y + 360], fill=(255, 90, 150, 90))
    a0 = min(1, u / 1.5)
    c.alpha_composite(alpha_im(glow.filter(ImageFilter.GaussianBlur(60)), a0)); c.alpha_composite(alpha_im(sun, a0), (int(W / 2 - 260), int(sun_y - 260)))
    if u > 1.2: put(c, text_img('GRAND  THEFT  AUTO', 46, WHITE, BLACK, 4, f=F_BLACK), W / 2, 280, min(1, (u - 1.2) / 0.6))
    tv = BAR * 1.0
    if u > tv:
        v = u - tv; s = 1 + 2.2 * math.exp(-v / 0.12)
        vi = grad_text('VI', 360, (255, 90, 170), (255, 190, 70), F_BLACKI, 12)
        if v > 0.4:
            ar = np.array(vi).astype(np.float32); xs = np.arange(vi.width)[None, :]; pos = ((v - 0.4) % 2.4) / 1.2 * (vi.width + 300) - 150
            band = np.exp(-((xs - pos - (np.arange(vi.height)[:, None] * 0.4)) / 40) ** 2)
            ar[..., :3] = np.clip(ar[..., :3] + band[..., None] * 160 * (ar[..., 3:4] / 255), 0, 255); vi = Image.fromarray(ar.astype(np.uint8))
        vi2 = vi.resize((int(vi.width * s), int(vi.height * s))); put(c, vi2, W / 2, 520)
        if v < 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - v / 0.12)))))
    if u > BAR * 2: put(c, fitw(text_img('19.11.2026', 70, WHITE, BLACK, 6, f=F_BLACKI)), W / 2, 790, easeback((u - BAR * 2) / 0.3))
    if u > BAR * 3:
        v = u - BAR * 3
        put(c, text_img('ДО РЕЛИЗА ОСТАЛОСЬ', 44, WHITE, BLACK, 5, f=F_BLACK), W / 2, 900)
        put(c, grad_text('МЕНЬШЕ 264 ЧАСОВ', 70, (255, 220, 90), (255, 110, 60), F_BLACKI, 7), W / 2, 980, easeback(v / 0.3))
        secs = max(0, 264 * 3600 - 1 - v); hh = int(secs // 3600); mm = int(secs % 3600 // 60); ss = secs % 60
        put(c, text_img(f'{hh:03d}:{mm:02d}:{ss:05.2f}', 56, WHITE, BLACK, 5, f=F_MONO), W / 2, 1080)
    if u > BAR * 5.5:
        quote(c, t, ta + BAR * 5.5, T_END - 1.2, 'Все мы в ожидании релиза)', 'Ржавый Светлячок', y=1150) if False else None
        caption(c, t, ta + BAR * 5.5, T_END, ['«Все мы в ожидании релиза)»'], 1160, 34, F_SERI, (255, 220, 180))

# ---------------- AUDIO ----------------
def build_audio(outp):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(HERE, 'track.mp3'), '-ar', str(SR), '-ac', '2', os.path.join(HERE, 'track.wav')], check=True)
    w = wave.open(os.path.join(HERE, 'track.wav')); tr = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2) / 32768
    n = len(tr); fx = np.zeros(n, np.float32); rng = np.random.default_rng(5)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n: return
        j = min(n, i + len(sig)); fx[i:j] += g * sig[:j - i]
    def tt(d): return np.arange(int(d * SR)) / SR
    def whoosh(d=0.6):
        t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2; return (np.convolve(x, np.ones(16) / 16, 'same') * 0.3).astype(np.float32)
    def boom(d=1.6, f0=80):
        t = tt(d); f = f0 * np.exp(-t * 3.5) + 32; return np.tanh(2.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2)).astype(np.float32)
    def key():
        t = tt(0.03); return (rng.standard_normal(len(t)) * np.exp(-t * 260) * 0.12).astype(np.float32)
    for s in SEG:
        if s['k'] in ('ch',): add(B(s['a']) - 0.25, whoosh(), 0.8)
    add(B(21) + 1.8, boom(), 0.5); add(B(187), boom(2.0, 70), 0.6)
    # typewriter in loss
    ta = B(87); text_len = 175
    for q in range(text_len): add(ta + 0.6 + q / 22, key(), 1.0)
    mix = tr + fx[:, None]; f = int(1.5 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
    mix = np.tanh(mix * 1.0) * 0.97
    st = (mix * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for s in SEG: print(f"{s['k']:8s} {B(s['a']):7.2f} {B(min(s['b'], 199)):7.2f}")
        sys.exit()
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:06.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--audio':
        build_audio(sys.argv[2]); sys.exit()
    if sys.argv[1] == '--part':
        out, a, b = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, b): p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
