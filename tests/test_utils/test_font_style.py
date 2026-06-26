"""
TestFontStyle subclasses 'UtilsTest' and tests the
'worQt.utils.font_nums.FontStyleNum' enumeration: its members, their
mapping to 'QFont.Style', and resolution by name and by raw 'QFont.Style'
value (the '__class_resolve__' hook).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QFont

from worQt.utils.font_nums import FontStyleNum

from . import UtilsTest


class TestFontStyle(UtilsTest):
  """Tests for the 'FontStyleNum' enumeration."""

  def test_members(self) -> None:
    """The styles are the upright, italic and oblique faces."""
    self.assertEqual([m.name for m in FontStyleNum],
                     ['NORMAL', 'ITALIC', 'OBLIQUE'])

  def test_values(self) -> None:
    """Each member carries its 'QFont.Style' value."""
    self.assertEqual(FontStyleNum.NORMAL.value, QFont.Style.StyleNormal)
    self.assertEqual(FontStyleNum.ITALIC.value, QFont.Style.StyleItalic)
    self.assertEqual(FontStyleNum.OBLIQUE.value, QFont.Style.StyleOblique)

  def test_resolve_by_name(self) -> None:
    """A member resolves from its name, case-insensitively."""
    self.assertIs(FontStyleNum('italic'), FontStyleNum.ITALIC)

  def test_resolve_by_value(self) -> None:
    """'__class_resolve__' resolves a member from a 'QFont.Style'."""
    self.assertIs(FontStyleNum(QFont.Style.StyleItalic), FontStyleNum.ITALIC)
    self.assertIs(FontStyleNum(QFont.Style.StyleNormal), FontStyleNum.NORMAL)
