"""
The parts of a rig: 'Support', 'Actuator' and 'Control'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple

#  What each kind of support holds: along, across and turning
_HOLDS = {
    'pin': (1, 1, 0),
    'roller': (0, 1, 0),
    'fixed': (1, 1, 1),
}


class Support(NamedTuple):
  """
  Support is what a beam rests on, 'at' mm from its left end, of a
  'kind': a 'pin' holds it along and across, a 'roller' across only and
  a 'fixed' clamp holds it turning too. 'holds' says which, along,
  across and turning, 1 held and 0 free.
  """

  at: float
  kind: str

  @property
  def holds(self) -> tuple[int, int, int]:
    """What the support holds: along, across and turning."""
    return _HOLDS[self.kind]

  @staticmethod
  def kinds() -> tuple[str, ...]:
    """The kinds of support there are."""
    return (*_HOLDS,)


class Actuator(NamedTuple):
  """
  Actuator is a servo-hydraulic actuator hung over a beam, 'at' mm from
  its left end, pushing it down or pulling it up. One actuator is
  driven by the rig's 'Control': it moves as the control says, and
  pushes with whatever force that takes.
  Every other actuator 'follows' another, by its index, pushing a
  'share' of the force that one pushes with, so a chain of them pushes
  the products of the shares of the force of the one driven. The one
  driven follows none, -1.
  """

  at: float
  follows: int
  share: float


class Control(NamedTuple):
  """
  Control is the rig's control loop: it reads the 'transducer' of its
  index and moves the 'actuator' of its index to make the reading
  follow its command, a ramp from nought at 'rate' mm/s to 'limit' mm,
  held there, either way: a transducer under the beam reads less than
  nought as the beam bends down, so a ramp down has a rate and a limit
  below nought. Each step of the test, a step of OpenSees, the command
  moves the share 'step' of its ramp, from where the ramp began to its
  limit: 0.001 is a thousand steps to the limit; so the control looks
  every 'step' times the ramp's length over its rate seconds, its
  'cycle', from nought. Each cycle a PID controller of gains 'kp'
  (1/s), 'ki' (1/s²) and 'kd' turns the error between the command and
  the reading into how fast the actuator moves, up positive as the
  reading is, as its servo valve opens, at most 'speed' mm/s either
  way.
  """

  transducer: int
  actuator: int
  rate: float
  limit: float
  step: float
  kp: float
  ki: float
  kd: float
  speed: float

  @property
  def cycle(self) -> float:
    """The seconds between two looks of the control, its ramp from
    nought: a step of it at its rate."""
    return abs(self.step * self.limit / self.rate)

  def towards(self, start: float) -> Control:
    """The control with its rate's sign turned, if need be, so that its
    ramp heads from 'start' for its limit, as fast."""
    if (self.limit - start) * self.rate < 0:
      return self.changed('rate', -self.rate)
    return self

  def changed(self, name: str, value: float) -> Control:
    """The control with its field 'name' set to 'value'."""
    values = [*self]
    values[self._fields.index(name)] = value
    return Control(*values)
