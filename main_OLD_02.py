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
#  The test windows main.py runs open without taking the focus (user,
#  2026-11-15: "do something so the window doesn't grab focus pls"):
#  shown unactivated, never focused; the children inherit it. Set it to
#  '0' to have them raised and activated.
os.environ.setdefault('QTEST_NO_FOCUS', '1')

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from yolo import yolo, runTests

SANDBOX_TESTS = ('tests.test_sandbox.test_universe',
                 'tests.test_sandbox.test_world',
                 'tests.test_sandbox.test_avatar',
                 'tests.test_sandbox.test_hotbar',
                 'tests.test_sandbox.test_gravitygun',
                 'tests.test_sandbox.test_item',
                 'tests.test_sandbox.test_gait',
                 'tests.test_sandbox.test_vehicle',
                 'tests.test_sandbox.test_mixer',
                 'tests.test_sandbox.test_skin',
                 'tests.test_sandbox.test_fourthpeep')
TRAINS_TESTS = ('tests.test_trains.test_loopworld',
                'tests.test_trains.test_minecart')
#  The rail's own: the track as a ribbon, drawn along it, the wheelset
#  rolling on it, the axlebox holding it.
RAIL_TESTS = ('tests.test_phys.test_ribbon',
              'tests.test_phys.test_trackdress',
              'tests.test_phys.test_wheelset',
              'tests.test_phys.test_axlebox')


def sandboxTests(*args, ) -> int:
  """Runs 'SANDBOX_TESTS' and 'TRAINS_TESTS' (half a minute or so).
  Returns 0 when all passed, 1 otherwise."""
  return runTests(*SANDBOX_TESTS, *TRAINS_TESTS)


def railTests(*args, ) -> int:
  """Runs 'RAIL_TESTS' (a minute or two). Returns 0 when all passed, 1
  otherwise."""
  return runTests(*RAIL_TESTS)


def trainsShow(*args, ) -> int:
  """Opens the trains (worQt.gaming.trains, on the sandbox): the loop's
  world, your avatar on its island. Click to look round, W A S D walk,
  Shift runs, Space jumps (twice: flies), E items, 1 to 9 the hotbar,
  Esc lets the mouse go. Returns the exit code once its window
  closes."""
  from worQt.gaming.trains._trainsapp import TrainsApp
  with TrainsApp(*sys.argv) as app:
    app.window.resize(1920, 1080)
    app.window.show()
  return app.returnCode


def sandboxShots(*args, ) -> int:
  """Renders the sandbox's loop world with the GPU to
  'previews/render-<view>-<variant>.png', as 'previews/render_sandbox.py'
  does, in a process of its own (it ends itself with os._exit), and
  returns its exit code."""
  import subprocess
  env = dict(os.environ)
  env['PYTHONPATH'] = src
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  path = os.path.join(here, 'previews', 'render_sandbox.py')
  return subprocess.run([sys.executable, path], env=env).returncode


if __name__ == '__main__':
  # yolo(sandboxTests, railTests, )
  # yolo(sandboxShots, )
  yolo(trainsShow, )
