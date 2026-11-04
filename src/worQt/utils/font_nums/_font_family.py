"""
FontFamily finds font families among those installed on this system. Which
families exist is only known at run time, and only once a 'QApplication'
does, so code never names a family it has no fallback for: a generic
family ('GenericFamilyNum') always finds one, and a family named by string
is looked up here. Lookups ignore case, spaces, hyphens and underscores, so
'JetBrainsMono' finds 'JetBrains Mono'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont, QFontDatabase, QGuiApplication
from worktoy.mcls import BaseObject
from worktoy.utilities import textFmt

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


class FontFamily(BaseObject):
  """
  FontFamily finds font families among those installed on this system.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def normalize(name: str) -> str:
    """
    The 'normalize' method returns 'name' lower-cased and without spaces,
    hyphens or underscores: the form two spellings of one family share.
    """
    out = str.lower(name)
    for char in ' -_':
      out = str.replace(out, char, '')
    return out

  @staticmethod
  def installed() -> tuple[str, ...]:
    """
    The 'installed' method returns the families installed on this system.
    The font database belongs to the application, so it needs a running
    'QApplication'.
    """
    if QGuiApplication.instance() is None:
      infoSpec = """The installed font families are only known once a
      'QApplication' exists!"""
      raise RuntimeError(textFmt(infoSpec))
    return (*QFontDatabase.families(),)

  @classmethod
  def pick(cls, installed: tuple[str, ...], *names: str) -> Optional[str]:
    """
    The 'pick' method returns the first of 'names' found among
    'installed', spelled the way it is installed, or 'None' when none of
    them is. Taking the installed families as an argument keeps the choice
    testable without an application.
    """
    byKey = {cls.normalize(family): family for family in installed}
    for name in names:
      family = byKey.get(cls.normalize(name), None)
      if family is not None:
        return family
    return None

  @classmethod
  def resolve(cls, name: str) -> str:
    """
    The 'resolve' method returns the installed family 'name' refers to.
    A family that is not installed raises 'LookupError': asking for one by
    name means wanting that one, so there is no silent substitute.
    """
    family = cls.pick(cls.installed(), name)
    if family is not None:
      return family
    infoSpec = """No installed font family matches '%s'!"""
    raise LookupError(textFmt(infoSpec % name))

  @staticmethod
  def hinted(hint: QFont.StyleHint) -> str:
    """
    The 'hinted' method returns the family Qt itself chooses for 'hint'.
    Qt always chooses one, which makes it the last resort of a generic
    family.
    """
    font = QFont()
    font.setStyleHint(hint)
    return font.defaultFamily()
