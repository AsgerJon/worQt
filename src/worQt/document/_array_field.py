"""
ArrayField is a document field holding an ordered collection of 'Member's -
the document's nodes, its elements, its paragraphs. The members are *owned*
here: adding one makes the document adopt it (assign a stable id and index
it), removing one releases it. The backing collection is a live
'ObservableList', so 'doc.nodes.append(node)' mutates in place and marks the
document dirty.

It subclasses 'BaseObject', so worktoy's descriptor base supplies
'hookSetName', 'getPrivateName' and the '__instance_get__' routing. There is
no '__instance_set__': assigning the field wholesale ('doc.nodes = [...]')
falls through to the inherited 'ReadOnlyError' - members go in through the
list.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

from ._observable_list import ObservableList

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Optional


def _findSubclass(base: type, name: str) -> Optional[type]:
  """The class named 'name' in the subtree rooted at 'base' (base itself or
  any loaded subclass), or None. Lets an array field hold a polymorphic mix
  of member subclasses, tagged by class name in the file."""
  if base.__name__ == name:
    return base
  for sub in base.__subclasses__():
    found = _findSubclass(sub, name)
    if found is not None:
      return found
  return None


class ArrayField(BaseObject):
  """A document field owning an ordered collection of members."""

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
    owner._registerArrayField(name, self)

  def __instance_get__(self, instance: Any, owner: type, **kwargs) -> Any:
    host = self.instance
    pvtName = self.getPrivateName()
    existing = getattr(host, pvtName, None)
    if existing is None:
      existing = ObservableList(
          self.__member_type__, host, self.getFieldName(), True)
      setattr(host, pvtName, existing)
    return existing

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SERIALIZATION  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def encode(self, instance: Any) -> list:
    return [m.encode() for m in self.__get__(instance, type(instance))]

  def buildMember(self, raw: dict) -> Any:
    """First-pass member construction: pick the subclass by its '__type__'
    tag, set its value attributes, and keep the stored id. References are
    left for the document's second pass."""
    base = self.__member_type__
    typeName = raw.get('__type__', base.__name__)
    memberCls = _findSubclass(base, typeName) or base
    member = memberCls()
    for name, field in memberCls._valueFields().items():
      if name in raw:
        field.decode(member, raw[name])
    member.__member_id__ = raw.get('__id__')
    return member
