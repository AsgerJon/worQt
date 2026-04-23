"""
Dimension encapsulates a write-once descriptor representation of a
component in a euclidean object.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import re
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject, BaseMeta
from worktoy.utilities import maybe, textFmt, typeCast
from worktoy.waitaminute import TypeException, MissingVariable
from worktoy.waitaminute.control_flow import SkipSet
from worktoy.waitaminute.desc import ProtectedError, WriteOnceError
from worktoy.waitaminute.dispatch import TypeCastException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias

  from worQt.utils.geom.euclid import EuclideanObject

  EuclideanType: TypeAlias = Type[EuclideanObject]


class Dimension(BaseObject):
  """
  Dimension encapsulates a write-once descriptor representation of a
  component in a euclidean object.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __default_keys__ = (
    'defaultValue',
    'default_value',
    'value',
    'val',
    'default',
    )

  #  Fallback Variables
  __fallback_value__ = 0.0
  __fallback_type__ = int

  #  Private Variables
  __value_type__ = None
  __default_value__ = None
  __field_name__ = None
  __field_owner__ = None
  __key_args__ = None
  __key_group__ = None  # Falls back to __field_name__

  #  Public Variables
  valueType = Field()
  defaultValue = Field()
  fieldName = Field()
  fieldOwner = Field()

  #  Virtual Variables
  pvtName = Field()
  keyGroup = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @valueType.GET
  def _getValueType(self, **kwargs) -> type:
    if self.__value_type__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self.__value_type__ = self.__fallback_type__
      return self._getValueType(_recursion=True)
    if isinstance(self.__value_type__, type):
      return self.__value_type__
    name, value = '__value_type__', self.__value_type__
    raise TypeException(name, value, type)

  @defaultValue.GET
  def _getDefaultValue(self, **kwargs) -> float:
    if self.__default_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      defVal = typeCast(self.valueType, self.__fallback_value__)
      self.__default_value__ = defVal
      return self._getDefaultValue(_recursion=True)
    try:
      value = typeCast(self.valueType, self.__default_value__)
    except TypeCastException as typeCastException:
      name, value = '__default_value__', self.__default_value__
      raise TypeException(name, value, int, float) from typeCastException
    else:
      return value

  @fieldName.GET
  def _getFieldName(self, ) -> str:
    if self.__field_name__ is None:
      raise MissingVariable(self, '__field_name__', str)
    if isinstance(self.__field_name__, str):
      return self.__field_name__
    name, value = '__field_name__', self.__field_name__
    raise TypeException(name, value, str)

  @fieldOwner.GET
  def _getFieldOwner(self, ) -> type:
    if self.__field_owner__ is None:
      raise MissingVariable(self, '__field_owner__', type)
    if isinstance(self.__field_owner__, type):
      return self.__field_owner__
    name, value = '__field_owner__', self.__field_owner__
    raise TypeException(name, value, type)

  @pvtName.GET
  def _getPvtName(self, ) -> str:
    pattern = re.compile(r'(?<!^)(?=[A-Z])')
    fName = '%s' % self.fieldName
    if fName == str.lower(fName):  # Require two words at least
      fName = '%sObject' % fName
    return '__%s__' % pattern.sub('_', fName).lower()

  @keyGroup.GET
  def _getKeyGroup(self, **kwargs) -> tuple[str, ...]:
    return maybe(self.__key_group__, ())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, ) -> None:
    valType, defVal, keys = None, None, []
    for arg in args:
      if isinstance(arg, (float, int)):
        if defVal is None:
          defVal = float(arg)
          continue
        infoSpec = """Received multiple default values: %s and %s"""
        info = infoSpec % (defVal, arg)
        raise ValueError(info)
      if isinstance(arg, str):
        keys.append(arg)
        continue
      if isinstance(arg, type):
        if valType is None:
          valType = arg
          continue
        infoSpec = """Received multiple value types: %s and %s"""
        info = infoSpec % (valType, arg)
        raise ValueError(info)
      raise TypeException('arg', arg, float, int, str)
    self.__value_type__ = maybe(valType, self.__fallback_type__)
    defVal = maybe(defVal, self.__fallback_value__)
    self.__default_value__ = typeCast(self.__value_type__, defVal)
    if keys:  # Cannot fall back because fieldName is not yet set.
      self.__key_group__ = (*keys,)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __get__(self, instance: Any, owner: type, **kwargs) -> Any:
    if instance is None:
      return self
    try:
      value = getattr(instance, self.pvtName)
    except AttributeError as attributeError:
      if kwargs.get('_recursion', False):
        raise attributeError from RecursionError
      setattr(instance, self.pvtName, self.defaultValue)
      return self.__get__(instance, owner, _recursion=True, )
    else:
      if isinstance(value, self.valueType):
        return value
      if kwargs.get('_recursion2', False):
        raise RecursionError
      try:
        casted = typeCast(self.valueType, value)
      except TypeCastException as typeCastException:
        name, val = self.pvtName, value
        raise TypeException(name, val, float, int) from typeCastException
      else:
        setattr(instance, self.pvtName, casted)
        return self.__get__(instance, owner, _recursion2=True, )

  def __set__(self, instance: Any, value: Any, **kwargs) -> None:
    try:
      isFrozen = getattr(instance, 'frozen')
    except AttributeError:
      pass
    else:
      if isFrozen:
        oldValue = getattr(instance, self.pvtName, None)
        raise WriteOnceError(self, oldValue, value)
    try:
      oldValue = getattr(instance, self.pvtName)
      if oldValue == value:
        raise SkipSet
    except (AttributeError, SkipSet):
      pass
    if isinstance(value, self.valueType):
      return setattr(instance, self.pvtName, value)
    if kwargs.get('_recursion', False):
      raise RecursionError
    try:
      casted = typeCast(self.valueType, value)
    except TypeCastException as typeCastException:
      name, val = self.pvtName, value
      raise TypeException(name, val, float, int) from typeCastException
    else:
      return self.__set__(instance, casted, _recursion=True, )

  def __delete__(self, instance: Any, ) -> None:
    try:
      oldValue = getattr(instance, self.pvtName)
    except AttributeError:
      oldValue = None
    raise ProtectedError(instance, self, oldValue)

  def __set_name__(self, owner: EuclideanType, name: str, ) -> None:
    if self.__field_name__ != name:
      infoSpec = """Tried setting field name to '%s', but it is already 
      set to '%s'!"""
      info = infoSpec % (name, self.__field_name__)
      raise RuntimeError(textFmt(info))
    if self.__field_name__ is None:
      infoSpec = """%s objects must have name set by metaclass system 
      before class creation, but found 'None'. Expected name '%s'!"""
      info = infoSpec % (type(self).__name__, name)
      raise RuntimeError(textFmt(info))
    self.__field_owner__ = owner
