"""AbstractGeometry provides an abstract baseclass for geometry objects.
Subclasses must provide the following properties:
  - left: float -> The left edge of the object.
  - top: float -> The top edge of the object.
  - right: float -> The right edge of the object.
  - bottom: float -> The bottom edge of the object.


"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from abc import abstractmethod

from worktoy.mcls import BaseObject

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

from worktoy.attr import Field


class AbstractGeometry(BaseObject):
  """AbstractGeometry provides an abstract baseclass for geometry objects.
  Subclasses must provide the following properties:
    - left: float -> The left edge of the object.
    - top: float -> The top edge of the object.
    - right: float -> The right edge of the object.
    - bottom: float -> The bottom edge of the object.
  """

  left = Field()
  top = Field()
  right = Field()
  bottom = Field()

  @abstractmethod
  @left.GET
  def _getLeft(self) -> float:
    """Get the left edge of the object."""
    raise NotImplementedError

  @abstractmethod
  @top.GET
  def _getTop(self) -> float:
    """Get the top edge of the object."""
    raise NotImplementedError

  @abstractmethod
  @right.GET
  def _getRight(self) -> float:
    """Get the right edge of the object."""
    raise NotImplementedError

  @abstractmethod
  @bottom.GET
  def _getBottom(self) -> float:
    """Get the bottom edge of the object."""
    raise NotImplementedError
