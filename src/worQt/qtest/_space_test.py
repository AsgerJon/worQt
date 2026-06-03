"""
SpaceTest subclasses 'BaseSpace' and provides the namespace class used by
the 'MetaTest' metaclass for the 'AppTest' class.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING
from types import FunctionType
from worktoy.mcls import BaseSpace
from worktoy.waitaminute import TypeException

from . import HookTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, Union, TypeAlias

  Bases: TypeAlias = tuple[type, ...]
  TestDict: TypeAlias = dict[str, Callable]


class DuplicateException(KeyError):
  __slots__ = ('key',)

  def __init__(self, key: str) -> None:
    self.key = key
    KeyError.__init__(self, )

  def __str__(self) -> str:
    infoSpec = """Duplicated key '%s' already defined!"""
    return infoSpec % (self.key,)

  __repr__ = __str__


class SpaceTest(BaseSpace):
  """
  Namespace class used by 'MetaTest' metaclass for 'AppTest' class.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables

  #  Fallback Variables

  #  Private Variables
  __test_methods__: Optional[TestDict] = None

  #  Public Variables
  hookTest: HookTest = HookTest()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def getTestMethods(self) -> TestDict:
    """
    Get the test methods defined in the namespace.

    Returns
    -------
    tuple[FunctionType, ...]
      A tuple of test methods defined in the namespace.
    """
    if self.__test_methods__ is None:
      return dict()
    if isinstance(self.__test_methods__, dict):
      if not self.__test_methods__:
        return dict()
      for key, test in self.__test_methods__.items():
        if isinstance(key, str) and callable(test):
          continue
        break
      else:
        return self.__test_methods__
      if isinstance(key, str):
        raise TypeException('key', key, str)
      raise TypeException('test', test, Callable)
    raise TypeException('__test_methods__', self.__test_methods__, tuple)

  def addTestMethod(self, key: str, method: Callable) -> None:
    """
    Add a test method to the namespace.

    Parameters
    ----------
    key: str
      The name of the test method.
    method: Callable
      The test method to add.
    """
    if not isinstance(key, str):
      raise TypeException('key', key, str)
    if not callable(method):
      raise TypeException('method', method, Callable)
    existing: dict[str, Callable] = self.getTestMethods()
    if key in existing:
      raise DuplicateException(key)
    existing[key] = method
    self.__test_methods__ = existing

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, mcls: type, name: str, bases: Bases, **kwargs) -> None:
    BaseSpace.__init__(self, mcls, name, bases, **kwargs)
