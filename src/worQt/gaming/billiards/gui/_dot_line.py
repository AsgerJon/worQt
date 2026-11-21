"""
'dotsOf' samples a line of words, drawn in a font, into the club
board's dot-matrix columns, for letters its 5 by 7 glyphs cannot draw.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QFontMetrics
from PySide6.QtGui import QImage, QPainter

#  Fonts drawing Hangul well at a few pixels, the first there is taken:
#  the Mac's own first, then the free ones, then any Korean font at all.
KOREAN_FONTS = ('Apple SD Gothic Neo', 'Noto Sans CJK KR', 'Noto Sans KR',
                'NanumGothic', 'Malgun Gothic', 'D2Coding')
DOT_ROWS = 13  # rows of dots a sampled line stands in


def dotsOf(text: str, rows: int = DOT_ROWS) -> list[int]:
  """Returns 'text' drawn in a Korean font, unsmoothed, sampled into
  'rows' rows of dots: a column each pixel across, an int whose bit r
  is lit at row r from the top. The font is as large as lets every
  letter of 'text' fit, the letters' band set in the middle of the
  rows. Needs a 'QGuiApplication'."""
  if not text:
    return []
  for size in range(rows + 2, 4, -1):
    lit = _litOf(text, _fontOf(size))
    band = numpy.nonzero(lit.any(axis=1))[0]
    if not len(band) or band[-1] - band[0] + 1 <= rows:
      break
  if not len(band):
    return [0] * lit.shape[1]
  low, high = int(band[0]), int(band[-1]) + 1
  top = low - (rows - (high - low)) // 2
  out = []
  for column in range(lit.shape[1]):
    bits = 0
    for row in range(rows):
      source = top + row
      if 0 <= source < lit.shape[0] and lit[source, column]:
        bits |= 1 << row
    out.append(bits)
  return out


def _fontOf(size: int) -> QFont:
  """Returns a Korean font 'size' pixels high, unsmoothed: the first of
  'KOREAN_FONTS' there is, else any Korean font, else Qt's own, which
  finds the letters where it can."""
  korean = sorted(QFontDatabase.families(
    QFontDatabase.WritingSystem.Korean))
  chosen = [name for name in KOREAN_FONTS if name in korean] + korean
  font = QFont(chosen[0]) if chosen else QFont()
  font.setPixelSize(size)
  font.setStyleStrategy(QFont.StyleStrategy.NoAntialias)
  font.setHintingPreference(QFont.HintingPreference.PreferFullHinting)
  return font


def _litOf(text: str, font: QFont) -> numpy.ndarray:
  """Returns 'text' drawn in 'font', white on black, as which pixels are
  lit: rows by columns."""
  metrics = QFontMetrics(font)
  width = max(metrics.horizontalAdvance(text), 1)
  height = max(metrics.height(), 1)
  image = QImage(width, height, QImage.Format.Format_Grayscale8)
  image.fill(0)
  painter = QPainter(image)
  painter.setFont(font)
  painter.setPen(QColor(255, 255, 255))
  painter.drawText(QRect(0, 0, width, height),
                   Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                   text)
  painter.end()
  line = image.bytesPerLine()
  pixels = numpy.frombuffer(image.constBits(), numpy.uint8, height * line)
  return pixels.reshape(height, line)[:, :width] > 127
