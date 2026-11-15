"""
TestHinges covers the hinge ('Hinge', 'Bush'; user, 2026-11-14:
"hinges, rigid and rubber-bushed or whatever ... use YoloD40
stochastic grease"): a steel bar 400 x 40 x 20 mm (2.5 kg) on a rigid
hinge at its end swings as a physical pendulum (its period to a
ten-thousandth), its pin's points together to a micrometre, its lines
in line; turning about its pin it keeps its speed (to two
thousandths in a second). On a car's rubber bushing (5 kN/mm across,
1 kN/mm along, 10 kN m/rad tilted) it gives under its weight as the
rubber says: across, hanging under a level pin; along, hanging from an
upright one (its line given either way along the pin alike); tilted,
standing out from an upright pin as a door (each to half a micrometre,
the step's own error: its fall over a step, times the rules' share);
and rests. A door (oak, 22 kg) on two rigid hinges on one line (each
holding what the other does: twice) rests, and pushed swings on; and
alike greased. The springs' world refuses it. Steps of 0.125 ms.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worQt.phys import Assembly, Body, Bush, Hinge, SmallSteps, State
from worQt.phys import World, boxShape, cross, minus, norm, plus
from worQt.phys import rotated, turnAbout

from . import PhysTest

FRAME = 1.0 / 60.0
STEP = 1.25e-4
GRAVITY = (0.0, 0.0, -9.81)
LENGTH = 0.4
BAR = Body.of(boxShape(LENGTH, 0.04, 0.02), 7850.0)
PIN = (0.0, 0.0, 1.0)
END = (-0.5 * LENGTH, 0.0, 0.0)
UP = (0.0, 0.0, 1.0)
ACROSS = (0.0, 1.0, 0.0)
DOWN = turnAbout(ACROSS, 0.5 * math.pi)


def ran(assembly: Assembly, states: tuple, seconds: float,
        gravity: tuple = GRAVITY, grease: float = 0.0) -> list:
  """The 'ran' function returns 'states' at each frame of 'seconds' on
  (the first as given), in small steps of 'STEP'."""
  world = SmallSteps(gravity, None, STEP, 1, grease, 'cpu')
  out = [states]
  for k in range(round(seconds / FRAME)):
    states = world.advancedAll(assembly, states, FRAME, k * FRAME)
    out.append(states)
  return out


def gapOf(hinge: Hinge, state: State) -> tuple:
  """The 'gapOf' function returns how far the bar's end of 'hinge' (in
  'state') is from its pin in the world."""
  return minus(plus(state.place, rotated(state.turn, minus(
    hinge.secondPoint, BAR.centre))), hinge.firstPoint)


def hung(axis: tuple, turn: tuple, line: tuple, bush: Bush) -> tuple:
  """The 'hung' function returns the bar on a hinge at its end to the
  world's pin along 'axis', turned by 'turn', its own pin's line
  'line', and its state as built."""
  hinge = Hinge(None, PIN, axis, 0, END, line, bush)
  return hinge, Assembly((BAR,), (hinge,)), (
    State(minus(PIN, rotated(turn, END)), turn),)


class TestHinges(PhysTest):
  """Tests for the hinge (about 40 s on the CPU)."""

  __time_out__ = 180.0

  def test_pendulum(self) -> None:
    """The bar on a rigid hinge at its end, let go 10 degrees off
    hanging, swings at the physical pendulum's period (with the
    amplitude's series) to a ten-thousandth; its pin's points stay
    within a micrometre, its lines in line to a hundred-thousandth of a
    radian."""
    angle = math.radians(10.0)
    hinge, assembly, states = hung(ACROSS, turnAbout(
      ACROSS, 0.5 * math.pi - angle), ACROSS, None)
    frames = ran(assembly, states, 3.0)
    crossings = []
    for k in range(1, len(frames)):
      a, b = (frames[j][0].place[0] - PIN[0] for j in (k - 1, k))
      if a < 0.0 <= b:
        crossings.append((k - b / (b - a)) * FRAME)
    period = (crossings[-1] - crossings[0]) / (len(crossings) - 1)
    mass, arm = BAR.mass, 0.5 * LENGTH
    moment = mass * (LENGTH ** 2 + 0.02 ** 2) / 12.0 + mass * arm ** 2
    wanted = 2.0 * math.pi * math.sqrt(moment / (mass * 9.81 * arm)) * (
      1.0 + angle ** 2 / 16.0 + 11.0 * angle ** 4 / 3072.0)
    self.assertNear(period, wanted, 1e-4 * wanted)
    for frame in frames:
      self.assertLess(norm(gapOf(hinge, frame[0])), 1e-6)
      line = rotated(frame[0].turn, ACROSS)
      self.assertLess(norm(cross(line, ACROSS)), 1e-5)

  def test_turns_freely(self) -> None:
    """With no gravity, the bar turning about its rigid pin at 3 rad/s
    keeps its speed for a second, to two thousandths."""
    hinge, assembly, states = hung(ACROSS, (1.0, 0.0, 0.0, 0.0), ACROSS,
                                   None)
    spin = (0.0, 3.0, 0.0)
    centre = states[0].place
    states = (State(centre, states[0].turn, cross(spin, minus(centre,
                                                              PIN)), spin),)
    frames = ran(assembly, states, 1.0, (0.0, 0.0, 0.0))
    self.assertNear(frames[-1][0].spin[1], 3.0, 6e-3)

  def test_bush_gives(self) -> None:
    """On a car's bushing ('Bush()'), the bar gives under its weight as
    the rubber says, to half a micrometre, and rests: hanging under a
    level pin, across it, m g / 5 kN/mm (4.9 um); hanging from an
    upright pin, along it, m g / 1 kN/mm (24.6 um), its line given
    either way along the pin; standing out level from an upright pin (a
    door), along it, and tilted m g (L / 2) / 10 kN m/rad (0.49 mrad,
    to a sixtieth)."""
    bush = Bush()
    weight = BAR.mass * 9.81
    hinge, assembly, states = hung(ACROSS, DOWN, ACROSS, bush)
    rest = ran(assembly, states, 1.0)[-1][0]
    self.assertNear(norm(gapOf(hinge, rest)), weight / bush.radial, 5e-7)
    self.assertLess(norm(rest.velocity), 1e-4)
    for line in ((1.0, 0.0, 0.0), (-1.0, 0.0, 0.0)):
      hinge, assembly, states = hung(UP, DOWN, line, bush)
      rest = ran(assembly, states, 1.0)[-1][0]
      self.assertNear(norm(gapOf(hinge, rest)), weight / bush.axial, 5e-7)
    hinge, assembly, states = hung(UP, (1.0, 0.0, 0.0, 0.0), UP, bush)
    rest = ran(assembly, states, 1.0)[-1][0]
    self.assertNear(norm(gapOf(hinge, rest)), weight / bush.axial, 2.5e-6)
    tilt = math.asin(norm(cross(rotated(rest.turn, UP), UP)))
    wanted = weight * 0.5 * LENGTH / bush.tilt
    self.assertNear(tilt, wanted, wanted / 60.0)

  def test_door(self) -> None:
    """A door (oak, 0.8 x 2 m, 40 mm) on two rigid hinges on one upright
    line 1.8 m apart rests (within 10 um of where it was hung) and,
    pushed open at 1 rad/s, swings on (to a thousandth in a second), its
    line upright to a hundred-thousandth of a radian; greased by a
    tenth of a micrometre ('SmallSteps.grease') alike."""
    door = Body.of(boxShape(0.8, 0.04, 2.0), 700.0)
    edge = (-0.4, 0.0, 0.0)
    hinges = tuple(Hinge(None, (0.0, 0.0, 1.1 + z), UP, 0,
                         plus(edge, (0.0, 0.0, z)), UP) for z in (-0.9, 0.9))
    assembly = Assembly((door,), hinges)
    standing = State(minus((0.0, 0.0, 1.1), edge))
    for grease in (0.0, 1e-7):
      rest = ran(assembly, (standing,), 1.0, GRAVITY, grease)[-1][0]
      self.assertLess(norm(minus(rest.place, standing.place)), 1e-5)
      spin = (0.0, 0.0, 1.0)
      pushed = State(standing.place, standing.turn, cross(spin, minus(
        standing.place, (0.0, 0.0, standing.place[2]))), spin)
      swung = ran(assembly, (pushed,), 1.0, GRAVITY, grease)[-1][0]
      self.assertNear(swung.spin[2], 1.0, 1e-3)
      self.assertLess(norm(cross(rotated(swung.turn, UP), UP)), 1e-5)

  def test_springs_refuse(self) -> None:
    """The springs' world refuses a hinge (small steps only)."""
    _, assembly, states = hung(ACROSS, DOWN, ACROSS, None)
    with self.assertRaises(ValueError):
      World(GRAVITY, 1e-3, None).advancedAll(assembly, states, 0.01)
