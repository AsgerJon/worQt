"""
CircuitsApp subclasses 'App' and is the application running electric
circuits.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ....app import App
from ....ezword.gui import EZWordApp
from . import CircuitsWindow


class CircuitsApp(App):
  """
  CircuitsApp subclasses 'App' and is the application running electric
  circuits: its window is a 'CircuitsWindow'. It is dark, in Qt's Fusion
  style with EZWord's dark palette, until worQt has a theme of its own.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = CircuitsWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    App.__init__(self, *args)
    self.setStyle('Fusion')
    self.setPalette(EZWordApp.darkPalette())
