"""
Builds drawing elements from a kind name and coordinates. 'parseNumbers' is
lenient about separators (commas and/or whitespace); 'itemFromCoords'
enforces the per-kind arity from a flat number string; 'buildItem' builds
from the '(x, y)' vertices the vertex editor produces; 'describeItem' is its
inverse, used when loading an item back into the editor or to JSON.

A module line is stored as origin '(x, y)' plus an 'angle'. From flat
numbers it is 'x, y, angle'; from vertices it is two points - the origin and
a point the line passes through - and the angle is derived from them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from ._items import (
  AnchorPoint,
  ModuleLine,
  Member,
  Dimension,
  AngularDimension,
)

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any

KINDS = ('Anchor', 'Module', 'Member', 'Dimension', 'Angle')

HINTS = {
  'Anchor': 'x, y',
  'Module': 'x, y, angle',
  'Member': 'drag between two anchors',
  'Dimension': 'x1, y1, x2, y2',
  'Angle': 'vx, vy, ax, ay, bx, by',
}


def parseNumbers(text: str) -> list:
  """
  Parse 'text' into a list of floats, splitting on commas and whitespace.
  Raises 'ValueError' if any token is not a number.
  """
  tokens = text.replace(',', ' ').split()
  return [float(token) for token in tokens]


def itemFromCoords(kind: str, text: str) -> Any:
  """
  Build the item named by 'kind' from the coordinates in 'text'. Raises
  'ValueError' on an unknown kind or a wrong number of coordinates.
  """
  nums = parseNumbers(text)
  if kind == 'Anchor':
    if len(nums) != 2:
      raise ValueError('Anchor needs 2 numbers: x, y')
    return AnchorPoint(nums[0], nums[1])
  if kind == 'Module':
    if len(nums) != 3:
      raise ValueError('Module needs 3 numbers: x, y, angle')
    return ModuleLine(nums[0], nums[1], nums[2])
  if kind == 'Member':
    raise ValueError('Members connect two anchors, not raw coordinates')
  if kind == 'Dimension':
    if len(nums) != 4:
      raise ValueError('Dimension needs 4 numbers: x1, y1, x2, y2')
    return Dimension(nums[0], nums[1], nums[2], nums[3])
  if kind == 'Angle':
    if len(nums) != 6:
      raise ValueError('Angle needs 6 numbers: vx, vy, ax, ay, bx, by')
    return AngularDimension(*nums)
  raise ValueError('Unknown item kind: %r' % (kind,))


def describeItem(item: Any) -> tuple:
  """
  Return '(kind, vertices)' for an existing item: its kind name and its
  coordinates as a list of '(x, y)' pairs. Inverse of 'buildItem'. A module
  line reports its origin and a point one unit along it (encoding the angle).
  """
  if isinstance(item, AnchorPoint):
    return ('Anchor', [(item.x, item.y)])
  if isinstance(item, ModuleLine):
    dx, dy = item.direction()
    return ('Module', [(item.x, item.y), (item.x + dx, item.y + dy)])
  if isinstance(item, Member):
    return ('Member', [(item.x1, item.y1), (item.x2, item.y2)])
  if isinstance(item, Dimension):
    return ('Dimension', [(item.x1, item.y1), (item.x2, item.y2)])
  if isinstance(item, AngularDimension):
    return ('Angle', [(item.vx, item.vy), (item.ax, item.ay),
                      (item.bx, item.by)])
  raise ValueError('Unknown item: %r' % (item,))


def itemAttrs(item: Any) -> dict:
  """
  The non-geometric attributes to persist for 'item' beyond its vertices -
  currently an anchor's support fixities. Returns an empty dict when there is
  nothing extra to store, so the saved form stays minimal.
  """
  if isinstance(item, AnchorPoint):
    attrs = {}
    if item.fixX:
      attrs['fixX'] = True
    if item.fixY:
      attrs['fixY'] = True
    if item.loadX:
      attrs['loadX'] = item.loadX
    if item.loadY:
      attrs['loadY'] = item.loadY
    if item.dispX:
      attrs['dispX'] = item.dispX
    if item.dispY:
      attrs['dispY'] = item.dispY
    return attrs
  return {}


def applyAttrs(item: Any, attrs: dict) -> None:
  """Apply the persisted non-geometric attributes onto 'item'."""
  if isinstance(item, AnchorPoint):
    item.fixX = True if attrs.get('fixX') else False
    item.fixY = True if attrs.get('fixY') else False
    item.loadX = float(attrs.get('loadX', 0.0))
    item.loadY = float(attrs.get('loadY', 0.0))
    item.dispX = float(attrs.get('dispX', 0.0))
    item.dispY = float(attrs.get('dispY', 0.0))


def buildItem(kind: str, vertices: list) -> Any:
  """
  Build the item named by 'kind' from a list of '(x, y)' vertex pairs (as
  produced by the vertex editor). Raises 'ValueError' on an unknown kind or
  the wrong number of vertices. A module line takes two vertices - origin and
  a point it passes through - and derives its angle from them.
  """
  if kind == 'Anchor':
    if len(vertices) != 1:
      raise ValueError('Anchor needs 1 vertex')
    x, y = vertices[0]
    return AnchorPoint(float(x), float(y))
  if kind == 'Module':
    if len(vertices) != 2:
      raise ValueError('Module needs 2 vertices: origin, through-point')
    (ox, oy), (px, py) = vertices
    angle = math.degrees(math.atan2(float(py) - float(oy),
                                    float(px) - float(ox)))
    return ModuleLine(float(ox), float(oy), float(angle))
  if kind == 'Member':
    raise ValueError('Members reference two anchors; build via Member(a, b)')
  if kind == 'Dimension':
    if len(vertices) != 2:
      raise ValueError('Dimension needs 2 vertices')
    (x1, y1), (x2, y2) = vertices
    return Dimension(float(x1), float(y1), float(x2), float(y2))
  if kind == 'Angle':
    if len(vertices) != 3:
      raise ValueError('Angle needs 3 vertices: vertex, arm, arm')
    (vx, vy), (ax, ay), (bx, by) = vertices
    return AngularDimension(float(vx), float(vy), float(ax), float(ay),
                            float(bx), float(by))
  raise ValueError('Unknown item kind: %r' % (kind,))
