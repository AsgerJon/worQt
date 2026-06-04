"""
The elements of the drawing model. Two families live here:

- Reference geometry that grounds the drawing but is not itself 'real':
  'Node' (a bare coordinate node) and 'ModuleLine' (an infinite
  module/datum line - a 'modullinje' - through an origin at a given angle,
  experienced as a prominent super-gridline).
- Dimensioning: 'Dimension' (linear) and 'AngularDimension' (angular).

Each is a pure 'worktoy' 'BaseObject' defined entirely by coordinates (and,
for a module line, an angle), with no Qt dependency, so the model is built
and tested without a running 'QApplication'. The canvas renders each type;
the items themselves only hold their parameters.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

if TYPE_CHECKING:  # pragma: no cover
  pass


class Node(BaseObject):
  """
  A structural node at '(x, y)' in one of 6 boundary-condition states - the
  cross of {free, roller, pinned} (translation) and {released, locked}
  (rotation, the 'charniere'). Only the SET quantities are stored (the FEA
  induces the rest):

  - free   -> applied force load 'F = (loadX, loadY)'.
  - roller -> locked direction 'theta'; a SET displacement 'rollerSet' along
    theta (settlement) and a SET force 'rollerLoad' along the rolling
    direction (perpendicular to theta).
  - pinned -> SET displacement (settlement) '(dispX, dispY)'; with rotation
    locked too this is the fixed/encastre support.
  - rotation: 'released' (charniere) keeps a SET moment 'loadMoment' (Mf,
    rotation free); 'locked' keeps a SET rotation 'setRot' (xy).

  The drawn symbol is inferred from 'supportType' (+ 'theta' for a roller);
  the analysis is OpenSees' job.
  """

  x = AttriBox[float](0.0)  # node position
  y = AttriBox[float](0.0)  # node position
  supportType = AttriBox[str]('free')  # 'free' | 'roller' | 'pinned'
  released = AttriBox[bool](True)  # charniere: rotation released if True
  theta = AttriBox[float](0.0)  # roller locked direction (degrees)
  loadX = AttriBox[float](0.0)  # F: applied force x (free state), N
  loadY = AttriBox[float](0.0)  # F: applied force y (free state), N
  dispX = AttriBox[float](0.0)  # x: set displacement x (pinned settlement)
  dispY = AttriBox[float](0.0)  # y: set displacement y (pinned settlement)
  rollerSet = AttriBox[float](0.0)  # x: set displacement along theta
  rollerLoad = AttriBox[float](0.0)  # F: set force across theta (along roll)
  setRot = AttriBox[float](0.0)  # xy: set rotation (when locked)
  loadMoment = AttriBox[float](0.0)  # Mf: set moment (when released)

  @overload(float, float)
  def __init__(self, x: float, y: float) -> None:
    self.x = x
    self.y = y

  @overload()
  def __init__(self, ) -> None:
    pass

  def supportKind(self, ) -> str:
    """The display kind: 'free', 'roller', 'pinned', or 'fixed' (a pinned
    support with rotation also locked, the encastre)."""
    if self.supportType == 'pinned' and not self.released:
      return 'fixed'
    return self.supportType

  def cycleSupport(self, ) -> str:
    """Advance the translational support free -> roller -> pinned -> free
    (the quick click gesture); rotation (charniere) is left to the editor."""
    order = {'free': 'roller', 'roller': 'pinned', 'pinned': 'free'}
    self.supportType = order.get(self.supportType, 'free')
    return self.supportKind()

  def __str__(self, ) -> str:
    parts = ['Node(%g, %g)' % (self.x, self.y)]
    if self.supportType == 'roller':
      parts.append('roller@%g' % (self.theta,))
    elif self.supportKind() != 'free':
      parts.append(self.supportKind())  # pinned / fixed
    if not self.released and self.supportKind() != 'fixed':
      parts.append('rot-locked')
    if self.supportType == 'free' and (self.loadX or self.loadY):
      parts.append('F(%g, %g)' % (self.loadX, self.loadY))
    if self.supportType == 'pinned' and (self.dispX or self.dispY):
      parts.append('d(%g, %g)' % (self.dispX, self.dispY))
    if self.supportType == 'roller':
      if self.rollerSet:
        parts.append('d%g' % (self.rollerSet,))
      if self.rollerLoad:
        parts.append('F%g' % (self.rollerLoad,))
    if self.released and self.loadMoment:
      parts.append('Mf(%g)' % (self.loadMoment,))
    if not self.released and self.setRot:
      parts.append('xy(%g)' % (self.setRot,))
    return ' '.join(parts)

  __repr__ = __str__


class ModuleLine(BaseObject):
  """
  An infinite module line (a 'modullinje') through the origin '(x, y)' at
  'angle' degrees: '0' is horizontal, '90' is vertical, anything between is
  a skew grid line. It carries no endpoints - it extends across the whole
  drawing at every zoom - and is drawn as a prominent super-gridline.
  """

  x = AttriBox[float](0.0)
  y = AttriBox[float](0.0)
  angle = AttriBox[float](0.0)  # degrees from the horizontal

  @overload(float, float, float)
  def __init__(self, x: float, y: float, angle: float) -> None:
    self.x = x
    self.y = y
    self.angle = angle

  @overload()
  def __init__(self, ) -> None:
    pass

  def direction(self, ) -> tuple:
    """The unit direction '(dx, dy)' of the line, from its angle."""
    radians = math.radians(self.angle)
    return (math.cos(radians), math.sin(radians))

  def __str__(self, ) -> str:
    return 'Module(%g, %g @ %g deg)' % (self.x, self.y, self.angle)

  __repr__ = __str__


class Member(BaseObject):
  """
  A structural member: a 'real', load-bearing element between two node
  nodes. It holds references to its two 'Node' endpoints, 'nodeA' and
  'nodeB'; its coordinates '(x1, y1)'/'(x2, y2)' read through to them, so
  moving a node moves every member attached to it. Members are the
  geometry the FEA model is built from; they are drawn solid.
  """

  nodeA = AttriBox[Node]()  # the start node
  nodeB = AttriBox[Node]()  # the end node
  x1 = Field()  # read-through to nodeA.x
  y1 = Field()  # read-through to nodeA.y
  x2 = Field()  # read-through to nodeB.x
  y2 = Field()  # read-through to nodeB.y

  @overload(Node, Node)
  def __init__(self, nodeA: Node, nodeB: Node) -> None:
    self.nodeA = nodeA
    self.nodeB = nodeB

  @overload()
  def __init__(self, ) -> None:
    pass

  @x1.GET
  def _getX1(self, **kwargs) -> float:
    return self.nodeA.x

  @y1.GET
  def _getY1(self, **kwargs) -> float:
    return self.nodeA.y

  @x2.GET
  def _getX2(self, **kwargs) -> float:
    return self.nodeB.x

  @y2.GET
  def _getY2(self, **kwargs) -> float:
    return self.nodeB.y

  def length(self, ) -> float:
    """The member length (mm)."""
    return ((self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2) ** 0.5

  def __str__(self, ) -> str:
    return 'Member(%g, %g -> %g, %g)' % (self.x1, self.y1, self.x2, self.y2)

  __repr__ = __str__


class Dimension(BaseObject):
  """A linear dimension annotating the distance between two points."""

  x1 = AttriBox[float](0.0)
  y1 = AttriBox[float](0.0)
  x2 = AttriBox[float](0.0)
  y2 = AttriBox[float](0.0)

  @overload(float, float, float, float)
  def __init__(self, x1: float, y1: float, x2: float, y2: float) -> None:
    self.x1 = x1
    self.y1 = y1
    self.x2 = x2
    self.y2 = y2

  @overload()
  def __init__(self, ) -> None:
    pass

  def length(self, ) -> float:
    """The measured distance between the two points."""
    return ((self.x2 - self.x1) ** 2 + (self.y2 - self.y1) ** 2) ** 0.5

  def __str__(self, ) -> str:
    return 'Dimension(%g mm)' % (self.length(),)

  __repr__ = __str__


class AngularDimension(BaseObject):
  """
  An angular dimension: the angle at 'vertex' between the rays to two arm
  points 'a' and 'b'. Defined by three points (vertex, a, b).
  """

  vx = AttriBox[float](0.0)
  vy = AttriBox[float](0.0)
  ax = AttriBox[float](0.0)
  ay = AttriBox[float](0.0)
  bx = AttriBox[float](0.0)
  by = AttriBox[float](0.0)

  @overload(float, float, float, float, float, float)
  def __init__(self, vx: float, vy: float, ax: float, ay: float,
               bx: float, by: float) -> None:
    self.vx, self.vy = vx, vy
    self.ax, self.ay = ax, ay
    self.bx, self.by = bx, by

  @overload()
  def __init__(self, ) -> None:
    pass

  def angle(self, ) -> float:
    """The included angle in degrees, in '[0, 180]'."""
    toA = math.atan2(self.ay - self.vy, self.ax - self.vx)
    toB = math.atan2(self.by - self.vy, self.bx - self.vx)
    degrees = math.degrees(toB - toA)
    degrees = (degrees + 180.0) % 360.0 - 180.0
    return abs(degrees)

  def __str__(self, ) -> str:
    return 'Angle(%.1f deg)' % (self.angle(),)

  __repr__ = __str__
