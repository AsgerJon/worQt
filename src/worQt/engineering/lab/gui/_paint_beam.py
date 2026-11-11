"""
PaintBeam subclasses 'AbstractPaintOp' and paints a 'BeamView': the
beam on its rig, as the lab sees it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QPolygonF

from ....paint_ops import AbstractPaintOp
from ...gui import crackLevel, levelColor, paintCrackScale

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from ._beam_view import BeamView

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_FRAME_TOP = 18.0  # pixels: the top of the frame's crosshead
_CROSSHEAD = 14.0  # pixels: how deep the crosshead is
_BODY = (34.0, 50.0)  # pixels: an actuator's cylinder


class PaintBeam(AbstractPaintOp):
  """
  PaintBeam subclasses 'AbstractPaintOp' and paints a 'BeamView': the
  strong floor and the frame standing on it, the supports, the
  transducers under the beam with what each reads, the beam itself with
  its stirrups, the gaps left without them, its bars, cracks, each the
  way it runs, and crushed concrete, the actuators pushing down from
  the frame, each with its name, what drives it and its force, and the
  cracks' colour scale. The part selected, held or under the mouse is
  accented; the control's transducer and actuator are named in its
  colour.
  """

  #  Annotations
  widget: BeamView

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the lab, back to front."""
    widget = self.widget
    painter.setPen(self.emptyPen)
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    self._paintFrame(painter)
    self._paintSupports(painter)
    self._paintTransducers(painter)
    self._paintConcrete(painter)
    self._paintStirrups(painter)
    self._paintBars(painter)
    self._paintCracks(painter)
    self._paintActuators(painter)
    if widget.experiment is not None:
      box = widget.beamRect()
      scale = QRectF(
        box.right() - 280.0, widget.floor() + 4.0, 280.0,
        18.0
        )
      paintCrackScale(painter, scale, widget.font)
    return rect

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _accented(self, part: tuple[str, int]) -> bool:
    """Whether 'part' is drawn accented: selected, held or under the
    mouse."""
    widget = self.widget
    if part in (widget.selected, widget.held, widget.hovered):
      return True
    return False

  def _partColor(self, part: tuple[str, int]) -> QColor:
    """The colour a part of the rig is drawn in."""
    widget = self.widget
    if self._accented(part):
      return widget.accentColor.Q
    return widget.rigColor.Q

  @staticmethod
  def _faded(color: QColor, alpha: int) -> QColor:
    """'color' as see-through as 'alpha'."""
    faded = QColor(color)
    faded.setAlpha(alpha)
    return faded

  def _paintFrame(self, painter: WPainter) -> None:
    """The strong floor, and the frame standing on it: two columns and
    the crosshead the actuators hang from."""
    widget = self.widget
    box, floor = widget.beamRect(), widget.floor()
    painter.setPen(QPen(widget.rigColor.Q, 2.0))
    painter.drawLine(QLineF(0.0, floor, float(widget.width()), floor))
    painter.setPen(self.emptyPen)
    painter.setBrush(self._faded(widget.rigColor.Q, 70))
    left, right = box.left() - 26.0, box.right() + 14.0
    for x in (left, right):
      painter.drawRect(QRectF(x, _FRAME_TOP, 12.0, floor - _FRAME_TOP))
    painter.drawRect(
      QRectF(
        left, _FRAME_TOP, right + 12.0 - left,
        _CROSSHEAD
        )
      )
    painter.setBrush(self.emptyBrush)

  def _paintSupports(self, painter: WPainter) -> None:
    """Each support on its pedestal: a pin, a roller or a clamp."""
    widget = self.widget
    box, floor = widget.beamRect(), widget.floor()
    base = box.bottom() + 20.0
    for index, support in enumerate(widget.rig.supports):
      tip = widget.toScreen(support.at, 0.0)
      color = self._partColor(('support', index))
      painter.setPen(QPen(color, 2.0))
      painter.setBrush(self.emptyBrush)
      if support.kind == 'fixed':
        top = widget.toScreen(support.at, widget.beam.height)
        painter.setBrush(self._faded(color, 120))
        painter.drawRect(
          QRectF(
            tip.x() - 12.0, tip.y(), 24.0,
            base - tip.y()
            )
          )
        painter.drawRect(
          QRectF(
            tip.x() - 12.0, top.y() - 10.0, 24.0,
            10.0
            )
          )
        painter.setBrush(self.emptyBrush)
      else:
        lift = 8.0 if support.kind == 'roller' else 0.0
        painter.drawPolygon(
            QPolygonF(
                [
                  tip, QPointF(tip.x() - 11.0, base - lift),
                  QPointF(tip.x() + 11.0, base - lift),
                ]
            )
        )
        if lift:
          painter.drawEllipse(QPointF(tip.x(), base - 4.0), 4.0, 4.0)
      painter.drawLine(QLineF(tip.x() - 16.0, base, tip.x() + 16.0, base))
      painter.setPen(self.emptyPen)
      painter.setBrush(self._faded(color, 60))
      painter.drawRect(QRectF(tip.x() - 14.0, base, 28.0, floor - base))
      painter.setBrush(self.emptyBrush)

  def _paintTransducers(self, painter: WPainter) -> None:
    """Each transducer on its stand, its plunger touching the beam's
    underside, its name and what it reads beside it, up positive."""
    widget = self.widget
    box, floor = widget.beamRect(), widget.floor()
    experiment = widget.experiment
    readings = None
    if experiment is not None and experiment.readings:
      readings = experiment.latest.transducers
    reads = widget.rig.control.transducer
    painter.setFont(widget.font)
    for index, x in enumerate(widget.rig.transducers):
      part = ('transducer', index)
      touch = widget.toScreen(x, 0.0)
      body = QRectF(touch.x() - 5.0, box.bottom() + 44.0, 10.0, 34.0)
      color = self._partColor(part)
      painter.setPen(QPen(color, 1.5))
      painter.drawLine(
        QLineF(
          touch.x(), touch.y(), touch.x(),
          body.top()
          )
        )
      painter.setBrush(self._faded(color, 90))
      painter.drawRect(body)
      painter.setBrush(self.emptyBrush)
      painter.drawLine(QLineF(touch.x(), body.bottom(), touch.x(), floor))
      text = widget.partName(part)
      if readings is not None and index < len(readings):
        text += '  %.2f mm' % readings[index]
      ink = widget.controlColor.Q if index == reads else widget.textColor.Q
      painter.setPen(color if self._accented(part) else ink)
      label = QRectF(touch.x() + 8.0, body.top(), 130.0, 16.0)
      painter.drawText(label, _LEFT, text)
      if index == reads:
        under = QRectF(touch.x() + 8.0, body.top() + 16.0, 130.0, 16.0)
        painter.drawText(under, _LEFT, 'control')

  def _edge(self, y: float) -> list[QPointF]:
    """The beam's edge 'y' up from its underside, along its length, as
    it has moved."""
    widget = self.widget
    experiment = widget.experiment
    if experiment is None:
      places = [0.0, widget.beam.length]
    else:
      places = [*experiment.nodes]
    return [widget.toScreen(x, y) for x in places]

  def _paintConcrete(self, painter: WPainter) -> None:
    """The beam's concrete, as it has bent."""
    widget = self.widget
    top = self._edge(widget.beam.height)
    bottom = self._edge(0.0)
    outline = QPolygonF([*top, *reversed(bottom)])
    painter.setPen(QPen(widget.edgeColor.Q, 1.0))
    painter.setBrush(widget.concreteColor.fillBrush)
    painter.drawPolygon(outline)
    painter.setBrush(self.emptyBrush)

  def _paintBars(self, painter: WPainter) -> None:
    """The bars inside the beam, dashed, at their depth."""
    widget = self.widget
    beam = widget.beam
    pen = QPen(widget.steelColor.Q, 1.6)
    pen.setStyle(Qt.PenStyle.DashLine)
    painter.setPen(pen)
    for layer, y in (
        (beam.bottom, beam.bottom.depth),
        (beam.top, beam.height - beam.top.depth)
    ):
      if layer.count:
        painter.drawPolyline(QPolygonF(self._edge(y)))

  def _paintCracks(self, painter: WPainter) -> None:
    """The cracks open on the face, each across its cell the way it
    runs, coloured by how wide it is; and the concrete crushed."""
    widget = self.widget
    experiment = widget.experiment
    if experiment is None:
      return
    xs, ys = experiment.mesh.xs, experiment.mesh.ys
    reach = 0.4 * min(min(b - a for a, b in zip(xs, xs[1:])),
                      min(b - a for a, b in zip(ys, ys[1:])))
    for x, y, run, width in widget.cracks():
      along, up = reach * math.cos(run), reach * math.sin(run)
      painter.setPen(QPen(levelColor(crackLevel(width)), 1.6))
      painter.drawLine(QLineF(widget.toScreen(x - along, y - up),
                              widget.toScreen(x + along, y + up)))
    painter.setPen(self.emptyPen)
    painter.setBrush(self._faded(widget.crushedColor.Q, 150))
    for left, right, low, high in widget.crushed():
      first = widget.toScreen(left, high)
      last = widget.toScreen(right, low)
      painter.drawRect(QRectF(first, last).normalized())
    painter.setBrush(self.emptyBrush)

  def _paintStirrups(self, painter: WPainter) -> None:
    """The gaps in the stirrups, shaded, and each stirrup, upright
    between the rows of bars, accented once it yields."""
    widget = self.widget
    beam = widget.beam
    low = beam.bottom.depth if beam.bottom.count else 30.0
    high = beam.height - (beam.top.depth if beam.top.count else 30.0)
    painter.setPen(self.emptyPen)
    for index, (start, end) in enumerate(beam.stirrups.gaps):
      color = self._partColor(('gap', index))
      painter.setBrush(self._faded(color, 60))
      first = widget.toScreen(start, beam.height)
      last = widget.toScreen(end, 0.0)
      painter.drawRect(QRectF(first, last).normalized())
    painter.setBrush(self.emptyBrush)
    for x, share in widget.stirrups():
      yielded = share >= 1.0
      color = widget.accentColor if yielded else widget.steelColor
      painter.setPen(QPen(color.Q, 1.0))
      painter.drawLine(QLineF(widget.toScreen(x, low),
                              widget.toScreen(x, high)))

  def _paintActuators(self, painter: WPainter) -> None:
    """Each actuator hanging from the crosshead, its rod down to its
    plate on the beam, its name, what drives it and its force."""
    widget = self.widget
    rig = widget.rig
    experiment = widget.experiment
    forces = None
    if experiment is not None and experiment.readings:
      forces = experiment.latest.forces
    width, length = _BODY
    painter.setFont(widget.font)
    for index, actuator in enumerate(rig.actuators):
      part = ('actuator', index)
      color = self._partColor(part)
      top = widget.toScreen(actuator.at, widget.beam.height)
      plate = QRectF(top.x() - 14.0, top.y() - 7.0, 28.0, 7.0)
      body = QRectF(
        top.x() - width / 2, _FRAME_TOP + _CROSSHEAD, width,
        length
        )
      painter.setPen(QPen(color, 5.0))
      painter.drawLine(
        QLineF(
          top.x(), plate.top(), top.x(),
          body.bottom()
          )
        )
      painter.setPen(QPen(color, 1.5))
      painter.setBrush(self._faded(color, 110))
      painter.drawRect(body)
      painter.drawRect(plate)
      painter.setBrush(self.emptyBrush)
      lines = [widget.partName(part), self._role(index)]
      if forces is not None and index < len(forces):
        lines.append('%.1f kN' % forces[index])
      driven = index == rig.driven
      ink = widget.controlColor.Q if driven else widget.textColor.Q
      painter.setPen(color if self._accented(part) else ink)
      for row, line in enumerate(lines):
        where = QRectF(
          body.right() + 4.0, body.top() + row * 15.0,
          110.0, 15.0
          )
        painter.drawText(where, _LEFT, line)

  def _role(self, index: int) -> str:
    """What drives the actuator of 'index': the control's transducer,
    or the share of the force of the one it follows."""
    widget = self.widget
    rig = widget.rig
    if index == rig.driven:
      reads = ('transducer', rig.control.transducer)
      return 'driven by %s' % widget.partName(reads)
    actuator = rig.actuators[index]
    follows = widget.partName(('actuator', actuator.follows))
    return '%.2f × %s' % (actuator.share, follows)
