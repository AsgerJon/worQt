"""ResNum enumerates resources. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import sys
import os
from abc import abstractmethod

from worktoy.mcls import Base
from worktoy.mcls import FunctionType as Func
from worktoy.keenum import NumSpace as NSpace, NUM

from worktoy.keenum import MetaNum
from worktoy.parse import maybe
from worktoy.text import typeMsg, monoSpace, stringList
from worktoy.waitaminute import MissingVariable, ReadOnlyError

from worQt import Shiboken
from worQt.waitaminute import MissingResource

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  from typing import Self, Any, Never


class ResNumEntry(NUM):
  """ResNumEntry is a resource number entry."""

  __owner_enumeration__ = None
  __cached_value__ = None

  def _getOwner(self, ) -> MetaResNum:
    """Get the owner of the resource number entry."""
    if TYPE_CHECKING:
      assert isinstance(self.__owner_enumeration__, MetaResNum)
    return self.__owner_enumeration__

  def _setOwner(self, owner: MetaResNum) -> None:
    """Set the owner of the resource number entry."""
    self.__owner_enumeration__ = owner

  def _createVal(self, ) -> None:
    """Creates and caches the value of the resource number entry."""
    owner = self._getOwner()
    resPath = owner.getResPath()
    createResType = owner.createResType()
    fallbackResType = owner.fallbackResType()
    for item in os.listdir(resPath):
      if item.startswith(self.key):
        resName = os.path.join(resPath, item)
        self.__cached_value__ = createResType(resName, )
        break
    else:
      self.__cached_value__ = fallbackResType()

  def _getVal(self, **kwargs) -> Any:
    """Get the value of the resource number entry."""
    owner = self._getOwner()
    resType = owner.getResType()
    if self.__cached_value__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      self._createVal()
      return self._getVal(_recursion=True)
    if isinstance(self.__cached_value__, resType):
      return self.__cached_value__
    name, obj = '__cached_value__', self.__cached_value__
    raise TypeError(typeMsg(name, obj, resType))

  def _setVal(self, value: Any) -> Never:
    """Set the value of the resource number entry."""
    raise ReadOnlyError(self, type(self).val, value)

  def __set_name__(self, owner: MetaResNum, name: str) -> None:
    """Set the name of the resource number entry."""
    if TYPE_CHECKING:
      assert isinstance(owner, MetaResNum)
    self._setOwner(owner)
    self.key = name


class MetaResNum(MetaNum):
  """Metaclass for ResNum"""

  def __new__(mcls, name: str, bases: Base, space: NSpace, **kwargs) -> type:
    """Create a new class."""
    requiredMethods = stringList("""
      getResPath, getResType, createResType, fallbackResType
    """)
    for name in requiredMethods:
      try:
        func = dict.__getitem__(space, name, )
      except KeyError as keyError:
        raise MissingVariable(name, Func) from keyError
      if not callable(func):
        if not isinstance(func, classmethod):
          raise TypeError(typeMsg(name, func, classmethod))
    memberNums = maybe(space.__member_nums__, [])
    memberObjects = []
    for num in memberNums:
      dict.__setitem__(space, num.key, ResNumEntry())
      memberObjects.append(space[num.key])
    space['__member_objects__'] = memberObjects
    return MetaNum.__new__(mcls, name, bases, space, **kwargs)

  def __init__(cls, name: str, bases: Base, space: NSpace, **kwargs) -> None:
    """The __init__ method is invoked to initialize the class."""
    setattr(cls, '__allow_instantiation__', False)

  def __instancecheck__(cls, instance: Any) -> bool:
    """Check if the instance is an instance of the class."""
    if isinstance(instance, ResNumEntry):
      return True
    return False


class ResNum(metaclass=MetaResNum):
  """ResNum provides the decorator. """

  @classmethod
  @abstractmethod
  def getResPath(cls) -> str:
    """Return the resource path."""

  @classmethod
  @abstractmethod
  def getResType(cls) -> type:
    """Return the resource type."""

  @abstractmethod
  def createResType(self, ) -> Shiboken:
    """Creator function for the resource type from the given file path."""

  @classmethod
  @abstractmethod
  def fallbackResType(cls) -> Shiboken:
    """Creates a fallback object."""

  if TYPE_CHECKING:
    def __init__(self, *args, **kwargs) -> None:
      pass
