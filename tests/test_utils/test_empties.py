"""
TestEmpties subclasses 'UtilsTest' and tests the small descriptor/flag
helpers: 'EmptyPen' and 'EmptyBrush' (the no-op pen/brush descriptors) and
'ButtonStateFlags.__bool__'. All are plain value types, so no
'QApplication' is needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QBrush

from worQt.utils import EmptyPen, EmptyBrush, ButtonStateFlags

from . import UtilsTest


class _Host:
  """A throwaway owner carrying the empty pen/brush descriptors."""

  pen = EmptyPen()
  brush = EmptyBrush()


class TestEmpties(UtilsTest):
  """Tests for 'EmptyPen', 'EmptyBrush' and 'ButtonStateFlags'."""

  def test_empty_pen_class_access(self) -> None:
    """Class access returns the descriptor itself."""
    self.assertIsInstance(_Host.pen, EmptyPen)

  def test_empty_pen_instance(self) -> None:
    """Instance access yields a no-pen, transparent 'QPen'."""
    pen = _Host().pen
    self.assertIsInstance(pen, QPen)
    self.assertEqual(pen.style(), Qt.PenStyle.NoPen)
    self.assertEqual(pen.color().alpha(), 0)

  def test_empty_brush_class_access(self) -> None:
    """Class access returns the descriptor itself."""
    self.assertIsInstance(_Host.brush, EmptyBrush)

  def test_empty_brush_instance(self) -> None:
    """Instance access yields a no-brush, transparent 'QBrush'."""
    brush = _Host().brush
    self.assertIsInstance(brush, QBrush)
    self.assertEqual(brush.style(), Qt.BrushStyle.NoBrush)
    self.assertEqual(brush.color().alpha(), 0)

  def test_button_state_flags_bool(self) -> None:
    """The flags are truthy only when the disabled bit is set."""
    self.assertTrue(ButtonStateFlags.DISABLED)
    self.assertFalse(ButtonStateFlags.HOVERED)
