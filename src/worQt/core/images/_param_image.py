"""
ParamImage subclasses BaseRaster and provides a parameterized image.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import BaseRaster

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Never, Callable, Iterator


class ParamImage(BaseRaster):
  """
  ParamImage subclasses BaseRaster and provides a parameterized image.
  """
