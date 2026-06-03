"""
Exercises the type-specific value editors and the form panel against a
live 'QApplication'. Qt emits its widget signals synchronously, so these
tests mutate the inner widgets and assert on the results without pumping
the event loop or opening any modal dialog.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json

from worQt.qtest import AppTest
from worQt.widgets import (
  StringValueEdit,
  NumberValueEdit,
  BoolValueEdit,
  valueEditor,
)
from worQt.window import JsonWindow


class TestForm(AppTest):
  """Round-trips the type-specific value editors and the form panel."""

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

  def test_form_lists_only_scalars(self, ) -> None:
    """Nested objects and arrays get no form row."""
    window = JsonWindow()
    window.show()
    window.loadData(
        {'name': 'x', 'n': 3, 'ok': True, 'nested': {'a': 1}, 'arr': [1]})
    editors = getattr(window.formWidget, '__editors__')
    self.assertEqual(set(editors), {'name', 'n', 'ok'})

  def test_form_edit_updates_text(self, ) -> None:
    """Editing a form field rewrites the JSON, preserving non-scalars."""
    window = JsonWindow()
    window.show()
    window.loadData(
        {'name': 'x', 'n': 3, 'ok': True, 'nested': {'a': 1}, 'arr': [1]})
    editors = getattr(window.formWidget, '__editors__')
    editors['n'].numberEdit.setText('10')
    editors['ok'].checkBox.setChecked(False)
    editors['name'].lineEdit.setText('worQt')
    data = json.loads(window.editor.toPlainText())
    self.assertEqual(data['n'], 10)
    self.assertFalse(data['ok'])
    self.assertEqual(data['name'], 'worQt')
    self.assertEqual(data['nested'], {'a': 1})  # preserved untouched
    self.assertEqual(data['arr'], [1])
    self.assertTrue(window.dirty)
