"""
The 'cad' package combines the two halves of the structural-CAD model: the
'draw' subpackage of 'dead' drawing primitives (the visual representation of
anchors, members, module lines and dimensions, plus the scene that collects
them, the factory and JSON serialisation) and the 'fea' subpackage that
analyses a structure (elements, the linear solver, the truss assembler).

'CADSettings' (the CAD colour palette and view defaults) lives at this
level, above the primitives it colours rather than among them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from . import draw
from . import fea
from ._cad_settings import CADSettings

__all__ = [
  'draw',
  'fea',
  'CADSettings',
]
