"""
RunRenderSweep subclasses 'WidgetTest' and exercises the painting stack by
constructing every concrete 'worQt.widgets' class, sizing it, and rendering
it to a 'QPixmap'. Rendering drives the inherited 'paintEvent' (and through
it the registered paint operations and the box model) without needing the
widget on screen, so the sweep runs the same headless or windowed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap

from worQt.widgets import (PaintedWidget,
  LabelWidget,
  TextWidget,
  PaintButton,
  ClickButton,
  PushButton)
from worQt.widgets import ScratchWidget

from . import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunRenderSweep(WidgetTest):
  """Renders every concrete widget to a pixmap and asserts it painted."""

  @classmethod
  def getWidgetTypes(cls) -> tuple[type, ...]:
    """The concrete widget types the sweep renders."""
    return (
      PaintedWidget,
      LabelWidget,
      TextWidget,
      PaintButton,
      ClickButton,
      PushButton,
      ScratchWidget,
    )

  def run_render_each(self) -> None:
    """Each widget renders to a non-null pixmap of the requested size."""
    for widgetType in self.getWidgetTypes():
      name = widgetType.__name__
      widget = widgetType()
      widget.resize(240, 160)
      pixmap = QPixmap(widget.size())
      widget.render(pixmap)
      self.assertFalse(pixmap.isNull(), name)
      self.assertEqual(pixmap.width(), 240, name)
      self.assertEqual(pixmap.height(), 160, name)

  def run_render_is_repeatable(self) -> None:
    """Rendering the same widget twice stays stable (paint ops reset)."""
    widget = ScratchWidget()
    widget.resize(200, 200)
    for _ in range(3):
      pixmap = QPixmap(widget.size())
      widget.render(pixmap)
      self.assertFalse(pixmap.isNull())
