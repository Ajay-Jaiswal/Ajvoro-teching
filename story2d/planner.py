"""Text -> scene plan.  Rule-based (no AI model needed), so it is instant and light on RAM."""
import re, io
from .art import find_icons

TEMPLATES = ['narration', 'title', 'bullets', 'steps', 'compare', 'stat', 'timeline', 'question', 'dialogue', 'bars', 'quote', 'outro']
TAGS = {t: t for t in TEMPLATES}; TAGS.update({'list': 'bullets', 'stats': 'stat', 'number': 'stat', 'vs': 'compare', 'chat': 'dialogue', 'chart': 'bars'})
YEAR = re.compile(r'(?<!\d)(1[0-9]{3}|20[0-9]{2})(?!\d)')
NUM = re.compile(r'(\d[\d,]*\.?\d*)\s*(%|प्रतिशत|percent|million|billion|trillion|मिलियन|बिलियन|ट्रिलियन|करोड़|लाख|अरब|crore|lakh)', re.I)
VS = re.compile(r'\b(?:vs\.?|versus)\b|बनाम', re.I)
BUL = re.compile(r'^\s*(?:[-•*▪●]|\d+[.)]|[०-९]+[.)])\s+(.*)$')
SPK = re.compile(r'^\s*([^\s:：\-#\[][^:：]{0,18}?)\s*[:：]\s*(.+)$')


def read_script(name, data: bytes) -> str:
    if name.lower().endswith('.docx'):
        import docx
        d = docx.Document(io.BytesIO(data))
        return '\n'.join(p.text for p in d.paragraphs)
    for enc in ('utf-8-sig', 'utf-16', 'cp1252'):
        try: return data.decode(enc)
        except Exception: pass
    return data.decode('utf-8', 'ignore')


def cps_for(text):
    dev = sum(1 for ch in text if '\u0900' <= ch <= '\u097f'); return 14.6 if dev > 0.25 * max(1, len(text)) else 13.0


def short(s, n=44):
    s = re.sub(r'\s+', ' ', s).strip(' ,;:-–—।.')
    if len(s) <= n: return s
    cut = s[:n].rsplit(' ', 1)[0]; return (cut or s[:n]) + '…'


def sentences(text):
    return [x.strip() for x in re.split(r'(?<=[।?!\.])\s+', text) if x.strip()]


def chunks(text, lo=40, hi=105, mx=130):
    out, acc = [], ''
    for s in sentences(text):
        if acc and len(acc) + 1 + len(s) <= hi and len(acc) < lo: acc += ' ' + s
        else:
            if acc: out.append(acc)
            acc = s
    if acc: out.append(acc)
    fin = []
    for q in out:
        while len(q) > mx:
            w = q.split(' '); m = len(w) // 2
            if m == 0: break
            fin.append(' '.join(w[:m])); q = ' '.join(w[m:])
        fin.append(q)
    return fin or ['']


STOP = {'और', 'में', 'का', 'की', 'के', 'को', 'से', 'है', 'हैं', 'ने', 'पर', 'यह', 'वह', 'तो', 'भी', 'the', 'a', 'an', 'of', 'and', 'in', 'to', 'is'}


def auto_title(text):
    m = re.search(r'\b([A-Z][A-Za-z0-9\-\.]{2,}(?:\s+[A-Z][A-Za-z0-9\-]+){0,2})', text)
    if m and len(m.group(1)) >= 3: return short(m.group(1), 28)
    first = sentences(text)[0] if sentences(text) else text
    w = first.split()[:4]
    while len(w) > 1 and w[-1].strip(',।.?!') in STOP: w.pop()
    return short(' '.join(w), 28)


def _kv_pairs(text):
    return [(a.strip(), b.strip()) for a, b in re.findall(r'([^:;|\n]+?)\s*[:：]\s*([\d.,]+)', text)]


def payload(sc):
    """(re)compute the template data from sc['text'] and sc['tpl']"""
    t, tpl, lines = sc['text'], sc['tpl'], sc.get('lines') or [sc['text']]
    sc['icons'] = find_icons(t, 3)
    if not sc.get('title'): sc['title'] = auto_title(t) if tpl in ('narration', 'question') else sc.get('title', '')
    if tpl in ('bullets', 'steps'):
        its = [m.group(1) for l in lines if (m := BUL.match(l))]
        if not its: its = [short(s, 44) for s in sentences(t)[:6]]
        sc['items'] = [short(i, 44) for i in its[:7]]
    elif tpl == 'compare':
        if '|' in t:
            parts = [p.strip() for p in t.split('|', 1)]; sides = []
            for p in parts:
                if ':' in p: h, r = p.split(':', 1); sides.append((short(h, 24), [short(x, 36) for x in re.split(r'[;；]', r) if x.strip()][:4]))
                else: sides.append((short(p, 24), []))
            sc['left'], sc['right'] = sides[0], sides[1] if len(sides) > 1 else ('', [])
        else:
            m = VS.search(t)
            if m:
                a, b = t[:m.start()], t[m.end():]; sa, sb = sentences(a), sentences(b)
                sc['left'] = (short(' '.join(a.split()[-3:]), 24), [short(sa[-1], 40)] if sa else [])
                sc['right'] = (short(' '.join(b.split()[:3]), 24), [short(sb[0], 40)] if sb else [])
            else:
                ss = sentences(t); h = max(1, len(ss) // 2)
                sc['left'] = ('', [short(s, 40) for s in ss[:h]][:4]); sc['right'] = ('', [short(s, 40) for s in ss[h:]][:4])
    elif tpl == 'stat':
        st = []
        for m in NUM.finditer(t):
            val = float(m.group(1).replace(',', '')); unit = m.group(2); pct = unit in ('%', 'प्रतिशत') or unit.lower() == 'percent'
            rest = t[m.end():].split(); lab = ' '.join(rest[:5]) if rest else ' '.join(t[:m.start()].split()[-4:])
            st.append(dict(val=val, suf='%' if pct else ' ' + unit, label=short(lab, 34)))
            if len(st) == 3: break
        if not st: sc['tpl'] = 'narration'; return payload(sc)
        sc['stats'] = st
    elif tpl == 'timeline':
        ev, seen = [], set()
        for m in YEAR.finditer(t):
            if m.group(1) in seen: continue
            seen.add(m.group(1)); rest = re.split(r'[,।.;:]|(?<!\d)(?:1[0-9]{3}|20[0-9]{2})', t[m.end():], 1)[0].split()
            rest = [w for w in rest if w not in STOP][:3]
            ev.append((m.group(1), short(' '.join(rest), 18)))
        sc['events'] = ev[:7] or [('', '')]
    elif tpl == 'dialogue':
        sc['dlg'] = [(m.group(1).strip(), m.group(2).strip()) for l in lines if (m := SPK.match(l))] or [('', t)]
    elif tpl == 'bars':
        kv = _kv_pairs(t)
        sc['bars'] = [(short(a, 26), float(b.replace(',', ''))) for a, b in kv if re.match(r'^[\d.,]+$', b)][:6] or [('', 1.0)]
    elif tpl in ('outro', 'title'):
        a = [x.strip() for x in t.split('|', 1)]; sc['title'] = a[0]; sc['sub'] = a[1] if len(a) > 1 else sc.get('sub', '')
    elif tpl == 'question':
        qs = [s for s in sentences(t) if s.endswith('?')]; sc['question'] = (qs[-1] if qs else sentences(t)[0] if sentences(t) else t)
    return sc


def detect(lines, text):
    sp = [m.group(1).strip() for l in lines if (m := SPK.match(l))]
    if len(sp) >= 2 and len(set(sp)) >= 2: return 'dialogue'
    bl = [BUL.match(l) for l in lines]
    if sum(1 for b in bl if b) >= 2: return 'steps' if all(re.match(r'^\s*(\d+|[०-९]+)[.)]', l) for l, b in zip(lines, bl) if b) else 'bullets'
    if VS.search(text): return 'compare'
    if len(set(YEAR.findall(text))) >= 3: return 'timeline'
    if NUM.search(text) and len(text) < 330: return 'stat'
    ss = sentences(text)
    if ss and ss[-1].endswith('?') and len(text) < 240: return 'question'
    return 'narration'


def parse(text, mode='Story', target_secs=20, cps=None, blank_break='auto'):
    cps = cps or cps_for(text)
    if blank_break == 'auto':
        blocks = [b for b in re.split(r'\n\s*\n', text) if b.strip()]; blank_break = 2 <= len(blocks) <= 70 and len(text) / max(1, len(blocks)) > 45
    groups, cur, est, tag, title = [], [], 0.0, None, ''
    def flush():
        nonlocal cur, est, tag, title
        if cur or tag: groups.append((cur, tag, title))
        cur, est, tag, title = [], 0.0, None, ''
    for raw in text.splitlines():
        ln = raw.strip()
        if not ln:
            if blank_break or est >= 0.5 * target_secs: flush()
            continue
        if ln == '---': flush(); continue
        m = re.match(r'^\[(\w+)\]\s*(.*)$', ln)
        if m and m.group(1).lower() in TAGS:
            flush(); tag = TAGS[m.group(1).lower()]
            if m.group(2): cur.append(m.group(2)); est += len(m.group(2)) / cps
            continue
        if ln.startswith('#'):
            flush(); title = ln.lstrip('#').strip(); continue
        if cur and not tag and (bool(BUL.match(ln)) != bool(BUL.match(cur[-1]))): flush()
        if est >= target_secs and not tag: flush()
        cur.append(ln); est += len(ln) / cps
    flush(); scenes, nar = [], 0
    rot = [0, 2, 0, 1] if mode == 'Story' else [1, 0, 1, 2]
    for lines, tag, title in groups:
        if not lines: continue
        text_ = ' '.join(re.sub(r'^\s*(?:[-•*▪●]|\d+[.)])\s+', '', l) for l in lines) if not tag == 'dialogue' else '\n'.join(lines)
        sc = dict(tpl=tag or detect(lines, ' '.join(lines)), title=title, text=' '.join(lines) if (tag or '') != 'dialogue' else ' '.join(lines), lines=lines, mode=mode)
        sc['text'] = ' '.join(BUL.sub(lambda m: m.group(1), l) if BUL.match(l) else l for l in lines)
        if sc['tpl'] == 'narration': sc['var'] = rot[nar % 4]; nar += 1
        else: sc['var'] = 0
        scenes.append(payload(sc))
    for s in scenes: s['chars'] = len(s['text'])
    return scenes


def allocate(scenes, total=None, cps=None, minsec=3.0):
    cps = cps or cps_for(' '.join(s['text'] for s in scenes))
    for s in scenes: s['secs'] = max(minsec, s.get('chars', len(s['text'])) / cps)
    if total:
        for _ in range(4):
            k = (total - 0) / sum(s['secs'] for s in scenes)
            for s in scenes: s['secs'] = max(minsec, s['secs'] * k)
            if abs(sum(s['secs'] for s in scenes) - total) < 0.5: break
    return scenes


def title_card(title, sub=''): return dict(tpl='title', title=title, sub=sub, text=title + (' — ' + sub if sub else ''), lines=[title], icons=[], var=0, chars=len(title), secs=5.0, mode='Story')
def outro_card(title='धन्यवाद!', sub='Like · Share · Subscribe'): return dict(tpl='outro', title=title, sub=sub, text=title + ' ' + sub, lines=[title], icons=[], var=0, chars=len(title), secs=6.0, mode='Story')
