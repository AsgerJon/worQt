"""
FileMenu subclasses 'WMenu' and provides the implementation of the 'File'
menu used by the main application windows in the worQt framework.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu, QMenuBar
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.utilities import textFmt

from . import WMenu, WAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Type, TypeAlias, Optional, Union

  ActionBox: TypeAlias = Union[WAction, AttriBox]

FILE_TIP: str = textFmt(
  """File menu providing access to file operations such as opening and 
  saving""",
  )
NEW_TIP: str = textFmt("""Create a new project.""", )
OPEN_TIP: str = textFmt("""Open an existing project.""")
SAVE_TIP: str = textFmt("""Save the current project.""", )
EXIT_TIP: str = textFmt("""Exit the application.""", )


class FileMenu(WMenu):
  """
  FileMenu subclasses 'WMenu' and provides the implementation of the 'File'
  menu used by the main application windows in the worQt framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  newAction: ActionBox = AttriBox[WAction](THIS, 'create', NEW_TIP)
  open: ActionBox = AttriBox[WAction](THIS, 'load', OPEN_TIP)
  save: ActionBox = AttriBox[WAction](THIS, 'save', SAVE_TIP)
  quit: ActionBox = AttriBox[WAction](THIS, 'close', EXIT_TIP)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initialize the user interface of the menu by adding the actions to the
    menu.
    """
    super().initUI()
    self.addAction(self.newAction)
    self.addAction(self.open)
    self.addAction(self.save)
    self.addSeparator()
    self.addAction(self.quit)
