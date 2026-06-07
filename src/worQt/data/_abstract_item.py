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

from worktoy.mcls import BaseObject, BaseMeta
from worktoy.desc import AttriBox
from worktoy.waitaminute import TypeException

from . import NotifyBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional


class AbstractItem(BaseObject):
  """
  Array items must subclass 'AbstractItem'
  """
