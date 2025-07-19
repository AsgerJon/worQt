"""
FileMenu subclasses AbstractMenu providing the common 'File' menu.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import LabelBox

from .. import AbstractMenu
from . import NewAction, OpenAction, SaveAction, ExitAction

from typing import TYPE_CHECKING

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
  new = LabelBox[NewAction](THIS)
  open = LabelBox[OpenAction](THIS)
  save = LabelBox[SaveAction](THIS)
  exit = LabelBox[ExitAction](THIS)

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
    self.addAction(self.new, )
    self.addAction(self.open, )
    self.addAction(self.save, )
    self.addSeparator()
    self.addAction(self.exit, )

  def initLogic(self) -> None:
    self.exit.triggered.connect(self.app.close, )
