"""
MachineWorker runs a 'Machine' in a process of its own, in step with the
clock, and streams back a 'Snapshot' a frame.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
import os
import time
from typing import NamedTuple, TYPE_CHECKING

import numpy
from worktoy.desc import Field
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from multiprocessing.connection import Connection

  from ._machine import Machine


class Snapshot(NamedTuple):
  """
  Snapshot is the machine as a frame of it ends: its 'time'; where the
  pusher's face is, 'face'; the coins in play, their middles 'places'
  and turns 'turns' (x y z w), a row each, in mm; and the books: the
  'purse', the coins 'onMachine' and 'inTray', those 'won' and
  'dropped' so far, and the 'total'.
  """

  time: float
  face: float
  places: numpy.ndarray
  turns: numpy.ndarray
  purse: int
  onMachine: int
  inTray: int
  won: int
  dropped: int
  total: int
  filling: bool
  started: bool
  countdown: float
  hits: tuple
  wonNow: int

  def joined(self, later: Snapshot) -> Snapshot:
    """The 'joined' method returns 'later' with what this one heard
    added to it: the hits of both, and the coins won in both."""
    a, b = self.hits, later.hits
    hits = (a[0] + b[0], max(a[1], b[1]), a[2] + b[2], max(a[3], b[3]),
            a[4] + b[4], max(a[5], b[5]))
    return Snapshot(*later[:-2], hits, self.wonNow + later.wonNow)


def snapshotOf(machine: Machine) -> Snapshot:
  """The 'snapshotOf' function returns 'machine' as it is now."""
  world = machine.world
  playing = world.playing
  return Snapshot(machine.time, machine.cabinet.faceAt(machine.time),
                  numpy.array(world.places[playing], numpy.float32),
                  numpy.array(world.turns[playing], numpy.float32),
                  machine.purse, machine.onMachine, machine.inTray,
                  machine.won, machine.dropped, machine.total,
                  machine.filling, machine.started, machine.countdown,
                  machine.hits, machine.wonNow)


def _ran(connection: Connection, seed: int) -> None:
  """Runs a machine, empty, a frame each 1/60 s of the clock, sending
  each frame's 'Snapshot' back over 'connection', the first once a frame
  has been played, so the coin solver is compiled before the window
  shows the machine at all. Asked ('start', seed)
  it starts a game: a new empty machine of 'seed', the house pouring
  the coins in; ('drop', side) drops a coin down that chute; ('pause',
  True) stops the clock, ('pause', False) starts it again; None, or the
  asker gone, ends it. Fallen behind the clock it catches up a few
  frames at a time, then lets the clock go."""
  from ._cabinet import Cabinet
  from ._machine import Machine
  try:
    machine = Machine(Cabinet(), 60, seed)
    machine.frame()
    connection.send(snapshotOf(machine))
    paused, began, played = False, time.perf_counter(), 0
    while True:
      while connection.poll():
        message = connection.recv()
        if message is None:
          return
        kind, value = message
        if kind == 'drop':
          machine.drop(value)
        elif kind == 'pause':
          paused = value
          began, played = time.perf_counter(), 0
        elif kind == 'start':
          machine = Machine(machine.cabinet, 60, value)
          machine.pour()
          began, played = time.perf_counter(), 0
      due = round((time.perf_counter() - began) * 60.0)
      if paused or played >= due:
        time.sleep(0.002)
        continue
      if due - played > 6:
        began, played = time.perf_counter() - played / 60.0, played
      machine.frame()
      played += 1
      connection.send(snapshotOf(machine))
  except (EOFError, OSError, BrokenPipeError):
    return


class MachineWorker(BaseObject):
  """
  MachineWorker runs a coin pusher in a process of its own, in step
  with the clock, so the window showing it never waits: 'start' spawns
  it, nothing of the asker carried over, the machine empty; 'latest'
  returns the newest 'Snapshot' come, never waiting, None if none came
  since; 'begin' starts a game, the house pouring the coins into an
  empty machine; 'drop' and 'pause' ask it to drop a coin, and to stop
  or go on. It ends on 'close' or with the asker; 'running' tells
  whether it is there, 'exitCode' how it ended, and 'cpuSeconds' how
  much processor time it has used: growing, it works; still, it waits
  or is stuck. The first start compiles the coin solver, once
  per computer: that takes a while.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_start_method__ = 'spawn'

  #  Private Variables
  __worker_process__: multiprocessing.Process | None = None
  __worker_pipe__: Connection | None = None
  __worker_seed__: int = 1

  #  Virtual Variables
  running: Field[bool] = Field()
  exitCode: Field[int] = Field()
  cpuSeconds: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the process is there."""
    process = self.__worker_process__
    return False if process is None else process.is_alive()

  @exitCode.GET
  def _getExitCode(self, ) -> int | None:
    """The 'exitCode' getter returns how the process ended, None while it
    runs or before it started."""
    process = self.__worker_process__
    return None if process is None else process.exitcode

  @cpuSeconds.GET
  def _getCpuSeconds(self, ) -> float | None:
    """The 'cpuSeconds' getter returns how much processor time the
    process has used, in s, as Linux counts it in '/proc'; None where
    that cannot be read. Its growth tells working from stuck."""
    process = self.__worker_process__
    if process is None or process.pid is None:
      return None
    try:
      with open('/proc/%d/stat' % process.pid) as stat:
        fields = stat.read().rsplit(')', 1)[1].split()
      ticks = int(fields[11]) + int(fields[12])
      return ticks / os.sysconf('SC_CLK_TCK')
    except (OSError, ValueError, IndexError):
      return None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def start(self, ) -> None:
    """The 'start' method spawns the process running the machine, if it
    is not there."""
    if self.running:
      return
    self.close()
    context = multiprocessing.get_context(self.__fallback_start_method__)
    mine, theirs = context.Pipe()
    process = context.Process(None, _ran, 'coin-pusher',
                              (theirs, self.__worker_seed__))
    process.daemon = True
    process.start()
    theirs.close()
    self.__worker_process__ = process
    self.__worker_pipe__ = mine

  def latest(self, ) -> Snapshot | None:
    """The 'latest' method returns the newest snapshot come since it was
    last asked, the hits of all those come added up, None if none came;
    it never waits."""
    pipe, newest = self.__worker_pipe__, None
    if pipe is None:
      return None
    try:
      while pipe.poll():
        come = pipe.recv()
        newest = come if newest is None else newest.joined(come)
    except (EOFError, OSError):
      self.__worker_pipe__ = None
    return newest

  def drop(self, side: int) -> None:
    """The 'drop' method asks for a coin down the chute on 'side', -1
    left or 1 right."""
    self._sent(('drop', side))

  def pause(self, paused: bool) -> None:
    """The 'pause' method stops the machine, or lets it go on."""
    self._sent(('pause', True if paused else False))

  def begin(self, ) -> None:
    """The 'begin' method starts a game: a new empty machine, the house
    pouring the coins in, the purse full."""
    self.__worker_seed__ += 1
    self._sent(('start', self.__worker_seed__))

  def close(self, ) -> None:
    """The 'close' method ends the process, if it is there."""
    pipe, process = self.__worker_pipe__, self.__worker_process__
    self.__worker_pipe__ = self.__worker_process__ = None
    if pipe is not None:
      try:
        pipe.send(None)
      except (OSError, BrokenPipeError):
        pass
      pipe.close()
    if process is not None:
      process.join(2.0)
      if process.is_alive():
        process.terminate()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _sent(self, message: tuple) -> None:
    """Sends 'message' to the process, if it is there."""
    pipe = self.__worker_pipe__
    if pipe is None:
      return
    try:
      pipe.send(message)
    except (OSError, BrokenPipeError):
      self.__worker_pipe__ = None
