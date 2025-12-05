"""
The 'getIcon' function retrieves an icon from a name.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QIcon


def getIcon(name: str) -> QIcon:
  icons = {
      'new'      : 'document-new',
      'open'     : 'document-open',
      'save'     : 'document-save',
      'close'    : 'window-close',
      'quit'     : 'application-exit',
      'undo'     : 'edit-undo',
      'redo'     : 'edit-redo',
      'cut'      : 'edit-cut',
      'copy'     : 'edit-copy',
      'paste'    : 'edit-paste',
      'selectAll': 'edit-select-all',
      'find'     : 'edit-find',
      'replace'  : 'edit-find-replace',
      'help'     : 'help-contents',
      'about'    : 'help-about',
  }
  if name in icons:
    return QIcon.fromTheme(icons[name])
  for key, val in icons.items():
    if name.lower() in key.lower():
      return getIcon(key)
  return QIcon()
