"""AbstractTestMap subclasses unittest.TestCase and is shared by various
map classes that subclass AbstractMap."""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from random import gauss
from unittest import TestCase
from math import pi

from worQt.tools.geometry import Point, Region, Size, Vector

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

if TYPE_CHECKING:
  pass


class AbstractTest(TestCase):
  """TestMoveMap tests the ScaleMap class."""

  @staticmethod
  def randFloat() -> float:
    """Creates a random float"""
    return gauss() * 2 * pi

  @classmethod
  def randInt(cls, ) -> int:
    """Creates a random integer"""
    return int(127 * gauss()) or cls.randInt()

  @classmethod
  def randPoint(cls, ) -> Point:
    """Creates a random point"""
    return Point(cls.randFloat(), cls.randFloat())

  @classmethod
  def randVector(cls, ) -> Vector:
    """Creates a random vector"""
    return Vector(cls.randFloat(), cls.randFloat())

  @classmethod
  def randComplex(cls) -> complex:
    """Creates a random complex number"""
    return cls.randFloat() + cls.randFloat() * 1j

  @classmethod
  def randFloats(cls) -> tuple[float, float]:
    """Creates a random tuple of floats"""
    return cls.randFloat(), cls.randFloat()

  @classmethod
  def randInts(cls) -> tuple[int, int]:
    """Creates a random tuple of integers"""
    return cls.randInt(), cls.randInt()

  @classmethod
  def randIntFloat(cls, ) -> tuple[int, float]:
    """Creates a random int and random float"""
    return cls.randInt(), cls.randFloat() / 2 / pi * 127

  @classmethod
  def randFloatInt(cls) -> tuple[float, int]:
    """Creates a random float and random int"""
    out = cls.randIntFloat()
    return out[1], out[0]

  @classmethod
  def randSize(cls) -> Size:
    """Creates a random size"""
    return Size(abs(cls.randFloat()), abs(cls.randFloat()))

  @classmethod
  def randRegion(cls) -> Region:
    """Creates a random region"""
    topLeft = cls.randPoint()
    size = cls.randSize()
    return Region(topLeft, size, )

  @classmethod
  def randRegions(cls, ) -> tuple[Region, Region]:
    """Creates a random tuple of regions"""
    return cls.randRegion(), cls.randRegion()

  @classmethod
  def randRegionSize(cls) -> tuple[Region, Size]:
    """Creates a random region and size"""
    return cls.randRegion(), cls.randSize()

  @classmethod
  def randSizeRegion(cls) -> tuple[Size, Region]:
    """Creates a random size and region"""
    return cls.randSize(), cls.randRegion()

  @classmethod
  def randPointFloat(cls) -> tuple[Point, float]:
    """Creates a random point and random float"""
    return cls.randPoint(), cls.randFloat()

  @classmethod
  def rand3Float(cls, ) -> tuple[float, float, float]:
    """Creates a random tuple of three floats"""
    return cls.randFloat(), cls.randFloat(), cls.randFloat()

  @classmethod
  def randPointVector(cls, ) -> tuple[Point, Vector]:
    """Creates a random point and random vector"""
    return cls.randPoint(), cls.randVector()
