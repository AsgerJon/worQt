"""
EditMenu subclasses 'WMenu' and provides the implementation of the 'Edit'
menu in the menu bar of the main application windows in the worQt framework.
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

EDIT_TIP: str = textFmt(
  """Edit menu providing access to editing operations such as undo and 
  redo""",
  )
CUT_TIP: str = textFmt("""Cut the selected content to the clipboard.""", )
COPY_TIP: str = textFmt("""Copy the selected content to the clipboard.""", )
PASTE_TIP: str = textFmt("""Paste the content from the clipboard.""", )
UNDO_TIP: str = textFmt("""Undo the last action.""", )
REDO_TIP: str = textFmt("""Redo the last undone action.""", )
SELECT_ALL_TIP: str = textFmt("""Select all content.""", )
UN_SELECT_TIP: str = textFmt("""Deselect all content.""", )


class EditMenu(WMenu):
  """
  EditMenu subclasses 'WMenu' and provides the implementation of the 'Edit'
  menu in the menu bar of the main application windows in the worQt
  framework.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  undo: ActionBox = AttriBox[WAction](THIS, 'undo', UNDO_TIP)
  redo: ActionBox = AttriBox[WAction](THIS, 'redo', REDO_TIP)
  cut: ActionBox = AttriBox[WAction](THIS, 'cut', CUT_TIP)
  copy: ActionBox = AttriBox[WAction](THIS, 'copy', COPY_TIP)
  paste: ActionBox = AttriBox[WAction](THIS, 'paste', PASTE_TIP)
  selectAll: ActionBox = AttriBox[WAction](THIS, 'selectAll', SELECT_ALL_TIP)
  unSelect: ActionBox = AttriBox[WAction](THIS, 'unSelect', UN_SELECT_TIP)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def addAction(self, *args, ) -> None:
    action, *_ = (*args, None)
    if isinstance(action, WAction):
      WAction.initUI(action, )
      return WMenu.addAction(self, action, )
    return WMenu.addAction(self, *args, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    """
    Initialize the user interface of the menu by adding the actions to the
    menu.
    """
    super().initUI()
    self.setToolTip(EDIT_TIP)
    self.addAction(self.undo)
    self.addAction(self.redo)
    self.addSeparator()
    self.addAction(self.cut)
    self.addAction(self.copy)
    self.addAction(self.paste)
    self.addSeparator()
    self.addAction(self.selectAll)
    self.addAction(self.unSelect)
