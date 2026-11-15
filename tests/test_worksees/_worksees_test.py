"""
WorkseesTest is the base class for the tests of 'worksees', each class
of them given a 'Solver' of its own.

Two models serve them, each with an answer known by hand. 'cantilever'
is a steel column 3 m high fixed at its foot, pushed 1 kN sideways at
its head: E 200 GPa, A 0.01 m², I 1e-4 m⁴, in N and m; the head moves
PL³/3EI = 0.45 mm and turns PL²/2EI = 0.225 mrad. 'patch' is a plate
2 m by 1 m, 0.1 m thick, of four plane stress quads around a node put
off the middle, pulled 1 kN along x at its right edge, its left edge
held along x and its bottom left corner along y, E 1000 kN/m² and
Poisson's ratio 0.25, in kN and m: the patch test, whose stress is
P / (h t) = 10 kN/m² along x at every point however the quads are
shaped, and whose right edge moves sigma L / E = 0.02 m. 'bar' is a
bar 1 m long along x, of area 1 and E 1000, held at its left end and
pulled by a load of 1 at its right: pushed there by u, it is held by
the load factor E A u / L = 1000 u.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worksees import Model, Solver


def cantilever() -> Model:
  """The 'cantilever' function returns the steel column pushed at its
  head: node 1 its foot, node 2 its head."""
  model = Model(2, 3)
  foot = model.addNode(0.0, 0.0)
  head = model.addNode(0.0, 3.0)
  model.fix(foot, 1, 1, 1)
  transform = model.add('geomTransf', 'Linear')
  model.add('element', 'elasticBeamColumn', foot, head, 0.01, 200e9,
            1e-4, transform)
  model.addLoad(head, 1000.0, 0.0, 0.0)
  return model


def patch() -> Model:
  """The 'patch' function returns the plate of four quads pulled at its
  right edge: nodes 1 to 9 row by row from the bottom left, node 5
  put off the middle."""
  model = Model(2, 2)
  points = [(x, y) for y in (0.0, 0.5, 1.0) for x in (0.0, 1.0, 2.0)]
  points[4] = (1.3, 0.4)
  for point in points:
    model.addNode(*point)
  plate = model.add('nDMaterial', 'ElasticIsotropic', 1000.0, 0.25)
  for corner in (1, 2, 4, 5):
    model.add('element', 'quad', corner, corner + 1, corner + 4,
              corner + 3, 0.1, 'PlaneStress', plate)
  for node in (1, 4, 7):
    model.fix(node, 1, 0)
  model.fix(1, 0, 1)
  model.addLoad(3, 0.25, 0.0)
  model.addLoad(6, 0.5, 0.0)
  model.addLoad(9, 0.25, 0.0)
  return model


def bar() -> Model:
  """The 'bar' function returns the bar pulled at its right end: node 1
  its left end, node 2 its right."""
  model = Model(1, 1)
  model.addNode(0.0)
  model.addNode(1.0)
  model.fix(1, 1)
  elastic = model.add('uniaxialMaterial', 'Elastic', 1000.0)
  model.add('element', 'truss', 1, 2, 1.0, elastic)
  model.addLoad(2, 1.0)
  return model


class WorkseesTest(BaseTest):
  """Base class for the tests of 'worksees', each class given a
  'solver' of its own, closed when it is done."""

  solver: Solver

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.solver = Solver()

  @classmethod
  def tearDownClass(cls) -> None:
    try:
      cls.solver.close()
    finally:
      super().tearDownClass()
