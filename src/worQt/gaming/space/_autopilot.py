"""
Autopilot keeps a vessel pointed (user, 2026-11-16: "an autopilot that
can lock their orientation in place or locked to following a path
towards apogee, or the opposite point"): it says how, the flight's
kernel turns the reaction wheels to do it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  What it can do, by the number the kernel knows it by: nothing; hold
#  the turn it was given; point the nose along the path (prograde: the
#  velocity over the ground in the air, the orbit's above it); point it
#  against the path (retrograde).
MODES = ('off', 'hold', 'prograde', 'retrograde')


class Autopilot:
  """
  Autopilot holds what a vessel's autopilot does ('mode', one of
  'MODES') and, holding, the turn it holds ('held', w x y z: the
  vessel's to the ecliptic's axes). The kernel does it: within a frame
  by the reaction wheels (the turn's error to a rate, the rate's to a
  torque), within a long step of time warp at once (the warp's rails).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  mode: str
  held: tuple

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.mode, self.held = 'off', (1.0, 0.0, 0.0, 0.0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @property
  def index(self, ) -> int:
    """The 'index' property is the mode's number, as the kernel knows
    it."""
    return MODES.index(self.mode)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def engaged(self, mode: str, turn: tuple) -> None:
    """The 'engaged' method sets the autopilot to 'mode', holding the
    vessel's 'turn' (w x y z) if it holds."""
    if mode not in MODES:
      raise ValueError('no autopilot mode %r: %r' % (mode, MODES))
    self.mode = mode
    if mode == 'hold':
      self.held = tuple(float(x) for x in turn)
