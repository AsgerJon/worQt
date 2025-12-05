"""
Stretched remaps the pixel values linearly to span the full unit range.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from .. import BaseUnary

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type, TypeAlias

  from .. import BaseRaster

  Img: TypeAlias = BaseRaster


class Stretched(BaseUnary):
  """
  Stretched remaps the pixel values linearly to span the full unit range.
  """

  def _apply(self, instance: Img, ) -> Img:
    minVal, maxVal = instance.data.min(), instance.data.max()
    stretchedData = (instance.data - minVal) / (maxVal - minVal)
    out = self.owner()
    setattr(out, '__raster_tensor__', stretchedData)
    return out
