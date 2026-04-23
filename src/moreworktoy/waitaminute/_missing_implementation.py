"""
MissingImplementation is a custom exception raised to indicate an attempt
to use method defined on a base class but which is available only on
subclasses that specifically implement it. This is different from an
abstract method in that the class owning the method may very well be
instantiable and used, but that the method defines a specific edge
requiring implementation on a subclass.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.waitaminute import TypeException
from types import FunctionType as Func

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type, Union, Optional, Callable

  MaybeStr: TypeAlias = Optional[str]


class MissingImplementation(TypeError, NotImplementedError):
  """
  MissingImplementation is a custom exception raised to indicate an attempt
  to use method defined on a base class but which is available only on
  subclasses that specifically implement it. This is different from an
  abstract method in that the class owning the method may very well be
  instantiable and used, but that the method defines a specific edge
  requiring implementation on a subclass.
  """

  __slots__ = ('cls', 'func',)

  def __init__(self, cls: Any, func: Any, ) -> None:
    if type(cls) is not type:
      self.cls = cls
    elif isinstance(cls, type):
      self.cls = cls
    else:
      self.cls = type(cls)
    if isinstance(func, str):
      self.func = func
    else:
      try:
        name = func.__name__
      except AttributeError as attributeError:
        raise TypeException('func', func, Func) from attributeError
      else:
        self.func = name

  def __str__(self, ) -> str:
    infoSpec = """Method '%s' on class '%s' requires implementation on a 
    subclass, but was called on '%s'!"""
    clsName = self.cls.__name__
    return infoSpec % (self.func, clsName, clsName)

  __repr__ = __str__
