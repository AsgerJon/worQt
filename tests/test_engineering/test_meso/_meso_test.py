"""
MesoTest and MesoWidgetTest are the base classes for the tests of
'worQt.engineering.meso'. 'MesoTest' subclasses 'BaseTest' for the
model, which needs no Qt; 'MesoWidgetTest' subclasses 'WidgetTest' for
the widgets. Both may run for two minutes: a uniaxial test is thousands
of steps.

They share a small cylinder, 40 mm across and 80 mm high, cast with a
Fuller grading of 8 mm stones, so a test runs in seconds; 'smallCylinder'
casts it and 'smallLattice' builds the lattice of its section, nodes at
least 1 mm apart. 'hashinShtrikman' is the oracle of the elastic tests:
the bounds on the stiffness of two isotropic phases in the plane.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering.meso import Cylinder, Grading, Lattice
from worQt.qtest import WidgetTest


def smallCylinder(seed: int) -> Cylinder:
  """The 'smallCylinder' function casts the small cylinder, 40 mm by
  80 mm, of a Fuller grading up to 8 mm."""
  return Cylinder(40.0, 80.0, Grading.fuller(8.0, 0.5), seed)


def smallLattice(seed: int) -> Lattice:
  """The 'smallLattice' function builds the lattice of the section through
  the axis of the small cylinder, its nodes at least 1 mm apart."""
  return Lattice(smallCylinder(seed), 1.0)


def hashinShtrikman(share: float, soft: float, stiff: float) -> tuple:
  """
  The 'hashinShtrikman' function returns the least and the greatest
  Young's modulus a plane mix may have of a 'soft' and a 'stiff' phase,
  'share' of it the stiff, both of Poisson's ratio nought, as the
  lattice's phases are: the Hashin-Shtrikman bounds, on the plane bulk
  modulus K and the shear modulus G, each E / 2 for such a phase, with
  E = 4 K G / (K + G).
  """
  k1 = g1 = soft / 2
  k2 = g2 = stiff / 2
  f1, f2 = 1.0 - share, share
  kLow = k1 + f2 / (1 / (k2 - k1) + f1 / (k1 + g1))
  gLow = g1 + f2 / (1 / (g2 - g1) + f1 * (k1 + 2 * g1) / (
      2 * g1 * (k1 + g1)))
  kHigh = k2 + f1 / (1 / (k1 - k2) + f2 / (k2 + g2))
  gHigh = g2 + f1 / (1 / (g1 - g2) + f2 * (k2 + 2 * g2) / (
      2 * g2 * (k2 + g2)))
  low = 4 * kLow * gLow / (kLow + gLow)
  high = 4 * kHigh * gHigh / (kHigh + gHigh)
  return low, high


class MesoTest(BaseTest):
  """Base class for the tests of the model."""

  __time_out__ = 120.0


class MesoWidgetTest(WidgetTest):
  """Base class for the tests of the widgets."""

  __time_out__ = 120.0
