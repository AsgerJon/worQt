"""
Reference is a single-valued member attribute that points at a 'Member'
living in some array field elsewhere in the document - the foreign key of
the model. It stores the target object in memory and serializes as the
target's id; on load the document resolves it back (second pass).

Like the other fields it subclasses 'BaseObject', so it gets worktoy's
descriptor machinery ('hookSetName', 'getPrivateName', the
'__instance_get__'/'__instance_set__' routing) instead of reimplementing it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from ._change import Change

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self


class Reference(BaseObject):
  """A pointer attribute from one member to another. None until set."""

  __member_type__ = None

  @classmethod
  def __class_getitem__(cls, memberType: type) -> Self:
    self = cls()
    self.__member_type__ = memberType
    return self

  def __call__(self, ) -> Self:
    return self

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DESCRIPTOR HOOKS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hookSetName(self, owner: type, name: str, **kwargs) -> None:
    owner._registerReference(name, self)

  def __instance_get__(self, instance: Any, owner: type, **kwargs) -> Any:
    return getattr(self.instance, self.getPrivateName(), None)

  def __instance_set__(self, instance: Any, target: Any, **kwargs) -> None:
    if target is not None:
      if not isinstance(target, self.__member_type__):
        raise TypeException(
            self.getFieldName(), target, self.__member_type__)
    host = self.instance
    pvtName = self.getPrivateName()
    old = getattr(host, pvtName, None)
    setattr(host, pvtName, target)
    if target is not old:
      host.notifyChange(
          Change(host, self.getFieldName(), 'set', old, target))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any) -> Any:
    target = self.__get__(instance, type(instance))  # through the context
    if target is None:
      return None
    if target.memberId is None:
      raise ValueError('reference target is not in any document')
    return target.memberId

  def resolve(self, instance: Any, raw: Any, index: dict) -> None:
    """Second-pass resolution: turn a stored id back into the live member
    from the document index. A missing id resolves to None. Writes the slot
    directly - the load path stays quiet rather than firing a change."""
    target = None if raw is None else index.get(raw)
    setattr(instance, self.getPrivateName(), target)
