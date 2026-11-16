"""
The 'worQt.gaming.trains' package is the trains on the sandbox (user,
2026-11-16: "lets' subclass over into our train package"), each piece a
subclass of the sandbox's concepts:
- 'LoopWorld': the void with the loop de loop, its platforms and the
  island by its start (user: "The world should be void with loop the
  loop and some platforms").
- 'Minecart': a Vehicle, an open steel tub on two real wheelsets in
  axleboxes (user: "let's get a 'minecart' but fr on that track").
- 'TrainsApp': the sandbox opened on the loop's world.
Still to come: FourthPeep levers.
Run it with 'python -m worQt.gaming.trains'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._minecart import Minecart
from ._loopworld import LoopWorld

__all__ = (
  'Minecart',
  'LoopWorld',
)
