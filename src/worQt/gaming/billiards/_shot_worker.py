"""
ShotWorker plays shots in a process of its own and streams them back a
'Stretch' at a time.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from multiprocessing.connection import Connection

  from ._carom_table import Ball
  from ._recorder import Recorder, Stretch


def _served(connection: Connection) -> None:
  """Plays each shot asked for over 'connection', its number, a
  'Recorder' and the balls, sending back each 'Stretch' with the shot's
  number as it is done; a new shot asked for drops the one under way;
  'None' asked for, or the asker gone, ends it."""
  message, pending = None, False
  try:
    while True:
      if not pending:
        message = _latest(connection, connection.recv())
      pending = False
      if message is None:
        return
      number, recorder, balls = message
      for stretch in recorder.stretches(balls):
        if connection.poll():
          message, pending = _latest(connection, connection.recv()), True
          break
        connection.send((number, stretch))
  except (EOFError, OSError):
    return


def _latest(connection: Connection, message: object) -> object:
  """Returns the last of 'message' and those waiting after it on
  'connection', each shot asked for dropping the one before; 'None', to
  end, if any is."""
  while message is not None and connection.poll():
    message = connection.recv()
  return message


class ShotWorker(BaseObject):
  """
  ShotWorker plays shots in a process of its own, so the window asking
  goes on showing them as they come: 'start' asks for a shot, a
  'Recorder' and the balls as they are struck, dropping any under way;
  'received' returns the stretches of it come so far, never waiting;
  'waited' waits for one at most so long first. The process is spawned,
  nothing of the asker carried over, on the first 'start' or on 'warm',
  and ends on 'close' or with the asker. 'running' tells whether it is
  there.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_start_method__ = 'spawn'

  #  Private Variables
  __shot_process__: multiprocessing.Process | None = None
  __shot_pipe__: Connection | None = None
  __shot_number__: int = 0

  #  Virtual Variables
  running: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the process is there."""
    process = self.__shot_process__
    return False if process is None else process.is_alive()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def warm(self, ) -> None:
    """The 'warm' method spawns the process, if it is not there, so the
    first shot need not wait for it."""
    if self.running:
      return
    self.close()
    context = multiprocessing.get_context(self.__fallback_start_method__)
    mine, theirs = context.Pipe()
    process = context.Process(None, _served, 'billiards-shots', (theirs,))
    process.daemon = True
    process.start()
    theirs.close()
    self.__shot_process__ = process
    self.__shot_pipe__ = mine

  def start(self, recorder: Recorder, balls: tuple[Ball, ...]) -> None:
    """The 'start' method asks for the shot 'recorder' plays of 'balls',
    dropping any under way."""
    self.warm()
    self.__shot_number__ += 1
    self.__shot_pipe__.send((self.__shot_number__, recorder, tuple(balls)))

  def received(self, ) -> list[Stretch]:
    """The 'received' method returns the stretches of the shot last
    asked for that have come since, in order, never waiting."""
    pipe, out = self.__shot_pipe__, []
    if pipe is None:
      return out
    try:
      while pipe.poll():
        number, stretch = pipe.recv()
        if number == self.__shot_number__:
          out.append(stretch)
    except (EOFError, OSError):
      self.close()
    return out

  def waited(self, seconds: float) -> list[Stretch]:
    """The 'waited' method returns the stretches as 'received' does,
    waiting 'seconds' at most for one to come if none has."""
    pipe = self.__shot_pipe__
    if pipe is None:
      return []
    out = self.received()
    if out or self.__shot_pipe__ is None:
      return out
    try:
      if pipe.poll(seconds):
        return self.received()
    except (EOFError, OSError):
      self.close()
    return []

  def close(self, ) -> None:
    """The 'close' method ends the process, if it is there."""
    pipe, process = self.__shot_pipe__, self.__shot_process__
    self.__shot_pipe__ = None
    self.__shot_process__ = None
    if pipe is not None:
      try:
        pipe.send(None)
      except OSError:
        pass
      pipe.close()
    if process is not None:
      process.join(1.0)
      if process.is_alive():
        process.terminate()
        process.join(1.0)
