"""
The 'draw' subpackage holds the geometry model for the drawing app:
coordinate-defined items, the scene that collects them, and the factory
that builds items from typed-in coordinates. All pure 'worktoy' models
with no Qt dependency.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._items import (
  AnchorPoint,
  ModuleLine,
  Member,
  Dimension,
  AngularDimension,
)
from ._scene import CADScene
from ._factory import (
  KINDS,
  HINTS,
  parseNumbers,
  itemFromCoords,
  buildItem,
  describeItem,
  itemAttrs,
  applyAttrs,
)
from ._serialize import (
  sceneToData,
  sceneFromData,
  sceneToJson,
  sceneFromJson,
  saveScene,
  loadScene,
)

__all__ = (
  'AnchorPoint',
  'ModuleLine',
  'Member',
  'Dimension',
  'AngularDimension',
  'CADScene',
  'KINDS',
  'HINTS',
  'parseNumbers',
  'itemFromCoords',
  'buildItem',
  'describeItem',
  'itemAttrs',
  'applyAttrs',
  'sceneToData',
  'sceneFromData',
  'sceneToJson',
  'sceneFromJson',
  'saveScene',
  'loadScene',
)
