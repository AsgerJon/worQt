"""
PusherApp subclasses 'App' and is the application playing a coin
pusher.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys
import traceback
from typing import TYPE_CHECKING

from PySide6.QtCore import QLoggingCategory

from ....app import App
from ....ezword.gui import EZWordApp
from . import PusherWindow

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent, QObject


class PusherApp(App):
  """
  PusherApp subclasses 'App' and is the application playing a coin
  pusher: its window is a 'PusherWindow'. It is dark, in Qt's Fusion
  style with EZWord's dark palette, until worQt has a theme of its own.
  What a slot raises is printed with its traceback, never swallowed in
  silence. Qt Multimedia's word on which FFmpeg it plays the sounds with
  is not printed; its warnings are.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = PusherWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    App.__init__(self, *args)
    self.setStyle('Fusion')
    self.setPalette(EZWordApp.darkPalette())
    QLoggingCategory.setFilterRules('qt.multimedia.ffmpeg.info=false\n'
                                    'qt.multimedia.ffmpeg.debug=false')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def handleException(self, exc: Exception, receiver: QObject = None,
                      event: QEvent = None) -> bool | None:
    """The 'handleException' method prints what a slot or event handler
    raised, with its traceback, and lets the event be."""
    sys.stderr.write(''.join(traceback.format_exception(exc)))
    return None
