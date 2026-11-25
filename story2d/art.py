"""Characters, icons, themes and small drawing helpers."""
import math, random

NAVY = (11, 16, 38); SAF = (255, 159, 28); TEAL = (46, 196, 182); LIL = (142, 154, 255)
GOLD = (255, 209, 102); RED = (255, 90, 95); WH = (244, 246, 255); IND = (108, 122, 224)

THEMES = {
    'Midnight': dict(g=((11, 16, 38), (30, 36, 90)), panel=(26, 34, 80), fg=(244, 246, 255), title=SAF, sub=GOLD, stars=True,
                     acc=[TEAL, SAF, LIL, GOLD, RED]),
    'Classroom (light)': dict(g=((247, 249, 255), (211, 224, 250)), panel=(255, 255, 255), fg=(26, 32, 66), title=(214, 100, 0), sub=(60, 80, 190), stars=False,
                              acc=[(0, 150, 136), (240, 130, 0), (92, 107, 230), (225, 160, 0), (215, 55, 70)]),
    'Sunset': dict(g=((58, 28, 92), (244, 132, 90)), panel=(80, 44, 120), fg=(255, 248, 240), title=(255, 214, 120), sub=(255, 235, 190), stars=True,
                   acc=[(70, 220, 200), (255, 190, 60), (190, 170, 255), (255, 225, 130), (255, 110, 110)]),
    'Forest': dict(g=((9, 38, 34), (28, 98, 78)), panel=(18, 64, 56), fg=(236, 250, 244), title=(255, 200, 80), sub=(170, 240, 210), stars=False,
                   acc=[(90, 220, 170), (255, 170, 50), (150, 190, 255), (255, 220, 110), (255, 120, 110)]),
}


def ease(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)


def pr(t, t0, dur=0.6): return ease((t - t0) / dur)


_ST = [(random.Random(i).random() * 1280, random.Random(i + 99).random() * 600, random.Random(i + 5).random() * 6) for i in range(60)]


def ambient(c, t, th):
    """slow background life: twinkling stars (dark themes) or drifting bubbles (light themes)"""
    if th['stars']:
        for x, y, ph in _ST: c.o(x, y, 1.3 + 1.1 * math.sin(t * 2 + ph) ** 2, fill=(210, 215, 255))
    else:
        for i in range(10):
            x = (i * 137 + t * (10 + i * 2)) % 1380 - 50; y = 120 + (i * 61) % 440 + 12 * math.sin(t + i)
            c.o(x, y, 10 + (i % 4) * 7, fill=(*th['acc'][i % 5], 40))


def person(c, x, y, s=1, shirt=TEAL, hair=(30, 30, 40), skin=(240, 190, 150), legs=True, look=1):
    if legs:
        for dx in (-22, 4): c.r(x + dx * s, y - 70 * s, 18 * s, 70 * s, (40, 44, 90), rad=6 * s)
    by = y - (70 if legs else 0) * s - 90 * s
    c.r(x - 32 * s, by, 64 * s, 90 * s, shirt, rad=16 * s)
    for sx in (-1, 1):
        c.l([(x + sx * 32 * s, by + 16 * s), (x + sx * 46 * s, by + 72 * s)], shirt, 12 * s); c.o(x + sx * 46 * s, by + 74 * s, 7 * s, fill=skin)
    hy = by - 30 * s; c.o(x, hy - 8 * s, 31 * s, 27 * s, hair); c.o(x + look * 2 * s, hy + 3 * s, 27 * s, 27 * s, skin)
    for dx in (-9, 9): c.o(x + (dx + look * 4) * s, hy + 3 * s, 3 * s, fill=(30, 30, 40))
    c.arc(x + look * 4 * s, hy + 10 * s, 10 * s, 7 * s, 20, 160, (150, 70, 70), 2 * s)


def robot(c, x, y, s=1, t=0, face='on', col=IND):
    for dx in (-26, 8): c.r(x + dx * s, y - 40 * s, 18 * s, 40 * s, (40, 44, 90), rad=5 * s)
    c.r(x - 45 * s, y - 140 * s, 90 * s, 100 * s, col, rad=18 * s)
    c.o(x, y - 92 * s, 11 * s * (1 + 0.15 * math.sin(4 * t)), fill=SAF)
    for sx in (-1, 1): c.r(x + (sx * 58 - 8) * s, y - 130 * s, 16 * s, 70 * s, col, rad=8 * s)
    c.r(x - 52 * s, y - 226 * s, 104 * s, 82 * s, (150, 160, 255), rad=18 * s); c.r(x - 40 * s, y - 216 * s, 80 * s, 62 * s, NAVY, rad=12 * s)
    if face == 'on':
        bl = 0.15 if (t % 3.2) < 0.12 else 1
        for dx in (-22, 6): c.r(x + dx * s, y - 196 * s + (1 - bl) * 8 * s, 16 * s, 18 * s * bl, TEAL, rad=4 * s)
        c.arc(x, y - 172 * s, 12 * s, 8 * s, 20, 160, TEAL, 2.5 * s)
    else: c.t('?', x, y - 185 * s, 44 * s, (150, 160, 180))
    c.l([(x, y - 226 * s), (x, y - 250 * s)], (150, 160, 255), 3 * s); c.o(x, y - 253 * s, 7 * s * (1 + 0.2 * math.sin(5 * t)), fill=SAF)


def character(c, kind, x, y, s, t, look=1, shirt=TEAL):
    if kind == 'robot': robot(c, x, y, s, t)
    else: person(c, x, y, s, shirt=shirt, look=look)


def bubble(c, txt, x, y, w, h, sz=26, fill=WH, tc=NAVY, tail=None):
    c.r(x - w / 2, y - h / 2, w, h, fill, rad=18)
    if tail: c.p_([(tail[0] - 12, y + h / 2 - 2), (tail[0] + 12, y + h / 2 - 2), (tail[1], tail[2])], fill)
    c.t(txt, x, y, sz, tc)


def wbubble(c, txt, x, y, maxw=520, sz=25, fill=WH, tc=NAVY, left=True):
    ls = c.wrap(txt, sz, maxw - 40)[:3]; h = 26 + len(ls) * (sz + 8); w = max(c.tw(l, sz) for l in ls) + 44
    c.r(x - w / 2, y - h / 2, w, h, fill, rad=18)
    for i, l in enumerate(ls): c.t(l, x, y - h / 2 + 22 + sz / 2 + i * (sz + 8), sz, tc)
    return h


def chip(c, txt, x, y, w, col, pp, sz=26, tc=NAVY):
    if pp <= 0.05: return
    yy = y + (1 - pp) * 18; c.r(x - w / 2, yy - 24, w, 48, col, rad=24); c.t(txt, x, yy, sz, tc)


def picto(c, k, x, y, r, col):
    """icon inside a coloured circle"""
    c.o(x, y, r, fill=col); u = r / 40; D = NAVY
    if k == 'doctor': c.r(x - 5 * u, y - 18 * u, 10 * u, 36 * u, D); c.r(x - 18 * u, y - 5 * u, 36 * u, 10 * u, D)
    elif k in ('teacher', 'edu', 'book'): c.r(x - 22 * u, y - 14 * u, 20 * u, 28 * u, D, rad=3 * u); c.r(x + 2 * u, y - 14 * u, 20 * u, 28 * u, D, rad=3 * u)
    elif k == 'designer': c.o(x, y, 20 * u, 16 * u, fill=D); [c.o(x + dx * u, y + dy * u, 4 * u, fill=col) for dx, dy in ((-8, -4), (0, -8), (8, -3))]
    elif k in ('coder', 'soft'): c.t('</>', x, y, 30 * u, D)
    elif k == 'factory': c.r(x - 20 * u, y - 2 * u, 40 * u, 20 * u, D); c.r(x + 8 * u, y - 20 * u, 8 * u, 20 * u, D); c.r(x - 14 * u, y - 12 * u, 8 * u, 10 * u, D)
    elif k == 'warehouse': c.r(x - 20 * u, y, 18 * u, 18 * u, D); c.r(x + 2 * u, y, 18 * u, 18 * u, D); c.r(x - 10 * u, y - 18 * u, 18 * u, 18 * u, D)
    elif k == 'farm': c.l([(x, y + 18 * u), (x, y - 6 * u)], D, 4 * u); c.o(x - 9 * u, y - 8 * u, 9 * u, 5 * u, fill=D); c.o(x + 9 * u, y - 14 * u, 9 * u, 5 * u, fill=D)
    elif k == 'car': c.r(x - 22 * u, y - 6 * u, 44 * u, 18 * u, D, rad=6 * u); c.r(x - 12 * u, y - 16 * u, 24 * u, 12 * u, D, rad=5 * u); [c.o(x + dx * u, y + 14 * u, 6 * u, fill=col, ol=D, ow=3) for dx in (-12, 12)]
    elif k == 'health': c.o(x - 7 * u, y - 6 * u, 8 * u, fill=D); c.o(x + 7 * u, y - 6 * u, 8 * u, fill=D); c.p_([(x - 14 * u, y - 2 * u), (x + 14 * u, y - 2 * u), (x, y + 16 * u)], D)
    elif k in ('fun', 'video'): c.r(x - 22 * u, y - 15 * u, 44 * u, 30 * u, D, rad=5 * u); c.p_([(x - 6 * u, y - 8 * u), (x - 6 * u, y + 8 * u), (x + 8 * u, y)], col)
    elif k == 'biz': c.r(x - 20 * u, y - 8 * u, 40 * u, 24 * u, D, rad=4 * u); c.r(x - 8 * u, y - 16 * u, 16 * u, 8 * u, None, rad=3 * u, ol=D, ow=3 * u)
    elif k == 'image': c.r(x - 22 * u, y - 16 * u, 44 * u, 32 * u, D, rad=4 * u); c.p_([(x - 18 * u, y + 12 * u), (x - 4 * u, y - 6 * u), (x + 4 * u, y + 4 * u), (x + 10 * u, y - 2 * u), (x + 18 * u, y + 12 * u)], col); c.o(x + 10 * u, y - 8 * u, 4 * u, fill=col)
    elif k == 'mic': c.r(x - 7 * u, y - 18 * u, 14 * u, 26 * u, D, rad=7 * u); c.arc(x, y, 13 * u, 13 * u, 0, 180, D, 3 * u); c.l([(x, y + 13 * u), (x, y + 20 * u)], D, 3 * u)
    elif k == 'layers': [c.r(x - 20 * u + i * 5 * u, y - 18 * u + i * 12 * u, 36 * u, 12 * u, D if i % 2 == 0 else WH, rad=3 * u) for i in range(3)]
    elif k == 'robot': c.r(x - 18 * u, y - 14 * u, 36 * u, 28 * u, D, rad=7 * u); [c.o(x + dx * u, y - 2 * u, 4 * u, fill=col) for dx in (-8, 8)]; c.l([(x, y - 14 * u), (x, y - 22 * u)], D, 3 * u)
    elif k == 'coin': c.o(x, y, 20 * u, fill=D); c.t('₹', x, y, 26 * u, col)
    elif k == 'chart': [c.r(x - 20 * u + i * 14 * u, y + 16 * u - h * u, 10 * u, h * u, D) for i, h in enumerate((14, 24, 36))]
    elif k == 'globe': c.o(x, y, 20 * u, fill=None, ol=D, ow=3 * u); c.o(x, y, 8 * u, 20 * u, fill=None, ol=D, ow=2.5 * u); c.l([(x - 20 * u, y), (x + 20 * u, y)], D, 2.5 * u)
    elif k == 'bulb': c.o(x, y - 4 * u, 14 * u, fill=D); c.r(x - 7 * u, y + 8 * u, 14 * u, 10 * u, D, rad=2 * u)
    elif k == 'phone': c.r(x - 12 * u, y - 20 * u, 24 * u, 40 * u, D, rad=5 * u); c.r(x - 8 * u, y - 15 * u, 16 * u, 26 * u, col, rad=2 * u)
    elif k == 'lock': c.r(x - 15 * u, y - 4 * u, 30 * u, 22 * u, D, rad=4 * u); c.arc(x, y - 4 * u, 10 * u, 12 * u, 180, 360, D, 4 * u)
    elif k == 'clock': c.o(x, y, 19 * u, fill=None, ol=D, ow=3.5 * u); c.l([(x, y), (x, y - 12 * u)], D, 3 * u); c.l([(x, y), (x + 9 * u, y + 4 * u)], D, 3 * u)
    elif k == 'people': [c.o(x + dx * u, y - 8 * u, 7 * u, fill=D) for dx in (-12, 12)]; [c.r(x + dx * u - 9 * u, y + 2 * u, 18 * u, 16 * u, D, rad=6 * u) for dx in (-12, 12)]
    elif k == 'rocket': c.o(x, y, 8 * u, 20 * u, fill=D); c.p_([(x - 8 * u, y + 10 * u), (x - 16 * u, y + 22 * u), (x - 4 * u, y + 16 * u)], D); c.p_([(x + 8 * u, y + 10 * u), (x + 16 * u, y + 22 * u), (x + 4 * u, y + 16 * u)], D)
    elif k == 'building': c.r(x - 14 * u, y - 20 * u, 28 * u, 40 * u, D); [c.r(x - 8 * u + (i % 2) * 10 * u, y - 14 * u + (i // 2) * 12 * u, 6 * u, 6 * u, col) for i in range(6)]
    else: c.o(x, y, 12 * u, fill=D)


# keyword -> icon (Hindi + English); first matches in the text are used as visual keywords
ICON_WORDS = [
    ('robot', ['ai ', ' ai', 'एआई', 'रोबोट', 'robot', 'artificial', 'मशीन', 'machine', 'chatgpt', 'gpt']),
    ('coder', ['कोड', 'code', 'program', 'प्रोग्राम', 'software', 'सॉफ्टवेयर', 'कंप्यूटर', 'computer', 'algorithm']),
    ('book', ['शिक्षा', 'पढ़', 'स्कूल', 'school', 'education', 'student', 'छात्र', 'शिक्षक', 'teacher', 'किताब', 'book']),
    ('coin', ['पैसा', 'पैसे', 'निवेश', 'invest', 'money', 'salary', 'सैलरी', 'रुपये', 'dollar', 'कीमत', 'price', 'फंडिंग', 'funding']),
    ('chart', ['ग्रोथ', 'वृद्धि', 'बढ़', 'growth', 'profit', 'sales', 'डेटा', 'data', 'रिपोर्ट', 'report', 'आँकड़']),
    ('globe', ['दुनिया', 'world', 'देश', 'country', 'global', 'भारत', 'india']),
    ('bulb', ['विचार', 'idea', 'सोच', 'think', 'सीख', 'learn', 'समझ', 'सवाल', 'question']),
    ('health', ['स्वास्थ्य', 'health', 'डॉक्टर', 'doctor', 'अस्पताल', 'hospital', 'प्यार', 'love']),
    ('factory', ['फैक्ट्री', 'factory', 'उद्योग', 'industry', 'plant', 'steel', 'स्टील', 'मशीनें']),
    ('car', ['गाड़ी', ' car', 'सड़क', 'road', 'vehicle', 'ट्रक']),
    ('phone', ['मोबाइल', 'phone', ' app', 'ऐप', 'internet', 'इंटरनेट']),
    ('lock', ['सुरक्षा', 'security', 'privacy', 'password', 'सुरक्षित']),
    ('clock', ['समय', ' time', 'घंटा', 'minute', 'सेकंड', 'second', 'घंटों']),
    ('people', ['लोग', 'people', 'team', 'कर्मचारी', 'employee', 'users', 'इंसान', 'human', 'नौकरी', 'job']),
    ('video', ['वीडियो', 'video', 'फिल्म', 'movie', 'camera', 'कैमरा']),
    ('mic', ['आवाज़', 'आवाज', 'voice', 'audio', 'music', 'गाना']),
    ('image', ['तस्वीर', 'image', 'photo', 'चित्र', 'design', 'डिज़ाइन']),
    ('rocket', ['स्टार्टअप', 'startup', 'launch', 'future', 'भविष्य', 'रफ़्तार', 'तेज़ी', 'तेज़']),
    ('farm', ['खेत', 'farm', 'किसान', 'पौधा']),
    ('building', ['शहर', 'city', 'building', 'कंपनी', 'company', 'office', 'ऑफिस']),
]


def find_icons(text, n=3):
    low = ' ' + text.lower() + ' '; hits = []
    for kind, words in ICON_WORDS:
        pos = [low.find(w) for w in words if w in low]
        if pos: hits.append((min(pos), kind))
    hits.sort(); return [k for _, k in hits[:n]]
