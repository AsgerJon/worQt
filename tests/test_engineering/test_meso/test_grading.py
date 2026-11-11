"""
TestGrading covers 'Grading', the grading curve of an aggregate, its
'kornkurve': the share of it, by volume, passing each sieve. Between two
sieves the curve runs straight on log-log paper, as a datasheet's curve
is drawn, so Fuller's curve, (d / D) ** q, is exact between its sieves
too. Stones sampled from the curve to fill a volume follow it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy
import torch

from worQt.engineering.meso import Grading

from . import MesoTest


class TestGrading(MesoTest):
  """Tests for 'Grading'."""

  def test_fullers_curve(self) -> None:
    """Fuller's curve passes (d / D) ** q of the aggregate through a
    sieve of d, and all of it through the largest size and beyond."""
    grading = Grading.fuller(16.0, 0.5)
    self.assertAlmostEqual(grading.passingAt(4.0), 0.5)
    self.assertAlmostEqual(grading.passingAt(1.0), 0.25)
    self.assertAlmostEqual(grading.passingAt(16.0), 1.0)
    self.assertAlmostEqual(grading.passingAt(31.5), 1.0)

  def test_between_the_sieves(self) -> None:
    """Between two sieves the curve is straight on log-log paper, so
    Fuller's curve holds between its sieves too."""
    grading = Grading.fuller(16.0, 0.5)
    self.assertAlmostEqual(grading.passingAt(6.0), math.sqrt(6 / 16))
    self.assertAlmostEqual(grading.passingAt(0.04), math.sqrt(0.04 / 16))

  def test_the_standard_sieves(self) -> None:
    """Fuller's curve is given at the standard sieves, 0.063 mm up to
    the largest size."""
    grading = Grading.fuller(16.0, 0.5)
    self.assertEqual(grading.sieves[0], 0.063)
    self.assertEqual(grading.sieves[-5:], (4.0, 5.6, 8.0, 11.2, 16.0))
    self.assertEqual(grading.maxSize, 16.0)
    self.assertEqual(Grading.fuller(12.0, 0.5).sieves[-2:], (11.2, 12.0))

  def test_a_datasheet(self) -> None:
    """A grading is any sieve table, as read off a datasheet; what
    passes never falls as the sieves grow, and all of it passes the
    last."""
    sieves = (0.25, 1.0, 4.0, 8.0, 16.0)
    grading = Grading(sieves, (0.05, 0.25, 0.45, 0.65, 1.0))
    self.assertAlmostEqual(grading.passingAt(4.0), 0.45)
    self.assertEqual(grading.maxSize, 16.0)
    with self.assertRaises(ValueError):
      Grading((1.0, 2.0, 4.0), (0.5, 0.4, 1.0))
    with self.assertRaises(ValueError):
      Grading((1.0, 2.0, 4.0), (0.2, 0.4, 0.9))
    with self.assertRaises(ValueError):
      Grading((1.0, 4.0, 2.0), (0.2, 0.4, 1.0))

  def test_the_stones_follow_the_curve(self) -> None:
    """Stones sampled from 4 mm up to fill a volume take the share of it
    the curve gives them, and of those stones the share by volume
    passing each sieve is the curve's."""
    grading = Grading.fuller(16.0, 0.5)
    rng = numpy.random.default_rng(3)
    sizes = grading.sample(rng, 4.0e6, 4.0)
    self.assertIsInstance(sizes, torch.Tensor)
    self.assertGreaterEqual(sizes.min().item(), 4.0)
    self.assertLessEqual(sizes.max().item(), 16.0)
    volumes = math.pi / 6 * sizes ** 3
    total = volumes.sum().item()
    self.assertAlmostEqual(total / 2.0e6, 1.0, delta=0.01)
    least = grading.passingAt(4.0)
    for sieve in (5.6, 8.0, 11.2):
      share = volumes[sizes <= sieve].sum().item() / total
      wanted = (grading.passingAt(sieve) - least) / (1.0 - least)
      self.assertAlmostEqual(share, wanted, delta=0.02)

  def test_the_largest_first(self) -> None:
    """The stones come largest first, the order they are placed in."""
    grading = Grading.fuller(16.0, 0.5)
    sizes = grading.sample(numpy.random.default_rng(5), 1.0e6, 4.0)
    self.assertTrue(bool((sizes[:-1] >= sizes[1:]).all()))
