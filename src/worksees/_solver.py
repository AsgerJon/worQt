"""
Solver solves models with OpenSees, in a process of its own.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.mcls import BaseObject

from ._job import runJob
from ._result import Result
from ._solver_error import SolverError
from ._worker import Worker

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Self

  from ._model import Model


class Solver(BaseObject):
  """
  Solver solves 'Model's with OpenSees, in a process of its own, its
  'Worker': the process starts on the first 'solve', is kept for those
  after it, each starting from an empty OpenSees, and ends on 'close' or
  with the 'with' block the solver is used in; 'running' tells whether
  it is there.

  'solve' analyses a model linearly, its loads applied in full in one
  step, and returns its 'Result', the elements asked each of the
  'queries' OpenSees answers: a word, such as 'stresses' or 'force', or
  a tuple of words and numbers, such as ('section', 1, 'deformation').
  A model OpenSees refuses raises 'SolverError', naming the command and
  holding what OpenSees said; a process OpenSees ends raises
  'SolverDied', and the next model starts a new one.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Public Variables
  worker = AttriBox[Worker]()

  #  Virtual Variables
  running: Field[bool] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @running.GET
  def _getRunning(self, ) -> bool:
    """The 'running' getter tells whether the solver's process is
    there."""
    return self.worker.running

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __enter__(self, ) -> Self:
    return self

  def __exit__(self, _, exception, __) -> None:
    self.close()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def solve(self, model: Model, *queries: str | tuple) -> Result:
    """The 'solve' method analyses 'model' linearly and returns its
    'Result', the elements asked each of the 'queries'."""
    outcome = self.worker.call(runJob, model.commands(), queries)
    if outcome[0] == 'refused':
      raise SolverError(outcome[1], outcome[2])
    _, frame, said = outcome
    return Result(*frame, queries, said)

  def close(self, ) -> None:
    """The 'close' method ends the solver's process, if it is there."""
    self.worker.close()
