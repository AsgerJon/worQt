"""
UndoAction subclasses 'AbstractAction' and provides the 'Undo' action in the
'Edit' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class UndoAction(AbstractAction):
  """
  UndoAction subclasses 'AbstractAction' and provides the 'Undo' action in
  the 'Edit' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'edit-undo'
  __action_title__: str = 'Undo'
  __key_bind__: str = 'Ctrl+Z'
