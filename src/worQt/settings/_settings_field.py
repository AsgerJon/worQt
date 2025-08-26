"""
SettingsField encapsulates a field in a settings class.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Self

  from . import AbstractSettings as Settings

  SettingsType: TypeAlias = Type[Settings]


class SettingsField:
  """
  SettingsField encapsulates a field in a settings class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __field_name__ = None
  __settings_class__ = None
  __value_type__ = None
  __default_value__ = None

  #  Public Variables
  name = Field()
  settingsClass = Field()
  valueType = Field()
  defaultValue = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @name.GET
  def _getName(self) -> str:
    return self.__field_name__

  @settingsClass.GET
  def _getSettingsClass(self) -> type:
    return self.__settings_class__

  @valueType.GET
  def _getValueType(self) -> type:
    return self.__value_type__

  @defaultValue.GET
  def _getDefaultValue(self) -> Any:
    return self.__default_value__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __set_name__(self, owner: SettingsType, name: str) -> None:
    self.__settings_class__ = owner
    self.__field_name__ = name
    owner.registerField(self)

  @classmethod
  def __class_getitem__(cls, valueType: type) -> Self:
    if not isinstance(valueType, type):
      raise TypeException('valueType', valueType, type)
    self = cls.__new__(cls)
    self.__value_type__ = valueType
    return self

  def __call__(self, defVal: Any) -> Self:
    self.__init__(defVal)
    return self

  def __str__(self, ) -> str:
    infoSpec = """%s.%s: %s = %s"""
    clsName = self.__settings_class__.__name__
    fName = self.__field_name__
    valName = self.__value_type__.__name__
    defVal = self.__default_value__
    info = infoSpec % (clsName, fName, valName, defVal)
    return textFmt(info)

  def __repr__(self, ) -> str:
    return self.__str__()

  def __get__(self, instance: Settings, owner: SettingsType) -> Any:
    if instance is None:
      return self
    return instance.cache.get(self.name, self.defaultValue)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, defVal: Any) -> None:
    if self.__value_type__ is None:
      self.__value_type__ = type(defVal)
    if not isinstance(defVal, self.__value_type__):
      raise TypeException('defVal', defVal, self.__value_type__)
    self.__default_value__ = defVal
