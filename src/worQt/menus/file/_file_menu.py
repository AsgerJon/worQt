"""
FileMenu subclasses AbstractMenu providing the common 'File' menu.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Signal
from worktoy.core.sentinels import THIS

from .. import AbstractMenu, ActionBox
from . import NewAction, OpenAction, SaveAction, ExitAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class FileMenu(AbstractMenu):
  """
  FileMenu subclasses AbstractMenu providing the common 'File' menu.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  newAction = ActionBox[NewAction](THIS)
  openAction = ActionBox[OpenAction](THIS)
  saveAction = ActionBox[SaveAction](THIS)
  exitAction = ActionBox[ExitAction](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SIGNALS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  exit = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    """
    Initialize the FileMenu with common 'File' actions.
    """
    super().__init__(*args, **kwargs)
    self.setTitle('File')
    self.setObjectName('menus_file')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    self.addAction(self.newAction, )
    self.addAction(self.openAction, )
    self.addAction(self.saveAction, )
    self.addSeparator()
    self.addAction(self.exitAction, )

  def initLogic(self) -> None:
    self.exitAction.triggered.connect(self.exit.emit)
