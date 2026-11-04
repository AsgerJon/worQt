"""
RunRenderSweep subclasses 'WidgetTest' and exercises the painting stack by
constructing every concrete 'worQt.widgets' class and showing it in an
actual window with 'showLive'. The show drives the inherited 'paintEvent'
(and through it the registered paint operations and the box model) on
screen, so 'paintView' is populated and the widget is visibly rendered.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.widgets import (PaintedWidget,
  LabelWidget,
  TextWidget,
  PaintButton,
  ClickButton,
  PushButton)
from worQt.widgets import ScratchWidget
from worQt.utils.geom import Rect

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunRenderSweep(WidgetTest):
  """Shows every concrete widget in a live window and asserts it painted."""

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
    """Each widget shows visibly and captures its paint view on screen."""
    for widgetType in self.getWidgetTypes():
      name = widgetType.__name__
      widget = widgetType()
      widget.resize(240, 160)
      self.showLive(widget)
      self.assertTrue(widget.isVisible(), name)
      self.assertIsInstance(widget.paintView, Rect, name)

  def run_render_is_repeatable(self) -> None:
    """Repainting a shown widget stays stable (the paint ops reset)."""
    widget = ScratchWidget()
    widget.resize(200, 200)
    self.showLive(widget)
    for _ in range(3):
      widget.update()
      self.wait(20)
      self.assertIsInstance(widget.paintView, Rect)
