"""
runTests runs a whole test tree through a 'FullRunner'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from ._full_runner import FullRunner

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional, TypeAlias

  MaybeStr: TypeAlias = Optional[str]


def runTests(testRoot: MaybeStr = None, pattern: MaybeStr = None) -> int:
  """
  Runs every discovered test class through a 'FullRunner', prints the
  report, and returns a process-style code: 0 when every class passed and
  1 otherwise. With no 'testRoot' the run targets the 'tests' folder
  beside the '__main__' module, so a project entry point can call this
  with no arguments.

  Parameters
  ----------
  testRoot : str, optional
      The folder searched for test classes. Defaults to the 'tests'
      directory beside the '__main__' module.
  pattern : str, optional
      The glob matching the test files under the root. Defaults to
      'test_*.py'.

  Returns
  -------
  int
      0 when every class succeeded, 1 otherwise.
  """
  if testRoot is None:
    runner = FullRunner()
  elif pattern is None:
    runner = FullRunner(testRoot)
  else:
    runner = FullRunner(testRoot, pattern)
  runner.run()
  print(runner.report())
  return 0 if runner.success else 1
