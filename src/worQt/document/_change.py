"""
Change is the payload carried by the document change channel. Every
mutation - a value set, a member added to or removed from an array field -
produces one and hands it to the owning document, which bumps its revision
and forwards it to subscribers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Change(BaseObject):
  """A single change to a document.

  Attributes
  ----------
  host : Any
      The 'Document' or 'Member' the change happened on.
  name : str
      The field/attribute name that changed.
  kind : str
      One of 'set' (a value/reference assignment), 'add' or 'remove' (an
      array-field membership change).
  old, new : Any
      The previous and current value for a 'set'; for 'add'/'remove' the
      affected member arrives in 'new'.
  """

  def __init__(self, host, name, kind, old=None, new=None) -> None:
    super().__init__()
    self.host = host
    self.name = name
    self.kind = kind
    self.old = old
    self.new = new

  def __repr__(self, ) -> str:
    return 'Change(%s.%s, %s)' % (
        type(self.host).__name__, self.name, self.kind)
