"""
TestMinecart covers the loop's minecart ('Minecart', a 'Vehicle'): it
waits on the start platform, standing, each axlebox carrying its share
of the body (by the lever, its centre of mass a little behind the
middle); the body meets what is spawned but not the track; the avatar
boards it; punted toward the edge with the avatar in it, it rolls over
and down the grade, the rider tied in the seat, the eyes' up tilting
with the cart, rumbling (its speed, its wheels' load near its weight,
the flanges' share) and reading its speed; pushed back it stops at the
buffer stop past the track's start, its back end at the buffer (user,
2026-11-16, previews/wiley_coyote_lol.png: it rolled off the open
end); fallen out of the world with its rider, the rider is set back
where it entered and the cart where it was put. Shoved off the rails
sideways (user, 2026-11-16: "derail shouldn't mean RuntimeError!") it
derails: its wheelsets free bodies of the world held in its boxes by
springs, its body meeting the track, the world stepping on, the wreck
on the platform; put back, it is as it was made. Its brake lever (a
'FourthPeep' among the world's) pulled, a shove back stops within a
metre (released, it rolls on to the buffer), its menu saying so.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys._assembly import Contact
from worQt.phys._poke import poked

from worQt.phys._assembly import Spring
from worQt.phys.rail import Axlebox, wheelsetBody

from worQt.gaming.trains import Minecart
from worQt.gaming.trains._loopworld import MINECART_AT
from worQt.gaming.trains._minecart import HALF_BASE, offRailsBody

from . import TrainsTest


class TestMinecart(TrainsTest):
  """Tests for the minecart (seconds)."""

  #  The loop world on the CPU, a wreck among it: slow.
  __time_out__ = 90.0

  def boarded(self, ) -> tuple:
    """Returns the loop's world, its avatar seated in its minecart."""
    world, avatar = self.loopWorld()
    cart = world.vehicles[0]
    states = list(world.states)
    tub = states[cart.frame].place
    states[avatar.index] = type(states[avatar.index])(
      (tub[0] - 2.5, 2.5, states[avatar.index].place[2]))
    world.states = tuple(states)
    self.ran(world, 0.2)
    eye, _ = avatar.eyes(world.states[avatar.index])
    avatar.yaw = math.atan2(tub[1] - eye[1], tub[0] - eye[0])
    avatar.pitch = math.atan2(tub[2] - eye[2], math.hypot(
      tub[0] - eye[0], tub[1] - eye[1]))
    avatar.pressed('e')
    self.ran(world, 0.1)
    return world, avatar, cart

  def test_waits(self) -> None:
    """On the start platform it stands, each box carrying its share of
    the body by the lever."""
    world, _ = self.loopWorld()
    cart = world.vehicles[0]
    self.assertIsInstance(cart, Minecart)
    body = world.assembly.bodies[cart.frame]
    self.assertAlmostEqual(world.states[cart.frame].place[0],
                           MINECART_AT + body.centre[0], 2)
    self.ran(world, 1.0)
    tub = world.states[cart.frame]
    self.assertLess(math.sqrt(sum(v * v for v in tub.velocity)), 0.02)
    for box in cart.boxes:
      way = 1.0 if box.box[0] > 0.0 else -1.0
      share = 0.25 * (1.0 + way * body.centre[0] / HALF_BASE) * (
        body.mass * 9.81)
      with self.subTest(side=box.side, wheelset=box.wheelset):
        self.assertAlmostEqual(world.solver.boxLoads[id(box)], share,
                               None, None, 0.02 * share)

  def test_touches(self) -> None:
    """The tub meets the avatar and the buffer stops, not the track's
    pieces or the island."""
    world, avatar = self.loopWorld()
    tub = world.vehicles[0].frame
    met = {c.first if c.second == tub else c.second
           for c in world.assembly.connections
           if isinstance(c, Contact) and tub in (c.first, c.second)}
    self.assertIn(avatar.index, met)
    self.assertEqual(met & world.still, set(world.buffers))

  def test_rides_over(self) -> None:
    """Boarded and punted toward the edge it rolls over and down the
    grade, the rider tied in the seat, the eyes' up tilting with it."""
    world, avatar, cart = self.boarded()
    self.assertIs(avatar.riding, cart)
    states = list(world.states)
    body = world.assembly.bodies[cart.frame]
    states[cart.frame] = poked(body, states[cart.frame],
                               states[cart.frame].place,
                               (4.0 * body.mass, 0.0, 0.0))
    world.states = tuple(states)
    top = world.states[cart.frame].place[2]
    self.ran(world, 7.0)
    tub = world.states[cart.frame]
    self.assertLess(tub.place[2], top - 2.0)
    seat = body.placeOf(tub, cart.seat)
    self.assertLess(math.dist(world.states[avatar.index].place, seat),
                    0.01)
    self.assertGreater(avatar.up()[0], 0.2)
    speed, load, flange = cart.rumble(world.states)
    self.assertGreater(speed, 2.0)
    self.assertGreater(load, 0.5)
    self.assertLess(load, 2.0)
    self.assertGreaterEqual(flange, 0.0)
    self.assertLessEqual(flange, 1.0)
    self.assertIn('km/h', cart.readout(world.states))

  def test_buffered(self) -> None:
    """Pushed back at ~1.2 m/s it rolls to the start's buffer stop, its
    back end meeting the buffer, and stays on the track, coming off it
    slowly (the body stops at the buffer, its wheelsets go on into their
    axleboxes' rubber, which hands them back)."""
    world, avatar = self.loopWorld()
    cart = world.vehicles[0]
    states = list(world.states)
    body = world.assembly.bodies[cart.frame]
    states[cart.frame] = poked(body, states[cart.frame],
                               states[cart.frame].place,
                               (-6.0 * body.mass, 0.0, 0.0))
    world.states = tuple(states)
    nearest = math.inf
    for _ in range(12):
      self.ran(world, 0.5)
      nearest = min(nearest, world.states[cart.frame].place[0])
    tub = world.states[cart.frame]
    back = -min(point[0] for point in body.shape.points)
    self.assertAlmostEqual(nearest, back + body.centre[0], None, None,
                           0.1)
    self.assertLess(abs(tub.velocity[0]), 0.3)
    self.assertGreater(tub.place[2], 29.0)

  def test_fallen_back(self) -> None:
    """Fallen below the world's 'lowest' with its rider, the rider is
    set back where it entered, the cart where it was put."""
    world, avatar, cart = self.boarded()
    placed = world.placings[id(cart)]
    states = list(world.states)
    for index in cart.bodies + (avatar.index,):
      state = states[index]
      states[index] = type(state)((state.place[0], state.place[1],
                                   world.lowest - 5.0), state.turn)
    world.states = tuple(states)
    self.ran(world, 0.2)
    self.assertIsNone(avatar.riding)
    self.assertAlmostEqual(world.states[avatar.index].place[2],
                           avatar.entered.place[2], 1)
    self.assertAlmostEqual(world.states[cart.frame].place[2],
                           placed[cart.frame].place[2], 1)

  def test_derails(self) -> None:
    """Shoved sideways off the rails it derails: its wheelsets free
    bodies held by springs, no axleboxes, the world stepping on, the
    wreck on the platform; put back, it is as it was made."""
    world, avatar = self.loopWorld()
    cart = world.vehicles[0]
    self.ran(world, 0.2)
    made = world.assembly.connections
    body = world.assembly.bodies[cart.frame]
    states = list(world.states)
    frame = states[cart.frame]
    states[cart.frame] = poked(body, frame, body.placeOf(
      frame, (0.0, 0.0, 0.9)), (0.0, -14.0 * body.mass, 0.0))
    world.states = tuple(states)
    self.ran(world, 1.0)
    self.assertEqual(sorted(cart.off), list(cart.bodies[1:]))
    for index in cart.bodies[1:]:
      self.assertIs(world.assembly.bodies[index], offRailsBody())
    connections = world.assembly.connections
    self.assertFalse([c for c in connections if isinstance(c, Axlebox)])
    self.assertEqual(len([c for c in connections
                          if isinstance(c, Spring)]), 4)
    self.assertIsNone(world.trouble)
    self.assertGreater(world.states[cart.frame].place[2], 29.5)
    cart.restored()
    for index in cart.bodies[1:]:
      self.assertIs(world.assembly.bodies[index], wheelsetBody())
    self.assertEqual(sorted(map(id, world.assembly.connections)),
                     sorted(map(id, made)))
    self.assertEqual(cart.off, {})

  def test_brakes(self) -> None:
    """Its lever pulled, shoved back at 1.5 m/s it stops within a metre;
    released, the same shove rolls it on (over a metre in a second);
    its menu says how far the brake is pulled."""
    for pulled in (True, False):
      with self.subTest(pulled=pulled):
        world, _ = self.loopWorld()
        cart = world.vehicles[0]
        self.assertIn(cart.lever, world.peeps)
        if pulled:
          cart.lever.used()
        self.ran(world, 0.4)
        self.assertEqual(cart.lever.value, 1.0 if pulled else 0.0)
        states = list(world.states)
        mass = sum(world.assembly.bodies[i].mass for i in cart.bodies)
        body = world.assembly.bodies[cart.frame]
        frame = states[cart.frame]
        states[cart.frame] = poked(body, frame, frame.place,
                                   (-1.5 * mass, 0.0, 0.0))
        world.states = tuple(states)
        was = world.states[cart.frame].place[0]
        self.ran(world, 1.0)
        moved = was - world.states[cart.frame].place[0]
        if pulled:
          self.assertLess(moved, 1.0)
          self.assertLess(abs(world.states[cart.frame].velocity[0]), 0.1)
          self.assertIn('brake 100 %', cart.readout(world.states))
        else:
          self.assertGreater(moved, 1.0)
          self.assertIn('brake 0 %', cart.readout(world.states))
