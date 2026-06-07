"""
NotifyBox subclasses 'AttriBox' and notifies the owning object whenever its
value is assigned. It is the attribute type required on 'AbstractItem': by
making every item attribute a 'NotifyBox', an item's in-place edits
('point.x = 5') reach the item's 'notifyChange' automatically, so the author
never wires change propagation by hand.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar, Generic

from worktoy.desc import AttriBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

T = TypeVar('T')


class NotifyBox(AttriBox, Generic[T]):
  """
  An 'AttriBox' that fires the owner's 'notifyChange' on every assignment.

  The notification runs in 'hookOnSet', which the descriptor calls once per
  assignment after the value is stored - not during lazy default creation
  and not during the internal coercion recursion. So exactly one
  notification fires per real write.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NOTIFIERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def hookOnSet(self, instance: Any, value: Any, **kwargs) -> None:
    super().hookOnSet(instance, value, **kwargs)
    instance.notifyChange()
