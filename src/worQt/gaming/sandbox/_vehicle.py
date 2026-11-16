"""
Vehicle is what an avatar rides in a world (user, 2026-11-15: "Vehicle:
car, train"; 2026-11-16: a minecart): bodies of the world it puts in
itself, a seat on its frame the rider is held to.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worQt.phys._assembly import Tie
from worQt.phys._body import State

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._world import World


class Vehicle:
  """
  Vehicle holds a vehicle in a world ('world'): its bodies there ('bodies',
  indices; the first its frame, what a rider is held to), the point of the
  frame a rider's middle is tied to ('seat', in the frame's own frame, m) and
  whom it carries ('rider': an avatar, None: no one); its 'name' and what its
  menu says of it ('readout'); how it sounds ('rumble': its speed, its
  wheels' load over standing and the flanges' share of it; None: silent). A
  subclass puts its bodies in a world ('placed', called by
  'World.addVehicle'). 'boarded' sets an avatar's ball in the seat, moving
  with it, and ties it there (the rider's weight on the frame, free to turn
  about the tie); 'left' lets the tie go (the rider where the seat was). Both
  on the world's thread, within a step.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  seat: tuple = (0.0, 0.0, 0.0)
  name: str = 'Vehicle'

  #  Public Variables
  world: World
  bodies: tuple
  rider: object

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.world, self.bodies, self.rider, self._tie = None, (), None, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  REQUIRED METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, world: World) -> None:
    """The 'placed' method puts the vehicle's bodies (and what joins
    them) in 'world', setting 'world' and 'bodies'."""
    raise NotImplementedError(type(self).__name__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def frame(self, ) -> int:
    """The 'frame' property is the index of the vehicle's frame."""
    if not self.bodies:
      raise RuntimeError('the vehicle is in no world yet')
    return self.bodies[0]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def readout(self, states: tuple) -> str:
    """The 'readout' method returns what the vehicle's menu says of it,
    its bodies in 'states': its speed here."""
    speed = sum(v * v for v in states[self.frame].velocity) ** 0.5
    return 'Speed  %.0f km/h' % (3.6 * speed)

  def rumble(self, states: tuple) -> tuple | None:
    """The 'rumble' method returns how the vehicle sounds, its bodies in
    'states' (its speed, m/s, its wheels' load over standing, their
    flanges' share of it), None: silent. Silent here."""
    return None

  def seatOf(self, states: list) -> State:
    """The 'seatOf' method returns a ball in the seat, its frame as in
    'states': where the seat is and how fast it moves."""
    body = self.world.assembly.bodies[self.frame]
    state = states[self.frame]
    return State(body.placeOf(state, self.seat),
                 (1.0, 0.0, 0.0, 0.0), body.velocityOf(state, self.seat))

  def boarded(self, avatar: object, states: list) -> None:
    """The 'boarded' method seats 'avatar' (its ball set in the seat in
    'states', moving with it) and ties it there."""
    if self.rider is not None:
      raise RuntimeError('the vehicle already has a rider')
    states[avatar.index] = self.seatOf(states)
    centre = self.world.assembly.bodies[avatar.index].centre
    self._tie = Tie(self.frame, self.seat, avatar.index, centre)
    self.world.connected(self._tie)
    self.rider = avatar

  def restored(self, ) -> None:
    """The 'restored' method makes the vehicle as it was made, put back
    where it was put ('World._fallenBack'); a vehicle that changes
    nothing of itself as it goes does nothing."""

  def left(self, ) -> None:
    """The 'left' method lets the rider go (where the seat is)."""
    if self.rider is None:
      raise RuntimeError('the vehicle has no rider')
    self.world.loosened(self._tie)
    self._tie, self.rider = None, None
