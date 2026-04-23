"""
LayoutBox subclasses 'BoxBase' and provides descriptor containment for
layout objects.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.mixin import BoxBase

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class LayoutBox(BoxBase):
  """
  LayoutBox subclasses 'BoxBase' and is intended to provide descriptor
  access to layouts.
  """
  pass
