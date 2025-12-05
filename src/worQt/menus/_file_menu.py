"""
FileMenu subclasses QMenu to provide the file menu for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QMenu, QMenuBar
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..core import WBaseObject
from . import WAction, MenuSeparator


class FileMenu(QMenu, WBaseObject):
  """
  FileMenu subclasses QMenu to provide the file menu for the application.
  """
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  newAction = AttriBox[WAction](THIS, 'new')
  openAction = AttriBox[WAction](THIS, 'open')
  saveAction = AttriBox[WAction](THIS, 'save')
  exitAction = AttriBox[WAction](THIS, 'exit')

  def __init__(self, bar: QMenuBar) -> None:
    QMenu.__init__(self, '&File', bar)
    self.addAction(self.newAction)
    self.addAction(self.openAction)
    self.addAction(self.saveAction)
    self.addAction(self.exitAction)
    self.addSeparator()
