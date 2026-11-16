"""
The games' shows run in a process of their own inside gamescope (user,
2026-11-16: "the fucking mouse won't stay in the window. Like t he
fukcing thing we did with gamescope before"): the trains' and the
space's alike.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import shutil
import subprocess
import sys

#  gamescope's options for the shows: its Wayland backend (a window on
#  the desktop) as large as the window inside it, the window filling
#  it.
GAMESCOPE = ('--backend', 'wayland', '-w', '1920', '-h', '1080', '-W',
             '1920', '-H', '1080', '--force-windows-fullscreen')


def scopedModule(module: str, *args: str) -> int:
  """Runs 'python -m <module> <args>' in a process of its own, 'src' on
  its path, and returns its exit code. On a Wayland desktop it runs
  inside gamescope ('GAMESCOPE': a small compositor of its own, seen in
  a window on the desktop; click into it): Wayland lets no program move
  or hold the pointer, but gamescope's own X server lets the game put it
  back in the middle, and while the game hides it (looking round)
  gamescope locks the desktop's pointer to its window; shown again (a
  menu, Esc) it is free to leave. Without gamescope there it says so
  and opens straight on the desktop, where the pointer can leave the
  window."""
  root = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))
  env = dict(os.environ)
  env['PYTHONPATH'] = os.path.join(root, 'src')
  env['PYTHONDONTWRITEBYTECODE'] = '1'
  command = [sys.executable, '-m', module, *args]
  scope = shutil.which('gamescope')
  if env.get('WAYLAND_DISPLAY') and scope is None:
    print('[%s] no gamescope found: the window opens straight on the '
          'Wayland desktop, where the pointer can leave it' % module,
          flush=True)
  elif env.get('WAYLAND_DISPLAY'):
    env['QT_QPA_PLATFORM'] = 'xcb'
    command = [scope, *GAMESCOPE, '--'] + command
  return subprocess.run(command, env=env).returncode
