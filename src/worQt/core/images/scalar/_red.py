"""
Red extracts the red channel from an image.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor

from . import BaseScalar

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, TypeAlias, Type


class Red(BaseScalar):
  """
  Red extracts the red channel from an image.
  """

  def _apply(self, operand: Tensor) -> Tensor:
    return operand[0, :, :].squeeze()
  