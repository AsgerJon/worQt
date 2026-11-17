"""
DockingPort is the rocket's nose meeting the space station's port
(user, 2026-11-17: "Get the docking!"; "we include buttons so that a
try-hard *could* manually do the thing ... But where we also provide an
automated system for the rest of. Same with docking"): how the rocket's
nose stands to the station's port (how far, along and off its axis,
closing how fast, tilted how far, turning with it or not); the latch
catching it; riding docked, the rocket moved with the station, not by
the flight; undocking, pushed gently off. Qt-free.

The station's port is its hub's mouth on its axis (its own +z); the
rocket docks nose first down that axis (its nose its own +z: down the
station's -z), turning with the station.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._station import SPIN
from ._stationmeshes import portTip
from ._turns import cross, dot, matrixBack, matrixTimes, norm
from ._turns import quaternionOf, rotated, unit, unrotated
from ._vessel import CAPSULE, CENTRE

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._station import Station
  from ._vessel import Vessel

#  The rocket's port: the tip of its nose (its own axes).
NOSE_PORT = (0.0, 0.0, CAPSULE[1] - CENTRE)
#  The latch catches the nose within 'CATCH' m of the station's port,
#  closing no faster than 'CLOSING' m/s, tilted from the station's axis
#  no more than 'TILT', turning with the station within 'TURNING' rad/s.
CATCH = 1.5
CLOSING = 1.0
TILT = math.radians(8.0)
TURNING = 0.03
#  Undocking pushes the rocket off along the station's axis, m/s.
PUSH_OFF = 0.3


class DockingPort:
  """
  DockingPort holds the docking of a vessel to 'station': 'readingOf'
  says how the vessel's nose stands to the station's port; 'caught'
  whether the latch would catch it; 'aligned' notes the vessel's turn in
  the station's axes, its nose put down the station's axis (its roll
  kept: 'relative', the station's own axes of the vessel's), and
  'turnAt' gives the turn that is at a time (what matching it holds);
  'latched' docks the vessel, 'heldOn' moves it with the station,
  'released' pushes it off.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('relative',)

  #  Public Variables
  station: Station
  relative: tuple | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, station: Station) -> None:
    self.station, self.relative = station, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def readingOf(self, vessel: Vessel, system: SolarSystem,
                t: float) -> dict:
    """The 'readingOf' method returns how the vessel's nose stands to
    the station's port at time 't': 'distance' between them, how far out
    along the station's axis ('along') and off it ('across'), m; how
    fast it closes in along the axis ('closing', m/s), its drift ('drift':
    its velocity from the port's, m/s) and its offset ('offset', m), each
    the ecliptic's axes from the vessel's anchor; how far its nose is
    tilted off the axis ('tilt', rad) and how far its spin is off the
    station's ('turning', rad/s); the station's 'axis', 'port' and
    'velocity' (its middle's, from the vessel's anchor)."""
    station = self.station
    there, moving = system.relative(station.parent, vessel.anchor, t)
    middle, velocity = station.stateAt(t)
    middle = tuple(a + b for a, b in zip(there, middle))
    velocity = tuple(a + b for a, b in zip(moving, velocity))
    rows = station.turnAt(t)
    axis = tuple(row[2] for row in rows)
    port = tuple(m + p for m, p in zip(middle, matrixTimes(rows,
                                                           portTip())))
    nose = tuple(p + n for p, n in zip(vessel.place, rotated(
      vessel.turn, NOSE_PORT)))
    offset = tuple(n - p for n, p in zip(nose, port))
    along = dot(offset, axis)
    drift = tuple(v - s for v, s in zip(vessel.velocity, velocity))
    way = rotated(vessel.turn, (0.0, 0.0, 1.0))
    spin = rotated(vessel.turn, vessel.spin)
    return {'distance': norm(offset), 'along': along,
            'across': norm(tuple(o - along * a for o, a in zip(offset,
                                                               axis))),
            'closing': -dot(drift, axis), 'drift': drift, 'offset': offset,
            'tilt': math.acos(max(-1.0, min(1.0, -dot(way, axis)))),
            'turning': norm(tuple(s - SPIN * a for s, a in zip(spin,
                                                               axis))),
            'axis': axis, 'port': port, 'velocity': velocity}

  def caught(self, reading: dict) -> bool:
    """The 'caught' method returns whether the latch catches the nose
    standing so ('readingOf')."""
    return (reading['distance'] <= CATCH and reading['closing'] <= CLOSING
            and reading['tilt'] <= TILT
            and reading['turning'] <= TURNING)

  def aligned(self, vessel: Vessel, t: float) -> None:
    """The 'aligned' method notes the vessel's turn in the station's own
    axes at time 't', put nose first down the station's axis, its roll
    kept ('relative': the vessel's own axes in the station's)."""
    rows = self.station.turnAt(t)
    side = matrixBack(rows, rotated(vessel.turn, (1.0, 0.0, 0.0)))
    flat = unit((side[0], side[1], 0.0)) if math.hypot(
      side[0], side[1]) > 1e-6 else (1.0, 0.0, 0.0)
    down = (0.0, 0.0, -1.0)
    self.relative = (flat, cross(down, flat), down)

  def turnAt(self, t: float) -> tuple:
    """The 'turnAt' method returns the vessel's turn (w x y z) its noted
    one in the station's axes ('aligned') is at time 't'."""
    rows = self.station.turnAt(t)
    columns = tuple(matrixTimes(rows, c) for c in self.relative)
    return quaternionOf(tuple(tuple(columns[k][i] for k in range(3))
                              for i in range(3)))

  def latched(self, vessel: Vessel, system: SolarSystem,
              t: float) -> None:
    """The 'latched' method docks the vessel at time 't': its turn
    noted in the station's axes, its engine and thrusters shut, its
    autopilot off: from now the station moves it ('heldOn'); the latch
    takes its drift off at once, a jolt it feels."""
    self.aligned(vessel, t)
    vessel.docked = True
    vessel.engine.throttled(0.0)
    vessel.rcs = (0.0, 0.0, 0.0)
    vessel.autopilot.engaged('off', vessel.turn)
    before = vessel.velocity
    self.heldOn(vessel, system, t)
    vessel.jolted(tuple(a - b for a, b in zip(vessel.velocity, before)))

  def heldOn(self, vessel: Vessel, system: SolarSystem, t: float) -> None:
    """The 'heldOn' method puts the docked vessel where the station has
    it at time 't': its nose in the port, turned as noted, moving and
    turning with the station; and what it feels, the latch's push a
    kilogram (user, 2026-11-17: "The experienced gravity in microgravity
    is the gravity pulled by the planet orbited minus the centri force
    caused by the movement about the planet"): how it is moved (the
    station's middle falling round its planet, the vessel's middle
    carried round the station's axis) less how gravity pulls it there;
    its spin steady."""
    station = self.station
    if vessel.anchor != station.parent:
      raise ValueError('docked to a station round body %d, kept from %d'
                       % (station.parent, vessel.anchor))
    turn = self.turnAt(t)
    reading = self.readingOf(vessel, system, t)
    place = tuple(p - n for p, n in zip(reading['port'], rotated(
      turn, NOSE_PORT)))
    axis = reading['axis']
    spin = tuple(SPIN * a for a in axis)
    vessel.placed(vessel.anchor, place, reading['velocity'], turn,
                  unrotated(turn, spin))
    middle, _ = station.stateAt(t)
    mu = system.bodies[station.parent].mu
    far = norm(middle)
    falling = tuple(-mu * m / far ** 3 for m in middle)
    offset = tuple(p - m for p, m in zip(place, middle))
    carried = cross(spin, cross(spin, offset))
    pulled = system.pullOn(vessel.anchor, place, t)
    vessel.felt = unrotated(turn, tuple(f + c - g for f, c, g in zip(
      falling, carried, pulled)))
    vessel.spinning = (0.0, 0.0, 0.0)

  def released(self, vessel: Vessel, system: SolarSystem,
               t: float) -> None:
    """The 'released' method undocks the vessel at time 't': pushed off
    along the station's axis at 'PUSH_OFF', still turning as it turned
    with the station."""
    reading = self.readingOf(vessel, system, t)
    velocity = tuple(v + PUSH_OFF * a for v, a in zip(reading['velocity'],
                                                      reading['axis']))
    vessel.docked = False
    vessel.jolted(tuple(PUSH_OFF * a for a in reading['axis']))
    vessel.placed(vessel.anchor, vessel.place, velocity, vessel.turn,
                  vessel.spin)

