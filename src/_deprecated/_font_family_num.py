"""
FontFamilyNum enumerates supported font families.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication
from worktoy.core import Object
from worktoy.desc import Field
from worktoy.keenum import KeeNum, KeeSpace, Kee, KeeMeta
from worktoy.mcls.space_hooks import AbstractSpaceHook

from worQt.mixin import MixinBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Union, Optional

  Bases: TypeAlias = tuple[type, ...]


class _FontApp(QApplication):
  pass


class _FontSpace(KeeSpace):
  """
  _FontSpace is a namespace for font family constants.
  """

  def __init__(self, *args, **kwargs) -> None:
    """Initializes the namespace. This is called after the preCompilePhase
    of the space hook. The default implementation does nothing. """
    KeeSpace.__init__(self, *args, **kwargs)
    app = QApplication.instance()
    try:
      if app is None:
        app = _FontApp([])
      fontDB = QFontDatabase()
      latins = fontDB.families(QFontDatabase.WritingSystem.Latin)
      families = []
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
        'monospace',
        'sans serif',
        'serif',
      ]

      def yeet(family_: str) -> str:
        for bad in badAny:
          if bad.lower() in family_.lower():
            return ''
        for char in badChars:
          if char in family_:
            return ''
        for bad in badEnd:
          if family_.lower().endswith(bad.lower()):
            return ''
        nameParts = str.split(family_, )
        out = []
        while nameParts:
          part = nameParts.pop(0)
          if part.lower() == 'nerd':
            break
          out.append(part)
        name = ' '.join(out)
        for bad in badFull:
          if name.lower() == bad.lower():
            return ''
        if str.endswith(name, 'M'):
          return name[:-1]
        return name

      for family in latins:
        family = yeet(family)
        if not family:
          continue
        if family not in families:
          families.append(family)
      families = sorted(families)

      def upperScore(name: str) -> str:
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

      varNames = []
      nameKees = []
      for family in families:
        varName = upperScore(family)
        if not varName:
          continue
        if varName[0].isdigit():
          continue
        if varName in varNames:
          continue
        if str.replace(varName, '_', '') in varNames:
          continue
        varNames.append(varName)
        kee = Kee[str](family)
        nameKees.append((varName, kee))
      nameKees.sort(key=lambda x: x[0])
      for name, kee in nameKees:
        self[name] = kee
    finally:
      if isinstance(app, _FontApp):
        app.quit()
        del app


class _FontMeta(KeeMeta):
  """
  _FontMeta is the metaclass for the FontFamilyNum class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kw) -> _FontSpace:
    return _FontSpace(mcls, name, bases, **kw)


class FontFamilyNum(KeeNum, metaclass=_FontMeta):
  """
  FontFamilyNum enumerates supported font families.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables

  #  Public Variables
  defaultMonospace = Field()
  defaultSans = Field()
  defaultSerif = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
