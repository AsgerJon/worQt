"""
NewAction subclasses 'AbstractAction' and provides the 'New' action in the
'File' menu in the main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QPixmap, QIcon, QKeySequence
from worktoy.desc import FixBox, Field

from .. import AbstractAction

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Optional


class NewAction(AbstractAction):
  """
  NewAction subclasses 'AbstractAction' and provides the 'New' action in
  the 'File' menu in the main window.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __icon_reference__: str = 'document-new'
  __action_title__: str = 'New'
  __key_bind__: str = 'Ctrl+N'

