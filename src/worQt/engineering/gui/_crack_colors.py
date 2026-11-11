"""
The colours cracks are drawn in: by how far a face has given, on a scale
from a micrometre to a millimetre.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QColor, QLinearGradient

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPainter

  from ...utils import WFont

CRACK_LEAST = 0.001  # mm: the scale's bottom, and the narrowest drawn
CRACK_MOST = 1.0  # mm: the scale's top
_STOPS = 16  # stops of the scale's gradient
CRACK_LEVELS = 24  # colours cracks are drawn in, a colour at a time
_FAINTEST = 0.15  # how opaque the narrowest crack is drawn
_BOTTOM, _TOP = 0.08, 0.92  # of turbo used, its darkest ends left out
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
#  Turbo, Google's rainbow for heat maps, as polynomials in the share
_TURBO = (
  (
    0.13572138, 4.61539260, -42.66032258, 132.13108234, -152.94239396,
    59.28637943
  ),
  (
    0.09140261, 2.19418839, 4.84296658, -14.18503333, 4.27729857,
    2.82956604
  ),
  (
    0.10667330, 12.64194608, -60.58204836, 110.36276771, -89.90310912,
    27.34824973
  ),
)


def crackShare(size: float) -> float:
  """The 'crackShare' function returns how far up the scale a crack
  'size' mm across is: evenly in the logarithm from a micrometre to a
  millimetre, kept at the ends."""
  if size <= CRACK_LEAST:
    return 0.0
  share = math.log(size / CRACK_LEAST) / math.log(CRACK_MOST / CRACK_LEAST)
  return min(share, 1.0)


def _turbo(share: float) -> tuple[float, float, float]:
  """The turbo colour at 'share' of the way up, red, green and blue."""
  out = []
  for terms in _TURBO:
    value = 0.0
    for term in reversed(terms):
      value = value * share + term
    out.append(min(max(value, 0.0), 1.0))
  return out[0], out[1], out[2]


def _scaleColor(share: float) -> QColor:
  """The colour 'share' of the way up the scale: turbo, but for its
  darkest ends, which the paste would hide."""
  return QColor.fromRgbF(*_turbo(_BOTTOM + (_TOP - _BOTTOM) * share))


def crackColor(size: float) -> QColor:
  """The 'crackColor' function returns the colour of a crack 'size' mm
  across: blue at a micrometre, through green and yellow, red at a
  millimetre."""
  return _scaleColor(crackShare(size))


def crackLevel(size: float) -> int:
  """The 'crackLevel' function returns which of the 'CRACK_LEVELS'
  colours a crack 'size' mm across is drawn in, so cracks are drawn a
  colour at a time."""
  return min(
    int(crackShare(size) * (CRACK_LEVELS - 1) + 0.5),
    CRACK_LEVELS - 1
    )


def levelColor(level: int) -> QColor:
  """The 'levelColor' function returns the colour of crack level
  'level', the narrower the fainter, so the wide cracks stand out of
  the many narrow ones."""
  share = level / (CRACK_LEVELS - 1)
  color = _scaleColor(share)
  color.setAlphaF(_FAINTEST + (1.0 - _FAINTEST) * share)
  return color


def crackTicks() -> list[tuple[float, str]]:
  """The 'crackTicks' function returns where the scale is read and what
  each reading says: each tenfold from a micrometre to a millimetre."""
  out = []
  for size, label in (
      (0.001, '1 µm'), (0.01, '10 µm'), (0.1, '100 µm'),
      (1.0, '1 mm')
  ):
    out.append((crackShare(size), label))
  return out


def paintCrackScale(painter: QPainter, rect: QRectF, font: WFont) -> None:
  """The 'paintCrackScale' function paints the scale in 'rect': its ends'
  readings either side of a bar coloured from bottom to top, with a
  tick at each tenfold."""
  metrics = font.metrics
  low, high = crackTicks()[0][1], crackTicks()[-1][1]
  lowWidth = metrics.horizontalAdvance(low) + 6.0
  highWidth = metrics.horizontalAdvance(high) + 6.0
  bar = QRectF(
    rect.left() + lowWidth, rect.center().y() - 4.0,
    rect.width() - lowWidth - highWidth, 8.0
    )
  gradient = QLinearGradient(bar.topLeft(), bar.topRight())
  for index in range(_STOPS + 1):
    share = index / _STOPS
    gradient.setColorAt(share, _scaleColor(share))
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(gradient)
  painter.drawRect(bar)
  painter.setBrush(Qt.BrushStyle.NoBrush)
  painter.setFont(font)
  painter.setPen(font.color.Q)
  for share, _ in crackTicks()[1:-1]:
    x = bar.left() + share * bar.width()
    painter.drawLine(QPointF(x, bar.top() - 2.0), QPointF(x, bar.top()))
  lowRect = QRectF(rect.left(), rect.top(), lowWidth - 4.0, rect.height())
  painter.drawText(lowRect, _RIGHT, low)
  highRect = QRectF(bar.right() + 4.0, rect.top(), highWidth, rect.height())
  painter.drawText(highRect, _LEFT, high)
