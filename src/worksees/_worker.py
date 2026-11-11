"""
Worker is the process OpenSees runs in, started when first asked.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
from concurrent.futures import Future, ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject

from ._job import quietProcess
from ._solver_error import SolverDied

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Callable


class Worker(BaseObject):
  """
  Worker is the process OpenSees runs in: OpenSees keeps a single model
  for its whole process and ends that process on some failures, so it
  never runs in the process asking. The process is spawned, nothing of
  the asker carried over, on the first 'call', which runs a function
  there and returns what it returns, or 'submit', which starts one and
  returns at once, its 'Future' to 'collect' when it is done; it is
  kept for the calls after, and ends on 'close'. 'running' tells
  whether it is there. A process that ends before its call is done
  raises 'SolverDied', and the next call starts a new one.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_start_method__ = 'spawn'

  #  Private Variables
  __worker_pool__: ProcessPoolExecutor | None = None

  #  Virtual Variables
  running: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the process is there."""
    return False if self.__worker_pool__ is None else True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def call(self, function: Callable, *args) -> object:
    """The 'call' method runs 'function' with 'args' in the process and
    returns what it returns."""
    return self.collect(self.submit(function, *args))

  def submit(self, function: Callable, *args) -> Future:
    """The 'submit' method starts 'function' with 'args' in the process
    and returns at once, with the 'Future' of what it returns; the
    asker goes on, and 'collect's it when it is 'done'."""
    try:
      return self._pool().submit(function, *args)
    except BrokenProcessPool:
      self._drop()
      raise SolverDied()

  def collect(self, future: Future) -> object:
    """The 'collect' method returns what the call 'future' stands for
    returned, waiting for it if it is not done."""
    try:
      return future.result()
    except BrokenProcessPool:
      self._drop()
      raise SolverDied()

  def close(self, ) -> None:
    """The 'close' method ends the process, if it is there."""
    if self.__worker_pool__ is not None:
      self.__worker_pool__.shutdown()
    self.__worker_pool__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _pool(self, ) -> ProcessPoolExecutor:
    """The pool of the one process, started on first use."""
    if self.__worker_pool__ is None:
      method = self.__fallback_start_method__
      context = multiprocessing.get_context(method)
      pool = ProcessPoolExecutor(1, context, quietProcess)
      self.__worker_pool__ = pool
    return self.__worker_pool__

  def _drop(self, ) -> None:
    """Lets go of a pool whose process has ended."""
    if self.__worker_pool__ is not None:
      self.__worker_pool__.shutdown(False)
    self.__worker_pool__ = None
