"""
TestFontNums subclasses 'UtilsTest' and tests the font enumerations in
'worQt.utils.font_nums'. In particular it guards the frozen-member
contract: 'apply' must be a plain method, since an overloaded method
cannot run on a frozen 'KeeNum'/'KeeFlags' member (the dispatcher would
try to cache a bound method on it and hit 'KeeWriteOnceError').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from types import SimpleNamespace

from PySide6.QtGui import QFont
from worktoy.keenum import Kee
from worktoy.waitaminute import TypeException

from worQt.utils import WFont
from worQt.utils.font_nums import FontWeightNum, FontLineFlags, FontMeta
from worQt.utils.font_nums import FontFamilyNum, GenericFamilyNum, FontFamilyMeta
import worQt.utils.font_nums._font_family_space as familySpace

from . import UtilsTest


class _NoResolveNum(FontMeta.keeNum):
  """A 'FontMeta' enumeration with no '__class_resolve__', so member
  resolution falls through to the base 'FontMeta._resolveMember'."""

  A = Kee[int](1)
  B = Kee[int](2)


class _FakeFamily:
  """A stand-in family member exposing only the '.value' the default
  getters compare against the curated category lists."""

  def __init__(self, value: str) -> None:
    self.value = value


class _FakeFamilyNum:
  """A stand-in enumeration class for driving the 'defaultSerif/Sans/Mono'
  getters with controlled members, independent of installed fonts."""

  __good_serif__ = FontFamilyMeta.__good_serif__
  __serif_families__ = FontFamilyMeta.__serif_families__
  __good_sans__ = FontFamilyMeta.__good_sans__
  __sans_serif__ = FontFamilyMeta.__sans_serif__
  __good_mono__ = FontFamilyMeta.__good_mono__
  __mono_space__ = FontFamilyMeta.__mono_space__
  FALLBACK_SERIF = 'FALLBACK_SERIF'
  FALLBACK_SANS = 'FALLBACK_SANS'
  FALLBACK_MONO = 'FALLBACK_MONO'

  def __init__(self, *values: str) -> None:
    self._families = [_FakeFamily(value) for value in values]

  def __iter__(self):
    return iter(self._families)


def _midOnly(midList, goodList) -> str:
  """A name present in the mid list but not the good list."""
  good = {name.lower() for name in goodList}
  return next(name for name in midList if name.lower() not in good)


class TestFontNums(UtilsTest):
  """Tests for the font enumerations, including the frozen-member fix."""

  def test_weight_value(self) -> None:
    """A weight member carries its 'QFont.Weight' value."""
    self.assertEqual(FontWeightNum.BOLD.value, QFont.Weight.Bold)

  def test_weight_apply_on_frozen_member(self) -> None:
    """'apply' runs on a frozen member and sets the weight on the font."""
    font = QFont()
    FontWeightNum.BOLD.apply(font)
    self.assertEqual(font.weight(), QFont.Weight.Bold)

  def test_weight_apply_normal(self) -> None:
    """A second member applies its own weight without interference."""
    font = QFont()
    FontWeightNum.THIN.apply(font)
    self.assertEqual(font.weight(), QFont.Weight.Thin)

  def test_weight_resolve_from_value(self) -> None:
    """'__class_resolve__' resolves a member from its 'QFont.Weight'."""
    self.assertIs(FontWeightNum(QFont.Weight.Bold), FontWeightNum.BOLD)

  def test_weight_resolve_from_name(self) -> None:
    """A name that the custom resolver declines falls through to the base
    name resolution ('FontMeta._resolveMember')."""
    self.assertIs(FontWeightNum('BOLD'), FontWeightNum.BOLD)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FONT META INSTANCE CHECK  # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_instancecheck_member_and_value(self) -> None:
    """'FontMeta.__instancecheck__' admits a member, a member's value, and
    rejects anything else."""
    self.assertIsInstance(FontWeightNum.BOLD, FontWeightNum)
    self.assertIsInstance(QFont.Weight.Bold, FontWeightNum)
    self.assertNotIsInstance('nope', FontWeightNum)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FONT FAMILY SPACE HELPERS  # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_upper_score(self) -> None:
    """'_upperScore' upper-snakes a display family name."""
    self.assertEqual(familySpace._upperScore('Cascadia Code'),
                     'CASCADIA_CODE')

  def test_name_value_pairs_filters(self) -> None:
    """'_nameValuePairs' drops empty, digit-leading and duplicate names."""
    pairs = familySpace._nameValuePairs(
        '', '123Font', 'DupFont', 'DupFont', 'Good Font')
    names = [name for name, _ in pairs]
    self.assertIn('DUP_FONT', names)
    self.assertIn('GOOD_FONT', names)
    self.assertEqual(len(names), len(set(names)))

  def test_filter_families(self) -> None:
    """'_filterFamilies' removes blacklisted suffixes, digits and names."""
    kept = familySpace._filterFamilies(
        'GoodFont', 'BadNF', 'sym1bol', 'KanjiStrokeOrders')
    self.assertEqual(kept, ('GoodFont',))

  def test_line_flags_apply_underline(self) -> None:
    """The 'UNDERLINE' flag applies underline to the font."""
    font = QFont()
    FontLineFlags.UNDERLINE.apply(font)
    self.assertTrue(font.underline())
    self.assertFalse(font.strikeOut())

  def test_line_flags_apply_strikeout(self) -> None:
    """The 'STRIKEOUT' flag applies strike-out to the font."""
    font = QFont()
    FontLineFlags.STRIKEOUT.apply(font)
    self.assertTrue(font.strikeOut())
    self.assertFalse(font.underline())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GENERIC FAMILY  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_generic_members(self) -> None:
    """'GenericFamilyNum' enumerates exactly mono, sans and serif."""
    names = {member.name for member in GenericFamilyNum}
    self.assertEqual(names, {'MONO', 'SANS', 'SERIF'})

  def test_generic_default_is_family(self) -> None:
    """Each generic member resolves to a concrete 'FontFamilyNum' member
    whose value is a non-empty family name string."""
    for member in GenericFamilyNum:
      family = member.default
      self.assertIsInstance(family, FontFamilyNum)
      self.assertIsInstance(family.value, str)
      self.assertTrue(family.value)

  def test_generic_round_trip(self) -> None:
    """Resolving a generic member's default family back through
    'GenericFamilyNum' returns the same generic member (the
    '__class_resolve__' fix and the 'FALLBACK_*' name handling)."""
    for member in GenericFamilyNum:
      self.assertIs(GenericFamilyNum(member.default), member)

  def test_generic_resolve_rejects_non_family(self) -> None:
    """A non-'FontFamilyNum' identifier raises 'TypeException', not an
    'AttributeError' about a missing '__sans_space__' attribute."""
    with self.assertRaises(TypeException):
      _ = GenericFamilyNum(123)

  def test_generic_resolve_fallback_names(self) -> None:
    """The 'FALLBACK_*' members resolve to their category by name,
    independent of the family value."""
    cases = {'FALLBACK_MONO': GenericFamilyNum.MONO,
             'FALLBACK_SANS': GenericFamilyNum.SANS,
             'FALLBACK_SERIF': GenericFamilyNum.SERIF}
    for name, expected in cases.items():
      stub = SimpleNamespace(name=name, value='whatever')
      self.assertIs(GenericFamilyNum.__class_resolve__(stub), expected)

  def test_generic_resolve_by_value(self) -> None:
    """A family whose value is in a category list resolves to it."""
    pairs = [(FontFamilyMeta.__mono_space__[0], GenericFamilyNum.MONO),
             (FontFamilyMeta.__sans_serif__[0], GenericFamilyNum.SANS),
             (FontFamilyMeta.__serif_families__[0], GenericFamilyNum.SERIF)]
    for value, expected in pairs:
      stub = SimpleNamespace(name='SomeFamily', value=value)
      self.assertIs(GenericFamilyNum.__class_resolve__(stub), expected)

  def test_generic_resolve_unrecognized(self) -> None:
    """A family in no category list raises 'ValueError'."""
    stub = SimpleNamespace(name='SomeFamily', value='NotARealFamilyZzz')
    with self.assertRaises(ValueError):
      GenericFamilyNum.__class_resolve__(stub)

  def test_generic_default_unknown_member_raises(self) -> None:
    """The 'default' getter rejects a value that is none of the three
    generic members (its defensive final branch)."""

    class _Fake:
      MONO = GenericFamilyNum.MONO
      SANS = GenericFamilyNum.SANS
      SERIF = GenericFamilyNum.SERIF

    with self.assertRaises(RuntimeError):
      GenericFamilyNum._getFamily(_Fake())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FAMILY DEFAULTS (metaclass)  # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_family_category_defaults(self) -> None:
    """'defaultSerif'/'defaultSans'/'defaultMono' each resolve to a member
    of the enumeration."""
    for family in (FontFamilyNum.defaultSerif,
                   FontFamilyNum.defaultSans,
                   FontFamilyNum.defaultMono):
      self.assertIsInstance(family, FontFamilyNum)

  def test_family_apply_sets_family(self) -> None:
    """'FontFamilyNum.apply' sets the family on a 'QFont'."""
    family = FontFamilyNum.defaultMono
    font = family.apply(QFont())
    self.assertEqual(font.family(), family.value)

  def test_default_serif_branches(self) -> None:
    """'defaultSerif' prefers a good serif, then a mid serif, then the
    fallback - driven deterministically through a fake enumeration."""
    good = _FakeFamilyNum(FontFamilyMeta.__good_serif__[0])
    self.assertEqual(FontFamilyMeta._getDefaultSerif(good).value,
                     FontFamilyMeta.__good_serif__[0])
    midName = _midOnly(FontFamilyMeta.__serif_families__,
                       FontFamilyMeta.__good_serif__)
    mid = _FakeFamilyNum(midName)
    self.assertEqual(FontFamilyMeta._getDefaultSerif(mid).value, midName)
    none = _FakeFamilyNum('No Such Family')
    self.assertEqual(FontFamilyMeta._getDefaultSerif(none), 'FALLBACK_SERIF')

  def test_default_sans_branches(self) -> None:
    """'defaultSans' prefers a good sans, then a mid sans, then fallback."""
    good = _FakeFamilyNum(FontFamilyMeta.__good_sans__[0])
    self.assertEqual(FontFamilyMeta._getDefaultSans(good).value,
                     FontFamilyMeta.__good_sans__[0])
    midName = _midOnly(FontFamilyMeta.__sans_serif__,
                       FontFamilyMeta.__good_sans__)
    mid = _FakeFamilyNum(midName)
    self.assertEqual(FontFamilyMeta._getDefaultSans(mid).value, midName)
    none = _FakeFamilyNum('No Such Family')
    self.assertEqual(FontFamilyMeta._getDefaultSans(none), 'FALLBACK_SANS')

  def test_default_mono_branches(self) -> None:
    """'defaultMono' prefers a good mono, then a mid mono, then fallback."""
    good = _FakeFamilyNum(FontFamilyMeta.__good_mono__[0])
    self.assertEqual(FontFamilyMeta._getDefaultMono(good).value,
                     FontFamilyMeta.__good_mono__[0])
    midName = _midOnly(FontFamilyMeta.__mono_space__,
                       FontFamilyMeta.__good_mono__)
    mid = _FakeFamilyNum(midName)
    self.assertEqual(FontFamilyMeta._getDefaultMono(mid).value, midName)
    none = _FakeFamilyNum('No Such Family')
    self.assertEqual(FontFamilyMeta._getDefaultMono(none), 'FALLBACK_MONO')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  FONT META RESOLUTION / WFONT PARSE  # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_instancecheck_identity(self) -> None:
    """'FontMeta.__instancecheck__' admits a member by identity (the path
    CPython's 'isinstance' fast-path normally bypasses)."""
    meta = type(FontWeightNum)
    self.assertTrue(meta.__instancecheck__(FontWeightNum, FontWeightNum.BOLD))

  def test_resolve_without_custom_resolver(self) -> None:
    """An enumeration with no '__class_resolve__' resolves by the base
    name lookup ('FontMeta._resolveMember' falls through)."""
    self.assertIs(_NoResolveNum('A'), _NoResolveNum.A)

  def test_name_value_pairs_strips_underscore_dupes(self) -> None:
    """A name whose underscore-stripped form already exists is dropped."""
    pairs = familySpace._nameValuePairs('FOOBAR', 'Foo Bar')
    self.assertEqual([name for name, _ in pairs], ['FOOBAR'])

  def test_wfont_parse_size_skips_non_int(self) -> None:
    """'WFont._parseFontSize' skips a leading non-int and returns the int
    with the rest preserved."""
    self.assertEqual(WFont._parseFontSize('x', 5), (5, ('x',)))
