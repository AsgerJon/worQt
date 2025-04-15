"""HelpMenu subclasses AbstractMenu and provides a help menu for the
application. Common help operations are included in the menu with typical
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


class HelpMenu(AbstractMenu):
  """HelpMenu subclasses AbstractMenu and provides a help menu for the
  application. Common help operations are included in the menu with typical
  shortcuts and icons. This class provides the actions, but does not
  implement their functionality, which is left to the window classes. """

  aboutPython = AttriBox[WAction]('About Python', THIS)
  aboutWorQt = AttriBox[WAction]('About worQt', THIS)
  aboutQt = AttriBox[WAction]('About Qt', THIS)

  def initUi(self, ) -> None:
    """Initialize the UI. """
    self.addAction(self.aboutPython)
    self.addAction(self.aboutWorQt)
    self.addAction(self.aboutQt)
