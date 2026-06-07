"""
SelectAllAction subclasses 'AbstractAction' and provides the 'Select All'
action in the 'Edit' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class SelectAllAction(AbstractAction):
  """
  SelectAllAction subclasses 'AbstractAction' and provides the 'Select All'
  action in the 'Edit' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'edit-select-all'
  __action_title__: str = 'Select All'
  __key_bind__: str = 'Ctrl+A'
