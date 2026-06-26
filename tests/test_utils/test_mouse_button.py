"""
TestMouseButton subclasses 'UtilsTest' and tests the
'worQt.utils.MouseButtonNum' enumeration: its members, their mapping to
'Qt.MouseButton', resolution by name and value, and the truth value (the
null button is falsy, every real button is truthy).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import Qt

from worQt.utils import MouseButtonNum

from . import UtilsTest


class TestMouseButton(UtilsTest):
  """Tests for the 'MouseButtonNum' enumeration."""

  def test_members(self) -> None:
    """The buttons are null, left, right, middle, back and forward."""
    self.assertEqual([m.name for m in MouseButtonNum],
                     ['NULL', 'LEFT', 'RIGHT', 'MIDDLE', 'BACK', 'FORWARD'])

  def test_values(self) -> None:
    """Each member carries its 'Qt.MouseButton' value."""
    self.assertEqual(MouseButtonNum.LEFT.value, Qt.MouseButton.LeftButton)
    self.assertEqual(MouseButtonNum.NULL.value, Qt.MouseButton.NoButton)

  def test_resolve_by_name(self) -> None:
    """A member resolves from its name."""
    self.assertIs(MouseButtonNum('LEFT'), MouseButtonNum.LEFT)

  def test_resolve_by_value(self) -> None:
    """A member resolves from its 'Qt.MouseButton' value."""
    self.assertIs(MouseButtonNum(Qt.MouseButton.RightButton),
                  MouseButtonNum.RIGHT)

  def test_bool(self) -> None:
    """The null button is falsy; a real button is truthy."""
    self.assertFalse(MouseButtonNum.NULL)
    self.assertTrue(MouseButtonNum.LEFT)
