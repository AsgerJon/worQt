"""
Exercises the pure FEA truss core: element geometry/stiffness, the linear
solver, and full assemble-and-solve against analytical results plus the
universal invariants (global equilibrium, symmetry, mechanism detection).
No Qt is involved, so these run without a 'QApplication'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.cad.fea import (
  Material,
  Section,
  Node,
  Bar,
  Truss,
  TrussSolution,
  solveLinear,
)


class TestTruss(BaseTest):
  """Covers the truss elements, the solver and the solve pipeline."""

  @staticmethod
  def _equilibrium(truss: Truss, solution: TrussSolution) -> tuple:
    """Residual of sum(reactions) + sum(loads); zero for a valid solve."""
    rx = sum(r[0] for r in solution.reactions)
    ry = sum(r[1] for r in solution.reactions)
    lx = sum(node.loadX for node in truss.nodes)
    ly = sum(node.loadY for node in truss.nodes)
    return (rx + lx, ry + ly)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ELEMENTS / LINEAR ALGEBRA   # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_bar_geometry(self, ) -> None:
    """A bar reports its length, direction cosines and axial stiffness."""
    bar = Bar(Node(0.0, 0.0), Node(300.0, 400.0), Material(210000.0),
              Section(100.0))
    self.assertAlmostEqual(bar.length(), 500.0)
    c, s = bar.cosines()
    self.assertAlmostEqual(c, 0.6)
    self.assertAlmostEqual(s, 0.8)
    self.assertAlmostEqual(bar.axialStiffness(), 210000.0 * 100.0 / 500.0)

  def test_bar_defaults_material_and_section(self, ) -> None:
    """Two-node bars adopt the default steel material and 100 mm^2 area."""
    bar = Bar(Node(0.0, 0.0), Node(100.0, 0.0))
    self.assertAlmostEqual(bar.material.modulus, 210000.0)
    self.assertAlmostEqual(bar.section.area, 100.0)

  def test_linear_solver_matches_known_system(self, ) -> None:
    """'solveLinear' solves a small known system."""
    matrix = [[2.0, 1.0], [1.0, 3.0]]
    result = solveLinear(matrix, [3.0, 5.0])
    self.assertAlmostEqual(result[0], 0.8)
    self.assertAlmostEqual(result[1], 1.4)

  def test_linear_solver_rejects_singular(self, ) -> None:
    """A singular matrix raises 'ValueError'."""
    with self.assertRaises(ValueError):
      solveLinear([[1.0, 2.0], [2.0, 4.0]], [1.0, 2.0])

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SOLVE   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_single_bar_matches_analytical(self, ) -> None:
    """A single axial bar gives u = P L / (E A) and a member force of P."""
    modulus, area, length, load = 210000.0, 100.0, 1000.0, 21000.0
    truss = Truss()
    base = truss.addNode(Node(0.0, 0.0)).pin()
    tip = truss.addNode(Node(length, 0.0)).roller(True)  # fix Y, free X
    tip.addLoad(load, 0.0)
    truss.addBar(Bar(base, tip, Material(modulus), Section(area)))
    solution = truss.solve()
    stiffness = modulus * area / length
    self.assertAlmostEqual(solution.displacements[1][0], load / stiffness)
    self.assertAlmostEqual(solution.displacements[1][1], 0.0)
    self.assertAlmostEqual(solution.forces[0], load)  # tension positive
    self.assertAlmostEqual(solution.reactions[0][0], -load)

  def test_solution_satisfies_global_equilibrium(self, ) -> None:
    """Reactions balance the applied loads for a solved truss."""
    truss = Truss()
    left = truss.addNode(Node(0.0, 0.0)).pin()
    right = truss.addNode(Node(2000.0, 0.0)).pin()
    apex = truss.addNode(Node(1000.0, -1000.0))
    apex.addLoad(3000.0, -10000.0)
    truss.addBar(Bar(left, apex))
    truss.addBar(Bar(right, apex))
    solution = truss.solve()
    residualX, residualY = self._equilibrium(truss, solution)
    self.assertAlmostEqual(residualX, 0.0, places=6)
    self.assertAlmostEqual(residualY, 0.0, places=6)

  def test_symmetric_truss_is_symmetric(self, ) -> None:
    """A symmetric truss under a vertical apex load moves straight down."""
    truss = Truss()
    left = truss.addNode(Node(0.0, 0.0)).pin()
    right = truss.addNode(Node(2000.0, 0.0)).pin()
    apex = truss.addNode(Node(1000.0, -1000.0))
    apex.addLoad(0.0, -10000.0)
    truss.addBar(Bar(left, apex))
    truss.addBar(Bar(right, apex))
    solution = truss.solve()
    self.assertAlmostEqual(solution.displacements[2][0], 0.0, places=6)
    self.assertLess(solution.displacements[2][1], 0.0)  # apex drops
    self.assertAlmostEqual(solution.forces[0], solution.forces[1], places=6)
    self.assertGreater(solution.forces[0], 0.0)  # both in tension

  def test_member_force_balances_at_loaded_node(self, ) -> None:
    """The bar forces resolve against the applied load at the loaded node."""
    modulus, area = 210000.0, 100.0
    truss = Truss()
    left = truss.addNode(Node(0.0, 0.0)).pin()
    right = truss.addNode(Node(2000.0, 0.0)).pin()
    apex = truss.addNode(Node(1000.0, -1000.0))
    apex.addLoad(0.0, -10000.0)
    barA = truss.addBar(Bar(left, apex, Material(modulus), Section(area)))
    barB = truss.addBar(Bar(right, apex, Material(modulus), Section(area)))
    solution = truss.solve()
    #  Nodal equilibrium at the apex: summing each member force times its
    #  own A->B direction recovers the external load applied at that node.
    sumX, sumY = 0.0, 0.0
    for bar, force in zip((barA, barB), solution.forces):
      c, s = bar.cosines()  # unit direction node A -> node B (the apex)
      sumX += force * c
      sumY += force * s
    self.assertAlmostEqual(sumX, 0.0, places=4)
    self.assertAlmostEqual(sumY, -10000.0, places=4)  # equals the apex load

  def test_mechanism_raises(self, ) -> None:
    """An under-supported structure (a mechanism) raises 'ValueError'."""
    truss = Truss()
    base = truss.addNode(Node(0.0, 0.0)).pin()
    free = truss.addNode(Node(1000.0, 0.0))  # free in Y: no restraint
    free.addLoad(100.0, 0.0)
    truss.addBar(Bar(base, free))
    with self.assertRaises(ValueError):
      truss.solve()
