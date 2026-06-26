"""
The 'new_words' launcher. 'NewWordsApp' fixes the window type for worQt's
'App' context manager; 'main' opens the editor and runs the event loop.

    PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src python -m worQt.new_words
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from worQt.app import App

from ._text_window import TextWindow

if TYPE_CHECKING:  # pragma: no cover
  pass


class NewWordsApp(App):
  """The 'new_words' application: worQt's 'App' with 'TextWindow' as its
  main window. It implements the exit-guard hooks; the window's 'closeEvent'
  (inherited from 'AbstractWindow') consults them automatically."""

  __window_class__ = TextWindow

  def hasUnsavedChanges(self) -> bool:
    """The editor's document drives the guard."""
    return self.window.document.isDirty()

  def saveChanges(self) -> bool:
    """Save through the window; a cancelled rename leaves it dirty, which
    aborts the exit."""
    self.window.saveDocument()
    return not self.window.document.isDirty()


def main() -> int:
  """Open the editor and run until it closes."""
  with NewWordsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode
