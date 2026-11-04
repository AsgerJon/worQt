"""
RunFontFamily subclasses 'UtilsAppTest' and covers the family lookup that
needs a live 'QApplication': the installed families, resolving one by name
however it is spelled, and each generic family finding a real family. The
assertions hold on any machine, whatever fonts it has installed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QFont

from worQt.utils.font_nums import FontFamily, GenericFamilyNum

from . import UtilsAppTest


class RunFontFamily(UtilsAppTest):
  """Tests for the installed-family lookup."""

  def run_installed(self) -> None:
    """The installed families are a non-empty tuple of names."""
    installed = FontFamily.installed()
    self.assertIsInstance(installed, tuple)
    self.assertTrue(installed)
    self.assertTrue(all(isinstance(name, str) for name in installed))

  def run_resolve_any_spelling(self) -> None:
    """An installed family resolves from another spelling of its name."""
    family = FontFamily.installed()[0]
    respelled = str.replace(str.upper(family), ' ', '_')
    resolved = FontFamily.resolve(respelled)
    self.assertIn(resolved, FontFamily.installed())
    self.assertEqual(FontFamily.normalize(resolved),
                     FontFamily.normalize(family))

  def run_resolve_unknown_raises(self) -> None:
    """A family that is not installed is refused, not substituted."""
    with self.assertRaises(LookupError):
      FontFamily.resolve('definitely not a real font zzz')

  def run_hinted_always_answers(self) -> None:
    """Qt names a family for every style hint, the generic last resort."""
    for hint in (QFont.StyleHint.Serif, QFont.StyleHint.SansSerif,
                 QFont.StyleHint.Monospace):
      self.assertTrue(FontFamily.hinted(hint))

  def run_generic_family_is_real(self) -> None:
    """Each generic family resolves to an installed family, or to the one
    Qt chooses when none of its candidates is installed."""
    installed = FontFamily.installed()
    for member in GenericFamilyNum:
      family = member.family
      self.assertIsInstance(family, str)
      if member.familyAmong(installed) is not None:
        self.assertIn(family, installed)
      else:  # pragma: no cover  # only on a machine without any candidate
        self.assertTrue(family)

  def run_generic_apply(self) -> None:
    """'apply' sets the generic family's family on a 'QFont'."""
    font = GenericFamilyNum.MONO.apply(QFont())
    self.assertEqual(font.family(), GenericFamilyNum.MONO.family)
