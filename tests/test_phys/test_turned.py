"""
TestTurned covers 'Turned', a solid turned on a lathe (its cross-section
spun about its own z axis), and 'outerRing', a bearing's outer ring with
a gothic arch groove. A plain ring's mass and moments are the formulas';
its drawn mesh is closed and nearly as large. The groove meets a ball at
the pitch circle on both flanks, at the contact angle either side. Held
upright, a ball in the groove at the bottom rests in the middle, pressed
outward m g / (2 k cos² a); rocked a little it swings with the period of
a ball rolling on its two contacts, 2 pi sqrt(rho (1 + 0.4 / cos² a) /
g); compiled (Warp) it runs as in plain Python. 'innerRing', the inner
ring to it, has the same groove facing out: closed, it meets a ball a
hair inside the pitch circle on both flanks at the contact angle.
'onShaft' presses an inner ring on a hollow shaft: closed, as much as
the ring and the tube together, and refused where the hole is no
narrower than the bore or the shaft does not reach through the ring.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Contact, HeldPose, Hexapod, Sphere
from worQt.phys import State, Turned, World, innerRing, nuInnerRing
from worQt.phys import nuOuterRing, onShaft, onShaftOf, outerRing
from worQt.phys import rollerOf, rollerShape
from worQt.phys import rotated
from worQt.phys import turnAbout

from . import PhysTest

G = 9.81
PITCH, BALL_SIZE, ANGLE, HUG = 20.0, 0.4, 120.0, 0.52
ALPHA = math.radians(90.0 - ANGLE / 2.0)
RING = Body.of(outerRing(PITCH, BALL_SIZE, ANGLE, HUG, 0.6, 0.5, 96), 7850.0)
BALL = Body.of(Sphere(BALL_SIZE / 2.0), 7850.0)
STIFF = 1e8
#  Steel on steel at this size: N/m at a point, s/m, grip, bristle N/m,
#  its damping N s/m.
STEEL = (STIFF, 0.5, 0.3, 1e8, 2e4)
#  The same with no grip: the geometry alone.
SLICK = (STIFF, 0.5, 0.0, 1e8, 2e4)
#  Upright: the ring's own z axis (its axle) along the world's -y.
UPRIGHT = turnAbout((1.0, 0.0, 0.0), 0.5 * math.pi)
HELD = HeldPose((0.0, 0.0, 0.0), UPRIGHT)
PLAIN = World((0.0, 0.0, -G), 1e-3, None, None, False)
COMPILED = World((0.0, 0.0, -G), 1e-3, None, None, True)


def inGroove(angle: float, radius: float) -> tuple:
  """The 'inGroove' function returns where a ball's middle is at
  'angle' (degrees, nought along x, -90 at the bottom) round the
  upright ring's axle, 'radius' from it."""
  a = math.radians(angle)
  return rotated(UPRIGHT, (radius * math.cos(a), radius * math.sin(a), 0.0))


def heldRing(angles: tuple[float, ...], law: tuple = STEEL) -> tuple:
  """The 'heldRing' function returns the ring held upright at the
  origin (its body first), a ball in its groove at each of 'angles' on
  the pitch circle, every ball touching the ring and each other by
  'law'; and how they start, still."""
  bodies = (RING,) + (BALL,) * len(angles)
  legs = Hexapod(1.0, 0.6, 20.0, 20.0, -11.0, 0.0).legs(RING, 0, HELD)
  count = len(bodies)
  contacts = tuple(Contact(a, b, *law) for a in range(count)
                   for b in range(max(a + 1, 1), count))
  states = (HELD.at(0.0).state(),) + tuple(
    State(inGroove(angle, PITCH / 2.0)) for angle in angles)
  return Assembly(bodies, legs + contacts), states


class TestTurned(PhysTest):
  """Tests for 'Turned' and 'outerRing'."""

  def test_plain_ring(self) -> None:
    """A ring of rectangular section, 1 to 1.5 m out and 0.4 m wide: its
    mass, and its moments about its axle and about a diameter, are the
    formulas'."""
    inner, outer, half = 1.0, 1.5, 0.2
    profile = (('line', (inner, -half), (outer, -half)),
               ('line', (outer, -half), (outer, half)),
               ('line', (outer, half), (inner, half)),
               ('line', (inner, half), (inner, -half)))
    body = Body.of(Turned(profile, 64), 1000.0)
    mass = 1000.0 * math.pi * (outer ** 2 - inner ** 2) * 2.0 * half
    self.assertAlmostEqual(body.mass / mass, 1.0, 12)
    axle = 0.5 * mass * (outer ** 2 + inner ** 2)
    across = mass * ((outer ** 2 + inner ** 2) / 4.0
                     + (2.0 * half) ** 2 / 12.0)
    self.assertAlmostEqual(body.inertia[2][2] / axle, 1.0, 12)
    self.assertAlmostEqual(body.inertia[0][0] / across, 1.0, 12)
    self.assertAlmostEqual(body.inertia[1][1] / across, 1.0, 12)
    self.assertNear(body.centre, (0.0, 0.0, 0.0), 1e-12)

  def test_mesh(self) -> None:
    """The outer ring's drawn mesh is closed, and as large as the ring
    within a percent (its sides are flat)."""
    mesh = RING.shape.mesh()
    self.assertTrue(mesh.isClosed())
    self.assertAlmostEqual(mesh.volume() / RING.shape.volume(), 1.0, 2)

  def test_groove(self) -> None:
    """A ball a hair outward of the pitch circle presses both flanks of
    the groove, at the contact angle either side of straight across the
    axle, as deep as the hair along their normals."""
    hair = 1e-8
    presses = RING.shape.presses(PITCH / 2.0 + hair, 0.0, BALL_SIZE / 2.0)
    self.assertEqual(len(presses), 2)
    ways = sorted((w, rho) for _, rho, w, _ in presses)
    self.assertNear(ways[0], (-math.sin(ALPHA), -math.cos(ALPHA)), 1e-5)
    self.assertNear(ways[1], (math.sin(ALPHA), -math.cos(ALPHA)), 1e-5)
    for _, _, _, depth in presses:
      self.assertAlmostEqual(depth / (hair * math.cos(ALPHA)), 1.0, 3)

  def test_rests_in_the_middle(self) -> None:
    """At the bottom of the ring held upright a ball with no grip
    rests in the middle of the groove, pressed outward m g / (2 k cos²
    a) by its weight on the two flanks (with grip, the flanks would hold
    some of it up as it settled, a wedge's friction)."""
    assembly, states = heldRing((-90.0,), SLICK)
    states = COMPILED.advancedAll(assembly, states, 3.0)
    x, y, z = states[1].place
    self.assertAlmostEqual(y, 0.0, 7)
    pressed = BALL.mass * G / (2.0 * STIFF * math.cos(ALPHA) ** 2)
    self.assertAlmostEqual((-z - PITCH / 2.0) / pressed, 1.0, 2)

  def test_swings(self) -> None:
    """Let go 3 degrees up the groove it rolls back and forth with the
    period of a ball rolling on its two contacts at the contact angle,
    2 pi sqrt(rho (1 + 0.4 / cos² a) / g): let go at rest at the end of
    its swing, it is next moving back the way it first went one period
    later."""
    assembly, states = heldRing((-93.0,))
    period, before, time = None, None, 0.0
    while period is None and time < 10.0:
      states = COMPILED.advancedAll(assembly, states, 0.01, time)
      time += 0.01
      along = states[1].velocity[0]
      if before is not None and before < 0.0 <= along:
        period = time
      before = along
    self.assertIsNotNone(period)
    rho = PITCH / 2.0
    expected = 2.0 * math.pi * math.sqrt(
      rho * (1.0 + 0.4 / math.cos(ALPHA) ** 2) / G)
    self.assertAlmostEqual(period / expected, 1.0, 2)

  def test_compiled(self) -> None:
    """Two balls in the groove of the ring held upright, one rolling at
    the other: compiled as in plain Python."""
    assembly, states = heldRing((-95.0, -90.0))
    moving = State(states[1].place, (1.0, 0.0, 0.0, 0.0), (1.0, 0.0, -0.1))
    states = (states[0], moving, states[2])
    plain = PLAIN.advancedAll(assembly, states, 0.3)
    compiled = COMPILED.advancedAll(assembly, states, 0.3)
    for one, other in zip(plain[1:], compiled[1:]):
      self.assertNear(other.place, one.place, 1e-10)
      self.assertNear(other.velocity, one.velocity, 1e-8)

  def test_inner_groove(self) -> None:
    """The inner ring is closed, its mesh as large within a percent; a
    ball a hair inside the pitch circle presses both its flanks, at the
    contact angle either side, outward, as deep as the hair along their
    normals."""
    inner = innerRing(PITCH, BALL_SIZE, ANGLE, HUG, 0.6, 0.5, 96)
    self.assertTrue(inner.isClosed())
    self.assertAlmostEqual(inner.mesh().volume() / inner.volume(), 1.0, 2)
    hair = 1e-8
    presses = inner.presses(PITCH / 2.0 - hair, 0.0, BALL_SIZE / 2.0)
    self.assertEqual(len(presses), 2)
    ways = sorted((w, rho) for _, rho, w, _ in presses)
    self.assertNear(ways[0], (-math.sin(ALPHA), math.cos(ALPHA)), 1e-5)
    self.assertNear(ways[1], (math.sin(ALPHA), math.cos(ALPHA)), 1e-5)
    for _, _, _, depth in presses:
      self.assertAlmostEqual(depth / (hair * math.cos(ALPHA)), 1.0, 3)

  def test_on_shaft(self) -> None:
    """An inner ring pressed on a hollow shaft is closed, as much as the
    ring and the tube (from the hole out to the bore, front to back)
    together; a hole as wide as the bore, or a shaft ending inside the
    ring, is refused."""
    ring = innerRing(PITCH, BALL_SIZE, ANGLE, HUG, 0.6, 0.5, 96)
    bore, half = ring.bounds()[0], 0.3
    shaft = onShaft(ring, 0.8 * bore, 1.0, 2.0)
    self.assertTrue(shaft.isClosed())
    tube = math.pi * bore * bore * (1.0 - 0.64) * 3.0
    self.assertAlmostEqual(shaft.volume() / (ring.volume() + tube), 1.0,
                           12)
    with self.assertRaises(ValueError):
      onShaft(ring, bore, 1.0, 2.0)
    with self.assertRaises(ValueError):
      onShaft(ring, 0.8 * bore, 0.5 * half, 2.0)

  def test_on_shaft_of(self) -> None:
    """Two different inner rings (a ball bearing's and an NU's plain
    one, their bores alike) pressed on one shaft are as much as both
    rings and the tube between; rings of different bores are refused;
    the same ring twice is 'onShaft's shaft."""
    ring = innerRing(PITCH, BALL_SIZE, ANGLE, HUG, 0.6, 0.5, 96)
    bore = ring.bounds()[0]
    plain = nuInnerRing(PITCH, BALL_SIZE, 0.0, 0.6, bore, 96)
    shaft = onShaftOf((ring, plain), 0.8 * bore, 3.0, 2.0, (0.0, 1.5))
    tube = math.pi * bore * bore * (1.0 - 0.64) * 5.0
    self.assertAlmostEqual(shaft.volume() / (ring.volume()
                                             + plain.volume() + tube),
                           1.0, 12)
    other = nuInnerRing(PITCH, BALL_SIZE, 0.0, 0.6, 0.9 * bore, 96)
    with self.assertRaises(ValueError):
      onShaftOf((ring, other), 0.8 * bore, 3.0, 2.0, (0.0, 1.5))
    self.assertEqual(onShaftOf((ring, ring), 0.8 * bore, 3.0, 2.0,
                               (0.0, 1.5)),
                     onShaft(ring, 0.8 * bore, 3.0, 2.0, (0.0, 1.5)))

  def test_roller(self) -> None:
    """A roller is a solid cylinder turned from its axis, as much as
    pi r² L, its middle at its centre; 'rollerOf' reads back its radius
    and half length, and None for a ring or a ball's shape."""
    roller = rollerShape(0.4, 1.0, 64)
    self.assertAlmostEqual(roller.volume() / (math.pi * 0.04), 1.0, 12)
    self.assertNear(roller.centre(), (0.0, 0.0, 0.0), 1e-12)
    self.assertEqual(rollerOf(roller), (0.2, 0.5))
    self.assertIsNone(rollerOf(innerRing(PITCH, BALL_SIZE, ANGLE, HUG,
                                         0.6, 0.5, 96)))
    self.assertIsNone(rollerOf(Sphere(1.0)))

  def test_nu_rings(self) -> None:
    """An NU bearing's rings: the outer's raceway 'play' outside the
    rollers between two ribs reaching in, as much as its ring less the
    groove between the ribs; the inner a plain cylinder 'play' inside
    them, as much as a tube; rings that cannot hold their rollers are
    refused."""
    pitch, roller, play, width = 4.0, 1.0, 0.01, 1.6
    outer = nuOuterRing(pitch, roller, play, width, 3.5, 0.2, 0.2, 96)
    race = 0.5 * pitch + 0.5 * roller + play
    low, high, bottom, top = outer.bounds()
    self.assertAlmostEqual(low, race - 0.2, 12)
    self.assertAlmostEqual(high, 3.5, 12)
    self.assertAlmostEqual(top - bottom, width, 12)
    whole = math.pi * (3.5 ** 2 - (race - 0.2) ** 2) * width
    groove = math.pi * (race ** 2 - (race - 0.2) ** 2) * (width - 0.4)
    self.assertAlmostEqual(outer.volume() / (whole - groove), 1.0, 12)
    inner = nuInnerRing(pitch, roller, play, width, 1.0, 96)
    outside = 0.5 * pitch - 0.5 * roller - play
    self.assertAlmostEqual(inner.bounds()[1], outside, 12)
    self.assertAlmostEqual(inner.volume() / (
      math.pi * (outside ** 2 - 1.0) * width), 1.0, 12)
    with self.assertRaises(ValueError):
      nuOuterRing(pitch, roller, play, width, 3.5, 2.0, 0.2, 96)
    with self.assertRaises(ValueError):
      nuInnerRing(pitch, roller, play, width, 2.0, 96)
