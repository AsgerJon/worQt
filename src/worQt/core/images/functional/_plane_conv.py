"""
The 'planeConv' function wraps the two-dimensional convolution operation
from PyTorch. The 'F.conv2d' function applies a 2D convolution over an
input having shape (N, C_in, H, W). The 'N' parameter specifies the batch
size in each operation, which is essential for machine learning tasks. The
'planeConv' function simplifies by restricting to single images (N==1).
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor

from torch.nn import functional as F
from worktoy.utilities import textFmt
from worktoy.waitaminute import TypeException

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Never, Callable, Iterator, TypeAlias, Type


def _reshape(tensor: Tensor) -> Tensor:
  """
  This utility function accepts a tensor with shape as one of:
  (H, W) or (1, H, W) or (1, 1, H, W) for monochrome images or
  (3, H, W) or (1, 3, H, W) for RGB images. It reshapes the tensor to
  have shape (1, 3, H, W).
  """
  if len(tensor.shape) not in (2, 3, 4):
    infoSpec = """Tensor data must have 2, 3 or 4 dimensions, 
    but received shape: %s"""
    shape = ', '.join(str(dim) for dim in tensor.shape)
    info = textFmt(infoSpec % shape)
    raise ValueError(info)
  if len(tensor.shape) == 4:
    if tensor.shape[0] != 1:
      infoSpec = """Tensor data of four dimensions must have the first (
      batch size) dimension equal to 1, but received N==%d"""
      info = textFmt(infoSpec % tensor.shape[0])
      raise ValueError(info)
  if len(tensor.shape) == 3:
    tensor = tensor.unsqueeze(0)
  if len(tensor.shape) == 2:
    tensor = tensor.unsqueeze(0).repeat(3, 1, 1).unsqueeze(-1)
  if tensor.shape[1] != 3:
    infoSpec = """Tensor data must have 3 channels (C==3), 
    but received C==%d"""
    info = textFmt(infoSpec % tensor.shape[0])
    raise ValueError(info)
  return tensor


def planeConv(image: Tensor, kernel: Tensor, **kwargs) -> Tensor:
  """
  Wraps the two-dimensional convolution operation from PyTorch. The
  'F.conv2d' function applies a 2D convolution over an input having shape
  (N, C_in, H, W). The 'N' parameter specifies the batch size in each
  operation, which is essential for machine learning tasks. The 'planeConv'
  function simplifies by restricting to single images (N==1).

  Args:
    image (Tensor): The input image tensor of shape (C_in, H, W).
    kernel (Tensor): The convolution kernel tensor. Shapes must be one of:
    (3, kH, kW), (1, kH, kW) or (kH, kW). If the shape is one of the
    latter two, it is repeated to match 3 input channels.

  Keyword Args:
    stride (int | tuple[int, int], optional): The stride of the convolution.
      Default is 1.
    dilation (int | tuple[int, int], optional): The spacing between kernel
      elements. Default is 1.
    padding (int | tuple[int, int], optional): The padding added to both
    sides of the input. Default is 0.

  Returns:
    Tensor: The resulting tensor after applying the convolution operation.
  """
  image = _reshape(image)
  h, w = image.shape[-2:]
  kernel = _reshape(kernel)
  kH, kW = kernel.shape[-2:]

  stride = kwargs.get('stride', 1)
  dilation = kwargs.get('dilation', 1)

  padding = kwargs.get('padding', None)
  if padding is None:
    #  If stride and dilation are 1, padding is calculated to preserve size.
    #  Otherwise, padding defaults to 0.
    if (stride - 1) ** 2 + (dilation - 1) ** 2:
      padding = 0, 0
    else:
      padding = int(0.5 * kH), int(0.5 * kW)
  if isinstance(padding, int):
    padding = padding, padding
  if isinstance(stride, int):
    stride = stride, stride
  if isinstance(dilation, int):
    dilation = dilation, dilation

  convolved = F.conv2d(
      input=image,
      weight=kernel,
      bias=None,
      stride=stride,
      padding=padding,
      dilation=dilation,
      groups=1,
  )

  if len(convolved.shape) == 4:
    convolved = convolved.squeeze(0)
  return convolved.mean(0, keepdim=False)
