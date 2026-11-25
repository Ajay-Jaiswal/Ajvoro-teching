"""Scene templates.  Each draws one scene at time t (seconds) of duration d, on a 1280x720 logical canvas.
Content must stay above y=600 (the caption bar lives below)."""
import math
from .art import *

def bg(c, th, t):
    c.grad(*th['g']); ambient(c, t, th)

def head(c, title, th, y=56, sz=46):
    if not title: return 100
    ls = c.wrap(title, sz, 1100)[:2]
    for i, l in enumerate(ls): c.t(l, 640, y + i * (sz + 8), sz, th['title'])
    return y + len(ls) * (sz + 8) + 20

def _at(i, n, d, start=0.06, span=0.8):
    return start * d + i * (span * d / max(1, n))

def narration(c, t, d, sc, th):
    bg(c, th, t); idx = sc.get('idx', 0); v = sc.get('var', 0); ic = sc.get('icons') or ['bulb']; n = len(ic); acc = th['acc']
    head(c, sc.get('title'), th)
    kind = 'robot' if idx % 2 == 0 else 'person'; shirt = acc[idx % 5]
    if v == 0:
        c.r(0, 560, 1280, 60, (*th['panel'], 120)); character(c, kind, 250, 570 + 4 * math.sin(2 * t), 1.55, t, 1, shirt)
        for k, i in enumerate(ic):
            z = pr(t, _at(k, n, d), 0.5)
            if z > 0.02: picto(c, i, 640 + k * 210 + (0 if n > 1 else 120), 330 - (1 - z) * 40 + 6 * math.sin(2 * t + k), 78 * (0.6 + 0.4 * z), acc[k % 5])
    elif v == 1:
        for k, i in enumerate(ic):
            z = pr(t, _at(k, n, d), 0.5); x = 640 + (k - (n - 1) / 2) * 280
            if z > 0.02: c.o(x, 350, 112 * z, fill=(*th['panel'], 255)); picto(c, i, x, 350 + 7 * math.sin(2 * t + k), 80 * z, acc[k % 5])
        character(c, 'robot' if idx % 2 else 'person', 1130, 600, 1.0, t, -1, shirt)
    else:
        z = pr(t, 0.2, 0.6)
        for k in range(3): c.o(640, 330, (90 + k * 34) * z, fill=None, ol=(*acc[k % 5], 90), ow=3)
        for k, i in enumerate(ic[:3]): a = t * 0.9 + k * 2.09; picto(c, i, 640 + 190 * math.cos(a), 330 + 120 * math.sin(a), 44, acc[k % 5])
        picto(c, ic[0], 640, 330, 70 * z, acc[0]); character(c, 'person', 230, 600, 1.2, t, 1, shirt); character(c, 'robot', 1050, 600, 1.2, t)

def title(c, t, d, sc, th):
    bg(c, th, t); z = pr(t, 0.2, 0.8); ls = c.wrap(sc['title'], int(40 + 30 * z), 1100)[:2]
    for i, l in enumerate(ls): c.t(l, 640, 150 + i * 84, int(40 + 30 * z), th['fg'])
    if sc.get('sub') and t > 1: c.t(sc['sub'], 640, 150 + len(ls) * 84 + 20, 34, th['sub'])
    robot(c, 640, 640 + 6 * math.sin(2 * t), 1.05, t)

def bullets(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title'), th); its = sc['items']; n = len(its); rh = min(88, (440 - (n - 1) * 12) / n); y0 = 120; acc = th['acc']
    for i, tx in enumerate(its):
        z = pr(t, _at(i, n, d), 0.4)
        if z <= 0.05: continue
        y = y0 + i * (rh + 12) + (1 - z) * 20; c.r(80, y, 800, rh, th['panel'], rad=16); c.o(145, y + rh / 2, min(27, rh / 2 - 6), fill=acc[i % 5])
        c.t(str(i + 1), 145, y + rh / 2, 24, NAVY); c.t(tx, 195, y + rh / 2, 27, th['fg'], 'lm')
    robot(c, 1060, 580, 1.35, t)

def steps(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title') or 'चरण', th); its = sc['items']; n = len(its); acc = th['acc']
    for i, s in enumerate(its):
        x = 90 + (i % 3) * 380; y = 160 + (i // 3) * 190; t0 = _at(i, n, d, 0.08, 0.75); st = 0 if t < t0 else (1 if t < t0 + min(1.2, d * 0.05) else 2)
        c.r(x, y, 340, 130, [th['panel'], acc[1], acc[0]][st], rad=18, ol=(*acc[2], 255) if st == 0 else None, ow=2)
        ls = c.wrap(f'{i + 1}. {s}', 26, 300)[:3]
        for k, l in enumerate(ls): c.t(l, x + 170, y + 65 + (k - (len(ls) - 1) / 2) * 32, 26, NAVY if st else th['fg'])
        if i % 3 < 2 and i < n - 1: c.p_([(x + 348, y + 55), (x + 348, y + 75), (x + 366, y + 65)], acc[2])

def compare(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title'), th); acc = th['acc']
    for s, (hd, its), col in ((0, sc['left'], acc[4]), (1, sc['right'], acc[0])):
        x = 60 + s * 620; c.r(x, 120, 560, 420, th['panel'], rad=20, ol=col, ow=4)
        if hd: c.t(hd, x + 280, 165, 34, col)
        if not its: continue
        for i, tx in enumerate(its):
            z = pr(t, _at(i, len(its), d, 0.1 + s * 0.3, 0.4), 0.4)
            if z > 0.05:
                ls = c.wrap('• ' + tx, 27, 500)[:3]
                for k, l in enumerate(ls): c.t(l, x + 36, 235 + i * 85 + k * 32 + (1 - z) * 14, 27, th['fg'], 'lm')
    c.o(640, 330, 32, fill=acc[1]); c.t('VS', 640, 330, 26, NAVY)

def stat(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title'), th); st = sc['stats']; n = len(st); w = (1140 - (n - 1) * 30) / n
    for i, s in enumerate(st):
        z = pr(t, 0.4 + i * min(1.5, d * 0.15), 1.4); x = 70 + i * (w + 30)
        c.r(x, 150, w, 330, th['panel'], rad=22); v = s['val'] * z
        txt = (f'{v:.1f}' if s['val'] != int(s['val']) else f'{int(v)}') + s['suf'].strip() if s['suf'].strip() == '%' else (f'{v:.1f}' if s['val'] != int(s['val']) else f'{int(v)}')
        c.t(txt, x + w / 2, 260, 88 if n < 3 else 70, th['title'])
        if s['suf'].strip() != '%': c.t(s['suf'].strip(), x + w / 2, 335, 30, th['sub'])
        for k, l in enumerate(c.wrap(s['label'], 26, w - 40)[:2]): c.t(l, x + w / 2, 395 + k * 34, 26, th['fg'])

def timeline(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title'), th, 56, 44); ev = sc['events']; n = len(ev); acc = th['acc']
    c.l([(70, 320), (1210, 320)], (*th['panel'], 255), 5); gap = 1140 / max(1, n)
    for i, (y, lb) in enumerate(ev):
        z = pr(t, _at(i, n, d), 0.4); cx = 70 + gap * (i + 0.5)
        if z > 0.05: c.t(y, cx, 250, 36, th['sub']); c.o(cx, 320, 12 + 4 * z, fill=acc[i % 5]); [c.t(l, cx, 385 + k * 28, 22, th['fg']) for k, l in enumerate(c.wrap(lb, 22, gap - 10)[:2])]

def question(c, t, d, sc, th):
    bg(c, th, t); idx = sc.get('idx', 0); person(c, 250, 600, 1.7, shirt=th['acc'][1], look=1)
    for i in range(6): c.t('?', 120 + i * 90, 340 - ((t * 40 + i * 90) % 220), 40, (*th['acc'][2], 255))
    z = pr(t, 0.3, 0.5)
    if z > 0.05: wbubble(c, sc['question'], 800, 250 + (1 - z) * 20, 700, 34)

def dialogue(c, t, d, sc, th):
    bg(c, th, t); dl = sc['dlg']; sp = []; 
    for s, _ in dl:
        if s not in sp: sp.append(s)
    person(c, 130, 640, 1.0, shirt=th['acc'][0], look=1); robot(c, 1150, 640, 0.95, t)
    for k, (s, tx) in enumerate(dl[:6]):
        z = pr(t, _at(k, min(6, len(dl)), d, 0.05, 0.85), 0.35)
        if z <= 0.05: continue
        left = sp.index(s) % 2 == 0; x = 480 if left else 800; y = 90 + k * 88 + (1 - z) * 12
        wbubble(c, tx, x, y, 520, 22, fill=WH if left else GOLD)
        c.t(s, 290 if left else 1010, y - 38, 20, th['sub'])

def bars(c, t, d, sc, th):
    bg(c, th, t); head(c, sc.get('title'), th); rows = sc['bars']; mx = max(v for _, v in rows) or 1; n = len(rows); rh = min(70, 400 / n)
    for i, (lb, v) in enumerate(rows):
        z = pr(t, _at(i, n, d, 0.08, 0.6), 1.0); y = 130 + i * (rh + 20); c.t(lb, 70, y + rh / 2, 26, th['fg'], 'lm'); bw = 640 * v / mx * z
        c.r(330, y, max(4, bw), rh, th['acc'][i % 5], rad=10); c.t(f'{v * z:.4g}', 330 + bw + 16, y + rh / 2, 30, th['acc'][i % 5], 'lm')

def quote(c, t, d, sc, th):
    bg(c, th, t); txt = sc.get('title') or sc['text']; ls = c.wrap(txt, 50, 1050)[:4]
    for i, l in enumerate(ls):
        z = pr(t, 0.2 + i * 0.35, 0.5)
        if z > 0.05: c.t(l, 640, 150 + i * 76 + (1 - z) * 16, 52, [th['fg'], th['title'], th['sub']][i % 3])
    character(c, 'person', 430, 625, 1.0, t, 1, th['acc'][1]); robot(c, 850, 625, 1.0, t)

def outro(c, t, d, sc, th):
    bg(c, th, t); c.r(470, 120, 340, 220, (235, 40, 40), rad=50); c.p_([(600, 170), (600, 290), (700, 230)], WH)
    c.t(sc.get('title') or 'धन्यवाद!', 640, 405, 50, th['title']); c.t(sc.get('sub') or 'Like · Share · Subscribe', 640, 475, 34, th['fg'])
    b = 14 * math.sin(t * 5) if int(t) % 3 == 0 else 0; c.o(860, 135, 26, fill=SAF); c.p_([(834, 160), (886, 160), (860, 184 + b / 6)], SAF)

FN = dict(narration=narration, title=title, bullets=bullets, steps=steps, compare=compare, stat=stat, timeline=timeline,
          question=question, dialogue=dialogue, bars=bars, quote=quote, outro=outro)
