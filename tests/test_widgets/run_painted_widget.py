"""
RunPaintedWidget subclasses 'WidgetTest' and tests the box-model machinery
on 'PaintedWidget' and its 'TestWidget' subclass: the default box-model
fields, paint-operation registration, the paint view captured during a
render, and a live, on-screen show.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap, QTextOption
from PySide6.QtTest import QTest

from worktoy.waitaminute import TypeException

from worQt.widgets import PaintedWidget, ScratchWidget
from worQt.paint_ops import PaintBoxModel
from worQt.utils.qee_num import Alignum, HAlignum, VAlignum, SizingMode
from worQt.utils.geom import Rect, Size, InSets, Color

from . import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunPaintedWidget(WidgetTest):
  """Box-model defaults, paint-op registration, and a live show."""

  def run_default_alignment(self) -> None:
    """A fresh painted widget centres its content by default."""
    widget = PaintedWidget()
    self.assertIs(widget.align, Alignum.CENTER)
    self.assertIs(widget.align.horizontal, Alignum.CENTER.horizontal)
    self.assertIs(widget.align.vertical, Alignum.CENTER.vertical)

  def run_default_sizing_modes(self) -> None:
    """Both sizing modes default to intrinsic."""
    widget = PaintedWidget()
    self.assertIs(widget.hMode, SizingMode.INTRINSIC)
    self.assertIs(widget.vMode, SizingMode.INTRINSIC)

  def run_default_box_dims(self) -> None:
    """The margin, border and padding insets take their fallback widths."""
    widget = PaintedWidget()
    self.assertEqual(widget.marginsDims.left, 2)
    self.assertEqual(widget.marginsDims.bottom, 2)
    self.assertEqual(widget.bordersDims.left, 1)
    self.assertEqual(widget.bordersDims.bottom, 1)
    self.assertEqual(widget.paddingsDims.left, 2)
    self.assertEqual(widget.paddingsDims.bottom, 2)

  def run_default_required_size(self) -> None:
    """The base required size is the 32x32 fallback content size."""
    widget = PaintedWidget()
    self.assertIsInstance(widget.reqSize, Size)
    self.assertEqual(widget.reqSize.width, 32)
    self.assertEqual(widget.reqSize.height, 32)

  def run_subclass_required_size(self) -> None:
    """'TestWidget' overrides the required size to 200x200."""
    widget = ScratchWidget()
    self.assertEqual(widget.reqSize.width, 200)
    self.assertEqual(widget.reqSize.height, 200)

  def run_paint_op_registration(self) -> None:
    """'TestWidget' declares exactly one box-model paint operation."""
    widget = ScratchWidget()
    ops = [*widget.paintOps]
    self.assertEqual(len(ops), 1)
    self.assertIsInstance(ops[0], PaintBoxModel)
    self.assertIs(ops[0].widget, widget)

  def run_base_has_no_paint_ops(self) -> None:
    """A bare painted widget registers no paint operations."""
    widget = PaintedWidget()
    self.assertEqual([*widget.paintOps], [])

  def run_paint_view_after_render(self) -> None:
    """Rendering captures the painter viewport as the paint view 'Rect'."""
    widget = ScratchWidget()
    widget.resize(200, 200)
    pixmap = QPixmap(widget.size())
    widget.render(pixmap)
    self.assertIsInstance(widget.paintView, Rect)

  def run_alignment_is_settable(self) -> None:
    """The alignment field accepts a new 'Alignum', and re-setting it to a
    different value proceeds (the pre-set guard sees a real change)."""
    widget = PaintedWidget()
    widget.align = Alignum.TOP_LEFT
    self.assertIs(widget.align, Alignum.TOP_LEFT)
    widget.align = Alignum.BOTTOM_RIGHT  # already set, differs -> no SkipSet
    self.assertIs(widget.align, Alignum.BOTTOM_RIGHT)

  def run_box_getters_all(self) -> None:
    """Reading every box-model field builds and returns its value."""
    widget = PaintedWidget()
    self.assertIsInstance(widget.marginsDims, InSets)
    self.assertIsInstance(widget.bordersDims, InSets)
    self.assertIsInstance(widget.paddingsDims, InSets)
    self.assertIsInstance(widget.marginsColor, Color)
    self.assertIsInstance(widget.bordersColor, Color)
    self.assertIsInstance(widget.paddingsColor, Color)
    self.assertIsInstance(widget.align, Alignum)
    self.assertIsInstance(widget.hAlign, HAlignum)
    self.assertIsInstance(widget.vAlign, VAlignum)
    self.assertIsInstance(widget.hMode, SizingMode)
    self.assertIsInstance(widget.vMode, SizingMode)
    self.assertIsInstance(widget.wrapMode, QTextOption.WrapMode)
    self.assertIsInstance(widget.textAlign, Alignum)
    self.assertIsInstance(widget.textOption, QTextOption)

  def run_box_recursion_guards(self) -> None:
    """Each lazy getter guards against a failed build."""
    getters = ('_getAlignment', '_getMarginsDims', '_getBordersDims',
               '_getPaddingsDims', '_getMarginsColor', '_getBordersColor',
               '_getPaddingsColor', '_getWrapMode', '_getTextAlignum',
               '_getHorizontalMode', '_getVerticalMode')
    for name in getters:
      widget = PaintedWidget()
      with self.assertRaises(RecursionError):
        getattr(widget, name)(_recursion=True)

  def run_box_type_guards(self) -> None:
    """Each getter rejects a corrupt backing slot."""
    specs = (('__alignment_flag__', '_getAlignment'),
             ('__margins_dims__', '_getMarginsDims'),
             ('__borders_dims__', '_getBordersDims'),
             ('__paddings_dims__', '_getPaddingsDims'),
             ('__margins_color__', '_getMarginsColor'),
             ('__borders_color__', '_getBordersColor'),
             ('__paddings_color__', '_getPaddingsColor'),
             ('__wrap_mode__', '_getWrapMode'),
             ('__text_align__', '_getTextAlignum'),
             ('__horizontal_mode__', '_getHorizontalMode'),
             ('__vertical_mode__', '_getVerticalMode'))
    for slot, getter in specs:
      widget = PaintedWidget()
      setattr(widget, slot, 'bad')
      with self.assertRaises(TypeException):
        getattr(widget, getter)()

  def run_box_color_setters(self) -> None:
    """Layer colours are settable, and re-setting the same is skipped."""
    widget = PaintedWidget()
    margin = Color(1, 2, 3)
    widget.marginsColor = margin
    widget.marginsColor = margin  # same instance -> SkipSet
    self.assertIs(widget.marginsColor, margin)
    borders = Color(4, 5, 6)
    widget.bordersColor = borders
    widget.bordersColor = borders  # same instance -> SkipSet
    paddings = Color(7, 8, 9)
    widget.paddingsColor = paddings
    widget.paddingsColor = paddings  # same instance -> SkipSet
    self.assertEqual((*widget.bordersColor,), (4, 5, 6, 255))

  def run_sizing_mode_setters(self) -> None:
    """Sizing modes are settable, and re-setting the same is skipped."""
    widget = PaintedWidget()
    widget.hMode = SizingMode.EXTRINSIC
    widget.hMode = SizingMode.EXTRINSIC  # same -> SkipSet
    self.assertIs(widget.hMode, SizingMode.EXTRINSIC)
    widget.vMode = SizingMode.EXTRINSIC
    widget.vMode = SizingMode.EXTRINSIC  # same -> SkipSet
    self.assertIs(widget.vMode, SizingMode.EXTRINSIC)
    widget.hMode = SizingMode.INTRINSIC  # already set, differs -> no SkipSet
    self.assertIs(widget.hMode, SizingMode.INTRINSIC)

  def run_component_alignment_setters_unimplemented(self) -> None:
    """The horizontal/vertical alignment setters are not implemented."""
    widget = PaintedWidget()
    with self.assertRaises(NotImplementedError):
      widget.hAlign = HAlignum.LEFT
    with self.assertRaises(NotImplementedError):
      widget.vAlign = VAlignum.TOP

  def run_extrinsic_render(self) -> None:
    """Rendering under the extrinsic sizing mode shrinks to the view."""
    widget = ScratchWidget()
    widget.hMode = SizingMode.EXTRINSIC
    widget.vMode = SizingMode.EXTRINSIC
    widget.resize(200, 200)
    pixmap = QPixmap(widget.size())
    widget.render(pixmap)
    self.assertIsInstance(widget.paintView, Rect)

  def run_show_visible(self) -> None:
    """A shown widget becomes visible while the event loop pumps."""
    widget = ScratchWidget()
    widget.setWindowTitle('worQt painted widget')
    widget.resize(200, 200)
    widget.show()
    QTest.qWait(200)
    self.assertTrue(widget.isVisible())
    widget.close()
