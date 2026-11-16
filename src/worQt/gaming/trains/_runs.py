"""
The trains' runs for the user's 'yolo' (user, 2026-11-16: "when you
want me to run something they must be functions. Just give me a tuple
of the functions and i will put them in yolo myself"): each takes
nothing and returns an exit code, nought when all went well.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import subprocess
import sys

#  The tests the trains stand on: the sandbox's, the trains', the
#  rail's (the ribbon, its dress, the wheelset, the axlebox, the points).
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
                'tests.test_trains.test_minecart',
                'tests.test_trains.test_train')
RAIL_TESTS = ('tests.test_phys.test_ribbon',
              'tests.test_phys.test_trackdress',
              'tests.test_phys.test_wheelset',
              'tests.test_phys.test_axlebox',
              'tests.test_phys.test_turnout')


def trainsTests() -> int:
  """The 'trainsTests' function runs the sandbox's, the trains' and the
  rail's tests (a few minutes on the CPU), each class in its own child
  process ('latest.log' has the record); nought when all passed."""
  from worQt.qtest import AppTestSuite
  return AppTestSuite().runNames(*SANDBOX_TESTS, *TRAINS_TESTS,
                                 *RAIL_TESTS)


def trainsShow() -> int:
  """The 'trainsShow' function opens the trains: the loop's world, your
  avatar on its island before the points. Click to look round, W A S D
  walk, Shift runs, Space jumps (twice: flies), E boards a cart, works
  the lever looked at or opens the menu, Tab changes the view, Esc lets
  the mouse go. Returns the window's exit code once it closes."""
  from ._trainsapp import TrainsApp
  with TrainsApp(*sys.argv) as app:
    app.window.resize(1920, 1080)
    app.window.show()
  return app.returnCode


def trainsShots() -> int:
  """The 'trainsShots' function renders the loop's world with the GPU to
  'previews/render-<view>.png' ('previews/render_sandbox.py'), in a
  process of its own, and returns its exit code."""
  root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
  env = dict(os.environ)
  env['PYTHONPATH'] = os.path.join(root, 'src')
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  script = os.path.join(root, 'previews', 'render_sandbox.py')
  return subprocess.run([sys.executable, script], env=env).returncode
