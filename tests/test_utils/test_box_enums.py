"""
TestBoxEnums subclasses 'UtilsTest' and tests the plain index enumerations
in 'worQt.utils.qee_num': 'BoxNum', 'EdgeNum' and 'VertexNum'. Each is a
four-member 'KeeNum' over the integers 0..3, so the tests cover member
values, indices, iteration order and the resolution paths (by name, by
index, by value).
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worQt.utils.qee_num import BoxNum, EdgeNum, VertexNum

from . import UtilsTest


class TestBoxEnums(UtilsTest):
  """Tests for the 'BoxNum', 'EdgeNum' and 'VertexNum' enumerations."""

  def test_box_num_members(self) -> None:
    """'BoxNum' enumerates margin, border, padding and content in order."""
    self.assertEqual(len(BoxNum), 4)
    self.assertEqual([m.name for m in BoxNum],
                     ['MARGIN', 'BORDER', 'PADDING', 'CONTENT'])

  def test_box_num_values(self) -> None:
    """Each 'BoxNum' member carries its declared integer value."""
    self.assertEqual(BoxNum.MARGIN.value, 0)
    self.assertEqual(BoxNum.BORDER.value, 1)
    self.assertEqual(BoxNum.PADDING.value, 2)
    self.assertEqual(BoxNum.CONTENT.value, 3)

  def test_box_num_index(self) -> None:
    """'int' of a member is its enumeration index."""
    self.assertEqual(int(BoxNum.MARGIN), 0)
    self.assertEqual(int(BoxNum.CONTENT), 3)

  def test_box_num_resolve_by_name(self) -> None:
    """A member resolves from its name, case-insensitively."""
    self.assertIs(BoxNum('MARGIN'), BoxNum.MARGIN)
    self.assertIs(BoxNum('content'), BoxNum.CONTENT)

  def test_box_num_resolve_by_value(self) -> None:
    """Calling with an integer value resolves the matching member."""
    self.assertIs(BoxNum(0), BoxNum.MARGIN)
    self.assertIs(BoxNum(3), BoxNum.CONTENT)

  def test_box_num_resolve_by_index(self) -> None:
    """Subscripting with an integer indexes the member sequence."""
    self.assertIs(BoxNum[0], BoxNum.MARGIN)
    self.assertIs(BoxNum[-1], BoxNum.CONTENT)

  def test_edge_num(self) -> None:
    """'EdgeNum' enumerates the edges clockwise from the left."""
    self.assertEqual([m.name for m in EdgeNum],
                     ['LEFT', 'TOP', 'RIGHT', 'BOTTOM'])
    self.assertEqual(EdgeNum.LEFT.value, 0)
    self.assertEqual(EdgeNum.BOTTOM.value, 3)
    self.assertIs(EdgeNum('TOP'), EdgeNum.TOP)

  def test_vertex_num(self) -> None:
    """'VertexNum' enumerates the corners clockwise from the top-left."""
    self.assertEqual([m.name for m in VertexNum],
                     ['TOP_LEFT', 'TOP_RIGHT', 'BOTTOM_RIGHT', 'BOTTOM_LEFT'])
    self.assertEqual(VertexNum.TOP_LEFT.value, 0)
    self.assertIs(VertexNum(2), VertexNum.BOTTOM_RIGHT)
