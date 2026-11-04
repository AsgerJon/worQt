"""
The 'moreworktoy.utilities' package provides provisional additions to the
'worktoy.utilities' package developed ad hoc during development of the
'worQt' library.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import worktoy.utilities as wu
from worktoy.utilities import *

from ._error_fmt import errorFmt

__more__ = ('errorFmt',)
__all__ = (*wu.__all__, *__more__,)
