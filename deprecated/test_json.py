"""
Exercises the generic JSON application against a live 'QApplication'. The
window's save path is driven directly through the model and the
non-dialog code path, so no modal 'QFileDialog'/'QMessageBox' is opened
(which would hang the harness until the deadline). The pure 'JsonDocument'
validation is checked too, without any Qt at all.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import os
import tempfile

from PySide6.QtTest import QTest

from worQt.qtest import AppTest
from worQt.doc import JsonDocument
from worQt.widgets import JsonHighlighter
from worQt.window import JsonWindow


class TestJsonWindow(AppTest):
  """Round-trips JSON through a live 'JsonWindow' and its model."""

  def test_round_trip(self, ) -> None:
    """Editor text saved to disk reloads byte-for-byte into a new window."""
    payload = {'name': 'worQt', 'nums': [1, 2, 3], 'nested': {'ok': True}}
    tmpDir = tempfile.mkdtemp()
    path = os.path.join(tmpDir, 'data.json')

    window = JsonWindow()
    window.show()
    QTest.qWait(250)  # dwell so the window actually paints

    #  Seed the editor and save through the non-dialog path (path is set)
    window.document.path = path
    window._showText(json.dumps(payload))
    self.assertTrue(window._onSave())
    self.assertFalse(window.dirty)

    #  The file on disk parses back to the original payload
    with open(path, 'r', encoding='utf-8') as jsonFile:
      self.assertEqual(json.load(jsonFile), payload)

    #  A fresh window loads the same file through its model
    other = JsonWindow()
    other.show()
    QTest.qWait(250)
    other.document.loadFile(path)
    other._showText(other.document.text)
    self.assertEqual(json.loads(other.editor.toPlainText()), payload)
    self.assertEqual(other.document.path, path)

    window.close()
    other.close()

  def test_invalid_json_rejected(self, ) -> None:
    """Setting non-JSON text on the model raises and leaves data intact."""
    document = JsonDocument()
    before = document.data
    with self.assertRaises(ValueError):
      document.text = '{not valid json'
    self.assertEqual(document.data, before)

  def test_format_and_minify(self, ) -> None:
    """Format re-indents and minify collapses, both preserving data."""
    payload = {'b': 2, 'a': [1, 2]}
    window = JsonWindow()
    window.show()
    QTest.qWait(150)

    window._showText(json.dumps(payload, separators=(',', ':')))
    window._onFormat()
    formatted = window.editor.toPlainText()
    self.assertIn('\n', formatted)  # pretty-printed spans lines
    self.assertEqual(json.loads(formatted), payload)

    window._onMinify()
    minified = window.editor.toPlainText()
    self.assertNotIn('\n', minified)  # collapsed to a single line
    self.assertNotIn(' ', minified)
    self.assertEqual(json.loads(minified), payload)

  def test_validity_indicator(self, ) -> None:
    """The status readout flips with the editor's JSON validity."""
    window = JsonWindow()
    window.show()
    QTest.qWait(150)

    window._showText('{"ok": true}')
    self.assertEqual(window.validityLabel.text(), '● valid JSON')

    window.editor.setPlainText('{oops')  # a live edit, not a programmatic set
    self.assertEqual(window.validityLabel.text(), '● invalid JSON')

  def test_model_compact(self, ) -> None:
    """The model's compact serialisation drops all insignificant space."""
    document = JsonDocument()
    document.text = '{"a": 1, "b": [2, 3]}'
    self.assertEqual(document.compact, '{"a":1,"b":[2,3]}')

  def test_model_validate(self, ) -> None:
    """'validate' reports success silently and failure with a message."""
    ok, message = JsonDocument.validate('{"x": 1}')
    self.assertTrue(ok)
    self.assertEqual(message, '')
    bad, why = JsonDocument.validate('{')
    self.assertFalse(bad)
    self.assertTrue(why)

  def test_highlighter_attached(self, ) -> None:
    """The window wires a 'JsonHighlighter' onto the editor's document."""
    window = JsonWindow()
    window.show()
    QTest.qWait(150)
    self.assertIsInstance(window.__json_highlighter__, JsonHighlighter)
    self.assertIs(
        window.__json_highlighter__.document(), window.editor.document())
