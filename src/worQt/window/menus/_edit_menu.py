"""EditMenu subclasses AbstractMenu and provides an edit menu for the
application. Common edit operations are included in the menu with typical
shortcuts and icons. This class provides the actions, but does not
implement their functionality, which is left to the window classes. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.attr import AttriBox
from worktoy.static import THIS

from . import AbstractMenu, WAction

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False


class EditMenu(AbstractMenu):
  """EditMenu subclasses AbstractMenu and provides an edit menu for the
  application. Common edit operations are included in the menu with typical
  shortcuts and icons. This class provides the actions, but does not
  implement their functionality, which is left to the window classes. """

  selectAll = AttriBox[WAction]('Select All', THIS)
  copy = AttriBox[WAction]('Copy', THIS)
  cut = AttriBox[WAction]('Cut', THIS)
  paste = AttriBox[WAction]('Paste', THIS)
  undo = AttriBox[WAction]('Undo', THIS)
  redo = AttriBox[WAction]('Redo', THIS)

  def initUi(self, ) -> None:
    """Initialize the UI. """
    self.addAction(self.selectAll)
    self.addAction(self.copy)
    self.addAction(self.cut)
    self.addAction(self.paste)
    self.addSeparator()
    self.addAction(self.undo)
    self.addAction(self.redo)
