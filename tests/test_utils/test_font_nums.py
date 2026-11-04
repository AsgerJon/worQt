"""
TestFontNums subclasses 'UtilsTest' and tests the font vocabulary in
'worQt.utils.font_nums' that works without a 'QApplication': the weight
enumeration and its resolution, the line flags (combinations included),
and how 'FontFamily' and 'GenericFamilyNum' choose among installed
families - given the installed families as an argument, so the choice is
tested on its own, independent of this machine's fonts.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication
from worktoy.waitaminute.keenum import KeeResolveError

from worQt.utils.font_nums import FontFamily, GenericFamilyNum
from worQt.utils.font_nums import FontWeightNum, FontLineFlags

from . import UtilsTest


class TestFontNums(UtilsTest):
  """Tests for the font enumerations and the family choice."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  WEIGHT   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_weight_value(self) -> None:
    """A weight member carries its 'QFont.Weight' value."""
    self.assertEqual(FontWeightNum.BOLD.value, QFont.Weight.Bold)

  def test_weight_apply(self) -> None:
    """'apply' runs on a frozen member and sets the weight on the font."""
    font = QFont()
    FontWeightNum.THIN.apply(font)
    self.assertEqual(font.weight(), QFont.Weight.Thin)

  def test_weight_resolve(self) -> None:
    """A weight resolves from its member, its name or its Qt value."""
    self.assertIs(FontWeightNum(FontWeightNum.BOLD), FontWeightNum.BOLD)
    self.assertIs(FontWeightNum('bold'), FontWeightNum.BOLD)
    self.assertIs(FontWeightNum(QFont.Weight.Bold), FontWeightNum.BOLD)

  def test_weight_resolve_miss(self) -> None:
    """Something that is no weight is refused."""
    with self.assertRaises(KeeResolveError):
      FontWeightNum('heavy-ish')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LINE FLAGS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_line_flags_single(self) -> None:
    """A single flag sets its own line and clears the others."""
    font = QFont()
    font.setOverline(True)
    FontLineFlags.UNDERLINE.apply(font)
    self.assertTrue(font.underline())
    self.assertFalse(font.strikeOut())
    self.assertFalse(font.overline())

  def test_line_flags_combined(self) -> None:
    """A combination sets every line in it (it used to set none)."""
    font = QFont()
    (FontLineFlags.UNDERLINE | FontLineFlags.OVERLINE).apply(font)
    self.assertTrue(font.underline())
    self.assertFalse(font.strikeOut())
    self.assertTrue(font.overline())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FAMILY CHOICE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_normalize(self) -> None:
    """Spellings of one family normalize to the same key."""
    self.assertEqual(FontFamily.normalize('JetBrains Mono'),
                     FontFamily.normalize('jetbrains_mono'))
    self.assertEqual(FontFamily.normalize('Noto-Sans'), 'notosans')

  def test_pick_returns_installed_spelling(self) -> None:
    """'pick' finds a family however it is spelled, and returns the
    installed spelling."""
    installed = ('DejaVu Sans', 'JetBrains Mono')
    self.assertEqual(FontFamily.pick(installed, 'JetBrainsMono'),
                     'JetBrains Mono')

  def test_pick_follows_the_order_asked(self) -> None:
    """The first name asked for that is installed wins."""
    installed = ('Hack', 'Fira Mono')
    self.assertEqual(FontFamily.pick(installed, 'FiraMono', 'Hack'),
                     'Fira Mono')

  def test_pick_none_installed(self) -> None:
    """With none of the names installed, 'pick' returns 'None'."""
    self.assertIsNone(FontFamily.pick(('Arial',), 'Hack', 'Fira Mono'))

  def test_installed_needs_an_application(self) -> None:
    """The installed families are unknown before a 'QApplication'."""
    if QApplication.instance() is not None:  # pragma: no cover
      self.skipTest('a QApplication is running in this process')
    with self.assertRaises(RuntimeError):
      FontFamily.installed()

  def test_generic_members(self) -> None:
    """'GenericFamilyNum' enumerates serif, sans and mono."""
    self.assertEqual([member.name for member in GenericFamilyNum],
                     ['SERIF', 'SANS', 'MONO'])

  def test_generic_prefers_the_preferred(self) -> None:
    """A preferred family beats an acceptable one, whatever the order of
    the installed list."""
    installed = ('Arimo', 'Noto Sans', 'Montserrat')
    self.assertEqual(GenericFamilyNum.SANS.familyAmong(installed),
                     'Montserrat')

  def test_generic_falls_back_to_acceptable(self) -> None:
    """With no preferred family installed, an acceptable one is used."""
    installed = ('Comic Sans MS', 'Inconsolata')
    self.assertEqual(GenericFamilyNum.MONO.familyAmong(installed),
                     'Inconsolata')

  def test_generic_finds_nothing(self) -> None:
    """With none of its families installed a member finds none, which
    sends 'family' to Qt's own choice."""
    self.assertIsNone(GenericFamilyNum.SERIF.familyAmong(('Comic Sans',)))

  def test_generic_kinds_do_not_mix(self) -> None:
    """Each member chooses only from its own kind."""
    installed = ('Noto Serif', 'Noto Sans', 'Hack')
    self.assertEqual(GenericFamilyNum.SERIF.familyAmong(installed),
                     'Noto Serif')
    self.assertEqual(GenericFamilyNum.SANS.familyAmong(installed),
                     'Noto Sans')
    self.assertEqual(GenericFamilyNum.MONO.familyAmong(installed), 'Hack')
