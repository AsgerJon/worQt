"""
TestRibbon covers the track as a ribbon ('rail._ribbon', the spec
"Trains: the math first", Track geometry): a circle drawn by one
constant pitch lies on its circle and its frame comes back to itself;
a loop drifts as it says, its frame back as it was; a loop eased in
and out (user, 2026-11-16: the wheels hopped at the loop's exit) turns
its rates up from nought and back with no step, its frame back as it
was exactly, its way out beside its way in, no taller than a few
decimetres over the plain loop; a clothoid ends
turned by the integral of its curvature and lies where Fresnel's
integrals put it; an easing that twists and pitches at once (rates off
one axis) matches a fine integration (Magnus' commutator term); the
frame stays square everywhere; what a vehicle feels ('feltAt') is the
centre line differentiated twice, less gravity; at a loop's top it is
V^2/R - g. And the loop's stage ('rail._stage'): it falls 'DROP' m to
the loop's foot, climbs to 'CLIMB', its loop clears its own ways in and
out, and k = 0.315 wants 26.6 m of drop for its loop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import numpy

from worQt.phys.rail import GRAVITY, LEVEL, Ribbon, bend, eased
from worQt.phys.rail import easedLoop, loop, straight
from worQt.phys.rail import loopSpan, loopTrack
from worQt.phys.rail import _stage

from . import PhysTest

#  The loop's radius and drift tried, m.
RADIUS, DRIFT = 10.0, 3.0


def _square(frame: numpy.ndarray) -> float:
  """Returns how far 'frame' is from a proper rotation."""
  return float(numpy.abs(frame.T @ frame - numpy.eye(3)).max()
               + abs(numpy.linalg.det(frame) - 1.0))


class TestRibbon(PhysTest):
  """Tests for the ribbon and the loop's stage (seconds)."""

  def test_circle(self) -> None:
    """One whole turn up at 1/R: every point on the circle about (0, 0,
    R), the frame's z toward its middle, back to itself at the end."""
    ribbon = Ribbon((bend(2.0 * math.pi, RADIUS, (0.0, -1.0, 0.0)),))
    middle = numpy.array((0.0, 0.0, RADIUS))
    for s in numpy.linspace(0.0, ribbon.length, 37):
      place, frame = ribbon.frameAt(s)
      self.assertNear(float(numpy.linalg.norm(place - middle)), RADIUS,
                      1e-12)
      inward = (middle - place) / RADIUS
      self.assertNear(float(frame[:, 2] @ inward), 1.0, 1e-12)
      self.assertLess(_square(frame), 1e-12)
    place, frame = ribbon.frameAt(ribbon.length)
    self.assertLess(float(numpy.abs(place).max()), 1e-12)
    self.assertLess(float(numpy.abs(frame - numpy.eye(3)).max()), 1e-12)

  def test_loop(self) -> None:
    """A loop drifting 3 m: its frame back as it was, its way out
    'DRIFT' m from its way in along its axis, nearly all of it to the
    left; its length the helix's."""
    piece = loop(RADIUS, DRIFT)
    ribbon = Ribbon((piece,))
    place, frame = ribbon.frameAt(ribbon.length)
    self.assertLess(float(numpy.abs(frame - numpy.eye(3)).max()), 1e-12)
    self.assertNear(float(numpy.linalg.norm(place)), DRIFT, 1e-12)
    pitch = DRIFT / (2.0 * math.pi)
    self.assertNear(float(place[1]), DRIFT * RADIUS / math.hypot(
      RADIUS, pitch), 1e-12)
    self.assertNear(piece.length, 2.0 * math.pi * math.hypot(RADIUS, pitch),
                    1e-12)
    highest = max(float(ribbon.frameAt(s)[0][2])
                  for s in numpy.linspace(0.0, ribbon.length, 721))
    self.assertNear(highest, 2.0 * RADIUS, 1e-3)

  def test_eased_loop(self) -> None:
    """Eased over 8 m: its rates nought at either end and the helix's
    between, with no step; one whole turn, the frame back as it was to
    1e-9; its way out level with its way in, 2.5 to 3 m to the left
    and further on; its top under 0.5 m over the plain loop's; easing
    over nothing, or over more than the loop, refused."""
    pieces = easedLoop(RADIUS, DRIFT, 8.0)
    self.assertEqual(len(pieces), 3)
    self.assertEqual(pieces[0].start, LEVEL)
    self.assertEqual(pieces[2].end, LEVEL)
    self.assertEqual(pieces[0].end, pieces[1].start)
    self.assertEqual(pieces[1].end, pieces[2].start)
    ribbon = Ribbon((straight(1.0),) + pieces + (straight(1.0),))
    place, frame = ribbon.frameAt(ribbon.length)
    self.assertLess(float(numpy.abs(frame - numpy.eye(3)).max()), 1e-9)
    self.assertLess(abs(float(place[2])), 1e-9)
    self.assertGreater(float(place[1]), 2.5)
    self.assertLess(float(place[1]), DRIFT)
    self.assertGreater(float(place[0]), 2.0)
    top = max(float(ribbon.frameAt(s)[0][2])
              for s in numpy.linspace(0.0, ribbon.length, 2000))
    self.assertGreater(top, 2.0 * RADIUS)
    self.assertLess(top, 2.0 * RADIUS + 0.5)
    for ease in (0.0, 2.0 * math.pi * RADIUS + 1.0):
      with self.subTest(ease=ease):
        with self.assertRaises(ValueError):
          easedLoop(RADIUS, DRIFT, ease)

  def test_clothoid(self) -> None:
    """A level clothoid from straight to 1/R over L: turned by L/(2R) at
    its end to rounding; its centre line where Fresnel's integrals put
    it, to a micrometre."""
    from scipy.special import fresnel
    length = 40.0
    ribbon = Ribbon((eased(length, (0.0, 0.0, 0.0),
                           (0.0, 0.0, 1.0 / RADIUS)),))
    place, frame = ribbon.frameAt(length)
    angle = length / (2.0 * RADIUS)
    self.assertNear(math.atan2(frame[1, 0], frame[0, 0]), angle, 1e-12)
    scale = math.sqrt(math.pi * RADIUS * length)
    for s in (10.0, 25.0, length):
      sine, cosine = fresnel(s / scale)
      place, _ = ribbon.frameAt(s)
      self.assertNear(float(place[0]), scale * cosine, 1e-6)
      self.assertNear(float(place[1]), scale * sine, 1e-6)

  def test_off_axis(self) -> None:
    """An easing whose twist and pitch both move (its rates off one
    axis): its end frame matches a fine integration to 1e-9 (the
    commutator term; left out, it is off by far more)."""
    start, end = (0.05, -0.02, 0.0), (-0.03, 0.08, 0.04)
    length = 30.0
    ribbon = Ribbon((eased(length, start, end),))
    place, frame = ribbon.frameAt(length)
    fine, here, turned = 200000, numpy.zeros(3), numpy.eye(3)
    h = length / fine
    a, b = numpy.array(start), numpy.array(end)
    from worQt.phys.rail import turnOf
    for k in range(fine):
      rate = a + (b - a) * (k + 0.5) / fine
      rotation, step = turnOf(rate, h)
      here = here + turned @ step
      turned = turned @ rotation
    self.assertLess(float(numpy.abs(frame - turned).max()), 1e-9)
    self.assertLess(float(numpy.abs(place - here).max()), 1e-6)

  def test_square(self) -> None:
    """The stage's frame is a proper rotation everywhere, to 1e-12, and
    continuous: no jump between neighbouring points 1 cm apart."""
    track = loopTrack()
    last = None
    for s in numpy.arange(0.0, track.length, 0.01):
      place, frame = track.frameAt(s)
      self.assertLess(_square(frame), 1e-12)
      if last is not None:
        self.assertLess(float(numpy.linalg.norm(place - last)), 0.0101)
      last = place

  def test_felt(self) -> None:
    """What a vehicle feels: the centre line differentiated twice along
    a run gaining speed, less gravity, turned into the track's frame,
    matches 'feltAt' to 1e-4 m/s^2 on the grade's curve, in the loop and
    on the climb; at the loop's top, with its rates and no gain, V^2/R'
    - g, R' the helix's radius of curvature."""
    track = loopTrack()
    begins, ends = loopSpan()
    for s0 in (17.0, 0.5 * (begins + ends), ends + 15.0):
      speed, gain, dt = 18.0, -2.0, 1e-3
      at = lambda t: track.frameAt(s0 + speed * t + 0.5 * gain * t * t)[0]
      accel = (at(dt) - 2.0 * at(0.0) + at(-dt)) / (dt * dt)
      _, frame = track.frameAt(s0)
      measured = frame.T @ (accel - numpy.array(GRAVITY))
      felt = track.feltAt(s0, speed, gain)
      self.assertLess(float(numpy.abs(measured - felt).max()), 1e-4,
                      (s0, measured, felt))
    middle = 0.5 * (begins + ends)
    _, frame = track.frameAt(middle)
    pitch = _stage.LOOP_DRIFT / (2.0 * math.pi)
    curved = (RADIUS * RADIUS + pitch * pitch) / RADIUS
    felt = track.feltAt(middle, 12.0, 0.0)
    self.assertNear(float(frame[2, 2]), -1.0, 1e-3)
    self.assertNear(float(felt[2]), 144.0 / curved - 9.81 * float(
      -frame[2, 2]), 1e-9)

  def test_stage(self) -> None:
    """The stage: its start 'DROP' m over the loop's foot, its far end
    'CLIMB' m; its loop's foot at nought; the loop clears the way in
    and out by 2.5 m or more, but where it joins them; its frame level
    at both ends; its drop enough for a wheelset (k = 0.315) by 3 m."""
    track = loopTrack()
    begins, ends = loopSpan()
    start, first = track.frameAt(0.0)
    end, last = track.frameAt(track.length)
    self.assertNear(float(start[2]), _stage.DROP, 1e-12)
    self.assertNear(float(end[2]), _stage.CLIMB, 1e-9)
    self.assertNear(float(track.frameAt(begins)[0][2]), 0.0, 1e-9)
    self.assertLess(float(numpy.abs(last - numpy.eye(3)).max()), 1e-9)
    loopPoints = numpy.array([track.frameAt(s)[0] for s in numpy.arange(
      begins + 8.0, ends - 8.0, 0.25)])
    others = numpy.array([track.frameAt(s)[0] for s in numpy.concatenate(
      (numpy.arange(0.0, begins - 8.0, 0.25),
       numpy.arange(ends + 8.0, track.length, 0.25)))])
    gaps = numpy.linalg.norm(loopPoints[:, None, :] - others[None, :, :],
                             axis=2)
    self.assertGreater(float(gaps.min()), 2.5)
    k = 0.315
    least = 2.0 * RADIUS + 0.5 * (1.0 + k) * RADIUS
    self.assertNear(least, 26.575, 1e-9)
    self.assertGreater(_stage.DROP, least + 3.0)
