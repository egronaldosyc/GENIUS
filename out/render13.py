import os, sys, math, random, subprocess, wave, json, re, datetime
import numpy as np, cv2
from PIL import Image, ImageDraw, ImageFilter, ImageFont
HERE = os.path.dirname(os.path.abspath(__file__))
SP = os.path.dirname(HERE)
sys.path.insert(0, SP)
from render import text_img, ease_pop, F_BLACK, F_BLACKI, F_MONO, F_SYM

W, H, FPS, SR = 720, 1280, 30, 44100
T_END = 175.281633; N = int(round(T_END * FPS))
F_MED = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'; F_SB = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'; F_BO = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
F_EMO = '/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf'
_fc = {}
def font(p, s):
    k = (p, s)
    if k not in _fc: _fc[k] = ImageFont.truetype(p, s)
    return _fc[k]
BAR = 4 * 60 / 126; OFF = 0.43
def B(x): return OFF + BAR * x
PINK = (255, 70, 160); ORANGE = (255, 150, 60); GOLD = (255, 205, 90); GREEN = (110, 230, 110); RED = (210, 30, 40); WHITE = (255, 255, 255); BLACK = (0, 0, 0)

# ---------------- data ----------------
MSGS = [x for x in json.load(open(os.path.join(HERE, 'm2.json'))) if x['kind'] == 'default' and x['text']]
CUM = json.load(open(os.path.join(HERE, 'cum.json')))
FOCUS = {int(k): v for k, v in json.load(open(os.path.join(HERE, 'focus.json'))).items()}
def find(pat):
    for x in MSGS:
        if pat in x['text']: return x
    raise KeyError(pat)
def strip_tags(t): return re.sub(r'\s*#\w+', '', t).strip()

# ---------------- sections ----------------
SEC = [('intro', 0, 8), ('m1', 8, 21), ('m2', 21, 38), ('wasted', 38, 40), ('m3', 40, 48), ('brk', 48, 52), ('build', 52, 60),
       ('drop', 60, 74), ('dip', 74, 75), ('outro', 75, 85), ('final', 85, 999)]
def sec_at(t):
    for k, a, b in SEC:
        if t < B(b): return k, a, b
    return SEC[-1]
DATES = {'intro': ('06.08', '17.08'), 'm1': ('18.08', '25.08'), 'm2': ('26.08', '31.08'), 'wasted': ('31.08', '31.08'), 'm3': ('01.09', '15.09'),
         'brk': ('16.09', '16.09'), 'build': ('17.09', '14.10'), 'drop': ('15.10', '06.11'), 'dip': ('07.11', '07.11'), 'outro': ('07.11', '07.11'), 'final': ('07.11', '07.11')}
def dt(s): d, m = s.split('.'); return datetime.datetime(2026, int(m), int(d))
CUMD = {dt(k[:5]): v for k, v in CUM.items()}
def cum_at(day):
    best = 0
    for d_, v in CUMD.items():
        if d_ <= day: best = max(best, v)
    return best
def date_at(t):
    k, a, b = sec_at(t); d0, d1 = DATES[k]; u = min(1, max(0, (t - B(a)) / (B(min(b, 92)) - B(a))))
    a_, b_ = dt(d0), dt(d1); return a_ + (b_ - a_) * u
RELEASE = datetime.datetime(2026, 11, 19)
STARS = {'intro': (0, 0), 'm1': (1, 3), 'm2': (3, 5), 'wasted': (5, 5), 'm3': (1, 1), 'brk': (0, 0), 'build': (0, 1), 'drop': (2, 5), 'dip': (0, 0), 'outro': (0, 0), 'final': (0, 0)}

# ---------------- shots ----------------
SHOTS = {'intro': ([50, 137, 125, 120], 2.0), 'm1': ([22, 20, 69, 26, 61, 28, 116, 65, 68, 104, 54, 15, 57], 1.0),
         'm2': ([35, 37, 49, 45, 31, 51, 66, 32, 67, 38, 41, 40, 44, 58, 59, 47, 43], 1.0), 'wasted': ([43], 2.0),
         'm3': ([30, 18, 10, 56, 9, 70, 34, 134], 1.0), 'brk': ([80], 4.0), 'build': ([52, 82, 83, 95, 115, 123, 12, 3], 1.0),
         'drop': ([111, 121, 91, 99, 127, 119, 110, 128, 129, 135, 133, 132, 136, 94, 97, 96, 85, 77, 98, 117, 1, 24, 2, 14, 74, 76, 73, 113], 0.5),
         'dip': ([118], 1.0), 'outro': ([42, 112, 109, 71, 100], 2.0), 'final': ([137], 99.0)}
_ic = {}
def shot_img(i):
    if i not in _ic:
        if len(_ic) > 8: _ic.pop(next(iter(_ic)))
        _ic[i] = cv2.cvtColor(cv2.imread(os.path.join(HERE, 'sh', f'{i:03d}.jpg')), cv2.COLOR_BGR2RGB)
    return _ic[i]
def shot_at(t):
    k, a, b = sec_at(t); lst, ln = SHOTS[k]
    rel = (t - B(a)) / BAR; j = min(len(lst) - 1, int(rel / ln)); u = (rel - j * ln) / ln
    return lst[j], u, ln, k, j
def frame_bg(t, rng):
    idx, u, ln, k, j = shot_at(t)
    img = shot_img(idx); cx = FOCUS.get(idx, 1138)
    pan = {2.0: 260, 4.0: 320, 1.0: 150, 0.5: 40, 99.0: 0}.get(ln, 120) * (1 if (idx % 2) else -1)
    zoom = 1.0 + (0.07 * u if ln >= 1 else 0)
    if k == 'drop': zoom += 0.05 * math.exp(-(((t - OFF) % (BAR / 4)) / 0.08))
    if k == 'wasted': zoom = 1.06 + 0.12 * u
    x0 = cx - 360 + pan * (u - 0.5)
    cw, ch = 720 / zoom, 1280 / zoom
    x0 = min(max(0, x0 + (720 - cw) / 2), 2276 - cw); y0 = (1280 - ch) / 2
    M = np.float32([[zoom, 0, -x0 * zoom], [0, zoom, -y0 * zoom]])
    out = cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    return out, k, u, j
def grade(img, k):
    x = img.astype(np.float32)
    x = x * np.array([1.04, 0.98, 1.05]) + np.array([6, 0, 10])
    g = x.mean(2, keepdims=True); x = g + (x - g) * 1.12
    if k == 'wasted': g = x.mean(2, keepdims=True); x = g * np.array([1.0, 0.95, 0.95])
    if k in ('brk', 'dip'): g = x.mean(2, keepdims=True); x = (g + (x - g) * 0.35) * 0.62
    if k == 'outro': x = x * 0.72
    return np.clip(x, 0, 255).astype(np.uint8)

# ---------------- rich text ----------------
EMO_RE = re.compile('(?:[\U0001F1E6-\U0001F1FF]{2}|[\U0001F000-\U0001FAFF☀-➿⬀-⯿⌀-⏿←-⇿](?:️)?(?:‍[\U0001F000-\U0001FAFF☀-➿](?:️)?)*)')
_ec = {}
def emoji_im(e, size):
    k = (e, size)
    if k not in _ec:
        im = Image.new('RGBA', (160, 160), (0, 0, 0, 0)); ImageDraw.Draw(im).text((8, 8), e, font=font(F_EMO, 109), embedded_color=True)
        bb = im.getbbox(); im = im.crop(bb) if bb else im
        s = size / max(1, im.height); _ec[k] = im.resize((max(1, int(im.width * s)), size), Image.LANCZOS)
    return _ec[k]
def tokens(text):
    out = []; pos = 0
    for mm in EMO_RE.finditer(text):
        if mm.start() > pos: out.append(('t', text[pos:mm.start()]))
        out.append(('e', mm.group())); pos = mm.end()
    if pos < len(text): out.append(('t', text[pos:]))
    return out
def layout(text, fo, maxw):
    ewid = fo.size * 1.12
    words = []
    for line in text.split('\n'):
        for w_ in re.split(r'(\s+)', line):
            if w_: words.append(w_)
        words.append('\n')
    lines = [[]]; cur = 0.0
    def wlen(w_): return sum(fo.getlength(v) if k == 't' else ewid for k, v in tokens(w_))
    for w_ in words[:-1]:
        if w_ == '\n': lines.append([]); cur = 0; continue
        wl = wlen(w_)
        if w_.isspace():
            if lines[-1]: lines[-1].append(w_); cur += wl
            continue
        if cur + wl > maxw and lines[-1]: lines.append([]); cur = 0
        lines[-1].append(w_); cur += wl
    return [''.join(l).rstrip() for l in lines]
def draw_rich(img, xy, text, fo, fill):
    d = ImageDraw.Draw(img); x, y = xy; es = int(fo.size * 1.0)
    for k, v in tokens(text):
        if k == 't': d.text((x, y), v, font=fo, fill=fill); x += fo.getlength(v)
        else: img.alpha_composite(emoji_im(v, es), (int(x + 1), int(y + fo.size * 0.12))); x += fo.size * 1.12
    return x

# ---------------- notifications ----------------
PAL = [(225, 90, 80), (240, 150, 50), (150, 110, 235), (80, 190, 110), (60, 170, 220), (230, 100, 170), (90, 140, 255)]
def avc(name): return PAL[sum(ord(c) for c in name) % len(PAL)]
N_ = []
def n(bar, pat, text=None, fl='', name=None):
    if name is None: name = find(pat)['from']
    if text is None: text = strip_tags(find(pat)['text'])
    N_.append(dict(t=B(bar), name=name[:24], text=text, fl=fl))
CH = 'Ржавый Светлячок'
# intro
n(1.5, 'получит расширенный обзор уже 27', 'Grand Theft Auto VI получит расширенный обзор уже 27 августа!')
n(3.0, 'Обзор это тип трейлер?'); n(4.0, 'Нетфликс...'); n(4.5, 'Если нет - это будет провал')
n(5.5, 'Бегу оформлять подписку Нетфликс'); n(6.75, 'Игра не вышла, а мерч готов')
# m1
n(9.0, 'Вот это слив🔥🥶'); n(9.75, 'СУКА ТАМ НОВЫЕ СЛИВЫ'); n(10.5, 'РАЗШИВИЛИЛИ ГАДОВ'); n(11.25, 'запрячут фишинг ссылки')
n(12.0, 'тратили больше 2 млрд'); n(12.75, 'Передоз контента от Рокстар'); n(13.5, 'пёрнут в лужу', 'ну или они пёрнут в лужу и это будет главный провал 21го века')
n(14.25, 'великой мыльной оперы', 'Короче, мужики, ложимся спать и на утро смотрим продолжение этой великой мыльной оперы')
n(15.0, 'Как думаете я успею?'); n(15.5, 'успеешь как раз накопить на пк'); n(16.0, 'мент обсуждает игру про воров')
n(16.75, 'хакерская движуха часть маркетинга', 'Прикиньте, эта вся хакерская движуха часть маркетинга')
n(17.5, 'За 4 дня мы получили 10 утечек', 'За 4 дня мы получили 10 утечек от cyberleak и 0 постов от Rockstar.', 'H')
n(18.75, 'кибердолбаебик может че угодно', 'кибердолбаебик может че угодно писать')
n(19.25, 'я уже окончил школу и два универа', fl='H'); n(20.25, 'ЫЫЫ КИБЕРЛИК СПАСИБО', fl='H')
# m2
n(22.25, 'Запасайтесь пивом на сегодня', fl='F'); n(23.0, 'пиво или водка к презентации', 'ладно вот вопрос: пиво или водка к презентации гта 6', 'H')
n(24.0, 'Полный холодильник'); n(24.75, 'говорил же гта6 не разочарует', fl='F'); n(25.5, 'Это ГТА 5 с модами', fl='X')
n(26.25, 'Бляя 30 фпс', fl='X'); n(26.75, 'холопские 30 кадров', fl='X'); n(27.5, 'пусть лучше будет реализм, а не дебилизм', fl='F')
n(28.25, 'физика сальто шакал', fl='X'); n(29.0, 'Мне почему то кажется что это ии', fl='X')
n(29.75, 'Эффекта " вау "', 'Эффекта «вау» я не увидел ни физики, ни геймплея. Это 5 из 10.', 'X'); n(30.5, '100+ часов смотреть на жопу', fl='F')
n(31.25, '28 лет эволюции гта ради волос', fl='H'); n(32.5, 'Им ничем не угодишь', fl='F')
n(33.25, 'Проблема завышенных ожиданий', 'Проблема завышенных ожиданий. Я искренне не понимаю, что нужно было показать этим людям, чтобы они остались довольны!', 'F')
n(34.5, 'Я НЕ ЖДУ ГТА 6 ПОСМОТРИТЕ', fl='HX'); n(36.0, 'Отменил предзаказ, потому что', fl='H')
# m3
n(41.0, '5 ноября заявление об увольнении'); n(41.75, 'выпадает на ебучую работу'); n(42.5, 'пк себе собираю. За 450к')
n(43.25, 'умножаем 5 стилей', 'умножаем 5 стилей на 80 часов сюжетки и прощаемся с семьей и друзьями до лета))')
n(44.0, 'Кто шарит за телевизоры'); n(44.75, 'Ёлки иголки. А я ещё пс5'); n(45.5, 'жены и любовницы два моих пс5', fl='H')
n(46.75, 'холодное ноябрьское утро в метро', fl='H')
# brk (center)
n(48.4, 'Из-за сложившейся жизненной', 'Друзья, всем привет)\n\nИз-за сложившейся жизненной ситуации мне пришлось продать свою PlayStation и, к сожалению, к огромному моему сожалению, всю свою игровую коллекцию.\n\nСпасибо вам за поддержку)💡', 'C')
# build
n(52.25, 'там шейхи бы накидали'); n(53.0, 'мир не без добрых людей'); n(53.75, 'Да, это жестко. Держись, братик', 'Да, это жестко. Держись, братик)')
n(54.5, 'Держись, удачи'); n(55.25, 'мы все вместе тебе на пс-ку', 'сделай возможность кидать тебе донаты, и так мы все вместе тебе на пс-ку накидаем')
n(56.25, 'вернуть себе возможность пройти эту легендарную', fl='H'); n(57.75, 'Собрал ПК. Рад как 10 летний', 'Баляяяя) Собрал ПК. Рад как 10 летний пацан. Поздравьте парни.')
n(58.5, 'Можете поздравить, я наконец то купил'); n(59.25, 'они все припрятали на последние 30 дней')
# drop
n(60.5, 'Новый трейлер\n', 'Новый трейлер', name=CH); n(61.0, 'аж мураши пошли')
n(61.5, 'официально получила возрастной рейтинг', 'GTA 6 официально получила возрастной рейтинг: кровь, нагота, грубый язык… Ну, в общем, это всё ещё GTA)')
n(62.25, 'Размер GTA 6, по сообщениям', 'Размер GTA 6, по сообщениям, составит 210 ГБ.'); n(62.75, '2 трейлера и полчаса геймплея')
n(63.25, 'надоели эти скрины покажите'); n(63.75, 'До выхода осталось всего ничего')
n(64.25, 'Вот как дожить до 19 ноября', 'Вот как дожить до 19 ноября:\nОглянитесь по сторонам перед переходом дороги\nПристегните ремень безопасности\nПейте воду\nНи в коем случае «одна последняя безумная вещь перед GTA 6»', 'H')
n(65.75, 'South Park показал', 'South Park показал эксклюзивный геймплей GTA 6.'); n(66.25, 'сэтап себе замутил', 'Вот такой сэтап себе замутил для ГТА за 150к рублей…')
n(66.75, 'пафосного ебальника джейсона'); n(67.25, 'рекламы на один квадратный метр'); n(67.75, 'говно ваще отменить надо')
n(68.25, 'Эмбарго на публикацию', 'СМИ начнут получать коды игры. Эмбарго на публикацию обзоров снимут 18 ноября.'); n(68.75, 'бля чем я в рабочее время')
n(69.5, 'Подъехали новые кадры'); n(70.0, 'Их очень много)'); n(70.5, 'Просто кайф))'); n(71.0, 'Ещееее)'); n(71.5, 'У меня разбегаются глаза'); n(72.5, 'Ааа, по ходу, все)')
# dip
n(74.1, 'Важное сообщение)', 'Важное сообщение)', 'C')
# outro
n(79.0, 'я родился до гта 3'); n(79.5, 'вопросы?'); n(83.0, 'Все мы в ожидании релиза)')
for x in N_:
    L = len(x['text'])
    if 'C' in x['fl']: x['life'] = {48.4: B(51.8) - B(48.4), 74.1: B(74.95) - B(74.1)}[round((x['t'] - OFF) / BAR, 1)]
    else:
        sk = sec_at(x['t'] + 0.01)[0]
        x['life'] = (min(2.8, max(1.5, 1.1 + L / 34)) if sk == 'drop' else min(4.4, max(2.1, 1.6 + L / 24))) + (0.9 if 'H' in x['fl'] else 0)
# make sure stacking doesn't run into section ends
CENTERS = [x['t'] for x in N_ if 'C' in x['fl']]
_card = {}
def card_img(i):
    if i in _card: return _card[i]
    x = N_[i]; center = 'C' in x['fl']; hero = 'H' in x['fl']
    bw = W - 40 if not center else W - 60
    fo = font(F_MED, 30 if center else 27); lh = int(fo.size * 1.3)
    lines = layout(x['text'], fo, bw - 140)
    if not center and len(lines) > 6: lines = lines[:6]; lines[-1] = lines[-1][:max(0, len(lines[-1]) - 1)] + '…'
    h = 98 + lh * len(lines) + 4
    im = Image.new('RGBA', (bw, h), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    col = avc(x['name']); d.ellipse([22, 24, 94, 96], fill=col)
    ini = EMO_RE.sub('', x['name']).strip()[:1].upper() or '?'
    d.text((58, 60), ini, font=font(F_BLACK, 34), fill=WHITE, anchor='mm')
    d.text((114, 22), 'Lumens Chat', font=font(F_SB, 23), fill=(35, 35, 40))
    d.text((bw - 24, 24), 'сейчас', font=font(F_MED, 21), fill=(110, 110, 120), anchor='ra')
    draw_rich(im, (114, 52), x['name'], font(F_SB, 25), (60, 60, 70) if not hero else (170, 40, 120))
    for j, l in enumerate(lines): draw_rich(im, (114, 88 + lh * j), l, fo, (18, 18, 22))
    _card[i] = (im, h, bw); return _card[i]
def easeback(u):
    if u <= 0: return 0.0
    if u >= 1: return 1.0
    c1 = 1.5; c3 = c1 + 1; return 1 + c3 * (u - 1) ** 3 + c1 * (u - 1) ** 2
def glass(c, x, y, im, bw, h, alpha=1.0, hero=False):
    x, y = int(x), int(y)
    if y + h < 0 or alpha <= 0: return
    y0 = max(0, y); crop = c.crop((x, y0, x + bw, min(H, y + h)))
    blur = crop.filter(ImageFilter.GaussianBlur(16)).convert('RGBA')
    base = Image.new('RGBA', (bw, h), (0, 0, 0, 0)); base.paste(blur, (0, y0 - y))
    tint = Image.new('RGBA', (bw, h), (246, 246, 250, 205)); base = Image.alpha_composite(base, tint)
    m = Image.new('L', (bw, h), 0); ImageDraw.Draw(m).rounded_rectangle([0, 0, bw - 1, h - 1], 28, fill=int(255 * alpha))
    card = Image.new('RGBA', (bw, h), (0, 0, 0, 0)); card.paste(base, (0, 0), m)
    cont = im.copy()
    if alpha < 1: a = np.array(cont); a[..., 3] = (a[..., 3] * alpha).astype(np.uint8); cont = Image.fromarray(a)
    card.alpha_composite(cont)
    sh = Image.new('RGBA', (bw + 60, h + 60), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh)
    if hero:
        sd.rounded_rectangle([18, 18, bw + 42, h + 42], 34, fill=PINK + (int(170 * alpha),))
        sh = sh.filter(ImageFilter.GaussianBlur(14))
    else:
        sd.rounded_rectangle([30, 36, bw + 30, h + 36], 28, fill=(0, 0, 0, int(80 * alpha))); sh = sh.filter(ImageFilter.GaussianBlur(12))
    c.alpha_composite(sh, (x - 30, y - 30)); c.alpha_composite(card, (x, y))
def draw_notifs(c, t):
    act = [i for i, x in enumerate(N_) if x['t'] <= t < x['t'] + x['life'] + 0.3 and 'C' not in x['fl'] and not any(x['t'] < cs <= t - 0.3 for cs in CENTERS)]
    act.sort(key=lambda i: -N_[i]['t'])
    y = 46.0
    for rank, i in enumerate(act):
        x = N_[i]; im, h, bw = card_img(i); hero = 'H' in x['fl']
        ein = easeback((t - x['t']) / 0.32)
        ex = min(1, max(0, (t - (x['t'] + x['life'])) / 0.3))
        for cs in CENTERS:
            if x['t'] < cs <= t: ex = max(ex, min(1, (t - cs) / 0.3))
        if rank >= 3:
            t_push = N_[act[rank - 3]]['t']; ex = max(ex, min(1, (t - t_push) / 0.25))
        alpha = (1 - ex) * min(1, ein * 1.5 + 0.05)
        yy = y - (1 - ein) * (h + 60) - ex * 40
        sc = 1.0
        if hero and t - x['t'] < 0.5: sc = 1 + 0.06 * math.sin(min(1, (t - x['t']) / 0.5) * math.pi)
        xoff = (W - bw) / 2
        if hero and t - x['t'] < 0.35: xoff += 6 * math.sin((t - x['t']) * 90)
        if sc != 1.0:
            im2 = im.resize((int(bw * sc), int(h * sc))); glass(c, xoff - bw * (sc - 1) / 2, yy, im2, im2.width, im2.height, alpha, hero)
        else: glass(c, xoff, yy, im, bw, h, alpha, hero)
        y += (h + 16) * ein * (1 - ex)
def hero_dim(t):
    a = 0
    for x in N_:
        if 'H' in x['fl'] and 0 <= t - x['t'] < 0.9: a = max(a, 0.32 * (1 - (t - x['t']) / 0.9))
    return a
def draw_center(c, t):
    for i, x in enumerate(N_):
        if 'C' not in x['fl'] or not (x['t'] <= t < x['t'] + x['life']): continue
        im, h, bw = card_img(i); u = t - x['t']
        s = easeback(u / 0.4); ex = max(0, (u - (x['life'] - 0.3)) / 0.3)
        c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(120 * min(1, u / 0.3) * (1 - ex)))))
        im2 = im.resize((max(1, int(bw * (0.85 + 0.15 * s))), max(1, int(h * (0.85 + 0.15 * s)))))
        glass(c, (W - im2.width) / 2, H / 2 - im2.height / 2 - 40, im2, im2.width, im2.height, min(1, s) * (1 - ex), True)

# ---------------- HUD & cards ----------------
MON = ['ЯНВ', 'ФЕВ', 'МАР', 'АПР', 'МАЙ', 'ИЮН', 'ИЮЛ', 'АВГ', 'СЕН', 'ОКТ', 'НОЯ', 'ДЕК']
def star(d, cx, cy, r, fill, outline):
    pts = []
    for k in range(10):
        a = -math.pi / 2 + k * math.pi / 5; rr = r if k % 2 == 0 else r * 0.45
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
    d.polygon(pts, fill=fill, outline=outline, width=2)
def hud(c, t, k):
    if k in ('final', 'outro'): return
    d = ImageDraw.Draw(c); day = date_at(t)
    x1 = W - 30
    txt = f'{day.day} {MON[day.month - 1]} 2026'
    d.text((x1, H - 210), txt, font=font(F_BLACKI, 40), fill=WHITE, anchor='rs', stroke_width=4, stroke_fill=BLACK)
    cnt = cum_at(day) if k not in ('outro', 'dip') else 17924
    d.text((x1, H - 150), f'${cnt:,}'.replace(',', ' '), font=font(F_BLACKI, 50), fill=GREEN, anchor='rs', stroke_width=5, stroke_fill=BLACK)
    d.text((x1, H - 124), 'сообщений в чате', font=font(F_MONO, 18), fill=(220, 220, 220), anchor='rs', stroke_width=2, stroke_fill=BLACK)
    s0, s1 = STARS[k]; ka, a, b = sec_at(t); u = min(1, max(0, (t - B(a)) / (B(b) - B(a)))) if b < 900 else 0
    ns = int(round(s0 + (s1 - s0) * u))
    blink = (k in ('wasted',) and int(t * 6) % 2) or (ns == 5 and int(t * 4) % 2 and k == 'm2')
    for j in range(5):
        cx = x1 - 22 - (4 - j) * 46; fill = (255, 255, 255) if j < ns and not blink else (40, 40, 40)
        star(d, cx, H - 82, 19, fill, (0, 0, 0))
    left = max(0, (RELEASE - day).days)
    if k == 'build' and t > B(58):
        left = max(12, int(left - (t - B(58)) / (B(60) - B(58)) * (left - 25)))
    pill = f'ДО РЕЛИЗА: {left} ДН.'
    fo = font(F_BO, 26); w_ = fo.getlength(pill) + 36
    d.rounded_rectangle([30, H - 106, 30 + w_, H - 58], 24, fill=(0, 0, 0, 170), outline=PINK, width=3)
    d.text((48, H - 82), pill, font=fo, fill=WHITE, anchor='lm')
def fitw(im, mw=W - 40):
    if im.width <= mw: return im
    s = mw / im.width; return im.resize((int(im.width * s), max(1, int(im.height * s))), Image.LANCZOS)
def grad_text(txt, size, c1=PINK, c2=ORANGE, f=F_BLACKI, stroke=8):
    base = text_img(txt, size, WHITE, (20, 0, 30), stroke, f=f, spacing=-6)
    a = np.array(base).astype(np.float32); hh = a.shape[0]
    g = np.linspace(0, 1, hh)[:, None]
    mask = (a[..., 0] > 200) & (a[..., 1] > 200)
    for ch in range(3): a[..., ch] = np.where(mask, c1[ch] * (1 - g) + c2[ch] * g, a[..., ch])
    return fitw(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)))
CARDS = {'m1': ('МИССИЯ 1', 'КИБЕРЛИК', '18 — 25 августа'), 'm2': ('МИССИЯ 2', 'ГРАЖДАНСКАЯ\nВОЙНА', '27 — 28 августа · Extended Look'),
         'm3': ('МИССИЯ 3', 'ПОДГОТОВКА', 'сентябрь'), 'drop': ('ФИНАЛЬНАЯ МИССИЯ', 'ФИНИШНАЯ\nПРЯМАЯ', 'октябрь — ноябрь'), 'build': ('', '16 СЕНТЯБРЯ', '')}
def mission_card(c, t, k, a):
    if k not in CARDS or k == 'build': return
    u = t - B(a); dur = 2.4 if k != 'drop' else 1.9
    if u > dur: return
    s = easeback(u / 0.3); ex = max(0, (u - dur + 0.3) / 0.3)
    small, big, sub = CARDS[k]
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    gi = grad_text(big, 118 if '\n' not in big else 100)
    sm = text_img(small, 38, WHITE, BLACK, 5, f=F_BLACK)
    sb = text_img(sub, 34, WHITE, BLACK, 4, f=F_SB)
    yc = 640
    lay.alpha_composite(sm, (int(W / 2 - sm.width / 2), int(yc - gi.height / 2 - sm.height - 6)))
    lay.alpha_composite(gi, (int(W / 2 - gi.width / 2), int(yc - gi.height / 2)))
    lay.alpha_composite(sb, (int(W / 2 - sb.width / 2), int(yc + gi.height / 2 + 4)))
    sc = 0.6 + 0.4 * s
    lay = lay.resize((int(W * sc), int(H * sc)))
    if ex > 0: a_ = np.array(lay); a_[..., 3] = (a_[..., 3] * (1 - ex)).astype(np.uint8); lay = Image.fromarray(a_)
    c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(70 * (1 - ex)))))
    c.alpha_composite(lay, (int((W - lay.width) / 2 - ex * 120), int((H - lay.height) / 2)))
def intro_titles(c, t):
    lines = [(B(0.25), '6 АВГУСТА 2026', 58, F_BLACKI, WHITE), (B(1.0), 'в Telegram создан чат', 34, F_SB, WHITE), (B(2.0), 'ЖДУНЫ', 150, None, None),
             (B(3.0), 'хроники ожидания GTA VI', 36, F_SB, WHITE)]
    if t > B(4.5): return
    fade = 1 - max(0, (t - B(4.1)) / (B(4.5) - B(4.1)))
    y = 520
    for t0, txt, sz, f, col in lines:
        if t < t0: y += sz + 30; continue
        a = min(1, (t - t0) / 0.5) * fade
        im = grad_text(txt, sz) if f is None else text_img(txt, sz, col, BLACK, 4, f=f)
        if a < 1: ar = np.array(im); ar[..., 3] = (ar[..., 3] * a).astype(np.uint8); im = Image.fromarray(ar)
        c.alpha_composite(im, (int(W / 2 - im.width / 2), int(y - 10 * (1 - a))))
        y += im.height + 8
def wasted(c, t):
    u = t - B(38)
    a = min(1, u / 0.5)
    im = fitw(text_img('ПОТРАЧЕНО', 120, (205, 25, 35), BLACK, 9, f=F_BLACKI))
    ar = np.array(im); ar[..., 3] = (ar[..., 3] * a).astype(np.uint8)
    c.alpha_composite(Image.fromarray(ar), (int(W / 2 - im.width / 2), 560))
    if u > 0.9:
        s2 = text_img('предзаказ отменён', 44, WHITE, BLACK, 5, f=F_SB); c.alpha_composite(s2, (int(W / 2 - s2.width / 2), 720))
CREDITS = [('В РОЛЯХ', [('Ржавый Светлячок', 'держал нас в курсе 3 месяца'), ('Егор Гусев', 'главный ждун · 2478 сообщений')]),
           ('', [('Ром🅰️', 'эксперт по сливам · 1230'), ('Александр', '1161 сообщение'), ('^Sonnyk^', '831 сообщение')]),
           ('', [('Deleted Account', 'ушёл, но не забыт · 770'), ('morinos', 'так и не купил PS5'), ('Nikola', '«Держись, братик)»')]),
           ('ОСОБАЯ БЛАГОДАРНОСТЬ', [('Киберлик', 'маркетолог года'), ('Rockstar', '0 постов за 4 дня')]),
           ('ИТОГО', [('17 924', 'сообщения'), ('1 533', 'скриншота'), ('737', 'голосовых'), ('502', 'раза слово «слив»')])]
def credits(c, t):
    rel = (t - B(75)) / BAR; j = min(4, int(rel / 2)); u = (rel - j * 2) / 2
    head, rows = CREDITS[j]
    a = min(1, u * 6) * min(1, (1 - u) * 6)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); y = 420
    if head:
        hi = grad_text(head, 64); lay.alpha_composite(hi, (int(W / 2 - hi.width / 2), y)); y += hi.height + 30
    for nm, role in rows:
        ni = Image.new('RGBA', (W, 80), (0, 0, 0, 0)); fo = font(F_BLACK, 50)
        wdt = sum(fo.getlength(v) if k_ == 't' else 56 for k_, v in tokens(nm))
        draw_rich(ni, ((W - wdt) / 2, 6), nm, fo, WHITE)
        lay.alpha_composite(ni, (0, y)); y += 70
        ri = text_img(role, 32, (255, 200, 120), BLACK, 3, f=F_SB); lay.alpha_composite(ri, (int(W / 2 - ri.width / 2), y)); y += ri.height + 26
    ar = np.array(lay); ar[..., 3] = (ar[..., 3] * a).astype(np.uint8); c.alpha_composite(Image.fromarray(ar))
def final(c, t):
    u = t - B(85)
    lay = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    # retro sun
    sun_y = 1000 - 260 * min(1, u / 1.8)
    sun = Image.new('RGBA', (520, 520), (0, 0, 0, 0)); sd = ImageDraw.Draw(sun)
    for yy in range(520):
        g = yy / 520; col = (int(255), int(70 + 150 * g), int(160 - 120 * g), 255)
        if yy > 260 and (yy // 14) % 3 == 0: continue
        sd.line([(0, yy), (520, yy)], fill=col)
    mk = Image.new('L', (520, 520), 0); ImageDraw.Draw(mk).ellipse([0, 0, 519, 519], fill=255)
    sun.putalpha(Image.fromarray(np.minimum(np.array(sun.getchannel('A')), np.array(mk))))
    glow = Image.new('RGBA', (W, H), (0, 0, 0, 0)); ImageDraw.Draw(glow).ellipse([W / 2 - 360, sun_y - 360, W / 2 + 360, sun_y + 360], fill=(255, 90, 150, 90))
    c.alpha_composite(glow.filter(ImageFilter.GaussianBlur(60)))
    c.alpha_composite(sun, (int(W / 2 - 260), int(sun_y - 260)))
    if u > 1.0:
        a = min(1, (u - 1.0) / 0.6)
        g1 = text_img('GRAND  THEFT  AUTO', 46, WHITE, BLACK, 4, f=F_BLACK); ar = np.array(g1); ar[..., 3] = (ar[..., 3] * a).astype(np.uint8)
        c.alpha_composite(Image.fromarray(ar), (int(W / 2 - g1.width / 2), 250))
    t_vi = B(86) - B(85)
    if u > t_vi:
        v = u - t_vi; s = 1 + 2.2 * math.exp(-v / 0.12)
        vi = grad_text('VI', 360, (255, 90, 170), (255, 190, 70), F_BLACKI, 12)
        if v > 0.4:  # shine sweep
            ar = np.array(vi).astype(np.float32); xs = np.arange(vi.width)[None, :]; pos = ((v - 0.4) % 2.2) / 1.2 * (vi.width + 300) - 150
            band = np.exp(-((xs - pos - (np.arange(vi.height)[:, None] * 0.4)) / 40) ** 2)
            ar[..., :3] = np.clip(ar[..., :3] + band[..., None] * 160 * (ar[..., 3:4] / 255), 0, 255); vi = Image.fromarray(ar.astype(np.uint8))
        vi2 = vi.resize((int(vi.width * s), int(vi.height * s)))
        c.alpha_composite(vi2, (int(W / 2 - vi2.width / 2), int(520 - vi2.height / 2)))
        if v < 0.12: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, int(255 * (1 - v / 0.12)))))
    t_date = B(87) - B(85)
    if u > t_date:
        dt_ = fitw(text_img('19.11.2026', 70, WHITE, BLACK, 6, f=F_BLACKI))
        s = easeback((u - t_date) / 0.3); dt2 = dt_.resize((max(1, int(dt_.width * s)), max(1, int(dt_.height * s))))
        c.alpha_composite(dt2, (int(W / 2 - dt2.width / 2), 760))
    t_cd = B(88) - B(85)
    if u > t_cd:
        v = u - t_cd
        l1 = text_img('ДО РЕЛИЗА ОСТАЛОСЬ', 44, WHITE, BLACK, 5, f=F_BLACK); c.alpha_composite(l1, (int(W / 2 - l1.width / 2), 880))
        l2 = grad_text('МЕНЬШЕ 264 ЧАСОВ', 70, (255, 220, 90), (255, 110, 60), F_BLACKI, 7)
        s = easeback(v / 0.3); l3 = l2.resize((max(1, int(l2.width * s)), max(1, int(l2.height * s))))
        c.alpha_composite(l3, (int(W / 2 - l3.width / 2), 940))
        secs = max(0, 264 * 3600 - 1 - v); hh = int(secs // 3600); mm = int(secs % 3600 // 60); ss = secs % 60
        cd = f'{hh:03d}:{mm:02d}:{ss:05.2f}'
        ci = text_img(cd, 56, (255, 255, 255), BLACK, 5, f=F_MONO); c.alpha_composite(ci, (int(W / 2 - ci.width / 2), 1060))
    if T_END - t < 0.6: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * (1 - (T_END - t) / 0.6)))))

# ---------------- frame ----------------
def render(fi):
    t = fi / FPS; rng = random.Random(fi)
    k, a, b = sec_at(t)
    if k == 'wasted':
        img, _, _, _ = frame_bg(B(38) - 0.05, rng)
        u = (t - B(38)) / (B(40) - B(38)); z = 1.0 + 0.1 * u
        img = cv2.warpAffine(img, cv2.getRotationMatrix2D((W / 2, H / 2), 3 * u, z), (W, H), borderMode=cv2.BORDER_REFLECT)
        img = grade(img, 'wasted')
    elif k == 'final':
        img, _, _, _ = frame_bg(t, rng); img = cv2.GaussianBlur(img, (0, 0), 14)
        u = t - B(85); img = (img.astype(np.float32) * (0.45 * min(1, u / 1.0) + 0.0)).astype(np.uint8)
        y = np.linspace(0, 1, H)[:, None, None]; tint = (np.array([60, 10, 70]) * (1 - y) + np.array([120, 30, 60]) * y)
        img = np.clip(img + tint * min(1, u / 1.0), 0, 255).astype(np.uint8)
    else:
        img, k2, u, j = frame_bg(t, rng); img = grade(img, k)
    c = Image.fromarray(img).convert('RGBA')
    # cut flash
    idx, u, ln, k3, j = shot_at(t)
    if k not in ('wasted', 'final', 'brk', 'dip') and u * ln * BAR < 0.07 and t > 1: c.alpha_composite(Image.new('RGBA', (W, H), (255, 255, 255, 50)))
    if k == 'intro': intro_titles(c, t)
    if k == 'wasted': wasted(c, t)
    if k == 'outro': credits(c, t)
    if k == 'final': final(c, t)
    if k == 'm2':
        fans = sum(1 for x in N_ if 'F' in x['fl'] and x['t'] <= t); haters = sum(1 for x in N_ if 'X' in x['fl'] and x['t'] <= t)
        d = ImageDraw.Draw(c); fo = font(F_BLACKI, 34)
        d.rounded_rectangle([W / 2 - 250, 930, W / 2 + 250, 990], 30, fill=(0, 0, 0, 170))
        d.text((W / 2 - 20, 960), f'ФАНАТЫ {fans}', font=fo, fill=GREEN, anchor='rm'); d.text((W / 2, 960), ':', font=fo, fill=WHITE, anchor='mm')
        d.text((W / 2 + 20, 960), f'{haters} ХЕЙТЕРЫ', font=fo, fill=(255, 90, 90), anchor='lm')
    hud(c, t, k)
    dim = hero_dim(t)
    if dim > 0: c.alpha_composite(Image.new('RGBA', (W, H), (0, 0, 0, int(255 * dim))))
    mission_card(c, t, k, a)
    if k == 'build' and t > B(58.5):
        day = date_at(t); left = max(0, (RELEASE - day).days)
        v = (t - B(58.5)) / (B(60) - B(58.5)); left = int(left - v * (left - 12))
        im = grad_text(f'{left}', 220, (255, 255, 255), PINK); c.alpha_composite(im, (int(W / 2 - im.width / 2), 640))
        l = text_img('ДНЕЙ ДО РЕЛИЗА', 44, WHITE, BLACK, 5, f=F_BLACK); c.alpha_composite(l, (int(W / 2 - l.width / 2), 900))
    draw_notifs(c, t)
    draw_center(c, t)
    return np.array(c.convert('RGB'))

# ---------------- AUDIO ----------------
def build_audio(outp):
    subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', os.path.join(HERE, 'track.mp3'), '-ar', str(SR), '-ac', '2', os.path.join(HERE, 'track.wav')], check=True)
    w = wave.open(os.path.join(HERE, 'track.wav')); tr = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(np.float32).reshape(-1, 2) / 32768
    n = len(tr); fx = np.zeros(n, np.float32); rng = np.random.default_rng(3)
    def add(t0, sig, g=1.0):
        i = int(t0 * SR)
        if i >= n: return
        j = min(n, i + len(sig)); fx[i:j] += g * sig[:j - i]
    def tt(d): return np.arange(int(d * SR)) / SR
    def ding(f1=1318.5, f2=1760.0, g=0.22):
        t = tt(0.5); a = np.sin(2 * np.pi * f1 * t) * np.exp(-t * 14) + 0.3 * np.sin(4 * np.pi * f1 * t) * np.exp(-t * 22)
        t2 = np.clip(t - 0.085, 0, None); b = (np.sin(2 * np.pi * f2 * t2) * np.exp(-t2 * 11) + 0.3 * np.sin(4 * np.pi * f2 * t2) * np.exp(-t2 * 20)) * (t > 0.085)
        return ((a + b) * g * np.minimum(1, t / 0.002)).astype(np.float32)
    def whoosh(d=0.5):
        t = tt(d); x = rng.standard_normal(len(t)) * np.sin(np.pi * t / d) ** 2; return (np.convolve(x, np.ones(14) / 14, 'same') * 0.35).astype(np.float32)
    def boom(d=1.4, f0=90):
        t = tt(d); f = f0 * np.exp(-t * 4) + 34; return np.tanh(2.4 * np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)).astype(np.float32)
    for x in N_:
        if 'C' in x['fl']: add(x['t'], ding(987.8, 1318.5, 0.26), 1.0); continue
        add(x['t'], ding(), 1.0)
        if 'H' in x['fl']: add(x['t'] - 0.12, whoosh(0.3), 0.5); add(x['t'], boom(0.6, 140), 0.25)
    for kk, a, b in SEC:
        if kk in CARDS and kk != 'build': add(B(a) - 0.2, whoosh(0.45), 0.8)
    add(B(38), boom(1.6, 60), 0.6)
    add(B(86), boom(2.0, 70), 0.7); add(B(86) - 0.3, whoosh(0.5), 0.8)
    mix = tr + fx[:, None]
    f = int(0.6 * SR); mix[-f:] *= np.linspace(1, 0, f)[:, None]
    mix = np.tanh(mix * 1.0) * 0.97
    st = (mix * 32767).astype(np.int16)
    w = wave.open(outp, 'wb'); w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes(st.tobytes()); w.close()

if __name__ == '__main__':
    if sys.argv[1] == '--info':
        print(len(N_), 'notifs'); print([(round(x['t'], 1), x['name'][:10], round(x['life'], 1)) for x in N_][:8]); sys.exit()
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
        for fi in range(a, b):
            p.stdin.write(render(fi).tobytes())
        p.stdin.close(); p.wait(); sys.exit()
