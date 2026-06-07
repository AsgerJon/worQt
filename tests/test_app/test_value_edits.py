"""
Exercises the type-specific value editors against a live 'QApplication'.
These editors are reused by 'SettingsDialog' (the JSON form that also used
them is deprecated). Qt emits its widget signals synchronously, so the tests
mutate the inner widgets and assert on the results without pumping the event
loop or opening any modal dialog.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.qtest import AppTest
from worQt.widgets import (
  StringValueEdit,
  NumberValueEdit,
  BoolValueEdit,
  valueEditor,
)


class TestValueEdits(AppTest):
  """Round-trips the type-specific value editors and the picker factory."""

  def test_string_edit(self, ) -> None:
    """The string editor reflects its line edit both ways."""
    editor = StringValueEdit()
    editor.value = 'hi'
    editor.build()
    self.assertEqual(editor.value, 'hi')
    editor.lineEdit.setText('bye')
    self.assertEqual(editor.value, 'bye')

  def test_number_edit_int(self, ) -> None:
    """The number editor keeps an int value in sync via the line edit."""
    editor = NumberValueEdit()
    editor.value = 7
    editor.build()
    self.assertEqual(editor.value, 7)
    editor.numberEdit.setText('42')
    self.assertEqual(editor.value, 42)
    self.assertEqual(editor.slider.value(), 42)

  def test_number_edit_float(self, ) -> None:
    """A float value survives the slider's hundredth-step resolution."""
    editor = NumberValueEdit()
    editor.value = 3.25
    editor.build()
    self.assertEqual(editor.value, 3.25)
    self.assertEqual(editor.slider.value(), 325)

  def test_bool_edit(self, ) -> None:
    """The bool editor reflects its checkbox both ways."""
    editor = BoolValueEdit()
    editor.value = True
    editor.build()
    self.assertTrue(editor.value)
    editor.checkBox.setChecked(False)
    self.assertFalse(editor.value)

  def test_factory_picks_by_type(self, ) -> None:
    """'valueEditor' maps each scalar type to its editor, bool before int."""
    self.assertIsInstance(valueEditor('x'), StringValueEdit)
    self.assertIsInstance(valueEditor(3), NumberValueEdit)
    self.assertIsInstance(valueEditor(3.5), NumberValueEdit)
    self.assertIsInstance(valueEditor(True), BoolValueEdit)
