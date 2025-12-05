"""
TestBoxModel tests the BoxModel functionality.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from worQt.core.geometry import BoxModel, Rect, Margins
from . import BoxTest


class SusWidget:
  """
  Imma widget, trust me bro!
  """

  box = BoxModel(
      margin=Margins(5, 5, 5, 5, ),
      border=Margins(2, 2, 2, 2, ),
      padding=Margins(10, 10, 10, 10, ),
  )

  boxMargin = 5
  boxBorder = 2
  boxPadding = 10


class TestBoxModel(BoxTest):
  """
  TestBoxModel tests the BoxModel functionality.
  """
