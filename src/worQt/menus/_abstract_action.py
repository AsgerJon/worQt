"""
AbstractAction provides a base class for actions in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from worktoy.waitaminute import TypeException

from ..desQt import App

if TYPE_CHECKING:  # pragma: no cover
  pass


class AbstractAction(QAction):
  """
  AbstractAction provides a base class for actions in the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  app = App()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    Subclasses should begin with the super call to this base initializer.
    It promises to handle the 'parent', if available, and pass it on to
    the 'QAction' base. The 'name'
    """
    parentKeys = ('parent', 'p', 'Parent', 'P')
    for arg in args:
      if isinstance(arg, QMenu):
        QAction.__init__(self, arg)
        break
    else:
      for key in parentKeys:
        if key in kwargs:
          parent = kwargs.get(key)
          if isinstance(parent, QMenu):
            QAction.__init__(self, parent)
            break
          raise TypeException('parent', parent, QMenu)
      else:
        QAction.__init__(self, )
