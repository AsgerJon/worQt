"""
Keglebillard is worQt's billiard room as an app of its own (user,
2026-11-16: "My step father plays the keglebillard and likes it. He has
a reasonably new macbook from 2024 can we make him something that just
lets him play the billiards part of worQt? Like a pack that is self
contained."; "let him have to walk over to the kegler"): it opens the
room, walking, cue in hand, to either table. PyInstaller builds it
('keglebillard.spec'), on GitHub for the Mac
(.github/workflows/keglebillard-mac.yml).

Set 'KEGLEBILLARD_SMOKE' to some seconds and it tries itself instead:
compiles the billiards' Warp kernels (saying '[smoke] kernels ready'),
opens the room, closes it after those seconds, a picture of its window
saved first to 'KEGLEBILLARD_SHOT' if that is set.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import multiprocessing
import os
import sys
import time


def kernelsReady() -> float:
  """The 'kernelsReady' function loads (compiling the first time) the
  billiards' Warp kernels on the processor and returns how long it
  took, s: the frozen app must carry their sources and Warp's own."""
  import warp as wp

  from worQt.gaming.billiards import _hits_kernels, _kegle_kernels
  began = time.perf_counter()
  wp.init()
  for module in (_hits_kernels, _kegle_kernels):
    wp.load_module(module, device='cpu')
  return time.perf_counter() - began


def shut(app: object) -> None:
  """Saves a picture of the window to 'KEGLEBILLARD_SHOT' (if set) and
  quits 'app'."""
  from PySide6.QtWidgets import QWidget

  shot = os.environ.get('KEGLEBILLARD_SHOT')
  try:
    if shot:
      saved = QWidget.grab(app.window).save(shot)
      print('[smoke] picture %s' % ('saved' if saved else 'NOT saved'),
            flush=True)
  finally:
    app.quit()


def main() -> int:
  """The 'main' function opens the billiard room, walking, its window
  filling the screen ('show' first: it builds the window), and returns
  its exit code once its window closes (tried for 'KEGLEBILLARD_SMOKE'
  seconds when set)."""
  smoke = float(os.environ.get('KEGLEBILLARD_SMOKE', '0') or 0.0)
  if smoke:
    print('[smoke] kernels ready in %.1f s' % kernelsReady(), flush=True)
  from PySide6.QtCore import QTimer

  from worQt.gaming.billiards.gui import BilliardsApp
  with BilliardsApp(*sys.argv) as app:
    app.window.show()
    app.window.showMaximized()
    app.window.enterRoom()
    if smoke:
      QTimer.singleShot(int(1000.0 * smoke), lambda: shut(app))
      print('[smoke] the room is open', flush=True)
  return app.returnCode


if __name__ == '__main__':
  multiprocessing.freeze_support()
  sys.exit(main())
