"""
MultiFieldList subclasses 'list' and backs a 'MultiField' value. It reads
and iterates exactly like a list, but every in-place mutation routes back to
the owning field, so changes are observable. A plain list returned from
'__get__' would let a caller 'doc.nodes.append(x)' mutate the document
silently, with no change signal; this closes that hole and gives a single
seam to hook dirty-tracking into later.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterable

  from worQt.data import MultiField


class MultiFieldList(list):
  """
  A list that notifies its owning 'MultiField' on every mutation.

  Reads and iteration behave exactly like 'list'. Item-adding mutators
  type-check against the field's element type, and every mutator calls the
  field's change hook with the bound document document, so in-place edits
  (e.g. 'doc.nodes.append(x)') are not invisible to the document.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, iterable: Iterable, field: MultiField, instance: Any):
    super().__init__(iterable)
    self.__multi_field__ = field
    self.__bound_instance__ = instance
    self.__connected_items__ = set()
    self._reconcile()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CALLBACKS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notifyChange(self, ) -> None:
    """Bubble a change (structural, or from a held item) to the field."""
    self.__multi_field__._notifyChange(self.__bound_instance__)

  def _reconcile(self, ) -> None:
    """Own items now present, release items gone, so each held item reports
    here. Set difference handles append, removal, reorder and duplicates
    uniformly - which is why items must be hashable."""
    current = set(self)
    for item in current - self.__connected_items__:
      item.__owner__ = self
    for item in self.__connected_items__ - current:
      item.__owner__ = None
    self.__connected_items__ = current

  def _afterChange(self, ) -> None:
    self._reconcile()
    self.notifyChange()

  def _checkItem(self, item: Any) -> None:
    raise NotImplementedError

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MUTATORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def append(self, item: Any) -> None:
    self._checkItem(item)
    super().append(item)
    self._afterChange()

  def insert(self, index: int, item: Any) -> None:
    self._checkItem(item)
    super().insert(index, item)
    self._afterChange()

  def extend(self, items: Iterable) -> None:
    items = [*items]
    for item in items:
      self._checkItem(item)
    super().extend(items)
    self._afterChange()

  def remove(self, item: Any) -> None:
    super().remove(item)
    self._afterChange()

  def pop(self, index: int = -1) -> Any:
    item = super().pop(index)
    self._afterChange()
    return item

  def clear(self, ) -> None:
    super().clear()
    self._afterChange()

  def sort(self, *args, **kwargs) -> None:
    super().sort(*args, **kwargs)
    self._afterChange()

  def reverse(self, ) -> None:
    super().reverse()
    self._afterChange()

  def __setitem__(self, index: Any, value: Any) -> None:
    if isinstance(index, slice):
      value = [*value]
      for item in value:
        self._checkItem(item)
    else:
      self._checkItem(value)
    super().__setitem__(index, value)
    self._afterChange()

  def __delitem__(self, index: Any) -> None:
    super().__delitem__(index)
    self._afterChange()

  def __iadd__(self, other: Iterable) -> MultiFieldList:
    other = [*other]
    for item in other:
      self._checkItem(item)
    super().__iadd__(other)
    self._afterChange()
    return self

  def __imul__(self, count: int) -> MultiFieldList:
    super().__imul__(count)
    self._afterChange()
    return self
