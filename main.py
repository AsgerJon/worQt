"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic
from worktoy.utilities import maybe

from worQt.qtest import AppTestSuite

ic.configureOutput(includeContext=True)

from worQt.app import AbstractApplication, App, JsonApp, DrawApp
from yolo import yolo, runTests


def tester00(*args, ) -> int:
  """Hello World!"""
  stuff = ['hello world!', os, sys, frozenset, runTests, AbstractApplication]
  for item in stuff:
    print(item)
  return 0


def tester01(*args, ) -> int:
  """
  Launch the generic worQt JSON editor seeded with random sample data.
  """
  with DrawApp(*sys.argv) as app:
    app.window.show()
  return 0


def tester02(*args, ) -> int:
  """
  Testing the multiprocessing bullshit
  """
  import multiprocessing
  currentContext = multiprocessing.get_context()
  print(currentContext.get_start_method())  # prints: 'forkserver'
  return 0


def tester03(*args, ) -> int:
  """
  testing some importlib stuff
  """

  from importlib.machinery import ModuleSpec

  for item in dir(ModuleSpec):
    print(item)
  return 0


def tester04(*args, ) -> int:
  """
  Testing dir shit
  """
  here: str = os.path.abspath(__file__)
  print(here)
  print(os.path.dirname(here))
  there = os.path.dirname(here)
  print(os.path.dirname(there))

  return 0


def tester05(*args, ) -> int:
  """
  Testing the AppTestSuite.runAll
  """
  try:
    res = AppTestSuite().runAll()
  except Exception as exception:
    print(exception)
    return 1
  return maybe(res, 0)


def tester06(*args, ) -> int:
  """
  Launch the worQt coordinate-driven vector drawing app, seeded with a few
  demo items. Scroll to zoom; add new items by coordinates in the panel.
  """
  with DrawApp(*sys.argv) as app:
    app.window.show()
    #  Seed one of each kind through the user-facing flow: pick the tool
    #  (which prefills its default coordinates) and click Add.
    for kind in ('Point', 'Line', 'Region'):
      app.window._selectTool(kind)
      app.window.newItemTool.addButton.click()
    app.window._selectTool('navigate')  # leave the app ready to navigate
  return 0


if __name__ == '__main__':
  yolo(tester05, tester06, )
