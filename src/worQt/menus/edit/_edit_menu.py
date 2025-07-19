"""
EditMenu provides the Edit menu for the main window.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worktoy.core.sentinels import THIS
from worktoy.desc import LabelBox

from . import SelectAllAction, CopyAction, PasteAction, CutAction
from .. import AbstractMenu

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Self


class EditMenu(AbstractMenu):
  """
  EditMenu provides a subclass of QMenu for the 'Edit' menu commonly found
  in applications.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  selectAll = LabelBox[SelectAllAction](THIS)
  cut = LabelBox[CutAction](THIS)
  copy = LabelBox[CopyAction](THIS)
  paste = LabelBox[PasteAction](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args, **kwargs) -> None:
    super().__init__(*args, **kwargs)
    self.setTitle('Edit')
    self.setObjectName('menus_edit')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUi(self, ) -> None:
    self.addAction(self.selectAll, )
    self.addSeparator()
    self.addAction(self.cut, )
    self.addAction(self.copy, )
    self.addAction(self.paste, )

  def initLogic(self) -> None:
    pass
