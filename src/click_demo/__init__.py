"""
The 'click_demo' package is a standalone example app exercising the worQt
'ClickButton' click/hold recogniser. It is NOT part of the 'worQt' library
- it lives beside it under 'src' purely as a runnable demonstration.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._demo_button import DemoButton
from ._gesture_light import GestureLight
from ._click_demo_window import ClickDemoWindow
from ._click_demo_app import ClickDemoApp

__all__ = [
  'DemoButton',
  'GestureLight',
  'ClickDemoWindow',
  'ClickDemoApp',
]
