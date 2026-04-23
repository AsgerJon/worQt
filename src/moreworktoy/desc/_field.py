"""
  Field implementation supporting type hinting better.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import Generic, TypeVar, TYPE_CHECKING, cast

from worktoy.core import MetaType  # Original metaclass for Field
from worktoy.desc import Field as __field__

T = TypeVar('T')


class _UnRetard(MetaType):
  @classmethod
  def __prepare__(mcls, name, bases, **kwargs):
    bases = (*(base for base in bases if base is not Generic),)
    return super().__prepare__(name, bases, **kwargs)

  def __new__(mcls, name, bases, namespace, **kwargs):
    bases = (*(base for base in bases if base is not Generic),)
    return super().__new__(mcls, name, bases, namespace, **kwargs)


class Field(__field__, Generic[T], metaclass=_UnRetard):
  """
  Field implementation supporting type hinting better.
  """

  def __get__(self, instance, owner) -> T:
    value = super().__get__(instance, owner)
    return cast(T, value)

  @classmethod
  def __class_getitem__(cls, item: type[T]) -> type[Field[T]]:
    return cls
