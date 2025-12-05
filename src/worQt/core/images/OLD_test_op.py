"""
TestOp subclasses OperatorProcedure and provides a test operation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from torch import Tensor, zeros, std, gradient, cat, stack, atan2, roll
from torch import zeros_like, eye
from torch import float32 as F32
from torch.nn.functional import conv2d, max_pool2d, pad
from torch.nn import Conv2d

from . import OperatorProcedure


class TestOp(OperatorProcedure):
  """Test operation for image processing."""

  @staticmethod
  def _gradient2d(data: Tensor) -> tuple[Tensor, Tensor]:
    print("""_gradient2d received shape: """, data.shape)
    gx = data[:, 1:] - data[:, :-1]
    gy = data[1:, :] - data[:-1, :]
    return gx * 0.5, gy * 0.5

  @staticmethod
  def _fastVar(data: Tensor) -> Tensor:
    print("""_fastVar received shape: """, data.shape)
    out = std(data, dim=0)
    print("""_fastVar output shape: """, out.shape)
    return out

  @staticmethod
  def _unitNorm(data: Tensor) -> Tensor:
    minVal, maxVal = data.min(), data.max()
    if abs(maxVal - minVal) < 1e-8:
      return zeros_like(data)
    return (data - minVal) / (maxVal - minVal)

  @classmethod
  def _rgb(cls, red: Tensor, green: Tensor, blue: Tensor) -> Tensor:
    return cls._unitNorm(stack((red, green, blue), dim=0))

  @staticmethod
  def _unitPool(data: Tensor, k: int, ) -> Tensor:
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    p = k // 2
    s = 1
    while len(data.shape) < 4:
      data = data.unsqueeze(0)
    pooled = max_pool2d(data, kernel_size=(k, k), stride=s, padding=p)
    return pooled.squeeze()

  @staticmethod
  def _unitConv(data: Tensor, kernel: Tensor) -> Tensor:
    padding = (kernel.shape[-2] // 2, kernel.shape[-1] // 2)
    if len(data) == 3:
      return conv2d(data.unsqueeze(0), kernel, padding=padding)
    return conv2d(data, kernel, padding=padding)

  @staticmethod
  def _edgeConv(data: Tensor, k: int) -> Tensor:
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    kN = k * k * 3
    p = k // 2
    edge = eye(kN, dtype=F32).view(kN, 3, k, k)
    if len(data) == 3:
      return conv2d(data.unsqueeze(0), edge, stride=1, padding=p)
    return conv2d(data, edge, stride=1, padding=p)

  @classmethod
  def _edge(cls, data: Tensor, k: int) -> Tensor:
    e = cls._edgeConv(data, k).squeeze()
    s = cls._fastVar(e)
    g = gradient(s)
    return (g[0] ** 2 + g[1] ** 2) ** 0.5

  def apply(self, data: Tensor, **kwargs) -> Tensor:
    height, width = data.shape[-2], data.shape[-1]
    kernel = 3
    redEdge = self._channelEdge(data, kernel, 0)
    greenEdge = self._channelEdge(data, kernel, 1)
    blueEdge = self._channelEdge(data, kernel, 2)
    redVar = self._fastVar(redEdge.squeeze())
    greenVar = self._fastVar(greenEdge.squeeze())
    blueVar = self._fastVar(blueEdge.squeeze())
    red = greenVar + blueVar
    green = redVar + blueVar
    blue = redVar + greenVar
    return self._rgb(red, green, blue)

  @classmethod
  def _fastGrad(cls, data: Tensor) -> tuple[Tensor, Tensor]:
    upper = roll(data, shifts=-1, dims=0)
    lower = roll(data, shifts=1, dims=0)
    left = roll(data, shifts=-1, dims=1)
    right = roll(data, shifts=1, dims=1)
    gx = (upper - lower) * 0.5
    gy = (left - right) * 0.5
    return gx, gy

  @classmethod
  def _gradMag(cls, data: Tensor) -> Tensor:
    gx, gy = cls._fastGrad(data)
    return (gx ** 2 + gy ** 2) ** 0.5

  @staticmethod
  def _channelEdge(data: Tensor, k: int, c: int) -> Tensor:
    if not k % 2:
      raise ValueError("Kernel size must be odd.")
    p = k // 2
    s = 1
    channel = data[c].unsqueeze(0).unsqueeze(0)
    kernel = eye(k * k, dtype=F32).view(k * k, 1, k, k)
    convolved = conv2d(channel, kernel, stride=s, padding=p)
    return convolved

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
