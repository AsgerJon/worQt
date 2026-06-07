"""
FontSpace subclasses 'KeeSpace' and provides a dynamic creation of the
font enumeration based on the fonts available in the current system. The
QFontDatabase provides the font families available, but it requires a
QApplication instance. Since the fonts are needed at class creation time,
before the main application will begin, the namespace spools up a
temporary application instance.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFontDatabase, QFont
from PySide6.QtWidgets import QApplication
from shiboken6 import delete
from worktoy.keenum import KeeSpace, Kee

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias


class _FontApp(QApplication):
  pass


def _collectFamilies() -> tuple[str, ...]:
  existing = QApplication.instance()
  app = _FontApp([]) if existing is None else existing
  try:
    fontDB = QFontDatabase()
    latins = fontDB.families(QFontDatabase.WritingSystem.Latin)
    font = QFont()
    font.setStyleHint(QFont.StyleHint.Serif)
    fallbackSerif = font.family()
    font.setStyleHint(QFont.StyleHint.SansSerif)
    fallbackSans = font.family()
    font.setStyleHint(QFont.StyleHint.Monospace)
    fallbackMono = font.family()
    public = (*(f for f in latins if not fontDB.isPrivateFamily(f)),)
    fallbacks = fallbackSerif, fallbackSans, fallbackMono
    return (*public, *fallbacks)  # noqa

  finally:
    if existing is None:  # only delete the temp app we created
      delete(app)


def _filterFamilies(*families) -> tuple[str, ...]:
  badEnd = [
    'NF',
    'NFM',
    'NFP',
    'Black',
    'Light',
    'Medium',
    'Thin',
    'Display',
    'Bold',
  ]
  badChars = '0123456789+[]'
  badAny = [
    'symbol',
  ]
  badFull = [
    'KanjiStrokeOrders',
  ]
  return tuple(
    f for f in families
    if not any(f.endswith(b) for b in badEnd)
    and not any(c in f for c in badChars)
    and not any(b in f.lower() for b in badAny)
    and f not in badFull
  )


def _upperScore(name: str) -> str:
  out = []
  for (i, char) in enumerate(name):
    if not i:
      out.append(char)
      continue
    if char == ' ':
      out.append('_')
      continue
    if char.isupper():
      if name[i - 1] != ' ' and not name[i - 1].isupper() and i != 1:
        out.append('_')
    out.append(char)
  return str.strip(''.join(out).upper(), )


def _nameValuePairs(*families) -> tuple[tuple[str, str], ...]:
  out = []
  varNames = []
  for family in families:
    varName = _upperScore(family)
    if not varName:
      continue
    if varName[0].isdigit():
      continue
    if varName in varNames:
      continue
    if str.replace(varName, '_', '') in varNames:
      continue
    varNames.append(varName)
    out.append((varName, family))
  return (*sorted(out),)


def _fontFamilies() -> tuple[tuple[str, str], ...]:
  families = _collectFamilies()
  fallbacksFamilies = families[-3:]
  fallbackNames = (*('FALLBACK_%s' % f for f in ('SERIF', 'SANS', 'MONO')),)
  families = _filterFamilies(*families)
  fallbacks = (*(zip(fallbackNames, fallbacksFamilies)),)
  return (*_nameValuePairs(*families), *fallbacks)  # noqa


class FontFamilySpace(KeeSpace):
  """
  The FontSpace subclasses 'KeeSpace' and provides a dynamic creation of the
  font enumeration based on the fonts available in the current system. The
  QFontDatabase provides the font families available, but it requires a
  QApplication instance. Since the fonts are needed at class creation time,
  before the main application will begin, the namespace spools up a
  temporary application instance.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    KeeSpace.__init__(self, *args, **kwargs)
    for name, value in _fontFamilies():
      self[name] = Kee[str](value)
