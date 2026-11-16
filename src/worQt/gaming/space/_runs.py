"""
The space's runs for the user's 'yolo' (user, 2026-11-16: "when you
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

from worQt.gaming._gamescope import scopedModule

#  The tests the space stands on.
SPACE_TESTS = ('tests.test_space.test_conic',
               'tests.test_space.test_heavenlybody',
               'tests.test_space.test_solarsystem',
               'tests.test_space.test_timekeeper',
               'tests.test_space.test_flight',
               'tests.test_space.test_autopilot')


def spaceTests() -> int:
  """The 'spaceTests' function runs the space's tests (a minute or so on
  the CPU), each class in its own child process ('latest.log' has the
  record); nought when all passed."""
  from worQt.qtest import AppTestSuite
  return AppTestSuite().runNames(*SPACE_TESTS)


def spaceShow() -> int:
  """The 'spaceShow' function opens the space window inside gamescope
  (the mouse kept in the window): the creative rocket on Terra's pad,
  the solar system as it stands today. Shift opens the throttle, Z at
  once; T holds the turn; A D, W S, Q E steer; M the map; , and . warp
  (above the air, the engine shut). Returns the window's exit code once
  it closes."""
  return scopedModule('worQt.gaming.space')


def mainSpace() -> int:
  """The 'mainSpace' function demonstrates the space as main.py does a
  show (user, 2026-11-14: "we do tests, lots of tests, before we start
  the show"): the space's tests first, said how they went, then the
  space window. Returns nought when the tests passed and the window
  closed cleanly."""
  tested = spaceTests()
  print('[mainSpace] the tests %s; opening the space window' % (
    'passed' if tested == 0 else 'FAILED (see latest.log)'), flush=True)
  shown = spaceShow()
  return tested or shown


def spaceShots() -> int:
  """The 'spaceShots' function renders the space window with the GPU to
  'previews/render-space-<view>.png' ('previews/render_space.py'), in a
  process of its own, and returns its exit code."""
  root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
  env = dict(os.environ)
  env['PYTHONPATH'] = os.path.join(root, 'src')
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  script = os.path.join(root, 'previews', 'render_space.py')
  return subprocess.run([sys.executable, script], env=env).returncode
