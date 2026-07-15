"""
RunLabelWidget subclasses 'WidgetTest' and exercises 'LabelWidget': its
overloaded constructors, the text/min-size/corner-radius fields (their lazy
getters, recursion and type guards, and setters), and the required-size
computation.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QWidget

from worktoy.waitaminute import TypeException

from worQt.widgets import LabelWidget
from worQt.utils.geom import Size

from worQt.qtest import WidgetTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunLabelWidget(WidgetTest):
  """Tests for 'LabelWidget'."""

  def run_constructors(self) -> None:
    """The overloaded constructors set parent, text and corner radii."""
    parent = QWidget()
    self.assertEqual(LabelWidget(parent).text, 'LABEL')
    self.assertEqual(LabelWidget(parent, 'hi').text, 'hi')
    labelled = LabelWidget(parent, 'hi', 4, 6)
    self.assertEqual(labelled.text, 'hi')
    self.assertEqual(labelled.cornerXRadius, 4)
    self.assertEqual(labelled.cornerYRadius, 6)

  def run_copy_constructor(self) -> None:
    """A 'LabelWidget' rebuilds from another via 'THIS'."""
    parent = QWidget()
    copy = LabelWidget(LabelWidget(parent, 'hi', 4, 6))
    self.assertEqual(copy.text, 'hi')
    self.assertEqual(copy.cornerXRadius, 4)

  def run_default_getters(self) -> None:
    """The lazy fields build their fallback values on first read."""
    widget = LabelWidget()
    self.assertEqual(widget.text, 'LABEL')
    self.assertEqual(widget.cornerXRadius, 0)
    self.assertEqual(widget.cornerYRadius, 0)
    self.assertIsInstance(widget.minWidth, int)
    self.assertIsInstance(widget.minHeight, int)
    self.assertIsInstance(widget.minSize, Size)

  def run_recursion_guards(self) -> None:
    """Each lazy getter guards against a failed build."""
    getters = ('_getText', '_getCornerXRadius', '_getCornerYRadius',
               '_getMinWidth', '_getMinHeight')
    for name in getters:
      widget = LabelWidget()
      with self.assertRaises(RecursionError):
        getattr(widget, name)(_recursion=True)

  def run_type_guards(self) -> None:
    """Each getter rejects a corrupt backing slot."""
    specs = (('__current_text__', '_getText'),
             ('__x_radius__', '_getCornerXRadius'),
             ('__y_radius__', '_getCornerYRadius'),
             ('__min_width__', '_getMinWidth'),
             ('__min_height__', '_getMinHeight'))
    for slot, getter in specs:
      widget = LabelWidget()
      setattr(widget, slot, object())
      with self.assertRaises(TypeException):
        getattr(widget, getter)()

  def run_text_setter(self) -> None:
    """Text is settable; re-setting the same value is skipped."""
    widget = LabelWidget()
    widget.text = 'hello'
    widget.text = 'hello'  # same -> SkipSet
    self.assertEqual(widget.text, 'hello')

  def run_text_setter_rejects_non_str(self) -> None:
    """A non-string text is refused."""
    widget = LabelWidget()
    with self.assertRaises(TypeException):
      widget.text = 123

  def run_corner_radius_setters(self) -> None:
    """The corner radii are settable and reject non-integers."""
    widget = LabelWidget()
    widget.cornerXRadius = 8
    widget.cornerYRadius = 9
    self.assertEqual(widget.cornerXRadius, 8)
    self.assertEqual(widget.cornerYRadius, 9)
    with self.assertRaises(TypeException):
      widget.cornerXRadius = 'x'
    with self.assertRaises(TypeException):
      widget.cornerYRadius = 'y'

  def run_required_size(self) -> None:
    """The required size bounds the label text."""
    widget = LabelWidget()
    widget.text = 'worQt'
    self.assertIsInstance(widget.reqSize, Size)
    self.assertGreaterEqual(widget.reqSize.width, widget.minWidth)
