"""
PaintLinearMap subclasses 'PaintedWidget' and provides graphical
representation of a real to real mapping.
"""
#  AGPL-3.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from . import AbstractPaintOp

if TYPE_CHECKING:  # pragma: no cover
  from typing import TypeAlias, Union, Optional

  MaybeFloat: TypeAlias = Optional[float]
