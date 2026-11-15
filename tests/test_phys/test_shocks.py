"""
TestShocks covers springs, dampers and sliding joints in the small
steps, and the shock absorber built of them ('_shock'; user,
2026-11-14: "shock absorbers should be mass damper spring systems. The
ends should be omni-hinged"): a 4.1 kg ball hung on a spring (20 kN/m)
swings at its period (to half a percent) and, damped, rests where its
weight stretches it (to a tenth of a millimetre); a damper holding back
rebound four times as hard as bump damps the swings up and down
unalike; a block on a sliding joint down a line 30 degrees off level
slides as g sin 30 says (to a percent), on its line to a micrometre,
unturned. The shock absorber ('Shock()': a 30 kN/m coil of 220 mm, a
damper of 1.76 kN s/m bump and 4.4 rebound, bump stop at 290 mm eye to
eye, top-out at 380, tube 2 kg and rod 1.5 kg on rod ends): under a 150
kg block it rests on its coil (to 2 mm), under 600 kg on its bump stop
(the coil and rubber sharing the load, to 3 mm), and pulled by a
hanging 100 kg it holds at its top-out (to 1.5 mm); on the rig,
holding up a wishbone and a 100 kg weight, its coil carries their
moment (1.8 kN) and its tube and rod stay in line. The springs' world
refuses a sliding joint and a damper's own rebound.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Damper, Slide, SmallSteps, Spring
from worQt.phys import Sphere, State, World, boxShape, cross, dot, minus
from worQt.phys import norm, rotated
from worQt.phys._carcass import TYRE_YARD
from worQt.phys._shock import LOWER_SEAT, UPPER_SEAT, Shock, shockBench
from worQt.phys._shock import shockOf

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 2.5e-4
GRAVITY = (0.0, 0.0, -9.81)
UP = (0.0, 0.0, 1.0)
BALL = Body.of(Sphere(0.05), 7850.0)
TOP = (0.0, 0.0, 2.0)
REST = 0.5
STIFF = 2e4


def ran(assembly: Assembly, states: tuple, seconds: float,
        grease: float = 0.0, ground: object = None) -> list:
  """The 'ran' function returns 'states' at each frame of 'seconds' on
  (the first as given), in small steps of 'STEP'."""
  world = SmallSteps(GRAVITY, ground, STEP, 1, grease, 'cpu')
  out = [states]
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    out.append(states)
  return out


def eyes(assembly: Assembly, states: tuple, tube: int) -> float:
  """The 'eyes' function returns how far apart a shock's eyes are, its
  tube body 'tube', its rod the next."""
  return norm(minus(assembly.bodies[tube + 1].placeOf(
    states[tube + 1], (0.0, 0.0, 0.0)), assembly.bodies[tube].placeOf(
    states[tube], (0.0, 0.0, 0.0))))


def shockUnder(mass: float) -> tuple:
  """The 'shockUnder' function returns a block of 'mass' kg sliding up
  and down a world line, on a shock absorber ('Shock()') from the world
  below it, 0.36 m eye to eye as built."""
  block = Body.of(boxShape(0.3, 0.3, 0.3), mass / 0.027)
  under, at = (0.0, 0.0, 0.1), (0.0, 0.0, 0.46)
  bodies, states, parts = shockOf(Shock(), 0, (0.0, 0.0, -0.15), None,
                                  under, 1, at, under)
  guide = Slide(None, (0.0, 0.0, 0.0), UP, 0, (0.0, 0.0, 0.0), UP)
  return Assembly((block,) + bodies, (guide,) + parts), (
    State((0.0, 0.0, 0.61)),) + states


class TestShocks(PhysTest):
  """Tests for springs, dampers, sliding joints and the shock absorber
  (about 30 s on the CPU)."""

  __time_out__ = 180.0

  def test_spring(self) -> None:
    """A 4.1 kg ball hung on a spring of 20 kN/m from its rest length
    swings at 2 pi sqrt(m / k) (to half a percent); damped (a fifth of
    critical) it rests stretched m g / k (to a tenth of a millimetre)."""
    spring = Spring(None, TOP, 0, (0.0, 0.0, 0.0), STIFF, REST)
    start = (State((0.0, 0.0, TOP[2] - REST)),)
    frames = ran(Assembly((BALL,), (spring,)), start, 2.0)
    heights = [frame[0].place[2] for frame in frames]
    middle = 0.5 * (min(heights) + max(heights))
    ups = [(k - (heights[k] - middle) / (heights[k] - heights[k - 1]))
           * FRAME for k in range(1, len(heights))
           if heights[k - 1] < middle <= heights[k]]
    period = (ups[-1] - ups[0]) / (len(ups) - 1)
    wanted = 2.0 * math.pi * math.sqrt(BALL.mass / STIFF)
    self.assertNear(period, wanted, 5e-3 * wanted)
    damper = Damper(None, TOP, 0, (0.0, 0.0, 0.0),
                    0.4 * math.sqrt(STIFF * BALL.mass))
    rest = ran(Assembly((BALL,), (spring, damper)), start, 1.5)[-1][0]
    self.assertNear(rest.place[2], TOP[2] - REST - BALL.mass * 9.81 / STIFF,
                    1e-4)

  def test_rebound(self) -> None:
    """Damped a tenth of critical shortening (bump) and four tenths
    lengthening (rebound), the ball's swings shrink unalike: each swing
    up, the spring shortening, by less than half (more than half left),
    each swing down by more (less than 0.35 left); it rests as damped
    alike."""
    critical = 2.0 * math.sqrt(STIFF * BALL.mass)
    assembly = Assembly((BALL,), (
      Spring(None, TOP, 0, (0.0, 0.0, 0.0), STIFF, REST),
      Damper(None, TOP, 0, (0.0, 0.0, 0.0), 0.1 * critical,
             0.4 * critical)))
    frames = ran(assembly, (State((0.0, 0.0, TOP[2] - REST)),), 1.5)
    rest = TOP[2] - REST - BALL.mass * 9.81 / STIFF
    off = [frame[0].place[2] - rest for frame in frames]
    peaks = [off[k] for k in range(1, len(off) - 1)
             if abs(off[k]) >= abs(off[k - 1])
             and abs(off[k]) >= abs(off[k + 1])]
    ratios = [abs(b / a) for a, b in zip(peaks, peaks[1:])][:3]
    self.assertGreater(ratios[0], 0.5)
    self.assertLess(ratios[1], 0.35)
    self.assertGreater(ratios[2], 0.5)
    self.assertNear(frames[-1][0].place[2], rest, 1e-4)

  def test_slide(self) -> None:
    """A block on a sliding joint down a line 30 degrees off level,
    let go, slides g sin 30 t² / 2 in half a second (to a percent),
    stays on its line to a micrometre and turns not at all."""
    tilt = math.radians(30.0)
    line = (math.cos(tilt), 0.0, -math.sin(tilt))
    block = Body.of(boxShape(0.1, 0.1, 0.1), 7850.0)
    start = (0.0, 0.0, 2.0)
    assembly = Assembly((block,), (Slide(None, start, line, 0,
                                         (0.0, 0.0, 0.0), line),))
    frames = ran(assembly, (State(start),), 0.5)
    for frame in frames:
      away = minus(frame[0].place, start)
      self.assertLess(norm(minus(away, tuple(dot(away, line) * x
                                            for x in line))), 1e-6)
    wanted = 9.81 * math.sin(tilt) * 0.25 / 2.0
    away = minus(frames[-1][0].place, start)
    self.assertNear(dot(away, line), wanted, 0.01 * wanted)
    self.assertLess(norm(frames[-1][0].spin), 1e-6)

  def test_shock_holds(self) -> None:
    """Under a 150 kg block the shock rests on its coil: its eyes the
    seats and the coil's free length apart, less what the load squeezes
    it (to 2 mm, greased as the bench is)."""
    shock = Shock()
    assembly, states = shockUnder(150.0)
    rest = ran(assembly, states, 4.0, 1e-7)[-1]
    wanted = LOWER_SEAT + UPPER_SEAT + shock.free - (
      150.0 + shock.rod) * 9.81 / shock.spring
    self.assertNear(eyes(assembly, rest, 1), wanted, 2e-3)

  def test_bump_stop(self) -> None:
    """Under 600 kg, past what the coil holds, the shock rests on its
    bump stop, the coil and the rubber sharing the load (to 3 mm)."""
    shock = Shock()
    assembly, states = shockUnder(600.0)
    rest = ran(assembly, states, 4.0, 1e-7)[-1]
    load = (600.0 + shock.rod) * 9.81
    wanted = (shock.spring * (LOWER_SEAT + UPPER_SEAT + shock.free)
              + shock.stop * shock.shortest - load) / (shock.spring
                                                       + shock.stop)
    self.assertNear(eyes(assembly, rest, 1), wanted, 3e-3)
    self.assertLess(eyes(assembly, rest, 1), shock.shortest)

  def test_top_out(self) -> None:
    """Hung from its rod's eye with 100 kg on its tube's, the shock
    opens to its top-out stop and holds there (to a millimetre and a
    half: 1.03 mm past it, the light tube's share of the rules)."""
    shock = Shock()
    block = Body.of(boxShape(0.3, 0.3, 0.3), 100.0 / 0.027)
    at, under = (0.0, 0.0, 2.0), (0.0, 0.0, 1.64)
    bodies, states, parts = shockOf(shock, None, at, 0, (0.0, 0.0, 0.15),
                                    1, at, under)
    guide = Slide(None, (0.0, 0.0, 0.0), UP, 0, (0.0, 0.0, 0.0), UP)
    assembly = Assembly((block,) + bodies, (guide,) + parts)
    rest = ran(assembly, (State((0.0, 0.0, under[2] - 0.15)),) + states,
               3.0, 1e-7)[-1]
    self.assertNear(eyes(assembly, rest, 1), shock.longest, 1.5e-3)

  def test_rig(self) -> None:
    """On the rig (the shock bench) the shock holds up the wishbone and
    its 100 kg weight: in 5 s its coil carries 1.6 to 2 kN (1.8: their
    moment about the pivots over the shock's), the wishbone 5 to 10
    degrees down, the shock's tube and rod in line to a ten-thousandth of
    a radian."""
    assembly, states = shockBench()
    rest = ran(assembly, states, 5.0, 1e-7, TYRE_YARD)[-1]
    shock = Shock()
    seats = eyes(assembly, rest, 4) - LOWER_SEAT - UPPER_SEAT
    coil = shock.spring * (shock.free - seats)
    self.assertGreater(coil, 1600.0)
    self.assertLess(coil, 2000.0)
    arm = rotated(rest[2].turn, (0.0, 0.0, -1.0))
    down = math.degrees(math.asin(-arm[2]))
    self.assertGreater(down, 5.0)
    self.assertLess(down, 10.0)
    self.assertLess(norm(cross(rotated(rest[4].turn, UP),
                               rotated(rest[5].turn, UP))), 1e-4)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses a sliding joint and a damper with a
    rebound of its own."""
    world = World(GRAVITY, 1e-3, None)
    start = (State((0.0, 0.0, 1.0)),)
    for connection in (Slide(None, (0.0, 0.0, 0.0), UP, 0, (0.0, 0.0, 0.0),
                             UP),
                       Damper(None, TOP, 0, (0.0, 0.0, 0.0), 1.0, 2.0)):
      with self.assertRaises(ValueError):
        world.advancedAll(Assembly((BALL,), (connection,)), start, 0.01)
