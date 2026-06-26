"""
TestSizing subclasses 'UtilsTest' and tests the sizing types in
'worQt.utils.qee_num': the 'SizingMode' enumeration (its mapping to
'QSizePolicy.Policy') and the 'SizePolicy' value object (its per-axis
modes, the write-once 'frozen' flag, the 'QSizePolicy' conversion and
hashing). 'QSizePolicy' is a Qt value class, so no 'QApplication' is
needed.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QSizePolicy

from worktoy.waitaminute import TypeException

from worQt.utils.qee_num import SizingMode, SizePolicy

from . import UtilsTest


class TestSizing(UtilsTest):
  """Tests for 'SizingMode' and 'SizePolicy'."""

  def test_sizing_mode_members(self) -> None:
    """'SizingMode' enumerates the extrinsic and intrinsic modes."""
    self.assertEqual([m.name for m in SizingMode],
                     ['EXTRINSIC', 'INTRINSIC'])

  def test_sizing_mode_q(self) -> None:
    """Each mode maps to its 'QSizePolicy.Policy' value."""
    self.assertEqual(SizingMode.EXTRINSIC.Q, QSizePolicy.Policy.Maximum)
    self.assertEqual(SizingMode.INTRINSIC.Q,
                     QSizePolicy.Policy.MinimumExpanding)

  def test_policy_defaults(self) -> None:
    """A default 'SizePolicy' is intrinsic on both axes and frozen."""
    policy = SizePolicy()
    self.assertIs(policy.horizontal, SizingMode.INTRINSIC)
    self.assertIs(policy.vertical, SizingMode.INTRINSIC)
    self.assertTrue(policy.frozen)

  def test_policy_set_axis(self) -> None:
    """A per-axis mode is settable on a standalone policy."""
    policy = SizePolicy()
    policy.horizontal = SizingMode.EXTRINSIC
    self.assertIs(policy.horizontal, SizingMode.EXTRINSIC)
    self.assertIs(policy.vertical, SizingMode.INTRINSIC)

  def test_policy_frozen_is_write_protected(self) -> None:
    """The 'frozen' flag rejects assignment."""
    policy = SizePolicy()
    with self.assertRaises(NotImplementedError):
      policy.frozen = False

  def test_policy_q_conversion(self) -> None:
    """The 'Q' field builds a 'QSizePolicy' from the per-axis modes."""
    qPolicy = SizePolicy().Q
    self.assertIsInstance(qPolicy, QSizePolicy)
    self.assertEqual(qPolicy.horizontalPolicy(),
                     QSizePolicy.Policy.MinimumExpanding)
    self.assertEqual(qPolicy.verticalPolicy(),
                     QSizePolicy.Policy.MinimumExpanding)

  def test_policy_hash(self) -> None:
    """Two default policies hash equal (so a policy is hashable)."""
    self.assertEqual(hash(SizePolicy()), hash(SizePolicy()))

  def test_policy_recursion_guards(self) -> None:
    """Each lazy getter guards against a failed build."""
    for name in ('_getHorizontalMode', '_getVerticalMode',
                 '_getFrozenFlag'):
      policy = SizePolicy()
      with self.assertRaises(RecursionError):
        getattr(policy, name)(_recursion=True)

  def test_policy_type_guards(self) -> None:
    """Each getter rejects a corrupt backing slot."""
    specs = (('__horizontal_mode__', '_getHorizontalMode'),
             ('__vertical_mode__', '_getVerticalMode'),
             ('__is_frozen__', '_getFrozenFlag'))
    for slot, getter in specs:
      policy = SizePolicy()
      setattr(policy, slot, 'bad')
      with self.assertRaises(TypeException):
        getattr(policy, getter)()

  def test_policy_setter_type_check(self) -> None:
    """The per-axis setters reject a non-'SizingMode' value."""
    with self.assertRaises(TypeException):
      SizePolicy().horizontal = 'bad'
    with self.assertRaises(TypeException):
      SizePolicy().vertical = 'bad'

  def test_policy_set_same_axis_skipped(self) -> None:
    """Re-setting an axis to its current value is skipped."""
    policy = SizePolicy()
    policy.horizontal = SizingMode.EXTRINSIC
    policy.horizontal = SizingMode.EXTRINSIC  # same -> SkipSet
    self.assertIs(policy.horizontal, SizingMode.EXTRINSIC)
    policy.vertical = SizingMode.EXTRINSIC
    policy.vertical = SizingMode.EXTRINSIC
    self.assertIs(policy.vertical, SizingMode.EXTRINSIC)

  def test_policy_set_different_axis_value(self) -> None:
    """Re-setting an already-set axis to a different value proceeds (the
    pre-set guard sees a real change, not a no-op)."""
    policy = SizePolicy()
    policy.horizontal = SizingMode.EXTRINSIC
    policy.horizontal = SizingMode.INTRINSIC  # differs -> no SkipSet
    self.assertIs(policy.horizontal, SizingMode.INTRINSIC)
    policy.vertical = SizingMode.EXTRINSIC
    policy.vertical = SizingMode.INTRINSIC
    self.assertIs(policy.vertical, SizingMode.INTRINSIC)
