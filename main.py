"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
from random import randint
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QRect
from worktoy.core.sentinels import ARGS
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.utilities import joinWords, stringList, textFmt

from pycharm_wyd import WYD
from worQt.qtest import testMeBro
from worQt.scratch import ScratchApp, ScratchWindow

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

ic.configureOutput(includeContext=True)

from worQt.app import App
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  pass


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, App]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Entry point for the ScratchApp.
  """
  app = ScratchApp(*args, )
  window = ScratchWindow()
  window.show()
  return app.exec()


class Foo(BaseObject):
  """A simple class for testing purposes."""

  @overload(*ARGS[int])
  def __init__(self, *args: int) -> None:
    print('_' * 40)
    print("""Reached integer constructor""")
    infoSpec: str = """Received the following integers: <br><tab>%s"""
    argStr: str = joinWords(*[str(arg) for arg in args])
    info: str = infoSpec % argStr
    print(textFmt(info))

  @overload(str)
  def __init__(self, arg: str) -> None:
    print('_' * 40)
    print("""Reached string constructor""")
    infoSpec: str = """Received the following string: <br><tab>%s"""
    info: str = infoSpec % arg
    print(textFmt(info))

  @overload.fallback
  def __init__(self, *args: object) -> None:
    print('_' * 40)
    print("""Reached fallback constructor""")
    infoSpec: str = """Received the following objects: <br><tab>%s"""
    argStr: str = str.join(' ', [str(arg) for arg in args])
    info: str = infoSpec % argStr
    print(textFmt(info))

  @overload.finalize
  def __init__(self, *args, **kwargs) -> None:
    print("Initialization complete.")
    print('¨' * 40)


def tester02() -> int:
  foo1: Foo = Foo(69, 420, 1337)
  foo2: Foo = Foo("""Never gonna give you up""")
  foo3: Foo = Foo(*str.split("""Never gonna let you down"""))
  numbers: tuple[int, ...] = (*(randint(0, 255) for _ in range(10)),)
  foos: list[Foo] = [Foo(*numbers[:i], ) for i in range(1, 10)]
  return 0


def tester03() -> int:
  wyd: WYD = WYD()
  print(wyd.a)
  print(wyd.b)
  return 0


def tester04() -> int:
  print(type(QRect).__name__)
  return 0


if __name__ == '__main__':
  yolo(tester04)
  # yolo(testMeBro, tester01)
