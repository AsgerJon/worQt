"""
Entry point for the 'worQt.qtest' runner.

With no arguments ('python -m worQt.qtest') it runs the whole suite through
'AppTestSuite.runAll' and exits with the number of failing classes.

With one or more dotted module names ('python -m worQt.qtest <name> ...') it
acts as the per-class child process: it resolves each name to its test class
through 'AppTestSuite.getNamed' and runs it, exactly one class per process,
the exit code reporting the outcome:

  0  a test class ran and returned normally
  1  none of the given names matched a discovered test module
  2  a name matched but the suite is malformed (lookup/structural error)
  3  a test class ran and failed (it raised)
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from worktoy.waitaminute import SubclassException

from . import AppTestSuite


def main(name: str) -> None:
  """
  Resolves 'name' to its test class and runs it. Propagates 'ImportError'
  when no discovered module matches 'name', and whatever 'runTest' raises
  when the test itself fails.
  """
  AppTestSuite.getNamed(name).runTest()


if __name__ == '__main__':
  names = sys.argv[1:]
  if not names:  # no name given: run the whole suite
    sys.exit(AppTestSuite().runAll())
  for arg in names:
    try:
      main(arg)
    except ImportError:
      continue  # 'arg' is not a discovered test module, try the next
    except (SubclassException, RuntimeError) as structuralError:
      sys.exit(2)  # matched, but the suite is malformed
    except Exception as testFailure:
      sys.exit(3)  # the test ran and failed
    else:
      sys.exit(0)  # the test ran and passed
  sys.exit(1)  # nothing matched any discovered test module
