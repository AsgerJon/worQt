"""
WheelDial shows where the steering wheel is (user, 2026-11-12: "an
indicator of the current position of the steering wheel from -135 to
135 degrees"): a three-spoked wheel drawn turned as it is, its top
marked, on a scale from 135 degrees left (-135) to 135 right, lit from
straight to where it is; beside it the angle in degrees (left negative)
and which way, and whether the mouse holds it.

MouseHands steers with the mouse as a first person game turns the head
(user, 2026-11-12: "put in mouse control of steering. like first
person walking sim, but where i steer the wheels instead"): taken
('take') on a surface (a widget, or the GPU's window), the pointer is
hidden and put back in the middle as it strays; its sideways moves add
up ('steered' hands them over, px, right up, and forgets them), each
read from the nearer of where the pointer last was and where it was
put ('frames'), as the walking view's; 'letGo' frees it, 'forget'
drops the frames when the pointer leaves.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QCursor, QFont, QPainter, QPen
from PySide6.QtWidgets import QWidget

from .._steering import WHEEL_LOCK

#  How far a pixel of the mouse turns the steering wheel, rad (lock to
#  lock 1080 px; 5 degrees of wheel, a turn at 30 m/s, 20 px).
MOUSE_STEER = math.radians(0.25)
#  The dial's size, px; the scale's middle and radius, the wheel's rim's
#  radius and the hub's, px.
_WIDTH, _HEIGHT = 200, 92
_MIDDLE, _SCALE, _RIM, _HUB = QPointF(46.0, 46.0), 40.0, 27.0, 6.0
#  Its tones: the panel, the scale, its lit part, the rim, the spokes,
#  the hub (the horn), the top's mark, the words and the dim words.
_PANEL = QColor(30, 33, 37)
_TRACK = QColor(62, 67, 75)
_LIT = QColor(240, 176, 80)
_RIM_TONE = QColor(150, 156, 166)
_SPOKE = QColor(200, 205, 213)
_HORN = QColor(245, 200, 40)
_TOP = QColor(232, 72, 44)
_WORDS = QColor(235, 238, 242)
_DIM = QColor(141, 147, 155)


def _on(degrees: float, radius: float) -> QPointF:
  """The '_on' function returns the point 'radius' px from the dial's
  middle, 'degrees' clockwise from straight up."""
  way = math.radians(degrees)
  return QPointF(_MIDDLE.x() + radius * math.sin(way),
                 _MIDDLE.y() - radius * math.cos(way))


def _sized(font: QFont, share: float, bold: bool) -> QFont:
  """The '_sized' function returns 'font' grown by 'share', bold or
  not (sized in points, or in pixels should it be so)."""
  out = QFont(font)
  if out.pointSizeF() > 0.0:
    out.setPointSizeF(share * out.pointSizeF())
  else:
    out.setPixelSize(max(1, int(round(share * out.pixelSize()))))
  out.setBold(bold)
  return out


class WheelDial(QWidget):
  """WheelDial shows the steering wheel's 'angle' (rad, left positive),
  set by 'setAngle'."""

  def __init__(self, ) -> None:
    QWidget.__init__(self)
    self.angle, self.mouse = 0.0, False
    self.setFixedSize(_WIDTH, _HEIGHT)
    self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
    self.setToolTip('The steering wheel: A or Left turns it left, D or '
                    'Right right; let go, it comes back to straight')

  def setAngle(self, angle: float) -> None:
    """Shows the wheel at 'angle', rad, left positive."""
    if angle != self.angle:
      self.angle = angle
      self.update()

  def setMouse(self, mouse: bool) -> None:
    """Shows whether the mouse holds the wheel."""
    if mouse != self.mouse:
      self.mouse = mouse
      self.update()

  def paintEvent(self, event: object) -> None:
    """Paints the panel, the scale, the wheel and the words."""
    shown = -math.degrees(self.angle)
    painter = QPainter(self)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_PANEL)
    painter.drawRoundedRect(QRectF(self.rect()), 6.0, 6.0)
    self._paintScale(painter, shown)
    self._paintWheel(painter, shown)
    self._paintWords(painter, shown)
    painter.end()

  def _paintScale(self, painter: QPainter, shown: float) -> None:
    """Paints the scale from -135 to 135 degrees round the wheel, a tick
    every 45 (longer at the locks and straight ahead), lit from straight
    to 'shown' (degrees clockwise, right positive)."""
    lock = math.degrees(WHEEL_LOCK)
    box = QRectF(_MIDDLE.x() - _SCALE, _MIDDLE.y() - _SCALE,
                 2.0 * _SCALE, 2.0 * _SCALE)
    pen = QPen(_TRACK, 4.0)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawArc(box, int(16 * (90.0 + lock)), int(-16 * 2.0 * lock))
    pen.setColor(_LIT)
    painter.setPen(pen)
    painter.drawArc(box, 16 * 90, int(round(-16 * shown)))
    pen = QPen(_DIM, 1.5)
    painter.setPen(pen)
    for tick in range(-3, 4):
      degrees = tick * lock / 3.0
      inner = _SCALE - (7.0 if tick in (-3, 0, 3) else 4.0)
      painter.drawLine(_on(degrees, inner), _on(degrees, _SCALE - 2.0))

  def _paintWheel(self, painter: QPainter, shown: float) -> None:
    """Paints the wheel turned 'shown' degrees clockwise: rim, three
    spokes (to the sides and down, as the car's), the hub, and a mark at
    its top."""
    painter.save()
    painter.translate(_MIDDLE)
    painter.rotate(shown)
    pen = QPen(_SPOKE, 3.0)
    pen.setCapStyle(Qt.PenCapStyle.RoundCap)
    painter.setPen(pen)
    for end in ((-_RIM, 0.0), (_RIM, 0.0), (0.0, _RIM)):
      painter.drawLine(QPointF(0.0, 0.0), QPointF(*end))
    painter.setPen(QPen(_RIM_TONE, 5.0))
    painter.setBrush(Qt.BrushStyle.NoBrush)
    painter.drawEllipse(QPointF(0.0, 0.0), _RIM, _RIM)
    pen = QPen(_TOP, 5.0)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    painter.setPen(pen)
    painter.drawLine(QPointF(0.0, -_RIM - 2.5), QPointF(0.0, -_RIM + 2.5))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.setBrush(_HORN)
    painter.drawEllipse(QPointF(0.0, 0.0), _HUB, _HUB)
    painter.restore()

  def _paintWords(self, painter: QPainter, shown: float) -> None:
    """Paints 'Steering wheel', the angle in degrees (left negative) and
    which way, right of the dial."""
    degrees = int(round(shown))
    way = 'left' if degrees < 0 else 'right' if degrees > 0 else 'straight'
    left = _MIDDLE.x() + _SCALE + 14.0
    painter.setFont(_sized(self.font(), 0.85, False))
    painter.setPen(_DIM)
    painter.drawText(QPointF(left, 22.0), 'Wheel: mouse' if self.mouse
                     else 'Steering wheel')
    painter.drawText(QPointF(left, 76.0), way)
    painter.setFont(_sized(self.font(), 1.7, True))
    painter.setPen(_WORDS)
    painter.drawText(QPointF(left, 55.0), '%+d°' % degrees if degrees
                     else '0°')


class MouseHands:
  """
  MouseHands steers with the mouse on 'surface' (a widget or a window):
  'taken' while it does, the sideways px not yet handed over in
  'moved'.
  """

  def __init__(self, surface: object) -> None:
    self.surface, self.taken, self.frames, self.moved = (surface, False,
                                                          [], 0.0)

  def take(self, ) -> None:
    """The 'take' method takes the mouse: the pointer hidden, put in the
    middle."""
    self.taken, self.frames, self.moved = True, [], 0.0
    self.surface.setCursor(QCursor(Qt.CursorShape.BlankCursor))
    self._recentre()

  def letGo(self, ) -> None:
    """The 'letGo' method lets the mouse go, the pointer shown."""
    if self.taken:
      self.surface.unsetCursor()
    self.taken, self.frames = False, []

  def forget(self, ) -> None:
    """The 'forget' method forgets where the pointer was (it left the
    surface: coming back in elsewhere must steer nothing)."""
    self.frames = []

  def steered(self, ) -> float:
    """The 'steered' method returns how far the mouse has moved sideways
    since last asked, px (right up), and forgets it."""
    moved, self.moved = self.moved, 0.0
    return moved

  def movedTo(self, at: QPointF, local: QPointF) -> None:
    """The 'movedTo' method notes the pointer at 'at' (on the screen),
    'local' on the surface: its move from the nearer frame added up,
    the pointer put back in the middle should it stray a quarter of the
    surface off it."""
    if not self.taken:
      return
    frames = self.frames
    if not frames:
      frames.append(at)
    nearest = min(range(len(frames)), key=lambda k: abs(
      at.x() - frames[k].x()) + abs(at.y() - frames[k].y()))
    last = frames.pop(nearest)
    frames.append(at)
    self.moved += at.x() - last.x()
    wide, high = self.surface.width(), self.surface.height()
    if abs(local.x() - 0.5 * wide) > 0.25 * wide \
        or abs(local.y() - 0.5 * high) > 0.25 * high:
      self._recentre()

  def _recentre(self, ) -> None:
    """Puts the hidden pointer back in the middle, keeping two frames to
    read moves from: where it last was and where it is put."""
    surface = self.surface
    target = surface.mapToGlobal(QPoint(surface.width() // 2,
                                        surface.height() // 2))
    self.frames = self.frames[-1:] + [QPointF(target)]
    QCursor.setPos(target)
