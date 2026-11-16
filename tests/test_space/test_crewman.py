"""
TestCrewman covers Asger out of his chair (user, 2026-11-17: "when can
Asger get up and float around in micro-gravity?"; "FAFO rules"): he gets
up behind his chair and sits again only near it; pulled to the floor he
walks (slower the harder he is pulled), weightless he pushes off the way
he looks; his up turns to stand against the pull, never while
weightless; a jump or a push off; his figure stands on his soles.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.sandbox._skin import PARTS
from worQt.gaming.space._aerospike import G0
from worQt.gaming.space._cockpit import FLOOR, Cockpit
from worQt.gaming.space._crewman import JUMP, PUSH, STRIDE
from worQt.gaming.space._turns import dot, norm

from . import SpaceTest


class TestCrewman(SpaceTest):
  """Tests for Asger out of his chair."""

  def test_up_and_down(self) -> None:
    """Getting up stands him on the floor behind his chair; he sits again
    near it, not far from it; his eyes are his body's when up."""
    cockpit = Cockpit()
    crewman = cockpit.crewman
    self.assertTrue(crewman.buckled)
    cockpit.gotUp()
    self.assertFalse(crewman.buckled)
    self.assertAlmostEqual(crewman.soles()[2], FLOOR, 1)
    self.assertGreater(cockpit.eye()[2], FLOOR + 1.4)
    crewman.middle = tuple(m - (2.0 if k == 0 else 0.0)
                           for k, m in enumerate(crewman.middle))
    self.assertFalse(cockpit.satDown())
    self.assertFalse(crewman.buckled)
    crewman.unbuckled()
    self.assertTrue(cockpit.satDown())
    self.assertTrue(crewman.buckled)

  def test_walking(self) -> None:
    """Pulled to the floor at one g he walks ahead at his stride, along
    the floor; at four g at a sixteenth of it; no keys, he stands."""
    crewman = Cockpit().crewman
    crewman.unbuckled()
    wanted, walking, wanting = crewman.wantOf({'ahead'}, 0.0, 0.0,
                                              (0.0, 0.0, -G0))
    self.assertEqual((walking, wanting), (1, 1))
    self.assertClose(wanted, (STRIDE, 0.0, 0.0), 1e-9)
    wanted, _, _ = crewman.wantOf({'ahead'}, 0.0, 0.0,
                                  (0.0, 0.0, -4.0 * G0))
    self.assertAlmostEqual(norm(wanted), STRIDE / 16.0, 9)
    wanted, walking, _ = crewman.wantOf(set(), 0.0, 0.0, (0.0, 0.0, -G0))
    self.assertEqual(walking, 1)
    self.assertClose(wanted, (0.0, 0.0, 0.0), 1e-12)

  def test_pushing(self) -> None:
    """Weightless he pushes off the way he looks (up too), at 'PUSH';
    no keys, he wants nothing."""
    crewman = Cockpit().crewman
    crewman.unbuckled()
    wanted, walking, wanting = crewman.wantOf({'ahead'}, 0.0, 0.5,
                                              (0.0, 0.0, 0.0))
    self.assertEqual((walking, wanting), (0, 1))
    self.assertAlmostEqual(norm(wanted), PUSH, 9)
    self.assertAlmostEqual(wanted[2] / PUSH, math.sin(0.5), 9)
    _, _, wanting = crewman.wantOf(set(), 0.0, 0.0, (0.0, 0.0, 0.0))
    self.assertEqual(wanting, 0)

  def test_righted(self) -> None:
    """His up turns to stand against the pull; weightless it stays."""
    crewman = Cockpit().crewman
    crewman.unbuckled()
    crewman.righted((0.0, 0.0, 0.0), 10.0)
    self.assertClose(crewman.up, (0.0, 0.0, 1.0), 1e-12)
    for _ in range(600):
      crewman.righted((G0, 0.0, 0.0), 1.0 / 60.0)
    self.assertClose(crewman.up, (-1.0, 0.0, 0.0), 1e-3)
    self.assertLess(abs(dot(crewman.up, crewman.ahead)), 1e-9)

  def test_leap(self) -> None:
    """Pulled, a jump as high as 'JUMP'; weightless, a push off what he
    touches; touching nothing, nothing."""
    crewman = Cockpit().crewman
    crewman.unbuckled()
    leap = crewman.leapOf((0.0, 0.0, -G0))
    self.assertAlmostEqual(leap[2] ** 2 / (2.0 * G0), JUMP, 9)
    crewman.ground = (0.0, 1.0, 0.0)
    self.assertClose(crewman.leapOf((0.0, 0.0, 0.0)), (0.0, PUSH, 0.0),
                     1e-12)
    crewman.touches = False
    self.assertClose(crewman.leapOf((0.0, 0.0, -G0)), (0.0, 0.0, 0.0), 0)

  def test_figure(self) -> None:
    """Up, his figure stands on his soles: every pivot over them, his
    head's 1.3 m up or more."""
    cockpit = Cockpit()
    cockpit.gotUp()
    soles = cockpit.crewman.soles()
    figure = cockpit.figureOf()
    self.assertEqual(len(figure), len(PARTS))
    for index, place, _ in figure:
      self.assertGreater(place[2], soles[2] - 1e-9, PARTS[index][0])
    head = [place for index, place, _ in figure
            if PARTS[index][0] == 'head']
    self.assertGreater(head[0][2] - soles[2], 1.3)
