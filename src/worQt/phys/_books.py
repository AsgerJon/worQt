"""
Books keeps the energy a run gains and loses, line by line, and Stored
the energy a world holds at a moment; Grease shakes the bodies at
random, its work booked.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import NamedTuple


class Stored(NamedTuple):
  """
  Stored is the energy bodies hold at a moment, J: 'kinetic', moving
  and turning; 'gravity', their height (nought at the origin);
  'springs', stretched or squeezed; 'ground', pressed into it and held
  by its bristles; 'contacts', bodies pressed into each other and held
  by theirs.
  """

  kinetic: float
  gravity: float
  springs: float
  ground: float
  contacts: float = 0.0

  def total(self, ) -> float:
    """The 'total' method returns all the energy held, J."""
    return (self.kinetic + self.gravity + self.springs + self.ground
            + self.contacts)


class Books(NamedTuple):
  """
  Books is the energy a run has gained and lost, J, line by line: heat
  lost to the 'ground' (its push damped, its bristles damped and
  slipping) and to the 'dampers'; lost as welds 'snaps' parts moving
  apart together; work put in by the 'actuators', by the 'grease' and
  by the 'ties' (ideal ties do none: what is here is the stepping's own
  error, to be nought but for a hair); heat lost where bodies touch,
  'contacts'. What is held at the end, with
  the heat, less the work, is what was held at the start, close
  enough.
  """

  ground: float = 0.0
  dampers: float = 0.0
  snaps: float = 0.0
  actuators: float = 0.0
  grease: float = 0.0
  ties: float = 0.0
  contacts: float = 0.0

  def heat(self, ) -> float:
    """The 'heat' method returns all the energy lost, J."""
    return self.ground + self.dampers + self.snaps + self.contacts

  def work(self, ) -> float:
    """The 'work' method returns all the work put in, J."""
    return self.actuators + self.grease + self.ties

  def plus(self, other: Books) -> Books:
    """The 'plus' method returns these books and 'other' added line by
    line."""
    return Books(*(a + b for a, b in zip(self, other)))


class Grease(NamedTuple):
  """
  Grease shakes every body at random, white noise, seeded: its centre
  as if pushed by an acceleration whose average over a second is
  'shake' m/s² either way, at random (a standard deviation, along each
  axis), and its turning likewise by 'spin' rad/s²; each step's share
  drawn ('normalDraws', a counting hash, the same compiled) from 'seed',
  the step's place in time and the body's place in the assembly, so a
  run cut anywhere on its steps goes on the same and the shaking is the
  same however fine the steps.
  """

  shake: float
  spin: float
  seed: int = 0


class Sleep(NamedTuple):
  """
  Sleep lets bodies at rest sleep, not stepped till something moving
  touches them, an approximation (what little they still shake is
  frozen out). Only a body held by nothing but contacts and the ground
  may sleep; one on a rule (a tie, an actuator, a spring, a damper)
  never does, but counts as still when it is. A body is still slower
  than 'speed' m/s and turning slower than 'spin' rad/s; still for
  'settle' s, everything it touches asleep or still, it falls asleep,
  stopped. Anything awake and moving touching a sleeper wakes it, and
  every sleeper touching that, at once.
  """

  speed: float = 0.002
  spin: float = 0.05
  settle: float = 0.2
