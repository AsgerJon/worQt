"""
RunMixinBase subclasses 'AppTest' and tests the 'worQt.mixin.MixinBase'
utilities every fused class inherits: the running-application handle, the
'src'/'root'/'etc' path fields, 'eps', the descriptor-ownership guards, the
'QObject' class-body ban, parent resolution and index rolling. 'MixinBase'
is not itself a 'QObject', but 'app' resolves a running 'QApplication', so
the tests run under 'AppTest'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from worktoy.core.sentinels import METACALL
from worktoy.desc import AttriBox
from worktoy.mcls import BaseObject

from worQt.mixin import MixinBase
from worQt.qtest import AppTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Sized(MixinBase):
  """A 'MixinBase' subclass that implements '__len__', so '_rollIndex'
  has a length to roll against."""

  def __len__(self) -> int:
    return 5


class _Owner(BaseObject):
  """Hosts a boxed '_Sized', so the boxed value gains field identity."""

  boxed = AttriBox[_Sized]()


class RunMixinBase(AppTest):
  """Tests for the 'MixinBase' shared utilities."""

  def run_app_returns_running_application(self) -> None:
    """'app' resolves the running 'QApplication'."""
    self.assertIs(MixinBase().app, QApplication.instance())

  def run_path_fields(self) -> None:
    """'src'/'root'/'etc' resolve to the expected directories."""
    base = MixinBase()
    self.assertEqual(os.path.basename(base.src), 'src')
    self.assertEqual(base.root, os.path.abspath(os.path.join(base.src, '..')))
    self.assertEqual(base.etc, os.path.join(base.src, 'etc'))

  def run_eps(self) -> None:
    """'eps' is the machine epsilon."""
    self.assertEqual(MixinBase().eps, sys.float_info.epsilon)

  def run_unowned_descriptor_fields_raise(self) -> None:
    """An instance not owned by an 'AttriBox' has no field identity."""
    base = MixinBase()
    with self.assertRaises(TypeError):
      _ = base.fieldOwner
    with self.assertRaises(TypeError):
      _ = base.fieldName

  def run_class_body_ban(self) -> None:
    """Using a 'MixinBase' as a class variable is refused at creation."""
    with self.assertRaises(RuntimeError):
      type('Banned', (), {'leak': MixinBase()})

  def run_len_unimplemented(self) -> None:
    """The base does not implement '__len__'."""
    with self.assertRaises(TypeError):
      _ = len(MixinBase())

  def run_resolve_parent(self) -> None:
    """'_resolveParent' returns the first 'QObject', else 'None'."""
    parent = QObject()
    self.assertIs(MixinBase._resolveParent('x', 1, parent), parent)
    self.assertIsNone(MixinBase._resolveParent('x', 1, 2.0))

  def run_roll_index_needs_len(self) -> None:
    """'_rollIndex' fails cleanly without a '__len__'."""
    with self.assertRaises(TypeError):
      MixinBase()._rollIndex(0)

  def run_roll_index_success(self) -> None:
    """With a '__len__', '_rollIndex' passes positives through, wraps
    negatives, and rejects out-of-range indices."""
    sized = _Sized()
    self.assertEqual(sized._rollIndex(2), 2)
    self.assertEqual(sized._rollIndex(-1), 4)
    with self.assertRaises(IndexError):
      sized._rollIndex(5)

  def run_field_identity_when_owned(self) -> None:
    """A value built by an 'AttriBox' carries its owner, name and box, so
    'fieldOwner'/'fieldName'/'fieldBox' resolve."""
    boxed = _Owner().boxed
    self.assertIs(boxed.fieldOwner, _Owner)
    self.assertEqual(boxed.fieldName, 'boxed')
    self.assertIsInstance(boxed.fieldBox, AttriBox)

  def run_metacall_for_class_dunder(self) -> None:
    """'_Shiboken.__getattr__' answers a missing '__class*__' name with the
    'METACALL' sentinel, while an ordinary missing name still raises."""
    self.assertIs(MixinBase.__class_frobnicate__, METACALL)
    with self.assertRaises(AttributeError):
      _ = MixinBase.totallyMissingThing
