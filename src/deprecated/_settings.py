"""
The 'Settings' class exposes the contents of the 'etc/settings.ini' file.
It uses the built-in 'configparser' module to read the file. The
information read from the file is then available through the descriptor
protocol.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os
import configparser
import json
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import typeCast, textFmt
from worktoy.waitaminute import attributeErrorFactory

from worQt.desQt import Etc, App

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Iterator

  Data: TypeAlias = dict[str, str]


class Settings:
  """
  The 'Settings' class exposes the contents of the 'etc/settings.ini' file.
  It uses the built-in 'configparser' module to read the file. The
  information read from the file is then available through the descriptor
  protocol.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  app = App()
  __file_name__ = 'settings.ini'
  __types_name__ = 'settings.types'

  #  Fallback Variables

  #  Private Variables
  __section_name__ = None

  #  Public Variables
  name = Field()

  #  Virtual Variables

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @name.GET
  def _getName(self, ) -> str:
    return self.__section_name__

  def _getSettingsName(self, **kwargs) -> str:
    return os.path.join(self.etc, self.__file_name__)

  def _getTypesName(self, **kwargs) -> str:
    return os.path.join(self.etc, self.__types_name__)

  def _getParser(self, **kwargs) -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    filePath = self._getSettingsName()
    parser.read(filePath, encoding='utf-8')
    return parser

  def _getRaw(self) -> Data:
    """
    Returns the raw data from the settings file. Keys are 'as-is' and
    values are all 'str' objects.
    """
    for section in self._getParser():
      for part in self.name.lower().split():
        if part not in section.lower():
          break
      else:
        return {k: v for (k, v) in self._getParser().items(section)}
    raise KeyError(self.name)

  def _getData(self, **kwargs) -> Data:
    """
    Returns the data with keys in camelCase and values still 'str'.
    """
    rawData = self._getRaw()
    out = dict()
    for key, value in rawData.items():
      camelKey = self._camelCase(key)
      if camelKey in out:
        infoSpec = """Found duplicate key '%s' in section '%s' of settings 
        file '%s'."""
        info = infoSpec % (camelKey, self.name, self._getSettingsName())
        raise KeyError(textFmt(info))
      out[camelKey] = value
    return out

  def _getSettingsTypes(self, ) -> dict[str, type]:
    """Get the types of the settings."""
    f = type('_', (), dict(close=lambda *_: None))()
    out = dict()
    fid = self._getTypesName()
    try:
      f = open(fid, 'r', encoding='utf-8')
    except Exception as exception:
      raise exception
    else:
      for sectionName, sectionData in json.load(f).items():
        for part in self.name.lower().split():
          if part not in sectionName.lower():
            break
        else:
          for key, value in sectionData.items():
            camelKey = self._camelCase(key)
            if camelKey in out:
              infoSpec = """Found duplicate key '%s' in section '%s' of 
              settings types file '%s'."""
              info = infoSpec % (camelKey, sectionName, fid)
              raise KeyError(textFmt(info))
            out[camelKey] = self._resolveType(value)
      return out
    finally:
      try:
        f.close()
      except AttributeError:  # An exception must have occurred
        pass  # Allows the original exception to propagate

  def _getCasted(self, **kwargs) -> dict[str, Any]:
    """
    Returns the data with keys in camelCase and values cast to the
    indicated types in the 'settings.types' file.
    """
    camelData = self._getData()
    settingTypes = self._getSettingsTypes()
    out = dict()
    for key, value in camelData.items():
      if key not in settingTypes:
        infoSpec = """Key '%s' not found in settings types file '%s'!"""
        info = infoSpec % (key, self._getTypesName())
        raise KeyError(textFmt(info))
      out[key] = typeCast(settingTypes[key], value)
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __getitem__(self, identifier: str) -> Any:
    return self._getCasted()[identifier]

  def __getattr__(self, identifier: str) -> Any:
    try:
      value = self[identifier]
    except KeyError:
      raise attributeErrorFactory(self, identifier)
    else:
      return value

  def __iter__(self, ) -> Iterator[str]:
    yield from self._getCasted().keys()

  def __get__(self, instance: Any, owner: type) -> Any:
    return self

  def __str__(self, ) -> str:
    return """<Settings object: '%s'>""" % self.name

  __repr__ = __str__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, sectionName: str) -> None:
    if sectionName not in self._getParser():
      infoSpec = """Unable to recognize section '%s' in settings file 
      '%s'. Expected one of: <br><tab> %s"""
      name = sectionName
      file = self._getSettingsName()
      sections = '<br><tab>'.join(self._getParser().sections())
      info = infoSpec % (name, file, sections)
      raise KeyError(info)
    self.__section_name__ = sectionName

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def get(self, identifier: str, defVal: Any = None) -> Any:
    try:
      value = self[identifier]
    except KeyError:
      return defVal
    else:
      return value

  def items(self, ) -> Iterator[tuple[str, Any]]:
    for key, value in self._getCasted().items():
      yield key, value

  def keys(self, ) -> Iterator[str]:
    for key in self._getCasted().keys():
      yield key

  def values(self, ) -> Iterator[Any]:
    for value in self._getCasted().values():
      yield value

  @staticmethod
  def _resolveType(typeName: str, ) -> type:
    """
    Resolves the 'typeName' to one of: 'int', 'float', 'str', 'bool'.
    """
    return dict(int=int, float=float, str=str, bool=bool)[typeName.lower()]

  @staticmethod
  def _camelCase(text: str, ) -> str:
    if not text:
      return ''
    if ' ' not in text:
      return text
    parts = text.strip().split()
    return parts[0].lower() + ''.join(p.title() for p in parts[1:])
