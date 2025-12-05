"""
ImgExtensions provides some common image file extensions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class ImgExtensions:
  """
  ImgExtensions provides some common image file extensions.
  """

  def __get__(self, instance: Any, owner: type) -> Any:
    if instance is None:
      return self
    return ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff', '.svg', ]
