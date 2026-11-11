"""
System is a system of masses joined by springs, dampers and components,
in space, under gravity.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .._doubles import doubles
from ._parts import Damper, Point, Spring, SpringMassDamper

_SHORTEST = 1e-9  # m: a spring shorter than this has no direction
_TURNINGS = ('fixed', 'hinge', 'free')


def _indices(pairs: list, at: int) -> torch.Tensor:
  """The indices at place 'at' of 'pairs', as a tensor."""
  return torch.tensor([pair[at] for pair in pairs]).long()


def _unit(vector: tuple) -> tuple[float, float, float]:
  """'vector' a unit long."""
  size = math.sqrt(sum(value * value for value in vector))
  return (*[value / size for value in vector],)


def _across(direction: tuple) -> list[tuple[float, float, float]]:
  """Two unit vectors square to 'direction' and to each other."""
  x, y, z = _unit(direction)
  other = (0.0, 0.0, 1.0) if abs(z) < 0.9 else (1.0, 0.0, 0.0)
  first = _unit((y * other[2] - z * other[1], z * other[0] - x * other[2],
                 x * other[1] - y * other[0]))
  a, b, c = first
  return [first, (y * c - z * b, z * a - x * c, x * b - y * a)]


class System(BaseObject):
  """
  System is a system of masses joined by springs, dampers and
  components, in m, kg, N and s, z up: its 'points', each a mass moving
  along the axes it may, an anchor along none; its 'springs' and its
  'dampers', each between two points; its 'components', so far
  'SpringMassDamper's, each a rod from one point to another, rigid but
  for its length, turning about its base as it may; and its 'gravity',
  in m/s², pulling every point down. A spring pulls along the line
  between its points as that line turns, so the system may swing as far
  as it likes.

  What a point may do is a guide on it: along its axes, and for the tip
  of a component, along the rod, fixed, or in its plane, hinged. The
  guides are linear, so the points move together in a space of their
  own, 'basis', its columns how they may move; 'accelerations' turns
  forces into the accelerations the guides let them have. 'forces' are
  the forces on the points, of their places and speeds;
  'elasticEnergy', 'gravityEnergy' and 'kineticEnergy' the energies;
  'tangent' the stiffness of the points' moving a little, 'rest' where
  they come to rest, if they do, and 'modes' how they swing about it, a
  little: each mode's frequency and shape. 'quickest' bounds how fast
  anything can change, for a step of time to be small enough.

  A system is made only whole: each point of a mass, each spring,
  damper and component between two points there are, stiff or damping.
  'withPoints', 'withSprings', 'withDampers', 'withComponents',
  'withGravity', 'withPoint' and 'withComponent' return it with those
  changed; 'withoutPoint' without a point and what is on it, the
  indices after it moved down; 'withoutSpring', 'withoutDamper' and
  'withoutComponent' without one. Made of nothing, it is the standard
  system: an anchor and two masses hanging from it, one off to the
  side, so it swings in three dimensions.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_gravity__ = 9.81  # m/s²
  __fallback_points__ = (
    Point((0.0, 0.0, 2.0), 1.0, ''),
    Point((0.0, 0.0, 1.3), 1.0, 'xyz'),
    Point((0.25, 0.1, 0.7), 0.5, 'xyz'),
  )
  __fallback_springs__ = (
    Spring(0, 1, 80.0, 0.6),
    Spring(1, 2, 40.0, 0.5),
  )
  __fallback_most_tries__ = 400  # steps 'rest' takes at most

  #  Private Variables
  __system_parts__: tuple | None = None
  __system_gravity__: float | None = None
  __system_tensors__: dict | None = None

  #  Virtual Variables
  points: Field[tuple[Point, ...]] = Field()
  springs: Field[tuple[Spring, ...]] = Field()
  dampers: Field[tuple[Damper, ...]] = Field()
  components: Field[tuple[SpringMassDamper, ...]] = Field()
  gravity: Field[float] = Field()
  masses: Field[torch.Tensor] = Field()
  free: Field[torch.Tensor] = Field()
  basis: Field[torch.Tensor] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple:
    if self.__system_parts__ is None:
      raise MissingVariable(self, '__system_parts__', tuple)
    return self.__system_parts__

  def _tensor(self, name: str) -> torch.Tensor:
    """The tensor 'name', made once."""
    if self.__system_tensors__ is None:
      raise MissingVariable(self, '__system_tensors__', dict)
    return self.__system_tensors__[name]

  @points.GET
  def _getPoints(self, ) -> tuple[Point, ...]:
    """The 'points' getter returns the points, in the order added."""
    return self._getParts()[0]

  @springs.GET
  def _getSprings(self, ) -> tuple[Spring, ...]:
    """The 'springs' getter returns the springs, in the order added."""
    return self._getParts()[1]

  @dampers.GET
  def _getDampers(self, ) -> tuple[Damper, ...]:
    """The 'dampers' getter returns the dampers, in the order added."""
    return self._getParts()[2]

  @components.GET
  def _getComponents(self, ) -> tuple[SpringMassDamper, ...]:
    """The 'components' getter returns the components, in the order
    added."""
    return self._getParts()[3]

  @gravity.GET
  def _getGravity(self, ) -> float:
    """The 'gravity' getter returns how hard gravity pulls, in m/s²."""
    if self.__system_gravity__ is None:
      raise MissingVariable(self, '__system_gravity__', float)
    return self.__system_gravity__

  @masses.GET
  def _getMasses(self, ) -> torch.Tensor:
    """The 'masses' getter returns the points' masses, in kg."""
    return self._tensor('masses')

  @free.GET
  def _getFree(self, ) -> torch.Tensor:
    """The 'free' getter returns which points may move at all, the rest
    pinned."""
    return self._tensor('free')

  @basis.GET
  def _getBasis(self, ) -> torch.Tensor:
    """The 'basis' getter returns how the points may move together, the
    guides kept: a column for each way, a row for each point's x, y and
    z in turn."""
    return self._tensor('basis')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d points, %d springs, %d dampers, %d components,
    g %g)"""
    return ' '.join(infoSpec.split()) % (
      type(self).__name__, len(self.points), len(self.springs),
      len(self.dampers), len(self.components), self.gravity)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple, tuple, tuple, float)
  def __init__(self, points: tuple, springs: tuple, dampers: tuple,
               components: tuple, gravity: float) -> None:
    points = (*[Point((*map(float, p.at),), float(p.mass), str(p.moves))
                for p in points],)
    springs = (*[Spring(int(s.first), int(s.second), float(s.stiffness),
                        float(s.rest)) for s in springs],)
    dampers = (*[Damper(int(d.first), int(d.second), float(d.damping))
                 for d in dampers],)
    components = (*[SpringMassDamper(
      int(c.base), int(c.tip), float(c.stiffness), float(c.damping),
      float(c.rest), str(c.turning), (*map(float, c.axis),))
      for c in components],)
    self._check(points, springs, dampers, float(gravity))
    self._checkComponents(points, components)
    self.__system_parts__ = (points, springs, dampers, components)
    self.__system_gravity__ = float(gravity)
    self.__system_tensors__ = self._tensors()

  @overload(tuple, tuple, tuple, tuple)
  def __init__(self, points: tuple, springs: tuple, dampers: tuple,
               components: tuple) -> None:
    self.__init__(points, springs, dampers, components,
                  self.__fallback_gravity__)

  @overload(tuple, tuple, tuple, float)
  def __init__(self, points: tuple, springs: tuple, dampers: tuple,
               gravity: float) -> None:
    self.__init__(points, springs, dampers, (), gravity)

  @overload(tuple, tuple, tuple)
  def __init__(self, points: tuple, springs: tuple,
               dampers: tuple) -> None:
    self.__init__(points, springs, dampers, (), self.__fallback_gravity__)

  @overload()
  def __init__(self, ) -> None:
    self.__init__(self.__fallback_points__, self.__fallback_springs__, (),
                  (), self.__fallback_gravity__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def positions(self, ) -> torch.Tensor:
    """The 'positions' method returns where the points are, a row each,
    in m."""
    return self._tensor('positions').clone()

  def accelerations(self, forces: torch.Tensor) -> torch.Tensor:
    """The 'accelerations' method returns the accelerations the guides
    let the points have, pushed by 'forces', a row each."""
    flat = self._tensor('projector') @ forces.reshape(-1)
    return flat.reshape(-1, 3)

  def forces(self, x: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """The 'forces' method returns the force on each point, in N, the
    points at 'x' moving at 'v': gravity, the springs' pulls and the
    dampers' resistance, the components' among them."""
    forces = torch.zeros_like(x)
    forces[:, 2] -= self.masses * self.gravity
    if len(self._tensor('stiffness')):
      first, second, n, length = self._lines('spring', x)
      stretch = length - self._tensor('rest')
      pull = (self._tensor('stiffness') * stretch)[:, None] * n
      forces.index_add_(0, first, pull)
      forces.index_add_(0, second, -pull)
    if len(self._tensor('damping')):
      first, second, n, _ = self._lines('damper', x)
      apart = ((v[second] - v[first]) * n).sum(-1)
      pull = (self._tensor('damping') * apart)[:, None] * n
      forces.index_add_(0, first, pull)
      forces.index_add_(0, second, -pull)
    return forces

  def dissipation(self, x: torch.Tensor, v: torch.Tensor) -> float:
    """The 'dissipation' method returns how fast the dampers turn the
    motion into heat, in W, the points at 'x' moving at 'v'."""
    if not len(self._tensor('damping')):
      return 0.0
    first, second, n, _ = self._lines('damper', x)
    apart = ((v[second] - v[first]) * n).sum(-1)
    return float((self._tensor('damping') * apart * apart).sum())

  def elasticEnergy(self, x: torch.Tensor) -> float:
    """The 'elasticEnergy' method returns the energy in the springs, in
    J, the points at 'x'."""
    if not len(self._tensor('stiffness')):
      return 0.0
    _, _, _, length = self._lines('spring', x)
    stretch = length - self._tensor('rest')
    return float((0.5 * self._tensor('stiffness') * stretch ** 2).sum())

  def gravityEnergy(self, x: torch.Tensor) -> float:
    """The 'gravityEnergy' method returns the free points' energy of
    height, in J, at 'x', from z nought."""
    free = self.free
    return float((self.masses[free] * self.gravity * x[free, 2]).sum())

  def kineticEnergy(self, v: torch.Tensor) -> float:
    """The 'kineticEnergy' method returns the free points' energy of
    motion, in J, moving at 'v'."""
    free = self.free
    return float((0.5 * self.masses[free] * (v[free] ** 2).sum(-1)).sum())

  def tangent(self, x: torch.Tensor) -> torch.Tensor:
    """The 'tangent' method returns the stiffness of the points' moving a
    little from 'x', a 3 x 3 block for each two points, in N/m: each
    spring stiff along its line, and across it as taut as it is over
    how long."""
    count = len(self.points)
    stiffness = torch.zeros(3 * count, 3 * count).double()
    k = self._tensor('stiffness')
    if not len(k):
      return stiffness
    first, second, n, length = self._lines('spring', x)
    taut = k * (length - self._tensor('rest')) / length
    eye = torch.eye(3).double()
    for s in range(len(k)):
      along = n[s][:, None] * n[s][None, :]
      block = k[s] * along + taut[s] * (eye - along)
      i, j = 3 * int(first[s]), 3 * int(second[s])
      stiffness[i:i + 3, i:i + 3] += block
      stiffness[j:j + 3, j:j + 3] += block
      stiffness[i:i + 3, j:j + 3] -= block
      stiffness[j:j + 3, i:i + 3] -= block
    return stiffness

  def quickest(self, x: torch.Tensor) -> float:
    """The 'quickest' method returns a bound on how fast anything in the
    system can change, at 'x', in 1/s: the quickest a point can swing
    on its springs, or settle on its dampers; guides only slow them."""
    count = len(self.points)
    rate = torch.zeros(count).double()
    k = self._tensor('stiffness')
    if len(k):
      first, second, n, length = self._lines('spring', x)
      taut = k * (length - self._tensor('rest')).abs() / length
      most = 2 * torch.maximum(k, taut)
      rate.index_add_(0, first, most)
      rate.index_add_(0, second, most)
    settle = torch.zeros(count).double()
    c = self._tensor('damping')
    if len(c):
      first, second = self._tensor('damper')
      settle.index_add_(0, first, 2 * c)
      settle.index_add_(0, second, 2 * c)
    free = self.free
    if not bool(free.any()):
      return 0.0
    swing = (rate / self.masses)[free].max().sqrt()
    return max(float(swing), float((settle / self.masses)[free].max()))

  def rest(self, ) -> torch.Tensor | None:
    """The 'rest' method returns where the points come to rest, the
    least energy near where they are, the guides kept, or 'None' if they
    never do: a point falling or a chain sliding away for ever."""
    x = self.positions()
    basis = self.basis
    scale = 1.0 + float(self.masses.sum()) * self.gravity
    scale += float((self._tensor('stiffness')
                    * self._tensor('rest').clamp_min(1.0)).sum())
    shift = 0.0
    energy = self._potential(x)
    for _ in range(self.__fallback_most_tries__):
      push = basis.T @ self.forces(x, torch.zeros_like(x)).reshape(-1)
      if not len(push) or float(push.abs().max()) <= 1e-10 * scale:
        return x
      x, energy, shift = self._tryStep(x, energy, push, shift, scale)
      if x is None or float(x.abs().max()) > 1e6:
        return None
    return None

  def modes(self, ) -> tuple[tuple[float, ...], torch.Tensor] | None:
    """The 'modes' method returns how the system swings a little about
    its rest, as its guides let it: the frequency of each mode, in Hz,
    the slowest first, and its shape, a row of how far each point moves,
    the most one moving a metre; or 'None' if it has no rest. A mode of
    nought swings nowhere: the points drift."""
    x = self.rest()
    if x is None:
      return None
    basis = self.basis
    count = basis.shape[1]
    if not count:
      return (), torch.zeros(0, len(self.points), 3).double()
    stiffness = basis.T @ self.tangent(x) @ basis
    lower = torch.linalg.cholesky(self._tensor('reduced'))
    undo = torch.linalg.inv(lower)
    scaled = undo @ stiffness @ undo.T
    values, vectors = torch.linalg.eigh(0.5 * (scaled + scaled.T))
    frequencies = [math.sqrt(max(float(value), 0.0)) / (2 * math.pi)
                   for value in values]
    shapes = (basis @ undo.T @ vectors).T.reshape(count, -1, 3)
    most = (shapes ** 2).sum(-1).sqrt().max(-1)[0].clamp_min(1e-300)
    return (*frequencies,), shapes / most[:, None, None]

  def withPoints(self, *points: Point) -> System:
    """The 'withPoints' method returns the system of 'points'."""
    return self._made(points, self.springs, self.dampers,
                      self.components, self.gravity)

  def withSprings(self, *springs: Spring) -> System:
    """The 'withSprings' method returns the system with 'springs'."""
    return self._made(self.points, springs, self.dampers,
                      self.components, self.gravity)

  def withDampers(self, *dampers: Damper) -> System:
    """The 'withDampers' method returns the system with 'dampers'."""
    return self._made(self.points, self.springs, dampers,
                      self.components, self.gravity)

  def withComponents(self, *components: SpringMassDamper) -> System:
    """The 'withComponents' method returns the system with
    'components'."""
    return self._made(self.points, self.springs, self.dampers,
                      components, self.gravity)

  def withGravity(self, gravity: float) -> System:
    """The 'withGravity' method returns the system under 'gravity'."""
    return self._made(self.points, self.springs, self.dampers,
                      self.components, gravity)

  def withPoint(self, index: int, point: Point) -> System:
    """The 'withPoint' method returns the system with the point of
    'index' replaced by 'point'."""
    points = [*self.points]
    points[index] = point
    return self.withPoints(*points)

  def withComponent(self, index: int,
                    component: SpringMassDamper) -> System:
    """The 'withComponent' method returns the system with the component
    of 'index' replaced by 'component'."""
    components = [*self.components]
    components[index] = component
    return self.withComponents(*components)

  def withoutPoint(self, index: int) -> System:
    """The 'withoutPoint' method returns the system without the point of
    'index', and without the springs, dampers and components on it."""
    points = [p for i, p in enumerate(self.points) if i != index]

    def moved(part: tuple) -> tuple | None:
      if index in part[:2]:
        return None
      ends = [end - (1 if end > index else 0) for end in part[:2]]
      return type(part)(*ends, *part[2:])

    springs = [s for s in map(moved, self.springs) if s is not None]
    dampers = [d for d in map(moved, self.dampers) if d is not None]
    components = [c for c in map(moved, self.components) if c is not None]
    return self._made(points, springs, dampers, components, self.gravity)

  def withoutSpring(self, index: int) -> System:
    """The 'withoutSpring' method returns the system without the spring
    of 'index'."""
    springs = [s for i, s in enumerate(self.springs) if i != index]
    return self.withSprings(*springs)

  def withoutDamper(self, index: int) -> System:
    """The 'withoutDamper' method returns the system without the damper
    of 'index'."""
    dampers = [d for i, d in enumerate(self.dampers) if i != index]
    return self.withDampers(*dampers)

  def withoutComponent(self, index: int) -> System:
    """The 'withoutComponent' method returns the system without the
    component of 'index'; its points stay."""
    components = [c for i, c in enumerate(self.components) if i != index]
    return self.withComponents(*components)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _made(self, points: tuple | list, springs: tuple | list,
            dampers: tuple | list, components: tuple | list,
            gravity: float) -> System:
    """A system of the parts given."""
    return System((*points,), (*springs,), (*dampers,), (*components,),
                  float(gravity))

  @staticmethod
  def _check(points: tuple, springs: tuple, dampers: tuple,
             gravity: float) -> None:
    """Raises unless the points, springs and dampers are whole."""
    for index, point in enumerate(points):
      if not all(map(math.isfinite, point.at)):
        raise ValueError('P%d is somewhere' % (index + 1))
      if not point.mass > 0:
        raise ValueError('P%d has a mass above nought' % (index + 1))
      moves = point.moves
      if any(axis not in 'xyz' or moves.count(axis) > 1 for axis in moves):
        infoSpec = """P%d moves along x, y or z, each once, not '%s'"""
        raise ValueError(infoSpec % (index + 1, moves))
    links = [('spring', s, s.stiffness) for s in springs]
    links += [('damper', d, d.damping) for d in dampers]
    for name, link, strength in links:
      System._checkEnds(name, link[:2], len(points))
      if not strength > 0:
        infoSpec = """a %s is %s, above nought, not %g"""
        word = 'stiff' if name == 'spring' else 'damping'
        raise ValueError(infoSpec % (name, word, strength))
    for spring in springs:
      if not spring.rest >= 0:
        raise ValueError("""a spring's rest length is nought or more""")
    if not gravity >= 0:
      raise ValueError('gravity pulls down, nought or more')

  @staticmethod
  def _checkEnds(name: str, ends: tuple, count: int) -> None:
    """Raises unless 'ends' are two points of 'count' there are."""
    for end in ends:
      if not 0 <= end < count:
        infoSpec = """a %s joins points there are, not P%d"""
        raise ValueError(infoSpec % (name, end + 1))
    if ends[0] == ends[1]:
      infoSpec = """a %s joins two points, not P%d to itself"""
      raise ValueError(infoSpec % (name, ends[0] + 1))

  @staticmethod
  def _checkComponents(points: tuple, components: tuple) -> None:
    """Raises unless each component stands between two points there
    are, as a rod with a direction, stiff, damping nought or more,
    turning as it can: a hinge's axis across the rod."""
    for component in components:
      System._checkEnds('component', component[:2], len(points))
      if not component.stiffness > 0:
        raise ValueError('a component is stiff, above nought')
      if not component.damping >= 0:
        raise ValueError("""a component's damping is nought or more""")
      if not component.rest >= 0:
        raise ValueError("""a component's rest length is nought or more""")
      if component.turning not in _TURNINGS:
        infoSpec = """a component turns fixed, hinged or free, not '%s'"""
        raise ValueError(infoSpec % component.turning)
      base = points[component.base].at
      tip = points[component.tip].at
      rod = (*[b - a for a, b in zip(base, tip)],)
      if math.sqrt(sum(v * v for v in rod)) < 1e-6:
        raise ValueError("""a component's tip is away from its base""")
      if component.turning != 'hinge':
        continue
      if math.sqrt(sum(v * v for v in component.axis)) < 1e-9:
        raise ValueError("""a hinge turns about an axis""")
      along = sum(a * b for a, b in zip(_unit(rod), _unit(component.axis)))
      if abs(along) > 0.99:
        raise ValueError('a hinge along the rod would turn nothing')

  def _tensors(self, ) -> dict:
    """The tensors the reckoning takes, made once: the springs and
    dampers with the components' among them, and the guides."""
    points, springs, dampers, components = self._getParts()
    stiff = [(s.first, s.second, s.stiffness, s.rest) for s in springs]
    stiff += [(c.base, c.tip, c.stiffness, c.rest) for c in components]
    damp = [(d.first, d.second, d.damping) for d in dampers]
    damp += [(c.base, c.tip, c.damping) for c in components
             if c.damping > 0]
    out = {
      'positions': doubles([[*p.at] for p in points]),
      'masses'   : doubles([p.mass for p in points]),
      'free'     : torch.tensor([not p.pinned for p in points]).bool(),
      'stiffness': doubles([s[2] for s in stiff]),
      'rest'     : doubles([s[3] for s in stiff]),
      'damping'  : doubles([d[2] for d in damp]),
      'spring'   : (_indices(stiff, 0), _indices(stiff, 1)),
      'damper'   : (_indices(damp, 0), _indices(damp, 1)),
    }
    if not points:
      out['positions'] = torch.zeros(0, 3).double()
    out.update(self._guides(out['masses']))
    return out

  def _guides(self, masses: torch.Tensor) -> dict:
    """The ways the points may move, kept by their guides, the mass of
    each way, and what turns forces into accelerations along them."""
    points, _, _, components = self._getParts()
    size = 3 * len(points)
    rows = []
    for index, point in enumerate(points):
      for axis, name in enumerate('xyz'):
        if name not in point.moves:
          row = torch.zeros(size).double()
          row[3 * index + axis] = 1.0
          rows.append(row)
    for component in components:
      base, tip = points[component.base].at, points[component.tip].at
      rod = (*[b - a for a, b in zip(base, tip)],)
      across = {'fixed': _across(rod), 'hinge': [_unit(component.axis)],
                'free' : []}[component.turning]
      for vector in across:
        row = torch.zeros(size).double()
        row[3 * component.tip:3 * component.tip + 3] = doubles(vector)
        row[3 * component.base:3 * component.base + 3] -= doubles(vector)
        rows.append(row)
    basis = torch.eye(size).double()
    if rows:
      _, values, turn = torch.linalg.svd(torch.stack(rows, 0))
      rank = int((values > 1e-10 * float(values.max())).sum())
      basis = turn[rank:].T.contiguous()
    weights = masses.repeat_interleave(3)
    reduced = basis.T @ (weights[:, None] * basis)
    projector = basis @ torch.linalg.inv(reduced) @ basis.T
    return {'basis': basis, 'reduced': reduced, 'projector': projector}

  def _lines(self, name: str, x: torch.Tensor) -> tuple:
    """The springs' or dampers' ends, the unit vectors from their first
    points to their second, at 'x', and their lengths."""
    first, second = self._tensor(name)
    between = x[second] - x[first]
    length = (between ** 2).sum(-1).sqrt().clamp_min(_SHORTEST)
    return first, second, between / length[:, None], length

  def _potential(self, x: torch.Tensor) -> float:
    """The energy of the springs and of height, at 'x'."""
    return self.elasticEnergy(x) + self.gravityEnergy(x)

  def _tryStep(self, x: torch.Tensor, energy: float, push: torch.Tensor,
               shift: float, scale: float) -> tuple:
    """A step towards rest from 'x', of the energy 'energy', pushed by
    'push' along the ways the points may move: Newton's, made shorter,
    the stiffness shifted, until the energy falls; 'None' if it never
    does."""
    basis = self.basis
    stiffness = basis.T @ self.tangent(x) @ basis
    weights = self._tensor('reduced')
    while shift <= 1e12 * scale:
      move = torch.linalg.pinv(stiffness + shift * weights) @ push
      moved = x + (basis @ move).reshape(-1, 3)
      after = self._potential(moved)
      if after <= energy + 1e-12 * scale:
        return moved, after, shift / 4 if shift > 1e-9 else 0.0
      shift = max(4 * shift, 1e-6)
    return None, energy, shift
