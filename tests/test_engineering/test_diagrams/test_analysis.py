"""
TestAnalysis covers 'Analysis', a frame reckoned: beams the hand knows,
simply supported, cantilevered, propped and continuous, under line,
point and triangular loads and a moment; a three hinged portal; a
column pushed down; the portal in equilibrium; frames not held refused,
saying why; and the shape as it bends.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.engineering.diagrams import Analysis, Frame, LineLoad, Member
from worQt.engineering.diagrams import Node, PointLoad, PointMoment
from worQt.engineering.diagrams import Support

from . import DiagramsTest, FORCE, LOAD, SPAN, beam, threeHinged

_SIMPLE = (Support(0, 'pin'), Support(1, 'roller'))


class TestAnalysis(DiagramsTest):
  """Tests for 'Analysis'."""

  def assertNear(self, value: float, exact: float) -> None:
    """'value' is 'exact', to a millionth of it."""
    self.assertLess(abs(value - exact), 1e-6 * max(abs(exact), 1.0))

  def test_line_load(self) -> None:
    """Simply supported under q: q L / 2 at each support, q L² / 8 at
    midspan, its peak; the shear q L / 2 at the ends, nought there."""
    loads = (LineLoad(0, 0.0, SPAN, LOAD, LOAD, 'down'),)
    analysis = Analysis(beam(_SIMPLE, loads))
    self.assertEqual(analysis.held, '')
    for _, up, _ in analysis.reactions:
      self.assertNear(up, LOAD * SPAN / 2)
    self.assertNear(analysis.moment(0, SPAN / 2), LOAD * SPAN ** 2 / 8)
    self.assertNear(analysis.shear(0, 0.0), LOAD * SPAN / 2)
    self.assertNear(analysis.shear(0, SPAN / 2), 0.0)
    (s, peak), = analysis.marks(0, 'M')
    self.assertNear(s, SPAN / 2)
    self.assertNear(peak, LOAD * SPAN ** 2 / 8)

  def test_point_load(self) -> None:
    """Simply supported under P at midspan: P L / 4 there, the shear
    jumping from P / 2 to -P / 2."""
    loads = (PointLoad(0, SPAN / 2, FORCE, 0.0),)
    analysis = Analysis(beam(_SIMPLE, loads))
    self.assertNear(analysis.moment(0, SPAN / 2), FORCE * SPAN / 4)
    self.assertNear(analysis.shear(0, SPAN / 2, -1), FORCE / 2)
    self.assertNear(analysis.shear(0, SPAN / 2, 1), -FORCE / 2)

  def test_cantilever(self) -> None:
    """A cantilever with P at its tip: -P L at its fixed end, held by a
    moment P L and a force P."""
    analysis = Analysis(beam((Support(0, 'fixed'),),
                             (PointLoad(0, SPAN, FORCE, 0.0),)))
    self.assertNear(analysis.moment(0, 0.0), -FORCE * SPAN)
    (_, up, turning), = analysis.reactions
    self.assertNear(up, FORCE)
    self.assertNear(turning, FORCE * SPAN)

  def test_propped(self) -> None:
    """Propped under q, indeterminate: -q L² / 8 at the fixed end, the
    prop 3 q L / 8, and the peak 9 q L² / 128 at 5 L / 8."""
    loads = (LineLoad(0, 0.0, SPAN, LOAD, LOAD, 'down'),)
    analysis = Analysis(beam((Support(0, 'fixed'), Support(1, 'roller')),
                             loads))
    self.assertNear(analysis.moment(0, 0.0), -LOAD * SPAN ** 2 / 8)
    self.assertNear(analysis.reactions[1][1], 3 * LOAD * SPAN / 8)
    s, peak = analysis.marks(0, 'M')[-1]
    self.assertNear(s, 5 * SPAN / 8)
    self.assertNear(peak, 9 * LOAD * SPAN ** 2 / 128)

  def test_two_spans(self) -> None:
    """Two spans under q: -q L² / 8 over the middle support, which takes
    5 q L / 4."""
    supports = (Support(0, 'pin'), Support(1, 'roller'),
                Support(2, 'roller'))
    loads = (LineLoad(0, 0.0, SPAN, LOAD, LOAD, 'down'),
             LineLoad(1, 0.0, SPAN, LOAD, LOAD, 'down'))
    analysis = Analysis(beam(supports, loads, 2))
    self.assertNear(analysis.moment(0, SPAN, -1), -LOAD * SPAN ** 2 / 8)
    self.assertNear(analysis.moment(1, 0.0), -LOAD * SPAN ** 2 / 8)
    self.assertNear(analysis.reactions[1][1], 5 * LOAD * SPAN / 4)

  def test_triangle(self) -> None:
    """Simply supported under a load rising from nought to q: q L / 6
    and q L / 3, and the peak q L² / (9 sqrt 3) at L / sqrt 3."""
    loads = (LineLoad(0, 0.0, SPAN, 0.0, LOAD, 'down'),)
    analysis = Analysis(beam(_SIMPLE, loads))
    self.assertNear(analysis.reactions[0][1], LOAD * SPAN / 6)
    self.assertNear(analysis.reactions[1][1], LOAD * SPAN / 3)
    (s, peak), = analysis.marks(0, 'M')
    self.assertNear(s, SPAN / math.sqrt(3))
    self.assertNear(peak, LOAD * SPAN ** 2 / (9 * math.sqrt(3)))

  def test_moment(self) -> None:
    """Simply supported under a moment at midspan: the supports push
    ±M / L, and the moment jumps by M, from M / 2 to -M / 2."""
    loads = (PointMoment(0, SPAN / 2, 12.0),)
    analysis = Analysis(beam(_SIMPLE, loads))
    self.assertNear(analysis.reactions[0][1], 12.0 / SPAN)
    self.assertNear(analysis.moment(0, SPAN / 2, -1), 6.0)
    self.assertNear(analysis.moment(0, SPAN / 2, 1), -6.0)

  def test_three_hinged(self) -> None:
    """The three hinged portal thrusts q L² / 8 h at each foot, its
    corners bend q L² / 8, its hinge nought, its columns pushed q L /
    2."""
    analysis = Analysis(threeHinged())
    (left, up, _), (right, _, _) = analysis.reactions
    self.assertNear(left, LOAD * SPAN ** 2 / 32)
    self.assertNear(right, -LOAD * SPAN ** 2 / 32)
    self.assertNear(up, LOAD * SPAN / 2)
    self.assertNear(abs(analysis.moment(0, 4.0, -1)), LOAD * SPAN ** 2 / 8)
    self.assertNear(analysis.moment(1, 3.0, -1), 0.0)
    self.assertNear(analysis.normal(0, 1.0), -LOAD * SPAN / 2)

  def test_column(self) -> None:
    """A column pushed down at its top is pressed all along, and does
    not bend."""
    frame = Frame((Node(0.0, 0.0), Node(0.0, 3.0)),
                  (Member(0, 1, 1e4, 1e6, False, False),),
                  (Support(0, 'fixed'),),
                  (PointLoad(0, 3.0, 50.0, 0.0),))
    analysis = Analysis(frame)
    self.assertNear(analysis.normal(0, 1.5), -50.0)
    self.assertNear(analysis.moment(0, 1.5), 0.0)

  def test_equilibrium(self) -> None:
    """The portal's reactions hold its loads: 15 kN of wind, 60 kN
    down."""
    analysis = Analysis(Frame())
    self.assertNear(sum(r[0] for r in analysis.reactions), -15.0)
    self.assertNear(sum(r[1] for r in analysis.reactions), 60.0)

  def test_not_held(self) -> None:
    """A frame not held is refused, saying why, its forces nought."""
    rolling = Analysis(beam((Support(0, 'roller'), Support(1, 'roller')),
                            ()))
    self.assertIn('along x', rolling.held)
    frame = Frame().withoutLoad(1).withoutLoad(0)
    hinged = frame.withMember(1, frame.members[1].hinged(True, True))
    hinged = hinged.withSupport(0, Support(0, 'pin'))
    analysis = Analysis(hinged)
    self.assertIn('move without bending', analysis.held)
    self.assertEqual(analysis.moment(0, 1.0), 0.0)
    self.assertEqual(analysis.shape(0), [])

  def test_shape(self) -> None:
    """Simply supported under q, the beam sags 5 q L^4 / 384 EI at
    midspan."""
    loads = (LineLoad(0, 0.0, SPAN, LOAD, LOAD, 'down'),)
    shape = Analysis(beam(_SIMPLE, loads)).shape(0)
    middle = [p for p in shape if abs(p[0] - SPAN / 2) < 1e-9]
    self.assertEqual(len(middle), 1)
    exact = 5 * LOAD * SPAN ** 4 / (384 * 1e4)
    self.assertNear(-middle[0][3], exact)
