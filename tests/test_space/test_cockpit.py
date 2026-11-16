"""
TestCockpit covers the capsule as Asger sits in it (user, 2026-11-16:
"Asger is presented iwth a fully functional diegetic dashboard";
"Asger sits upright on the launch pad"; "a style that is more 1970's
B&O ... *Every* fourtpeep input ... must visibly deform when activated";
"When I press a keyboard key my view will turn to center on that key"):
every input within his reach, each its own key and action, and the one
his eyes rest on when he looks or glances at it; he, his seat, the
dashboard and every piece of it inside the capsule's wall; ahead of him
a window; his eyes sinking under thrust; each input moving as it is
worked in the cabin's parts, the needles, lamps and legends as told.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import itertools
import math

import numpy

from worQt.gaming.sandbox import FourthPeep, Knob, Pushbutton, Slider
from worQt.gaming.sandbox._skin import PARTS
from worQt.gaming.space import _dashboard as dashboard
from worQt.gaming.space._cockpit import BACKREST, BALL_RADIUS, BAT_ON
from worQt.gaming.space._cockpit import CUSHION, EYE, GLASS, GLOBE_AT
from worQt.gaming.space._cockpit import GLOBE_AXES
from worQt.gaming.space._cockpit import FIGURE, FLOOR, KEY_TRAVEL
from worQt.gaming.space._cockpit import LEFT_CONSOLE, PANEL_AXES
from worQt.gaming.space._cockpit import RIGHT_CONSOLE, SCALE, SLIDER_LONG
from worQt.gaming.space._cockpit import WALL, Cockpit, capsuleRadius
from worQt.gaming.space._cabinworld import restingLoose
from worQt.gaming.space._cockpit import inWindow
from worQt.gaming.space._dashboard import SWEEP, dialAngle, dialShare
from worQt.gaming.space._dashboard import LEGENDS, ballCentre, legendAxes
from worQt.gaming.space._dashboard import pieces
from worQt.gaming.space._dashboard import pieceRows, pivotOf
from worQt.gaming.space._dashpictures import labelCells
from worQt.gaming.space._deckmodel import AXIS, movingParts, stillParts
from worQt.gaming.space._turns import aboutAxis, cross, product, rotated
from worQt.gaming.space._turns import unrotated
from worQt.gaming.space._vessel import RADIUS

from . import SpaceTest

#  The dashboard's still meshes, by their makers' names.
STILL = ('panelFace', 'panelFrame', 'dialFaces', 'bezels', 'monitorBody',
         'screenRows',
         'paperRows',
         'sliderTrack', 'consoleBases', 'domeRows', 'monitorInset',
         'globeStand', 'sideboardRows', 'sideboardTop', 'paperFrame')


def _inside(point: tuple) -> bool:
  """Returns whether 'point' is inside the capsule's inner wall, over
  its floor."""
  return point[2] >= FLOOR - 1e-9 and math.hypot(point[0], point[1]) <= (
    capsuleRadius(point[2]) - WALL)


def _resting() -> dict:
  """Returns what a cabin's frame takes of the cabin world at rest: the
  loose things where they rest, one g at the candles."""
  return {'loose': restingLoose(), 'weight': 1.0}


def _corners(middle: tuple, half: tuple) -> list:
  """Returns a box's eight corners."""
  return [tuple(m + s * h for m, s, h in zip(middle, signs, half))
          for signs in itertools.product((-1.0, 1.0), repeat=3)]


def _inverse(turn: tuple) -> tuple:
  """Returns the unit quaternion 'turn' undone."""
  return turn[0], -turn[1], -turn[2], -turn[3]


def _turnClose(one: tuple, two: tuple) -> float:
  """Returns how far apart two turns are (nought: the same, either
  sign)."""
  return min(math.dist(one, two), math.dist(one, tuple(-x for x in two)))


class TestCockpit(SpaceTest):
  """Tests for 'Cockpit', its dashboard and its cabin's parts."""

  def test_inputs(self) -> None:
    """The dashboard has its 20 inputs, each its own action and key: six
    switches and the view's, four knobs (warp, orbit, gravity, the
    engine's limit), eight keys, the slide; the switches plain
    FourthPeeps, the rest their kinds."""
    controls = Cockpit().controls
    self.assertEqual(len(controls), 20)
    actions = [control.action for control in controls]
    keys = [control.key for control in controls]
    self.assertEqual(len(set(actions)), len(actions))
    self.assertEqual(len(set(keys)), len(keys))
    kinds = {}
    for control in controls:
      kind = type(control.peep).__name__
      kinds[kind] = kinds.get(kind, 0) + 1
    self.assertEqual(kinds, {'FourthPeep': 7, 'Knob': 4, 'Pushbutton': 8,
                             'Slider': 1})
    switch = Cockpit().controlOf('hold').peep
    self.assertIs(type(switch), FourthPeep)
    self.assertIsInstance(Cockpit().controlOf('warp').peep, Knob)
    self.assertIsInstance(Cockpit().controlOf('play').peep, Pushbutton)
    self.assertIsInstance(Cockpit().controlOf('throttle').peep, Slider)
    self.assertIsNone(Cockpit().controlOf('nothing'))

  def test_handed(self) -> None:
    """Every input's and legend's axes are right-handed (right, up, out:
    read as he reads them, never mirrored), unit and square."""
    frames = [control.axes for control in Cockpit().controls]
    frames += [legendAxes(k) for k in range(len(LEGENDS))]
    for right, up, out in frames:
      self.assertClose(cross(right, up), out, 1e-9)
      for axis in (right, up, out):
        self.assertAlmostEqual(math.hypot(*axis), 1.0, 9)

  def test_reach(self) -> None:
    """Every input is within his arms' reach: 0.3 m or more from his
    eyes, at most 0.8 m from his nearer shoulder (his arm and hand),
    none behind him."""
    shoulders = [tuple(f + SCALE * p for f, p in zip(FIGURE, part[2]))
                 for part in PARTS if part[0].endswith('arm')]
    for control in Cockpit().controls:
      self.assertGreater(math.dist(control.centre, EYE), 0.3, control.name)
      reach = min(math.dist(control.centre, s) for s in shoulders)
      self.assertLess(reach, 0.8, control.name)
      self.assertGreater(control.centre[0] - EYE[0], -0.2, control.name)

  def test_looked_at(self) -> None:
    """Looking at an input's middle his eyes rest on it, no other in
    the way."""
    cockpit = Cockpit()
    for control in cockpit.controls:
      way = tuple(a - b for a, b in zip(control.centre, EYE))
      size = math.dist(control.centre, EYE)
      way = tuple(x / size for x in way)
      cockpit.yaw = math.atan2(way[1], way[0])
      cockpit.pitch = math.asin(way[2])
      self.assertIs(cockpit.lookedAt(), control, control.name)

  def test_glance(self) -> None:
    """A key pressed, his head turns to its input, most of the way in
    a tenth of a second, resting on it within half a second; the mouse
    takes his head back at once; an action no input works turns
    nothing."""
    cockpit = Cockpit()
    for control in cockpit.controls:
      cockpit.yaw, cockpit.pitch = 0.0, -0.12
      cockpit.glanced(control.action)
      start = (cockpit.yaw, cockpit.pitch)
      aim = cockpit.glancing
      cockpit.acted(0.1)
      gone = math.dist((cockpit.yaw, cockpit.pitch), start)
      whole = math.dist(aim, start)
      self.assertAlmostEqual(gone / whole, 1.0 - math.exp(-1.0), 6,
                             control.name)
      for _ in range(30):
        cockpit.acted(1.0 / 60.0)
      self.assertIs(cockpit.lookedAt(), control, control.name)
    cockpit.glanced('hold')
    cockpit.turned(10.0, 0.0)
    self.assertIsNone(cockpit.glancing)

  def test_gravity(self) -> None:
    """The gravity enchantment starts off (user, 2026-11-17: "It starts
    off"), a tenth of a g a notch up to one g, its knob by the warp's."""
    cockpit = Cockpit()
    self.assertEqual(cockpit.weight(), 0.0)
    self.assertFalse(cockpit.heavier(-1))
    for _ in range(20):
      cockpit.heavier(1)
    self.assertAlmostEqual(cockpit.weight(), 1.0, 9)
    self.assertFalse(cockpit.heavier(1))
    cockpit.heavier(-7)
    self.assertAlmostEqual(cockpit.weight(), 0.3, 9)
    knob, warp = cockpit.controlOf('gravity'), cockpit.controlOf('warp')
    self.assertIsInstance(knob.peep, Knob)
    self.assertLess(math.dist(knob.centre, warp.centre), 0.15)
    cockpit.glanced('nothing')
    self.assertIsNone(cockpit.glancing)

  def test_inside(self) -> None:
    """He, his seat, the consoles, every still mesh of the dashboard
    and every moving piece at rest are inside the capsule's wall, over
    its floor."""
    cockpit = Cockpit()
    for index, place, turn in cockpit.figureOf():
      block = PARTS[index][1]
      pivot = PARTS[index][2]
      for corner in itertools.product(block[0:2], block[2:4], block[4:6]):
        local = tuple(SCALE * (c - p) for c, p in zip(corner, pivot))
        point = tuple(a + b for a, b in zip(place, rotated(turn, local)))
        self.assertTrue(_inside(point), (PARTS[index][0], point))
    for middle, half in (CUSHION, BACKREST, LEFT_CONSOLE, RIGHT_CONSOLE):
      for corner in _corners(middle, half):
        self.assertTrue(_inside(corner), corner)
    for name in STILL:
      rows = numpy.asarray(getattr(dashboard, name)()[0])
      for row in rows:
        self.assertTrue(_inside(tuple(row[:3])), (name, tuple(row[:3])))
    from worQt.gaming.space._cabin import chairFrame
    for row in chairFrame()[0]:
      self.assertTrue(_inside(tuple(row[:3])), tuple(row[:3]))
    for _, (rows, _) in stillParts():
      wall = numpy.vectorize(capsuleRadius)(rows[:, 2]) - WALL
      self.assertTrue((rows[:, 2] >= FLOOR).all())
      self.assertTrue((numpy.hypot(rows[:, 0], rows[:, 1]) <= wall).all())
    cells = labelCells()
    for piece in pieces(cockpit.controls):
      rows = numpy.asarray(pieceRows(piece, cells)[0])
      pivot = pivotOf(piece)
      for row in rows:
        point = tuple(a + b for a, b in zip(row[:3], pivot))
        self.assertTrue(_inside(point), (piece[0], point))

  def test_window(self) -> None:
    """To his left he sees out through the window by him (user,
    2026-11-16: "To his left is a window"), ahead of him and to his
    right the room he is in; looking down, his panel."""
    cockpit = Cockpit()
    for yaw, pitch in ((1.35, 0.1), (1.1, -0.2), (1.6, 0.4)):
      cockpit.yaw, cockpit.pitch = yaw, pitch
      self.assertTrue(inWindow(cockpit.looking()[0], EYE), (yaw, pitch))
    for yaw, pitch in ((0.0, 0.1), (-1.35, 0.1), (0.0, -0.5)):
      cockpit.yaw, cockpit.pitch = yaw, pitch
      self.assertFalse(inWindow(cockpit.looking()[0], EYE), (yaw, pitch))

  def test_pressed_down(self) -> None:
    """Pushed along his nose at 1.5 g his eyes sink 18 mm into his seat;
    not pushed, they stay; the shake is a few mm at full throttle."""
    cockpit = Cockpit()
    self.assertAlmostEqual(cockpit.eyeOf(1.5, 0.0)[2], EYE[2] - 0.018, 9)
    self.assertAlmostEqual(cockpit.eyeOf(0.0, 0.0)[2], EYE[2], 9)
    shaken = cockpit.eyeOf(0.0, 1.0)
    self.assertLess(math.dist(shaken, EYE), 0.005)

  def test_dials(self) -> None:
    """A dial's share of its scale grows with its value, nought at
    nought, whole at its last tick and past it; the needle sweeps 270
    degrees."""
    for name, (turn, most, ticks, unit) in dashboard.DIAL_SCALES.items():
      self.assertAlmostEqual(dialShare(name, 0.0), 0.0, 9)
      self.assertAlmostEqual(dialShare(name, most), 1.0, 9)
      self.assertAlmostEqual(dialShare(name, 10 * most), 1.0, 9)
      shares = [dialShare(name, value) for value, _ in ticks]
      self.assertEqual(shares, sorted(shares))
      self.assertEqual(len(set(shares)), len(shares))
    self.assertAlmostEqual(dialAngle(1.0) - dialAngle(0.0), SWEEP, 9)

  def test_cabin(self) -> None:
    """The cabin's parts come in their order: the dashboard's pieces,
    the ball, its marks, his limbs (his head and arms left out seen from
    his eyes); a key pressed sinks its travel in and springs back; a switch
    thrown turns its bat; a knob turns by its notches; the slide moves
    with the throttle; a needle turns as told; a lamp and a legend glow
    lit; the hull's camera, outside the tank, looks aft."""
    from worQt.gaming.space._instruments import Instruments
    from worQt.gaming.space._navball import Navball
    from worQt.gaming.space._scenery import AFTER_PIECES, LAMP_OFF
    from worQt.gaming.space._scenery import LAMP_ON, LEGEND_ON, Scenery
    from worQt.gaming.space._scenery import MARK_KINDS, MECHANISM
    system = self.systemOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    cockpit, scenery = Cockpit(), Scenery()
    dash = Instruments(cockpit).dash()
    dash.update(_resting())
    ball = Navball().frameOf(vessel, system, 104.0)
    turn = vessel.turn
    rocket = ((0.0, 0.0, 0.0), turn, True)
    every = pieces(cockpit.controls)

    def parts(inside: bool = True) -> list:
      """Returns the cabin's parts now."""
      return scenery.cabinOf(system, vessel, cockpit, rocket, ball, dash,
                             inside)['parts']

    plain = parts()
    self.assertEqual(len(plain), len(every) + AFTER_PIECES)
    first = len(every) + 1 + len(MECHANISM) + len(MARK_KINDS)
    outside = parts(False)
    for k, part in enumerate(PARTS):
      hidden = part[0] in ('head', 'right arm', 'left arm')
      self.assertEqual(plain[first + k][2], not hidden, part[0])
      self.assertTrue(outside[first + k][2], part[0])
    order = {piece: k for k, piece in enumerate(every)}
    key = cockpit.controlOf('toAp')
    at = order[('control', key)]
    key.peep.used()
    cockpit.acted(0.2)
    self.assertAlmostEqual(math.dist(parts()[at][0], plain[at][0]),
                           KEY_TRAVEL, 9)
    cockpit.acted(0.2)
    self.assertAlmostEqual(math.dist(parts()[at][0], plain[at][0]), 0.0, 9)
    switch = cockpit.controlOf('hold')
    at = order[('control', switch)]
    switch.peep.used()
    cockpit.acted(1.0)
    want = product(turn, aboutAxis(switch.peep.axis, BAT_ON))
    self.assertLess(_turnClose(parts()[at][1], want), 1e-9)
    knob = cockpit.controlOf('warp')
    at = order[('control', knob)]
    knob.peep.set(3)
    cockpit.acted(1.0)
    want = product(turn, aboutAxis(knob.peep.axis,
                                   knob.peep.near + 3 * knob.peep.step))
    self.assertLess(_turnClose(parts()[at][1], want), 1e-9)
    slide = cockpit.controlOf('throttle')
    at = order[('control', slide)]
    slide.peep.slid(1.0)
    cockpit.acted(1.0)
    self.assertAlmostEqual(math.dist(parts()[at][0], plain[at][0]),
                           SLIDER_LONG, 9)
    dash['needles'][1] = 0.5
    dash['lamps'][0] = True
    dash['legends'][0] = True
    now = parts()
    want = product(turn, aboutAxis(PANEL_AXES[2], -dialAngle(0.5)))
    self.assertLess(_turnClose(now[order[('needle', 1)]][1], want), 1e-9)
    self.assertEqual(now[order[('lamp', 0)]][3], LAMP_ON)
    self.assertEqual(now[order[('lamp', 1)]][3], LAMP_OFF)
    self.assertEqual(now[order[('legend', 0)]][3], LEGEND_ON)
    at, way, up = scenery.cabinOf(system, vessel, cockpit, rocket, ball,
                                  dash, True)['camera']
    local = unrotated(turn, at)
    self.assertGreater(math.hypot(local[0], local[1]), RADIUS + 0.2)
    nose = rotated(turn, (0.0, 0.0, 1.0))
    self.assertLess(sum(a * b for a, b in zip(way, nose)), -0.95)
    self.assertLess(abs(sum(a * b for a, b in zip(way, up))), 0.5)

  def test_deck(self) -> None:
    """The tape deck is at his right, facing him, within reach of his
    eyes' turn; its reels turn about their spindles as told, its knob
    with the play; a reel's parts all turn alike."""
    from worQt.gaming.space._scenery import KNOB_TURN, Scenery
    for kind, index, _, pivot, _, _ in movingParts():
      self.assertLess(pivot[1], EYE[1] - 0.5)
      toward = tuple(e - p for e, p in zip(EYE, pivot))
      self.assertGreater(sum(a * b for a, b in zip(AXIS, toward)), 0.0)
    kinds = sorted({(kind, index) for kind, index, *_ in movingParts()})
    self.assertEqual(kinds, [('knob', 0), ('reel', 0), ('reel', 1)])
    system = self.systemOf()
    vessel = self.orbiting(system, 300e3, 300e3)
    cockpit, scenery = Cockpit(), Scenery()
    from worQt.gaming.space._instruments import Instruments
    from worQt.gaming.space._navball import Navball
    dash = Instruments(cockpit).dash()
    dash.update(_resting())
    dash['reels'], dash['knob'] = (0.4, -1.1), 1.0
    ball = Navball().frameOf(vessel, system, 104.0)
    turn = vessel.turn
    parts = scenery.cabinOf(system, vessel, cockpit, ((0.0, 0.0, 0.0),
                                                      turn, True), ball,
                            dash, True)['parts']
    every = pieces(cockpit.controls)
    for k, (kind, index, _, pivot, _, _) in enumerate(movingParts()):
      part = parts[every.index(('deck', k))]
      angle = dash['reels'][index] if kind == 'reel' else -KNOB_TURN
      want = product(turn, aboutAxis(AXIS, angle))
      self.assertLess(_turnClose(part[1], want), 1e-9, (kind, index))
      self.assertClose(unrotated(turn, part[0]), pivot, 1e-9)

  def test_ball(self) -> None:
    """The horizon is a globe on its stand (user, 2026-11-16: "like a
    globe"), facing his eyes, its ball under a glass dome; it turns in
    the cabin as the rocket turns; its mechanism follows it: the hubs on
    its poles, the axles across them, the ring flat in its stand; its
    marks lie on it."""
    from worQt.gaming.space._navball import Navball
    from worQt.gaming.space._scenery import MARK_KINDS, MARK_OVER
    from worQt.gaming.space._scenery import MECHANISM, Scenery
    self.assertGreater(GLASS, BALL_RADIUS)
    toward = tuple(e - g for e, g in zip(EYE, GLOBE_AT))
    size = math.dist(EYE, GLOBE_AT)
    self.assertAlmostEqual(sum(a * b / size for a, b in zip(
      GLOBE_AXES[2], toward)), 1.0, 9)
    self.assertClose(cross(GLOBE_AXES[0], GLOBE_AXES[1]), GLOBE_AXES[2],
                     1e-9)
    system = self.systemOf()
    cockpit, scenery = Cockpit(), Scenery()
    every = pieces(cockpit.controls)
    dash = {'needles': [0.0] * 4, 'lamps': [False] * 6,
            'legends': [False] * 7, 'reels': (0.0, 0.0), 'column': 0.0,
            'knob': 0.0, 'bug': 0.5, 'guards': {}, 'flicker': 1.0}
    dash.update(_resting())
    held, marked = [], 0
    for nose in ('up', 'ahead'):
      vessel = self.orbiting(system, 300e3, 300e3, nose)
      ball = Navball().frameOf(vessel, system, 104.0)
      rocket = ((0.0, 0.0, 0.0), vessel.turn, True)
      parts = scenery.cabinOf(system, vessel, cockpit, rocket, ball, dash,
                              True)['parts']
      part = parts[len(every)]
      self.assertClose(unrotated(vessel.turn, part[0]), ballCentre(), 1e-9)
      held.append(product(_inverse(vessel.turn), part[1]))
      ring, axles, hubs = scenery.mechanismOf(ball['turn'])
      pole = rotated(ball['turn'], (0.0, 0.0, 1.0))
      self.assertClose(rotated(hubs, (0.0, 1.0, 0.0)), pole, 1e-9)
      across = rotated(axles, (1.0, 0.0, 0.0))
      self.assertAlmostEqual(sum(a * b for a, b in zip(across, pole)), 0.0,
                             9)
      self.assertClose(rotated(ring, (0.0, 0.0, 1.0)), (0.0, 0.0, 1.0),
                       1e-9)
      first = len(every) + 1 + len(MECHANISM)
      for k in range(len(MARK_KINDS)):
        mark = parts[first + k]
        if not mark[2]:
          continue
        marked += 1
        local = unrotated(vessel.turn, mark[0])
        self.assertAlmostEqual(math.dist(local, ballCentre()),
                               BALL_RADIUS + MARK_OVER, 9)
    self.assertGreater(marked, 0)
    self.assertGreater(_turnClose(held[0], held[1]), 0.5)
