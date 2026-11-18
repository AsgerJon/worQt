"""
The numbers of Sol, its nine planets and Terra's two moons, and the
solar system made of them on a given day (user, 2026-11-16: "just put in
the 9 planets around Terra, and yes, Pluto *is* a fucking planet!";
"Sol is the common Danish word so that's it!"). Each planet starts where
the real one stands on that day (JPL's 'Keplerian elements for
approximate positions of the major planets', table 1, 1800 to 2050; Pluto
from the table's older edition, before it was dropped), moving as its
path then says (Sol's G M and its own summed). Terra is the Earth (its
true size, its G M: g 9.82, its day and tilt), off the Earth and Moon's
barycentre (the table's path) as far as its moons weigh: Luna, the Moon
on its mean path of the day (its mean elements, Meeus), and Mani, a
small one of our own. From then on every body pulls every other
(user, 2026-11-18: real gravity, '_ephemeris').
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from datetime import datetime

import numpy

from ._atmosphere import TERRA_AIR
from ._conic import Conic, TAU
from ._ephemeris import Ephemeris
from ._heavenlybody import HeavenlyBody
from ._solarsystem import SolarSystem

AU = 1.495978707e11
DAY = 86400.0
J2000 = 2451545.0
CENTURY = 36525.0
#  General precession in longitude, deg a century: longitudes of the
#  date's equinox taken back to J2000's.
PRECESSION = 1.396971
#  G M, m³/s².
SOL_MU = 1.32712440018e20
TERRA_MU = 3.986004418e14
#  Sol: radius m, a sidereal turn h, tilt deg.
SOL = ('Sol', SOL_MU, 6.957e8, 609.12, 7.25, 'sol')
#  Each planet: name, G M (m³/s²), radius (m), a sidereal turn (h), tilt
#  to its path (deg, past 90: turning backward), look; then JPL's
#  elements at J2000 and their rates a century: a (au), e, I, L, the
#  periapsis' longitude, the node's longitude (deg).
PLANETS = (
  ('Mercury', 2.2031868551e13, 2.4397e6, 1407.6, 0.034, 'mercury',
   (0.38709927, 0.20563593, 7.00497902, 252.25032350, 77.45779628,
    48.33076593),
   (0.00000037, 0.00001906, -0.00594749, 149472.67411175, 0.16047689,
    -0.12534081)),
  ('Venus', 3.24858592e14, 6.0518e6, 5832.6, 177.36, 'venus',
   (0.72333566, 0.00677672, 3.39467605, 181.97909950, 131.60246718,
    76.67984255),
   (0.00000390, -0.00004107, -0.00078890, 58517.81538729, 0.00268329,
    -0.27769418)),
  ('Terra', TERRA_MU, 6.371e6, 23.9344696, 23.4392911, 'terra',
   (1.00000261, 0.01671123, -0.00001531, 100.46457166, 102.93768193,
    0.0),
   (0.00000562, -0.00004392, -0.01294668, 35999.37244981, 0.32327364,
    0.0)),
  ('Mars', 4.282837362e13, 3.3895e6, 24.6229, 25.19, 'mars',
   (1.52371034, 0.09339410, 1.84969142, -4.55343205, -23.94362959,
    49.55953891),
   (0.00001847, 0.00007882, -0.00813131, 19140.30268499, 0.44441088,
    -0.29257343)),
  ('Jupiter', 1.26686534e17, 6.9911e7, 9.925, 3.13, 'jupiter',
   (5.20288700, 0.04838624, 1.30439695, 34.39644051, 14.72847983,
    100.47390909),
   (-0.00011607, -0.00013253, -0.00183714, 3034.74612775, 0.21252668,
    0.20469106)),
  ('Saturn', 3.7931187e16, 5.8232e7, 10.656, 26.73, 'saturn',
   (9.53667594, 0.05386179, 2.48599187, 49.95424423, 92.59887831,
    113.66242448),
   (-0.00125060, -0.00050991, 0.00193609, 1222.49362201, -0.41897216,
    -0.28867794)),
  ('Uranus', 5.793939e15, 2.5362e7, 17.24, 97.77, 'uranus',
   (19.18916464, 0.04725744, 0.77263783, 313.23810451, 170.95427630,
    74.01692503),
   (-0.00196176, -0.00004397, -0.00242939, 428.48202785, 0.40805281,
    0.04240589)),
  ('Neptune', 6.836529e15, 2.4622e7, 16.11, 28.32, 'neptune',
   (30.06992276, 0.00859048, 1.77004347, -55.12002969, 44.96476227,
    131.78422574),
   (0.00026291, 0.00005105, 0.00035372, 218.45945325, -0.32241464,
    -0.00508664)),
  ('Pluto', 8.696e11, 1.1883e6, 153.2928, 119.6, 'pluto',
   (39.48211675, 0.24882730, 17.14001206, 238.92903833, 224.06891629,
    110.30393684),
   (-0.00031596, 0.00005170, 0.00004818, 145.20780515, -0.04062942,
    -0.01183482)),
)
#  Luna: G M, radius, its equator's tilt to the ecliptic (deg); its mean
#  longitude and node at J2000 and their rates a century (deg, the
#  date's equinox: Meeus).
LUNA = ('Luna', 4.9048695e12, 1.7374e6, 1.5424)
LUNA_LONGITUDE = (218.3164477, 481267.88123421)
LUNA_NODE = (125.0445479, -1934.1362891)
#  Where the Moon is on a day (Meeus, 'Astronomical Algorithms', ch.
#  47; user, 2026-11-18, real gravity: started on its mean path it went
#  round in 26.5 to 27.3 days by the day it started, the path of the
#  moment not being the mean one): its mean longitude, mean elongation,
#  the Sun's mean anomaly, its own, its argument of latitude (deg at
#  J2000, deg a century); its greatest periodic terms in longitude
#  (1e-6 deg) and distance (1e-3 km), each its multiples of those four
#  last, and in latitude (1e-6 deg); its mean distance, km. Meeus'
#  worked example (1992 April 12) within 0.004 deg and 29 km; the total
#  eclipse of 2024 April 8 by the Sun, 359 812 km off.
MOON_ARGUMENTS = ((218.3164477, 481267.88123421),
                  (297.8501921, 445267.1114034),
                  (357.5291092, 35999.0502909),
                  (134.9633964, 477198.8675055),
                  (93.2720950, 483202.0175233))
MOON_LONGITUDE = (
  (0, 0, 1, 0, 6288774, -20905355), (2, 0, -1, 0, 1274027, -3699111),
  (2, 0, 0, 0, 658314, -2955968), (0, 0, 2, 0, 213618, -569925),
  (0, 1, 0, 0, -185116, 48888), (0, 0, 0, 2, -114332, -3149),
  (2, 0, -2, 0, 58793, 246158), (2, -1, -1, 0, 57066, -152138),
  (2, 0, 1, 0, 53322, -170733), (2, -1, 0, 0, 45758, -204586),
  (0, 1, -1, 0, -40923, -129620), (1, 0, 0, 0, -34720, 108743),
  (0, 1, 1, 0, -30383, 104755), (2, 0, 0, -2, 15327, 10321),
  (0, 0, 1, 2, -12528, 0), (0, 0, 1, -2, 10980, 79661),
  (4, 0, -1, 0, 10675, -34782), (0, 0, 3, 0, 10034, -23210),
  (4, 0, -2, 0, 8548, -21636))
MOON_LATITUDE = (
  (0, 0, 0, 1, 5128122), (0, 0, 1, 1, 280602), (0, 0, 1, -1, 277693),
  (2, 0, 0, -1, 173237), (2, 0, -1, 1, 55413), (2, 0, -1, -1, 46271),
  (2, 0, 0, 1, 32573), (0, 0, 2, 1, 17198), (2, 0, 1, -1, 9266),
  (0, 0, 2, -1, 8822))
MOON_DISTANCE = 385000.56
#  Its velocity is had from its places this far either side, s.
MOON_STEP = 300.0
#  Mani, our small moon (the spec: "400 km across and about 650,000 km
#  out, giving roughly a two-month orbit"): radius (m), its rock's
#  density (kg/m³), a (m), e, i, node, periapsis and mean anomaly at
#  J2000 (deg). It goes round backward (i past 90 deg): with every body
#  pulling every other (2026-11-18), going round the way Luna does it
#  was thrown out of Terra's reach within a year (Sol's pull, and
#  Luna's every second turn of hers); backward it stays, 20 years flown
#  within 676 000 km, never nearer Luna than 222 000 km.
MANI = ('Mani', 2.0e5, 3000.0, 6.5e8, 0.03, 172.5, 40.0, 110.0, 200.0)
GRAVITATIONAL = 6.6743e-11
#  Where the pad is on Terra: on the equator, its prime meridian
#  (latitude, longitude, deg).
PAD = (0.0, 0.0)


def julianOf(when: datetime) -> float:
  """Returns the Julian date of 'when' (a datetime with its time zone),
  days."""
  return 2440587.5 + when.timestamp() / DAY


def solarSystemOn(julian: float, device: str) -> SolarSystem:
  """Returns the solar system as it stands on Julian date 'julian' (its
  time nought then): Sol, the nine planets, Terra's two moons, their
  paths flown on 'device' (Warp's: the GPU in the game, the CPU in the
  tests)."""
  centuries = (julian - J2000) / CENTURY
  sol = HeavenlyBody(SOL[0], None, SOL[1], SOL[2], _spinOf(SOL[3]),
                     _tilted((0.0, 0.0, 1.0), SOL[4], 0.0), 0.0, None,
                     SOL[5], None)
  bodies = [sol]
  terra = None
  for name, mu, radius, hours, tilt, look, base, rate in PLANETS:
    conic = _planetConic(base, rate, centuries)
    if name == 'Terra':
      pole = _tilted((0.0, 0.0, 1.0), -tilt, 0.0)
      body = HeavenlyBody(name, sol, mu, radius, _earthSpin(), pole,
                          _earthAngle(julian), conic, look, TERRA_AIR)
      terra = body
    else:
      normal = tuple(row[2] for row in conic.turn)
      pole = _tilted(normal, tilt, conic.node)
      body = HeavenlyBody(name, sol, mu, radius, _spinOf(hours), pole,
                          0.0, conic, look, None)
    bodies.append(body)
  bodies.append(_luna(terra, julian))
  bodies.append(_mani(terra, julian))
  bodies = tuple(bodies)
  parents = [-1] + [bodies.index(b.parent) for b in bodies[1:]]
  ephemeris = Ephemeris(device, parents, [b.depth for b in bodies],
                        [b.mu for b in bodies], statesOf(bodies), 0.0)
  return SolarSystem(bodies, ephemeris)


def statesOf(bodies: tuple) -> numpy.ndarray:
  """Returns each body's place and velocity from its parent at time
  nought (float64, shape (bodies, 2, 3); Sol's nought): where its day's
  path has it, moving as fast as the path says with its parent's G M
  and its own summed (they go round each other); a planet with moons
  off its path (the barycentre's, as JPL's table gives Terra's) by as
  much as they weigh."""
  out = numpy.zeros((len(bodies), 2, 3))
  for k, body in enumerate(bodies):
    if body.parent is None:
      continue
    conic = body.conic
    mu = body.parent.mu + body.mu
    together = Conic(mu, conic.a, conic.e, conic.i, conic.node, conic.peri,
                     conic.anomaly)
    out[k] = together.stateAt(0.0)
  for k, body in enumerate(bodies):
    moons = [j for j, b in enumerate(bodies) if b.parent is body]
    if not moons or body.parent is None:
      continue
    total = body.mu + sum(bodies[j].mu for j in moons)
    shift = sum(bodies[j].mu * out[j] for j in moons) / total
    out[k] -= shift
  return out


def _planetConic(base: tuple, rate: tuple, centuries: float) -> Conic:
  """Returns a planet's path from JPL's elements at J2000 ('base') and
  their rates a century ('rate'), 'centuries' on."""
  a, e, i, mean, perihelion, node = (x + r * centuries
                                     for x, r in zip(base, rate))
  return Conic(SOL_MU, a * AU, e, math.radians(i), math.radians(node),
               math.radians(perihelion - node),
               math.radians(mean - perihelion))


def _luna(terra: HeavenlyBody, julian: float) -> HeavenlyBody:
  """Returns Luna where the Moon is on Julian date 'julian' and moving
  as it is ('moonPlace': its path of the moment, Terra's G M and hers
  summed), turned as the Moon is: its face to Terra on the whole (its
  spin its mean longitude's), its pole tilted from the ecliptic's away
  from its path's (Cassini)."""
  name, mu, radius, tilt = LUNA
  centuries = (julian - J2000) / CENTURY
  back = PRECESSION * centuries
  longitude = LUNA_LONGITUDE[0] + LUNA_LONGITUDE[1] * centuries - back
  node = LUNA_NODE[0] + LUNA_NODE[1] * centuries - back
  place = moonPlace(julian)
  step = MOON_STEP / DAY
  ahead, behind = moonPlace(julian + step), moonPlace(julian - step)
  velocity = tuple((a - b) / (2.0 * MOON_STEP) for a, b in zip(ahead,
                                                                behind))
  conic = Conic.fromState(TERRA_MU + mu, place, velocity)
  side = math.radians(node + 90.0)
  lean = math.radians(tilt)
  pole = (math.sin(lean) * math.cos(side), math.sin(lean) * math.sin(side),
          math.cos(lean))
  spin = math.radians(LUNA_LONGITUDE[1]) / (CENTURY * DAY)
  return HeavenlyBody(name, terra, mu, radius, spin, pole,
                      _facing(pole, math.radians(longitude)), conic,
                      'luna', None)


def moonPlace(julian: float) -> tuple:
  """Returns where the Moon is from the Earth on Julian date 'julian',
  m, the ecliptic's axes (J2000's: its longitude of the date taken back
  by the precession): Meeus' greatest terms ('MOON_LONGITUDE',
  'MOON_LATITUDE', and his three additive ones)."""
  centuries = (julian - J2000) / CENTURY
  mean, elong, sun, own, latitude = (
    math.radians((a + b * centuries) % 360.0) for a, b in MOON_ARGUMENTS)
  eccentric = 1.0 - 0.002516 * centuries - 0.0000074 * centuries ** 2
  sl = sr = sb = 0.0
  for d, m, mp, f, along, out in MOON_LONGITUDE:
    angle = d * elong + m * sun + mp * own + f * latitude
    weight = eccentric ** abs(m)
    sl += weight * along * math.sin(angle)
    sr += weight * out * math.cos(angle)
  for d, m, mp, f, up in MOON_LATITUDE:
    sb += eccentric ** abs(m) * up * math.sin(
      d * elong + m * sun + mp * own + f * latitude)
  a1 = math.radians(119.75 + 131.849 * centuries)
  a2 = math.radians(53.09 + 479264.290 * centuries)
  a3 = math.radians(313.45 + 481266.484 * centuries)
  sl += (3958.0 * math.sin(a1) + 1962.0 * math.sin(mean - latitude)
         + 318.0 * math.sin(a2))
  sb += (-2235.0 * math.sin(mean) + 382.0 * math.sin(a3)
         + 175.0 * math.sin(a1 - latitude) + 175.0 * math.sin(a1 + latitude)
         + 127.0 * math.sin(mean - own) - 115.0 * math.sin(mean + own))
  along = math.radians(math.degrees(mean) + sl / 1e6
                       - PRECESSION * centuries)
  up = math.radians(sb / 1e6)
  far = 1e3 * (MOON_DISTANCE + sr / 1e3)
  return (far * math.cos(up) * math.cos(along),
          far * math.cos(up) * math.sin(along), far * math.sin(up))


def _mani(terra: HeavenlyBody, julian: float) -> HeavenlyBody:
  """Returns Mani on its path, carried on from J2000 to 'julian', its
  face to Terra, its pole its path's."""
  name, radius, density, a, e, i, node, peri, anomaly = MANI
  mu = GRAVITATIONAL * density * 4.0 / 3.0 * math.pi * radius ** 3
  conic = Conic(TERRA_MU, a, e, math.radians(i), math.radians(node),
                math.radians(peri), math.radians(anomaly))
  conic = conic.after((julian - J2000) * DAY)
  pole = tuple(row[2] for row in conic.turn)
  there = conic.stateAt(0.0)[0]
  return HeavenlyBody(name, terra, mu, radius, conic.motion, pole,
                      _facing(pole, math.atan2(there[1], there[0])),
                      conic, 'mani', None)


def _facing(pole: tuple, longitude: float) -> float:
  """Returns the angle putting a moon's prime meridian toward its
  planet, the moon at ecliptic 'longitude' (rad) round it: the planet
  is half a turn on, from the node of the moon's equator."""
  node = math.atan2(-pole[0], pole[1])
  return (longitude + math.pi - node) % TAU


def _tilted(normal: tuple, tilt: float, node: float) -> tuple:
  """Returns 'normal' (a unit vector) leant 'tilt' deg about the line
  in the ecliptic at 'node' rad: a planet's pole off its path's
  normal."""
  axis = (math.cos(node), math.sin(node), 0.0)
  angle = math.radians(tilt)
  cos, sin = math.cos(angle), math.sin(angle)
  along = sum(a * b for a, b in zip(axis, normal))
  cross = (axis[1] * normal[2] - axis[2] * normal[1],
           axis[2] * normal[0] - axis[0] * normal[2],
           axis[0] * normal[1] - axis[1] * normal[0])
  return tuple(n * cos + c * sin + a * along * (1.0 - cos)
               for n, c, a in zip(normal, cross, axis))


def _spinOf(hours: float) -> float:
  """Returns the spin of a body turning once in 'hours' h, rad/s."""
  return TAU / (3600.0 * hours)


def _earthSpin() -> float:
  """Returns Terra's spin, the Earth's rotation angle's rate, rad/s."""
  return TAU * 1.00273781191135448 / DAY


def _earthAngle(julian: float) -> float:
  """Returns Terra's turn on Julian date 'julian': the Earth's rotation
  angle (its prime meridian from the equinox), rad."""
  return TAU * (0.7790572732640 + 1.00273781191135448
                * (julian - J2000)) % TAU
