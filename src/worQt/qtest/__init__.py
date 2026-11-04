"""
The 'worQt.qtest' package: a test runner safe from hanging. Write tests by
subclassing 'AppTest' (its metaclass collects every 'test*'/'run*' method,
inherited ones included) or a plain 'BaseTest', and run the suite with
'python -m worQt.qtest', 'testMeBro()' or 'AppTestSuite().runAll()'. Every
discovered test *class* runs in a child process of its own under a
deadline, so a hang, a segfault or a broken import becomes a reported
status - with the stack of where it happened - instead of a frozen
terminal or a dead suite. Inside the child the standard unittest runner
runs the tests, an 'AppTest' inside a live event loop.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._hook_test import HookTest
from ._space_test import SpaceTest
from ._meta_test import MetaTest

from ._app_test import AppTest
from ._app_test_run import AppTestRun
from ._app_test_suite import AppTestSuite
from ._test_me_bro import testMeBro

__all__ = (
  'HookTest',
  'SpaceTest',
  'MetaTest',
  'AppTest',
  'AppTestRun',
  'AppTestSuite',
  'testMeBro',
)
