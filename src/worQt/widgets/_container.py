"""
Container is a plain 'BaseWidget' used purely to host a nested layout. It
exists as a dedicated subclass so that 'AttriBox[Container](THIS)' on a
'BaseWidget'-derived owner builds a real child widget rather than aliasing
the owner itself: 'AttriBox[T](THIS)' returns the owner when the owner is
already a 'T', so a host must be boxed as a type the owner does not inherit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._base_widget import BaseWidget

if TYPE_CHECKING:  # pragma: no cover
  pass


class Container(BaseWidget):
  """A plain widget that hosts a nested layout as a real child."""
