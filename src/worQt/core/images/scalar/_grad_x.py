"""
GradX provides a descriptor returning a scalar field representation of the
image gradient in the x-direction.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from torch import Tensor

from .. import BaseUnary

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Self, Never, Callable, Iterator, TypeAlias, Type


class GradX(BaseUnary):
  """
  GradX provides a descriptor returning a scalar field representation of the
  image gradient in the x-direction.
  """
