"""
MixinMeta is a metaclass compatible with Shiboken.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from shiboken6 import Shiboken
from worktoy.core.sentinels import METACALL
from worktoy.mcls import BaseMeta

from worQt.mixin import MixinSpace

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias

  Bases: TypeAlias = tuple[type, ...]
  Space: TypeAlias = MixinSpace
  Class: TypeAlias = Type[Any]

_ObjectType = type(Shiboken.Object)


class _Shiboken(_ObjectType, ):
  """
  In between class inserting fix to worktoy jank.
  """

  def __getattr__(self, name: str) -> Any:
    """
    The WType metaclass defined below cannot inherit from BaseMeta,
    but must still return the special sentinel METACALL for certain
    special names as expected by BaseMeta (through inheriting from
    AbstractMetaclass). This metaclass system expects that certain names
    return this special sentinel rather than raising AttributeError. Thus,
    we intercept here after Shiboken.__getattr__. This ensures
    compatibility with AbstractMetaclass.
    """
    if str.startswith(name, '__class') and str.endswith(name, '__'):
      return METACALL
    if hasattr(_ObjectType, '__getattr__'):
      try:
        value = _ObjectType.__getattr__(self, name)
      except AttributeError:
        raise
      else:
        return value
    raise AttributeError(name)


class MixinMeta(_Shiboken, BaseMeta):
  """
  MixinMeta is a metaclass compatible with Shiboken.
  """

  @classmethod
  def __prepare__(mcls, name: str, bases: Bases, **kwargs: Any) -> Space:
    space = MixinSpace(mcls, name, bases, **kwargs)
    return space

  def __new__(mcls, name: str, bases: Bases, space: Space, **kw) -> Class:
    return _ObjectType.__new__(mcls, name, bases, space.compile(), **kw)
