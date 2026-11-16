"""
SpaceApp opens the space window: the creative rocket on Terra's pad, the
solar system as it stands the day it opens.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os

from worQt.app import App

from ._spacewindow import SpaceWindow


class SpaceApp(App):
  """
  SpaceApp opens a 'SpaceWindow'. On a Wayland desktop it runs through
  XWayland ('xcb'), unless a platform is asked for: Wayland lets no
  program move the pointer, so the hidden pointer could not be kept in
  the middle while looking round (as the sandbox's).
  """

  __window_class__ = SpaceWindow

  def __init__(self, *args) -> None:
    if os.environ.get('WAYLAND_DISPLAY') and os.environ.get('DISPLAY'):
      os.environ.setdefault('QT_QPA_PLATFORM', 'xcb')
    App.__init__(self, *args)
