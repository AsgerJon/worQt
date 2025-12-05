"""
OperatorProcedure provides a procedure class for image operations. It
requires that subclasses implement the 'apply' method to define the
specific operation on image data. If at all possible, this should happen
in place. Where a new tensor is instead desired, the owning class should
pass a copy of the image data to the operator procedure.


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

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, TypeAlias, Type, Optional, Union
  from . import BaseImage

  Image: TypeAlias = Optional[Union[BaseImage, Self]]
  ImType: TypeAlias = Type[BaseImage]


class OperatorProcedure(BaseObject):
  """Procedure class for image operations."""

  @abstractmethod  # noqa
  def apply(self, imageData: Tensor, **kwargs) -> Tensor:
    """
    Subclasses must implement this method to specify the operation. The
    data format is unit ranged floating points with channels (always three),
    height and width as dimensions.

    :param imageData: torch.Tensor with dtype torch.float32 and shape
      (3,H,W) representing three colors with height H and width W.

    :return: torch.Tensor with dtype torch.float32 and shape (3,H,W)
    """

  def __get__(self, image: Image, imType: ImType) -> Image:
    if image is None:
      return self

    def func(imageData: Tensor, **kwargs) -> Tensor:
      return self.apply(imageData, **kwargs)

    return func

  @staticmethod
  def _localCombined(data: Tensor, k: int) -> Tensor:
    """
    This method collects for each pixel the (3, k, k) local image
    centered on each pixel. The data tensor is expected to have shape
    (3, H, W) or (1, 3, H, W) and the output will have shape:
    (k * k * 3, H, W).
    """
    kernel = eye(k * k * 3, dtype=F32).view(k * k * 3, 3, k, k)
    p = k // 2
    s = 1
    if len(data.shape) == 3:
      data = data.unsqueeze(0)
    return conv2d(data, kernel, stride=s, padding=p).squeeze(0)

  @staticmethod
  def _localChannel(data: Tensor, k: int, c: int) -> Tensor:
    """
    This method collects for each pixel the (1, k, k) local image
    centered on each pixel for the specified channel c. The data tensor is
    expected to have shape (3, H, W) or (1, 3, H, W) and the output will have
    shape: (k * k, H, W).
    """
    kernel = eye(k * k, dtype=F32).view(k * k, 1, k, k)
    p = k // 2
    s = 1
    if len(data.shape) == 3:
      data = data.unsqueeze(0)
    print("""data shape: %s""" % (str(data.shape)))
    print("""data[0] shape: %s""" % (str(data[0].shape)))
    return data

  @staticmethod
  def _distKernel(k: int, ) -> Tensor:
    """
    Constructs a kernel K of size (k, k) with odd k, such that
    K[i, j] = (i - c) ** 2 + (j - c) ** 2 where c = k // 2.
    """
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    center = k // 2
    indices = torch.arange(0, k, dtype=F32)
    gridY, gridX = torch.meshgrid(indices, indices, indexing='ij')
    return ((gridY - center) ** 2 + (gridX - center) ** 2) ** 0.5

  @classmethod
  def _gaussKernel(cls, k: int, sigma: float) -> Tensor:
    """
    Constructs a Gaussian kernel of size (k, k) with odd k and standard
    deviation sigma.
    """
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    distKernel = cls._distKernel(k)
    gaussKernel = torch.exp(-distKernel / (2 * sigma ** 2))
    gaussKernel /= gaussKernel.sum()
    return gaussKernel

  @classmethod
  def _kernelPixel(cls, data: Tensor, kernel: Tensor) -> Tensor:
    """
    Applies each channel in data with the provided kernel. The data
    tensor is expected to have shape (3, H, W) or (1, 3, H, W), the kernel
    tensor is expected to have shape (k, k) with odd k. The output will
    have shape (3, H, W).
    """
    k = kernel.shape[0]
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    p = k // 2
    s = 1
    if len(data.shape) == 3:
      data = data.unsqueeze(0)
    K = stack((*(kernel.unsqueeze(0) for _ in 'lol'),), )
    return conv2d(data, K, padding=p, groups=3).squeeze(0)

  @classmethod
  def _gaussianBlur(cls, data: Tensor, k: int, sigma: float) -> Tensor:
    """
    Applies Gaussian blur to the provided data tensor. The data tensor
    is expected to have shape (3, H, W) or (1, 3, H, W), the kernel
    tensor is expected to have shape (k, k) with odd k. The output will
    have shape (3, H, W).
    """
    kernel = cls._gaussKernel(k, sigma)
    return cls._kernelPixel(data, kernel)
