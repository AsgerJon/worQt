"""
DuplicateRegistration is raised when a menu bar or menu registers a second
type under a name it already holds.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.utilities import textFmt


class DuplicateRegistration(Exception):
  """
  DuplicateRegistration is raised when a menu bar registers two menu types
  under the same field name, or a menu registers two action types under the
  same field name. Registration happens by field name while the class body
  executes, so a repeated name is a declaration mistake caught at import.

  Attributes
  ----------
  owner : type
    The menu-bar or menu class the registration was attempted on.
  name : str
    The field name that was registered more than once.
  existing : type
    The type already registered under 'name'.
  duplicate : type
    The type whose registration was rejected.
  """

  __slots__ = ('owner', 'name', 'existing', 'duplicate')

  def __init__(
      self, owner: type, name: str, existing: type, duplicate: type,
  ) -> None:
    self.owner = owner
    self.name = name
    self.existing = existing
    self.duplicate = duplicate
    Exception.__init__(self, )

  def __str__(self) -> str:
    infoSpec = """Class '%s' already registers name '%s' as '%s'; it cannot
    also be registered as '%s'!"""
    ownerName = getattr(self.owner, '__name__', str(self.owner))
    existingName = getattr(self.existing, '__name__', str(self.existing))
    duplicateName = getattr(self.duplicate, '__name__', str(self.duplicate))
    info = infoSpec % (ownerName, self.name, existingName, duplicateName)
    return textFmt(info)

  __repr__ = __str__
