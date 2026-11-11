"""
The 'handPicture' function paints a gloved bridge hand, and
'cuePicture' the cue resting in it, seen from above, two pictures laid
one over the other on the cloth behind ball 1 in the view from above,
so the cue may slide back and forth through the bridge.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QImage, QLinearGradient
from PySide6.QtGui import QPainter, QPainterPath, QPen, QPolygonF

#  The picture on the cloth, in mm: how long, along the cue, from where
#  the cue fades out to its tip; and how wide across. The tip is at the
#  right edge, the cue along the middle, the bridge hand on the left of
#  it, as a right-handed player bent over the shot sees it.
HAND_LENGTH = 700.0
HAND_WIDTH = 240.0
_PIXELS = 1024  # the picture's pixels along
#  How far the cue may be drawn back, in mm, its tip short of the bridge.
STROKE_MOST = 140.0
#  The stroke, in shares of the time before the cue meets the ball: still
#  at the address until the first, drawn back until the second, held
#  until the third, then sent on to the ball.
_STROKE_SHARES = (0.12, 0.62, 0.76)
FOLLOW_SECONDS = 0.15  # s the cue follows through after meeting the ball
FOLLOW_SHARE = 0.4  # of the backswing, how far on past the ball it goes

_GLOVE_BACK = QColor(14, 15, 17)
_GLOVE_FRONT = QColor(44, 46, 52)
_GLOVE_EDGE = QColor(2, 2, 3)
_GOLD = QColor(229, 192, 123)
_SKIN = QColor(219, 168, 131)
_SKIN_EDGE = QColor(150, 98, 66)
_SLEEVE = QColor(40, 44, 52)
_SLEEVE_EDGE = QColor(16, 17, 20)
_SHADOW = QColor(0, 0, 0, 70)
_MAPLE_EDGE = QColor(201, 166, 112)
_MAPLE = QColor(246, 232, 200)
_MAPLE_DARK = QColor(170, 132, 82)
_FERRULE = QColor(246, 243, 233)
_CHALK = QColor(63, 120, 200)

#  The bridge, in mm, the tip at 'HAND_LENGTH', the cue along y nought,
#  the player's left at y below nought. Each finger from under the palm
#  to its tip, how thick at its root and at its tip, and whether the
#  glove covers it: the index and middle finger do, the ring and little
#  finger lie bare. The thumb lies along the cue, under it, its tip
#  showing past it.
_FINGERS = (
  (True, (482.0, -12.0), (577.0, -23.0), 18.0, 15.0),
  (True, (478.0, -34.0), (587.0, -51.0), 18.5, 15.5),
  (False, (470.0, -54.0), (569.0, -76.0), 17.0, 14.0),
  (False, (460.0, -70.0), (534.0, -92.0), 15.0, 12.5),
)
_THUMB = ((452.0, -5.0), (533.0, 9.0), 20.0, 16.0)
#  The back of the gloved hand, round through these, the knuckles ahead.
_PALM = ((496.0, -9.0), (489.0, -42.0), (478.0, -75.0), (446.0, -87.0),
         (406.0, -70.0), (393.0, -38.0), (405.0, -11.0), (448.0, -2.0))
#  The forearm, back from the wrist toward the player, bare a little
#  way, then in its sleeve, fading out.
_WRIST = (398.0, -40.0)
_ELBOW = (200.0, -128.0)
_BARE = 34.0  # mm of bare wrist out of the glove
_ARM_WIDTHS = (50.0, 70.0)  # at the wrist and at the elbow
_FADE = 260.0  # mm from the cue's back end, over which it fades in
_EDGE_FADE = 22.0  # mm in from the left edge, over which it fades in


def handPicture() -> QImage:
  """The 'handPicture' function returns the bridge hand: gloved, the
  thumb, index and middle finger in black, the ring and little finger
  bare, a gold stripe at the cuff, the forearm going back in its
  sleeve; its shadow on the cloth; all fading out away from where the
  cue's tip rests, at the picture's right edge. The rest is clear."""
  image, painter = _canvas()
  _paintHandShadow(painter)
  _paintArm(painter)
  _paintHand(painter)
  _paintFade(painter)
  painter.end()
  return image


def cuePicture() -> QImage:
  """The 'cuePicture' function returns the cue as it rests in the
  bridge of 'handPicture', the same size, to lie over it: a maple
  shaft, its white ferrule and chalked tip at the picture's right edge,
  its shadow on the cloth, fading out toward the back. The rest is
  clear."""
  image, painter = _canvas()
  _paintCueShadow(painter)
  _paintCue(painter)
  _paintFade(painter)
  painter.end()
  return image


def cueBackAt(seconds: float, wait: float, most: float) -> float:
  """The 'cueBackAt' function returns how far back the cue is drawn
  through the bridge, in mm, 'seconds' after the player settles over a
  shot that meets the ball 'wait' seconds later, the backswing 'most':
  still a moment at the address; drawn back smoothly; held a moment at
  the back; sent on, ever faster, meeting the ball at 'wait'; then on
  through where the ball was, slowing, 'FOLLOW_SHARE' of the backswing
  past it after 'FOLLOW_SECONDS', and held there."""
  if seconds >= wait:
    after = min((seconds - wait) / FOLLOW_SECONDS, 1.0)
    return -FOLLOW_SHARE * most * (1.0 - (1.0 - after) ** 2)
  share = max(seconds, 0.0) / wait
  address, back, hold = _STROKE_SHARES
  if share <= address:
    return 0.0
  if share < back:
    u = (share - address) / (back - address)
    return most * u * u * (3.0 - 2.0 * u)
  if share < hold:
    return most
  u = (share - hold) / (1.0 - hold)
  return most * (1.0 - u * u)


def _canvas() -> tuple[QImage, QPainter]:
  """Returns a clear picture 'HAND_LENGTH' by 'HAND_WIDTH' mm and a
  painter on it in mm, the tip's end of the cue's line at the right
  edge, y nought along the middle."""
  height = round(_PIXELS * HAND_WIDTH / HAND_LENGTH)
  image = QImage(_PIXELS, height, QImage.Format.Format_ARGB32_Premultiplied)
  image.fill(Qt.GlobalColor.transparent)
  painter = QPainter(image)
  painter.setRenderHint(QPainter.RenderHint.Antialiasing)
  scale = _PIXELS / HAND_LENGTH
  painter.scale(scale, scale)
  painter.translate(0.0, 0.5 * HAND_WIDTH)
  return image, painter


def _smoothLoop(points: tuple) -> QPainterPath:
  """Returns a closed curve through 'points', round at each, as a
  Catmull-Rom spline runs."""
  count = len(points)
  path = QPainterPath(QPointF(*points[0]))
  for k in range(count):
    p0, p1 = points[k - 1], points[k]
    p2, p3 = points[(k + 1) % count], points[(k + 2) % count]
    first = QPointF(p1[0] + (p2[0] - p0[0]) / 6.0,
                    p1[1] + (p2[1] - p0[1]) / 6.0)
    second = QPointF(p2[0] - (p3[0] - p1[0]) / 6.0,
                     p2[1] - (p3[1] - p1[1]) / 6.0)
    path.cubicTo(first, second, QPointF(*p2))
  path.closeSubpath()
  return path


def _taper(start: tuple, end: tuple, root: float,
           tip: float) -> QPainterPath:
  """Returns a tapering bar from 'start' to 'end', 'root' thick at the
  start and 'tip' at the end, the end rounded."""
  ux, uy = end[0] - start[0], end[1] - start[1]
  length = math.hypot(ux, uy)
  ux, uy = ux / length, uy / length
  nx, ny = -uy, ux
  r, t = 0.5 * root, 0.5 * tip
  bulge = 1.33 * t
  path = QPainterPath(QPointF(start[0] + nx * r, start[1] + ny * r))
  path.lineTo(end[0] + nx * t, end[1] + ny * t)
  path.cubicTo(QPointF(end[0] + nx * t + ux * bulge,
                       end[1] + ny * t + uy * bulge),
               QPointF(end[0] - nx * t + ux * bulge,
                       end[1] - ny * t + uy * bulge),
               QPointF(end[0] - nx * t, end[1] - ny * t))
  path.lineTo(start[0] - nx * r, start[1] - ny * r)
  path.closeSubpath()
  return path


def _fill(painter: QPainter, path: QPainterPath, brush: QBrush | QColor,
          edge: QColor, width: float) -> None:
  """Fills 'path' with 'brush', outlined 'width' thick in 'edge'."""
  pen = QPen(edge, width, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
             Qt.PenJoinStyle.RoundJoin)
  painter.setPen(pen)
  painter.setBrush(brush)
  painter.drawPath(path)


def _cuePath() -> QPainterPath:
  """Returns the shaft's outline: 20 mm thick at the picture's back
  edge, 12 mm at the ferrule."""
  ferrule = HAND_LENGTH - 24.0
  path = QPainterPath()
  path.addPolygon(QPolygonF([QPointF(0.0, -10.0), QPointF(ferrule, -6.1),
                             QPointF(ferrule, 6.1), QPointF(0.0, 10.0)]))
  path.closeSubpath()
  return path


def _handPaths() -> list[QPainterPath]:
  """Returns the hand's parts that cast a shadow: the palm, the fingers
  and the thumb."""
  paths = [_smoothLoop(_PALM)]
  for _, start, end, root, tip in _FINGERS:
    paths.append(_taper(start, end, root, tip))
  paths.append(_taper(*_THUMB))
  return paths


def _armWay() -> tuple[float, float]:
  """Returns the way back from the wrist to the elbow, of length one."""
  ax, ay = _ELBOW[0] - _WRIST[0], _ELBOW[1] - _WRIST[1]
  length = math.hypot(ax, ay)
  return ax / length, ay / length


def _paintHandShadow(painter: QPainter) -> None:
  """Paints the hand's shadow on the cloth, close under it."""
  painter.save()
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(_SHADOW)
  painter.translate(2.5, 3.5)
  for path in _handPaths():
    painter.drawPath(path)
  painter.restore()


def _paintCueShadow(painter: QPainter) -> None:
  """Paints the cue's shadow on the cloth, further off than the
  hand's, as it rides above the cloth."""
  painter.save()
  painter.setPen(Qt.PenStyle.NoPen)
  painter.setBrush(_SHADOW)
  painter.translate(6.5, 8.5)
  painter.drawPath(_cuePath())
  painter.restore()


def _paintArm(painter: QPainter) -> None:
  """Paints the forearm going back from the wrist: a little bare, then
  in its sleeve, fading out toward the elbow."""
  ax, ay = _armWay()
  wx, wy = _WRIST
  cuff = (wx + ax * _BARE, wy + ay * _BARE)
  wrist, elbow = _ARM_WIDTHS
  _fill(painter, _taper(cuff, _WRIST, 0.5 * (wrist + elbow) - 8.0,
                        wrist), _SKIN, _SKIN_EDGE, 1.4)
  fade = QLinearGradient(QPointF(*cuff), QPointF(*_ELBOW))
  fade.setColorAt(0.0, _SLEEVE)
  fade.setColorAt(0.55, QColor(_SLEEVE.red(), _SLEEVE.green(),
                               _SLEEVE.blue(), 150))
  fade.setColorAt(1.0, QColor(_SLEEVE.red(), _SLEEVE.green(),
                              _SLEEVE.blue(), 0))
  edge = QColor(_SLEEVE_EDGE)
  edge.setAlpha(120)
  sleeve = _taper(_ELBOW, cuff, elbow + 6.0, 0.5 * (wrist + elbow))
  _fill(painter, sleeve, QBrush(fade), edge, 1.2)


def _paintHand(painter: QPainter) -> None:
  """Paints the bridge hand: the fingers, the gloved back of the hand
  over their roots, the thumb along the cue, the gold stripe at the
  cuff."""
  for gloved, start, end, root, tip in reversed(_FINGERS):
    path = _taper(start, end, root, tip)
    if gloved:
      _fill(painter, path, _glovedBrush(start, end), _GLOVE_EDGE, 1.6)
    else:
      _fill(painter, path, _SKIN, _SKIN_EDGE, 1.4)
  palm = _smoothLoop(_PALM)
  shine = QLinearGradient(QPointF(*_WRIST), QPointF(500.0, -30.0))
  shine.setColorAt(0.0, _GLOVE_BACK)
  shine.setColorAt(1.0, _GLOVE_FRONT)
  _fill(painter, palm, QBrush(shine), _GLOVE_EDGE, 1.6)
  _paintCuff(painter)
  start, end, root, tip = _THUMB
  _fill(painter, _taper(start, end, root, tip), _glovedBrush(start, end),
        _GLOVE_EDGE, 1.6)


def _glovedBrush(start: tuple, end: tuple) -> QBrush:
  """Returns the glove's black, lighter toward the tip of a finger
  from 'start' to 'end', as the light catches the leather."""
  shine = QLinearGradient(QPointF(*start), QPointF(*end))
  shine.setColorAt(0.0, _GLOVE_BACK)
  shine.setColorAt(0.7, _GLOVE_FRONT)
  shine.setColorAt(1.0, _GLOVE_BACK)
  return QBrush(shine)


def _paintCuff(painter: QPainter) -> None:
  """Paints the gold stripe across the glove's cuff, just in from the
  wrist."""
  ax, ay = _armWay()
  wx, wy = _WRIST
  across = 0.5 * _ARM_WIDTHS[0] - 1.0
  cx, cy = wx - 9.0 * ax, wy - 9.0 * ay
  pen = QPen(_GOLD, 3.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
  painter.setPen(pen)
  painter.drawLine(QPointF(cx - ay * across, cy + ax * across),
                   QPointF(cx + ay * across, cy - ax * across))


def _paintCue(painter: QPainter) -> None:
  """Paints the cue resting in the bridge: the maple shaft, lit along
  its middle, the ferrule and the chalked tip."""
  shading = QLinearGradient(0.0, -10.0, 0.0, 10.0)
  shading.setColorAt(0.0, _MAPLE_EDGE)
  shading.setColorAt(0.35, _MAPLE)
  shading.setColorAt(1.0, _MAPLE_DARK)
  _fill(painter, _cuePath(), QBrush(shading), _MAPLE_DARK.darker(170),
        1.0)
  painter.setPen(QPen(_FERRULE.darker(135), 0.9))
  painter.setBrush(_FERRULE)
  painter.drawRect(QRectF(HAND_LENGTH - 24.0, -6.1, 18.0, 12.2))
  tip = QPainterPath(QPointF(HAND_LENGTH - 6.0, -6.0))
  tip.lineTo(HAND_LENGTH - 3.0, -6.0)
  tip.quadTo(HAND_LENGTH, -6.0, HAND_LENGTH, 0.0)
  tip.quadTo(HAND_LENGTH, 6.0, HAND_LENGTH - 3.0, 6.0)
  tip.lineTo(HAND_LENGTH - 6.0, 6.0)
  tip.closeSubpath()
  _fill(painter, tip, _CHALK, _CHALK.darker(150), 0.9)


def _paintFade(painter: QPainter) -> None:
  """Fades all out toward the back edge, away from the tip, and toward
  the edge on the left, where the sleeve leaves the picture."""
  painter.setCompositionMode(
    QPainter.CompositionMode.CompositionMode_DestinationIn)
  top = -0.5 * HAND_WIDTH
  fades = ((QLinearGradient(0.0, 0.0, _FADE, 0.0),
            QRectF(0.0, top, _FADE, HAND_WIDTH)),
           (QLinearGradient(0.0, top, 0.0, top + _EDGE_FADE),
            QRectF(0.0, top, HAND_LENGTH, _EDGE_FADE)))
  for fade, rect in fades:
    fade.setColorAt(0.0, QColor(0, 0, 0, 0))
    fade.setColorAt(1.0, QColor(0, 0, 0, 255))
    painter.fillRect(rect, QBrush(fade))
