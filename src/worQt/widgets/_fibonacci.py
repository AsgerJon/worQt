"""
FibonacciWidget
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from math import pi, cos, sin

from PySide6.QtCore import QPoint, QLine, Qt, QRect, QSizeF, QPointF
from PySide6.QtGui import QPaintEvent, QPainter, QBrush, QColor, QPen
from PySide6.QtGui import QWheelEvent, QFont, QMouseEvent
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.utilities import maybe

from . import PaintedWidget
from ..utils.geom import Rect

if TYPE_CHECKING:  # pragma: no cover
  pass


class FibonacciWidget(PaintedWidget):
  """
  FibonacciWidget provides a widget that displays the Fibonacci sequence
  visually.
  """
  __fallback_scale__ = 5
  __fallback_base__ = [1, 2, 3, 5, 8]
  __fallback_angle__ = pi / 4
  __draw_scale__ = None
  __fib_base__ = None
  __rotation_angle__ = None
  scale = Field()
  fibBase = Field()
  angle = Field()

  @scale.GET
  def _getScale(self) -> int:
    return maybe(self.__draw_scale__, self.__fallback_scale__)

  @fibBase.GET
  def _getFibBase(self) -> list[int]:
    return maybe(self.__fib_base__, self.__fallback_base__)

  @angle.GET
  def _getAngle(self) -> float:
    return maybe(self.__rotation_angle__, self.__fallback_angle__)

  @scale.SET
  def _setScale(self, value: int) -> None:
    self.__draw_scale__ = value
    self.update()

  def paintMeLike(self, painter: QPainter, contentRect: Rect) -> None:
    viewRect = painter.viewport()
    x0 = viewRect.left() + viewRect.width() // 2
    y0 = viewRect.top() + viewRect.height() // 2

    black = QColor()
    black.setRed(0)
    black.setGreen(0)
    black.setBlue(0)

    gray = QColor()
    gray.setRed(200)
    gray.setGreen(200)
    gray.setBlue(200)

    orange = QColor()
    orange.setRed(255)
    orange.setGreen(165)
    orange.setBlue(0)

    pink = QColor()
    pink.setRed(255)
    pink.setGreen(0)
    pink.setBlue(144)

    pen = QPen()
    pen.setColor(orange)
    pen.setWidth(2)

    pointBrush = QBrush()
    pointBrush.setColor(pink)
    pointBrush.setStyle(Qt.BrushStyle.SolidPattern)

    pen.setStyle(Qt.PenStyle.SolidLine)
    painter.setPen(pen)

    painter.drawRect(viewRect)
    bottom = QPoint(x0, y0 + 4 * self.scale)
    top = QPoint(x0, y0 - 4 * self.scale)
    left = QPoint(x0 - 4 * self.scale, y0)
    right = QPoint(x0 + 4 * self.scale, y0)
    painter.drawLine(bottom, top)
    painter.drawLine(left, right)

    fibPen = QPen()
    fibPen.setColor(black)
    fibPen.setWidth(1)
    fibPen.setStyle(Qt.PenStyle.SolidLine)

    gridPen = QPen()
    gridPen.setColor(gray)
    gridPen.setWidth(1)
    gridPen.setStyle(Qt.PenStyle.DotLine)

    brush = QBrush()
    orange = QColor()
    orange.setRed(255)
    orange.setGreen(165)
    orange.setBlue(0)
    brush.setColor(orange)
    painter.setBrush(brush)

    font = QFont()
    font.setFamily('Montserrat')
    font.setPointSize(20)
    painter.setFont(font)

    pen.setWidth(1)
    painter.setPen(pen)

    fibs = ', '.join([str(f) for f in self.fibBase])
    angle = round(self.angle * 180 / pi)
    currentSpec = """Scale: %d, Base: [%s], angle: %d°"""
    currentText = currentSpec % (self.scale, fibs, angle)
    flag = Qt.AlignmentFlag.AlignCenter
    boundSize = painter.boundingRect(viewRect, flag, currentText).size()
    textRect = QRect(viewRect.topLeft(), boundSize)
    painter.drawText(textRect, flag, currentText)

    fibSeries = []
    while len(fibSeries) < 50:
      fibSeries.extend(self.fibBase)

    painter.setPen(gridPen)
    xg = int(x0)
    yg = int(y0)
    #  Generate view grid
    while xg < viewRect.right():
      startPoint = QPoint(xg, viewRect.top())
      endPoint = QPoint(xg, viewRect.bottom())
      line = QLine(startPoint, endPoint)
      painter.drawLine(line)
      xg += self.scale
    while yg < viewRect.bottom():
      startPoint = QPoint(viewRect.left(), yg)
      endPoint = QPoint(viewRect.right(), yg)
      line = QLine(startPoint, endPoint)
      painter.drawLine(line)
      yg += self.scale
    xg = int(x0)
    yg = int(y0)
    while xg > viewRect.left():
      startPoint = QPoint(xg, viewRect.top())
      endPoint = QPoint(xg, viewRect.bottom())
      line = QLine(startPoint, endPoint)
      painter.drawLine(line)
      xg -= self.scale
    while yg > viewRect.top():
      startPoint = QPoint(viewRect.left(), yg)
      endPoint = QPoint(viewRect.right(), yg)
      line = QLine(startPoint, endPoint)
      painter.drawLine(line)
      yg -= self.scale

    painter.setPen(fibPen)
    fibPoints = [QPoint(x0, y0)]

    x, y = x0, y0
    tail = True
    for j in range(50):
      for ii, f in enumerate(self.fibBase):
        i = ii + j * len(self.fibBase)
        p0 = QPoint.toPointF(fibPoints[-1])
        step = self._getVector(i)
        nextX = p0.x() + step.x() * f * self.scale
        nextY = p0.y() + step.y() * f * self.scale
        nextPointF = QPointF(nextX, nextY)
        for p in fibPoints:
          dist = self._distance(QPoint.toPointF(p), nextPointF)
          if dist < 1:
            break
        else:
          fibPoints.append(QPointF.toPoint(nextPointF))
          continue
        break
      else:
        continue
      break
    else:
      tail = False
    if tail:
      fibPoints.append(fibPoints[0])

    pointSizeF = QSizeF(self.scale * 0.5, self.scale * 0.5)
    pointSize = QSizeF.toSize(pointSizeF)
    origin = QPoint(0, 0)
    painter.setBrush(pointBrush)
    while fibPoints:
      startPoint = fibPoints.pop(0)
      pointRect = QRect(origin, pointSize)
      pointRect.moveCenter(startPoint)
      painter.drawEllipse(pointRect)
      if not fibPoints:
        break
      endPoint = fibPoints[0]
      line = QLine(startPoint, endPoint)
      painter.drawLine(line)

  def wheelEvent(self, event: QWheelEvent) -> None:
    delta = event.angleDelta().y() // 120
    if delta > 0:
      self.scale = max(int(1.2 * self.scale), self.scale + 1)
      if self.scale == 1:
        self.scale = 2
    elif delta < 0:
      self.scale = max(int(0.8 * self.scale), 1)
    super().wheelEvent(event)

  def mouseReleaseEvent(self, mouseEvent: QMouseEvent) -> None:
    button = mouseEvent.button()
    if button == Qt.MouseButton.LeftButton:
      self.fibBase.append(self.fibBase[-1] + self.fibBase[-2])
      self.update()
    elif button == Qt.MouseButton.RightButton:
      if len(self.fibBase) > 2:
        self.fibBase.pop()
        self.update()
    super().mouseReleaseEvent(mouseEvent)

  def __init__(self, *args, **kwargs) -> None:
    PaintedWidget.__init__(self, *args, **kwargs)
    QWidget.setMouseTracking(self, True)

  def _getVector(self, n: int) -> QPointF:
    t = n * self.angle
    while t > pi:
      t -= 2 * pi
    while t < -pi:
      t += 2 * pi
    x = cos(n * self.angle).real
    y = sin(n * self.angle).real
    return QPointF(x, y)

  @staticmethod
  def _distance(p0: QPointF, p1: QPointF) -> float:
    dx = p1.x() - p0.x()
    dy = p1.y() - p0.y()
    return (dx ** 2 + dy ** 2) ** 0.5
