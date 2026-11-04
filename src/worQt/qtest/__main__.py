"""
Entry point for the 'worQt.qtest' runner.

  python -m worQt.qtest
      Runs every discovered test module, each in its own child process,
      and exits 0 when all of them passed, 1 otherwise.

  python -m worQt.qtest <module> [<module> ...]
      Runs just the named test modules (dotted names, such as
      'tests.test_utils.test_color') the same way, plain and 'AppTest'
      classes alike.

  python -m worQt.qtest --child <module>
      Internal: the child process that 'AppTestRun' starts for one module.
      Its exit code is decoded by the suite: 0 passed, 2 the class could
      not be loaded or run, 3 a test failed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from . import AppTestRun, AppTestSuite

if __name__ == '__main__':
  args = sys.argv[1:]
  if args[:1] == ['--child']:
    sys.exit(AppTestRun.runChild(*args[1:]))
  if args:
    sys.exit(AppTestSuite().runNames(*args))
  sys.exit(AppTestSuite().runAll())
