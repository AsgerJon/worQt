"""
'ActionIcons' provides a map from name to icon.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QIcon

from . import ActionResource, ActionBase

if TYPE_CHECKING:  # pragma: no cover
  pass


class ActionIcons(ActionBase):
  """
  ActionIcons provides a map from name to icon.
  """

  new = ActionResource('document-new')
  open = ActionResource('document-open')
  save = ActionResource('document-save')
  saveAs = ActionResource('document-save-as')
  printIcon = ActionResource('document-print')
  cut = ActionResource('edit-cut')
  copy = ActionResource('edit-copy')
  paste = ActionResource('edit-paste')
  undo = ActionResource('edit-undo')
  redo = ActionResource('edit-redo')
  delete = ActionResource('edit-delete')
  refresh = ActionResource('view-refresh')
  help = ActionResource('help-contents')
  about = ActionResource('help-about')
  preferences = ActionResource('preferences-system')
  exit = ActionResource('application-exit')
  run = ActionResource('system-run')
  stop = ActionResource('process-stop')
  play = ActionResource('media-playback-start')
  pause = ActionResource('media-playback-pause')
  forward = ActionResource('media-seek-forward')
  rewind = ActionResource('media-seek-backward')

  @staticmethod
  def toQ(res: ActionResource) -> QIcon:
    if isinstance(res, str):
      res = ActionResource(res.replace('Action', ''))
    return QIcon.fromTheme(res.__sys_name__)
