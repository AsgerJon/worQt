"""
TestMenuBoxes covers the declarative registration guards: the 'ActionBox'
and 'MenuBox' subscript and '__set_name__' type/subclass checks, the
'registerActionType'/'registerMenuType' duplicate and type guards, and the
registry accessors' type guards. These are class-level, so no
'QApplication' is built.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QMenu
from worktoy.waitaminute import TypeException, SubclassException

from worQt.waitaminute import DuplicateRegistration
from worQt.windows.menus import (AbstractMenu, AbstractMenuBar, ActionBox,
                                MenuBox, MenuSeparator)

from . import WindowsTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _NotAQt:
  """A plain class that is neither a 'QAction' nor a 'QMenu'."""


class TestMenuBoxes(WindowsTest):
  """Tests for the box and registry guards."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ACTION BOX  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_action_box_subscript_guards(self) -> None:
    """'ActionBox' rejects non-types and non-'QAction' types, but admits
    'MenuSeparator' by name."""
    with self.assertRaises(TypeException):
      _ = ActionBox[123]
    with self.assertRaises(SubclassException):
      _ = ActionBox[_NotAQt]
    self.assertIsNotNone(ActionBox[MenuSeparator])

  def test_action_box_set_name_guards(self) -> None:
    """'ActionBox.__set_name__' requires a 'QMenu' owner type."""
    box = ActionBox[MenuSeparator]
    with self.assertRaises(TypeException):
      box.__set_name__(123, 'x')
    with self.assertRaises(SubclassException):
      box.__set_name__(_NotAQt, 'x')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MENU BOX  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_menu_box_subscript_guards(self) -> None:
    """'MenuBox' rejects non-types and non-'QMenu' types."""
    with self.assertRaises(TypeException):
      _ = MenuBox[123]
    with self.assertRaises(SubclassException):
      _ = MenuBox[_NotAQt]

  def test_menu_box_set_name_guards(self) -> None:
    """'MenuBox.__set_name__' requires a 'QMenuBar' owner type."""
    box = MenuBox[QMenu]
    with self.assertRaises(TypeException):
      box.__set_name__(123, 'x')
    with self.assertRaises(SubclassException):
      box.__set_name__(_NotAQt, 'x')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ACTION REGISTRY  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_register_action_guards(self) -> None:
    """'registerActionType' rejects duplicates, non-types and non-actions."""

    class _Menu(AbstractMenu):
      pass

    _Menu.registerActionType('a', MenuSeparator)
    with self.assertRaises(DuplicateRegistration):
      _Menu.registerActionType('a', MenuSeparator)
    with self.assertRaises(TypeException):
      _Menu.registerActionType('b', 123)
    with self.assertRaises(SubclassException):
      _Menu.registerActionType('b', _NotAQt)

  def test_action_registry_type_guards(self) -> None:
    """A corrupt action registry raises on read."""

    class _BadType(AbstractMenu):
      pass

    _BadType.__registered_action_types__ = {'x': 123}
    with self.assertRaises(TypeException):
      _BadType._classGetRegisteredActionTypes()

    class _BadSub(AbstractMenu):
      pass

    _BadSub.__registered_action_types__ = {'x': _NotAQt}
    with self.assertRaises(SubclassException):
      _BadSub._classGetRegisteredActionTypes()

    class _BadContainer(AbstractMenu):
      pass

    _BadContainer.__registered_action_types__ = 'bad'
    with self.assertRaises(TypeException):
      _BadContainer._classGetRegisteredActionTypes()

  def test_action_registry_recursion(self) -> None:
    """A recursive registry read with no registry raises."""

    class _Menu(AbstractMenu):
      pass

    with self.assertRaises(RecursionError):
      _Menu._classGetRegisteredActionTypes(_recursion=True)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MENU REGISTRY  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_register_menu_guards(self) -> None:
    """'registerMenuType' rejects duplicates, non-types and non-menus."""

    class _Bar(AbstractMenuBar):
      pass

    class _Menu(AbstractMenu):
      pass

    _Bar.registerMenuType('m', _Menu)
    with self.assertRaises(DuplicateRegistration):
      _Bar.registerMenuType('m', _Menu)
    with self.assertRaises(TypeException):
      _Bar.registerMenuType('n', 123)
    with self.assertRaises(SubclassException):
      _Bar.registerMenuType('n', _NotAQt)

  def test_menu_registry_type_guards(self) -> None:
    """A corrupt menu registry raises on read."""

    class _BadType(AbstractMenuBar):
      pass

    _BadType.__registered_menu_types__ = {'x': 123}
    with self.assertRaises(TypeException):
      _BadType._classGetRegisteredMenuTypes()

    class _BadSub(AbstractMenuBar):
      pass

    _BadSub.__registered_menu_types__ = {'x': _NotAQt}
    with self.assertRaises(SubclassException):
      _BadSub._classGetRegisteredMenuTypes()

    class _BadContainer(AbstractMenuBar):
      pass

    _BadContainer.__registered_menu_types__ = 'bad'
    with self.assertRaises(TypeException):
      _BadContainer._classGetRegisteredMenuTypes()

  def test_menu_registry_recursion(self) -> None:
    """A recursive registry read with no registry raises."""

    class _Bar(AbstractMenuBar):
      pass

    with self.assertRaises(RecursionError):
      _Bar._classGetRegisteredMenuTypes(_recursion=True)
