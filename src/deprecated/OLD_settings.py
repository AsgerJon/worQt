"""
Settings exposes the application settings from the 'etc/settings.ini' file
through the descriptor protocol. The 'AbstractApplication' class from the
'worQt.app' package owns a 'Settings' instance, so classes and functions
across the 'worQt' library should access settings through the running
'QCoreApplication'. However, since 'Settings' is not a 'QObject', it does
not require a running application, so where functionality needs access to
the settings, even when no application is running, the 'Settings' class
allow any class to own an instance of it.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe, textFmt
from worktoy.waitaminute import attributeErrorFactory, TypeException

from . import Etc

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator


class _FlexDict(dict):
  """Allows dot access to keys"""

  supportedTypes = (str, int, float, bool, type(None),)

  @classmethod
  def _convert(cls, value: Any) -> Any:
    """Convert value to a type suitable for the dictionary."""
    if isinstance(value, dict):
      return cls(value)
    elif isinstance(value, (list, tuple)):
      return [cls._convert(item) for item in value]
    elif isinstance(value, (set, frozenset)):
      return {cls._convert(item) for item in value}
    elif isinstance(value, cls.supportedTypes):
      return value
    raise TypeException('value', value, *cls.supportedTypes, )

  def __init__(self, *args, **kwargs) -> None:
    dict.__init__(self, )
    for arg in args:
      if isinstance(arg, dict):
        for key, value in arg.items():
          self[key] = self._convert(value)
      else:
        raise TypeException('arg', arg, dict, )
    for key, value in kwargs.items():
      if isinstance(key, str):
        self[key] = self._convert(value)
      else:
        raise TypeException('key', key, str, )

  def __getattr__(self, key: str) -> Any:
    """Allows dot access to keys."""
    attributeError = attributeErrorFactory(self, key, )
    if str.startswith(key, '__') and str.endswith(key, '__'):
      raise attributeError
    for k, v in self.items():
      if key.lower() == k.lower():
        break
    else:
      raise attributeError
    return v

  def __setattr__(self, key: str, value: Any) -> None:
    """Allows dot access to keys."""
    if str.startswith(key, '__') and str.endswith(key, '__'):
      return object.__setattr__(self, key, value)
    self[key] = self._convert(value)

  def __delattr__(self, key: str) -> None:
    """Allows dot access to keys."""
    if str.startswith(key, '__') and str.endswith(key, '__'):
      return object.__delattr__(self, key)
    newData = dict()
    oldData = [(k, v) for k, v in self.items()]
    oldData = [*reversed(oldData), ]
    while oldData:
      k, v = oldData.pop()
      if key.lower() == k.lower():
        for kk, vv in oldData:
          newData[kk] = vv
        break
      newData[k] = v
    else:
      raise attributeErrorFactory(self, key, )
    self.clear()
    for k, v in newData.items():
      self[k] = self._convert(v)

  def keys(self, ) -> Iterator[str]:
    """Returns an iterator over the keys of the dictionary."""
    yield from (key.lower() for key in dict.keys(self))

  def values(self) -> Iterator[Any]:
    """Returns an iterator over the values of the dictionary."""
    yield from dict.values(self)

  def items(self) -> Iterator[tuple[str, Any]]:
    """Returns an iterator over the items of the dictionary."""
    yield from ((key.lower(), value) for key, value in dict.items(self))

  def __getitem__(self, key: str) -> Any:
    """Allows access to keys using the square bracket notation."""
    if isinstance(key, str):
      for k, v in self.items():
        if key.lower() == k.lower():
          return v
    raise KeyError(textFmt(f"Key '{key}' not found in settings."))

  def __setitem__(self, key: str, value: Any) -> None:
    """Allows setting keys using the square bracket notation."""
    if isinstance(key, str):
      self.__setattr__(key, value)
    else:
      raise TypeException('key', key, str, )

  def __delitem__(self, key: str) -> None:
    """Allows deleting keys using the square bracket notation."""
    if isinstance(key, str):
      return self.__delattr__(key)
    raise TypeException('key', key, str, )

  def __iter__(self) -> Iterator[str]:
    """Allows iteration over the dictionary."""
    yield from self.keys()

  def __contains__(self, key: str) -> bool:
    """Allows checking if a key exists in the dictionary."""
    try:
      _ = self[key]
    except KeyError:
      return False
    else:
      return True

  def __len__(self, ) -> int:
    """Returns the number of items in the dictionary."""
    return sum([1 for _ in self])

  def __bool__(self, ) -> bool:
    for _ in self:
      return True
    return False


class Settings(BaseObject):
  """
  Settings exposes the application settings from the 'etc/settings.ini' file
  through the descriptor protocol. The 'AbstractApplication' class from the
  'worQt.app' package owns a 'Settings' instance, so classes and functions
  across the 'worQt' library should access settings through the running
  'QCoreApplication'. However, since 'Settings' is not a 'QObject', it does
  not require a running application, so where functionality needs access to
  the settings, even when no application is running, the 'Settings' class
  allow any class to own an instance of it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  __file_name__ = 'settings.json'

  #  Fallback Variables

  #  Private Variables
  __settings_cache__ = None

  #  Public Variables

  #  Virtual Variables
  filePath = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @filePath.GET
  def _getSettingsPath(self) -> str:
    return os.path.join(self.etc, self.__file_name__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, section: str = None) -> None:
    settingsData = self.loadFile()
    if section is None:
      self.__settings_cache__ = settingsData
    elif isinstance(section, str):
      for key, value in settingsData.items():
        if key.lower() == section.lower():
          self.__settings_cache__ = value
          break
      else:
        infoSpec = """Unable to recognize section '%s' in settings file!"""
        info = infoSpec % section
        raise KeyError(textFmt(info))
    else:
      raise TypeException('section', section, str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def loadFile(self, **kwargs) -> dict:
    f = type('_', (), dict(close=lambda *_: None))()
    try:
      f = open(self.filePath, 'r', encoding='utf-8')
    except FileNotFoundError:
      return _FlexDict()
    else:
      return _FlexDict(json.load(f), )
    finally:
      f.close()

  def saveFile(self, data: dict, **kwargs) -> None:
    f = type('_', (), dict(close=lambda *_: None))()
    try:
      f = open(self.filePath, 'w', encoding='utf-8')
    except Exception as exception:
      raise exception
    else:
      json.dump(data, f, indent=2, ensure_ascii=False)
    finally:
      f.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __getitem__(self, key: str) -> Any:
    return self.__settings_cache__[key]

  def __setitem__(self, key: str, value: Any) -> None:
    self.__settings_cache__[key] = value

  def __delitem__(self, key: str) -> None:
    del self.__settings_cache__[key]

  def __contains__(self, key: str) -> bool:
    return key in self.__settings_cache__

  def __iter__(self) -> Iterator[str]:
    yield from self.__settings_cache__

  def __len__(self) -> int:
    return len(self.__settings_cache__)

  def __bool__(self) -> bool:
    return bool(self.__settings_cache__)

  def __getattr__(self, key: str) -> Any:
    try:
      value = self.__settings_cache__[key]
    except Exception as exception:
      raise attributeErrorFactory(self, key, ) from exception
    else:
      return value

  def __setattr__(self, key: str, value: Any) -> None:
    if key.startswith('__') and key.endswith('__'):
      return object.__setattr__(self, key, value)
    if self.__settings_cache__ is None:
      self.__settings_cache__ = _FlexDict()
    self.__settings_cache__[key] = value

  def __delattr__(self, key: str) -> None:
    if key.startswith('__') and key.endswith('__'):
      return object.__delattr__(self, key)
    try:
      self.__settings_cache__.__delitem__(key)
    except Exception as exception:
      raise attributeErrorFactory(self, key, ) from exception
