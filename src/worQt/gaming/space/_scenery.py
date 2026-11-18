"""
Scenery works out what the space view draws where, each frame, from
the eye: the far layer's heavenly bodies (past 'FAR' m drawn nearer and
smaller in proportion: the same picture, within float32 and the depth
buffer), the near layer's rocket, pad and ground cap, the sun's light,
the sky's colour; and on the map, the bodies, their paths and marks.
Qt-free: plain numbers, float64 until the view takes them (each from the
eye, so small).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worQt.gaming.sandbox._skin import PARTS

from worQt.gaming.sandbox import Pushbutton, Slider

from ._cockpit import BALL_RADIUS, CAMERA_AT, CAMERA_LOOK, CAMERA_UP
from ._cockpit import FLOOR, GLOBE_AT, GLOBE_AXES, GUARD_OPEN, LIT_KEYS
from ._cockpit import panelPoint
from ._dashboard import BUGS, LEGENDS, ballCentre, dialAngle
from ._dashboard import dialAxes, dialCentre
from ._dashboard import HATCH_HINGE, HATCH_OPEN, guardHinge, headPlace
from ._dashboard import pieces
from ._deckmodel import AXIS, movingParts
from ._dockingport import NOSE_PORT
from ._furnishings import candleLight, lampLight, looseParts
from ._gunbeam import beamRows
from ._meshes import CAP_REACH
from ._night import shineOf
from ._walkway import BACK, SWING_AWAY, leafTurn
from ._bolts import axesOf
from ._walkwaymeshes import hallLight
from ._orrery import SPAN
from ._planets import PAD
from ._stationinterior import FAR_HIGH
from ._stationmeshes import beaconTips
from ._turns import aboutAxis, cross, dot, matrixBack, matrixTimes, norm
from ._turns import product, quaternionOf, rotated, unit, unrotated

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._cockpit import Cockpit
  from ._orrery import Orrery
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  Past this from the eye a body is drawn nearer, by the logarithm of how
#  much further it is, 'FAR_LOG' m an e-fold: Pluto lands within 2 FAR.
#  A satellite (the space station) shows within 'SATELLITE_SEEN' of the
#  eye (the near layer's reach), drawn as it is.
FAR = 1e6
FAR_LOG = FAR / 16.0
SATELLITE_SEEN = 2.9e6
#  Farther than this a satellite's lights (the station's beacons and its
#  windows) are drawn as points of light too (a bright light far off is
#  seen as a point however small it is; drawn as it is it would fall
#  between the pixels), m.
LIGHTS_FROM = 2e4
#  The station's bolts' rings glow this much (violet: magic).
BOLT_GLOW = 1.0
#  The door's leaf glows this share of its own colour (lit inside and out
#  alike: the tower's lights pass through walls).
DOOR_FILL = 0.15
#  The light near a body (user, 2026-11-17: the station "visible from
#  the gorund"): the body's shadow (the sun's light gone within it,
#  fading at its edge: '_night.shineOf') and its day side's light
#  thrown back up ('ALBEDO' of the sun's, as much as its lit share of
#  the face seen and as near as it is).
ALBEDO = 0.3
#  The pad shows within this of the eye, m; the ground's cap below this
#  height, m, made anew once the eye is a quarter of its reach off its
#  middle.
PAD_SEEN = 6e4
CAP_HIGH = 6e5
CAP_MOVED = 0.25 * CAP_REACH
#  The sky's blue on the ground at noon (0 to 255).
SKY = (110.0, 160.0, 225.0)
#  A path's points round a body.
ORBIT_POINTS = 256
#  The cabin: its marks on the horizon's globe (their 'Navball' kinds,
#  where they truly are: the globe is held level with the horizon); how
#  bright a lamp glows lit and not, a legend lit and
#  not; its lamp, under the nose (the vessel's own axes, m). Its moving
#  parts' order: the dashboard's pieces, the ball, its mechanism, its
#  marks, Asger's limbs ('AFTER_PIECES' after the pieces).
MARK_KINDS = ('prograde', 'retrograde', 'aim')
#  The horizon's mechanism (user, 2026-11-16: "a ball rotated by an
#  actual mechanism vaguely visible inside the dashboard"), a gimbal as
#  an attitude indicator's: the roll ring about the panel's out, the
#  pitch axles across it, the ball spinning on its poles' hubs; how far
#  from lock the ring is still turned (its pole near the out axis, it
#  keeps its turn); how much the marks painted on the ball glow; how far
#  over the ball they lie, m.
MECHANISM = ('ring', 'axles', 'hubs')
LOCKED = 0.05
MARK_GLOW = 0.6
MARK_OVER = 0.0008
LAMP_ON, LAMP_OFF = 1.3, 0.0
LEGEND_ON, LEGEND_OFF = 1.6, 0.05
CABIN_LIGHT = (0.0, 0.0, FLOOR + 3.5)
#  The panel's flood lamp, above it to his left and before it (the ball's
#  shading shows it round), and how much the ball glows of its own (an
#  instrument's backlight: lit only from outside it was black at night;
#  user, 2026-11-17: "have the ball-horizon emit light slightly": it
#  glows more, and lights what is near it a little, 'globeLight').
PANEL_LAMP = panelPoint(-0.35, 0.35, 0.2)
BALL_GLOW = 0.3
#  The hull's floodlight (user, 2026-11-16: "have a tiny bit of
#  artificial light outside the rocket so we can stuff on it during
#  takeoff"): over the closed circuit camera, along its look.
FLOOD_AT = (CAMERA_AT[0], CAMERA_AT[1], CAMERA_AT[2] + 0.15)
#  How much the dials' needles glow (their dials backlit); the enchanted
#  knobs' glint (laid as a screen: its streaks add light); the cabin's
#  lights (the candles' flames by their flicker), the candles' flames
#  going round below 'ROUND_BELOW' g (nothing carries their hot air
#  up).
NEEDLE_GLOW = 0.45
GLINT_GLOWS = {'warp': 1.3, 'action': 1.3}
#  How brightly the gravity egg's marble glows (user, 2026-11-18: "a ball
#  that emits light").
EGG_GLOW = 2.0
GLOWS = {'flames': 2.4, 'flames round': 2.0, 'shade': 0.55, 'bulbs': 1.8}
ROUND_BELOW = 0.2
#  How far the tape deck's stop and play knob turns from stop to play
#  (clockwise as one faces it), rad.
KNOB_TURN = 0.7
AFTER_PIECES = 1 + len(MECHANISM) + len(MARK_KINDS) + len(PARTS)
#  The nose's docking camera (user, 2026-11-17: "one that aims the
#  docking"): just past the tip of the nose (the vessel's own axes).
NOSE_CAMERA = (0.0, 0.0, NOSE_PORT[2] + 0.3)
#  His parts left out seen from his own eyes: his head, and his arms
#  (blocks a hand's breadth from his eyes: they hid both consoles).
UNSEEN = ('head', 'right arm', 'left arm')


class Scenery:
  """
  Scenery works out a frame of the flight view ('flightOf') and of the
  map ('mapOf'). It keeps the ground's cap: its middle ('capCentre', a
  unit vector in the anchor's own axes, None: none made) and on which
  body ('capBody'); a frame whose cap is to be made anew says so.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  capCentre: tuple | None
  capBody: int

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.capCentre, self.capBody, self._pieces = None, -1, None
    self._roll = 0.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def flightOf(self, system: SolarSystem, vessel: Vessel, seen: tuple,
               t: float) -> dict:
    """The 'flightOf' method returns a frame of the flight view at time
    't', seen from 'seen' (where the eye is from the vessel's middle, the
    way it looks and its up: the chase camera's, or Asger's eyes): the
    eye's 'forward' and 'up', 'far' (each body's place from the eye,
    turn and drawn radius), 'rocket' and 'pad' (each its place, turn,
    shown), 'satellites' (each of the system's: its place, turn, shown),
    'lights' (far satellites' lights as points: each its place from the
    eye and its rainbow's share, or below nought warm), 'shine' (how much
    of the sun's light reaches the eye: nought in the anchor's shadow),
    'earth' (the anchor's light thrown back: the way it goes and how
    strong, a share of the sun's), 'cap' (its place, turn, shown, and its
    middle and radius
    when it is to be made anew, else None), 'sun' (the way its light
    goes) and 'sky' (its colour)."""
    offset, forward, up = seen
    anchor = vessel.anchor
    body = system.bodies[anchor]
    eye = tuple(a + b for a, b in zip(vessel.place, offset))
    turn = body.turnAt(t)
    far = []
    for index, other in enumerate(system.bodies):
      there = system.relative(index, anchor, t)[0]
      d = tuple(a - b for a, b in zip(there, eye))
      size = norm(d)
      shown = size if size <= FAR else FAR + FAR_LOG * math.log(size / FAR)
      scale = shown / size if size > 0.0 else 1.0
      far.append((tuple(scale * x for x in d), quaternionOf(
        other.turnAt(t)), other.radius * scale))
    rocket = (tuple(-x for x in offset), vessel.turn, True)
    sol = system.relative(0, anchor, t)[0]
    sun = unit(tuple(a - b for a, b in zip(eye, sol)))
    satellites, lights = [], []
    for satellite in system.satellites:
      parent = satellite.parent
      there = tuple(a + b - c for a, b, c in zip(
        system.relative(parent, anchor, t)[0],
        satellite.stateAt(t)[0], eye))
      rows = satellite.turnAt(t)
      apart = norm(there)
      satellites.append((there, quaternionOf(rows),
                         apart < SATELLITE_SEEN))
      if LIGHTS_FROM < apart < SATELLITE_SEEN and not _hidden(
          eye, there, body.radius):
        lights.append((there, -1.0))
        tips = beaconTips()
        lights += [(tuple(a + b for a, b in zip(there, matrixTimes(
          rows, tip))), k / len(tips)) for k, tip in enumerate(tips)]
    shine, earth = self._litOf(body, eye, sun)
    return {'forward': forward, 'up': up, 'far': far, 'rocket': rocket,
            'satellites': satellites, 'lights': lights, 'shine': shine,
            'earth': earth,
            'pad': self._padOf(system, anchor, turn, eye),
            'cap': self._capOf(body, anchor, turn, eye),
            'sun': sun, 'sky': self._skyOf(body, eye, sun)}

  def cabinOf(self, system: SolarSystem, vessel: Vessel,
              cockpit: Cockpit, rocket: tuple, ball: dict, dash: dict,
              inside: bool) -> dict:
    """The 'cabinOf' method returns the cabin's moving parts this frame,
    the vessel's middle at 'rocket' from the eye: 'parts', each (place,
    turn, shown, glow), in the order the view keeps ('cabinPieces'): the
    dashboard's pieces ('_dashboard.pieces': each input as its
    FourthPeep stands, the needles at 'dash''s 'needles' (each a share
    of its scale), the lamps and legends lit by its 'lamps' and
    'legends', the tape deck's reels at its 'reels' and its knob at its
    'knob', the typehead at its 'column'), the horizon's ball (its
    'Navball.frameOf' as 'ball'), its marks, Asger's limbs (his head and
    arms left out 'inside' his eyes; 'Cockpit.figureOf'), the loose
    things where 'dash''s 'loose' has them, the candles' flames tall or
    round by its 'weight' (g at the candles), the gravity gun as its
    'gun' says (shown, his eyes' place and their frame's turn); 'light'
    (the cabin's lamp's
    place), 'lamp' (the panel's flood lamp's), 'flood' (the hull's
    floodlight: its place, the way it shines, its up), 'hygge' (the
    floor lamp's light's place, the candles', their flicker), 'egg' (the
    gravity egg's marble, where 'dash''s 'egg' has it: its light),
    'headlamp' (Asger's, as 'dash''s 'headlamp' has it: whether it is
    on, its place, the way it shines, its up) and
    'camera' (the closed circuit camera feeding the monitor, the
    nose's if 'dash''s 'nose' else the hull's: its place, the way it
    looks and its picture's up, from the eye)."""
    place, turn = rocket[0], vessel.turn

    def there(local: tuple) -> tuple:
      """Returns 'local' (the vessel's own axes) from the eye."""
      return tuple(a + b for a, b in zip(place, rotated(turn, local)))

    parts, seen = [], dict(dash, inside=inside)
    for piece in self.cabinPieces(cockpit):
      parts.append(self._pieceAt(piece, seen, there, turn))
    centre = ballCentre()
    panel = quaternionOf(tuple((GLOBE_AXES[0][k], GLOBE_AXES[1][k],
                                GLOBE_AXES[2][k]) for k in range(3)))
    held = ball['held']
    globe = product((panel[0], -panel[1], -panel[2], -panel[3]), held)
    parts.append((there(centre), product(turn, held), True, BALL_GLOW))
    for gimbal in self.mechanismOf(globe):
      parts.append((there(centre), product(turn, product(panel, gimbal)),
                    True, 0.0))
    for kind in MARK_KINDS:
      way = ball['ways'].get(kind)
      if way is None:
        parts.append(((0.0, 0.0, 0.0), turn, False, 0.0))
        continue
      out = BALL_RADIUS + MARK_OVER
      local = tuple(c + out * w for c, w in zip(centre, way))
      normal = unrotated(panel, way)
      parts.append((there(local), product(turn, product(panel, decalTurnOf(
        normal))), True, MARK_GLOW))
    for index, pivot, limb in cockpit.figureOf():
      shown = not (inside and PARTS[index][0] in UNSEEN)
      parts.append((there(pivot), product(turn, limb), shown, 0.0))
    return {'parts': parts, 'light': there(CABIN_LIGHT),
            'lamp': there(PANEL_LAMP),
            'globe': there(GLOBE_AT),
            'flood': (there(FLOOD_AT), rotated(turn, unit(CAMERA_LOOK)),
                      rotated(turn, CAMERA_UP)),
            'hygge': (there(lampLight()), there(candleLight()),
                      dash['flicker']),
            'egg': there(dash['egg']),
            'headlamp': self._headlampOf(there, turn, dash.get(
              'headlamp', HEADLAMP_OFF)),
            'camera': self._cameraOf(there, turn, dash['nose']),
            'aboard': dash.get('aboard', False),
            'beam': self._beamOf(there, turn, dash.get('beam', (False,))),
            'hand': (bool(dash.get('hand', dash['gun'][0])) and inside,
                     tuple(dash['gun'][3]) if len(dash['gun']) > 3 else (
                       0.0, 0.0, 0.0)),
            'swing': (dash.get('back', BACK), dash.get('swing',
                                                        SWING_AWAY)),
            'outdoor': (there(hallLight()), dash.get('swing', SWING_AWAY)
                        < SWING_AWAY)}

  def _headlampOf(self, there: object, turn: tuple, lamp: tuple) -> tuple:
    """Returns Asger's headlamp ('lamp' the window's: on, his eyes,
    the way they look, their up, the vessel's own axes) from the eye:
    whether it shines, its place, the way it shines, its up."""
    on, eye, look, up = lamp
    return (bool(on), there(eye), rotated(turn, unit(look)),
            rotated(turn, unit(up)))

  def _beamOf(self, there: object, turn: tuple, beam: tuple) -> tuple:
    """Returns the gravity gun's beam ('_gunbeam'; 'beam' the window's:
    shown, the muzzle and the bolt (the vessel's own axes), its phase and
    strength): its place from the eye, its turn, whether shown, its core's
    and its coils' meshes (None when not shown)."""
    if not beam[0]:
      return (0.0, 0.0, 0.0), turn, False, None, None
    _, start, end, phase, strength = beam
    core, coils = beamRows(tuple(e - s for e, s in zip(end, start)), phase,
                           strength)
    return there(start), turn, True, core, coils

  def _cameraOf(self, there: object, turn: tuple, nose: bool) -> tuple:
    """Returns the closed circuit camera feeding the monitor ('nose':
    the nose's docking camera, looking ahead along the nose, its
    picture's up the rocket's x; else the hull's, looking aft): its
    place from the eye, the way it looks and its picture's up."""
    if nose:
      return (there(NOSE_CAMERA), rotated(turn, (0.0, 0.0, 1.0)),
              rotated(turn, (1.0, 0.0, 0.0)))
    return (there(CAMERA_AT), rotated(turn, unit(CAMERA_LOOK)),
            rotated(turn, CAMERA_UP))

  def mechanismOf(self, ball: tuple) -> tuple:
    """The 'mechanismOf' method returns how the horizon's mechanism
    turns for the ball turned 'ball' (in the panel's own axes, as the
    mechanism rests: the ring flat, the axles along x, the hubs along
    y): the ring and its axles turned about the panel's out by the roll
    that brings the ball's pole above it, the hubs then pitched onto the
    pole. Near lock (the pole on the out axis) the ring keeps its turn."""
    pole = rotated(ball, (0.0, 0.0, 1.0))
    if math.hypot(pole[0], pole[1]) > LOCKED:
      self._roll = math.atan2(-pole[0], pole[1])
    pitch = math.asin(max(-1.0, min(1.0, pole[2])))
    ring = aboutAxis((0.0, 0.0, 1.0), self._roll)
    return ring, ring, product(ring, aboutAxis((1.0, 0.0, 0.0), pitch))

  def cabinPieces(self, cockpit: Cockpit) -> tuple:
    """The 'cabinPieces' method returns the dashboard's moving pieces of
    'cockpit' (kept: the view and the scenery keep their order)."""
    if self._pieces is None or self._pieces[0] is not cockpit:
      self._pieces = cockpit, pieces(cockpit.controls)
    return self._pieces[1]

  def _pieceAt(self, piece: tuple, dash: dict, there: object,
               turn: tuple) -> tuple:
    """Returns where a dashboard's piece is, its turn, shown, its glow."""
    kind, what = piece
    if kind == 'control':
      peep = what.peep
      pivot = peep.pivot
      if isinstance(peep, Pushbutton):
        lit = what.name in LIT_KEYS and dash['legends'][LEGENDS.index(
          what.name)]
        return (there(tuple(p + peep.sunk() * a for p, a in zip(
          pivot, peep.axis))), turn, True, (
          LEGEND_ON if lit else LEGEND_OFF) if what.name in LIT_KEYS
          else 0.0)
      if isinstance(peep, Slider):
        return (there(tuple(p + peep.along() * a for p, a in zip(
          pivot, peep.axis))), turn, True, 0.0)
      return (there(pivot), product(turn, aboutAxis(peep.axis,
                                                    peep.angle())), True,
              0.0)
    if kind == 'needle':
      angle = dialAngle(dash['needles'][what])
      return (there(dialCentre(what)), product(turn, aboutAxis(
        dialAxes(what)[2], -angle)), True, NEEDLE_GLOW)
    if kind == 'glint' and isinstance(what.peep, Pushbutton):
      peep = what.peep
      shown = bool(dash['legends'][LEGENDS.index(what.name)])
      return (there(tuple(p + peep.sunk() * a for p, a in zip(
        peep.pivot, peep.axis))), turn, shown, GLINT_GLOWS[what.action])
    if kind == 'glint':
      peep = what.peep
      return (there(peep.pivot), product(turn, aboutAxis(peep.axis,
                                                         peep.angle())),
              True, GLINT_GLOWS[what.action])
    if kind in GLOWS:
      flame = kind in ('flames', 'flames round')
      glow = GLOWS[kind] * (dash['flicker'] if flame else 1.0)
      shown = not flame or (kind == 'flames') == (
        dash['weight'] >= ROUND_BELOW)
      return there((0.0, 0.0, 0.0)), turn, shown, glow
    if kind == 'loose':
      place, held = dash['loose'][looseParts()[what][0]]
      return there(place), product(turn, held), True, 0.0
    if kind in ('gun', 'gun mark'):
      shown, eye, held = dash['gun'][:3]
      return there(eye), product(turn, held), shown and not dash.get(
        'inside', False), 0.0
    if kind == 'egg ball':
      return there(dash['egg']), turn, True, EGG_GLOW
    if kind == 'hatch':
      return there(HATCH_HINGE), product(turn, aboutAxis(
        (0.0, 1.0, 0.0), -HATCH_OPEN * dash.get('hatch', 0.0))), True, 0.0
    if kind in ('sbolt', 'sring'):
      bolts = dash.get('sbolts', ())
      if what >= len(bolts):
        return there((0.0, 0.0, 0.0)), turn, False, 0.0
      place, way = bolts[what]
      held = quaternionOf(tuple(zip(*axesOf(way))))
      return there(place), product(turn, held), True, (
        BOLT_GLOW if kind == 'sring' else 0.0)
    if kind in ('lift', 'lift glass'):
      place, held, shown = dash.get('lift', (((0.0, 0.0, 0.0), (
        1.0, 0.0, 0.0, 0.0), False),) * 4)[what + (
          2 if kind == 'lift glass' else 0)]
      return there(place), product(turn, held), shown, (
        0.15 if kind == 'lift' else 0.0)
    if kind == 'door':
      return there((0.0, 0.0, 0.0)), product(turn, leafTurn(dash.get(
        'door', 0.0))), True, DOOR_FILL
    if kind == 'door glass':
      return there((0.0, 0.0, 0.0)), product(turn, leafTurn(dash.get(
        'door', 0.0))), True, 0.0
    if kind == 'port door':
      return there((0.0, 0.0, FAR_HIGH - 0.05)), turn, bool(dash.get(
        'aboard', False)), 0.0
    if kind == 'car':
      cars = dash.get('cars', ())
      if what >= len(cars):
        return there((0.0, 0.0, 0.0)), turn, False, 0.0
      middle, held, shown = cars[what]
      return there(middle), product(turn, held), shown, 0.0
    if kind in ('guard', 'glint lid'):
      share = dash['guards'].get(what.action, 0.0)
      return (there(guardHinge(what)), product(turn, aboutAxis(
        what.axes[0], -GUARD_OPEN * share)), True,
              GLINT_GLOWS[what.action] if kind == 'glint lid' else 0.0)
    if kind == 'lamp':
      return (there((0.0, 0.0, 0.0)), turn, True,
              LAMP_ON if dash['lamps'][what] else LAMP_OFF)
    if kind == 'legend':
      return (there((0.0, 0.0, 0.0)), turn, True,
              LEGEND_ON if dash['legends'][what] else LEGEND_OFF)
    if kind == 'bug':
      dial = BUGS[what]
      return (there(dialCentre(dial)), product(turn, aboutAxis(
        dialAxes(dial)[2], -dialAngle(dash['bugs'][what]))), True, 0.0)
    if kind == 'check':
      checks = dash.get('checks', ())
      lit = what < len(checks) and checks[what]
      return (there((0.0, 0.0, 0.0)), turn, True,
              LAMP_ON if lit else LAMP_OFF)
    if kind == 'deck':
      part, index, _, pivot = movingParts()[what][:4]
      angle = (dash['reels'][index] if part == 'reel'
               else -KNOB_TURN * dash['knob'])
      return (there(pivot), product(turn, aboutAxis(AXIS, angle)), True,
              0.0)
    return there(headPlace(dash['column'])), turn, True, 0.0

  def mapOf(self, system: SolarSystem, vessel: Vessel, orrery: Orrery,
            t: float, wide: float, high: float) -> dict:
    """The 'mapOf' method returns a frame of the map at time 't' on a
    view 'wide' by 'high' pixels: the eye's 'forward' and 'up'; 'bodies'
    (each body's place, turn, radius, scaled to the map); 'lines' (each
    body's path's middle, its parent, and scale; Sol's none; then each
    satellite's); the
    vessel's 'path' (its points from its anchor), its middle and scale
    ('pathAt'); the 'marks'."""
    eye, forward, up = orrery.eyeOf(vessel, system, t)
    scale = SPAN / orrery.distance
    anchor = vessel.anchor
    places = [system.relative(k, anchor, t)[0]
              for k in range(len(system.bodies))]
    bodies, lines = [], []
    for index, body in enumerate(system.bodies):
      d = tuple(scale * (a - b) for a, b in zip(places[index], eye))
      bodies.append((d, quaternionOf(body.turnAt(t)), scale * body.radius))
      parent = system.parents[index]
      if parent >= 0:
        lines.append((tuple(scale * (a - b) for a, b in zip(
          places[parent], eye)), scale))
    for satellite in system.satellites:
      parent = satellite.parent
      lines.append((tuple(scale * (a - b) for a, b in zip(
        places[parent], eye)), scale))
    return {'forward': forward, 'up': up, 'bodies': bodies, 'lines': lines,
            'path': orrery.pathOf(vessel, system),
            'pathAt': (tuple(-scale * x for x in eye), scale),
            'marks': orrery.marksOf(vessel, system, t, wide, high)}

  def orbitsOf(self, system: SolarSystem) -> list:
    """The 'orbitsOf' method returns each body's path round its parent
    (Sol's None), then each satellite's: points from the parent, m, the
    first again last."""
    out = [None]
    for body in system.bodies[1:] + tuple(system.satellites):
      points = body.conic.pathPoints(ORBIT_POINTS, 0.0)
      out.append(points + points[:1])
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _litOf(self, body: object, eye: tuple, sun: tuple) -> tuple:
    """Returns how much of the sun's light reaches 'eye' (from 'body''s
    middle; the light going 'sun'): nought in the body's shadow, fading
    at its edge ('shineOf'); and the body's light thrown back up:
    the way it goes (out of the body) and how strong."""
    far = norm(eye)
    if far <= 0.0:
      return 1.0, ((0.0, 0.0, 1.0), 0.0)
    shine = shineOf(body.radius, eye, sun)
    up = tuple(e / far for e in eye)
    lit = 0.5 * (1.0 - dot(up, sun))
    return shine, (up, ALBEDO * lit * min(1.0, (body.radius / far) ** 2))

  def _padOf(self, system: SolarSystem, anchor: int, turn: tuple,
             eye: tuple) -> tuple:
    """Returns the pad's place from the eye, its turn (its own x east, y
    north, z up), whether it shows (on Terra, near the eye)."""
    if system.bodies[anchor].name != 'Terra':
      return (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), False
    radius = system.bodies[anchor].radius
    lat, lon = math.radians(PAD[0]), math.radians(PAD[1])
    up = (math.cos(lat) * math.cos(lon), math.cos(lat) * math.sin(lon),
          math.sin(lat))
    east = (-math.sin(lon), math.cos(lon), 0.0)
    north = cross(up, east)
    rows = tuple(matrixTimes(turn, x) for x in (east, north, up))
    frame = tuple((rows[0][k], rows[1][k], rows[2][k]) for k in range(3))
    there = tuple(radius * x for x in rows[2])
    place = tuple(a - b for a, b in zip(there, eye))
    return place, quaternionOf(frame), norm(place) < PAD_SEEN

  def _capOf(self, body: object, anchor: int, turn: tuple,
             eye: tuple) -> tuple:
    """Returns the ground's cap: its place from the eye, its turn (the
    body's own axes), whether it shows, and its middle and radius when
    it is to be made anew (else None)."""
    height = norm(eye) - body.radius
    if height > CAP_HIGH:
      return (0.0, 0.0, 0.0), (1.0, 0.0, 0.0, 0.0), False, None
    below = unit(matrixBack(turn, eye))
    made = None
    if self.capCentre is None or self.capBody != anchor or math.acos(
        max(-1.0, min(1.0, dot(below, self.capCentre)))) > CAP_MOVED:
      self.capCentre, self.capBody = below, anchor
      made = below, body.radius
    there = matrixTimes(turn, tuple(body.radius * x
                                    for x in self.capCentre))
    place = tuple(a - b for a, b in zip(there, eye))
    return place, quaternionOf(turn), True, made

  def _skyOf(self, body: object, eye: tuple, sun: tuple) -> tuple:
    """Returns the sky's colour at 'eye' (0 to 255 a channel): blue in the
    air by day, fading with the air's thinning and the sun's setting;
    black above it and at night."""
    air = body.air
    if air is None:
      return 0.0, 0.0, 0.0
    height = norm(eye) - body.radius
    thick = (air.densityAt(height) / air.densities[0]) ** 0.25
    high = -dot(unit(eye), sun)
    day = max(0.0, min(1.0, 6.0 * high + 0.3))
    return tuple(thick * day * x for x in SKY)


#  Asger's headlamp when the window tells nothing of it: off, at his eye
#  and looking ahead.
HEADLAMP_OFF = (False, (0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 0.0, 1.0))


def decalTurnOf(normal: tuple) -> tuple:
  """Returns how a mark's decal (resting flat, facing z) lies on the
  ball at the unit 'normal' (the panel's own axes): facing out of the
  ball there, its up the panel's up as near as the ball lets it."""
  up = (-normal[1] * normal[0], 1.0 - normal[1] * normal[1],
        -normal[1] * normal[2])
  size = norm(up)
  up = (0.0, 1.0, 0.0) if size < 1e-9 else tuple(x / size for x in up)
  right = cross(up, normal)
  return quaternionOf(tuple((right[k], up[k], normal[k]) for k in range(3)))


def _hidden(eye: tuple, there: tuple, radius: float) -> bool:
  """Returns whether a body 'radius' round (its middle 'eye' back from
  the eye) stands between the eye and what is 'there' from it."""
  reach = sum(x * x for x in there)
  if reach <= 0.0:
    return False
  share = min(1.0, max(0.0, -sum(e * t for e, t in zip(eye, there))
                       / reach))
  nearest = tuple(e + share * t for e, t in zip(eye, there))
  return sum(x * x for x in nearest) < radius * radius
