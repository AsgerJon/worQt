"""
The 'pil_to_tensor' function receives a PIL image and converts it into a
PyTorch tensor representation.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import numpy as np
from PIL import Image
from torch import Tensor


def pilToTensor(img: Image.Image, **kwargs) -> Tensor:
  """
  Receives a PIL image and converts it into a PyTorch tensor
  representation.

  Args:
    img (Image.Image): The input PIL image.

  Returns:
    Tensor: The resulting PyTorch tensor.
  """

  arr = np.array(img).astype(np.float32) / 255.0
  tensor = Tensor(arr).permute((2, 0, 1))
  return tensor
