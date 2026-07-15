"""
RunWidgetInternals covers the widget accessors and setters not reached by
the render/event tests: 'PaintedWidget' alignment/mode/colour setters and
their guards, the paint-op cache helpers, 'TextWidget.initUI' and its
derived sizes, 'ScratchWidget', the 'PaintButton' default positions/state and
the 'LabelWidget' copy constructor and text notifier.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException

from worQt.widgets import (PaintedWidget, LabelWidget, TextWidget,
                          PaintButton, ScratchWidget)
from worQt.utils.geom import Color, Size
from worQt.utils.qee_num import SizingMode, HAlignum, VAlignum

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunWidgetInternals(WidgetTest):
  """Tests for the widget accessor/setter internals."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PAINTED WIDGET  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_axis_align_setters_unsupported(self) -> None:
    """The per-axis alignment setters are not supported directly."""
    widget = PaintedWidget()
    with self.assertRaises(NotImplementedError):
      widget.hAlign = HAlignum.LEFT
    with self.assertRaises(NotImplementedError):
      widget.vAlign = VAlignum.TOP

  def run_setter_type_guards(self) -> None:
    """The mode/colour/align setters reject wrong types."""
    widget = PaintedWidget()
    for attr in ('hMode', 'vMode', 'marginsColor', 'bordersColor',
                 'paddingsColor', 'align'):
      with self.assertRaises(TypeException):
        setattr(widget, attr, 1)

  def run_mode_and_colour_set(self) -> None:
    """Valid mode/colour assignments take effect and skip no-op re-sets."""
    widget = PaintedWidget()
    widget.hMode = SizingMode.EXTRINSIC
    widget.vMode = SizingMode.EXTRINSIC
    self.assertIs(widget.hMode, SizingMode.EXTRINSIC)
    widget.marginsColor = Color(1, 2, 3)
    widget.marginsColor = widget.marginsColor  # same value -> SkipSet
    widget.bordersColor = Color(4, 5, 6)
    widget.paddingsColor = Color(7, 8, 9)
    widget.align = widget.align  # same value -> SkipSet

  def run_paint_op_cache_helpers(self) -> None:
    """The paint-op instantiate/clear helpers run."""
    widget = PaintedWidget()
    widget._instantiatePaintOpObjects()
    widget._clearPaintOpObjects()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TEXT WIDGET  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_text_widget_init_ui(self) -> None:
    """'initUI' sets the box model and the derived text sizes resolve."""
    widget = TextWidget()
    widget.resize(200, 200)
    self.showLive(widget)
    widget.initUI()
    self.assertIsInstance(widget.text, str)
    self.assertGreaterEqual(widget.reqHeight, 0)
    self.assertIsInstance(widget._getRequiredSize(), Size)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  TEST WIDGET  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_scratch_widget(self) -> None:
    """'ScratchWidget' constructs and reports its fixed required size."""
    size = ScratchWidget()._getRequiredSize()
    self.assertEqual((size.width, size.height), (200, 200))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PAINT BUTTON  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_paint_button_default_positions(self) -> None:
    """With no event point, the cursor positions are the sentinel and the
    state is the null state."""
    button = PaintButton()
    for point in (button.cursorPosition, button.assignedRectPosition,
                  button.contentRectPosition):
      self.assertEqual((point.x, point.y), (-1, -1))
    self.assertFalse(button.button)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LABEL WIDGET  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def run_label_copy_and_notify(self) -> None:
    """The 'LabelWidget' copy constructor copies the visible state, and
    setting the text fires the repaint notifier."""
    original = LabelWidget()
    original.text = 'hello'
    original.cornerXRadius = 7
    copy = LabelWidget(original)
    self.assertEqual(copy.text, 'hello')
    self.assertEqual(copy.cornerXRadius, 7)
    copy.text = 'changed'  # onSet -> update
    self.assertEqual(copy.text, 'changed')
    self.assertEqual(
        (copy.minSize.width, copy.minSize.height),
        (copy.minWidth, copy.minHeight))
