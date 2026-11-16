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
import shutil
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
                'tests.test_trains.test_train',
                'tests.test_trains.test_locomotive')
RAIL_TESTS = ('tests.test_phys.test_ribbon',
              'tests.test_phys.test_trackdress',
              'tests.test_phys.test_wheelset',
              'tests.test_phys.test_axlebox',
              'tests.test_phys.test_turnout',
              'tests.test_phys.test_crankpin')
#  gamescope's options for the shows: its Wayland backend (a window on
#  the desktop) as large as the window inside it, the window filling
#  it.
GAMESCOPE = ('--backend', 'wayland', '-w', '1920', '-h', '1080', '-W',
             '1920', '-H', '1080', '--force-windows-fullscreen')


def trainsTests() -> int:
  """The 'trainsTests' function runs the sandbox's, the trains' and the
  rail's tests (a few minutes on the CPU), each class in its own child
  process ('latest.log' has the record); nought when all passed."""
  from worQt.qtest import AppTestSuite
  return AppTestSuite().runNames(*SANDBOX_TESTS, *TRAINS_TESTS,
                                 *RAIL_TESTS)


def trainsShow() -> int:
  """The 'trainsShow' function opens the trains ('_scoped': inside
  gamescope, the mouse kept in the window): the loop's world, your
  avatar on its island before the points. Click to look round, W A S D
  walk, Shift runs, Space jumps (twice: flies), E boards a cart, works
  the lever looked at or opens the menu, Tab changes the view, Esc lets
  the mouse go. Returns the window's exit code once it closes."""
  return _scoped()


def mainTrain() -> int:
  """The 'mainTrain' function demonstrates the trains as main.py does a
  show (user, 2026-11-14: "we do tests, lots of tests, before we start
  the show"): the sandbox's, the trains' and the rail's tests first (a
  few minutes on the CPU; 'latest.log' has the record), said how they
  went, then the trains themselves: the train on the siding, the points'
  lever by where you enter. Returns nought when the tests passed and the
  window closed cleanly."""
  tested = trainsTests()
  print('[mainTrain] the tests %s; opening the trains' % (
    'passed' if tested == 0 else 'FAILED (see latest.log)'), flush=True)
  shown = trainsShow()
  return tested or shown


def steamShow() -> int:
  """The 'steamShow' function opens the steam train on its oval
  ('_scoped': inside gamescope, the mouse kept in the window): you on
  the grass by the cab's left side. E boards the engine, then E on a
  lever in the cab: the regulator (steam), the reverser (thrown:
  backward), the brake (the whole train's). Returns the window's exit
  code once it closes."""
  return _scoped('steam')


def mainSteam() -> int:
  """The 'mainSteam' function demonstrates the steam train as 'mainTrain'
  does the loop's: the tests first (a few minutes on the CPU), said how
  they went, then the steam train ('steamShow'). Returns nought when the
  tests passed and the window closed cleanly."""
  tested = trainsTests()
  print('[mainSteam] the tests %s; opening the steam train' % (
    'passed' if tested == 0 else 'FAILED (see latest.log)'), flush=True)
  shown = steamShow()
  return tested or shown


def steamShots() -> int:
  """The 'steamShots' function renders the steam train with the GPU to
  'previews/render-steam-<view>.png' ('previews/render_steam.py'),
  standing and after 20 s under steam, in a process of its own, and
  returns its exit code."""
  return _previewed('render_steam.py')


def trainsShots() -> int:
  """The 'trainsShots' function renders the loop's world with the GPU to
  'previews/render-<view>.png' ('previews/render_sandbox.py'), in a
  process of its own, and returns its exit code."""
  return _previewed('render_sandbox.py')


def _previewed(name: str) -> int:
  """Runs the script 'previews/<name>' in a process of its own, 'src' on
  its path, and returns its exit code."""
  root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
  env = dict(os.environ)
  env['PYTHONPATH'] = os.path.join(root, 'src')
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  script = os.path.join(root, 'previews', name)
  return subprocess.run([sys.executable, script], env=env).returncode


def _scoped(*args: str) -> int:
  """Runs 'python -m worQt.gaming.trains <args>' in a process of its own,
  'src' on its path, and returns its exit code. On a Wayland desktop it
  runs inside gamescope ('GAMESCOPE': a small compositor of its own,
  seen in a window on the desktop; click into it): Wayland lets no
  program move or hold the pointer, but gamescope's own X server lets
  the sandbox put it back in the middle, and while the sandbox hides it
  (looking round) gamescope locks the desktop's pointer to its window;
  shown again (the menu, Esc) it is free to leave. Without gamescope
  there it says so and opens straight on the desktop, where the
  pointer can leave the window."""
  root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))))
  env = dict(os.environ)
  env['PYTHONPATH'] = os.path.join(root, 'src')
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  command = [sys.executable, '-m', 'worQt.gaming.trains', *args]
  scope = shutil.which('gamescope')
  if env.get('WAYLAND_DISPLAY') and scope is None:
    print('[trains] no gamescope found: the window opens straight on the '
          'Wayland desktop, where the pointer can leave it', flush=True)
  elif env.get('WAYLAND_DISPLAY'):
    env['QT_QPA_PLATFORM'] = 'xcb'
    command = [scope, *GAMESCOPE, '--'] + command
  return subprocess.run(command, env=env).returncode
