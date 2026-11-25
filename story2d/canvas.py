"""Tiny 2D drawing layer on top of Qt (QPainter). Works offscreen, no GPU, shapes Hindi correctly."""
import os
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from pathlib import Path
from PySide6.QtGui import (QGuiApplication, QImage, QPainter, QColor, QFont, QFontDatabase,
                           QFontMetricsF, QLinearGradient, QPen, QBrush, QPolygonF)
from PySide6.QtCore import Qt, QPointF, QRectF

LW, LH = 1280, 720          # logical canvas; everything is drawn in these units
PREFERRED = ['Nirmala UI', 'Noto Sans Devanagari', 'Mangal', 'Kohinoor Devanagari', 'Lohit Devanagari', 'FreeSans']
_state = {'app': None, 'family': None}


def init(font_family=None):
    if QGuiApplication.instance() is None:
        _state['app'] = QGuiApplication([])
    for f in (Path(__file__).resolve().parent.parent / 'fonts').glob('*.ttf'):
        QFontDatabase.addApplicationFont(str(f))
    fams = set(QFontDatabase.families())
    _state['family'] = font_family if font_family in fams else next((f for f in PREFERRED if f in fams), 'FreeSans')
    return _state['family']


def available_fonts():
    init(); return sorted(QFontDatabase.families())


def _col(c):
    return QColor(*c) if c is not None else None


class Canvas:
    def __init__(self, w=1280, h=720, lw=LW, lh=LH):
        if _state['family'] is None: init()
        self.w, self.h, self.lw, self.lh = w, h, lw, lh
        self.img = QImage(w, h, QImage.Format_RGB32)
        self.p = QPainter(self.img)
        self.p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.p.scale(w / lw, h / lh)
        self._fonts = {}

    # ---- helpers
    def font(self, sz, bold=True):
        k = (round(sz), bold)
        if k not in self._fonts:
            f = QFont(_state['family']); f.setPixelSize(max(4, round(sz))); f.setBold(bold)
            f.setHintingPreference(QFont.PreferNoHinting); self._fonts[k] = f
        return self._fonts[k]

    def tw(self, txt, sz, bold=True):
        return QFontMetricsF(self.font(sz, bold)).horizontalAdvance(txt)

    def wrap(self, txt, sz, maxw, bold=True):
        out, cur = [], ''
        for w in txt.split(' '):
            tr = (cur + ' ' + w).strip()
            if self.tw(tr, sz, bold) <= maxw or not cur: cur = tr
            else: out.append(cur); cur = w
        out.append(cur); return out

    def _pen(self, ol, ow):
        self.p.setPen(QPen(_col(ol), ow) if ol else Qt.NoPen)

    def _brush(self, fill):
        self.p.setBrush(QBrush(_col(fill)) if fill else Qt.NoBrush)

    # ---- drawing
    def grad(self, top, bot):
        g = QLinearGradient(0, 0, 0, self.lh); g.setColorAt(0, _col(top)); g.setColorAt(1, _col(bot))
        self.p.fillRect(QRectF(0, 0, self.lw, self.lh), QBrush(g))

    def r(self, x, y, w, h, fill, rad=0, ol=None, ow=2):
        self._pen(ol, ow); self._brush(fill)
        if rad: self.p.drawRoundedRect(QRectF(x, y, w, h), rad, rad)
        else: self.p.drawRect(QRectF(x, y, w, h))

    def o(self, cx, cy, rx, ry=None, fill=(255, 255, 255), ol=None, ow=2):
        self._pen(ol, ow); self._brush(fill); self.p.drawEllipse(QPointF(cx, cy), rx, rx if ry is None else ry)

    def p_(self, pts, fill):
        self._pen(None, 0); self._brush(fill); self.p.drawPolygon(QPolygonF([QPointF(x, y) for x, y in pts]))

    def l(self, pts, col=(255, 255, 255), w=3):
        pen = QPen(_col(col), w); pen.setCapStyle(Qt.RoundCap); pen.setJoinStyle(Qt.RoundJoin)
        self.p.setPen(pen); self.p.setBrush(Qt.NoBrush); self.p.drawPolyline(QPolygonF([QPointF(x, y) for x, y in pts]))

    def arc(self, cx, cy, rx, ry, a0, a1, col, w=3):
        """angles in degrees, clockwise from 3 o'clock (a0<a1) - so 20..160 is a smile"""
        pen = QPen(_col(col), w); pen.setCapStyle(Qt.RoundCap); self.p.setPen(pen); self.p.setBrush(Qt.NoBrush)
        self.p.drawArc(QRectF(cx - rx, cy - ry, 2 * rx, 2 * ry), int(-a1 * 16), int((a1 - a0) * 16))

    def t(self, txt, x, y, sz, fill=(255, 255, 255), anchor='mm', bold=True):
        f = self.font(sz, bold); fm = QFontMetricsF(f); w = fm.horizontalAdvance(txt)
        px = x - w / 2 if anchor[0] == 'm' else (x if anchor[0] == 'l' else x - w)
        self.p.setPen(_col(fill)); self.p.setFont(f)
        self.p.drawText(QPointF(px, y + (fm.ascent() - fm.descent()) / 2 - fm.descent() * 0.15), txt)

    def fade(self, a):
        if a < 1: self.r(0, 0, self.lw, self.lh, (0, 0, 0, int(255 * (1 - max(0, a)))))

    def close(self):
        if self.p.isActive(): self.p.end()

    def __del__(self):
        try: self.close()
        except Exception: pass

    def data(self):
        return bytes(self.img.constBits())

    def save(self, path):
        self.p.end(); self.img.save(str(path)); self.p.begin(self.img)
        self.p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform)
        self.p.scale(self.w / self.lw, self.h / self.lh)
