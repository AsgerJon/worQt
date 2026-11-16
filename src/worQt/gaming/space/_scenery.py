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

from ._meshes import CAP_REACH
from ._orrery import SPAN
from ._planets import PAD
from ._turns import cross, dot, matrixBack, matrixTimes, norm
from ._turns import quaternionOf, unit

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._chasecamera import ChaseCamera
  from ._orrery import Orrery
  from ._solarsystem import SolarSystem
  from ._vessel import Vessel

#  Past this from the eye a body is drawn nearer, by the logarithm of how
#  much further it is, 'FAR_LOG' m an e-fold: Pluto lands within 2 FAR.
FAR = 1e6
FAR_LOG = FAR / 16.0
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
    self.capCentre, self.capBody = None, -1

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def flightOf(self, system: SolarSystem, vessel: Vessel,
               chase: ChaseCamera, t: float) -> dict:
    """The 'flightOf' method returns a frame of the flight view at time
    't': 'forward' and 'up' (the eye's), 'far' (each body's place from
    the eye, turn and drawn radius), 'rocket' and 'pad' (each its place,
    turn, shown), 'cap' (its place, turn, shown, and its middle and
    radius when it is to be made anew, else None), 'sun' (the way its
    light goes) and 'sky' (its colour)."""
    offset, forward, up = chase.eyeOf(vessel, system)
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
    return {'forward': forward, 'up': up, 'far': far, 'rocket': rocket,
            'pad': self._padOf(system, anchor, turn, eye),
            'cap': self._capOf(body, anchor, turn, eye),
            'sun': sun, 'sky': self._skyOf(body, eye, sun)}

  def mapOf(self, system: SolarSystem, vessel: Vessel, orrery: Orrery,
            t: float, wide: float, high: float) -> dict:
    """The 'mapOf' method returns a frame of the map at time 't' on a
    view 'wide' by 'high' pixels: the eye's 'forward' and 'up'; 'bodies'
    (each body's place, turn, radius, scaled to the map); 'lines' (each
    body's path's middle, its parent, and scale; Sol's none); the
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
    return {'forward': forward, 'up': up, 'bodies': bodies, 'lines': lines,
            'path': orrery.pathOf(vessel, system),
            'pathAt': (tuple(-scale * x for x in eye), scale),
            'marks': orrery.marksOf(vessel, system, t, wide, high)}

  def orbitsOf(self, system: SolarSystem) -> list:
    """The 'orbitsOf' method returns each body's path round its parent
    (Sol's None): points from the parent, m, the first again last."""
    out = [None]
    for body in system.bodies[1:]:
      points = body.conic.pathPoints(ORBIT_POINTS, 0.0)
      out.append(points + points[:1])
    return out

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

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
