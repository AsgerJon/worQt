"""
RunToolButton covers 'ToolButton', a button saying what it does: a click
on it tells of it, unless it is disabled; it may show itself checked.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.gui import ToolButton

from . import EngineeringWidgetTest


class RunToolButton(EngineeringWidgetTest):
  """Tests for 'ToolButton'."""

  def _liveButton(self, ) -> ToolButton:
    button = ToolButton()
    button.text = 'Add support'
    button.resize(button.sizeHint())
    self.showLive(button)
    return button

  def run_a_click_tells(self) -> None:
    """A click on the button tells of it."""
    button = self._liveButton()
    spy = self.spy(button.clicked)
    self.click(button)
    self.assertEqual(spy.count, 1)

  def run_disabled_says_nothing(self) -> None:
    """A disabled button tells of no click."""
    button = self._liveButton()
    spy = self.spy(button.clicked)
    button.setEnabled(False)
    self.click(button)
    self.assertEqual(spy.count, 0)

  def run_fits_its_text_and_paints(self) -> None:
    """The button is wide enough for its text, and paints checked or
    not."""
    button = self._liveButton()
    width = button.font.metrics.horizontalAdvance('Add support')
    self.assertGreater(button.sizeHint().width(), width)
    button.checked = True
    self.assertFalse(button.grab().isNull())
