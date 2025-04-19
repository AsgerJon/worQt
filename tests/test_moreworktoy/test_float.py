"""Testing the _Float class"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from random import random, randint

try:
  from typing import TYPE_CHECKING
except ImportError:
  try:
    from typing_extensions import TYPE_CHECKING
  except ImportError:
    TYPE_CHECKING = False

from unittest import TestCase

from moreworktoy.text._float_fmt import _Float


class TestFloat(TestCase):
  """Test the _Float class."""

  @staticmethod
  def randFloat() -> tuple[float, int, float]:
    """Generate a random float."""
    eps = 1e-16
    m = random() * (0.9 - 2 * eps) + 0.1 + eps
    e = randint(-16, 16)
    return m, e, m * (10 ** e)

  @staticmethod
  def randSigDigs(n: int) -> float:
    """Generate a random float with n significant digits."""
    if not n:
      return 1
    eps = 1e-16
    base = random() * (1 - 2 * eps) + eps
    base *= (10 ** n)
    return round(base) * (10 ** -n)

  def setUp(self, ) -> None:
    """Set up the test case."""
    baseVals = [2 ** -x for x in range(1, 17)]
    vals = [*baseVals, *[1 - x for x in baseVals]]
    vals.sort()
    self.linSamples = [0.1 + 0.9 * x for x in vals]
    self.randSamples = [self.randFloat() for _ in range(100)]
    self.sigSamples = [self.randSigDigs(x) for x in range(17)]

  def test_log10ceil(self) -> None:
    """Test the _Float class."""
    for val in self.linSamples:
      for e in range(-16, 16):
        self.assertEqual(_Float._log10ceil(val * 10 ** e), e)

  def test_values(self, ) -> None:
    """Test that the values are correct. """
    for m, e, v in self.randSamples:
      self.assertAlmostEqual(float(_Float(v)), v)

  def test_mantissas(self, ) -> None:
    """Test that the mantissa values are correct. """
    for m, e, v in self.randSamples:
      self.assertAlmostEqual(_Float(v).getMantissa(), m)

  def test_exponents(self, ) -> None:
    """Test that the exponent values are correct. """
    for m, e, v in self.randSamples:
      self.assertEqual(_Float(v).getExponent(), e)
