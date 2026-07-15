"""
The 'worQt.qtest' package: a test runner safe from hanging. Write tests by
subclassing 'AppTest' (its metaclass collects every 'test*'/'run*' method)
and run the suite with 'testMeBro()', 'AppTestSuite().runAll()', or
'python -m worQt.qtest'. Each discovered test *class* runs on its own: an
'AppTest' is isolated in a child process under a deadline, so a hang or
segfault becomes a reported status instead of a frozen terminal, while a
plain 'BaseTest'/'TestCase' runs in-process. A failure prints its traceback.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._hook_test import HookTest
from ._space_test import SpaceTest
from ._meta_test import MetaTest
from ._render_mode import RenderMode
from . import primitives

from ._app_test import AppTest
from ._app_test_run import AppTestRun
from ._app_test_suite import AppTestSuite
from ._widget_test import WidgetTest
from ._test_me_bro import testMeBro

__all__ = (
  'HookTest',
  'SpaceTest',
  'MetaTest',
  'RenderMode',
  'primitives',
  'AppTest',
  'AppTestRun',
  'AppTestSuite',
  'WidgetTest',
  'testMeBro',
)
