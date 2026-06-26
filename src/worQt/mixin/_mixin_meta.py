"""
MixinMeta is a metaclass compatible with Shiboken.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from shiboken6 import Shiboken
from worktoy.core.sentinels import METACALL
from worktoy.mcls import BaseMeta

from . import MixinSpace

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias

  Bases: TypeAlias = tuple[type, ...]
  Space: TypeAlias = MixinSpace
  Class: TypeAlias = Type[Any]

_ObjectType = type(Shiboken.Object)


class _Shiboken(_ObjectType, ):
  """
  Intermediate metaclass placed between Shiboken's ObjectType and
  BaseMeta in MixinMeta's MRO. Its sole job is to bridge Shiboken's
  attribute lookup to the protocol that worktoy's AbstractMetaclass
  expects.
  """

  def __getattr__(self, name: str) -> Any:
    """
    Bridge Shiboken's attribute lookup to worktoy's AbstractMetaclass
    protocol. AbstractMetaclass (a parent of BaseMeta) expects names
    matching the __class*__ pattern to resolve to the METACALL sentinel
    rather than raise AttributeError. Shiboken does not honour that
    contract, so we intercept here and return METACALL for that
    pattern. Any other name raises AttributeError as normal:
    'ObjectType' defines no '__getattr__' to fall through to.
    """
    if str.startswith(name, '__class') and str.endswith(name, '__'):
      return METACALL
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
