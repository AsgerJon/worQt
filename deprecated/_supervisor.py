"""
The supervisor. 'runTests' takes a 'Cutest' subclass -- the class object
you imported -- and runs each of its 'test' methods in its own forked
child process under a wall-clock deadline.

A 'fork' child is a copy of this process, so the test class is already in
the child's memory: no re-launch, no re-import, no string names. The
child shares this process's stdout and stderr, so a failing test's
traceback prints to your terminal as it happens. The supervisor holds no
Qt, so it cannot freeze and the fork is safe: its deadline always fires
and its 'SIGKILL' always lands, so a hang becomes 'TIMEOUT' rather than a
frozen terminal.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import faulthandler
import multiprocessing
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
  from typing import Type

  from ._cutest import Cutest

  Result = tuple[str, str]
  Results = tuple[Result, ...]


def _runMethod(testClass: Type[Cutest], method: str, deadline: float) -> None:
  """Runs in the forked child: build the instance and run the one
  method. An exception propagates so the child prints its traceback and
  exits non-zero. The faulthandler dumps the stack if it hangs."""
  faulthandler.dump_traceback_later(deadline * 2, exit=True)
  instance = testClass()
  instance.setUp()
  getattr(instance, method)()
  instance.tearDown()


def runTests(testClass: Type[Cutest], deadline: float = 5.0) -> Results:
  """
  Runs every 'test' method of the given 'Cutest' subclass, each in its
  own forked child, prints a status line per method, and returns the
  '(method, status)' pairs. No test can hang the call: each terminates
  within 'deadline', any failure prints its traceback, a hang is
  'TIMEOUT', a segfault is 'CRASH'.
  """
  fork = multiprocessing.get_context('fork')
  results = []
  for method in dir(testClass):
    if not method.startswith('test'):
      continue
    if not callable(getattr(testClass, method)):
      continue
    proc = fork.Process(target=_runMethod, args=(testClass, method, deadline))
    proc.start()
    proc.join(deadline)
    if proc.is_alive():
      proc.kill()
      proc.join()
      status = 'TIMEOUT'
    elif proc.exitcode and proc.exitcode < 0:
      status = 'CRASH'
    elif proc.exitcode == 0:
      status = 'PASS'
    else:
      status = 'FAIL'
    print('%-8s %s' % (status, method))
    results.append((method, status))
  return (*results,)
