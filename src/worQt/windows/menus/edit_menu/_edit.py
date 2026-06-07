"""
Edit subclasses 'AbstractMenu' and provides the 'Edit' menu in the main
window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractMenu, ActionBox
from . import UndoAction, RedoAction, CutAction, CopyAction, PasteAction
from . import SelectAllAction, DeleteAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class Edit(AbstractMenu):
  """
  Edit subclasses 'AbstractMenu' and provides the 'Edit' menu in the main
  window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __menu_title__ = 'Edit'

  #  Actions
  undoAction = ActionBox[UndoAction]()
  redoAction = ActionBox[RedoAction]()
  cutAction = ActionBox[CutAction]()
  copyAction = ActionBox[CopyAction]()
  pasteAction = ActionBox[PasteAction]()
  selectAllAction = ActionBox[SelectAllAction]()
  deleteAction = ActionBox[DeleteAction]()
