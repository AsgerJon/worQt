"""
File subclasses 'AbstractMenu' and provides the 'File' menu in the main
window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractMenu, ActionBox
from . import NewAction, OpenAction, SaveAction, RenameAction, ExitAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class File(AbstractMenu):
  """
  File subclasses 'AbstractMenu' and provides the 'File' menu in the main
  window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Actions
  newAction = ActionBox[NewAction]()
  openAction = ActionBox[OpenAction]()
  saveAction = ActionBox[SaveAction]()
  renameAction = ActionBox[RenameAction]()
  exitAction = ActionBox[ExitAction]()
