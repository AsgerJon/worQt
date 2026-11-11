"""
BilliardsSounds decides what a shot shown sounds like and has a
'SoundPlayer', a process of its own, play it.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from ...pusher._sound_player import SoundPlayer

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from .. import Recording

#  Where the billiards' sounds are made.
BANK = 'worQt.gaming.billiards._sounds:takes'


class BilliardsSounds(BaseObject):
  """
  BilliardsSounds decides what a shot shown sounds like and has its
  'player', a 'SoundPlayer' in a process of its own, play it, nothing of
  the window waiting on sound: the cue's tock as the cue ball is struck,
  louder the harder; a clack for each ball meeting a ball and a thud for
  each ball into a cushion as the shot shown passes them, louder the
  faster they meet, a few at most at once; a pin's own note as a ball
  knocks it and as it falls (keglebillard); a fanfare for a point; and,
  while a shot is played fast ('fastForward'), a wind up, a whirr over
  and over, and a wind down. 'enabled' turns it all on and off.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  __most_at_once__ = 4  # sounds started at most in one go
  __loud_speed__ = 3500.0  # mm/s meeting at which a sound is loudest
  __landed_up__ = 0.26  # a pin's axis this far up, cos 75 deg, has fallen
  __landed_volume__ = 0.45  # how loud a pin falling onto the cloth rings

  #  Private Variables
  __sound_player__: SoundPlayer | None = None
  __sound_enabled__: bool = True
  __sound_whirring__: bool = False

  #  Virtual Variables
  player: Field[SoundPlayer] = Field()
  enabled: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @player.GET
  def _getPlayer(self, ) -> SoundPlayer:
    """The 'player' getter returns the sound process's handle, made the
    first time."""
    if self.__sound_player__ is None:
      self.__sound_player__ = SoundPlayer()
    return self.__sound_player__

  @enabled.GET
  def _getEnabled(self, ) -> bool:
    """The 'enabled' getter tells whether sounds are played."""
    return self.__sound_enabled__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @enabled.SET
  def _setEnabled(self, enabled: bool) -> None:
    """The 'enabled' setter turns sounds on or off, a whirr stopped."""
    self.__sound_enabled__ = True if enabled else False
    if not enabled and self.__sound_whirring__:
      self.player.stop('whirr')
      self.__sound_whirring__ = False

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def start(self, folder: str) -> None:
    """The 'start' method has the sound process start, making the
    billiards' sounds into 'folder'."""
    self.player.start(folder, BANK)

  def heard(self, ) -> None:
    """The 'heard' method reads what the sound process said."""
    self.player.heard()

  def close(self, ) -> None:
    """The 'close' method ends the sound process."""
    self.player.close()

  def volumeOf(self, speed: float) -> float:
    """The 'volumeOf' method returns how loud a meeting at 'speed' mm/s
    sounds, 0 to 1."""
    return min(1.0, 0.12 + 0.88 * speed / self.__loud_speed__)

  def struck(self, speed: float) -> None:
    """The 'struck' method plays the cue's tock for a cue ball sent at
    'speed' mm/s."""
    self._play('tock', self.volumeOf(speed))

  def between(self, recording: Recording, start: float,
              end: float) -> None:
    """The 'between' method plays the meetings of 'recording' that began
    after 'start' and by 'end', in s from the stroke: a clack for balls
    meeting, louder the faster they met, a thud for a ball into a
    cushion, louder the faster it came; in keglebillard a pin's note, a
    xylophone's bar, for a ball knocking it, louder the faster, and
    softer as it falls onto the cloth; sad when red knocks it, a foul
    (the user), and as a pin credited to red falls; happy as red
    meets its second white, 'rødt' (the user); and a ball dropping into
    a pocket, a white neutral, red sad (the user); a few at most."""
    played = 0
    for index, (time, touch) in enumerate(recording.touches):
      if time <= start:
        continue
      if time > end or played >= self.__most_at_once__:
        break
      named = {ball.name: ball for ball in
               recording.ballsAt(max(time - 0.002, 0.0))}
      first = named.get(touch.first)
      if first is None:
        continue
      if touch.kind == 'ball' and touch.second in named:
        other = named[touch.second]
        speed = math.hypot(first.vx - other.vx, first.vy - other.vy)
        self._play('clack', self.volumeOf(speed))
        if recording.pinParts and _madeRed(recording, index):
          self._play('carom', 0.8)
      elif touch.kind == 'cushion':
        self._play('thud', self.volumeOf(math.hypot(first.vx, first.vy)))
      elif touch.kind == 'pin':
        name = 'sadPin' if touch.first == 'red' else 'pin'
        self._play(name + touch.second,
                   self.volumeOf(math.hypot(first.vx, first.vy)))
      elif touch.kind == 'pocket':
        sad = touch.first == 'red'
        loud = max(self.volumeOf(math.hypot(first.vx, first.vy)), 0.5)
        self._play('sadPocket' if sad else 'pocket', loud)
      else:
        continue
      played += 1
    self._landings(recording, start, end, self.__most_at_once__ - played)

  def fastForward(self, fast: bool) -> None:
    """The 'fastForward' method winds up and whirrs while a shot is
    played 'fast', and stops the whirr and winds down once it is not."""
    fast = True if fast and self.__sound_enabled__ else False
    if fast == self.__sound_whirring__:
      return
    self.__sound_whirring__ = fast
    if fast:
      self._play('windUp', 0.6)
      self.player.loop('whirr', 0.45)
    else:
      self.player.stop('whirr')
      self._play('windDown', 0.5)

  def fanfare(self, ) -> None:
    """The 'fanfare' method plays the fanfare of a point made."""
    self._play('fanfare', 0.85)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _landings(self, recording: Recording, start: float, end: float,
                room: int) -> None:
    """Plays the note of each pin of 'recording' falling onto the cloth
    after 'start' and by 'end', its axis coming down past
    '__landed_up__' of upright, the sad one for a pin credited to red;
    'room' at most."""
    if room <= 0 or not recording.pinParts:
      return
    before, after = recording.pinsAt(start), recording.pinsAt(end)
    red = recording.names.index('red') if 'red' in recording.names else -1
    for one, other in zip(before, after):
      if room <= 0:
        return
      if _upOf(one) > self.__landed_up__ >= _upOf(other):
        number = int(one[0])
        if red >= 0 and int(other[9]) == red:
          self._play('sadLand%d' % number, self.__landed_volume__)
        else:
          self._play('pin%d' % number, self.__landed_volume__)
        room -= 1

  def _play(self, name: str, volume: float) -> None:
    """Plays 'name' at 'volume', if sounds are on."""
    if self.__sound_enabled__:
      self.player.play(name, volume)


def _upOf(row: object) -> float:
  """Returns how far up a pin's axis points, a share, its state 'row'
  as a sample holds it ('PIN_STATE'): one upright, nought lying."""
  qx, qy = float(row[5]), float(row[6])
  return 1.0 - 2.0 * (qx * qx + qy * qy)


def _madeRed(recording: Recording, index: int) -> bool:
  """Tells whether touch 'index' of keglebillard's 'recording' is red
  meeting a white for the first time, having met the other: 'rødt'."""
  touches = [touch for _, touch in recording.touches]
  touch = touches[index]
  if touch.kind != 'ball' or 'red' not in (touch.first, touch.second):
    return False
  met = {each.second if each.first == 'red' else each.first
         for each in touches[:index]
         if each.kind == 'ball' and 'red' in (each.first, each.second)}
  other = touch.second if touch.first == 'red' else touch.first
  return len(met) == 1 and other not in met
