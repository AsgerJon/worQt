"""FileMenu subclasses AbstractMenu and provides a file menu for the
application. Common file operations are included in the menu with typical
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


class FileMenu(AbstractMenu):
  """FileMenu subclasses AbstractMenu and provides a file menu for the
  application. Common file operations are included in the menu with typical
  shortcuts and icons. This class provides the actions, but does not
  implement their functionality, which is left to the window classes. """

  new = AttriBox[WAction]('New', THIS)
  open = AttriBox[WAction]('Open', THIS)
  save = AttriBox[WAction]('Save', THIS)
  saveAs = AttriBox[WAction]('Save As', THIS)
  exit = AttriBox[WAction]('Exit', THIS)

  def initUi(self, ) -> None:
    """Initialize the UI. """
    self.addAction(self.new)
    self.addAction(self.open)
    self.addAction(self.save)
    self.addAction(self.saveAs)
    self.addSeparator()
    self.addAction(self.exit)
