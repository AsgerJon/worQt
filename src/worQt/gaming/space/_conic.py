"""
Conic is the path one body takes round another pulling it alone: an
ellipse, or a hyperbola once it is fast enough to leave (user,
2026-11-16: the "skrå kast" "turns into something far more beautiful:
an elliptic orbital path"), the puller in its focus.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

TAU = 2.0 * math.pi
#  Below these an orbit is taken as round, or as lying in the ecliptic:
#  its periapsis, or its node, is then measured from the x axis.
ROUND = 1e-11
FLAT = 1e-11


class Conic:
  """
  Conic is a body's path round its puller ('mu', its G M, m³/s², in the
  focus): how big ('a', m: half the long axis, below nought for a
  hyperbola), how stretched ('e'), its tilt to the ecliptic ('i', rad),
  where it crosses it going north ('node', rad from the x axis), where
  its periapsis lies in it ('peri', rad from the node) and where along it
  the body is at time nought ('anomaly', its mean anomaly, rad; on an
  ellipse within one turn). Times are s from nought; places and
  velocities in the ecliptic's axes (x the equinox, z its north), m and
  m/s from the puller. Python's floats: the reference the flight's
  kernel holds to, and what the sky and the map are worked out with.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  mu: float
  a: float
  e: float
  i: float
  node: float
  peri: float
  anomaly: float
  turn: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, mu: float, a: float, e: float, i: float, node: float,
               peri: float, anomaly: float) -> None:
    if mu <= 0.0 or e < 0.0:
      raise ValueError('no conic has mu %r and e %r' % (mu, e))
    if (e < 1.0) != (a > 0.0):
      raise ValueError('an ellipse has a > 0, a hyperbola a < 0: a %r, '
                       'e %r' % (a, e))
    self.mu, self.a, self.e = float(mu), float(a), float(e)
    self.i, self.node, self.peri = float(i), float(node), float(peri)
    self.anomaly = float(anomaly) % TAU if e < 1.0 else float(anomaly)
    self.turn = _turnOf(self.node, self.i, self.peri)

  @classmethod
  def fromState(cls, mu: float, place: tuple, velocity: tuple) -> Conic:
    """The 'fromState' method returns the conic a body at 'place' moving
    at 'velocity' (m, m/s from the puller, whose G M is 'mu') follows,
    its time nought now."""
    r, v = tuple(place), tuple(velocity)
    distance = math.sqrt(_dot(r, r))
    h = _cross(r, v)
    size = math.sqrt(_dot(h, h))
    if distance == 0.0 or size == 0.0:
      raise ValueError('a body falling straight in has no conic')
    speed2 = _dot(v, v)
    lean = (speed2 - mu / distance) / mu, _dot(r, v) / mu
    eccentric = tuple(lean[0] * a - lean[1] * b for a, b in zip(r, v))
    e = math.sqrt(_dot(eccentric, eccentric))
    i = math.acos(max(-1.0, min(1.0, h[2] / size)))
    across = math.hypot(h[0], h[1]) / size
    node = math.atan2(h[0], -h[1]) if across > FLAT else 0.0
    flat = _unturned(node, i, eccentric)
    peri = math.atan2(flat[1], flat[0]) if e > ROUND else 0.0
    at = _unturned(node, i, r)
    true = math.atan2(at[1], at[0]) - peri
    energy = 0.5 * speed2 - mu / distance
    if energy < 0.0:
      e = min(e, 1.0 - 1e-12)
    else:
      e = max(e, 1.0 + 1e-12)
      energy = max(energy, 1e-12 * mu / distance)
    if e < 1.0:
      a = -0.5 * mu / energy
      E = 2.0 * math.atan2(math.sqrt(1.0 - e) * math.sin(0.5 * true),
                           math.sqrt(1.0 + e) * math.cos(0.5 * true))
      anomaly = E - e * math.sin(E)
    else:
      a = -0.5 * mu / energy
      H = 2.0 * math.atanh(math.sqrt((e - 1.0) / (e + 1.0))
                           * math.tan(0.5 * true))
      anomaly = e * math.sinh(H) - H
    return cls(mu, a, e, i, node, peri, anomaly)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def closed(self, ) -> bool:
    """The 'closed' property says whether the conic is an ellipse."""
    return self.e < 1.0

  @property
  def motion(self, ) -> float:
    """The 'motion' property is the mean motion, rad/s."""
    return math.sqrt(self.mu / abs(self.a) ** 3)

  @property
  def period(self, ) -> float:
    """The 'period' property is the time once round, s (a hyperbola's:
    'math.inf')."""
    return TAU / self.motion if self.closed else math.inf

  @property
  def periapsis(self, ) -> float:
    """The 'periapsis' property is the nearest the path comes to the
    puller's middle, m."""
    return abs(self.a) * abs(1.0 - self.e)

  @property
  def apoapsis(self, ) -> float:
    """The 'apoapsis' property is the furthest the path goes from the
    puller's middle, m ('math.inf' on a hyperbola)."""
    return self.a * (1.0 + self.e) if self.closed else math.inf

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def anomalyAt(self, t: float) -> float:
    """The 'anomalyAt' method returns the mean anomaly at time 't', s
    (on an ellipse within one turn)."""
    anomaly = self.anomaly + self.motion * t
    return anomaly % TAU if self.closed else anomaly

  def stateAt(self, t: float) -> tuple:
    """The 'stateAt' method returns where the body is and how fast it
    moves at time 't', s: two triples, m and m/s from the puller."""
    flat, flatSpeed = self.flatAt(self.anomalyAt(t))
    return _turned(self.turn, flat), _turned(self.turn, flatSpeed)

  def flatAt(self, anomaly: float) -> tuple:
    """The 'flatAt' method returns the place and velocity at the mean
    'anomaly' in the orbit's own plane (x toward the periapsis, z along
    its pull's turning)."""
    a, e, mu = abs(self.a), self.e, self.mu
    if self.closed:
      E = eccentricOf(anomaly, e)
      cos, sin = math.cos(E), math.sin(E)
      root = math.sqrt(1.0 - e * e)
      r = a * (1.0 - e * cos)
      speed = math.sqrt(mu * a) / r
      return ((a * (cos - e), a * root * sin, 0.0),
              (-speed * sin, speed * root * cos, 0.0))
    H = hyperbolicOf(anomaly, e)
    cosh, sinh = math.cosh(H), math.sinh(H)
    root = math.sqrt(e * e - 1.0)
    r = a * (e * cosh - 1.0)
    speed = math.sqrt(mu * a) / r
    return ((a * (e - cosh), a * root * sinh, 0.0),
            (-speed * sinh, speed * root * cosh, 0.0))

  def after(self, seconds: float) -> Conic:
    """The 'after' method returns the same path, its time nought
    'seconds' s later (the leap's fold: the anomaly carried on)."""
    return Conic(self.mu, self.a, self.e, self.i, self.node, self.peri,
                 self.anomalyAt(seconds))

  def timeTo(self, anomaly: float, t: float) -> float | None:
    """The 'timeTo' method returns how long from time 't' till the body
    is next at mean 'anomaly', s; None if it never is (a hyperbola past
    it)."""
    now = self.anomalyAt(t)
    if self.closed:
      return ((anomaly - now) % TAU) / self.motion
    if anomaly < now:
      return None
    return (anomaly - now) / self.motion

  def timeToApoapsis(self, t: float) -> float | None:
    """The 'timeToApoapsis' method returns how long from time 't' till
    the body is at its apoapsis, s; None on a hyperbola."""
    return self.timeTo(math.pi, t) if self.closed else None

  def timeToPeriapsis(self, t: float) -> float | None:
    """The 'timeToPeriapsis' method returns how long from time 't' till
    the body is at its periapsis, s; None once past it on a
    hyperbola."""
    return self.timeTo(0.0, t)

  def pathPoints(self, count: int, reach: float) -> list:
    """The 'pathPoints' method returns 'count' points along the path
    (m, from the puller): once round an ellipse from the periapsis, a
    hyperbola out to 'reach' m from the puller either way."""
    a, e = abs(self.a), self.e
    out = []
    if self.closed:
      root = math.sqrt(1.0 - e * e)
      for k in range(count):
        E = TAU * k / count
        out.append(_turned(self.turn, (a * (math.cos(E) - e),
                                       a * root * math.sin(E), 0.0)))
      return out
    root = math.sqrt(e * e - 1.0)
    most = math.acosh(max(1.0, (reach / a + 1.0) / e))
    for k in range(count):
      H = -most + 2.0 * most * k / max(1, count - 1)
      out.append(_turned(self.turn, (a * (e - math.cosh(H)),
                                     a * root * math.sinh(H), 0.0)))
    return out


def eccentricOf(anomaly: float, e: float) -> float:
  """Returns the eccentric anomaly of an ellipse's mean 'anomaly' (rad),
  by Newton (Kepler's equation)."""
  E = anomaly if e < 0.8 else math.pi
  for _ in range(60):
    step = (E - e * math.sin(E) - anomaly) / (1.0 - e * math.cos(E))
    E -= step
    if abs(step) < 1e-15:
      break
  return E


def hyperbolicOf(anomaly: float, e: float) -> float:
  """Returns the hyperbolic anomaly of a hyperbola's mean 'anomaly', by
  Newton."""
  H = math.asinh(anomaly / e)
  for _ in range(80):
    step = (e * math.sinh(H) - H - anomaly) / (e * math.cosh(H) - 1.0)
    H -= step
    if abs(step) < 1e-15 * max(1.0, abs(H)):
      break
  return H


def _turnOf(node: float, i: float, peri: float) -> tuple:
  """Returns the turn from an orbit's own plane to the ecliptic's axes,
  Rz(node) Rx(i) Rz(peri), three rows."""
  cn, sn = math.cos(node), math.sin(node)
  ci, si = math.cos(i), math.sin(i)
  cp, sp = math.cos(peri), math.sin(peri)
  return ((cn * cp - sn * ci * sp, -cn * sp - sn * ci * cp, sn * si),
          (sn * cp + cn * ci * sp, -sn * sp + cn * ci * cp, -cn * si),
          (si * sp, si * cp, ci))


def _turned(turn: tuple, x: tuple) -> tuple:
  """Returns 'x' turned by 'turn' (three rows)."""
  return tuple(row[0] * x[0] + row[1] * x[1] + row[2] * x[2]
               for row in turn)


def _unturned(node: float, i: float, x: tuple) -> tuple:
  """Returns the ecliptic's 'x' in a plane through 'node' tilted 'i'
  (x toward the node): Rx(-i) Rz(-node) x."""
  cn, sn = math.cos(node), math.sin(node)
  ci, si = math.cos(i), math.sin(i)
  u = cn * x[0] + sn * x[1]
  w = -sn * x[0] + cn * x[1]
  return u, ci * w + si * x[2], -si * w + ci * x[2]


def _dot(a: tuple, b: tuple) -> float:
  """Returns the dot product of 'a' and 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: tuple, b: tuple) -> tuple:
  """Returns the cross product of 'a' and 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])
