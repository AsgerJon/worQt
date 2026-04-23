"""
TestWFont subclasses 'BaseTest' from the 'worktoy' package. It does *not*
require a running QApplication.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont
from icecream import ic
from worktoy.ezdata import EZData
from worktoy.keenum import KeeBox
from worktoy.work_test import BaseTest

from worQt.utils.font_nums import FontFamilyNum, FontFamilyMeta
from worQt.utils import WFont


class NumEntry(EZData):
  name: str = 'familyNum'
  keeNum: str = 'FontFamilyNum'
  getterKey: str = 'family'
  setterKey: str = 'setFamily'
  altNum: tuple[str, ...] = ()


if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias

  NumDict: TypeAlias = dict[str, NumEntry]


class Foo:
  familyNum = KeeBox[FontFamilyNum]('MONTSERRAT')

  @familyNum.onSet
  def _onSetFamilyNum(self, value: FontFamilyNum) -> None:
    ic(value)


class TestWFont(BaseTest):
  """
  TestWFont subclasses 'BaseTest' from the 'worktoy' package. It does *not*
  require a running QApplication.
  """

  sharedEnumerations: NumDict
  normalEnumerations: NumDict

  def setUp(self, ) -> None:
    """
    This method is called before each test method is executed. It can be used
    to set up any necessary state or resources for the tests.
    """
    super().setUp()
    self.sharedEnumerations = dict(
      familyNum=NumEntry(
        'familyNum',
        'FontFamilyNum',
        'family',
        'setFamily',
        FontFamilyMeta.__good_mono__,
        ),
      weightNum=NumEntry(
        'weightNum',
        'FontWeightNum',
        'weight',
        'setWeight',
        ('THIN', 'EXTRA_LIGHT', 'LIGHT', 'NORMAL', 'MEDIUM', 'SEMI_BOLD',),
        ),
      styleNum=NumEntry(
        'styleNum',
        'FontStyleNum',
        'style',
        'setStyle',
        ('NORMAL', 'ITALIC', 'OBLIQUE',),
        ),
      )
    self.normalEnumerations = dict(
      linesNum=NumEntry(
        'linesNum',
        'FontLineFlags',
        ),
      colorNum=NumEntry(
        'colorNum',
        'ColorNum',
        ),
      )

  def test_num_entry(self) -> None:
    """
    This method tests the 'NumEntry' data class.
    """
    numEntry = NumEntry(
      'familyNum',
      'FontFamilyNum',
      'family',
      'setFamily',
      )
    self.assertEqual(numEntry.name, 'familyNum')
    self.assertIs(numEntry.keeNum, 'FontFamilyNum')
    self.assertEqual(numEntry.getterKey, 'family')
    self.assertEqual(numEntry.setterKey, 'setFamily')

  def test_init(self, ) -> None:
    """
    This method tests that the WFont class can instantiate without a
    running QApplication.
    """
    font = WFont()
    self.assertIsInstance(font, WFont)

  def test_shared_num(self) -> None:
    """
    This method tests that the shared enumerations can be set and retrieved
    correctly.
    """

    for name, entry in self.sharedEnumerations.items():
      font = WFont()
      #  Testing the enumeration type
      expectedKeeNumName = entry.keeNum
      desc = getattr(WFont, name)
      actualKeeNum = desc.fieldType
      actualKeeNumName = actualKeeNum.__name__
      self.assertEqual(actualKeeNumName, expectedKeeNumName)
      #  Testing the default value
      expectedDefaultValue = KeeBox._resolveNum(desc, )
      actualDefaultValue = desc.__get__(font, WFont)
      self.assertEqual(actualDefaultValue, expectedDefaultValue)
      #  Testing agreement with QFont value
      getterFunc = getattr(WFont, entry.getterKey)
      actualValue = getterFunc(font)
      expectedValue = actualDefaultValue.value
      self.assertEqual(actualValue, expectedValue)
      #  Testing the setter mechanism
      setterFunc = getattr(WFont, entry.setterKey)
      for alt in entry.altNum:
        #  Retrieves enumeration from name
        try:
          altEnumeration = getattr(actualKeeNum, str.upper(alt))
        except AttributeError:
          continue
        else:
          #  Sets the enumeration at the 'KeeBox' descriptor
          desc.__set__(font, altEnumeration, )
          #  Verifies agreement after setting
          expectedNum = altEnumeration
          actualNum = desc.__get__(font, WFont)
          self.assertIs(actualNum, expectedNum)
          #  Verifies agreement with QFont value
          actualValue = getterFunc(font)
          expectedValue = altEnumeration.value
          self.assertEqual(actualValue, expectedValue)
