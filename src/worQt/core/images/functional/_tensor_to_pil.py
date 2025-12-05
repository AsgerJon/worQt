"""
The 'tensorToPIL' function creates a PIL image from a PyTorch tensor. The
tensor must be in the format (C==3, H, W) with float values in unit range.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import numpy as np
from PIL import Image
from torch import Tensor


def tensorToPIL(data: Tensor, **kwargs) -> Image.Image:
  """
  Creates a PIL image from a PyTorch tensor. The tensor must be in the
  format (C==3, H, W) with float values in unit range.

  Args:
    data (Tensor): The input tensor representing the image.

  Returns:
    Image.Image: The resulting PIL image.
  """

  arr = data.permute((1, 2, 0)).numpy(force=True) * 255.0
  return Image.fromarray(arr.astype(np.uint8)).convert('RGB')
