"""Frame loop -> ffmpeg.  Streams frames straight into the encoder, so RAM stays small (a few hundred MB at most)."""
import subprocess, math
from pathlib import Path
from PySide6.QtCore import QRectF
from .canvas import Canvas, init
from .art import THEMES, WH
from .templates import FN
from .planner import chunks
from .audio import ffmpeg

SIZES = {'480p': 854, '720p': 1280, '1080p': 1920}


def cap_chunks(sc):
    ch = chunks(sc.get('text', '')); tot = sum(len(x) for x in ch) or 1
    out, a = [], 0.0
    for x in ch: l = len(x) / tot * sc['secs']; out.append((a, a + l, x)); a += l
    return out


def srt(scenes):
    def ts(x): h = int(x // 3600); m = int(x % 3600 // 60); s = x % 60; return f'{h:02d}:{m:02d}:{int(s):02d},{int((s % 1) * 1000):03d}'
    out, n, st = [], 1, 0.0
    for sc in scenes:
        for a, b, x in cap_chunks(sc): out.append(f'{n}\n{ts(st + a)} --> {ts(st + b - 0.05)}\n{x}\n'); n += 1
        st += sc['secs']
    return '\n'.join(out)


def _caption(c, text, size=26, y=612, h=96):
    ls = c.wrap(text, size, 1100)
    if len(ls) > 2: size = 22; ls = c.wrap(text, size, 1100)
    c.r(50, y, 1180, h, (8, 10, 28, 235), rad=14); y0 = y + h / 2 - (len(ls) - 1) * 17
    for k, l in enumerate(ls[:3]): c.t(l, 640, y0 + k * 34, size, WH)


def draw_scene(c, sc, t, th, st, caps):
    sc['idx'] = sc.get('idx', 0)
    FN[sc['tpl']](c, t, sc['secs'], sc, th)
    if st.get('watermark'): c.t(st['watermark'], 1240, 28, 20, (255, 255, 255, 140), 'rm')
    if st.get('captions', True) and caps:
        cur = caps[-1][2]
        for a, b, x in caps:
            if t < b: cur = x; break
        _caption(c, cur)


def frame_size(st):
    w = SIZES.get(st.get('res', '720p'), 1280)
    if st.get('aspect', '16:9') == '9:16': w = {854: 480, 1280: 720, 1920: 1080}[w]; return w, w * 16 // 9 // 2 * 2
    return w, w * 9 // 16 // 2 * 2


def preview(sc, st, frac, out):
    init(st.get('font')); th = THEMES[st.get('theme', 'Midnight')]
    cc = Canvas(1280, 720); sc = dict(sc); draw_scene(cc, sc, sc['secs'] * frac, th, dict(st, captions=st.get('aspect') != '9:16'), cap_chunks(sc))
    cc.save(out); cc.close()


def render(scenes, st, out, audio=None, progress=None):
    init(st.get('font')); th = THEMES[st.get('theme', 'Midnight')]; fps = int(st.get('fps', 15)); W, H = frame_size(st); vert = st.get('aspect') == '9:16'
    cc = Canvas(1280, 720) if vert else Canvas(W, H)
    fc = Canvas(W, H, W, H) if vert else None
    for i, s in enumerate(scenes): s['idx'] = i
    nfs = [max(1, round(s['secs'] * fps)) for s in scenes]; total = sum(nfs); total_s = total / fps
    cmd = [ffmpeg(), '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr0', '-s', f'{W}x{H}', '-r', str(fps), '-i', '-']
    if audio: cmd += ['-i', str(audio)]
    cmd += ['-c:v', 'libx264', '-preset', st.get('preset', 'veryfast'), '-crf', str(st.get('crf', 23)), '-pix_fmt', 'yuv420p']
    if audio: cmd += ['-c:a', 'aac', '-b:a', '160k', '-t', f'{total_s:.3f}']
    cmd += ['-movflags', '+faststart', str(out)]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE); done = 0
    try:
        for sc, nf in zip(scenes, nfs):
            caps = cap_chunks(sc); sc['secs'] = nf / fps; d = sc['secs']
            for k in range(nf):
                t = k / fps; a = min(1, t / 0.35, (d - t) / 0.35)
                if vert:
                    draw_scene(cc, sc, t, th, dict(st, captions=False), caps); cc.fade(a)
                    fc.grad(*th['g']); fh = W * 606 / 1200
                    fc.p.drawImage(QRectF(0, 120, W, fh), cc.img, QRectF(40, 0, 1200, 606))
                    if st.get('captions', True):
                        cur = caps[-1][2]
                        for x0, x1, x in caps:
                            if t < x1: cur = x; break
                        ls = fc.wrap(cur, 40, W - 70)[:6]
                        for j, l in enumerate(ls): fc.t(l, W / 2, 120 + fh + 90 + j * 56, 40, (255, 255, 255))
                    p.stdin.write(fc.data())
                else:
                    draw_scene(cc, sc, t, th, st, caps); cc.fade(a); p.stdin.write(cc.data())
                done += 1
                if progress and done % 10 == 0: progress(done, total)
    finally:
        p.stdin.close(); p.wait(); cc.close()
        if fc: fc.close()
    if progress: progress(total, total)
    return dict(video=str(out), seconds=total_s, frames=total)
