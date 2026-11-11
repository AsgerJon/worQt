"""
TestFrame covers 'Frame', a plane frame of straight members: it is made
only whole; its members' lengths and directions; a node moved carries
the loads on its members along; parts taken away take what is on them
and renumber the rest; its indeterminacy is counted.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.engineering.diagrams import Frame, LineLoad, Member, Node
from worQt.engineering.diagrams import PointLoad, Support

from . import DiagramsTest, beam, threeHinged


class TestFrame(DiagramsTest):
  """Tests for 'Frame'."""

  def test_standard(self) -> None:
    """Made of nothing, it is a portal, fixed at its left foot and
    pinned at its right, loaded on its beam and at its top left."""
    frame = Frame()
    self.assertEqual(len(frame.nodes), 4)
    self.assertEqual(len(frame.members), 3)
    self.assertEqual([s.kind for s in frame.supports], ['fixed', 'pin'])
    self.assertEqual(frame.length(1), 6.0)
    self.assertEqual(frame.direction(0), (0.0, 1.0))
    self.assertEqual(frame.pointAt(1, 2.0), (2.0, 4.0))
    self.assertEqual(frame.joined(1), [0, 1])

  def test_refused(self) -> None:
    """It is made only whole."""
    nodes = (Node(0.0, 0.0), Node(4.0, 0.0))
    member = Member(0, 1, 1.0, 1.0, False, False)
    cases = (
      ((Node(0.0, 0.0), Node(0.0, 0.0)), (), (), (), 'same place'),
      (nodes, (Member(0, 2, 1.0, 1.0, False, False),), (), (), 'not N3'),
      (nodes, (Member(0, 0, 1.0, 1.0, False, False),), (), (),
       'to itself'),
      (nodes, (member, Member(1, 0, 1.0, 1.0, False, False)), (), (),
       'one member at most'),
      (nodes, (member,), (Support(0, 'pin'), Support(0, 'roller')), (),
       'one support at most'),
      (nodes, (member,), (Support(0, 'hook'),), (), "not 'hook'"),
      (nodes, (member,), (), (PointLoad(0, 5.0, 1.0, 0.0),),
       'along its member'),
      (nodes, (member,), (), (LineLoad(0, 3.0, 1.0, 1.0, 1.0, 'down'),),
       'ends after it starts'),
      (nodes, (member,), (), (LineLoad(0, 0.0, 1.0, 1.0, 1.0, 'up'),),
       "not 'up'"),
    )
    for points, members, supports, loads, words in cases:
      with self.assertRaises(ValueError) as context:
        Frame(points, members, supports, loads)
      self.assertIn(words, str(context.exception))

  def test_moved_node(self) -> None:
    """A node moved carries the loads on its members along, as a share
    of their lengths."""
    frame = Frame()
    moved = frame.withNode(2, Node(12.0, 4.0))
    self.assertEqual(moved.length(1), 12.0)
    self.assertEqual(moved.loads[0][1:3], (0.0, 12.0))
    self.assertEqual(moved.loads[1], frame.loads[1])

  def test_without(self) -> None:
    """A node taken away takes its members, their loads and its support
    along; a member taken away takes its loads, the rest renumbered."""
    frame = Frame()
    without = frame.withoutNode(0)
    self.assertEqual(len(without.nodes), 3)
    self.assertEqual([m[:2] for m in without.members], [(0, 1), (1, 2)])
    self.assertEqual(without.supports, (Support(2, 'pin'),))
    self.assertEqual(len(without.loads), 1)
    self.assertEqual(without.loads[0].member, 0)
    self.assertEqual(frame.withoutMember(0).loads[0].member, 0)
    self.assertEqual(len(frame.withoutLoad(0).loads), 1)
    self.assertEqual(len(frame.withoutSupport(0).supports), 1)

  def test_indeterminacy(self) -> None:
    """Counted: a beam on a pin and a roller nought, propped on a fixed
    end one, the portal two, three hinged nought, a portal hinged at
    every corner below nought."""
    self.assertEqual(beam((Support(0, 'pin'), Support(1, 'roller')),
                          ()).indeterminacy(), 0)
    self.assertEqual(beam((Support(0, 'fixed'), Support(1, 'roller')),
                          ()).indeterminacy(), 1)
    self.assertEqual(Frame().indeterminacy(), 2)
    self.assertEqual(threeHinged().indeterminacy(), 0)
    frame = Frame().withoutLoad(1).withoutLoad(0)
    hinged = frame.withMember(1, frame.members[1].hinged(True, True))
    hinged = hinged.withSupport(0, Support(0, 'pin'))
    self.assertEqual(hinged.indeterminacy(), -1)
