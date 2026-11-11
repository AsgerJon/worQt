"""
TestUniaxial3D covers 'CompressionTest' and 'TensionTest' on the whole
cylinder in space, a 'Lattice3D': the same springs, sliding two ways
along each face. Of three dimensions, the cylinder is held round its
middle as a real one is, and comes to its strength at about the strain
EN 1992-1-1 gives a concrete of that strength, 0.7 fcm ** 0.31 per
mille.

The cylinder is small and its lattice coarse, so the tests run in a
minute or so.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.meso import CompressionTest, TensionTest
from worQt.engineering.meso import Grading, Lattice3D, WholeCylinder

from . import MesoTest


class TestUniaxial3D(MesoTest):
  """Tests for the uniaxial tests in space."""

  __time_out__ = 300.0

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cylinder = WholeCylinder(30.0, 60.0, Grading.fuller(8.0, 0.5), 7)
    cls.lattice = Lattice3D(cylinder, 2.0)
    cls.modulus = cls.lattice.elasticModulus()
    cls.tension = TensionTest(cls.lattice)
    cls.tension.run()
    cls.compression = CompressionTest(cls.lattice)
    cls.compression.run()

  def test_both_reach_their_ends(self) -> None:
    """Each test reaches its end, softened past its strength."""
    for test in (self.compression, self.tension):
      self.assertTrue(test.finished)
      self.assertLess(abs(test.curve[-1][1]), 0.34 * test.strength)
      self.assertGreater(test.crackedCount, test.strengthCracks)

  def test_as_stiff_as_the_lattice(self) -> None:
    """Before it cracks, the cylinder is as stiff as its lattice, to five
    hundredths."""
    for test in (self.compression, self.tension):
      for strain, stress in test.curve:
        if abs(stress) >= 0.3 * test.strength:
          break
      self.assertAlmostEqual(stress / strain / self.modulus, 1.0,
                             delta=0.05)

  def test_the_strengths(self) -> None:
    """Crushed, it is between five and twenty five times as strong as
    pulled apart."""
    ratio = self.compression.strength / self.tension.strength
    self.assertGreater(ratio, 5.0)
    self.assertLess(ratio, 25.0)

  def test_the_strain_at_its_strength(self) -> None:
    """Crushed, it comes to its strength within three tenths of the
    strain EN 1992-1-1 gives a concrete as strong: 0.7 fcm ** 0.31 per
    mille."""
    code = 0.7 * self.compression.strength ** 0.31 / 1000
    ratio = self.compression.strengthStrain / code
    self.assertAlmostEqual(ratio, 1.0, delta=0.3)
