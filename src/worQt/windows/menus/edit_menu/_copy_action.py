"""
CopyAction subclasses 'AbstractAction' and provides the 'Copy' action in the
'Edit' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  pass


class CopyAction(AbstractAction):
  """
  CopyAction subclasses 'AbstractAction' and provides the 'Copy' action in
  the 'Edit' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'edit-copy'
  __action_title__: str = 'Copy'
  __key_bind__: str = 'Ctrl+C'
