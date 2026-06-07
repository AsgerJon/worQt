"""
AbstractItem is the required base for objects stored in a 'MultiField'.
Internal mutation of a plain object ('node.x = 5') is invisible to the list
holding it, since Python has no hook for attribute assignment on an object
you do not control. So an item opts in: it declares its state in 'NotifyBox'
attributes (enforced by the metaclass), which fire 'notifyChange' on every
write. The 'MultiFieldList' holding the item points its '__owner__' at
itself, so the change reaches the document. Items are identity-hashable so
the list can track which ones it holds.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject
from . import ItemMeta

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractItem(BaseObject, metaclass=ItemMeta):
  """
  Array items must subclass 'AbstractItem'
  """

  #  Private Variables
  __owning_field__ = None  # the 'ArrayField' holding this item, if any
  __owning_document__ = None  # the document that field belongs to, if any

  def notifyChange(self, ) -> None:
    """Fired by a 'NotifyBox' attribute after every write. When the item is
    held by an array it forwards to the owning field's change hook; an item
    not yet added to any array has no owner, so this is a no-op."""
    field = self.__owning_field__
    document = self.__owning_document__
    if field is not None and document is not None:
      field.notifyChange(document)
