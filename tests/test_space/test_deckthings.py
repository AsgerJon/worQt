"""
TestDeckThings covers the loose furnishings on Terra Prime's deck at the
foot of each terminal's stairs (user, 2026-11-19: "we need to put some
furnishings *with* physics at the end of the spokes"): each rests on
the deck, its axes a turn (a mirror's turn garbled the cage's plates
and these, 2026-11-19); laid into the docked rocket's axes and taken
back they are where they were; docked, the station's turn alone holds
them on the deck, still.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.gaming.space._accelerometer import Accelerometer
from worQt.gaming.space._cabinworld import CabinWorld
from worQt.gaming.space._cockpit import Cockpit
from worQt.gaming.space._deckthings import TELEPORTED, DeckThings
from worQt.gaming.space._deckthings import deckThings, deckWorldThings
from worQt.gaming.space._station import SPIN
from worQt.gaming.space._stationinterior import DECK, shaftWays
from worQt.gaming.space._terminal import terminalSolids

from . import FRAME, SpaceTest

#  Asger's legs at rest (he sits in his chair: not in this world).
STILL = ((0.0, 0.0, 0.0), 0, 0, (0.0, 0.0, 0.0))
#  How high over the deck each is let go, m.
LIFT = 0.03


class TestDeckThings(SpaceTest):
  """Tests for the deck's loose furnishings."""

  #  The cabin's kernels on the CPU.
  __time_out__ = 900.0

  def test_rest(self) -> None:
    """Each furnishing at rest stands on the deck (its bottom within 3 mm
    of it), its axes a turn (determinant one), its up toward the
    station's axis."""
    for name, _, middle, half, axes, _ in deckThings():
      self.assertAlmostEqual(numpy.linalg.det(numpy.array(axes)), 1.0, 9,
                             name)
      out = math.hypot(middle[0], middle[1])
      self.assertAlmostEqual(out + half[2], DECK, delta=0.003)
      inward = (-middle[0] / out, -middle[1] / out, 0.0)
      self.assertAlmostEqual(sum(a * b for a, b in zip(axes[2], inward)),
                             1.0, 9, name)

  def test_kept(self) -> None:
    """Laid into the docked rocket's axes and taken back, each is where
    it was, turned as it was."""
    deck = DeckThings()
    places = numpy.array(deck.places)
    turns = numpy.array(deck.turns)
    deck.kept(deck.laid(TELEPORTED), TELEPORTED)
    self.assertLess(numpy.abs(numpy.array(deck.places) - places).max(),
                    1e-9)
    alike = numpy.abs((numpy.array(deck.turns) * turns).sum(1))
    self.assertGreater(alike.min(), 1.0 - 1e-9)

  def test_settled(self) -> None:
    """Docked, each let go 'LIFT' m over the deck, the station's turn
    alone pulls it down onto it: after a second and a half each is
    within 1 cm of where it rests, turned under a degree, still (under 3
    mm over the last quarter second: the velocity read back carries the
    last step's pull, ~2 cm/s, which the next step's contact takes)."""
    things = deckWorldThings()
    world = CabinWorld('cpu', things)
    rest = DeckThings().laid(TELEPORTED)
    lifted = []
    for place, turn in rest:
      across = math.hypot(place[0], place[1])
      share = (across - LIFT) / across
      lifted.append(((place[0] * share, place[1] * share, place[2]), turn))
    world.bodiesPlaced(0, tuple(lifted), tuple(
      thing[4] for thing in things))
    ways = shaftWays(TELEPORTED)
    world.stationed(True, ways, terminalSolids(TELEPORTED))
    meter = Accelerometer()
    meter.felt, meter.turning = (0.0, 0.0, 0.0), (0.0, 0.0, -SPIN)
    meter.speeding = (0.0, 0.0, 0.0)
    crewman = Cockpit().crewman
    for _ in range(int(round(1.25 / FRAME))):
      world.stepped(FRAME, meter, crewman, STILL)
    before = numpy.array([place for place, _ in world.shown()])
    for _ in range(int(round(0.25 / FRAME))):
      world.stepped(FRAME, meter, crewman, STILL)
    for (name, *_), (was, turned), (now, turn) in zip(things, rest,
                                                      world.shown()):
      self.assertLess(math.dist(was, now), 0.01, name)
      alike = abs(sum(a * b for a, b in zip(turned, turn)))
      angle = 2.0 * math.acos(min(1.0, alike))
      self.assertLess(angle, math.radians(1.0), name)
    after = numpy.array([place for place, _ in world.shown()])
    self.assertLess(numpy.linalg.norm(after - before, axis=1).max(),
                    0.003)
