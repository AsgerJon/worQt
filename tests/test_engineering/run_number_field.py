"""
RunNumberField covers 'NumberField', a form field holding one number
with its unit: a click and the number typed replaces the one shown,
Enter or leaving the field takes it, Escape gives it up, the arrow keys
step it, and what is taken stays between its limits.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QApplication

from worQt.engineering.gui import NumberField

from . import EngineeringWidgetTest

_NO_MOD = Qt.KeyboardModifier.NoModifier


class RunNumberField(EngineeringWidgetTest):
  """Tests for 'NumberField'."""

  def _liveField(self, ) -> NumberField:
    field = NumberField()
    field.value, field.unit, field.step = 6.0, 'm', 0.05
    field.minimum, field.maximum = 1.2, 100.0
    field.resize(160, 32)
    self.showLive(field)
    return field

  def enter(self, field: NumberField, text: str) -> None:
    """Click the field, type 'text' and press Enter."""
    self.click(field)
    self.typeText(field, text)
    self.key(field, Qt.Key.Key_Return, _NO_MOD, '\r')

  def run_shows_its_number(self) -> None:
    """The field shows its number to its decimals, its unit beside it."""
    field = self._liveField()
    self.assertEqual(field.shownText, '6.00')
    self.assertEqual(field.unit, 'm')
    self.assertFalse(field.grab().isNull())

  def run_typing_replaces_and_enter_takes_it(self) -> None:
    """After a click the first key replaces the number shown; Enter
    takes the number typed and tells of it."""
    field = self._liveField()
    spy = self.spy(field.valueEdited)
    self.enter(field, '7.5')
    self.assertEqual(field.value, 7.5)
    self.assertEqual(spy.args, (7.5,))

  def run_escape_gives_it_up(self) -> None:
    """Escape gives up what was typed."""
    field = self._liveField()
    spy = self.spy(field.valueEdited)
    self.click(field)
    self.typeText(field, '9')
    self.key(field, Qt.Key.Key_Escape, _NO_MOD, '\x1b')
    self.assertEqual(field.value, 6.0)
    self.assertEqual(field.shownText, '6.00')
    self.assertEqual(spy.count, 0)

  def run_leaving_takes_it(self) -> None:
    """Leaving the field takes what was typed, as Enter does."""
    field = self._liveField()
    self.click(field)
    self.typeText(field, '3')
    QApplication.sendEvent(field, QFocusEvent(QEvent.Type.FocusOut))
    self.assertEqual(field.value, 3.0)

  def run_arrow_keys_step(self) -> None:
    """The up and down arrow keys step the number, each step told of."""
    field = self._liveField()
    spy = self.spy(field.valueEdited)
    self.key(field, Qt.Key.Key_Up)
    self.assertAlmostEqual(field.value, 6.05)
    self.key(field, Qt.Key.Key_Down)
    self.key(field, Qt.Key.Key_Down)
    self.assertAlmostEqual(field.value, 5.95)
    self.assertEqual(spy.count, 3)

  def run_limits(self) -> None:
    """A number beyond the limits is taken as the nearest it may be."""
    field = self._liveField()
    self.enter(field, '0.5')
    self.assertEqual(field.value, 1.2)
    self.enter(field, '1000')
    self.assertEqual(field.value, 100.0)

  def run_a_comma_is_a_decimal_point(self) -> None:
    """A comma is read as the decimal point."""
    field = self._liveField()
    self.enter(field, '7,25')
    self.assertEqual(field.value, 7.25)

  def run_what_is_no_number_is_given_up(self) -> None:
    """What is no number is given up, and letters are not typed at
    all; the same number again tells of nothing."""
    field = self._liveField()
    spy = self.spy(field.valueEdited)
    self.enter(field, '-')
    self.enter(field, 'abc')
    self.enter(field, '6')
    self.assertEqual(field.value, 6.0)
    self.assertEqual(spy.count, 0)
