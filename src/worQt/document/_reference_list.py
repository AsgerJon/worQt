"""
ReferenceList is an ordered, change-aware list of references to 'Member's
living in array fields elsewhere - e.g. a FEM element pointing at the nodes
that define it. It serializes as a list of target ids and resolves back on
load. Unlike an 'ArrayField' it does not own its members, so adding to it
neither assigns ids nor indexes anything.

It subclasses 'BaseObject' for worktoy's descriptor machinery and stores its
live 'ObservableList' under the inherited private name.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

from ._observable_list import ObservableList

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self


class ReferenceList(BaseObject):
  """An ordered list of references to members of other array fields."""

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
    owner._registerReferenceList(name, self)

  def __instance_get__(self, instance: Any, owner: type, **kwargs) -> Any:
    host = self.instance
    pvtName = self.getPrivateName()
    existing = getattr(host, pvtName, None)
    if existing is None:
      existing = ObservableList(
          self.__member_type__, host, self.getFieldName(), False)
      setattr(host, pvtName, existing)
    return existing

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any) -> list:
    out = []
    for target in self.__get__(instance, type(instance)):  # through context
      if target.memberId is None:
        raise ValueError('reference target is not in any document')
      out.append(target.memberId)
    return out

  def resolve(self, instance: Any, rawList: Any, index: dict) -> None:
    """Second-pass resolution: rebuild the list of live members from stored
    ids. Ids missing from the index are dropped."""
    referenceList = self.__get__(instance, type(instance))
    referenceList.clear()
    for memberId in (rawList or []):
      target = index.get(memberId)
      if target is not None:
        referenceList.append(target)
