"""
ClickDemoApp is the 'App' for the click-button demo: it builds a
'ClickDemoWindow' as its main window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.app import App

from ._click_demo_window import ClickDemoWindow


class ClickDemoApp(App):
  """The demo application; builds a 'ClickDemoWindow'."""

  __window_class__ = ClickDemoWindow
