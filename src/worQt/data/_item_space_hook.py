"""
ItemSpaceHook subclasses 'AbstractSpaceHook' from
'worktoy.mcls.space_hooks' and provides a space hook raising on any
presence of 'AttriBox'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from worktoy.desc import AttriBox
from worktoy.mcls.space_hooks import AbstractSpaceHook, SpaceDesc
from worktoy.utilities import textFmt
from . import NotifyBox

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias

  from . import ItemSpace


class ItemSpaceHook(AbstractSpaceHook):
  """
  ItemSpaceHook subclasses 'AbstractSpaceHook' from
  'worktoy.mcls.space_hooks' and provides a space hook raising on any
  presence of 'AttriBox'.
  """

  space: SpaceDesc[ItemSpace]

  def setItemPhase(self, key: str, val: Any, old: Any = None, ) -> bool:
    if isinstance(val, NotifyBox):
      return False
    if isinstance(val, AttriBox):
      infoSpec = """Attempted to set key: '%s' to an 'AttriBox' instance. 
      This is not allowed in class '%s' which requires use of 'NotifyBox' 
      instead!"""
      clsName = self.space.getClassName()
      info = textFmt(infoSpec % (key, clsName))
      raise TypeError(info)
    return False
