"""
ActionResource provides a descriptor for action resources
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING
from warnings import warn

from worktoy.core import Object
from worktoy.desc import Field
from worktoy.utilities import maybe, textFmt

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any
  from . import ActionMeta


class ActionResource(Object):
  """
  Private class for icon name constants. For example:
  new: 'document-new'
  open: 'document-open'
  """

  __sys_name__ = None

  q = Field()

  @q.GET
  def _getQ(self, **kwargs) -> Any:
    cls = self.getFieldOwner()
    fieldName = self.getFieldName().replace('Action', '')
    return cls.toQ(self, fieldName)

  def __init__(self, *args) -> None:
    for arg in args:
      if isinstance(arg, str):
        self.__sys_name__ = arg.replace('Action', '')
        break

  def __get__(self, instance: Any, owner: Any) -> Any:
    if instance is None:
      return self
    return self.__sys_name__

  def nameParts(self, ) -> list[str]:
    names = []
    name = []
    fieldName = self.getFieldName()
    for char in fieldName:
      if char.isupper() and name:
        names.append(''.join(name))
        name = [char.lower(), ]
      else:
        name.append(char.lower())
    if name:
      names.append(''.join(name))
    return names

  def __set_name__(self, owner: ActionMeta, name: str) -> None:
    name = name.replace('Action', '')
    if all([p in name.lower() for p in ('save', 'as')]):
      name = name.lower().replace(' ', '')
      name = name.lower().replace('_', '')
      name = name.lower().replace('save', '')
      name = name.lower().replace('as', '')
      if not name:
        infoSpec = """The 'Save As' action is deprecated. Replace with 
        requiring a name when creating a new document and with a 'rename' 
        action for existing documents. With those the 'save' action is 
        sufficient. """
        warn(textFmt(infoSpec), DeprecationWarning)
    Object.__set_name__(self, owner, name)
    if hasattr(owner, 'registerResource'):
      owner._registerIconName(name, self.__sys_name__)  # noqa

  def __str__(self, ) -> str:
    return maybe(self.__sys_name__, object.__str__(self, ))

  def __repr__(self, ) -> str:
    infoSpec = """%s = %s(%s)"""
    clsName = type(self).__name__
    fieldName, sysName = self.getFieldName(), self.__sys_name__
    return infoSpec % (fieldName, clsName, repr(sysName))
