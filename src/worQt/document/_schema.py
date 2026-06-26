"""
Schema is the shared base for 'Document' and 'Member'. It holds the
per-class registries of fields and attributes (populated by the descriptors
in their '__set_name__') and defines the change-notification contract that
the two subclasses implement differently: a 'Document' marks itself dirty, a
'Member' forwards to its owning document.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from ._change import Change


class Schema(BaseObject):
  """Base for 'Document' and 'Member': field/attribute registries plus the
  'notifyChange' contract. Subclasses 'BaseObject', so every concrete
  document and member inherits the full worktoy toolset - 'overload'
  constructors, 'Field'/'AttriBox' descriptors, the instance/owner context -
  even though this layer itself only leans on the class machinery."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REGISTRIES   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def _ownRegistry(cls, key: str) -> dict:
    """The registry living in *this* class's own '__dict__', created empty
    on first use so subclasses never mutate a base class's registry."""
    if key not in vars(cls):
      setattr(cls, key, {})
    return vars(cls)[key]

  @classmethod
  def _gatherRegistry(cls, key: str) -> dict:
    """The registry merged across the MRO, base-first, so a subclass sees
    inherited fields plus its own."""
    merged = {}
    for klass in reversed(cls.__mro__):
      merged.update(vars(klass).get(key, {}))
    return merged

  #  Registration - called from each descriptor's '__set_name__'.
  @classmethod
  def _registerValueField(cls, name: str, field: Any) -> None:
    cls._ownRegistry('__value_fields__')[name] = field

  @classmethod
  def _registerArrayField(cls, name: str, field: Any) -> None:
    cls._ownRegistry('__array_fields__')[name] = field

  @classmethod
  def _registerReference(cls, name: str, field: Any) -> None:
    cls._ownRegistry('__reference_fields__')[name] = field

  @classmethod
  def _registerReferenceList(cls, name: str, field: Any) -> None:
    cls._ownRegistry('__reference_list_fields__')[name] = field

  #  Gathered views.
  @classmethod
  def _valueFields(cls, ) -> dict:
    return cls._gatherRegistry('__value_fields__')

  @classmethod
  def _arrayFields(cls, ) -> dict:
    return cls._gatherRegistry('__array_fields__')

  @classmethod
  def _references(cls, ) -> dict:
    return cls._gatherRegistry('__reference_fields__')

  @classmethod
  def _referenceLists(cls, ) -> dict:
    return cls._gatherRegistry('__reference_list_fields__')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CHANGE CONTRACT  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def notifyChange(self, change: Change) -> None:
    """Receive a change originating on this object. 'Document' overrides to
    mark itself dirty; 'Member' overrides to forward to its document. The
    base does nothing, so a 'Member' with no document is silently inert."""
