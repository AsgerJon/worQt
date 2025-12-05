"""
ActionShortcuts provides the action shortcuts used in the worQt framework.
Please note that actions not meant to have default shortcuts are not
registered here. For this reason, instead of raising AttributeError,
a special NULL shortcut is returned for unregistered actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QKeySequence
from worktoy.core import Object
from worktoy.desc import Field

from . import ActionMeta, ActionIcons, ActionBase, ActionResource

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _ShortcutMeta(ActionMeta):
  """
  Metaclass for ActionShortcuts.
  """

  __null_cut__ = None
  NULL_CUT = Field()

  def _createNullCut(cls, ) -> None:
    nullCut = ActionResource('')
    setattr(cls, '__null_cut__', nullCut)
    Object.__set_name__(nullCut, cls, 'NULL_CUT', )

  @NULL_CUT.GET
  def _getNullCut(cls, **kwargs) -> ActionResource:
    if cls.__null_cut__ is None:
      if kwargs.get('_recursion', False):
        raise RecursionError
      cls._createNullCut()
      return cls._getNullCut(_recursion=True)
    return cls.__null_cut__

  def __getattr__(cls, name: str) -> Any:
    try:
      value = ActionMeta.__getattr__(cls, name)
    except AttributeError:
      try:
        _ = getattr(ActionIcons, name)
      except AttributeError:
        return type.__getattribute__(cls, name)
      else:
        return ''
    else:
      return value


class ActionShortcuts(ActionBase, metaclass=_ShortcutMeta):
  """
  ActionShortcuts provides the action shortcuts used in the worQt framework.
  Please note that actions not meant to have default shortcuts are not
  registered here. For this reason, instead of raising AttributeError,
  a special NULL shortcut is returned for unregistered actions.
  """

  new = ActionResource('Ctrl+N')
  open = ActionResource('Ctrl+O')
  save = ActionResource('Ctrl+S')
  saveAs = ActionResource('Ctrl+Shift+S')
  close = ActionResource('Ctrl+W')
  quit = ActionResource('Ctrl+Q')
  undo = ActionResource('Ctrl+Z')
  redo = ActionResource('Ctrl+Y')
  cut = ActionResource('Ctrl+X')
  copy = ActionResource('Ctrl+C')
  paste = ActionResource('Ctrl+V')
  delete = ActionResource('Del')
  selectAll = ActionResource('Ctrl+A')
  find = ActionResource('Ctrl+F')
  replace = ActionResource('Ctrl+R')

  @staticmethod
  def toQ(res: ActionResource) -> QKeySequence:
    if not isinstance(res, ActionResource):
      res = ActionResource(res)
    return QKeySequence(res.__sys_name__)
