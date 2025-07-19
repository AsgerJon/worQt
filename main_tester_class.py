"""Tester"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import sys

from typing import Callable


class Point:
  """Defines a location in a 2D space."""

  x: float = 0
  y: float = 0

  def __init__(self, x: float, y: float) -> None:
    """Initializes the point with the given coordinates."""
    self.x = x
    self.y = y


class Region:

  def lowerBound(self, ) -> Callable:
    """Returns a float-float map defining the lower bound of the region."""

    def func(x: float) -> float:
      """Returns the lower bound of the region."""
      return 0

    return func

  def upperBound(self, ) -> Callable:
    """Returns a float-float map defining the upper bound of the region."""

    def func(x: float) -> float:
      """Returns the upper bound of the region."""
      return 1

    return func

  def __contains__(self, point: Point) -> bool:
    """Returns True if the point is in the region, False otherwise."""
    if not isinstance(point, Point):
      return False
    yMin, yMax = self.lowerBound()(point.x), self.upperBound()(point.x)
    if point.y < yMin or point.y > yMax:
      return False
    return True


def main(*args) -> int:
  """Main function to test the Region class."""
  region = Region()  # Sample region
  point = Point(0.5, 0.5)  # Sample point in the region
  if point not in region:
    print("""Something went wrong!""")
    return 1
  print("""The point is in the region!""")
  return 0


if __name__ == '__main__':
  sys.exit(main(*sys.argv))
