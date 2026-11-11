"""
TestUniaxial covers 'CompressionTest' and 'TensionTest', the cylinder
crushed and pulled apart between its platens, step by step, as a testing
machine does, each cell moving as Newton says, under the springs' forces.
A spring is elastic until its strength; then a crack opens, softening it
by the fracture energy of its material, and a crack that closes again
bears as before; along its face it holds by cohesion and friction, the
cohesion wearing off as it slides.

Nothing in it is concrete: the stones, the mortar and the bond are, and
the concrete behaves as concrete does. It is as stiff as its lattice,
cracks well before its strength in compression, softens after it, and
is about ten times as strong in compression as in tension.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import torch

from worQt.engineering.meso import CompressionTest, TensionTest
from worQt.engineering.meso import PhaseMaterial, UniaxialTest

from . import MesoTest, smallLattice


def _secant(test: UniaxialTest, share: float) -> float:
  """The stress over the strain where the stress first reaches 'share'
  of the strength."""
  for strain, stress in test.curve:
    if abs(stress) >= share * test.strength:
      return stress / strain
  raise ValueError(share)


class TestUniaxial(MesoTest):
  """Tests for 'CompressionTest' and 'TensionTest'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.lattice = smallLattice(7)
    cls.modulus = cls.lattice.elasticModulus()
    cls.tension = TensionTest(cls.lattice)
    cls.tension.run()
    cls.compression = CompressionTest(cls.lattice)
    cls.compression.run()

  def test_the_directions(self) -> None:
    """A compression test shortens the cylinder, a tension test
    lengthens it; each reaches its end."""
    self.assertLess(self.compression.direction, 0)
    self.assertGreater(self.tension.direction, 0)
    self.assertTrue(self.compression.finished)
    self.assertTrue(self.tension.finished)
    self.assertLess(self.compression.strain, 0.0)
    self.assertGreater(self.tension.strain, 0.0)

  def test_as_stiff_as_the_lattice(self) -> None:
    """Before it cracks, the cylinder is as stiff as its lattice, to five
    hundredths."""
    for test in (self.compression, self.tension):
      secant = _secant(test, 0.3)
      self.assertAlmostEqual(secant / self.modulus, 1.0, delta=0.05)
      self.assertEqual(test.stiffness, secant)

  def test_the_tensile_strength(self) -> None:
    """Pulled apart, it is weaker than its mortar, the bond giving out
    first, but stronger than half the bond."""
    lattice = self.lattice
    strength = self.tension.strength
    self.assertLess(strength, lattice.mortarMaterial.tension)
    self.assertGreater(strength, 0.5 * lattice.bondMaterial.tension)

  def test_the_compressive_strength(self) -> None:
    """Crushed, it is between five and twenty five times as strong as
    pulled apart, at a strain between a half and four per mille."""
    ratio = self.compression.strength / self.tension.strength
    self.assertGreater(ratio, 5.0)
    self.assertLess(ratio, 25.0)
    self.assertGreater(self.compression.strengthStrain, 0.5e-3)
    self.assertLess(self.compression.strengthStrain, 4.0e-3)

  def test_it_softens(self) -> None:
    """After its strength, the stress falls: the test ends with it at a
    third of the strength or less."""
    for test in (self.compression, self.tension):
      last = abs(test.curve[-1][1])
      self.assertLess(last, 0.34 * test.strength)
      self.assertGreater(abs(test.strain), test.strengthStrain)

  def test_it_cracks(self) -> None:
    """It cracks before its strength, and more after; a crack is a face
    opened past its strength."""
    for test in (self.compression, self.tension):
      self.assertGreater(test.strengthCracks, 0)
      self.assertGreater(test.crackedCount, test.strengthCracks)
      self.assertGreater(float(test.openings.max()), 0.0)
      self.assertEqual(len(test.openings), len(self.lattice.phases))

  def test_the_same_run(self) -> None:
    """The same lattice tested twice gives the same curve."""
    one, two = TensionTest(self.lattice), TensionTest(self.lattice)
    one.advance(1500)
    two.advance(1500)
    self.assertEqual(one.curve, two.curve)
    self.assertEqual(one.step, 1500)

  def test_the_materials(self) -> None:
    """A test may be given its own stone, mortar and bond, and where to
    reckon; a weaker bond makes a weaker cylinder."""
    lattice = self.lattice
    weak = PhaseMaterial(25000.0, 1.0, 0.0125, 2.0, 0.6, 0.125)
    materials = (lattice.stoneMaterial, lattice.mortarMaterial, weak)
    test = TensionTest(lattice, materials, 'cpu')
    self.assertEqual(test.materials, materials)
    self.assertEqual(test.device, 'cpu')
    test.run()
    self.assertLess(test.strength, self.tension.strength)
    self.assertEqual(self.tension.device, 'cpu')
    self.assertEqual(self.tension.materials[2], lattice.bondMaterial)

  def test_cracks_that_slide(self) -> None:
    """A face gives by opening or by sliding; its crack is the more of
    the two. Crushed, many faces slide further than they open: the
    inclined cracks."""
    test = self.compression
    sizes, openings, slips = test.crackSizes, test.openings, test.slips
    self.assertTrue(bool((sizes >= openings).all()))
    self.assertTrue(bool((sizes >= slips).all()))
    self.assertTrue(torch.equal(sizes, torch.maximum(openings, slips)))
    sliding = (slips > 1e-3) & (openings <= 1e-3)
    self.assertGreater(int(sliding.sum()), 0)
