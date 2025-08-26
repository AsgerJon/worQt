"""
AbstractSettings provides an abstract baseclass for the settings classes
in the 'worQt' library.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import json
import os
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe
from worktoy.waitaminute import TypeException, attributeErrorFactory
from worktoy.work_io import validateExistingFile

from ..desQt import Etc
from . import SettingsField

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any

  # from . import SettingsField


class AbstractSettings(BaseObject):
  """
  AbstractSettings provides an abstract baseclass for the settings classes
  in the 'worQt' library.

  The settings exposed by a subclass should store data in a JSON file in
  the 'etc' directory. This file should contain session persistent data.
  In contrast, the default settings of the subclass should be hardcoded
  into the class definition.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  etc = Etc()
  __file_name__: str  # Set this name or override '_getFilePath' method
  __settings_fields__ = None

  #  Private Variables
  __data_cache__ = None
  __has_changes__ = None
  __disk_data__ = None

  #  Public Variables
  cache = Field()
  fields = Field()

  #  Virtual Variables
  filePath = Field()
  hasUnsavedChanges = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @filePath.GET  # Abstract method
  def _getFilePath(self, ) -> str:
    """Subclasses should set the desired file name in the class variable
    '__file_name__' or override this method."""
    return os.path.join(self.etc, self.__file_name__)

  @cache.GET
  def _getCache(self, **kwargs) -> dict:
    if self.__data_cache__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.load(_buildCache=True)
      return self._getCache(_recursion=True)
    if isinstance(self.__data_cache__, dict):
      return self.__data_cache__
    raise TypeException('__data_cache__', self.__data_cache__, dict)

  @fields.GET
  def _getFields(self, ) -> list[SettingsField]:
    return maybe(self.__settings_fields__, [])

  @hasUnsavedChanges.GET
  def _getHasUnsavedChanges(self, ) -> bool:
    if self.__data_cache__ is None:
      return False
    if self.__disk_data__ is None:
      return True
    if not isinstance(self.__disk_data__, dict):
      raise TypeException('__disk_data__', self.__disk_data__, dict)
    if not isinstance(self.__data_cache__, dict):
      raise TypeException('__data_cache__', self.__data_cache__, dict)
    for f in self:
      disk = self.__disk_data__[f.name]
      cache = self.__data_cache__[f.name]
      if disk != cache:
        return True
    return False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def registerField(cls, field: SettingsField) -> None:
    existing = maybe(cls.__settings_fields__, [])
    for f in existing:
      if f.name.lower() == field.name.lower():
        raise NotImplementedError("""TODO: Duplicate field!""")
    setattr(cls, '__settings_fields__', [*existing, field])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _readFile(self, ) -> dict:
    f = type('_', (), dict(close=lambda *_: None))()
    try:
      fid = validateExistingFile(self.filePath)
      f = open(fid, 'r', encoding='utf-8')
    except FileNotFoundError:
      return dict()
    else:
      out = json.load(f)
      self.__disk_values__ = out
      return out
    finally:
      f.close()

  def _writeFile(self, data: dict) -> None:
    fid = self.filePath
    f = type('_', (), dict(close=lambda *_: None))()
    try:
      f = open(fid, 'w', encoding='utf-8')
    except Exception as exception:
      raise exception
    else:
      json.dump(data, f, indent=2, ensure_ascii=False)
    finally:
      f.close()

  def save(self, ) -> None:
    if self.hasUnsavedChanges:
      self._writeFile(self.asDict())
      self.load()

  def load(self, **kwargs) -> None:
    """
    Attempts to load the settings from the disk file. If no file exists,
    one is created using the default values of the fields. If the file
    does exist, but with incomplete data, the missing fields are populated
    with the values from default values.
    """
    try:
      data = self._readFile()
    except FileNotFoundError:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._writeFile(self.asDict())
      return self.load(_recursion=True)
    else:
      self.__disk_data__ = data
      self.__data_cache__ = data

  def asDict(self, ) -> dict:
    data = dict()
    for f in self:
      data[f.name] = self.cache.get(f.name, f.defaultValue)
    return data

  @classmethod
  def _resolveName(cls, item: Any) -> str:
    if isinstance(item, cls):
      return item.name
    elif isinstance(item, str):
      return item
    else:
      raise TypeException('item', item, cls, str)

  def _resolveField(self, item: Any) -> SettingsField:
    itemName = self._resolveName(item)
    for f in self:
      if f.name.lower() == itemName.lower():
        return f
    infoSpec = """'%s' has no field named '%s'"""
    clsName = type(self).__name__
    info = infoSpec % (clsName, itemName)
    raise KeyError(info)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator[SettingsField]:
    yield from self.fields

  def __contains__(self, item: Any) -> bool:
    try:
      _ = self._resolveField(item)
    except (KeyError, TypeException):
      return False
    else:
      return True

  def __getitem__(self, item: Any) -> Any:
    f = self._resolveField(item)
    return self.cache.get(f.name, f.defaultValue)

  def __setitem__(self, item: Any, value: Any) -> None:
    f = self._resolveField(item)
    if not isinstance(value, f.valueType):
      raise TypeException('value', value, f.valueType)
    self.cache[f.name] = value

  def __getattr__(self, item: str) -> Any:
    try:
      f = self._resolveField(item)
    except (KeyError, TypeException):
      raise attributeErrorFactory(self, item)
    else:
      return self.cache.get(f.name, f.defaultValue)

  def __setattr__(self, item: str, value: Any) -> None:
    try:
      f = self._resolveField(item)
    except (KeyError, TypeException):
      super().__setattr__(item, value)
    else:
      if not isinstance(value, f.valueType):
        raise TypeException('value', value, f.valueType)
      self.cache[f.name] = value
