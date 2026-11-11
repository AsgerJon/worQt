"""
PusherSounds decides the coin pusher's sounds as its snapshots come, and
has a 'SoundPlayer', a process of its own, play them: the coins clinking
and knocking as they meet, a coin landing in the tray, the countdown
and the game on.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PySide6.QtCore import QDir

from .._sound_player import SoundPlayer

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from .._machine_worker import Snapshot


class PusherSounds:
  """
  PusherSounds decides what the coin pusher sounds like and has its
  'player', a 'SoundPlayer' in a process of its own, play it: nothing of
  the sound system runs in the window's process, so a sound system that
  hangs or dies never holds the window up (made here, the sounds once
  hung it for good). 'heard' plays what a snapshot says happened since
  the last: for coins meeting coins, up to three clinks, louder the
  harder the hardest hit; for coins meeting the cabinet, up to two
  knocks; for coins landing in the tray, up to three rings; a beep as
  the countdown counts each second, a higher one at the last, and a
  chord as the game is on. Nothing plays while 'enabled' is 'False'.
  """

  def __init__(self, ) -> None:
    self.player = SoundPlayer()
    self.player.start(QDir.tempPath())
    self.__last_count__ = 0
    self.__was_started__ = False
    self.enabled = True

  def played(self, name: str, volume: float) -> None:
    """The 'played' method has sound 'name' played at 'volume' (0 to
    1), unless sounds are off."""
    if self.enabled:
      self.player.play(name, volume)

  def heard(self, snapshot: Snapshot) -> None:
    """The 'heard' method plays what 'snapshot' says happened since the
    last: coins meeting, coins into the tray, the countdown's beats, the
    game on."""
    self.player.heard()
    coins, hardest, knocks, firmest, landed, landing = snapshot.hits
    clinks = 0.15 + 0.6 * min(1.0, hardest / 1200.0)
    for k in range(min(int(coins), 3)):
      self.played('clink', clinks * 0.8 ** k)
    knocking = 0.1 + 0.5 * min(1.0, firmest / 1000.0)
    for k in range(min(int(knocks), 2)):
      self.played('tick', knocking * 0.8 ** k)
    into = max(int(landed), snapshot.wonNow)
    for k in range(min(into, 3)):
      self.played('tray', 0.35 + 0.5 * min(1.0, landing / 1500.0))
    count = math.ceil(snapshot.countdown) if snapshot.countdown > 0 else 0
    if count and count != self.__last_count__:
      self.played('last' if count == 1 else 'beep', 0.7)
    self.__last_count__ = count
    if snapshot.started and not self.__was_started__:
      self.played('go', 0.8)
    self.__was_started__ = snapshot.started

  def close(self, ) -> None:
    """The 'close' method ends the sound process."""
    self.player.close()
