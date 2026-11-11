"""
TestStrutTie covers 'StrutTie', the strut-and-tie model of a disk on two
supports on its bottom edge, loaded on its top edge: a tied arch, the
loads split by the support they go to, each part carried down by a
strut, the struts held apart at the top by a strut and together at the
bottom by the tie the reinforcement makes. Every strut and node is held
to nu fc, nu = 0.7 - fc / 200, the tie to As fy. The factor is a lower
bound: the loads may be that many times what they are.

The numbers are those of the wall over the entrance with a tie of
4 Ø20 at 0.06 m, worked by hand: the reactions are 600 kN each, the
loads split at midspan, the parts carried from 1.5 m and 4.5 m; with
d = 2.64 m and nu fc t = 4950 kN/m the top strut solves
H = 4950 (d - sqrt(d² - 2 M / 4950)) for M = 600 (1.5 - 0.15) = 810
kNm, H = 310.5 kN, and the struts carry sqrt(600² + 310.5²) = 675.6 kN.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering import Disk, Rebar, StrutTie, Support

from . import EngineeringTest, DEEP_BEAM

_TIE = 'rebar 0.05 0.06 5.95 0.06 4 20'


class TestStrutTie(EngineeringTest):
  """Tests for 'StrutTie'."""

  def _tied(self, ) -> Disk:
    disk = Disk(DEEP_BEAM)
    disk.addRebar(Rebar(_TIE))
    return disk

  def _check(self, model: StrutTie, name: str) -> tuple:
    for check in model.checks:
      if check.name == name:
        return check
    raise KeyError(name)

  def test_the_effectiveness(self) -> None:
    """nu is 0.7 - fc / 200, fc in MPa."""
    self.assertAlmostEqual(StrutTie(self._tied()).nu, 0.55)

  def test_the_arch(self) -> None:
    """The arch rises from the bearings at the tie to the parts of the
    load, held apart by the top strut and tied at the bottom."""
    model = StrutTie(self._tied())
    self.assertTrue(model.applicable)
    kinds = [member.kind for member in model.members]
    self.assertEqual(sorted(kinds), ['strut', 'strut', 'strut', 'tie'])
    tie = [member for member in model.members if member.kind == 'tie'][0]
    self.assertAlmostEqual(tie.start[0], 0.15)
    self.assertAlmostEqual(tie.end[0], 5.85)
    self.assertAlmostEqual(tie.start[1], 0.06)
    self.assertAlmostEqual(tie.force, 310.5, delta=0.1)
    tops = sorted(node[0] for node in model.nodes if node[1] > 1.0)
    self.assertAlmostEqual(tops[0], 1.5)
    self.assertAlmostEqual(tops[1], 4.5)

  def test_the_forces(self) -> None:
    """The bearings take 600 kN each, the struts down to them 675.6 kN,
    the tie 310.5 kN of the 1005.3 kN 4 Ø20 yield at."""
    model = StrutTie(self._tied())
    bearing = self._check(model, 'bearing at the left support')
    self.assertAlmostEqual(bearing.demand, 600.0)
    self.assertAlmostEqual(bearing.capacity, 1485.0)
    strut = self._check(model, 'strut at the left support')
    self.assertAlmostEqual(strut.demand, 675.6, delta=0.1)
    tie = self._check(model, 'tie')
    self.assertAlmostEqual(tie.demand, 310.5, delta=0.1)
    self.assertAlmostEqual(tie.capacity, 1005.3, delta=0.1)

  def test_the_lower_bound(self) -> None:
    """The loads may be 2.35 times what they are, the struts at the
    supports giving out first; at that factor no check is exceeded."""
    model = StrutTie(self._tied())
    self.assertAlmostEqual(model.factor, 2.35, delta=0.01)
    self.assertIn(model.governing, ('strut at the left support',
                                    'strut at the right support'))
    worst = max(check.utilisation for check in model.checksAt(model.factor))
    self.assertAlmostEqual(worst, 1.0, delta=1e-4)

  def test_no_tie_no_arch(self) -> None:
    """With no bars tying the supports together nothing holds the arch:
    the factor is nought, and the tie governs."""
    model = StrutTie(Disk(DEEP_BEAM))
    self.assertTrue(model.applicable)
    self.assertEqual(model.factor, 0.0)
    self.assertEqual(model.governing, 'tie')

  def test_what_it_does_not_take(self) -> None:
    """A disk the tied arch does not fit says why."""
    disk = self._tied()
    disk.addSupport(Support('support left 1 1.3 x'))
    self.assertFalse(StrutTie(disk).applicable)
    self.assertIn('two supports', StrutTie(disk).reason)
    disk = Disk(6, 2.7, 0.3)
    self.assertFalse(StrutTie(disk).applicable)
