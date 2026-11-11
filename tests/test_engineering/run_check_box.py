"""
RunCheckBox covers 'CheckBox', a box ticked or not with what it means
beside it: a click or Space ticks it or clears it, and it tells of each
change; greyed out, it takes no clicks.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.engineering.gui import CheckBox

from . import EngineeringWidgetTest


class RunCheckBox(EngineeringWidgetTest):
  """Tests for 'CheckBox'."""

  def openBox(self) -> CheckBox:
    """A box saying 'Use GPU', shown live."""
    box = CheckBox()
    box.text = 'Use GPU'
    box.resize(box.sizeHint())
    self.showLive(box)
    return box

  def run_says_what_it_is(self) -> None:
    """It shows what it means, and starts clear."""
    box = self.openBox()
    self.assertEqual(box.text, 'Use GPU')
    self.assertFalse(box.checked)
    self.assertGreater(box.sizeHint().width(), box.sizeHint().height())
    self.assertFalse(box.grab().isNull())

  def run_a_click_ticks_it(self) -> None:
    """A click ticks it and another clears it, each change told once."""
    box = self.openBox()
    spy = self.spy(box.toggled)
    self.click(box)
    self.assertTrue(box.checked)
    self.click(box)
    self.assertFalse(box.checked)
    self.assertEqual(spy.count, 2)
    self.assertEqual([args[0] for args in spy.args], [True, False])

  def run_space_ticks_it(self) -> None:
    """Space ticks it too."""
    box = self.openBox()
    self.key(box, Qt.Key.Key_Space)
    self.assertTrue(box.checked)

  def run_set_as_it_is(self) -> None:
    """Set to what it already is, it tells of nothing."""
    box = self.openBox()
    spy = self.spy(box.toggled)
    box.checked = False
    self.assertEqual(spy.count, 0)
    box.checked = True
    self.assertEqual(spy.count, 1)

  def run_greyed_out(self) -> None:
    """Greyed out, it takes no clicks."""
    box = self.openBox()
    box.setEnabled(False)
    self.click(box)
    self.assertFalse(box.checked)
    self.assertFalse(box.grab().isNull())
