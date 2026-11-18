"""
Accelerometer is what the vessel feels (user, 2026-11-17: Asger getting
up and floating round in micro-gravity, "FAFO rules"): its push, its
turning and how fast its turning changes, each in its own axes; and from
them the pull on anything loose in its cabin ('pullAt'). What it reads
is simulated, the very frame's (user, 2026-11-17, after Asger suddenly
had gravity docked to Terra Prime: "there better be a physically
simulated such fucking thing every where it needs to be calculated";
"There is NEVER gravity when in orbit EVER!!!"): the push is what the
frame's forces but gravity pushed the vessel a kilogram, summed by the
flight's kernel where it applies them ('Vessel.felt': the thrust, drag,
the legs on the ground, the thrusters, the station's solids), docked
the latch's ('DockingPort.heldOn'); a jolt between frames (the latch
catching, undocking: 'Vessel.jolt') is felt over the frame it falls in.
Nothing is kept from frame to frame and nothing is assumed: before a
frame has been simulated there is nothing to read, and reading then
raises.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._turns import cross, unrotated

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._vessel import Vessel


class Accelerometer:
  """
  Accelerometer reads the vessel each frame ('measured'): 'felt', the
  push it feels a kg (m/s², its own axes: everything but gravity, which
  pulls everything in it alike; on the pad the ground's one g up, in
  orbit nought), 'turning' (its spin, rad/s, its own axes) and
  'speeding' (how fast that changed over the frame, rad/s²), each None
  till it has read a simulated frame.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  felt: tuple | None
  turning: tuple | None
  speeding: tuple | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.felt, self.turning, self.speeding = None, None, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def measured(self, vessel: Vessel, seconds: float) -> None:
    """The 'measured' method reads 'vessel' after a frame of 'seconds' s
    of the game's time: its simulated push and spin, and a jolt and a
    twirl it took between frames felt over this one (then spent)."""
    if vessel.felt is None or vessel.spinning is None:
      raise ValueError('the vessel has not been simulated yet: nothing '
                       'to feel')
    felt = tuple(vessel.felt)
    jolt = vessel.jolt
    if any(jolt) and seconds > 0.0:
      own = unrotated(vessel.turn, jolt)
      felt = tuple(f + j / seconds for f, j in zip(felt, own))
      vessel.jolt = (0.0, 0.0, 0.0)
    speeding = tuple(vessel.spinning)
    twirl = vessel.twirl
    if any(twirl) and seconds > 0.0:
      speeding = tuple(s + w / seconds for s, w in zip(speeding, twirl))
      vessel.twirl = (0.0, 0.0, 0.0)
    self.felt = felt
    self.turning = tuple(vessel.spin)
    self.speeding = speeding

  def grounded(self, felt: tuple, turning: tuple) -> None:
    """The 'grounded' method reads a frame held on a turning body's
    ground (the pad's, '_pad.Pad.feltOf'): its push 'felt' and its
    turning 'turning', steady (its own axes)."""
    self.felt, self.turning = tuple(felt), tuple(turning)
    self.speeding = (0.0, 0.0, 0.0)

  def pullAt(self, place: tuple, velocity: tuple) -> tuple:
    """The 'pullAt' method returns the pull on something loose at
    'place' moving 'velocity' (the vessel's own axes, from its middle),
    m/s²: the vessel's push the other way, its turning's (out from the
    axis it turns about, across the way it moves, and as it turns
    faster)."""
    if self.felt is None:
      raise ValueError('nothing measured yet: nothing to feel')
    turning, speeding = self.turning, self.speeding
    out = cross(turning, cross(turning, place))
    sideways = cross(turning, velocity)
    faster = cross(speeding, place)
    return tuple(-f - o - 2.0 * s - a for f, o, s, a in zip(
      self.felt, out, sideways, faster))
