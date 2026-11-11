"""
BilliardsApp subclasses 'App' and is the application showing a
three-cushion table.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING

from ....app import App
from ....ezword.gui import EZWordApp
from . import BilliardsWindow

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent, QObject


class BilliardsApp(App):
  """
  BilliardsApp subclasses 'App' and is the application showing a
  three-cushion table: its window is a 'BilliardsWindow'. It is dark, in
  Qt's Fusion style with EZWord's dark palette, until worQt has a theme
  of its own. What a slot raises is printed with its traceback, never
  swallowed in silence.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = BilliardsWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    App.__init__(self, *args)
    self.setStyle('Fusion')
    self.setPalette(EZWordApp.darkPalette())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def handleException(self, exc: Exception, receiver: QObject = None,
                      event: QEvent = None) -> bool | None:
    """The 'handleException' method prints what a slot or event handler
    raised, with its traceback, and lets the event be."""
    sys.stderr.write(''.join(traceback.format_exception(exc)))
    return None
