"""
TestLattice covers 'Lattice', the section through a cylinder's axis
cut into Voronoi cells, each a rigid body, each pair of neighbours held
together across the face they share by a normal and a shear spring of
the material between their nodes: stone, mortar, or, where the line
between them crosses a stone's edge, the bond, of the stone and the
mortar it crosses in series. The cells along the top and the bottom
bear on the platens.

Of Poisson's ratio nought, the lattice is exactly uniform: under any
uniform strain every cell is in equilibrium, and of one material it is
exactly as stiff as the material. With stones in it, it is about as
stiff as the Hashin-Shtrikman bounds say a mix of its stones and mortar
may be.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch

from worQt.engineering.meso import Lattice, PhaseNum

from . import MesoTest, smallLattice, hashinShtrikman


def _plain() -> Lattice:
  """A lattice of mortar only, 40 mm by 80 mm."""
  return Lattice(40.0, 80.0, (), 1.0, 7)


def _inside(points: torch.Tensor, polygon: torch.Tensor) -> torch.Tensor:
  """Which 'points' are inside a convex polygon, its corners in order
  counter-clockwise: left of every edge."""
  start = polygon
  along = torch.roll(polygon, -1, 0) - polygon
  offset = points[:, None, :] - start[None]
  turn = (along[None, :, 0] * offset[..., 1]
          - along[None, :, 1] * offset[..., 0])
  return (turn > 0).all(1)


class TestLattice(MesoTest):
  """Tests for 'Lattice'."""

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.lattice = smallLattice(7)

  def test_the_section(self) -> None:
    """The lattice is of the section through the axis, its nodes in it
    and at least the spacing apart, about one to each three spacings
    squared."""
    lattice = self.lattice
    self.assertEqual(lattice.width, 40.0)
    self.assertEqual(lattice.height, 80.0)
    nodes = lattice.nodes
    self.assertGreaterEqual(nodes[:, 0].min().item(), -20.0)
    self.assertLessEqual(nodes[:, 0].max().item(), 20.0)
    gaps = torch.cdist(nodes, nodes) + torch.eye(len(nodes)).double() * 9
    self.assertGreaterEqual(gaps.min().item(), 1.0)
    self.assertGreater(lattice.nodeCount, 3200 / 4)
    self.assertLess(lattice.nodeCount, 3200 / 2)

  def test_the_cells_fill_the_section(self) -> None:
    """The cells fill the section, no more and no less."""
    total = self.lattice.areas.sum().item()
    self.assertAlmostEqual(total, 40.0 * 80.0, delta=1e-6)
    self.assertGreater(self.lattice.areas.min().item(), 0.0)

  def test_the_faces(self) -> None:
    """The face between two neighbours is square to the line between
    their nodes and halfway along it."""
    lattice = self.lattice
    inner = lattice.phases != [*PhaseNum].index(PhaseNum.PLATEN)
    first = lattice.nodes[lattice.first[inner]]
    second = lattice.nodes[lattice.second[inner]]
    normals = lattice.normals[inner]
    ends = lattice.facetEnds[inner]
    along = ((ends[:, 1] - ends[:, 0]) * normals).sum(1)
    self.assertLess(along.abs().max().item(), 1e-9)
    middle = lattice.centres[inner] - (first + second) / 2
    self.assertLess((middle * normals).sum(1).abs().max().item(), 1e-9)

  def test_the_platens(self) -> None:
    """The cells along the bottom bear on the bottom platen and those
    along the top on the top, over the whole width."""
    lattice = self.lattice
    bottom = lattice.lengths[lattice.bottomMask].sum().item()
    top = lattice.lengths[lattice.topMask].sum().item()
    self.assertAlmostEqual(bottom, 40.0, delta=1e-9)
    self.assertAlmostEqual(top, 40.0, delta=1e-9)
    links = lattice.phases == [*PhaseNum].index(PhaseNum.PLATEN)
    self.assertTrue(torch.equal(links, lattice.bottomMask | lattice.topMask))

  def test_the_patch_test(self) -> None:
    """Of one material, under a uniform strain, every cell clear of the
    edges is in equilibrium."""
    lattice = _plain()
    strain = torch.tensor([[1.0e-3, 3.0e-4], [3.0e-4, -2.0e-3]]).double()
    places = torch.cat([lattice.nodes, lattice.platenPoints])
    moves = torch.zeros(len(places), 3).double()
    moves[:, :2] = places @ strain
    forces = lattice.elasticForces(moves.reshape(-1)).reshape(-1, 3)
    inner = ~lattice.boundaryNodes
    largest = forces[:lattice.nodeCount][inner].abs().max().item()
    self.assertLess(largest, 1e-9)

  def test_the_phases(self) -> None:
    """A spring between two nodes in one stone is of stone, one between
    two nodes clear of every stone of mortar, and one crossing a stone's
    edge of the bond."""
    lattice = self.lattice
    polygons = lattice.stones
    inner = lattice.phases != [*PhaseNum].index(PhaseNum.PLATEN)
    first = lattice.nodes[lattice.first[inner]]
    second = lattice.nodes[lattice.second[inner]]
    phases = lattice.phases[inner]

    def stoneOf(points: torch.Tensor) -> torch.Tensor:
      inside = torch.stack([_inside(points, polygon)
                            for polygon in polygons], 1)
      return torch.where(inside.any(1), inside.double().argmax(1), -1)

    one, two = stoneOf(first), stoneOf(second)
    stone = phases == [*PhaseNum].index(PhaseNum.STONE)
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
    mortar's, and a bond spring between: the stone and the mortar along
    it in series."""
    lattice = self.lattice
    stone = lattice.stoneMaterial.stiffness
    mortar = lattice.mortarMaterial.stiffness
    moduli = lattice.moduli
    phases = lattice.phases
    self.assertTrue(bool((moduli[phases == 0] == stone).all()))
    self.assertTrue(bool((moduli[phases == 1] == mortar).all()))
    bond = moduli[phases == 2]
    self.assertGreaterEqual(bond.min().item(), mortar - 1e-6)
    self.assertLessEqual(bond.max().item(), stone + 1e-6)

  def test_mortar_alone(self) -> None:
    """A lattice of mortar alone is exactly as stiff as the mortar."""
    lattice = _plain()
    self.assertEqual(lattice.stoneFraction, 0.0)
    mortar = lattice.mortarMaterial.stiffness
    self.assertAlmostEqual(lattice.elasticModulus() / mortar, 1.0,
                           delta=1e-9)

  def test_the_bounds(self) -> None:
    """With stones in it, the lattice is about as stiff as the
    Hashin-Shtrikman bounds say a mix of its stones and its mortar may
    be: within two hundredths of them."""
    lattice = self.lattice
    share = lattice.stoneFraction
    self.assertGreater(share, 0.1)
    low, high = hashinShtrikman(share, lattice.mortarMaterial.stiffness,
                                lattice.stoneMaterial.stiffness)
    modulus = lattice.elasticModulus()
    self.assertGreater(modulus, 0.98 * low)
    self.assertLess(modulus, 1.02 * high)
    self.assertTrue(math.isfinite(modulus))
