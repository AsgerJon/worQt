"""
Sleep is Asger's night in the bed (user, 2026-11-17: "Asger should be
able to key_E into bed to advance the time to morning if it is dark,
otherwise it should say like in Minecraft, 'you can only sleep at
night'"): he lies down, the screen goes dark over 'FALL' s, time is sent
on to the morning (leapt on the ground, warped off it), and he wakes as
it lightens over 'WAKE' s. Qt-free; real time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

#  How long the screen takes to go dark as he falls asleep, and to come
#  back as he wakes, s of real time.
FALL = 1.5
WAKE = 1.2


class Sleep:
  """
  Sleep holds a night's sleep: whether he is asleep ('on'), when he lay
  down ('since', s of real time), how long till the morning ('wait', s
  of the game's) and when that is ('until', the timekeeper's 'elapsed'),
  whether time has been sent on to it ('sent'), and when he woke
  ('woke', s of real time; None: not yet).
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  on: bool
  since: float
  wait: float
  until: float
  sent: bool
  woke: float | None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, ) -> None:
    self.on, self.since, self.wait, self.until = False, 0.0, 0.0, 0.0
    self.sent, self.woke = False, None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def lay(self, now: float, wait: float, elapsed: float) -> None:
    """The 'lay' method lays him down at 'now' (real s), the morning
    'wait' s on from the game's 'elapsed'."""
    self.on, self.since, self.wait = True, float(now), float(wait)
    self.until = float(elapsed) + self.wait
    self.sent, self.woke = False, None

  def due(self, now: float) -> bool:
    """The 'due' method says whether time is to be sent on now: asleep,
    the screen dark, not sent yet."""
    return self.on and not self.sent and now - self.since >= FALL

  def waking(self, now: float) -> None:
    """The 'waking' method wakes him at 'now' (real s): the screen
    lightens."""
    if self.woke is None:
      self.woke = float(now)

  def shade(self, now: float) -> float:
    """The 'shade' method returns how dark the screen is at 'now' (real
    s): nought to one; past waking, it ends the sleep."""
    if not self.on:
      return 0.0
    if self.woke is None:
      return min(1.0, max(0.0, (now - self.since) / FALL))
    left = 1.0 - (now - self.woke) / WAKE
    if left <= 0.0:
      self.on = False
      return 0.0
    return min(1.0, left)
