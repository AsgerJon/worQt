"""
Set lol
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Callable, TypeAlias, Type, Any, Self, Iterator


class MetaSet(type):
  pass


class RussellException(Exception):
  pass


class Set(metaclass=MetaSet):
  """
  Basic Set implementation
  """

  def __init__(self, func: Callable[[Any], bool]) -> None:
    self._func = func

  def __contains__(self, element: Any) -> bool:
    return True if self._func(element) else False


class LiteralSet(metaclass=MetaSet):
  __member_elements__ = None

  def _getMembers(self, ) -> Iterator[Any]:
    yield from self.__member_elements__

  def __init__(self, *elements: Any) -> None:
    e = ()
    for element in elements:
      if element in e:
        continue
      e = (*e, element)
    self.__member_elements__ = e

  def __contains__(self, element: Any) -> bool:
    return True if element in self.__member_elements__ else False


#  Below we create a class representation of Sets under the axiom of
#  choice. The "Axiom of Choice" is fundamental to a set theory introduced
#  to evade certain paradoxes. It is typically associated with the works of
#  Ernst Zermelo and Abraham Fraenkel, who developed the Zermelo-Fraenkel set


def magicChoice() -> Any:
  """LOL how?"""
  raise NotImplementedError


class ZFSet(Set, LiteralSet):
  """
  Zermelo-Fraenkel Set implementation
  """

  __previous_elements__ = None

  def __iter__(self, ) -> Any:
    self.__previous_elements__ = []
    return self

  def __next__(self, ) -> Any:
    try:
      element = magicChoice()
    except Exception:
      raise StopIteration
    else:
      if element in self.__previous_elements__:
        return self.__next__()
      self.__previous_elements__.append(element)
      return element

  def __contains__(self, element: Any) -> bool:
    try:
      result = Set.__contains__(self, element)
    except Exception:
      pass
    else:
      if result:
        return True
    try:
      result = LiteralSet.__contains__(self, element)
    except Exception:
      pass
    else:
      if result:
        return True
    return False
