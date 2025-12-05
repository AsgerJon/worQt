"""
The 'worQt.math.images' package provides image related tensor utilities.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import functional
from . import conversions
from ._base_raster import BaseRaster
from ._base_unary import BaseUnary
from ._base_binary import BaseBinary
from . import dyn_range

from ._operator_procedure import OperatorProcedure
from ._test_op import TestOp
from ._base_image import BaseImage
from ._op_image import OpImage
from ._effect_procedure import EffectProcedure
from ._edge_detection import EdgeDetection

__all__ = [
    'functional',
    'OperatorProcedure',
    'TestOp',
    'BaseImage',
    'OpImage',
    'EffectProcedure',
    'EdgeDetection',
]
