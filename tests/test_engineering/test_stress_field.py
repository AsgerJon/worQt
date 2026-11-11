"""
TestStressField covers 'StressField', the stress in a disk of plain,
uncracked concrete found by OpenSees on a mesh of plane stress quads:
the mesh meets every support and load, a column pressed evenly is
pressed evenly throughout, the wall over the entrance bends like the
deep beam it is, its supports carrying the load, and a disk its
supports do not hold has no field and says why.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worksees import Solver

from worQt.engineering import CellStress, Disk, StressField

from . import EngineeringTest, DEEP_BEAM

#  A column 2 m wide and 4 m high pressed by 600 kN along its top, held
#  along its bottom and its left side so nothing holds back its
#  spreading: -600 / (2 x 0.3) = -1000 kN/m2 throughout
_COLUMN = """disk 2 x 4 x 0.3
support bottom 0 2 y
support left 0 4 x
load top 0 2 F 0 -600"""


class TestStressField(EngineeringTest):
  """Tests for 'StressField'."""

  solver: Solver

  @classmethod
  def setUpClass(cls) -> None:
    super().setUpClass()
    cls.solver = Solver()
    cls.wall = StressField(Disk(DEEP_BEAM), cls.solver)

  @classmethod
  def tearDownClass(cls) -> None:
    cls.solver.close()
    super().tearDownClass()

  def test_principal_stresses(self) -> None:
    """A cell's principal stresses are those of Mohr's circle, the
    major one's direction from x."""
    pulled = CellStress(0.0, 0.0, 2.0, -1.0, 0.0)
    self.assertAlmostEqual(pulled.major, 2.0)
    self.assertAlmostEqual(pulled.minor, -1.0)
    self.assertAlmostEqual(pulled.angle, 0.0)
    sheared = CellStress(0.0, 0.0, 0.0, 0.0, 1.0)
    self.assertAlmostEqual(sheared.major, 1.0)
    self.assertAlmostEqual(sheared.minor, -1.0)
    self.assertAlmostEqual(sheared.angle, math.pi / 4)

  def test_modulus(self) -> None:
    """The concrete's modulus is EN 1992-1-1's 22 ((fc + 8) / 10)^0.3
    GPa: 32.8 GPa for C30."""
    self.assertAlmostEqual(self.wall.Ecm, 32836.6, 1)

  def test_mesh_meets_stretches(self) -> None:
    """The mesh has a line at the end of every support and load, the
    lines at most a 24th of the shorter side apart."""
    columns, rows = self.wall.columns, self.wall.rows
    for at in (0.0, 0.3, 5.7, 6.0):
      self.assertTrue(any(abs(x - at) < 1e-9 for x in columns))
    self.assertEqual((rows[0], rows[-1]), (0.0, 2.7))
    for lines in (columns, rows):
      for low, high in zip(lines, lines[1:]):
        self.assertGreater(high - low, 0.0)
        self.assertLessEqual(high - low, 2.7 / 24 + 1e-9)
    cellCount = (len(columns) - 1) * (len(rows) - 1)
    self.assertEqual(len(self.wall.cells), cellCount)

  def test_column_evenly_pressed(self) -> None:
    """The column is pressed by -1 MPa throughout, along y only, its
    bottom carrying the whole 600 kN."""
    field = StressField(Disk(_COLUMN), self.solver)
    self.assertTrue(field.applicable)
    for cell in field.cells:
      self.assertAlmostEqual(cell.sy, -1.0, 9)
      self.assertAlmostEqual(cell.sx, 0.0, 9)
      self.assertAlmostEqual(cell.sxy, 0.0, 9)
    (bottomX, bottomY), (sideX, sideY) = field.reactions
    self.assertAlmostEqual(bottomY, 600.0, 6)
    for force in (bottomX, sideX, sideY):
      self.assertAlmostEqual(force, 0.0, 6)

  def test_wall_carried(self) -> None:
    """The supports carry the 1200 kN between them, about half each,
    and nothing along x."""
    (leftX, leftY), (rightX, rightY) = self.wall.reactions
    self.assertAlmostEqual(leftY + rightY, 1200.0, 6)
    self.assertLess(abs(leftY - 600.0), 5.0)
    self.assertAlmostEqual(leftX + rightX, 0.0, 6)

  def test_wall_bends(self) -> None:
    """The wall bends: pulled along its bottom at midspan, pressed along
    its top, and pressed hardest over its supports."""
    field = self.wall
    middle = (len(field.columns) - 1) // 2
    bottom = field.cellAt(middle, 0)
    top = field.cellAt(middle, len(field.rows) - 2)
    self.assertGreater(bottom.sx, 1.0)
    self.assertLess(top.sx, -1.0)
    _, index = min((cell.minor, n) for n, cell in enumerate(field.cells))
    hardest = field.cells[index]
    self.assertLess(min(hardest.x, 6.0 - hardest.x), 0.6)
    self.assertLess(hardest.y, 0.6)

  def test_unheld(self) -> None:
    """A disk its supports do not hold has no field, and says why:
    nothing holding it along x, or nothing stopping it turning."""
    sliding = Disk(DEEP_BEAM.replace('5.7 6 x y', '5.7 6 y'))
    field = StressField(sliding, self.solver)
    self.assertFalse(field.applicable)
    self.assertEqual(field.reason, 'nothing holds it along x')
    self.assertEqual(field.cells, ())
    turning = Disk('\n'.join(['disk 6 x 2.7 x 0.3',
                              'support bottom 0 6 x',
                              'support left 0 2.7 y',
                              'load top 0 6 F 0 -1200']))
    field = StressField(turning, self.solver)
    self.assertFalse(field.applicable)
    self.assertEqual(field.reason, 'nothing stops it turning')
