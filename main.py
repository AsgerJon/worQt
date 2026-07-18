"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

from moreworktoy.utilities import errorFmt
from worQt.qtest import testMeBro

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

ic.configureOutput(includeContext=True)

from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  from typing import Never


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, ]
  for item in stuff:
    print(item)
  return 0


def tester01() -> int:
  """
  Testing errorFmt
  """

  class _Breh(BaseObject):
    @overload(float, float, )
    def __init__(self, *args) -> None:
      pass

    @overload(float, float, float, )
    def __init__(self, *args) -> None:
      pass

  def never() -> Never:
    urmom = _Breh('69, 420')

  def gonna() -> None:
    never()

  def give() -> None:
    gonna()

  def you() -> None:
    give()

  def up() -> None:
    try:
      you()
    except Exception as e:
      print(errorFmt(e))

  up()
  return 0


def runClickDemo(*args) -> int:
  """
  Launch the click-button demo app from the 'click_demo' package.
  """
  from click_demo import ClickDemoApp
  with ClickDemoApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  yolo(runClickDemo, )
