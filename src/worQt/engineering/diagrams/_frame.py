"""
Frame is a plane frame of straight members on its supports under its
loads, in kN and m.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._parts import LineLoad, Member, Node, PointLoad, PointMoment, Support

Load = PointLoad | LineLoad | PointMoment
_DIRECTIONS = ('down', 'right')


class Frame(BaseObject):
  """
  Frame is a plane frame, in kN and m, y up: its 'nodes', where its
  'members' meet, each straight, joined rigidly but where hinged; its
  'supports', each at a node; and its 'loads', point loads, line loads
  and point moments, each somewhere along a member. A beam is a frame of
  members in a line.

  A frame is made only whole: its nodes apart, each member between two
  of them, at most one support a node, each load on its member, each
  line load from a start to an end after it. 'length' and 'direction'
  give a member's length and the unit vector it runs along; 'joined'
  the members at a node. 'indeterminacy' says how many more ways it is
  held than it takes to hold it, nought for a frame statically
  determinate; whether it is held at all, 'Analysis' finds.

  'withNodes', 'withMembers', 'withSupports' and 'withLoads' return it
  with those changed; 'withNode', 'withMember', 'withSupport' and
  'withLoad' with one replaced, a node moved carrying the loads on its
  members along as a share of their lengths; 'withoutNode' without a
  node and the members and support on it, 'withoutMember' without a
  member and its loads, its nodes left, 'withoutSupport' and
  'withoutLoad' without one, the indices after it moved down. Made of
  nothing, it is the standard frame: a portal 6 m wide and 4 m high,
  fixed at its left foot, pinned at its right, 10 kN/m on its beam and
  15 kN of wind at its top left corner.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_stiffness__ = (1e4, 1e6)  # EI kNm², EA kN
  __fallback_nodes__ = (Node(0.0, 0.0), Node(0.0, 4.0), Node(6.0, 4.0),
                        Node(6.0, 0.0))
  __fallback_members__ = (
    Member(0, 1, 1e4, 1e6, False, False),
    Member(1, 2, 1e4, 1e6, False, False),
    Member(2, 3, 1e4, 1e6, False, False),
  )
  __fallback_supports__ = (Support(0, 'fixed'), Support(3, 'pin'))
  __fallback_loads__ = (
    LineLoad(1, 0.0, 6.0, 10.0, 10.0, 'down'),
    PointLoad(0, 4.0, 0.0, 15.0),
  )

  #  Private Variables
  __frame_parts__: tuple | None = None

  #  Virtual Variables
  nodes: Field[tuple[Node, ...]] = Field()
  members: Field[tuple[Member, ...]] = Field()
  supports: Field[tuple[Support, ...]] = Field()
  loads: Field[tuple[Load, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple:
    if self.__frame_parts__ is None:
      raise MissingVariable(self, '__frame_parts__', tuple)
    return self.__frame_parts__

  @nodes.GET
  def _getNodes(self, ) -> tuple[Node, ...]:
    """The 'nodes' getter returns the nodes, in the order added."""
    return self._getParts()[0]

  @members.GET
  def _getMembers(self, ) -> tuple[Member, ...]:
    """The 'members' getter returns the members, in the order added."""
    return self._getParts()[1]

  @supports.GET
  def _getSupports(self, ) -> tuple[Support, ...]:
    """The 'supports' getter returns the supports, in the order
    added."""
    return self._getParts()[2]

  @loads.GET
  def _getLoads(self, ) -> tuple[Load, ...]:
    """The 'loads' getter returns the loads, in the order added."""
    return self._getParts()[3]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(%d nodes, %d members, %d supports, %d loads)"""
    return infoSpec % (type(self).__name__, len(self.nodes),
                       len(self.members), len(self.supports),
                       len(self.loads))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple, tuple, tuple)
  def __init__(self, nodes: tuple, members: tuple, supports: tuple,
               loads: tuple) -> None:
    nodes = (*[Node(float(n.x), float(n.y)) for n in nodes],)
    members = (*[Member(int(m.first), int(m.second), float(m.EI),
                        float(m.EA), bool(m.startHinge),
                        bool(m.endHinge)) for m in members],)
    supports = (*[Support(int(s.node), str(s.kind)) for s in supports],)
    loads = (*map(self._cleaned, loads),)
    self._checkNodes(nodes, members)
    self._checkSupports(nodes, supports)
    self.__frame_parts__ = (nodes, members, supports, ())
    self._checkLoads(loads)
    self.__frame_parts__ = (nodes, members, supports, loads)

  @overload()
  def __init__(self, ) -> None:
    self.__init__(self.__fallback_nodes__, self.__fallback_members__,
                  self.__fallback_supports__, self.__fallback_loads__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def length(self, index: int) -> float:
    """The 'length' method returns how long the member of 'index' is, in
    m."""
    member = self.members[index]
    a, b = self.nodes[member.first], self.nodes[member.second]
    return math.hypot(b.x - a.x, b.y - a.y)

  def direction(self, index: int) -> tuple[float, float]:
    """The 'direction' method returns the unit vector the member of
    'index' runs along, from its first node to its second."""
    member = self.members[index]
    a, b = self.nodes[member.first], self.nodes[member.second]
    long = self.length(index)
    return (b.x - a.x) / long, (b.y - a.y) / long

  def pointAt(self, index: int, s: float) -> tuple[float, float]:
    """The 'pointAt' method returns where 's' m along the member of
    'index' is, in m."""
    start = self.nodes[self.members[index].first]
    tx, ty = self.direction(index)
    return start.x + s * tx, start.y + s * ty

  def joined(self, node: int) -> list[int]:
    """The 'joined' method returns the members at the node of index
    'node'."""
    return [i for i, m in enumerate(self.members)
            if node in (m.first, m.second)]

  def supportAt(self, node: int) -> Support | None:
    """The 'supportAt' method returns the support at the node of index
    'node', or 'None'."""
    for support in self.supports:
      if support.node == node:
        return support
    return None

  def indeterminacy(self, ) -> int:
    """The 'indeterminacy' method returns how many more ways the frame
    is held than it takes, counted: three for each member and each way
    a support holds, less three for each node and one for each moment a
    hinge lets go, a node hinged on every member it has letting go one
    fewer, its fixed support, if any, holding it turning to no end. A
    frame not held at all counts below nought, or may still count
    nought or more: 'Analysis' finds whether it is held."""
    count = 3 * len(self.members) - 3 * len(self.nodes)
    for index in range(len(self.nodes)):
      ends = [(m.first == index and m.startHinge)
              or (m.second == index and m.endHinge)
              for m in map(self.members.__getitem__, self.joined(index))]
      support = self.supportAt(index)
      held = sum(support.holds) if support is not None else 0
      if ends and all(ends):
        count -= len(ends) - 1
        held -= support.holds[2] if support is not None else 0
      else:
        count -= sum(ends)
      count += held
    return count

  def withNodes(self, *nodes: Node) -> Frame:
    """The 'withNodes' method returns the frame of 'nodes'."""
    return Frame(nodes, self.members, self.supports, self.loads)

  def withMembers(self, *members: Member) -> Frame:
    """The 'withMembers' method returns the frame of 'members'."""
    return Frame(self.nodes, members, self.supports, self.loads)

  def withSupports(self, *supports: Support) -> Frame:
    """The 'withSupports' method returns the frame on 'supports'."""
    return Frame(self.nodes, self.members, supports, self.loads)

  def withLoads(self, *loads: Load) -> Frame:
    """The 'withLoads' method returns the frame under 'loads'."""
    return Frame(self.nodes, self.members, self.supports, loads)

  def withNode(self, index: int, node: Node) -> Frame:
    """The 'withNode' method returns the frame with the node of 'index'
    moved to 'node', the loads on its members carried along as a share
    of their lengths."""
    nodes = [*self.nodes]
    nodes[index] = Node(float(node.x), float(node.y))
    moved = Frame((*nodes,), self.members, self.supports, ())
    loads = []
    for load in self.loads:
      factor = moved.length(load.member) / self.length(load.member)
      loads.append(self._scaled(load, factor))
    return moved.withLoads(*loads)

  def withMember(self, index: int, member: Member) -> Frame:
    """The 'withMember' method returns the frame with the member of
    'index' replaced by 'member'."""
    members = [*self.members]
    members[index] = member
    return self.withMembers(*members)

  def withSupport(self, index: int, support: Support) -> Frame:
    """The 'withSupport' method returns the frame with the support of
    'index' replaced by 'support'."""
    supports = [*self.supports]
    supports[index] = support
    return self.withSupports(*supports)

  def withLoad(self, index: int, load: Load) -> Frame:
    """The 'withLoad' method returns the frame with the load of 'index'
    replaced by 'load'."""
    loads = [*self.loads]
    loads[index] = load
    return self.withLoads(*loads)

  def withoutNode(self, index: int) -> Frame:
    """The 'withoutNode' method returns the frame without the node of
    'index', the members on it and their loads, and its support."""
    frame = self
    for member in sorted(self.joined(index))[::-1]:
      frame = frame.withoutMember(member)
    nodes = [n for i, n in enumerate(frame.nodes) if i != index]

    def down(at: int) -> int:
      return at - (1 if at > index else 0)

    members = [Member(down(m.first), down(m.second), *m[2:])
               for m in frame.members]
    supports = [Support(down(s.node), s.kind) for s in frame.supports
                if s.node != index]
    return Frame((*nodes,), (*members,), (*supports,), frame.loads)

  def withoutMember(self, index: int) -> Frame:
    """The 'withoutMember' method returns the frame without the member of
    'index' and its loads; its nodes stay."""
    members = [m for i, m in enumerate(self.members) if i != index]
    loads = []
    for load in self.loads:
      if load.member == index:
        continue
      at = load.member - (1 if load.member > index else 0)
      loads.append(type(load)(at, *load[1:]))
    return Frame(self.nodes, (*members,), self.supports, (*loads,))

  def withoutSupport(self, index: int) -> Frame:
    """The 'withoutSupport' method returns the frame without the support
    of 'index'."""
    supports = [s for i, s in enumerate(self.supports) if i != index]
    return self.withSupports(*supports)

  def withoutLoad(self, index: int) -> Frame:
    """The 'withoutLoad' method returns the frame without the load of
    'index'."""
    loads = [load for i, load in enumerate(self.loads) if i != index]
    return self.withLoads(*loads)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _scaled(load: Load, factor: float) -> Load:
    """'load' as far along its member, as a share of it, as before, the
    member 'factor' times as long."""
    if isinstance(load, LineLoad):
      return LineLoad(load.member, load.start * factor, load.end * factor,
                      load.first, load.last, load.direction)
    return load.movedTo(load.at * factor)

  @staticmethod
  def _cleaned(load: Load) -> Load:
    """'load' of numbers, refused if it is no load."""
    if isinstance(load, LineLoad):
      return LineLoad(int(load.member), *map(float, load[1:5]),
                      str(load.direction))
    if isinstance(load, PointLoad):
      return PointLoad(int(load.member), *map(float, load[1:]))
    if isinstance(load, PointMoment):
      return PointMoment(int(load.member), *map(float, load[1:]))
    raise ValueError('a load is a point load, a line load or a moment')

  @staticmethod
  def _checkNodes(nodes: tuple, members: tuple) -> None:
    """Raises unless the nodes are apart and each member between two of
    them, stiff, once."""
    for index, node in enumerate(nodes):
      if not (math.isfinite(node.x) and math.isfinite(node.y)):
        raise ValueError('N%d is somewhere' % (index + 1))
      for other in range(index):
        if math.hypot(node.x - nodes[other].x,
                      node.y - nodes[other].y) < 1e-6:
          infoSpec = """N%d and N%d are at the same place"""
          raise ValueError(infoSpec % (other + 1, index + 1))
    pairs = set()
    for member in members:
      for end in (member.first, member.second):
        if not 0 <= end < len(nodes):
          raise ValueError('a member joins nodes there are, not N%d'
                           % (end + 1))
      if member.first == member.second:
        raise ValueError('a member joins two nodes, not N%d to itself'
                         % (member.first + 1))
      if not (member.EI > 0 and member.EA > 0):
        raise ValueError("""a member's EI and EA are above nought""")
      pair = frozenset((member.first, member.second))
      if pair in pairs:
        infoSpec = """N%d and N%d are joined by one member at most"""
        raise ValueError(infoSpec % (member.first + 1, member.second + 1))
      pairs.add(pair)

  @staticmethod
  def _checkSupports(nodes: tuple, supports: tuple) -> None:
    """Raises unless each support is of a kind there is, at a node there
    is, one a node."""
    taken = set()
    for support in supports:
      if support.kind not in Support.kinds():
        infoSpec = """a support is a pin, a roller or fixed, not '%s'"""
        raise ValueError(infoSpec % support.kind)
      if not 0 <= support.node < len(nodes):
        raise ValueError('a support is at a node there is, not N%d'
                         % (support.node + 1))
      if support.node in taken:
        raise ValueError('N%d has one support at most'
                         % (support.node + 1))
      taken.add(support.node)

  def _checkLoads(self, loads: tuple) -> None:
    """Raises unless each load is on a member there is, along it, of
    numbers, each line load from its start to an end after it, down or
    to the right."""
    for load in loads:
      if not 0 <= load.member < len(self.members):
        raise ValueError('a load is on a member there is, not M%d'
                         % (load.member + 1))
      long = self.length(load.member)
      values = [*load[1:5]] if isinstance(load, LineLoad) else [*load[1:]]
      if not all(map(math.isfinite, values)):
        raise ValueError('a load is of numbers')
      ends = (load.start, load.end) if isinstance(load, LineLoad) else (
        load.at,)
      for s in ends:
        if not -1e-9 <= s <= long + 1e-9:
          infoSpec = """a load is along its member, 0 to %g m, not at %g
          m"""
          raise ValueError(' '.join(infoSpec.split()) % (long, s))
      if isinstance(load, LineLoad):
        if not load.end > load.start:
          raise ValueError('a line load ends after it starts')
        if load.direction not in _DIRECTIONS:
          infoSpec = """a line load pushes down or right, not '%s'"""
          raise ValueError(infoSpec % load.direction)
