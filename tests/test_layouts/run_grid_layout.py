"""
RunGridLayout subclasses 'LayoutAppTest' and tests the
'worQt.layouts.GridLayout' manager against a live 'QApplication': the
widget mapping, item access by 'LayoutIndex', and the 'initUI'/'reset'
placement cycle onto the underlying 'QGridLayout'.

'LayoutIndex' has identity semantics (no '__eq__'/'__hash__'), so the same
index instance is reused as the dictionary key throughout.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QGridLayout
from worktoy.waitaminute import TypeException

from worQt.layouts import GridLayout, BaseLayout, LayoutIndex
from worQt.widgets import PaintedWidget

from . import LayoutAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunGridLayout(LayoutAppTest):
  """Tests for the 'GridLayout' manager."""

  def run_is_base_layout(self) -> None:
    """'GridLayout' is a 'BaseLayout' and a 'QGridLayout'."""
    self.assertTrue(issubclass(GridLayout, BaseLayout))
    layout = GridLayout()
    self.assertIsInstance(layout, QGridLayout)

  def run_widget_dict_starts_empty(self) -> None:
    """A fresh layout has an empty widget mapping."""
    layout = GridLayout()
    self.assertEqual(layout.widgetDict, {})

  def run_setitem_getitem(self) -> None:
    """A widget set at an index reads back at the same index."""
    layout = GridLayout()
    index = LayoutIndex(0, 0)
    widget = PaintedWidget()
    layout[index] = widget
    self.assertIs(layout[index], widget)
    self.assertIn(index, layout.widgetDict)

  def run_init_ui_adds_widgets(self) -> None:
    """'initUI' places every mapped widget onto the 'QGridLayout'."""
    layout = GridLayout()
    layout[LayoutIndex(0, 0)] = PaintedWidget()
    layout[LayoutIndex(0, 1)] = PaintedWidget()
    self.assertEqual(QGridLayout.count(layout), 0)
    layout.initUI()
    self.assertEqual(QGridLayout.count(layout), 2)

  def run_reset_clears(self) -> None:
    """'reset' removes every item previously placed on the layout."""
    layout = GridLayout()
    layout[LayoutIndex(0, 0)] = PaintedWidget()
    layout.initUI()
    self.assertEqual(QGridLayout.count(layout), 1)
    layout.reset()
    self.assertEqual(QGridLayout.count(layout), 0)

  def run_widget_dict_type_guards(self) -> None:
    """The widget-mapping accessor rejects a corrupt mapping."""
    badWidget = GridLayout()
    badWidget.__widget_dict__ = {LayoutIndex(0, 0): 'not a widget'}
    with self.assertRaises(TypeException):
      _ = badWidget.widgetDict
    badIndex = GridLayout()
    badIndex.__widget_dict__ = {'not an index': PaintedWidget()}
    with self.assertRaises(TypeException):
      _ = badIndex.widgetDict
    notDict = GridLayout()
    notDict.__widget_dict__ = 'bad'
    with self.assertRaises(TypeException):
      _ = notDict.widgetDict

  def run_widget_dict_recursion_guard(self) -> None:
    """The lazy widget-mapping getter guards against a failed build."""
    with self.assertRaises(RecursionError):
      GridLayout()._getWidgetDict(_recursion=True)
