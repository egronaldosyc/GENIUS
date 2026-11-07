import os, sys, math, random, subprocess, wave, json, re
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
sys.path.insert(0, SP); sys.path.insert(0, os.path.join(SP, 'v13')); sys.path.insert(0, os.path.join(SP, 'v14'))
import render13 as R13
import render14 as R14
from render import text_img
from render13 import font, tokens, draw_rich, grad_text, fitw, easeback, F_MED, F_SB, F_BO, F_BLACK, F_BLACKI, F_MONO, PINK, GOLD, WHITE, BLACK, shot_img, FOCUS
from render14 import P, put, fade, rich_block, caption, letterbox, alpha_im, F_SER, F_SERI, CREAM, VIG

W, H, FPS, SR = 720, 1280, 30, 44100
T_END = 247.72; N = int(round(T_END * FPS))
BAR = 4 * 60 / 116.25; OFF = 0.41
def B(x): return OFF + BAR * x
BLUE = (70, 140, 255); REDC = (235, 50, 60); YEL = (255, 205, 60); GRN = (80, 220, 120); GREY = (170, 170, 180)

# ---------------- sections ----------------
SEC = []
def sec(k, a, b, shots, **kw): SEC.append(dict(k=k, a=a, b=b, shots=shots, **kw))
sec('intro', 0, 7.5, [137]); sec('law', 7.5, 15.5, [111])
sec('round', 15.5, 27.5, [20, 26, 28, 22], n=1, title='ГРАФОН', date='18 — 28 августа', count='1882 сообщения за 27–28 августа', L='ФАНАТЫ', R='ХЕЙТЕРЫ')
sec('round', 27.5, 37, [32, 35, 31, 66], n=2, title='АРМИЯ\nИ ВОЗРАСТ', date='1 — 2 сентября', count='733 сообщения', L='Олександр', R='Nikola')
sec('round', 37, 55, [49, 38, 39, 51, 58, 67], n=3, title='ВОЗВРАТ\nВ STEAM', date='12 — 13 сентября', count='2081 сообщение за 2 дня', L='^Sonnyk^', R='Александр и finik')
sec('after', 55, 59, [47])
sec('round', 59, 63, [61, 68], n=4, title='ХЕЙТЕР\nПРИШЁЛ', date='24 октября', count='426 сообщений', L='dooma', R='правила')
sec('wise', 63, 67.5, [80])
sec('round', 67.5, 71.5, [116, 54], n=5, title='«ГОВНО»', date='4 ноября', count='', L='Димочка Орлов', R='dooma')
sec('verdict', 71.5, 82, [121, 111])
sec('hall', 82, 100, [127, 99, 91, 113, 119, 110, 117, 128, 129])
sec('codex', 100, 108, [137])
sec('moral', 108, 113.9, [112])
sec('final', 113.9, 999, [137])
def sec_at(t):
    for s in SEC:
        if t < B(s['b']): return s
    return SEC[-1]

# ---------------- chat bubbles ----------------
# side: L / R / M (moderator) / N (neutral); fl: I insult, A apology, W win, X lose
BUB = []
def b(bar, side, who, text, fl=''): BUB.append(dict(t=B(bar), side=side, who=who, text=text, fl=fl))
# round 1
b(17.0, 'L', 'Ostonaev.1', 'Ебать графон, говорил же гта6 не разочарует')
b(18.0, 'R', 'Serge Bolshakov', 'Я вот как раз не увидел другого уровня. Это ГТА 5 с модами')
b(19.0, 'R', 'Alexander', 'Бляя 30 фпс')
b(19.75, 'L', 'GH05T', 'пусть лучше будет реализм, а не дебилизм')
b(20.75, 'R', 'Areg Areg', 'Мне почему то кажется что это ии')
b(21.75, 'L', 'Deleted Account', 'Им ничем не угодишь, сидят на диванах и ноют, мол, игра нереалистичная😂😂')
b(23.0, 'N', 'Jpputr', 'Сука что за д**ны ещё голосуют?', 'I')
b(24.5, 'N', 'NaNaNa', 'Ну так ты еб***та кусок сам это выложил', 'I')
b(26.0, 'N', 'Дениус', 'Ты че распизделся, я в твою сторону никаких оскорблений не говорил')
# round 2
b(29.0, 'L', 'Олександр', 'Я привел тебе множество аргументов почему это может быть харизматичный персонаж ни разу не переходя на личности')
b(30.5, 'R', 'Nikola', 'Где я перешел на личности? Просто указал, что у тебя мышление ещё очень молодого человека.', 'I')
b(32.0, 'R', 'Nikola', 'Тебя уволили я правильно понял?)', 'I')
b(33.25, 'R', 'Nikola', 'школьник это оскорбление теперь? ну ок, давай буду говорить малолетка или малой', 'I')
b(35.0, 'L', 'Олександр', 'Второй день подряд ты сливаешься и переходишь на личности, делай выводы')
# round 3
b(39.0, 'R', 'finik', 'я думаю мы победили, задавили аргументами наших оппонентов, и вышли абсолютными победителями', 'W')
b(41.0, 'N', 'LeonSKennedy1994', 'вот я и говорю ты нищеброд и уходишь на пк за торрентами', 'I')
b(42.5, 'N', 'LeonSKennedy1994', 'что стим? Ты там играми не владеешь д*лб**б, там так же указана аренда', 'I')
b(44.0, 'L', '^Sonnyk^', 'Скидывай правила пользования общим доступом 🤣')
b(45.0, 'N', 'Max', 'Просто мне этот разговор напомнил мем - дверь мне запили 😂😂😂')
b(46.25, 'N', 'Златовласка', 'Чел, тут уже спор давно не про баны, а переходы на личности')
b(48.0, 'M', 'Lumens Chat', 'Так, друзья, давайте завязывайте сраться. Если хотите выяснять отношения - идите общаться в ЛС. Не разводите здесь срач. Спасибо)')
b(52.0, 'M', 'Lumens Chat', 'Сейчас банить буду', 'BIG')
# after
b(55.5, 'R', 'Александр', 'Я лично извиняюсь за оскорьления с моей стороны.', 'A')
b(57.0, 'R', 'finik', 'извиняюсь, да не было, поэтому мы проиграли', 'X')
# round 4
b(60.0, 'M', 'Lumens Chat', 'Без оскорблений.')
b(60.75, 'L', 'dooma', 'глупое правило. он пришел поныть, пооскорблять игру, которую мы тут очень ждем, поэтому я имею полное право его оскорбить', 'I')
b(62.25, 'M', 'Lumens Chat', 'Это правило чата.')
# round 5
b(68.5, 'L', 'Димочка Орлов', 'Да это говно ваще отменить надо')
b(69.75, 'R', 'dooma', 'это оскорбление полностью обоснованное', 'I')
CENSOR_T = [x['t'] for x in BUB if 'I' in x['fl']]
_bc = {}
def bubble(i):
    if i in _bc: return _bc[i]
    x = BUB[i]; side = x['side']
    mod = side == 'M'; big = 'BIG' in x['fl']
    maxw = 600 if mod else 520
    fo = font(F_MED, 30 if not big else 46); lines = R13.layout(x['text'], fo, maxw - 44); lh = int(fo.size * 1.28)
    wid = lambda l: sum(fo.getlength(v) if k == 't' else fo.size * 1.12 for k, v in tokens(l))
    bw = int(min(maxw, max(max(wid(l) for l in lines) + 48, 260)))
    h = 58 + lh * len(lines) + 16
    col = {'L': (30, 60, 120), 'R': (120, 30, 40), 'M': (110, 85, 10), 'N': (45, 45, 55)}[side]
    if 'I' in x['fl']: col = (150, 20, 30)
    im = Image.new('RGBA', (bw, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw - 1, h - 1], 26, fill=col + (235,), outline=((255, 80, 90) if 'I' in x['fl'] else (255, 255, 255, 60)), width=4 if 'I' in x['fl'] else 2)
    ncol = {'L': (140, 190, 255), 'R': (255, 150, 150), 'M': YEL, 'N': (220, 220, 230)}[side]
    nm = ('🛡 МОДЕРАТОР · ' + x['who']) if mod else x['who']
    draw_rich(im, (22, 14), nm, font(F_BO, 24), ncol)
    for j, l in enumerate(lines): draw_rich(im, (22, 50 + lh * j), l, fo, WHITE)
    _bc[i] = im; return im
def stamp_im(txt, col, size=40):
    t = text_img(txt, size, col, col, 0, f=F_BLACK)
    fr = Image.new('RGBA', (t.width + 36, t.height + 22), (0, 0, 0, 0)); ImageDraw.Draw(fr).rounded_rectangle([3, 3, fr.width - 4, fr.height - 4], 10, outline=col + (255,), width=6)
    fr.alpha_composite(t, (18, 11)); a = np.array(fr); m = np.random.default_rng(len(txt)).random(a.shape[:2]) < 0.15; a[m, 3] = (a[m, 3] * 0.3).astype(np.uint8)
    return Image.fromarray(a)
STAMPS = {'I': ('ПЕРЕХОД НА ЛИЧНОСТИ', (255, 60, 70)), 'A': ('ИЗВИНЕНИЕ ПРИНЯТО', GRN), 'W': ('ПОБЕДА?', GRN), 'X': ('ПОРАЖЕНИЕ', (255, 160, 60))}
_st = {k: stamp_im(*v) for k, v in STAMPS.items()}
def draw_chat(c, t, s):
    lo, hi = B(s['a']), B(s['b'])
    if s['k'] == 'after': lo = B(55)
    idx = [i for i, x in enumerate(BUB) if lo <= x['t'] <= t and x['t'] < hi]
    y = 1150.0; top = 430
    for i in reversed(idx):
        x = BUB[i]
        if 'BIG' in x['fl']: continue
        im = bubble(i); u = t - x['t']; ein = easeback(min(1, u / 0.3))
        yy = y - im.height
        a = min(1, ein * 1.4) * max(0, min(1, (yy + im.height - top) / 140))
        xx = {'L': 24, 'R': W - 24 - im.width, 'N': (W - im.width) / 2, 'M': (W - im.width) / 2}[x['side']]
        if 'I' in x['fl'] and u < 0.4: xx += 8 * math.sin(u * 80)
        if a > 0:
            put(c, im, xx, yy + (1 - ein) * 50, a, 'tl')
            for fl, st in _st.items():
                if fl in x['fl'] and u > 0.25:
                    sa = min(1, (u - 0.25) / 0.12); sc = 1 + 0.8 * max(0, 1 - (u - 0.25) / 0.12)
                    sim = st.rotate(-6, expand=True, resample=Image.BICUBIC); sim = sim.resize((int(sim.width * sc * 0.55), int(sim.height * sc * 0.55)))
                    sx = min(W - sim.width / 2 - 6, max(sim.width / 2 + 6, xx + im.width - sim.width / 2 + 20)); put(c, sim, sx, yy + 6 + (1 - ein) * 50, sa * a)
        y -= (im.height + 18) * ein
        if y < top - 200: break
    for i in idx:
        x = BUB[i]
        if 'BIG' in x['fl']:
            u = t - x['t']; a = fade(t, x['t'], hi, 0.15, 0.3)
            c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(150 * a))))
            sim = stamp_im('СЕЙЧАС БАНИТЬ БУДУ', (255, 205, 60), 64); sim = fitw(sim.rotate(-6, expand=True, resample=Image.BICUBIC))
            sc = 1 + 1.2 * max(0, 1 - u / 0.15); sim = sim.resize((int(sim.width * sc), int(sim.height * sc)))
            put(c, fitw(sim, W + 300), W / 2, 700, a)
            put(c, text_img('— 🛡 Lumens Chat, 13 сентября'.replace('🛡 ', ''), 30, YEL, BLACK, 3, f=F_BO), W / 2, 840, a)
def round_head(c, t, s):
    a = 1.0; ta = B(s['a']); u = t - ta
    big = u < 1.6
    if big:
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(140 * fade(t, ta, ta + 1.6, 0.1, 0.4)))))
        aa = fade(t, ta, ta + 1.6, 0.15, 0.4)
        put(c, text_img(f'РАУНД {s["n"]}', 44, (255, 200, 120), BLACK, 3, f=F_BLACK), W / 2, 500, aa)
        g = grad_text(s['title'], 120, (255, 255, 255), REDC, F_BLACKI, 9); put(c, g, W / 2, 660, aa * easeback(min(1, u / 0.3)))
        put(c, text_img(s['date'], 34, WHITE, BLACK, 3, f=F_SER), W / 2, 820 if '\n' in s['title'] else 770, aa)
        return
    d = ImageDraw.Draw(c)
    d.rounded_rectangle([20, 90, W - 20, 300], 22, fill=(0, 0, 0, 165))
    put(c, text_img(f'РАУНД {s["n"]}', 26, (255, 200, 120), BLACK, 2, f=F_BLACK), W / 2, 118)
    g = grad_text(s['title'].replace('\n', ' '), 58, (255, 255, 255), REDC, F_BLACKI, 6); put(c, fitw(g, W - 60), W / 2, 172)
    if s['count']: put(c, text_img(s['date'] + ' · ' + s['count'], 24, (220, 220, 220), BLACK, 2, f=F_MED), W / 2, 222)
    # VS
    fo = font(F_BLACKI, 32)
    d.rounded_rectangle([40, 248, W / 2 - 40, 290], 20, fill=BLUE + (220,)); d.rounded_rectangle([W / 2 + 40, 248, W - 40, 290], 20, fill=REDC + (220,))
    for txt, cx in ((s['L'], W / 4), (s['R'], 3 * W / 4)):
        wd = sum(fo.getlength(v) if k == 't' else 36 for k, v in tokens(txt)); sc = min(1, (W / 2 - 100) / max(1, wd))
        ti = Image.new('RGBA', (int(wd) + 20, 50), (0, 0, 0, 0)); draw_rich(ti, (10, 4), txt, fo, WHITE)
        if sc < 1: ti = ti.resize((int(ti.width * sc), int(ti.height * sc)))
        put(c, ti, cx, 270)
    put(c, text_img('VS', 40, YEL, BLACK, 4, f=F_BLACKI), W / 2, 270)

# ---------------- background ----------------
def bg(t, s):
    sh = s['shots']; ln = (s['b'] - s['a']) / len(sh) if s['b'] < 900 else 99
    if s['k'] == 'hall': ln = 2.0
    rel = (t - B(s['a'])) / BAR; j = min(len(sh) - 1, int(rel / ln)); u = (rel - j * ln) / ln
    idx = sh[j]; img = shot_img(idx); cx = FOCUS.get(idx, 1138); pan = (120 + 30 * min(ln, 6)) * (1 if idx % 2 else -1)
    zoom = 1.0 + 0.06 * u
    x0 = cx - 360 + pan * (u - 0.5); cw, ch = 720 / zoom, 1280 / zoom
    x0 = min(max(0, x0 + (720 - cw) / 2), 2276 - cw); y0 = (1280 - ch) / 2
    M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT), j, u, ln
def grade(img, k, t):
    x = img.astype(np.float32)
    dark = {'round': 0.55, 'intro': 0.4, 'law': 0.5, 'after': 0.7, 'wise': 0.45, 'verdict': 0.5, 'hall': 0.55, 'codex': 0.35, 'moral': 0.6, 'final': 0.35}.get(k, 0.6)
    g = x.mean(2, keepdims=True); x = g + (x - g) * (0.8 if k != 'after' else 1.0)
    x = x * dark * VIG
    r = np.random.default_rng(int(t * 30)); x += r.normal(0, 5, (H // 2, W // 2, 1)).repeat(2, 0).repeat(2, 1)
    return np.clip(x, 0, 255).astype(np.uint8)

# ---------------- render ----------------
def render(fi):
    t = fi / FPS; s = sec_at(t); k = s['k']; ta, tb = B(s['a']), B(min(s['b'], 200))
    img, j, u, ln = bg(t, s); c = P(grade(img, k, t)); rng = random.Random(fi)
    if k not in ('intro', 'wise', 'codex', 'final', 'moral') and j > 0 and u * ln * BAR < 0.07: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 35)))
    if k == 'intro':
        caption(c, t, 0.6, ta + 7.4, ['17 924 сообщения.'], 520, 48, F_SER, CREAM)
        caption(c, t, 3.0, tb, ['и далеко не все из них —', 'про графику'], 600, 40, F_SER, CREAM, 6)
        caption(c, t, 7.5, tb, ['мы не одобряем оскорбления.', 'они показаны для наглядности и скрыты цензурой'], 1060, 24, F_MED, (190, 190, 190), 4)
    if k == 'law':
        caption(c, t, ta + 0.2, tb, ['в чате Ржавого Светлячка', 'одно главное правило'], 380, 40, F_SER, CREAM, 6)
        if t > ta + 5.0:
            g = grad_text('СРАТЬСЯ МОЖНО', 92, (255, 255, 255), GRN, F_BLACKI, 8); put(c, g, W / 2, 640, easeback(min(1, (t - ta - 5.0) / 0.3)))
        if t > ta + 10.0:
            g = grad_text('НА ЛИЧНОСТИ —\nНЕЛЬЗЯ', 96, (255, 255, 255), REDC, F_BLACKI, 9); put(c, g, W / 2, 860, easeback(min(1, (t - ta - 10.0) / 0.3)))
        caption(c, t, ta + 12.5, tb, ['КОДЕКС ЛЮМЕНА'], 1100, 40, F_BLACK, (255, 200, 120))
    if k == 'round':
        draw_chat(c, t, s); round_head(c, t, s)
    if k == 'after':
        caption(c, t, ta + 0.1, tb, ['на следующий день'], 260, 40, F_SERI, (255, 200, 120))
        draw_chat(c, t, s)
    if k == 'wise':
        caption(c, t, ta + 0.3, tb, ['а что думают мудрецы?'], 330, 40, F_SERI, (255, 200, 120))
        R14.quote(c, t, ta + 1.5, tb - 0.2, 'ну если объективно, то оскорблять смысла нет, человек с претензией написал, я ему развернуто с претензией ответил, это норм, а просто оскорбить - какой смысл', 'Ром🅰️', y=640)
    if k == 'verdict':
        u2 = t - ta
        if u2 < 7.5:
            caption(c, t, ta, ta + 7.5, ['ВЕРДИКТ МОДЕРАТОРА · 4 ноября'], 260, 32, F_BLACK, YEL)
            caption(c, t, ta + 0.2, ta + 7.5, ['«Оскорбления не могут быть', 'оправданными или обоснованными.»'], 450, 42, F_SERI, WHITE, 6)
            if u2 > 2.6:
                im = rich_block('«Никакие обстоятельства или причины не делают оскорбления допустимыми. Даже если вы не согласны с чьим-то мнением, это не дает вам право переходить на личности и унижать собеседника.»', font(F_SERI, 34), W - 100, CREAM)
                put(c, im, W / 2, 760, fade(t, ta + 2.6, ta + 7.5, 0.6, 0.4))
            caption(c, t, ta + 4.0, ta + 7.5, ['— Lumens Chat'], 1000, 28, F_BO, (255, 200, 120))
        elif u2 < 10.6:
            R14.quote(c, t, ta + 7.6, ta + 10.6, 'плохое мышление, человека можно спокойно оскорблять, если он это заслужил… правила вредят этому чату', 'dooma', y=600)
        elif u2 < 13.8:
            g = text_img('«Ох уж эти вредные правила»', 62, WHITE, BLACK, 5, f=F_SERI); put(c, fitw(g), W / 2, 600, fade(t, ta + 10.7, ta + 13.8, 0.2, 0.3))
            caption(c, t, ta + 11.0, ta + 13.8, ['— Димочка Орлов'], 700, 30, F_BO, (255, 200, 120))
        else:
            v = t - (ta + 13.9)
            g = text_img('«Ты давай на личности не переходи 👉👈»'.replace(' 👉👈', ''), 54, WHITE, BLACK, 5, f=F_SERI); put(c, fitw(g), W / 2, 600, fade(t, ta + 13.9, tb, 0.2, 0.3))
            em = R13.emoji_im('👉', 90); em2 = R13.emoji_im('👈', 90); put(c, em, W / 2 - 60 + 10 * math.sin(v * 12), 730, fade(t, ta + 14.2, tb, 0.2, 0.3)); put(c, em2, W / 2 + 60 - 10 * math.sin(v * 12), 730, fade(t, ta + 14.2, tb, 0.2, 0.3))
            caption(c, t, ta + 14.4, tb, ['— Димочка Орлов'], 830, 30, F_BO, (255, 200, 120))
    if k == 'hall':
        cards = [('ЗАЛ СЛАВЫ', 'великих срачей', ''), ('2 дня · 2081 сообщение', 'самый длинный срач', 'возврат в Steam'), ('510 сообщений', 'за два дня спора', '^Sonnyk^ — главный оратор'),
                 ('72', 'раза написали слово', '«аргумент»'), ('117', 'раз вспоминали', '«правила»'), ('46', 'раз звучало', '«оскорбл…»'), ('20', 'извинений', 'это тоже рекорд'),
                 ('1', 'победа finik', 'которая на следующий день стала поражением'), ('0', 'реальных банов за срачи', 'Люмены сами всё поняли')]
        rel = (t - ta) / BAR; jj = min(len(cards) - 1, int(rel / 2.0)); u2 = (rel - jj * 2.0) / 2.0
        big, l1, l2 = cards[jj]; a = min(1, u2 * 8) * min(1, (1 - u2) * 8); sc = 1 + 0.35 * math.exp(-u2 * 2.0 * BAR / 0.1)
        g = grad_text(big, 120 if len(big) < 6 else 70, (255, 255, 255), PINK, F_BLACKI, 9); g = fitw(g.resize((int(g.width * sc), int(g.height * sc))))
        put(c, g, W / 2, 560, a); put(c, text_img(l1, 40, WHITE, BLACK, 4, f=F_SB), W / 2, 690, a)
        if l2: put(c, fitw(text_img(l2, 34, (255, 200, 120), BLACK, 3, f=F_SERI)), W / 2, 760, a)
    if k == 'codex':
        put(c, grad_text('КОДЕКС ЛЮМЕНА', 74, (255, 255, 255), (255, 200, 120), F_BLACKI, 7), W / 2, 230, fade(t, ta, tb + 5, 0.4, 0.4))
        rules = ['Спорь об игре — сколько угодно', 'Аргументы сильнее оскорблений', 'На личности — нельзя', 'Оскорбления не бывают «обоснованными»',
                 'Хочешь выяснять отношения — иди в ЛС', 'Сюжетные сливы — бан', 'Извиниться — не стыдно', 'Ты давай на личности не переходи 👉👈']
        yy = 340
        for jj, r in enumerate(rules):
            a = fade(t, ta + 0.8 + jj * 1.85, tb + 5, 0.25, 0.4)
            im = rich_block(f'{jj + 1}. {r}', font(F_SB, 34), W - 80, WHITE, 'l')
            put(c, im, 20, yy + (1 - a) * 20, a, 'tl'); yy += im.height - 4
    if k == 'moral':
        R14.quote(c, t, ta + 0.3, tb - 0.2, 'срачи тут веселые бывают, но зачастую именно без прямых оскорблений, так что все хорошо 🤘', 'Егор Гусев', y=620)
    if k == 'final':
        u2 = t - ta
        g = grad_text('КОДЕКС ЛЮМЕНА', 92, (255, 255, 255), PINK, F_BLACKI, 8); put(c, g, W / 2, 560, easeback(min(1, u2 / 0.3)) if u2 < 0.3 else 1.0)
        if u2 < 0.1: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(200 * (1 - u2 / 0.1)))))
        caption(c, t, ta + 0.8, T_END, ['сраться можно.'], 700, 46, F_SERI, GRN)
        caption(c, t, ta + 1.8, T_END, ['на личности — нельзя.'], 770, 46, F_SERI, (255, 120, 120))
        caption(c, t, ta + 3.5, T_END, ['Люмены 🤘'.replace(' 🤘', '')], 900, 40, F_BLACK, (255, 200, 120))
    # censor flash
    for ct in CENSOR_T:
        if 0 <= t - ct - 0.25 < 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 0, 0, 50)))
    letterbox(c)
    if T_END - t < 2.0: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * min(1, (2.0 - (T_END - t)) / 2.0)))))
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(HERE, 'track.mp3'), '-ar', str(SR), '-ac', '2', os.path.join(HERE, 'track.wav')], check=True)
    w = wave.open(os.path.join(HERE, 'track.wav')); tr = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2) / 32768
    n = len(tr); fx = np.zeros(n, np.float32); rng = np.random.default_rng(9)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n or i < 0: return
        j = min(n, i + len(sig)); fx[i:j] += g * sig[:j - i]
    def tt(d): return np.arange(int(d * SR)) / SR
    def beep(d=0.32): t = tt(d); return (0.16 * np.sin(2 * np.pi * 1000 * t) * np.minimum(1, t / 0.005) * np.minimum(1, (d - t) / 0.01)).astype(np.float32)
    def pop(): t = tt(0.07); return (0.08 * np.sin(2 * np.pi * (700 + 900 * t / 0.07) * t) * np.exp(-t * 50)).astype(np.float32)
    def whistle(): t = tt(0.6); f = 2400 + 300 * np.sign(np.sin(2 * np.pi * 22 * t)); return (0.1 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.minimum(1, t / 0.02) * np.clip((0.6 - t) / 0.05, 0, 1)).astype(np.float32)
    def gavel(): t = tt(0.3); return (np.tanh(3 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 30)) * 0.5 + rng.standard_normal(len(t)) * 0.3 * np.exp(-t * 60)).astype(np.float32)
    def whoosh(d=0.5): t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2; return (np.convolve(x, np.ones(16) / 16, 'same') * 0.3).astype(np.float32)
    def bell(): t = tt(1.5); return (sum(np.sin(2 * np.pi * f * t) * np.exp(-t * d) for f, d in ((830, 2.5), (1245, 3), (1660, 4))) * 0.12).astype(np.float32)
    for x in BUB:
        if x['side'] == 'M': add(x['t'], whistle(), 1.0)
        else: add(x['t'], pop(), 1.0)
        if 'I' in x['fl']: add(x['t'] + 0.25, beep(), 1.0)
        if 'A' in x['fl'] or 'W' in x['fl'] or 'X' in x['fl']: add(x['t'] + 0.25, gavel(), 0.8)
        if 'BIG' in x['fl']: add(x['t'], gavel(), 1.0); add(x['t'] + 0.15, gavel(), 0.8)
    for s in SEC:
        if s['k'] == 'round': add(B(s['a']) - 0.2, whoosh(), 0.8); add(B(s['a']), bell(), 0.6)
    for jj in range(8): add(B(100) + 0.8 + jj * 1.85, gavel(), 0.5)
    add(B(113.9), gavel(), 0.9)
    mix = tr + fx[:, None]; f = int(2.0 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
    mix = np.tanh(mix) * 0.97; st = (mix * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        for s in SEC: print(f"{s['k']:8s} {B(s['a']):7.2f} {B(min(s['b'], 120)):7.2f}")
        sys.exit()
    if sys.argv[1] == '--preview':
        os.makedirs(os.path.join(HERE, 'pv'), exist_ok=True)
        for t in [float(x) for x in sys.argv[2].split(',')]:
            Image.fromarray(render(int(round(t * FPS)))).save(os.path.join(HERE, 'pv', f'{t:06.2f}.jpg'), quality=85)
        sys.exit()
    if sys.argv[1] == '--audio':
        build_audio(sys.argv[2]); sys.exit()
    if sys.argv[1] == '--part':
        out, a, b_ = sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
                              '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '20', '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
        for fi in range(a, b_): p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
