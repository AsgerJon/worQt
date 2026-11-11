"""
MesoApp subclasses 'App' and is the application testing concrete
cylinders.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ....app import App
from ....ezword.gui import EZWordApp
from . import MesoWindow


class MesoApp(App):
  """
  MesoApp subclasses 'App' and is the application testing concrete
  cylinders: its window is a 'MesoWindow'. It is dark, in Qt's Fusion
  style with EZWord's dark palette, until worQt has a theme of its own.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __window_class__ = MesoWindow

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, *args) -> None:
    App.__init__(self, *args)
    self.setStyle('Fusion')
    self.setPalette(EZWordApp.darkPalette())
