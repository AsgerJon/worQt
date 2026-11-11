"""
SolverError is raised when OpenSees refuses a model; SolverDied when the
process OpenSees runs in ends before it is done.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations


class SolverError(Exception):
  """
  SolverError is raised when OpenSees refuses a model: 'command' is the
  call it refused, a command and its arguments, and 'said' is what
  OpenSees said, its own warnings naming what is wrong.
  """

  command: tuple
  said: str

  def __init__(self, command: tuple, said: str) -> None:
    self.command = command
    self.said = said
    Exception.__init__(self, command, said)

  def __str__(self, ) -> str:
    words = ' '.join(str(arg) for arg in self.command)
    infoSpec = """OpenSees refused '%s': %s"""
    return infoSpec % (words, self.said.strip() or 'it said nothing')


class SolverDied(SolverError):
  """
  SolverDied is raised when the process OpenSees runs in ends before it
  is done, as OpenSees ends it on some failures; the 'Solver' starts a
  new one for the next model.
  """

  def __init__(self, ) -> None:
    SolverError.__init__(self, ('solve',), '')

  def __str__(self, ) -> str:
    return 'the process OpenSees ran in ended before it was done'
