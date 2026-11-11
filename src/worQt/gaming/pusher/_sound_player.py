"""
SoundPlayer plays a game's sounds, the coin pusher's or another bank of
them, in a process of its own, so a sound system that hangs or dies
never holds up the window.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import importlib
import multiprocessing
import os
import time
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from multiprocessing.connection import Connection

#  The sounds and how many of each may ring at once
COPIES = 3
#  The coin pusher's bank of sounds: where the function making them is.
PUSHER = 'worQt.gaming.pusher._sound_player:_takes'


def _takes() -> dict:
  """Every sound, made: a name, and the takes of it, samples each."""
  from . import _sounds
  clinks = (2900.0, 3300.0, 3750.0, 4300.0)
  return {'clink': [_sounds.clink(f, k) for k, f in enumerate(clinks)],
          'tick': [_sounds.tick(k) for k in range(2)],
          'tray': [_sounds.tray(k) for k in range(2)],
          'beep': [_sounds.beep(880.0)],
          'last': [_sounds.beep(1320.0)],
          'go': [_sounds.go()]}


def _takesOf(bank: str) -> dict:
  """Returns the sounds of 'bank', 'module:function', made by calling
  the function: a name, and the takes of it, samples each."""
  module, name = bank.split(':')
  return getattr(importlib.import_module(module), name)()


def _played(connection: Connection, folder: str, bank: str) -> None:
  """Makes the sounds of 'bank', as '_takesOf' has them, writes them to
  'folder', and plays them as asked over 'connection': ('play', name,
  volume) on a copy not ringing, the copies taken in turn; ('loop',
  name, volume) one copy over and over until ('stop', name, 0) stops
  it. Says ('ready', seconds) once all are loaded, or ('trouble',
  words). None, or the asker gone, ends it. Its Qt runs plain, nothing
  of the asker's, so its threads never wait on Python."""
  import sys
  from pathlib import Path

  from PySide6.QtCore import QLoggingCategory, QTimer, QUrl
  from PySide6.QtGui import QGuiApplication
  from PySide6.QtMultimedia import QSoundEffect

  from . import _sounds

  began = time.perf_counter()
  QLoggingCategory.setFilterRules('qt.multimedia.ffmpeg.info=false\n'
                                  'qt.multimedia.ffmpeg.debug=false')
  app = QGuiApplication(['worQt-sounds', '-platform', 'offscreen'])
  pools = {}
  for name, takes in _takesOf(bank).items():
    pool = []
    for k, samples in enumerate(takes):
      path = Path(folder) / ('worQt-sound-%d-%s-%d.wav' % (os.getpid(),
                                                          name, k))
      path.write_bytes(_sounds.waveBytes(samples))
      for _ in range(COPIES):
        effect = QSoundEffect()
        effect.setSource(QUrl.fromLocalFile(str(path)))
        pool.append(effect)
    pools[name] = pool
  turns = {name: 0 for name in pools}
  looping = {}
  told = [False]

  def ready() -> bool:
    """Whether every copy is loaded."""
    return all(effect.status() == QSoundEffect.Status.Ready
               for pool in pools.values() for effect in pool)

  def heard() -> None:
    """Reads what is asked and plays it; says once when ready."""
    try:
      if not told[0]:
        if ready():
          told[0] = True
          connection.send(('ready', time.perf_counter() - began))
        elif any(effect.status() == QSoundEffect.Status.Error
                 for pool in pools.values() for effect in pool):
          told[0] = True
          connection.send(('trouble', 'a sound would not load'))
      while connection.poll():
        message = connection.recv()
        if message is None:
          app.quit()
          return
        kind, name, volume = message
        pool = pools[name]
        if kind == 'loop':
          effect = looping.get(name) or pool[0]
          effect.setLoopCount(QSoundEffect.Loop.Infinite.value)
          effect.setVolume(max(0.0, min(1.0, volume)))
          if not effect.isPlaying():
            effect.play()
          looping[name] = effect
          continue
        if kind == 'stop':
          effect = looping.pop(name, None)
          if effect is not None:
            effect.stop()
            effect.setLoopCount(1)
          continue
        for _ in range(len(pool)):
          turns[name] = (turns[name] + 1) % len(pool)
          effect = pool[turns[name]]
          if not effect.isPlaying():
            effect.setVolume(max(0.0, min(1.0, volume)))
            effect.play()
            break
    except (EOFError, OSError, BrokenPipeError):
      app.quit()

  timer = QTimer()
  timer.timeout.connect(heard)
  timer.start(10)
  app.exec()
  sys.exit(0)


class SoundPlayer(BaseObject):
  """
  SoundPlayer plays a game's sounds, the coin pusher's unless 'start' is
  given another bank ('module:function', the function returning the
  sounds by name, the takes of each), in a process of its own,
  spawned, nothing of the asker carried over: its Qt runs plain, so the
  sound system's threads never wait on the asker's Python, and if the
  sound system hangs or dies only the sounds stop. 'start' spawns it;
  'play' asks for a sound by name at a volume, never waiting; 'loop'
  plays one over and over until 'stop'; 'heard'
  reads what it said: 'ready' once all its sounds are loaded, after
  'readyAfter' s, or 'trouble'. 'running' tells whether it is there,
  'exitCode' how it ended; 'close' ends it.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_start_method__ = 'spawn'

  #  Private Variables
  __sound_process__: multiprocessing.Process | None = None
  __sound_pipe__: Connection | None = None
  __sound_ready__: float | None = None
  __sound_trouble__: str | None = None

  #  Virtual Variables
  running: Field[bool] = Field()
  exitCode: Field[int] = Field()
  ready: Field[bool] = Field()
  readyAfter: Field[float] = Field()
  trouble: Field[str] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the process is there."""
    process = self.__sound_process__
    return False if process is None else process.is_alive()

  @exitCode.GET
  def _getExitCode(self, ) -> int | None:
    """The 'exitCode' getter returns how the process ended, None while it
    runs or before it started."""
    process = self.__sound_process__
    return None if process is None else process.exitcode

  @ready.GET
  def _getReady(self, ) -> bool:
    """The 'ready' getter tells whether every sound is loaded."""
    return self.__sound_ready__ is not None

  @readyAfter.GET
  def _getReadyAfter(self, ) -> float | None:
    """The 'readyAfter' getter returns how long the sounds took to make
    and load, in s, None until they are."""
    return self.__sound_ready__

  @trouble.GET
  def _getTrouble(self, ) -> str | None:
    """The 'trouble' getter returns what went wrong, if the process said
    so, else None."""
    return self.__sound_trouble__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def start(self, folder: str, bank: str = None) -> None:
    """The 'start' method spawns the process, writing the sounds of
    'bank', the coin pusher's if none is given, to 'folder', if it is
    not there."""
    if self.running:
      return
    self.close()
    context = multiprocessing.get_context(self.__fallback_start_method__)
    mine, theirs = context.Pipe()
    process = context.Process(None, _played, 'worQt-sounds',
                              (theirs, folder, bank or PUSHER))
    process.daemon = True
    process.start()
    theirs.close()
    self.__sound_process__ = process
    self.__sound_pipe__ = mine
    self.__sound_ready__ = None
    self.__sound_trouble__ = None

  def play(self, name: str, volume: float) -> None:
    """The 'play' method asks for sound 'name' at 'volume' (0 to 1), if
    the process is there and ready; it never waits."""
    pipe = self.__sound_pipe__
    if pipe is None or self.__sound_ready__ is None:
      return
    try:
      pipe.send(('play', name, float(volume)))
    except (OSError, BrokenPipeError):
      self.__sound_pipe__ = None

  def loop(self, name: str, volume: float) -> None:
    """The 'loop' method asks for sound 'name' at 'volume' (0 to 1)
    over and over until 'stop' stops it, if the process is there and
    ready; it never waits."""
    self._send(('loop', name, float(volume)))

  def stop(self, name: str) -> None:
    """The 'stop' method stops sound 'name' looping, if it is; it never
    waits."""
    self._send(('stop', name, 0.0))

  def _send(self, message: tuple) -> None:
    """Sends 'message' to the process, if it is there and ready."""
    pipe = self.__sound_pipe__
    if pipe is None or self.__sound_ready__ is None:
      return
    try:
      pipe.send(message)
    except (OSError, BrokenPipeError):
      self.__sound_pipe__ = None

  def heard(self, ) -> None:
    """The 'heard' method reads what the process said, never waiting."""
    pipe = self.__sound_pipe__
    if pipe is None:
      return
    try:
      while pipe.poll():
        kind, value = pipe.recv()
        if kind == 'ready':
          self.__sound_ready__ = value
        else:
          self.__sound_trouble__ = value
    except (EOFError, OSError):
      self.__sound_pipe__ = None

  def close(self, ) -> None:
    """The 'close' method ends the process, if it is there."""
    pipe, process = self.__sound_pipe__, self.__sound_process__
    self.__sound_pipe__ = self.__sound_process__ = None
    if pipe is not None:
      try:
        pipe.send(None)
      except (OSError, BrokenPipeError):
        pass
      pipe.close()
    if process is not None:
      process.join(1.0)
      if process.is_alive():
        process.terminate()
