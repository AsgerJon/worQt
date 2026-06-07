"""
OpenAction subclasses 'AbstractAction' and provides the 'Open' action in
the 'File' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional


class OpenAction(AbstractAction):
  """
  OpenAction subclasses 'AbstractAction' and provides the 'Open' action in
  the 'File' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'document-open'
  __action_title__: str = 'Open'
  __key_bind__: str = 'Ctrl+O'
