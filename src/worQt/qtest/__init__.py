"""
The 'worQt.qtest' package: a test runner safe from hanging. Write tests by
subclassing 'AppTest' (its metaclass collects every 'test*'/'run*' method,
inherited ones included), 'WidgetTest' (an 'AppTest' with gestures for
event-based widget tests) or a plain 'BaseTest', and run the suite with
'python -m worQt.qtest', 'testMeBro()' or 'AppTestSuite().runAll()'. Every
discovered test *class* runs in a child process of its own under a
deadline, so a hang, a segfault or a broken import becomes a reported
status - with the stack of where it happened - instead of a frozen
terminal or a dead suite. Inside the child the standard unittest runner
runs the tests, an 'AppTest' inside a live event loop.

'WidgetTest' loads on first access: it builds on 'worQt.utils', and the
runner itself must not depend on the library it tests.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from ._hook_test import HookTest
from ._space_test import SpaceTest
from ._meta_test import MetaTest
from ._render_mode import RenderMode
from . import primitives

from ._app_test import AppTest
from ._app_test_run import AppTestRun
from ._app_test_suite import AppTestSuite
from ._test_me_bro import testMeBro

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

  from ._widget_test import WidgetTest

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


def __getattr__(name: str) -> Any:
  """
  The module-level '__getattr__' imports 'WidgetTest' the first time it is
  reached, so importing the runner does not import 'worQt.utils'.
  """
  if name == 'WidgetTest':
    return import_module('%s._widget_test' % __name__).WidgetTest
  infoSpec = """module '%s' has no attribute '%s'"""
  raise AttributeError(infoSpec % (__name__, name))
