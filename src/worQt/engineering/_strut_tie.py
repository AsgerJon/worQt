"""
StrutTie is the strut-and-tie model of a disk: a tied arch, and the
lower bound it gives.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._disk import Disk
from ._edge_num import EdgeNum

_TOLERANCE = 1e-9
_SPLIT_STEPS = 80  # halvings finding where the loads split
_FACTOR_STEPS = 80  # halvings finding the lower bound


class StrutTieMember(NamedTuple):
  """
  StrutTieMember is a member of a strut-and-tie model: its 'kind',
  'strut' or 'tie', where it runs from and to, in metres, the 'force'
  it carries, in kN, and the 'width' a strut needs at nu fc, in metres,
  nought for a tie.
  """

  kind: str
  start: tuple[float, float]
  end: tuple[float, float]
  force: float
  width: float


class StrutTieCheck(NamedTuple):
  """
  StrutTieCheck is a check of a strut-and-tie model: its 'name', the
  'demand' on it and the 'capacity' it has, in the same units, and the
  'utilisation', the one over the other.
  """

  name: str
  demand: float
  capacity: float

  @property
  def utilisation(self) -> float:
    """The demand over the capacity; endless for a demand on nothing."""
    if self.capacity > 0:
      return self.demand / self.capacity
    return 0.0 if self.demand <= 0 else math.inf


class StrutTie(BaseObject):
  """
  StrutTie is the strut-and-tie model of a disk on two supports on its
  bottom edge, loaded pressing down on its top edge: a tied arch. The
  loads are split by the support they go to, so each part is carried
  straight down to its support by a strut; the two struts are held apart
  at the top by the top strut and together at the bottom by the tie,
  which the horizontal reinforcement running between the supports makes,
  at the height of its centroid. The arch is in equilibrium whatever the
  loads, so the model is statically admissible.

  Every strut is held to nu fc over the thickness, nu = 0.7 - fc / 200
  with fc in MPa (M. P. Nielsen): the top strut takes the depth its
  force needs below the top edge, which sets the lever arm; a strut at a
  support is held to the width the node gives it, the bearing times the
  sine of its angle and the tie zone, twice the tie's height, times the
  cosine. The bearings and the loads press on nu fc, and the tie yields
  at As fy. 'checks' are these at the loads as they are; 'factor' is
  the lower bound, how many times the loads may be what they are with no
  check exceeded, and 'governing' the check that gives out first.

  A disk the tied arch does not fit is not 'applicable', and 'reason'
  says why.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_tie_height__ = 0.05  # metres: where a missing tie would go

  #  Private Variables
  __model_disk__: Disk | None = None
  __model_reason__: str | None = None
  __model_factor__: float | None = None

  #  Virtual Variables
  disk: Field[Disk] = Field()
  applicable: Field[bool] = Field()
  reason: Field[str] = Field()
  nu: Field[float] = Field()
  factor: Field[float] = Field()
  governing: Field[str] = Field()
  members: Field[tuple[StrutTieMember, ...]] = Field()
  nodes: Field[tuple[tuple[float, float], ...]] = Field()
  checks: Field[tuple[StrutTieCheck, ...]] = Field()
  tieCapacity: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @disk.GET
  def _getDisk(self, ) -> Disk:
    """The 'disk' getter returns the disk modelled."""
    if self.__model_disk__ is None:
      raise MissingVariable(self, '__model_disk__', Disk)
    return self.__model_disk__

  @applicable.GET
  def _getApplicable(self, ) -> bool:
    """The 'applicable' getter tells whether the tied arch fits the
    disk."""
    return True if self.__model_reason__ is None else False

  @reason.GET
  def _getReason(self, ) -> str:
    """The 'reason' getter says why the tied arch does not fit the disk,
    and is empty where it does."""
    return '' if self.__model_reason__ is None else self.__model_reason__

  @nu.GET
  def _getNu(self, ) -> float:
    """The 'nu' getter returns the effectiveness factor of the concrete,
    0.7 - fc / 200."""
    return 0.7 - self.disk.fc / 200

  @factor.GET
  def _getFactor(self, ) -> float:
    """The 'factor' getter returns the lower bound: how many times the
    loads may be what they are."""
    if self.__model_factor__ is None:
      self.__model_factor__ = self._findFactor()
    return self.__model_factor__

  @governing.GET
  def _getGoverning(self, ) -> str:
    """The 'governing' getter returns the name of the check that gives
    out first."""
    if not self.applicable:
      return ''
    scale = self.factor if self.factor > 0 else 1.0
    checks = self.checksAt(scale)
    worst = max(check.utilisation for check in checks)
    for check in checks:
      if check.utilisation == worst:
        return check.name

  @members.GET
  def _getMembers(self, ) -> tuple[StrutTieMember, ...]:
    """The 'members' getter returns the struts and the tie, at the loads
    as they are."""
    return self._solve(1.0)[0] if self.applicable else ()

  @nodes.GET
  def _getNodes(self, ) -> tuple[tuple[float, float], ...]:
    """The 'nodes' getter returns where the members meet."""
    return self._solve(1.0)[1] if self.applicable else ()

  @checks.GET
  def _getChecks(self, ) -> tuple[StrutTieCheck, ...]:
    """The 'checks' getter returns the checks at the loads as they
    are."""
    return self.checksAt(1.0)

  @tieCapacity.GET
  def _getTieCapacity(self, ) -> float:
    """The 'tieCapacity' getter returns the force the tie yields at, in
    kN: As fy."""
    return self._tie()[0] * self.disk.fy / 1000.0

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Disk)
  def __init__(self, disk: Disk) -> None:
    self.__model_disk__ = disk
    self.__model_reason__ = self._unfit(disk)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def checksAt(self, scale: float) -> tuple[StrutTieCheck, ...]:
    """The 'checksAt' method returns the checks with the loads 'scale'
    times what they are."""
    return self._solve(scale)[2] if self.applicable else ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  # \___________
  #  The fit  ]
  # /¨¨¨¨¨¨¨¨¨¨¨

  @staticmethod
  def _unfit(disk: Disk) -> str | None:
    """Why the tied arch does not fit 'disk', or 'None'."""
    supports = disk.supports
    bottom = [s for s in supports if s.edge is EdgeNum.BOTTOM]
    if len(supports) != 2 or len(bottom) != 2:
      return 'the tied arch needs two supports on the bottom edge'
    if not disk.loads:
      return 'the tied arch needs a load on the top edge'
    for load in disk.loads:
      down = abs(load.fx) < _TOLERANCE and load.fy < 0
      if load.edge is not EdgeNum.TOP or not down:
        return 'the tied arch takes loads pressing down on the top edge'
    first, second = sorted(s.start + s.end for s in supports)
    if abs(first - second) < _TOLERANCE:
      return 'the tied arch needs its supports apart'
    left, right = StrutTie._reactions(disk)
    if left <= 0 or right <= 0:
      return 'a support would lift: the loads lie beyond it'
    return None

  @staticmethod
  def _bearings(disk: Disk) -> tuple:
    """The left and the right support."""
    first, second = disk.supports
    if first.start + first.end <= second.start + second.end:
      return first, second
    return second, first

  @staticmethod
  def _parts(disk: Disk) -> list[tuple[float, float, float]]:
    """Each load as its stretch and its force per metre, pressing
    down."""
    return [(l.start, l.end, -l.fy / l.width) for l in disk.loads]

  @staticmethod
  def _reactions(disk: Disk) -> tuple[float, float]:
    """The reactions of the left and the right support, at the loads as
    they are."""
    left, right = StrutTie._bearings(disk)
    xA, xB = (left.start + left.end) / 2, (right.start + right.end) / 2
    parts = StrutTie._parts(disk)
    total = sum(q * (e - s) for s, e, q in parts)
    moment = sum(q * (e * e - s * s) / 2 for s, e, q in parts)
    rightReaction = (moment - total * xA) / (xB - xA)
    return total - rightReaction, rightReaction

  # \___________
  #  The arch  ]
  # /¨¨¨¨¨¨¨¨¨¨¨

  def _split(self, ) -> tuple[float, float]:
    """Where the part of the loads going to each support is carried
    from: the centroid of the loads left of where they split by the
    reactions, and of those right of it."""
    parts = self._parts(self.disk)
    leftReaction, rightReaction = self._reactions(self.disk)

    def carried(x: float) -> float:
      return sum(q * min(max(x - s, 0.0), e - s) for s, e, q in parts)

    low = min(s for s, e, q in parts)
    high = max(e for s, e, q in parts)
    for _ in range(_SPLIT_STEPS):
      middle = (low + high) / 2
      if carried(middle) < leftReaction:
        low = middle
      else:
        high = middle
    split = (low + high) / 2
    leftMoment = rightMoment = 0.0
    for s, e, q in parts:
      cut = min(max(split, s), e)
      leftMoment += q * (cut * cut - s * s) / 2
      rightMoment += q * (e * e - cut * cut) / 2
    return leftMoment / leftReaction, rightMoment / rightReaction

  def _tie(self, ) -> tuple[float, float]:
    """The area, in mm², of the horizontal reinforcement running between
    the supports, and the height of its centroid, in metres; where there
    is none, nought and the height a tie would go at."""
    left, right = self._bearings(self.disk)
    xA, xB = (left.start + left.end) / 2, (right.start + right.end) / 2
    area = moment = 0.0
    for rebar in self.disk.rebars:
      xs = (rebar.start[0], rebar.end[0])
      spans = min(xs) <= xA + _TOLERANCE and max(xs) >= xB - _TOLERANCE
      if rebar.horizontal and spans:
        area += rebar.area
        moment += rebar.area * rebar.start[1]
    if area <= 0:
      return 0.0, self.__fallback_tie_height__
    return area, moment / area

  def _solve(self, scale: float) -> tuple:
    """The members, the nodes and the checks with the loads 'scale'
    times what they are."""
    disk = self.disk
    nuFct = self.nu * disk.fc * 1000.0 * disk.thickness  # kN a metre
    left, right = self._bearings(disk)
    xA, xB = (left.start + left.end) / 2, (right.start + right.end) / 2
    leftReaction, rightReaction = self._reactions(disk)
    rA, rB = leftReaction * scale, rightReaction * scale
    x1, x2 = self._split()
    area, yT = self._tie()
    depth = disk.height - yT
    moment = rA * (x1 - xA)
    discriminant = depth * depth - 2 * moment / nuFct
    horizontal = nuFct * (depth - math.sqrt(max(discriminant, 0.0)))
    topDepth = horizontal / nuFct
    yC = disk.height - topDepth / 2
    strutA = math.hypot(rA, horizontal)
    strutB = math.hypot(rB, horizontal)
    tieZone = 2 * yT
    members = (
      StrutTieMember('tie', (xA, yT), (xB, yT), horizontal, 0.0),
      StrutTieMember('strut', (xA, yT), (x1, yC), strutA, strutA / nuFct),
      StrutTieMember('strut', (x1, yC), (x2, yC), horizontal, topDepth),
      StrutTieMember('strut', (x2, yC), (xB, yT), strutB, strutB / nuFct),
    )
    nodes = ((xA, yT), (x1, yC), (x2, yC), (xB, yT))
    widthA = self._nodeWidth(left.width, tieZone, x1 - xA, yC - yT)
    widthB = self._nodeWidth(right.width, tieZone, xB - x2, yC - yT)
    pressure = max(q for s, e, q in self._parts(disk)) * scale
    checks = (
      StrutTieCheck('strut at the left support', strutA, nuFct * widthA),
      StrutTieCheck('strut at the right support', strutB, nuFct * widthB),
      StrutTieCheck('top strut', moment, nuFct * depth * depth / 2),
      StrutTieCheck('tie', horizontal, area * disk.fy / 1000.0),
      StrutTieCheck('bearing at the left support', rA, nuFct * left.width),
      StrutTieCheck('bearing at the right support', rB,
                    nuFct * right.width),
      StrutTieCheck('load on the top edge', pressure, nuFct),
    )
    return members, nodes, checks

  @staticmethod
  def _nodeWidth(bearing: float, zone: float, run: float,
                 rise: float) -> float:
    """The width a node at a support gives the strut leaving it: the
    bearing times the sine of the strut's angle and the tie zone times
    its cosine."""
    length = math.hypot(run, rise)
    return bearing * rise / length + zone * abs(run) / length

  def _findFactor(self, ) -> float:
    """The lower bound, found by halving: the most the loads may be
    multiplied by with no check exceeded."""
    if not self.applicable:
      return 0.0

    def worst(scale: float) -> float:
      return max(check.utilisation for check in self.checksAt(scale))

    if math.isinf(worst(1.0)):
      return 0.0
    high = 1.0
    while worst(high) <= 1.0 and high < 1e6:
      high *= 2
    low = 0.0
    for _ in range(_FACTOR_STEPS):
      middle = (low + high) / 2
      if worst(middle) <= 1.0:
        low = middle
      else:
        high = middle
    return low
