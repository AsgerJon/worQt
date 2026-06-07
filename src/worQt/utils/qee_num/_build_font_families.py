"""
The 'buildFontFamilies' function builds a list of font family names
available in the system. It uses the 'QFontDatabase' class, thus requiring
the 'QApplication' instance to be already running. When it runs, it stores
the font families in the '/etc/resources/families.txt' (relative to
project root) file.

Since this function requires the running app, certain classes must finish
their creation without having access to this function. If this is called
without the running app, and the file at '/etc/resources/families.txt' is
empty or missing, this function will populate it with 'consolas'. This
will allow the application to always start. In this case, this function
also schedules itself to run on startup of the application. Thus,
a restart of the application may be required to have access to all font
families.
}
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
from typing import TYPE_CHECKING

import os

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication

from ...mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator


def _familiesPath() -> str:
  """
  This method returns the absolute path to the '/etc/resources/families.txt'
  file, which is used to store the font families data. The path is
  constructed
  using the 'etc' attribute of the 'MixinBase' class, and is relative to the
  project root.
  """
  etcPath = os.path.abspath(MixinBase().etc)
  return os.path.join(etcPath, 'resources', 'families.txt')


def _fallbackFamilies() -> tuple[str, ...]:
  """
  This method returns the fallback font families data, which is used when
  the '/etc/resources/families.json' file is missing or empty. The fallback
  data contains 'consolas' as the only font family, and a hash value of 0.
  """
  return ('consolas',)


def _loadFontFamilies(**kwargs) -> tuple[str, ...]:
  """
  This method loads the font families available in the system from the
  '/etc/resources/families.json' file. If the file is missing or empty,
  it will populate it with fallback data containing 'consolas' as the only
  font family, and return that. This allows the application to always start,
  even without a running 'QApplication' instance.
  """
  f = None
  try:
    f = open(_familiesPath(), 'r')
  except FileNotFoundError:
    if kwargs.get('strict', False):
      raise
    return _fallbackFamilies()
  else:
    data = f.read()
    if data:
      families = str.split(data, os.linesep)
      return (*sorted([f for f in families if f]),)
    return _fallbackFamilies()
  finally:
    try:
      f.close()
    except AttributeError:
      pass


def _fromQFontDatabase() -> tuple[str, ...]:
  """
  This method collects the font families available in the system using the
  'QFontDatabase' class, and returns them as a tuple of strings.
  """
  fontDB = QFontDatabase()
  families = fontDB.families(QFontDatabase.WritingSystem.Latin)
  out = []
  for family in families:
    if fontDB.isPrivateFamily(family):
      continue
    out.append(family)
  return (*sorted(out),)


def _saveFontFamilies(*families: str, ) -> None:
  """
  This method saves the given font families to the
  '/etc/resources/families.txt' file, one family per line.
  """
  f = None
  try:
    f = open(_familiesPath(), 'w')
  except Exception as exception:
    raise exception
  else:
    for family in families:
      f.write("""%s%s""" % (family, os.linesep))
  finally:
    try:
      f.close()
    except AttributeError:
      pass


def getFontFamilies(preLoad: tuple[str, ...] = None) -> tuple[str, ...]:
  """
  This method returns the font families available in the system. Please
  note, that this method requires a running 'QApplication' instance,
  and will return 'None' if called before the application is running.
  """

  if not QApplication.instance():
    return _loadFontFamilies()
  try:
    cached = _loadFontFamilies(strict=True)
  except FileNotFoundError:
    cached = None
  if preLoad is None:
    fromQFont = _fromQFontDatabase()
    if cached != fromQFont:
      _saveFontFamilies(*fromQFont)
    return getFontFamilies(fromQFont)
  if cached == preLoad:
    return cached
  raise ValueError("""Inconsistent font families detected!""")
