"""
Running 'python -m worQt.engineering.quests' plays the circuit quests.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import sys

from .gui import QuestsApp


def main() -> int:
  """The 'main' function plays the quests and returns its exit code."""
  with QuestsApp(*sys.argv) as app:
    app.window.show()
  return app.returnCode


if __name__ == '__main__':
  sys.exit(main())
