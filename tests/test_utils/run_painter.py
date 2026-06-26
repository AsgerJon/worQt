"""
RunPainter subclasses 'UtilsAppTest' and tests the painting helpers used by
every 'PaintedWidget.paintEvent': 'WPainterPath' (its geometry-aware
'addRect'/'addRoundedRect') and 'WPainter' (the paint device, 'setFont'
write-through, and the box-model 'fillBetween'). A 'QPainter' needs a paint
device, so the tests paint onto a 'QPixmap' under a 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import QRect, QRectF
from PySide6.QtGui import QPixmap, QFont, QPaintDevice, QPainterPath

from worktoy.waitaminute import TypeException

from worQt.utils import WPainter, WPainterPath, WFont, Color
from worQt.utils.geom import Rect, RoundedRect

from . import UtilsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunPainter(UtilsAppTest):
  """Tests for 'WPainter' and 'WPainterPath'."""

  def run_path_add_rect(self) -> None:
    """'addRect' accepts a worQt 'Rect' and grows the path."""
    path = WPainterPath()
    path.addRect(Rect(0, 0, 10, 10))
    self.assertGreater(path.elementCount(), 0)

  def run_path_add_rect_rejects_bad(self) -> None:
    """'addRect' refuses a non-rect argument."""
    path = WPainterPath()
    with self.assertRaises(TypeException):
      path.addRect(123)

  def run_path_rounded_variants(self) -> None:
    """'addRoundedRect' accepts 'Rect', 'RoundedRect', 'QRect' and
    'QRectF'."""
    for rect in (Rect(0, 0, 10, 10),
                 RoundedRect(Rect(0, 0, 10, 10), 4, 4),
                 QRect(0, 0, 10, 10),
                 QRectF(0, 0, 10, 10)):
      path = WPainterPath()
      path.addRoundedRect(rect, 2, 2)
      self.assertGreater(path.elementCount(), 0)

  def run_path_rounded_rejects_bad(self) -> None:
    """'addRoundedRect' refuses a non-rect argument."""
    with self.assertRaises(TypeException):
      WPainterPath().addRoundedRect('bad')

  def run_path_add_rect_with_args(self) -> None:
    """'addRect' forwards the four-number form to the base path."""
    path = WPainterPath()
    path.addRect(0, 0, 10, 10)
    self.assertGreater(path.elementCount(), 0)

  def run_paint_device_inactive_raises(self) -> None:
    """Reading 'paintDevice' off an inactive painter raises."""
    with self.assertRaises(TypeException):
      _ = WPainter().paintDevice

  def run_paint_device(self) -> None:
    """The 'paintDevice' field returns the device being painted on."""
    pixmap = QPixmap(40, 40)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      self.assertIsInstance(painter.paintDevice, QPaintDevice)
    finally:
      painter.end()

  def run_set_font(self) -> None:
    """'setFont' accepts both 'WFont' and 'QFont' and refuses others."""
    pixmap = QPixmap(40, 40)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      painter.setFont(WFont())
      painter.setFont(QFont())
      with self.assertRaises(TypeException):
        painter.setFont(123)
    finally:
      painter.end()

  def run_fill_between(self) -> None:
    """'fillBetween' paints the ring between two nested rects."""
    pixmap = QPixmap(100, 100)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      painter.fillBetween(Rect(0, 0, 100, 100),
                          Rect(10, 10, 90, 90),
                          Color(0, 0, 0))
      painter.fillBetween(RoundedRect(Rect(0, 0, 100, 100), 8, 8),
                          RoundedRect(Rect(10, 10, 90, 90), 4, 4),
                          Color(255, 0, 0))
    finally:
      painter.end()

  def run_fill_between_swaps_args(self) -> None:
    """Passing the inner rect first is corrected by a swap, not an error."""
    pixmap = QPixmap(100, 100)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      painter.fillBetween(Rect(10, 10, 90, 90),
                          Rect(0, 0, 100, 100),
                          Color(0, 0, 0))
    finally:
      painter.end()

  def run_fill_between_rejects_intersecting(self) -> None:
    """Overlapping, non-nested rects are refused."""
    pixmap = QPixmap(100, 100)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      with self.assertRaises(ValueError):
        painter.fillBetween(Rect(0, 0, 50, 50),
                            Rect(25, 25, 75, 75),
                            Color(0, 0, 0))
    finally:
      painter.end()

  def run_fill_path(self) -> None:
    """'fillPath' fills a path with a colour."""
    pixmap = QPixmap(40, 40)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      path = QPainterPath()
      path.addRect(QRect(0, 0, 10, 10))
      painter.fillPath(path, Color(1, 2, 3).Q)
    finally:
      painter.end()

  def run_print_label_rejects_bad_rect(self) -> None:
    """'printLabel' refuses a non-'Rect' target."""
    pixmap = QPixmap(40, 40)
    painter = WPainter()
    painter.begin(pixmap)
    try:
      with self.assertRaises(TypeException):
        painter.printLabel('x', 'not a rect')
    finally:
      painter.end()
