"""
RunFontFamily subclasses 'UtilsAppTest' and covers the parts of
'FontFamilyMeta' that need a live 'QApplication': the dynamic
'__getattr__' that materialises a font-family member on first access by
querying 'QFontDatabase'. The in-process generic-family behaviour lives in
'TestFontNums'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFontDatabase

from worQt.utils.font_nums import FontFamilyNum

from . import UtilsAppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class RunFontFamily(UtilsAppTest):
  """Tests for the running-app font-family discovery."""

  @staticmethod
  def _key(family: str) -> str:
    """The attribute spelling 'FontFamilyMeta.__getattr__' resolves: the
    family name lower-cased with spaces turned into underscores."""
    return family.lower().replace(' ', '_')

  def run_dynamic_member_creation(self) -> None:
    """Accessing a family by its derived key materialises a member and
    grows the enumeration (the '__registered_members__' fix)."""
    families = QFontDatabase.families()
    self.assertTrue(families)
    target = families[0]
    before = len([*FontFamilyNum])
    member = getattr(FontFamilyNum, self._key(target))
    self.assertIsInstance(member, FontFamilyNum)
    self.assertIn(member.value, families)
    self.assertEqual(member.name, self._key(target).upper())
    after = len([*FontFamilyNum])
    self.assertGreaterEqual(after, before)

  def run_dynamic_member_cached(self) -> None:
    """A second access returns the same member object, not a fresh one."""
    key = self._key(QFontDatabase.families()[0])
    first = getattr(FontFamilyNum, key)
    second = getattr(FontFamilyNum, key)
    self.assertIs(first, second)

  def run_unknown_family_raises(self) -> None:
    """A key matching no installed family raises 'AttributeError'."""
    with self.assertRaises(AttributeError):
      _ = getattr(FontFamilyNum, 'definitely_not_a_real_font_zzz')

  def run_dunder_miss_raises(self) -> None:
    """A missing dunder is deferred to normal lookup (the dunder guard
    that prevents '__getattr__' recursing), so it raises 'AttributeError'
    rather than being treated as a font family."""
    with self.assertRaises(AttributeError):
      _ = getattr(FontFamilyNum, '__no_such_dunder__')

  def run_partial_match_skipped(self) -> None:
    """A key that is a proper substring of a family (so a remainder is
    left after stripping it) is skipped, not matched, and ultimately
    raises 'AttributeError'."""
    family = QFontDatabase.families()[0]
    partial = family.lower()[:-1]  # a truncation: substring, never exact
    with self.assertRaises(AttributeError):
      _ = getattr(FontFamilyNum, partial)

  def run_getattr_before_members_built(self) -> None:
    """While the member registry is absent, '__getattr__' defers to normal
    lookup instead of trying to build a member (the build-time guard)."""
    saved = FontFamilyNum.__dict__.get('__registered_members__')
    type.__setattr__(FontFamilyNum, '__registered_members__', None)
    try:
      with self.assertRaises(AttributeError):
        _ = getattr(FontFamilyNum, 'somethingmissingzzz')
    finally:
      type.__setattr__(FontFamilyNum, '__registered_members__', saved)
