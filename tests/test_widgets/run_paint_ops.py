"""
RunPaintOps covers the 'worQt.paint_ops' layer: the 'AbstractPaintOp'
accessors and base 'prepare'/'reset', the 'PaintLabel' font save/restore
and its 'paint'/'TEXT' guards, the integration through a rendered
'LabelWidget' (driving 'PaintBoxModel' and 'PaintLabel' under a real
paint device), and the 'PaintedWidget.paintEvent' exception routing.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap, QPaintEvent, QFont, QPainter
from PySide6.QtCore import QRect
from worktoy.waitaminute import TypeException, MissingVariable, VariableNotNone

from worQt.paint_ops import AbstractPaintOp, PaintBoxModel, PaintLabel
from worQt.waitaminute.events import EventException
from worQt.widgets import LabelWidget, PaintedWidget
from worQt.utils.geom import Rect

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _BareOp(AbstractPaintOp):
  """A paint op that keeps the base 'prepare'/'reset'."""

  def paint(self, painter: Any, rect: Rect, event: Any) -> Rect:
    return rect


class _BoomOp(AbstractPaintOp):
  """A paint op whose 'paint' always raises."""

  def paint(self, painter: Any, rect: Rect, event: Any) -> Rect:
    raise RuntimeError('boom')


class _BoomWidget(PaintedWidget):
  """A widget whose paint op raises, to drive the paintEvent guard."""
  boomOp = _BoomOp()


class _BadReturnOp(AbstractPaintOp):
  """A paint op whose 'paint' returns a non-'Rect' value."""

  def paint(self, painter: Any, rect: Rect, event: Any) -> Any:
    return 'not a rect'


class _BadReturnWidget(PaintedWidget):
  """A widget whose paint op returns a non-'Rect', to drive the
  paint-view type guard in 'paintEvent'."""
  badOp = _BadReturnOp()


class RunPaintOps(WidgetTest):
  """Tests for the paint-operation layer."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT PAINT OP  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_accessors_default(self) -> None:
    """An unbound op reports empty widget/type/name and non-root."""
    op = PaintBoxModel()
    self.assertIsNone(op.widget)
    self.assertIsNone(op.widgetType)
    self.assertIsNone(op.opName)
    self.assertFalse(op.isRoot)

  def run_device_guards(self) -> None:
    """'device'/'deviceType' raise when unset or wrongly typed."""
    op = PaintBoxModel()
    with self.assertRaises(MissingVariable):
      _ = op.device
    op.__paint_device__ = 'bad'
    with self.assertRaises(TypeException):
      _ = op.device
    op2 = PaintBoxModel()
    with self.assertRaises(MissingVariable):
      _ = op2.deviceType
    op2.__device_type__ = 'bad'
    with self.assertRaises(TypeException):
      _ = op2.deviceType

  def run_device_type_valid(self) -> None:
    """A valid 'deviceType' slot reads back unchanged."""
    op = PaintBoxModel()
    op.__device_type__ = int
    self.assertIs(op.deviceType, int)

  def run_base_prepare_reset(self) -> None:
    """The base 'prepare'/'reset' record and clear the paint device."""
    pixmap = QPixmap(10, 10)
    painter = QPainter()
    painter.begin(pixmap)
    op = _BareOp()
    op.prepare(painter)
    op.reset(painter)
    painter.end()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PAINT LABEL  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_label_reset_branches(self) -> None:
    """'reset' restores a saved 'QFont', installs a fresh one when none was
    saved, and rejects a wrongly-typed saved font."""
    pixmap = QPixmap(10, 10)
    painter = QPainter()
    painter.begin(pixmap)
    op = PaintLabel()
    op.__old_font__ = None
    op.reset(painter)
    op.__old_font__ = QFont()
    op.reset(painter)
    op.__old_font__ = 'bad'
    with self.assertRaises(TypeException):
      op.reset(painter)
    painter.end()

  def run_label_paint_guards(self) -> None:
    """'paint' validates painter, rect and event types."""
    pixmap = QPixmap(10, 10)
    painter = QPainter()
    painter.begin(pixmap)
    op = PaintLabel()
    event = QPaintEvent(QRect(0, 0, 1, 1))
    with self.assertRaises(TypeException):
      op.paint('not a painter', Rect(), event)
    with self.assertRaises(TypeException):
      op.paint(painter, 'not a rect', event)
    with self.assertRaises(TypeException):
      op.paint(painter, Rect(), 'not an event')
    painter.end()

  def run_label_text_decorator(self) -> None:
    """'TEXT' records one getter and rejects a second or a non-callable."""
    op = PaintLabel()

    def getter(widget: Any) -> str:
      return 'x'

    op.TEXT(getter)
    with self.assertRaises(VariableNotNone):
      op.TEXT(getter)
    with self.assertRaises(TypeException):
      PaintLabel().TEXT(123)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  INTEGRATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_label_widget_shows(self) -> None:
    """Showing a 'LabelWidget' drives its box-model and label ops under a
    real paint device on screen."""
    widget = LabelWidget()
    widget.resize(120, 60)
    self.showLive(widget)
    self.assertIsInstance(widget.paintView, Rect)

  def run_paint_event_routes_exception(self) -> None:
    """A paint op that raises surfaces as an 'EventException'."""
    widget = _BoomWidget()
    widget.resize(40, 40)
    with self.assertRaises(EventException):
      widget.render(QPixmap(widget.size()))

  def run_paint_event_rejects_non_rect(self) -> None:
    """A paint op returning a non-'Rect' view is caught and surfaces as an
    'EventException' (from the paint-view type guard)."""
    widget = _BadReturnWidget()
    widget.resize(40, 40)
    with self.assertRaises(EventException):
      widget.render(QPixmap(widget.size()))
