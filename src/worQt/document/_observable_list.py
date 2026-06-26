"""
ObservableList is the live, mutate-in-place collection backing both
'ArrayField' and 'ReferenceList'. Every mutation notifies the host. When
'owns' is True (an array field) the host adopts each added member and
releases each removed one - assigning ids and indexing them on the document.
When False (a reference list) the list only references members owned by some
array field elsewhere, so no adoption happens.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from worktoy.waitaminute import TypeException

from ._change import Change

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator


class ObservableList(BaseObject):
  """A change-aware list bound to one field on a host object."""

  def __init__(self, elementType, host, fieldName, owns) -> None:
    super().__init__()
    self.__list_element_type__ = elementType
    self.__list_host__ = host
    self.__list_field_name__ = fieldName
    self.__list_owns__ = owns
    self.__list_items__ = []

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  INTERNAL   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _check(self, item: Any) -> Any:
    if isinstance(item, self.__list_element_type__):
      return item
    raise TypeException('item', item, self.__list_element_type__)

  def _adopt(self, member: Any) -> None:
    if self.__list_owns__:
      self.__list_host__._adoptMember(member)

  def _release(self, member: Any) -> None:
    if self.__list_owns__:
      self.__list_host__._releaseMember(member)

  def _changed(self, kind: str, member: Any) -> None:
    host, name = self.__list_host__, self.__list_field_name__
    host.notifyChange(Change(host, name, kind, None, member))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MUTATORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def append(self, member: Any) -> None:
    self._check(member)
    self._adopt(member)
    self.__list_items__.append(member)
    self._changed('add', member)

  def insert(self, index: int, member: Any) -> None:
    self._check(member)
    self._adopt(member)
    self.__list_items__.insert(index, member)
    self._changed('add', member)

  def extend(self, members) -> None:
    for member in members:
      self.append(member)

  def remove(self, member: Any) -> None:
    self.__list_items__.remove(member)
    self._release(member)
    self._changed('remove', member)

  def pop(self, index: int = -1) -> Any:
    member = self.__list_items__.pop(index)
    self._release(member)
    self._changed('remove', member)
    return member

  def clear(self, ) -> None:
    for member in [*self.__list_items__]:
      self.remove(member)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  READ-ONLY VIEWS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __iter__(self, ) -> Iterator:
    return iter(self.__list_items__)

  def __len__(self, ) -> int:
    return len(self.__list_items__)

  def __getitem__(self, index: Any) -> Any:
    return self.__list_items__[index]

  def __contains__(self, member: Any) -> bool:
    return member in self.__list_items__

  def __bool__(self, ) -> bool:
    return True if self.__list_items__ else False

  def __repr__(self, ) -> str:
    return 'ObservableList(%s, %d)' % (
        self.__list_element_type__.__name__, len(self.__list_items__))
