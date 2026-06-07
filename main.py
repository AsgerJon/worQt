"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

from typing import TYPE_CHECKING

from worktoy.utilities import ExceptionInfo, wordWrap, textFmt

from tests import TempDir

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from worQt.app import AbstractApplication
from worQt.cad import CADApp
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  from typing import Optional


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, AbstractApplication]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Entry point for cad larping project. Launches the CAD app and runs the
  Qt event loop until the window is closed (settings load on entry).
  """
  with CADApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


def tester02(*args, ) -> int:
  """
  Testing TempDir
  """
  print(os.listdir(TempDir.directory))
  TempDir.clear()
  print(os.listdir(TempDir.directory))
  return 0


def tester03(*args, ) -> int:
  """
  Testing SampleDocument
  """
  with ExceptionInfo(Exception) as info:
    res = int(420.69)
  if info:
    print(info.report)
  print(res)

  return 0


def tester04(*args, ) -> int:
  """
  Testing tuple subclassing
  """

  class Array(tuple):
    __owning_container__: Optional[object] = None

    def __init__(self, arg, **kwargs) -> None:
      print('trololololo')

  with ExceptionInfo(Exception) as info:
    res = Array((1, 2, 3))
    setattr(res, '__owning_field__', 'breh')
  if info:
    print(info.report)
  else:
    print(res)
    print(res.__owning_container__)

  return 0


def tester05(*args, ) -> int:
  """
  Testing tuple __new__
  """

  with ExceptionInfo(Exception) as info:
    res = tuple(69, )
  if info:
    infoLines = str.split(wordWrap(75, textFmt(info.report)), os.linesep)
    info = str.join('<br><tab>', infoLines)
    print(textFmt(info))
  else:
    print(res)

  return 0


if __name__ == '__main__':
  # yolo(tester04)
  yolo(testMeBro, )
