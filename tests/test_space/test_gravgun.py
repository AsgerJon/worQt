"""
TestGravGun covers the Grav-Gun (user, 2026-11-17: "the official name is
'zero point energy field manipulator, if you really want to'. But
'gravgun' is the code name in the code and Grav-Gun is the public name.
All it does is that when aimed at an interactable object, right click
starts a force acting between the gun and its holder and the
interactable object that increases in magnitude with distance. Left
click sends a pulse of a greater force opposite of the right click";
2026-11-18: "gravgun pulls only when right click held, until the item is
picked up or the gun is near the bolt. Then the connection stays and
another rightclick releases it"): the field's pull on its holder toward
its target, 'PULL' a metre apart; the button let go, the field ends;
within 'NEAR' of the muzzle it holds, the button let go or not; held, a
loose thing is kept before the muzzle and a bolt keeps him at the length
he came to, each by a damped spring that never rings up however long a
frame; off, nothing; the pulse 'PUNT' times as hard the other way for
'PULSE' s, ending field and hold; it takes bolts and loose things alone.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.gaming.space._gravgun import HOLD, NEAR, PULL, PULSE, PUNT
from worQt.gaming.space._gravgun import GravGun
from worQt.gaming.space._inventory import ITEMS

from . import SpaceTest

#  Where the holder is, the way the gun points, how heavy he is.
HOME = (0.0, 0.0, 0.0)
AHEAD = (1.0, 0.0, 0.0)
STILL = (0.0, 0.0, 0.0)
HEFT = 80.0


class TestGravGun(SpaceTest):
  """Tests for the Grav-Gun."""

  def _pull(self, gun: GravGun, there: tuple, seconds: float = 0.1,
            moving: tuple = STILL, heft: float = HEFT) -> tuple:
    """Returns the gun's push on its holder (at 'HOME', the muzzle there
    too, pointing 'AHEAD'), what it acts on at 'there'."""
    return gun.pushOf(HOME, AHEAD, HOME, there, moving, heft, seconds)

  def test_named(self) -> None:
    """In the inventory it is the Grav-Gun ('gravgun' in the code)."""
    self.assertEqual(ITEMS['gravgun'][0], 'Grav-Gun')

  def test_field(self) -> None:
    """Its field pulls its holder toward its target, harder the further
    apart (in proportion); off, it pulls nothing."""
    gun = GravGun()
    self.assertEqual(self._pull(gun, (3.0, 0.0, 0.0)), STILL)
    gun.gripped(('bolt', 2))
    near = self._pull(gun, (2.0, 0.0, 0.0))
    far = gun.pushOf((1.0, 1.0, 1.0), AHEAD, (1.0, 1.0, 1.0),
                     (1.0, 5.0, 1.0), STILL, HEFT, 0.1)
    self.assertClose(near, (2.0 * PULL, 0.0, 0.0), 1e-12)
    self.assertClose(far, (0.0, 4.0 * PULL, 0.0), 1e-12)
    self.assertEqual(gun.acting, ('bolt', 2))
    self.assertFalse(gun.holding)
    gun.released()
    self.assertIsNone(gun.acting)

  def test_let_up(self) -> None:
    """The button let go before what it pulls is near, the field ends;
    let go once it holds, it holds on."""
    gun = GravGun()
    gun.gripped(('loose', 3))
    self._pull(gun, (5.0, 0.0, 0.0))
    self.assertTrue(gun.letUp())
    self.assertIsNone(gun.target)
    self.assertFalse(gun.letUp())
    gun.gripped(('loose', 3))
    self._pull(gun, (0.9 * NEAR, 0.0, 0.0))
    self.assertTrue(gun.holding)
    self.assertFalse(gun.letUp())
    self.assertEqual(gun.target, ('loose', 3))
    gun.released()
    self.assertFalse(gun.holding)

  def test_holds_near(self) -> None:
    """Within 'NEAR' of the muzzle it holds what it pulls, at the length
    it came to: a loose thing there before the muzzle, along the way it
    points (pushed back to it, the holder pulled after it); a bolt from
    his middle (a rod: pulled back to that length, the way it lies)."""
    gun = GravGun()
    gun.gripped(('loose', 0))
    self._pull(gun, (0.0, 0.8, 0.0), heft=0.3)
    self.assertAlmostEqual(gun.hold, 0.8, 12)
    push = self._pull(gun, (0.0, 0.8, 0.0), 1.0 / 60.0, heft=0.3)
    self.assertGreater(push[1], 0.0)
    self.assertLess(push[0], 0.0)
    rod = GravGun()
    rod.gripped(('bolt', 1))
    self._pull(rod, (0.0, 0.0, 0.9))
    pulled = self._pull(rod, (0.0, 0.0, 1.2), 1.0 / 60.0)
    pushed = self._pull(rod, (0.0, 0.0, 0.6), 1.0 / 60.0)
    self.assertGreater(pulled[2], 0.0)
    self.assertLess(pushed[2], 0.0)
    self.assertClose(pulled[:2], (0.0, 0.0), 1e-9)

  def test_settles(self) -> None:
    """Held, what it holds settles at its place and stays, however long
    the frames (the spring solved backward: it never rings up, never
    faster than its start's energy allows)."""
    for frame in (1.0 / 240.0, 1.0 / 60.0, 0.1, 0.5):
      gun = GravGun()
      gun.gripped(('loose', 0))
      self._pull(gun, (0.5, 0.0, 0.0), heft=0.3)
      place, moving = [0.9, 0.3, -0.2], [2.0, -3.0, 1.0]
      largest = 0.0
      for _ in range(int(4.0 / frame)):
        push = self._pull(gun, tuple(place), frame, tuple(moving), 0.3)
        for k in range(3):
          moving[k] -= push[k] / 0.3 * frame
          place[k] += moving[k] * frame
        largest = max(largest, math.hypot(*moving))
      self.assertLess(math.dist(place, (0.5, 0.0, 0.0)), 1e-3)
      self.assertLess(math.hypot(*moving), 1e-2)
      start = math.sqrt(14.0 + (HOLD * math.dist(
        (0.9, 0.3, -0.2), (0.5, 0.0, 0.0))) ** 2)
      self.assertLessEqual(largest, start)

  def test_pulse(self) -> None:
    """A pulse pushes the other way, 'PUNT' times the pull, for 'PULSE'
    s of frames, then nothing; it ends the field and the hold and is
    counted."""
    gun = GravGun()
    gun.gripped(('loose', 0))
    self._pull(gun, (0.5, 0.0, 0.0), heft=0.3)
    self.assertTrue(gun.holding)
    gun.punted(('loose', 0))
    self.assertIsNone(gun.target)
    self.assertFalse(gun.holding)
    self.assertEqual(gun.pulses, 1)
    pushes, frames = [], 0
    while gun.acting is not None:
      pushes.append(self._pull(gun, (2.0, 0.0, 0.0), 0.01))
      frames += 1
    self.assertEqual(frames, round(PULSE / 0.01))
    for push in pushes:
      self.assertClose(push, (-2.0 * PUNT * PULL, 0.0, 0.0), 1e-12)
    self.assertEqual(self._pull(gun, (2.0, 0.0, 0.0), 0.01), STILL)

  def test_aimed(self) -> None:
    """Up, the gun aims at the nearest loose thing his look passes
    within its round of, or within 'AIM' of (a mug far off is a speck):
    2 degrees off a mug 8 m away it is aimed at, 4 degrees off not."""
    from worQt.gaming.space._cockpit import AIM, Cockpit
    cockpit = Cockpit()
    cockpit.gotUp()
    eye, look = cockpit.eye(), cockpit.looking()[0]
    side = (-look[1], look[0], 0.0)
    size = math.hypot(*side)
    side = tuple(s / size for s in side)
    mug = (0.042, 0.042, 0.05)

    def at(far: float, degrees: float) -> tuple:
      a = math.radians(degrees)
      return tuple(e + far * (math.cos(a) * l + math.sin(a) * s)
                   for e, l, s in zip(eye, look, side))

    self.assertLess(math.radians(2.0), AIM)
    self.assertEqual(cockpit.looseAimed(((at(8.0, 2.0), mug),)), 0)
    self.assertIsNone(cockpit.looseAimed(((at(8.0, 4.0), mug),)))
    self.assertEqual(cockpit.looseAimed(((at(8.0, 1.0), mug),
                                         (at(3.0, 2.0), mug))), 1)

  def test_targets(self) -> None:
    """It takes a magic bolt or a loose thing by index, nothing else."""
    gun = GravGun()
    for bad in (('chair', 0), ('bolt', -1), ('loose', 1.5)):
      with self.assertRaises(ValueError):
        gun.gripped(bad)
