"""
DockingPort is the rocket's nose meeting the space station's port
(user, 2026-11-17: "Get the docking!"; "we include buttons so that a
try-hard *could* manually do the thing ... But where we also provide an
automated system for the rest of. Same with docking"): how the rocket's
nose stands to the station's port (how far, along and off its axis,
closing how fast, tilted how far, turning with it or not); the port's
ring catching it and drawing it in (a spring and damper to the port's
mouth and to the turn it docks at, the flight's kernel's: user,
2026-11-18, "PHYSICS MUST BE REAL"; it snapped into place before); home,
the latches lock and the two are one body (the station's flown body
then the pair's: their mass, middle, moments, their momentum and spin
kept), the rocket where the pair has it; undocking, a spring pushes
them apart, each as hard. Qt-free.

The station's ports are its drum's hole, entered from either face
(user, 2026-11-18: "Terra Prime should have docking ports on both
sides"; its own +z and -z: 'side'; 2026-11-19: "the head our rocket
insert itself here, so that the spokes align with the doors to our top
floor"); the rocket docks from the side its middle is on, nose first
down that axis (its nose its own +z) through the hole till its top
floor is in the station's plane, turning with the station, rolled so
its four doors face the four shafts (the hole's guides catch it within
'ROLL' of that and turn it the rest of the way in).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._station import INERTIA, MASS
from ._stationmeshes import portTip
from ._turns import cross, dot, matrixBack, matrixTimes, norm, product
from ._turns import quaternionOf, rotated, unrotated
from ._vessel import CAPSULE, CENTRE

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._solarsystem import SolarSystem
  from ._station import Station
  from ._vessel import Vessel

#  The rocket's port: the tip of its nose (its own axes).
NOSE_PORT = (0.0, 0.0, CAPSULE[1] - CENTRE)
#  Its doors face its own x, y, -x, -y; the station's shafts its own x,
#  y, -x, -y: the hole's guides catch the nose rolled within 'ROLL' of a
#  quarter turn's (rad).
ROLL = math.radians(10.0)
QUARTER = 0.5 * math.pi
#  The latch catches the nose within 'CATCH' m of the station's port,
#  closing no faster than 'CLOSING' m/s, tilted from the station's axis
#  no more than 'TILT', turning with the station within 'TURNING' rad/s.
CATCH = 1.5
CLOSING = 1.0
TILT = math.radians(8.0)
TURNING = 0.03
#  Drawn in, the latches lock once the nose is within 'HOME' m of the
#  port's mouth, turned within 'HOME_TURN' of the turn it docks at,
#  moving and turning with the station within 'HOME_DRIFT' m/s and
#  'HOME_SPIN' rad/s.
HOME = 0.01
HOME_TURN = math.radians(0.2)
HOME_DRIFT = 0.01
HOME_SPIN = 0.002
#  Undocking a spring pushes the rocket and the station apart along the
#  station's axis till they part this fast, m/s.
PUSH_OFF = 0.3


class DockingPort:
  """
  DockingPort holds the docking of a vessel to 'station' at one of its
  ports ('side': its +z port, one; its -z, minus one: undocked, the one
  on the vessel's nose's side, 'readingOf' chooses it): 'readingOf'
  says how the vessel's nose stands to that port; 'caught' whether the
  port's ring would catch it, 'captured' has it catch it (the vessel's
  'latch': the flight draws it in), 'home' whether it is drawn in;
  'aligned' notes the vessel's turn in the station's axes, its nose put
  down the station's axis into that port (its roll kept: 'relative', the
  station's own axes of the vessel's), and 'turnAt' gives the turn that
  is at a time (what matching it holds); 'latched' locks it, the two one
  body ('held': the vessel's middle from the pair's, the station's own
  axes), 'heldOn' puts the vessel where the pair has it, 'released'
  pushes them apart.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  What a saved game keeps of it ('_savegame'): its fields.
  SAVED = ('relative', 'side', 'held')

  #  Public Variables
  station: Station
  relative: tuple | None
  side: float
  held: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, station: Station) -> None:
    self.station, self.relative, self.side = station, None, 1.0
    self.held = (0.0, 0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def readingOf(self, vessel: Vessel, system: SolarSystem,
                t: float) -> dict:
    """The 'readingOf' method returns how the vessel's nose stands to
    the station's port at time 't' (undocked, the port on its nose's
    side: 'side' chosen anew, a noted turn noted anew for it): 'distance'
    between them, how far out along the port's way ('along') and off the
    station's axis ('across'), m; how fast it closes in along it
    ('closing', m/s), its drift ('drift': its velocity from the port's,
    m/s) and its offset ('offset', m), each the ecliptic's axes from the
    vessel's anchor; how far its nose is tilted off the axis ('tilt',
    rad) and how far its spin is off the station's ('turning', rad/s);
    the port's way out ('axis'), the station's spin ('spin', rad/s), the
    port's place ('port') and the station's middle's 'velocity' (from
    the vessel's anchor); how far its roll is from its doors facing the
    shafts ('roll', rad)."""
    station = self.station
    there, moving = system.relative(station.parent, vessel.anchor, t)
    middle, velocity = station.stateAt(t)
    middle = tuple(a + b for a, b in zip(there, middle))
    velocity = tuple(a + b for a, b in zip(moving, velocity))
    rows = station.turnAt(t)
    own = tuple(row[2] for row in rows)
    nose = tuple(p + n for p, n in zip(vessel.place, rotated(
      vessel.turn, NOSE_PORT)))
    if not vessel.docked:
      side = 1.0 if dot(tuple(p - m for p, m in zip(vessel.place, middle)),
                        own) >= 0.0 else -1.0
      if side != self.side:
        self.side = side
        if self.relative is not None:
          self.aligned(vessel, t)
    axis = tuple(self.side * o for o in own)
    port = tuple(m + p for m, p in zip(middle, matrixTimes(
      rows, portTip(self.side))))
    offset = tuple(n - p for n, p in zip(nose, port))
    along = dot(offset, axis)
    drift = tuple(v - s for v, s in zip(vessel.velocity, velocity))
    way = rotated(vessel.turn, (0.0, 0.0, 1.0))
    spin = rotated(vessel.turn, vessel.spin)
    turning = station.spinAt(t)
    flat = matrixBack(rows, rotated(vessel.turn, (1.0, 0.0, 0.0)))
    roll = math.atan2(flat[1], flat[0])
    roll = abs(roll - QUARTER * round(roll / QUARTER))
    return {'distance': norm(offset), 'along': along, 'roll': roll,
            'across': norm(tuple(o - along * a for o, a in zip(offset,
                                                               axis))),
            'closing': -dot(drift, axis), 'drift': drift, 'offset': offset,
            'tilt': math.acos(max(-1.0, min(1.0, -dot(way, axis)))),
            'turning': norm(tuple(s - w for s, w in zip(spin, turning))),
            'axis': axis, 'spin': turning,
            'port': port, 'velocity': velocity}

  def caught(self, reading: dict) -> bool:
    """The 'caught' method returns whether the latch catches the nose
    standing so ('readingOf')."""
    return (reading['distance'] <= CATCH and reading['closing'] <= CLOSING
            and reading['tilt'] <= TILT and reading['roll'] <= ROLL
            and reading['turning'] <= TURNING)

  def aligned(self, vessel: Vessel, t: float) -> None:
    """The 'aligned' method notes the vessel's turn in the station's own
    axes at time 't', put nose first down the station's axis into the
    port on its 'side', rolled to the nearest quarter turn that faces
    its doors to the shafts ('relative': the vessel's own axes in the
    station's)."""
    rows = self.station.turnAt(t)
    side = matrixBack(rows, rotated(vessel.turn, (1.0, 0.0, 0.0)))
    roll = math.atan2(side[1], side[0]) if math.hypot(
      side[0], side[1]) > 1e-6 else 0.0
    roll = QUARTER * round(roll / QUARTER)
    flat = (float(round(math.cos(roll))), float(round(math.sin(roll))),
            0.0)
    down = (0.0, 0.0, -self.side)
    self.relative = (flat, cross(down, flat), down)

  def turnAt(self, t: float) -> tuple:
    """The 'turnAt' method returns the vessel's turn (w x y z) its noted
    one in the station's axes ('aligned') is at time 't'."""
    rows = self.station.turnAt(t)
    columns = tuple(matrixTimes(rows, c) for c in self.relative)
    return quaternionOf(tuple(tuple(columns[k][i] for k in range(3))
                              for i in range(3)))

  def captured(self, vessel: Vessel, t: float) -> None:
    """The 'captured' method has the port's ring catch the vessel's nose
    at time 't': its turn noted in the station's axes ('aligned'), its
    engine and thrusters shut, its autopilot off; its 'latch' set (the
    flight draws it in from now: '_flight_kernels')."""
    self.aligned(vessel, t)
    vessel.engine.throttled(0.0)
    vessel.rcs = (0.0, 0.0, 0.0)
    vessel.autopilot.engaged('off', vessel.turn)
    vessel.latch = (portTip(self.side), self.relativeTurn(), NOSE_PORT)

  def home(self, vessel: Vessel, reading: dict, t: float) -> bool:
    """The 'home' method returns whether the caught nose is drawn home
    ('HOME', 'HOME_TURN', 'HOME_DRIFT', 'HOME_SPIN'), standing so
    ('readingOf' at time 't')."""
    if vessel.latch is None:
      return False
    wanted = self.turnAt(t)
    inner = abs(sum(a * b for a, b in zip(wanted, vessel.turn)))
    turned = 2.0 * math.acos(min(1.0, inner))
    return (reading['distance'] <= HOME and turned <= HOME_TURN
            and norm(reading['drift']) <= HOME_DRIFT
            and reading['turning'] <= HOME_SPIN)

  def relativeTurn(self, ) -> tuple:
    """The 'relativeTurn' method returns the noted turn ('relative') as a
    quaternion (w x y z): the vessel's own axes in the station's."""
    return quaternionOf(tuple(tuple(self.relative[k][i] for k in range(3))
                              for i in range(3)))

  def latched(self, vessel: Vessel, system: SolarSystem,
              t: float) -> None:
    """The 'latched' method locks the latches at time 't': the vessel and
    the station one body (the station's flown body the pair's: their
    mass, its middle, their moments about it in the station's own axes,
    their momentum and their spin about it kept), the station's middle
    where it is, the vessel home in the port (it was within 'HOME'); the
    vessel docked, where the pair has it ('heldOn'), what that changed of
    its motion felt as a jolt."""
    station = self.station
    body = station.body
    relative = self.relativeTurn()
    home = tuple(p - n for p, n in zip(portTip(self.side), rotated(
      relative, NOSE_PORT)))
    q = quaternionOf(station.turnAt(t))
    body.placed(body.anchor, body.place, body.velocity, q, body.spin)
    ms, mr = body.mass, vessel.mass
    whole = ms + mr
    ownS = tuple(-mr * h / whole for h in home)
    self.held = tuple(ms * h / whole for h in home)
    middle, moving = station.stateAt(t)
    pair = tuple(m - o for m, o in zip(middle, rotated(q, ownS)))
    velocity = tuple((ms * a + mr * b) / whole for a, b in zip(
      moving, vessel.velocity))
    momentum = [0.0, 0.0, 0.0]
    for mass, place, speed, turn, spin, inertia in (
        (ms, middle, moving, q, body.spin, body.inertia),
        (mr, vessel.place, vessel.velocity, vessel.turn, vessel.spin,
         vessel.inertia)):
      own = rotated(turn, tuple(i * w for i, w in zip(inertia, spin)))
      orbit = cross(tuple(p - c for p, c in zip(place, pair)), tuple(
        mass * (s - v) for s, v in zip(speed, velocity)))
      momentum = [a + b + c for a, b, c in zip(momentum, own, orbit)]
    moments = _pairMoments(ms, body.inertia, ownS, mr, vessel.inertia,
                           relative, self.held)
    spin = tuple(m / i for m, i in zip(unrotated(q, tuple(momentum)),
                                       moments))
    body.mass, body.inertia = whole, moments
    body.placed(body.anchor, pair, velocity, q, spin)
    station.offset, station.at = ownS, t
    before = vessel.velocity
    vessel.docked, vessel.latch = True, None
    vessel.touching = 0
    self.heldOn(vessel, system, t)
    vessel.jolted(tuple(a - b for a, b in zip(vessel.velocity, before)))

  def homed(self, vessel: Vessel, t: float) -> None:
    """The 'homed' method puts the vessel home in the port at time 't'
    (nose in its mouth, turned as noted: 'relative'), moving and turning
    with the station, not docked."""
    station = self.station
    middle, moving = station.stateAt(t)
    q = quaternionOf(station.turnAt(t))
    relative = self.relativeTurn()
    turn = product(q, relative)
    arm = rotated(q, tuple(p - n for p, n in zip(portTip(self.side),
                                                 rotated(relative,
                                                         NOSE_PORT))))
    spin = station.spinAt(t)
    vessel.placed(station.parent, tuple(m + a for m, a in zip(middle, arm)),
                  tuple(v + c for v, c in zip(moving, cross(spin, arm))),
                  turn, unrotated(turn, spin))

  def teleported(self, vessel: Vessel, system: SolarSystem,
                 t: float) -> None:
    """The 'teleported' method docks the vessel at once at time 't' (the
    debug menu's warp: no approach): put home in the port on the
    station's own z side ('homed'), nose down its axis, its own x the
    station's, its engine, thrusters and autopilot shut, then
    latched."""
    if vessel.docked:
      return
    self.side = 1.0
    self.relative = ((1.0, 0.0, 0.0), (0.0, -1.0, 0.0), (0.0, 0.0, -1.0))
    self.homed(vessel, t)
    vessel.touching, vessel.latch = 0, None
    vessel.engine.throttled(0.0)
    vessel.rcs = (0.0, 0.0, 0.0)
    vessel.steered(0.0, 0.0, 0.0)
    vessel.autopilot.engaged('off', vessel.turn)
    vessel.felt, vessel.spinning = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    self.latched(vessel, system, t)
    vessel.jolt = (0.0, 0.0, 0.0)

  def heldOn(self, vessel: Vessel, system: SolarSystem, t: float) -> None:
    """The 'heldOn' method puts the docked vessel where the pair has it
    at time 't' (its middle 'held' from the pair's, turned as noted,
    moving and turning with it) and has it feel what the pair feels
    there (user, 2026-11-17: "The experienced gravity in microgravity is
    the gravity pulled by the planet orbited minus the centri force
    caused by the movement about the planet"): the pair's push, its
    turning and its turning faster at the vessel's middle, less how
    gravity pulls the vessel more than the pair's middle (the tide)."""
    station = self.station
    if vessel.anchor != station.parent:
      raise ValueError('docked to a station round body %d, kept from %d'
                       % (station.parent, vessel.anchor))
    body = station.body
    q, relative = quaternionOf(station.turnAt(t)), self.relativeTurn()
    middle, moving = station.stateAt(t)
    arm = rotated(q, tuple(h - o for h, o in zip(self.held,
                                                 station.offset)))
    spin = station.spinAt(t)
    place = tuple(p + a for p, a in zip(middle, arm))
    turn = product(q, relative)
    vessel.placed(body.anchor, place, tuple(
      v + c for v, c in zip(moving, cross(spin, arm))), turn,
                  unrotated(relative, body.spin))
    felt = body.felt or (0.0, 0.0, 0.0)
    faster = body.spinning or (0.0, 0.0, 0.0)
    carried = cross(body.spin, cross(body.spin, self.held))
    swung = cross(faster, self.held)
    pair = tuple(m - c for m, c in zip(middle, rotated(q, station.offset)))
    tide = unrotated(q, tuple(a - b for a, b in zip(
      system.pullOn(body.anchor, place, t),
      system.pullOn(body.anchor, pair, t))))
    own = tuple(f + c + s - d for f, c, s, d in zip(felt, carried, swung,
                                                    tide))
    vessel.felt = unrotated(relative, own)
    vessel.spinning = unrotated(relative, faster)

  def parted(self, vessel: Vessel, system: SolarSystem, t: float) -> None:
    """The 'parted' method parts the docked pair at time 't' without a
    push (the debug menu's warp takes the rocket elsewhere): the
    station's body its own again, moving and turning as its part of the
    pair did; undocked, nothing."""
    if not vessel.docked:
      return
    station = self.station
    body = station.body
    middle, moving = station.stateAt(t)
    q = quaternionOf(station.turnAt(t))
    body.mass, body.inertia = MASS, INERTIA
    body.placed(body.anchor, middle, moving, q, body.spin)
    station.offset, self.held = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    station.at = t
    vessel.docked = False

  def released(self, vessel: Vessel, system: SolarSystem,
               t: float) -> None:
    """The 'released' method undocks the vessel at time 't': the pair
    parted (each as it was moving there, turning alike: their momentum
    and spin kept), the station's body its own again; a spring pushes
    them apart along the station's axis till they part at 'PUSH_OFF',
    each as hard (the light rocket the faster), felt as a jolt."""
    station = self.station
    body = station.body
    self.heldOn(vessel, system, t)
    middle, moving = station.stateAt(t)
    q = quaternionOf(station.turnAt(t))
    axis = rotated(q, (0.0, 0.0, self.side))
    ms, mr = MASS, vessel.mass
    whole = ms + mr
    body.mass, body.inertia = MASS, INERTIA
    body.placed(body.anchor, middle, tuple(
      v - PUSH_OFF * mr / whole * a for v, a in zip(moving, axis)), q,
                body.spin)
    station.offset, self.held = (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)
    station.at = t
    push = tuple(PUSH_OFF * ms / whole * a for a in axis)
    vessel.docked = False
    vessel.jolted(push)
    vessel.placed(vessel.anchor, vessel.place, tuple(
      v + p for v, p in zip(vessel.velocity, push)), vessel.turn,
                  vessel.spin)


def _pairMoments(ms: float, inertiaS: tuple, ownS: tuple, mr: float,
                 inertiaR: tuple, relative: tuple, ownR: tuple) -> tuple:
  """Returns the pair's moments of inertia about its middle, the
  station's own axes: the station's ('inertiaS', its middle at 'ownS'
  from the pair's), the rocket's ('inertiaR' about its own axes, turned
  'relative' in the station's, its middle at 'ownR'), each carried to
  the pair's middle; its axes are the station's (the rocket lies down
  its axis: a product of inertia left over raises)."""
  tensor = [[0.0] * 3 for _ in range(3)]
  columns = tuple(rotated(relative, e) for e in (
    (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, 1.0)))
  for i in range(3):
    tensor[i][i] += inertiaS[i]
    for j in range(3):
      tensor[i][j] += sum(columns[k][i] * inertiaR[k] * columns[k][j]
                          for k in range(3))
  for mass, own in ((ms, ownS), (mr, ownR)):
    size2 = sum(o * o for o in own)
    for i in range(3):
      for j in range(3):
        tensor[i][j] += mass * ((size2 if i == j else 0.0) - own[i] * own[j])
  largest = max(tensor[k][k] for k in range(3))
  for i in range(3):
    for j in range(3):
      if i != j and abs(tensor[i][j]) > 1e-9 * largest:
        raise ValueError('the pair\'s moments are not about the '
                         'station\'s axes: %r' % (tensor,))
  return tuple(tensor[k][k] for k in range(3))
