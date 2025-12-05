"""
EffectProcedure provides a Procedure class for image effects.
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


class EffectProcedure(BaseObject):
  """Procedure class for image effects."""

  @abstractmethod  # noqa
  def apply(self, imageData: Tensor, **kwargs) -> Tensor:
    """
    Subclasses must implement this method to specify the effect. The
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
  def _edgeColor(data: Tensor, k: int, ) -> Tensor:
    """
    Assumes monochrome
    """
    if not k % 2:
      raise ValueError('Kernel size k must be odd.')
    if len(data.shape) == 3:
      data = data.unsqueeze(0)
    K = eye(k * k, dtype=F32).view(-1, 1, k, k)
    p = k // 2
    s = 1
    convolved = conv2d(data, K, stride=s, padding=p, groups=1)
    return convolved

  @staticmethod
  def _edgeFull(data: Tensor, k: int, ) -> Tensor:
    """
    This method collects samples for each pixel in a k by k region
    centered on it.
    """
    if not k % 2:
      raise ValueError('Kernel size k must be odd.')
    if len(data.shape) == 3:
      data = data.unsqueeze(0)
    K = eye(k * k, dtype=F32).view(-1, 1, k, k)
    K = cat([K, K, K], dim=1)
    p = k // 2
    s = 1
    convolved = conv2d(data, K, stride=s, padding=p, groups=1)
    return convolved

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

  @classmethod
  def _partialDerivative(cls, data: Tensor, ) -> tuple[Tensor, Tensor]:
    """
    Computes the partial derivatives of the provided data tensor
    along height and width dimensions using central differences.
    The data tensor is expected to have shape (H, W).
    Returns a tuple (dI/dy, dI/dx).
    """
    x = torch.arange(0, 7, dtype=F32)
    y = torch.arange(0, 7, dtype=F32)
    gridY, gridX = torch.meshgrid(y, x, indexing='ij')
    gridX -= 3
    gridY -= 3
    gridX /= gridX.max()
    gridY /= gridY.max()
    angle = torch.atan2(gridY, gridX)  # -pi to pi
    kx = -torch.sin(angle)
    ky = torch.cos(angle)
    kx /= kx.abs().sum()
    ky /= ky.abs().sum()
    kx = kx.unsqueeze(0).unsqueeze(0)
    ky = ky.unsqueeze(0).unsqueeze(0)
    p = 3
    s = 1
    if len(data.shape) == 2:
      data = data.unsqueeze(0).unsqueeze(0)
    dIdx = conv2d(data, kx, padding=p, groups=1).squeeze()
    dIdy = conv2d(data, ky, padding=p, groups=1).squeeze()
    return dIdy, dIdx
