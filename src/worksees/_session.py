"""
Session keeps a model in OpenSees and pushes it step by step, the way
an actuator pushes a specimen.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import itertools
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._job import advanceSession, openSession
from ._model import Model
from ._result import Result
from ._solver_error import SolverError
from ._worker import Worker

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self

#  What tells the sessions apart in the process they share
_TOKENS = itertools.count(1)


class Session(BaseObject):
  """
  Session keeps a 'Model' in OpenSees, in a process of its own, its
  'Worker', and pushes it step by step under displacement control, the
  way an actuator pushes a specimen: each step moves the 'freedom' of
  the 'node' pushed by an increment, and OpenSees finds the factor its
  loads must be applied by to hold it there, 'loadFactor' of each
  step's 'Result'. The loads are thus the actuator's force per unit of
  that factor. Each step is tried by Newton's method, then by those
  that cope where it does not, then split in four, and those again,
  three times over, for 45 seconds at most.

  'advance' pushes 'count' steps of 'increment' each and returns a
  'Result' to each step made, the elements asked each of the 'queries';
  'submit' starts the same and returns at once, for 'collect' to return
  the results when they are done, 'ready' telling when. A step that
  cannot be made ends it early, and 'stuck' is True from then on, the
  model as it was after the last step made. 'steps' counts the steps
  made. The model is built when the session is made, a command
  OpenSees refuses raising 'SolverError'; 'close' or the end of its
  'with' block ends its process.

  A session given a 'Worker' shares that worker's process, which keeps
  going after the session is closed, so a process need not be started
  for each; the process holds one session at a time, and a session
  opened after another there leaves that one 'SolverError' on
  'advance'.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __session_model__: Model | None = None
  __session_push__: tuple[int, int] | None = None
  __session_steps__: int = 0
  __session_worker__: Worker | None = None
  __session_token__: int = 0

  #  Public Variables
  ownsWorker = AttriBox[bool](True)
  stuck = AttriBox[bool](False)

  #  Virtual Variables
  model: Field[Model] = Field()
  node: Field[int] = Field()
  freedom: Field[int] = Field()
  steps: Field[int] = Field()
  worker: Field[Worker] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @model.GET
  def _getModel(self, ) -> Model:
    """The 'model' getter returns the model pushed."""
    if self.__session_model__ is None:
      raise MissingVariable(self, '__session_model__', Model)
    return self.__session_model__

  def _getPush(self, ) -> tuple[int, int]:
    if self.__session_push__ is None:
      raise MissingVariable(self, '__session_push__', tuple)
    return self.__session_push__

  @node.GET
  def _getNode(self, ) -> int:
    """The 'node' getter returns the number of the node pushed."""
    return self._getPush()[0]

  @freedom.GET
  def _getFreedom(self, ) -> int:
    """The 'freedom' getter returns the freedom of the node pushed,
    counted from 1."""
    return self._getPush()[1]

  @worker.GET
  def _getWorker(self, ) -> Worker:
    """The 'worker' getter returns the worker the session runs in, its
    own unless given one."""
    if self.__session_worker__ is None:
      self.__session_worker__ = Worker()
    return self.__session_worker__

  @steps.GET
  def _getSteps(self, ) -> int:
    """The 'steps' getter returns how many steps have been made."""
    return self.__session_steps__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self, ) -> Self:
    return self

  def __exit__(self, _, exception, __) -> None:
    self.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Model, int, int)
  def __init__(self, model: Model, node: int, freedom: int) -> None:
    if not 1 <= node <= model.nodeCount:
      raise ValueError('there is no node %d to push' % node)
    if not 1 <= freedom <= model.freedoms:
      raise ValueError('a node has no freedom %d' % freedom)
    self.__session_model__ = model
    self.__session_push__ = (node, freedom)
    self.__session_token__ = next(_TOKENS)
    outcome = self.worker.call(
      openSession, model.commands(), node,
      freedom, self.__session_token__
      )
    if outcome[0] == 'refused':
      self.close()
      raise SolverError(outcome[1], outcome[2])

  @overload(Model, int, int, Worker)
  def __init__(
      self, model: Model, node: int, freedom: int,
      worker: Worker
      ) -> None:
    self.__session_worker__ = worker
    self.ownsWorker = False
    self.__init__(model, node, freedom)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advance(
      self, increment: float, count: int,
      *queries: str | tuple
      ) -> tuple[Result, ...]:
    """The 'advance' method pushes 'count' steps of 'increment' each and
    returns a 'Result' to each step made."""
    return self.collect(self.submit(increment, count, *queries))

  def submit(
      self, increment: float, count: int,
      *queries: str | tuple
      ) -> tuple:
    """The 'submit' method starts pushing 'count' steps of 'increment'
    each and returns at once, with what to 'collect' when it is done:
    the asker goes on meanwhile, as a window must."""
    if self.stuck:
      return None, queries
    future = self.worker.submit(
      advanceSession, self.__session_token__,
      float(increment), int(count), queries
      )
    return future, queries

  @staticmethod
  def ready(pending: tuple) -> bool:
    """The 'ready' method tells whether the push 'pending' is done, so
    'collect' will not wait for it."""
    future, _ = pending
    return True if future is None or future.done() else False

  def collect(self, pending: tuple) -> tuple[Result, ...]:
    """The 'collect' method returns a 'Result' to each step made of the
    push 'pending' is, as 'submit' returned it, waiting for it if it is
    not done."""
    future, queries = pending
    if future is None:
      return ()
    outcome = self.worker.collect(future)
    if outcome[0] == 'refused':
      raise SolverError(outcome[1], outcome[2])
    _, frames, stuck, said = outcome
    self.__session_steps__ += len(frames)
    self.stuck = stuck
    return (*[Result(*frame, queries, said) for frame in frames],)

  def close(self, ) -> None:
    """The 'close' method ends the session's process, unless it shares
    a worker given it."""
    if self.ownsWorker:
      self.worker.close()
