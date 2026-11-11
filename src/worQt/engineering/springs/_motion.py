"""
Motion is a system of springs moving, stepped through time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .._doubles import doubles
from ._system import System


class Energies(NamedTuple):
  """
  Energies are the energies of a system in motion, in J: the points'
  'kinetic' energy, moving, the springs' 'elastic' energy, the points'
  energy of height, 'gravity', from where the motion began, the energy
  the dampers have 'dissipated' as heat, and the work done by the 'hand'
  holding points. Their 'total', all but the hand's work, stays what it
  began as.
  """

  kinetic: float
  elastic: float
  gravity: float
  dissipated: float
  hand: float

  @property
  def total(self) -> float:
    """The energy the motion began with: what it has, what it has lost
    as heat, less what the hand has put in."""
    return (self.kinetic + self.elastic + self.gravity + self.dissipated
            - self.hand)


class Sample(NamedTuple):
  """
  Sample is a motion at a 'time', in s: where its points are,
  'positions', and its 'energies'.
  """

  time: float
  positions: torch.Tensor
  energies: Energies


class Motion(BaseObject):
  """
  Motion is a 'system' in motion: its points at 'positions' moving at
  'velocities', 'time' seconds on, as their guides let them, stepped by
  velocity Verlet, which keeps the energy of a system without dampers,
  swinging back and forth about what it began with, never drifting off;
  each step a small part of the quickest swing in the system, so a stiff
  spring takes many steps. 'advance' moves it on, at most so many steps
  a call, 'slowed' if they took it less far than asked. 'samples' are
  the motion as it was after each call, the last minute of it.

  A point may be held, by the hand dragging it: 'hold' pulls it towards
  where it is held, by a stiff spring with a damper, firm as the point
  is heavy, so it follows the hand closely along the ways its guides
  let it, and an anchor not at all; 'release' lets it go, moving as it
  was, flung. 'energies' keep the account: the work the hand has done,
  and what the dampers have dissipated.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_accuracy__ = 0.02  # of a radian of the quickest swing a step
  __fallback_most_steps__ = 4000  # steps a call to 'advance' takes at most
  __fallback_kept__ = 60.0  # s of samples kept
  __fallback_grip__ = 2 * math.pi * 5.0  # rad/s: how quick the hand is

  #  Private Variables
  __motion_system__: System | None = None
  __motion_state__: tuple[torch.Tensor, torch.Tensor] | None = None
  __motion_time__: float = 0.0
  __motion_heat__: float = 0.0
  __motion_hand__: float = 0.0
  __motion_height__: float = 0.0
  __motion_held__: dict | None = None
  __motion_samples__: list | None = None
  __motion_slowed__: bool = False

  #  Virtual Variables
  system: Field[System] = Field()
  positions: Field[torch.Tensor] = Field()
  velocities: Field[torch.Tensor] = Field()
  time: Field[float] = Field()
  energies: Field[Energies] = Field()
  samples: Field[tuple[Sample, ...]] = Field()
  held: Field[tuple[int, ...]] = Field()
  slowed: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getState(self, ) -> tuple[torch.Tensor, torch.Tensor]:
    if self.__motion_state__ is None:
      raise MissingVariable(self, '__motion_state__', tuple)
    return self.__motion_state__

  @system.GET
  def _getSystem(self, ) -> System:
    """The 'system' getter returns the system moving."""
    if self.__motion_system__ is None:
      raise MissingVariable(self, '__motion_system__', System)
    return self.__motion_system__

  @positions.GET
  def _getPositions(self, ) -> torch.Tensor:
    """The 'positions' getter returns where the points are now, in m."""
    return self._getState()[0].clone()

  @velocities.GET
  def _getVelocities(self, ) -> torch.Tensor:
    """The 'velocities' getter returns how fast the points move now, in
    m/s."""
    return self._getState()[1].clone()

  @time.GET
  def _getTime(self, ) -> float:
    """The 'time' getter returns the seconds the motion has run."""
    return self.__motion_time__

  @energies.GET
  def _getEnergies(self, ) -> Energies:
    """The 'energies' getter returns the energies now."""
    system = self.system
    x, v = self._getState()
    height = system.gravityEnergy(x) - self.__motion_height__
    return Energies(system.kineticEnergy(v), system.elasticEnergy(x),
                    height, self.__motion_heat__, self.__motion_hand__)

  @samples.GET
  def _getSamples(self, ) -> tuple[Sample, ...]:
    """The 'samples' getter returns the motion after each call to
    'advance', the last minute of it."""
    return (*(self.__motion_samples__ or ()),)

  @held.GET
  def _getHeld(self, ) -> tuple[int, ...]:
    """The 'held' getter returns the points held."""
    return (*sorted(self.__motion_held__ or {}),)

  @slowed.GET
  def _getSlowed(self, ) -> bool:
    """The 'slowed' getter tells whether the last call to 'advance' took
    the motion less far than asked, its steps too many."""
    return self.__motion_slowed__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(System, torch.Tensor, torch.Tensor)
  def __init__(self, system: System, positions: torch.Tensor,
               velocities: torch.Tensor) -> None:
    count = len(system.points)
    if tuple(positions.shape) != (count, 3):
      raise ValueError('a motion has a place for each of %d points'
                       % count)
    if tuple(velocities.shape) != (count, 3):
      raise ValueError('a motion has a speed for each of %d points'
                       % count)
    basis = system.basis
    flat = velocities.double().reshape(-1)
    guided = (basis @ (basis.T @ flat)).reshape(-1, 3)
    self.__motion_system__ = system
    self.__motion_state__ = (positions.double().clone(), guided)
    self.__motion_height__ = system.gravityEnergy(positions.double())
    self.__motion_held__ = {}
    self.__motion_samples__ = []
    self._sample()

  @overload(System, torch.Tensor)
  def __init__(self, system: System, positions: torch.Tensor) -> None:
    self.__init__(system, positions, torch.zeros_like(positions))

  @overload(System)
  def __init__(self, system: System) -> None:
    self.__init__(system, system.positions())

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advance(self, seconds: float) -> float:
    """The 'advance' method moves the motion on 'seconds', in steps small
    enough, at most so many, and returns how far it went."""
    if not seconds > 0:
      return 0.0
    x, _ = self._getState()
    rate = self.system.quickest(x)
    if self.__motion_held__:
      rate = max(rate, 2 * self.__fallback_grip__)
    longest = seconds
    if rate > 0:
      longest = min(seconds, self.__fallback_accuracy__ / rate)
    needed = math.ceil(seconds / longest - 1e-9)
    step = seconds / needed
    most = self.__fallback_most_steps__
    self.__motion_slowed__ = True if needed > most else False
    count = min(needed, most)
    for _ in range(count):
      self._step(step)
    self.__motion_time__ += count * step
    self._sample()
    return count * step

  def hold(self, index: int, at: tuple[float, float, float]) -> None:
    """The 'hold' method holds the point of 'index', pulling it towards
    'at', in m, as long as it is held."""
    if not 0 <= index < len(self.system.points):
      raise IndexError('there is no point P%d' % (index + 1))
    self.__motion_held__[index] = doubles([*at])

  def release(self, index: int) -> None:
    """The 'release' method lets the point of 'index' go, moving as it
    was."""
    self.__motion_held__.pop(index, None)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _hand(self, x: torch.Tensor, v: torch.Tensor) -> torch.Tensor:
    """The hand's pull on the points held, at 'x' moving at 'v': a stiff
    spring to where each is held, with a damper, firm as it is heavy."""
    pull = torch.zeros_like(x)
    grip = self.__fallback_grip__
    for index, target in self.__motion_held__.items():
      mass = float(self.system.masses[index])
      pull[index] = mass * (grip * grip * (target - x[index])
                            - 2 * grip * v[index])
    return pull

  def _step(self, step: float) -> None:
    """A step of velocity Verlet, 'step' seconds long, the points
    moving as their guides let them, the hand pulling those held."""
    system = self.system
    x, v = self._getState()
    hand = self._hand(x, v)
    before = system.forces(x, v) + hand
    half = v + system.accelerations(before) * (0.5 * step)
    after = x + half * step
    handAfter = self._hand(after, half)
    forces = system.forces(after, half) + handAfter
    v = half + system.accelerations(forces) * (0.5 * step)
    middle = 0.5 * (x + after)
    self.__motion_heat__ += system.dissipation(middle, half) * step
    if self.__motion_held__:
      push = 0.5 * (hand + handAfter)
      self.__motion_hand__ += float((push * (after - x)).sum())
    self.__motion_state__ = (after, v)

  def _sample(self, ) -> None:
    """Notes the motion as it is now, forgetting what is older than a
    minute."""
    x, _ = self._getState()
    samples = self.__motion_samples__
    samples.append(Sample(self.time, x.clone(), self.energies))
    kept = self.__fallback_kept__
    while samples and samples[0].time < self.time - kept:
      del samples[0]
