"""
TestPoke covers poking a body: 'hitOf' finds the nearest body a ray
meets and where, with the surface's outward normal there (a box's face,
a ball's round side, a turned ring, looked at side by side, where its
whole mesh says), passing over the bodies it is told to; 'poked' gives
a body an impulse at a point: its velocity changes by the impulse over
its mass, its spin by the twist about its centre through its inertia,
and it wakes. 'motorTorque' falls straight from the stall torque
standing to nought at the free speed, brakes past it, and is cut at
twice the stall torque; 'rotorSpinOf' is how fast a motor's rotor turns
on its housing about its axis; 'runMotor' sets a drive to twist so at
every step: a wheel on such a motor, free, runs up to its free speed,
and let go of, coasts.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Sphere, State, boxShape, cross
from worQt.phys import Drive, Motor, World, hitOf, motorTorque, outerRing
from worQt.phys import poked, rotorSpinOf, runMotor, solved, turnAbout

from . import PhysTest

BOX = Body.of(boxShape(0.4, 0.3, 0.2), 1000.0)
BALL = Body.of(Sphere(0.1), 1000.0)
RING = Body.of(outerRing(20.0, 0.4, 120.0, 0.52, 0.6, 0.5, 72), 7850.0)


class TestPoke(PhysTest):
  """Tests for 'hitOf' and 'poked'."""

  def test_box_face(self) -> None:
    """A ray along x from far off meets the box's near face, its
    normal facing back along the ray."""
    assembly = Assembly((BOX,))
    hit = hitOf(assembly, (State((0.0, 0.0, 0.0)),), (-2.0, 0.05, 0.02),
                (1.0, 0.0, 0.0), ())
    self.assertIsNotNone(hit)
    index, point, normal = hit
    self.assertEqual(index, 0)
    self.assertNear(point, (-0.2, 0.05, 0.02), 1e-12)
    self.assertNear(normal, (-1.0, 0.0, 0.0), 1e-12)

  def test_miss(self) -> None:
    """A ray passing by meets nothing."""
    assembly = Assembly((BOX,))
    hit = hitOf(assembly, (State((0.0, 0.0, 0.0)),), (-2.0, 1.0, 0.0),
                (1.0, 0.0, 0.0), ())
    self.assertIsNone(hit)

  def test_ball(self) -> None:
    """A ray straight down meets a ball on its top, its normal up."""
    assembly = Assembly((BALL,))
    hit = hitOf(assembly, (State((0.3, 0.0, 0.5)),), (0.3, 0.0, 2.0),
                (0.0, 0.0, -1.0), ())
    self.assertNear(hit[1], (0.3, 0.0, 0.6), 1e-12)
    self.assertNear(hit[2], (0.0, 0.0, 1.0), 1e-12)

  def test_nearest_and_passed_over(self) -> None:
    """With a ball in front of the box the ball is met; told to pass
    over the ball, the box is."""
    assembly = Assembly((BOX, BALL))
    states = (State((0.0, 0.0, 0.0)), State((-0.6, 0.0, 0.0)))
    hit = hitOf(assembly, states, (-2.0, 0.0, 0.0), (1.0, 0.0, 0.0), ())
    self.assertEqual(hit[0], 1)
    self.assertNear(hit[1], (-0.7, 0.0, 0.0), 1e-12)
    hit = hitOf(assembly, states, (-2.0, 0.0, 0.0), (1.0, 0.0, 0.0), (1,))
    self.assertEqual(hit[0], 0)

  def test_poked_through_the_centre(self) -> None:
    """Pushed through its centre it moves off at the impulse over its
    mass and does not turn."""
    state = poked(BOX, State((0.0, 0.0, 0.0)), (-0.2, 0.0, 0.0),
                  (2.0, 0.0, 0.0))
    self.assertNear(state.velocity, (2.0 / BOX.mass, 0.0, 0.0), 1e-15)
    self.assertNear(state.spin, (0.0, 0.0, 0.0), 1e-15)
    self.assertEqual(state.rest, 0.0)

  def test_poked_off_centre(self) -> None:
    """Pushed off its centre it also turns: its spin changes by its
    inertia's inverse times the twist about its centre."""
    point, impulse = (-0.2, 0.1, 0.0), (2.0, 0.0, 0.0)
    resting = State((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                    (0.0, 0.0, 0.0), (), (), 0.5)
    state = poked(BOX, resting, point, impulse)
    twist = cross(point, impulse)
    spin = solved([list(row) for row in BOX.inertia], list(twist))
    self.assertNear(state.spin, tuple(spin), 1e-12)
    self.assertEqual(state.rest, 0.0)

  def test_turned_ring(self) -> None:
    """Rays at the outer ring standing upright (turned and moved), into
    its groove, its bore, its outside and past it: each meets it where
    its whole mesh, every face looked at, says, the normal alike."""
    turned = State((1.0, 2.0, 10.6), turnAbout((1.0, 0.0, 0.0),
                                               0.5 * math.pi))
    mesh = Body(RING.mass, RING.centre, RING.inertia, RING.shape.mesh())
    rays = (((1.3, -6.0, 0.35), (0.0, 1.0, 0.0)),
            ((1.0, 2.1, 5.0), (0.05, 0.0, -1.0)),
            ((-14.0, 2.1, 10.0), (1.0, 0.0, 0.03)),
            ((1.0, -6.0, 0.5), (0.1, 1.0, 0.0)),
            ((25.0, 2.0, 10.6), (1.0, 0.0, 0.0)))
    for eye, way in rays:
      sides = hitOf(Assembly((RING,)), (turned,), eye, way, ())
      whole = hitOf(Assembly((mesh,)), (turned,), eye, way, ())
      if whole is None:
        self.assertIsNone(sides)
        continue
      self.assertIsNotNone(sides)
      self.assertNear(sides[1], whole[1], 1e-9)
      self.assertNear(sides[2], whole[2], 1e-9)

  def test_motor_torque(self) -> None:
    """Standing a motor twists at its stall torque, at half its free
    speed half that, at its free speed not at all, past it it brakes,
    turned backwards harder, and never harder either way than twice its
    stall torque."""
    for spin, torque in ((0.0, 2.0), (2.5, 1.0), (5.0, 0.0), (7.5, -1.0),
                         (-2.5, 3.0), (-50.0, 4.0), (50.0, -4.0)):
      self.assertAlmostEqual(motorTorque(2.0, 5.0, spin), torque, 12)

  def test_rotor_spin(self) -> None:
    """A rotor turned a quarter about x (its axis its own z, so the
    world's -y) spinning 3 rad/s about -y and 1 about x, its housing 0.5
    about -y, turns 2.5 rad/s on its housing; with no housing (the
    world), 3."""
    rotor = State((0.0, 0.0, 0.0), turnAbout((1.0, 0.0, 0.0),
                                             0.5 * math.pi),
                  (0.0, 0.0, 0.0), (1.0, -3.0, 0.0))
    housing = State((0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), (0.0, 0.0, 0.0),
                    (0.0, -0.5, 0.0))
    motor = Motor(0, 1, (0.0, 0.0, 1.0), Drive())
    self.assertAlmostEqual(rotorSpinOf(motor, (housing, rotor)), 2.5, 12)
    alone = Motor(None, 0, (0.0, 0.0, 1.0), Drive())
    self.assertAlmostEqual(rotorSpinOf(alone, (rotor,)), 3.0, 12)

  def test_run_motor(self) -> None:
    """A steel disc on a motor of 0.5 N m standing and 10 rad/s free,
    run 10 of its time constants (its moment times the free speed over
    the stall torque) turns at its free speed (to a thousandth); let go
    of ('on' False), the drive twists nought and the disc coasts on."""
    disc = Body.of(boxShape(0.2, 0.2, 0.02), 7850.0)
    drive = Drive()
    runMotor(drive, 0.5, 10.0, True)
    self.assertEqual((drive.torque, drive.damping, drive.most),
                     (0.5, 0.05, 1.0))
    assembly = Assembly((disc,), (Motor(None, 0, (0.0, 0.0, 1.0), drive),))
    world = World((0.0, 0.0, 0.0), 1e-3, None)
    lasting = disc.inertia[2][2] * 10.0 / 0.5
    state = world.advancedAll(assembly, (State((0.0, 0.0, 0.0)),),
                              10.0 * lasting)[0]
    self.assertAlmostEqual(state.spin[2] / 10.0, 1.0, 3)
    runMotor(drive, 0.5, 10.0, False)
    self.assertEqual((drive.torque, drive.damping, drive.most),
                     (0.0, 0.0, 0.0))
    coasted = world.advancedAll(assembly, (state,), lasting)[0]
    self.assertAlmostEqual(coasted.spin[2], state.spin[2], 9)
