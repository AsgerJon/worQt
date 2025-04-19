"""The 'worQt.tools.geometry' module provides the custom geometry tools for
the 'worQt' library. Most classes defined here has a corresponding
counterpart in the Qt library. """
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from ._abstract_geometry import AbstractGeometry

from ._plane import Plane
from ._point import Point
from ._vector import Vector
from ._size import Size
from ._region import Region
from ._abstract_map import AbstractMap
from ._region_map import RegionMap
from ._move_map import MoveMap
from ._scale_map import ScaleMap
from ._rotate_map import RotateMap
from ._rotate_point_map import RotatePointMap
