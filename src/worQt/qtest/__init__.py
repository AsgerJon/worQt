"""
The 'worQt.qtest' package: a test runner safe from hanging. You import a
'Cutest' subclass and pass it to 'runTests'; each test method runs in its
own child process under a deadline, so a hang or crash becomes a reported
status instead of a frozen terminal, and a failure prints its traceback.
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
