"""
The private '_doubles' module makes float64 tensors of Python numbers.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import numpy
import torch


def doubles(values: list | tuple) -> torch.Tensor:
  """
  The 'doubles' function returns 'values', numbers or rows of them, as a
  float64 tensor, every digit kept: 'torch.tensor' makes float32 of
  Python floats, losing them.
  """
  return torch.from_numpy(numpy.array(values, numpy.float64))
