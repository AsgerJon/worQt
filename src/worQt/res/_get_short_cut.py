"""
The 'getShortCut' function retrieves a keyboard shortcut from a name.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtGui import QKeySequence


def getShortCut(name: str) -> QKeySequence:
  shortcuts = {
      'new'      : 'Ctrl+N',
      'open'     : 'Ctrl+O',
      'save'     : 'Ctrl+S',
      'close'    : 'Ctrl+W',
      'quit'     : 'Ctrl+Q',
      'undo'     : 'Ctrl+Z',
      'redo'     : 'Ctrl+Y',
      'cut'      : 'Ctrl+X',
      'copy'     : 'Ctrl+C',
      'paste'    : 'Ctrl+V',
      'selectAll': 'Ctrl+A',
      'find'     : 'Ctrl+F',
      'replace'  : 'Ctrl+H',
      'help'     : 'F1',
      'about'    : '',
  }
  if name in shortcuts:
    return QKeySequence(shortcuts[name])
  for key, val in shortcuts.items():
    if name.lower() in key.lower():
      return getShortCut(key)
  return QKeySequence()
