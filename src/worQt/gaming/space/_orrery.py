"""
Orrery is the map (user, 2026-11-16: "we need a 'full map' that shows a
model of the solar system"; the spec: "It opens centred on the rocket
... The wheel zooms smoothly out to the whole solar system ... Clicking
a body centres the map on it"): where its eye is, and what it shows
where, worked out for the view to draw.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._turns import cross, dot, norm, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  The eye is this many scene units from what it looks at (the scene is
#  scaled to it each frame: float32 sees everything near its own size);
#  its field of view up and down, deg (Qt Quick 3D's own).
SPAN = 1000.0
FIELD = 60.0
#  How far the wheel takes the eye a notch; how near and far it may be,
#  m; rad a pixel dragged; how steep it may look, rad.
ZOOM = 1.2
NEAREST, FURTHEST = 2e3, 3e13
TURN = 0.005
STEEPEST = 1.5
#  A moon's mark this many pixels or nearer its planet's is not shown.
CROWDED = 14.0
#  A mark's label (14 px monospace, 8 px right of its dot): its line's
#  height and a letter's width, px; a label that would cover an earlier
#  one goes to the nearest free line ('line': down, then up), at most
#  'LINES' lines off (else it stays on its dot's).
LINE = 16.0
LETTER = 8.5
LINES = 3
#  A mark's colours.
BODY_COLOUR = '#cfd8e6'
VESSEL_COLOUR = '#7dff9a'
#  A satellite's mark (the space station's), and what marks it (no body:
#  not looked at by a click).
SATELLITE_COLOUR = '#ff8be0'
SATELLITE_MARK = -3
#  The closest approach's marks (the rocket then, the station then): not
#  clickable.
APPROACH_COLOUR = '#8fd3ff'
APPROACH_MARK = -4
APSIS_COLOUR = '#ffd36b'
#  The vessel's path: points along it; a hyperbola drawn out this many
#  times its periapsis.
PATH_POINTS = 360
PATH_REACH = 40.0


class Orrery:
  """
  Orrery holds the map's eye: what it looks at ('focus': a body's index,
  or -1 the vessel), how far it is from it ('distance', m), and round
  it ('yaw', 'pitch', rad, about the ecliptic's north). Everything is
  reckoned from the body the vessel is kept from (float64) and handed on
  from the eye, scaled so the eye is 'SPAN' units from its focus. The
  vessel's next closest approach to the space station ('closest', as
  '_approach.closestApproach' says it, its time left kept by the
  window; None: none) is marked: where the rocket and the station will
  be then.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  focus: int
  distance: float
  yaw: float
  pitch: float
  closest: tuple | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.focus, self.distance = -1, 3e7
    self.yaw, self.pitch = -0.5 * math.pi, 0.7
    self.closest = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def opened(self, vessel: Vessel, system: SolarSystem) -> None:
    """The 'opened' method centres the map on the vessel, far enough out
    to see its whole path round its anchor."""
    self.focus = -1
    conic = vessel.conicOf(system)
    far = norm(vessel.place) if conic is None else (
      conic.apoapsis if conic.closed else 4.0 * conic.periapsis)
    self.distance = max(NEAREST, min(FURTHEST, 3.5 * max(
      far, norm(vessel.place))))

  def turned(self, right: float, down: float) -> None:
    """The 'turned' method turns the eye round its focus as the mouse
    was dragged 'right' and 'down' pixels."""
    self.yaw -= TURN * right
    self.pitch = max(-STEEPEST, min(STEEPEST, self.pitch + TURN * down))

  def zoomed(self, notches: float) -> None:
    """The 'zoomed' method brings the eye nearer ('notches' over nought)
    or further."""
    self.distance = max(NEAREST, min(FURTHEST, self.distance
                                     * ZOOM ** -notches))

  def focused(self, focus: int, system: SolarSystem) -> None:
    """The 'focused' method centres the map on body 'focus' (-1: the
    vessel), near enough to see it and its moons."""
    self.focus = focus
    if focus >= 0:
      body = system.bodies[focus]
      children = system.children(focus)
      reach = max([system.bodies[k].conic.apoapsis for k in children]
                  or [20.0 * body.radius])
      self.distance = max(NEAREST, min(FURTHEST, 3.0 * reach))

  def eyeOf(self, vessel: Vessel, system: SolarSystem, t: float) -> tuple:
    """The 'eyeOf' method returns where the eye is (m, from the vessel's
    anchor), the way it looks, and its up."""
    there = self.placeOf(self.focus, vessel, system, t)
    way = (math.cos(self.pitch) * math.cos(self.yaw), math.cos(
      self.pitch) * math.sin(self.yaw), math.sin(self.pitch))
    eye = tuple(a + self.distance * b for a, b in zip(there, way))
    forward = tuple(-x for x in way)
    right = unit(cross(forward, (0.0, 0.0, 1.0)))
    return eye, forward, cross(right, forward)

  def placeOf(self, index: int, vessel: Vessel, system: SolarSystem,
              t: float) -> tuple:
    """The 'placeOf' method returns where body 'index' (-1: the vessel)
    is from the vessel's anchor, m."""
    if index < 0:
      return vessel.place
    return system.relative(index, vessel.anchor, t)[0]

  def marksOf(self, vessel: Vessel, system: SolarSystem, t: float,
              wide: float, high: float) -> list:
    """The 'marksOf' method returns the marks over the map, each a dict:
    where on the view (x, y pixels), its 'text', 'colour' and what it
    marks ('index': a body's, -1 the vessel, -2 an apsis, -3 a
    satellite: the space station); a moon's left out when it crowds its
    planet's."""
    eye, forward, up = self.eyeOf(vessel, system, t)
    seen = {}
    out = []
    for index, body in enumerate(system.bodies):
      at = self.screenOf(system.relative(index, vessel.anchor, t)[0], eye,
                         forward, up, wide, high)
      if at is None:
        continue
      parent = system.parents[index]
      if parent in seen and math.dist(at, seen[parent]) < CROWDED:
        continue
      seen[index] = at
      out.append({'x': at[0], 'y': at[1], 'text': body.name,
                  'colour': BODY_COLOUR, 'index': index})
    for satellite in system.satellites:
      parent = system.bodies.index(satellite.parent)
      place = tuple(a + b for a, b in zip(system.relative(
        parent, vessel.anchor, t)[0], satellite.stateAt(t)[0]))
      at = self.screenOf(place, eye, forward, up, wide, high)
      if at is not None:
        out.append({'x': at[0], 'y': at[1], 'text': satellite.name,
                    'colour': SATELLITE_COLOUR, 'index': SATELLITE_MARK})
    at = self.screenOf(vessel.place, eye, forward, up, wide, high)
    if at is not None:
      out.append({'x': at[0], 'y': at[1], 'text': 'You',
                  'colour': VESSEL_COLOUR, 'index': -1})
    middle = seen.get(vessel.anchor)
    for mark in self._apsides(vessel, system, eye, forward, up, wide,
                              high):
      if middle is None or math.dist((mark['x'], mark['y']),
                                     middle) >= CROWDED:
        out.append(mark)
    return _uncrowded(out + self._approached(eye, forward, up, wide,
                                             high))

  def pathOf(self, vessel: Vessel, system: SolarSystem) -> list:
    """The 'pathOf' method returns points along the vessel's path round
    its anchor (m, from the anchor), a closed one's first again last."""
    conic = vessel.conicOf(system)
    if conic is None:
      return [vessel.place, (0.0, 0.0, 0.0)]
    points = conic.pathPoints(PATH_POINTS, PATH_REACH * conic.periapsis)
    if conic.closed:
      points.append(points[0])
    return points

  def screenOf(self, place: tuple, eye: tuple, forward: tuple, up: tuple,
               wide: float, high: float) -> tuple | None:
    """The 'screenOf' method returns where 'place' (m, from the vessel's
    anchor) shows on a view 'wide' by 'high' pixels from the eye at
    'eye' looking along 'forward', 'up' its up; None behind it."""
    d = tuple(a - b for a, b in zip(place, eye))
    depth = dot(d, forward)
    if depth <= 0.0:
      return None
    right = cross(forward, up)
    focal = 0.5 * high / math.tan(math.radians(0.5 * FIELD))
    return (0.5 * wide + focal * dot(d, right) / depth,
            0.5 * high - focal * dot(d, up) / depth)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _apsides(self, vessel: Vessel, system: SolarSystem, eye: tuple,
               forward: tuple, up: tuple, wide: float, high: float) -> list:
    """Returns the marks of the vessel's apoapsis and periapsis: their
    heights over its anchor's ground and the time till each."""
    conic = vessel.conicOf(system)
    radius = system.bodies[vessel.anchor].radius
    out = []
    if conic is None:
      return out
    for name, distance, time, side in (
        ('Ap', conic.apoapsis, conic.timeToApoapsis(0.0), -1.0),
        ('Pe', conic.periapsis, conic.timeToPeriapsis(0.0), 1.0)):
      if not math.isfinite(distance) or time is None:
        continue
      flat = (side * distance, 0.0, 0.0)
      place = tuple(row[0] * flat[0] for row in conic.turn)
      at = self.screenOf(place, eye, forward, up, wide, high)
      if at is None:
        continue
      out.append({'x': at[0], 'y': at[1], 'text': '%s %s  in %s' % (
        name, lengthText(distance - radius), timeText(time)),
                  'colour': APSIS_COLOUR, 'index': -2})
    return out


  def _approached(self, eye: tuple, forward: tuple, up: tuple,
                  wide: float, high: float) -> list:
    """Returns the marks of the closest approach (none without one):
    the rocket then, how near and how long till it; the station then."""
    if self.closest is None:
      return []
    wait, gap, _, place, there = self.closest
    out = []
    for at, text in ((place, 'Closest %s  in %s' % (lengthText(gap),
                                                    timeText(wait))),
                     (there, 'Terra Prime then')):
      shown = self.screenOf(at, eye, forward, up, wide, high)
      if shown is None or (out and math.dist(shown, (
          out[0]['x'], out[0]['y'])) < CROWDED):
        continue
      out.append({'x': shown[0], 'y': shown[1], 'text': text,
                  'colour': APPROACH_COLOUR, 'index': APPROACH_MARK})
    return out


def _uncrowded(marks: list) -> list:
  """Returns 'marks', each given the line its label sits on by its
  dot ('line', lines down; up is less than nought): the nearest that
  covers no earlier label (down first), its dot's own if none is."""
  boxes = []
  tries = [0] + [k * way for k in range(1, LINES + 1) for way in (1, -1)]
  for mark in marks:
    wide = LETTER * len(mark['text'])
    mark['line'] = 0
    for line in tries:
      top = mark['y'] + LINE * line
      if not any(abs(top - y) < LINE - 2.0 and mark['x'] < x + w
                 and x < mark['x'] + wide for x, y, w in boxes):
        mark['line'] = line
        break
    boxes.append((mark['x'], mark['y'] + LINE * mark['line'], wide))
  return marks


def lengthText(metres: float) -> str:
  """Returns 'metres' as people read it: m, km, Mm, Gm."""
  size = abs(metres)
  if size < 0.5:
    return '0 m'
  if size < 1e4:
    return '%.0f m' % metres
  if size < 1e7:
    return '%.1f km' % (metres / 1e3)
  if size < 1e10:
    return '%.0f km' % (metres / 1e3)
  return '%.2f AU' % (metres / 1.495978707e11)


def timeText(seconds: float) -> str:
  """Returns 'seconds' as a clock reads it: h:mm:ss, d and h past a
  day."""
  seconds = max(0.0, seconds)
  if seconds >= 86400.0:
    return '%dd %dh' % (seconds // 86400.0, (seconds % 86400.0) // 3600.0)
  return '%d:%02d:%02d' % (seconds // 3600.0, (seconds % 3600.0) // 60.0,
                           seconds % 60.0)
