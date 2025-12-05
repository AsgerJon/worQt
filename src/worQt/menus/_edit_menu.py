"""
EditMenu subclasses QMenu to provide the edit menu for the application.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu, QMenuBar
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox

from ..core import WBaseObject
from . import WAction, MenuSeparator

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class EditMenu(QMenu, WBaseObject):
  """
  EditMenu subclasses QMenu to provide the edit menu for the application.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  undoAction = AttriBox[WAction](THIS, 'undo')
  redoAction = AttriBox[WAction](THIS, 'redo')
  selectAllAction = AttriBox[WAction](THIS, 'selectAll')
  cutAction = AttriBox[WAction](THIS, 'cut')
  copyAction = AttriBox[WAction](THIS, 'copy')
  pasteAction = AttriBox[WAction](THIS, 'paste')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, bar: QMenuBar) -> None:
    QMenu.__init__(self, '&Edit', bar)
    self.addAction(self.undoAction)
    self.addAction(self.redoAction)
    self.addSeparator()
    self.addAction(self.cutAction)
    self.addAction(self.copyAction)
    self.addAction(self.pasteAction)
    self.addSeparator()
    self.addAction(self.selectAllAction)
