"""
EdgeDetection subclasses EffectProcedure providing an edge detection effect.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from abc import abstractmethod

import torch
from torch import Tensor, zeros, std, gradient, cat, stack, atan2, roll
from torch import zeros_like, eye
from torch import float32 as F32
from torch.nn.functional import conv2d, max_pool2d, pad
from torch.nn import Conv2d

from worktoy.mcls import BaseObject

from . import EffectProcedure

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, TypeAlias, Type, Optional, Union
  from . import BaseImage

  Image: TypeAlias = Optional[Union[BaseImage, Self]]
  ImType: TypeAlias = Type[BaseImage]


class EdgeDetection(EffectProcedure):
  """
  EdgeDetection subclasses EffectProcedure providing an edge detection
  effect.
  """

  def apply(self, imageData: Tensor, **kwargs) -> Tensor:
    """
    Subclasses must implement this method to specify the effect. The
    data format is unit ranged floating points with channels (always three),
    height and width as dimensions.

    :param imageData: torch.Tensor with dtype torch.float32 and shape
      (3,H,W) representing three colors with height H and width W.

    :return: torch.Tensor with dtype torch.float32 and shape (3,H,W)
    """
    blurred = self._gaussianBlur(imageData, k=11, sigma=.5)
    redBlur = blurred[0].unsqueeze(0)
    greenBlur = blurred[1].unsqueeze(0)
    blueBlur = blurred[2].unsqueeze(0)
    redEdge = self._edgeColor(redBlur, k=3).squeeze()
    greenEdge = self._edgeColor(greenBlur, k=3).squeeze()
    blueEdge = self._edgeColor(blueBlur, k=3).squeeze()
    redStd = redEdge.std(dim=0, unbiased=False)
    greenStd = greenEdge.std(dim=0, unbiased=False)
    blueStd = blueEdge.std(dim=0, unbiased=False)
    red = greenStd + blueStd
    green = redStd + blueStd
    blue = redStd + greenStd
    rgb = stack((red, green, blue), dim=0)
    rgb -= rgb.min()
    rgb /= rgb.max()
    return rgb
