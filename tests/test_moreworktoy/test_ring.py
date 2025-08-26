"""
TestRing tests the 'Ring' class from the moreworktoy module.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from moreworktoy.utilities import Ring
from . import MoreTest


class TestRing(MoreTest):
  """
  TestRing tests the 'Ring' class from the moreworktoy module.
  """

  def setUp(self) -> None:
    """Creates various rings at self.r0, self.r1, ... for testing."""
    self.r0 = Ring()
    self.r1 = Ring(8)
    self.r2 = Ring(69, 420)

  def tearDown(self) -> None:
    """Cleans up after tests."""
    del self.r0
    del self.r1
    del self.r2

  def test_init(self, ) -> None:
    """Tests that 'Ring' objects can be initialized."""
    self.assertIsInstance(self.r0, Ring)
    self.assertIsInstance(self.r1, Ring)
    self.assertIsInstance(self.r2, Ring)

  def test_bool(self) -> None:
    """
    Tests the boolean evaluation of 'Ring' objects.
    """
    self.assertFalse(self.r0)
    self.assertFalse(self.r1)
    self.assertTrue(self.r2)

  def test_append(self) -> None:
    """
    Tests the 'append' method of 'Ring' objects.
    """
    for r in (self.r0, self.r1, self.r2):
      _c = 0
      while len(r) < abs(r):
        r.append(1)
        _c += 1
        self.assertEqual(len(r), _c)
        if _c > 1000:
          raise RuntimeError

  def test_iter(self, ) -> None:
    """Testing the iteration over 'Ring' objects."""
    #
    # for i, r in enumerate((self.r0, self.r1, self.r2)):
    #   print("""Testing: %s""" % ['r0', 'r1', 'r2'][i])
    #   while len(r) < abs(r):
    #     r.append(len(r))
    #   for e in r:
    #     print(e)
    #   print("""--- END ---""")

  def test_roll(self) -> None:
    """
    Tests that the first element disappears when appending to a full
    ring.
    """

    for i, r in enumerate((self.r0, self.r1, self.r2)):
      while len(r) < abs(r):
        r.append(len(r))
