"""
TestLattice3D covers 'Lattice3D', the whole cylinder cut into Voronoi
cells in three dimensions, each a rigid body moving and turning every
way, each pair of neighbours held together across the face they share
by a normal spring and two shear springs of the material between their
nodes: stone, mortar, or, where the line between them crosses a stone's
face, the bond, of the stone and the mortar along it in series. The
cells along the top and the bottom bear on the platens; those along the
round wall are free.

Of Poisson's ratio nought, the lattice is exactly uniform: under any
uniform strain every cell clear of the edges is in equilibrium. Of one
material it is as stiff as the material but for the little its round
wall, faceted by the cells along it, differs from a cylinder. With
stones in it, it is about as stiff as the Hashin-Shtrikman bounds say a
mix of its stones and mortar may be.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch

from worQt.engineering.meso import Grading, Lattice3D, PhaseNum
from worQt.engineering.meso import WholeCylinder

from . import MesoTest


def _plain() -> Lattice3D:
  """A lattice of mortar only, a cylinder 50 mm across and 60 mm high."""
  return Lattice3D(25.0, 60.0, (), 2.0, 7)


def _small() -> Lattice3D:
  """The lattice of a whole small cylinder, 30 mm across and 60 mm high,
  of a Fuller grading up to 8 mm, nodes at least 1.5 mm apart."""
  cylinder = WholeCylinder(30.0, 60.0, Grading.fuller(8.0, 0.5), 7)
  return Lattice3D(cylinder, 1.5)


def _bounds(share: float, soft: float, stiff: float) -> tuple:
  """The Hashin-Shtrikman bounds on Young's modulus of a mix in space of
  a 'soft' and a 'stiff' phase, 'share' of it the stiff, both of
  Poisson's ratio nought: K = E / 3 and G = E / 2 for each, and
  E = 9 K G / (3 K + G)."""
  k1, g1, k2, g2 = soft / 3, soft / 2, stiff / 3, stiff / 2
  f1, f2 = 1.0 - share, share
  kLow = k1 + f2 / (1 / (k2 - k1) + 3 * f1 / (3 * k1 + 4 * g1))
  kHigh = k2 + f1 / (1 / (k1 - k2) + 3 * f2 / (3 * k2 + 4 * g2))
  gLow = g1 + f2 / (1 / (g2 - g1) + 6 * f1 * (k1 + 2 * g1) / (
      5 * g1 * (3 * k1 + 4 * g1)))
  gHigh = g2 + f1 / (1 / (g1 - g2) + 6 * f2 * (k2 + 2 * g2) / (
      5 * g2 * (3 * k2 + 4 * g2)))
  low = 9 * kLow * gLow / (3 * kLow + gLow)
  high = 9 * kHigh * gHigh / (3 * kHigh + gHigh)
  return low, high


def _inside(points: torch.Tensor, stone) -> torch.Tensor:
  """Which 'points' are inside 'stone': within every face."""
  reach = (points - stone.centre) @ stone.normals.T - stone.offsets
  return (reach < 0).all(1)


class TestLattice3D(MesoTest):
  """Tests for 'Lattice3D'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.plain = _plain()
    cls.lattice = _small()

  def test_the_cylinder(self) -> None:
    """The lattice is of the whole cylinder, its nodes in it and at least
    the spacing apart."""
    lattice = self.plain
    self.assertEqual(lattice.radius, 25.0)
    self.assertEqual(lattice.height, 60.0)
    nodes = lattice.nodes
    reach = torch.sqrt(nodes[:, 0] ** 2 + nodes[:, 2] ** 2)
    self.assertLessEqual(reach.max().item(), 25.0)
    self.assertGreaterEqual(nodes[:, 1].min().item(), 0.0)
    self.assertLessEqual(nodes[:, 1].max().item(), 60.0)
    gaps = torch.cdist(nodes, nodes) + torch.eye(len(nodes)).double() * 9
    self.assertGreaterEqual(gaps.min().item(), 2.0)
    self.assertEqual(lattice.bodyMoves, 6)

  def test_the_cells_fill_the_cylinder(self) -> None:
    """The cells fill the cylinder, to the little their faces along the
    round wall differ from it: a hundredth."""
    total = self.plain.volumes.sum().item()
    self.assertAlmostEqual(total / (math.pi * 625 * 60), 1.0, delta=0.01)
    self.assertGreater(self.plain.volumes.min().item(), 0.0)

  def test_the_faces(self) -> None:
    """The face between two neighbours is square to the line between
    their nodes and halfway along it."""
    lattice = self.plain
    inner = lattice.phases != [*PhaseNum].index(PhaseNum.PLATEN)
    first = lattice.nodes[lattice.first[inner]]
    second = lattice.nodes[lattice.second[inner]]
    normals = lattice.normals[inner]
    middle = lattice.centres[inner] - (first + second) / 2
    self.assertLess((middle * normals).sum(1).abs().max().item(), 1e-9)
    self.assertGreater(lattice.faceAreas.min().item(), 0.0)

  def test_the_platens(self) -> None:
    """The cells along the bottom bear on the bottom platen and those
    along the top on the top, over the whole end."""
    lattice = self.plain
    area = math.pi * 625
    bottom = lattice.faceAreas[lattice.bottomMask].sum().item()
    top = lattice.faceAreas[lattice.topMask].sum().item()
    self.assertAlmostEqual(bottom / area, 1.0, delta=0.01)
    self.assertAlmostEqual(top / area, 1.0, delta=0.01)
    self.assertAlmostEqual(lattice.loadedArea, bottom)

  def test_the_patch_test(self) -> None:
    """Of one material, under a uniform strain, every cell clear of the
    edges is in equilibrium."""
    lattice = self.plain
    strain = torch.tensor([[1.0e-3, 3.0e-4, -2.0e-4],
                           [3.0e-4, -2.0e-3, 5.0e-4],
                           [-2.0e-4, 5.0e-4, 7.0e-4]]).double()
    places = torch.cat([lattice.nodes, lattice.platenPoints])
    moves = torch.zeros(len(places), 6).double()
    moves[:, :3] = places @ strain
    forces = lattice.elasticForces(moves.reshape(-1)).reshape(-1, 6)
    inner = ~lattice.boundaryNodes
    largest = forces[:lattice.nodeCount][inner].abs().max().item()
    self.assertLess(largest, 1e-8)

  def test_mortar_alone(self) -> None:
    """A lattice of mortar alone is as stiff as the mortar, but for the
    little its faceted wall takes off: within half a hundredth."""
    lattice = self.plain
    mortar = lattice.mortarMaterial.stiffness
    self.assertAlmostEqual(lattice.elasticModulus() / mortar, 1.0,
                           delta=0.005)

  def test_the_phases(self) -> None:
    """A spring between two nodes in one stone is of stone, one between
    two nodes clear of every stone of mortar, and one crossing a stone's
    face of the bond."""
    lattice = self.lattice
    stones = lattice.stones
    inner = lattice.phases != [*PhaseNum].index(PhaseNum.PLATEN)
    first = lattice.nodes[lattice.first[inner]]
    second = lattice.nodes[lattice.second[inner]]
    phases = lattice.phases[inner]

    def stoneOf(points: torch.Tensor) -> torch.Tensor:
      inside = torch.stack([_inside(points, stone) for stone in stones], 1)
      return torch.where(inside.any(1), inside.double().argmax(1), -1)

    one, two = stoneOf(first), stoneOf(second)
    stone = phases == [*PhaseNum].index(PhaseNum.STONE)
    self.assertGreater(int(stone.sum()), 0)
    self.assertTrue(bool((one[stone] >= 0).all()))
    self.assertTrue(bool((one[stone] == two[stone]).all()))
    mortar = phases == [*PhaseNum].index(PhaseNum.MORTAR)
    self.assertTrue(bool((one[mortar] < 0).all()))
    self.assertTrue(bool((two[mortar] < 0).all()))
    bond = phases == [*PhaseNum].index(PhaseNum.BOND)
    self.assertGreater(int(bond.sum()), 0)
    self.assertFalse(bool(((one == two) & (one >= 0) & bond).any()))

  def test_the_moduli(self) -> None:
    """A stone spring is of the stone's modulus, a mortar spring of the
    mortar's, and a bond spring between."""
    lattice = self.lattice
    stone = lattice.stoneMaterial.stiffness
    mortar = lattice.mortarMaterial.stiffness
    moduli, phases = lattice.moduli, lattice.phases
    self.assertTrue(bool((moduli[phases == 0] == stone).all()))
    self.assertTrue(bool((moduli[phases == 1] == mortar).all()))
    bond = moduli[phases == 2]
    self.assertGreaterEqual(bond.min().item(), mortar - 1e-6)
    self.assertLessEqual(bond.max().item(), stone + 1e-6)

  def test_the_bounds(self) -> None:
    """With stones in it, the lattice is about as stiff as the
    Hashin-Shtrikman bounds say a mix of its stones and mortar may be:
    within three hundredths of them."""
    lattice = self.lattice
    share = lattice.stoneFraction
    self.assertGreater(share, 0.1)
    low, high = _bounds(share, lattice.mortarMaterial.stiffness,
                        lattice.stoneMaterial.stiffness)
    modulus = lattice.elasticModulus()
    self.assertGreater(modulus, 0.97 * low)
    self.assertLess(modulus, 1.03 * high)
