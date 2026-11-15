"""
LiveWindow shows a widget as a real top-level window and blocks until it is
mapped and painted, so a test acts on an actually rendered window. In the
headless fallback the offscreen platform still exposes the window, so the
same fixture serves both modes. With 'QTEST_NO_FOCUS' set to '1' in the
environment (an unattended run: the job runner's, user, 2026-11-14: "make
it so the app doesn't take focus") the window is shown without being
activated and takes no focus, so the person at the desktop keeps theirs.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QWidget
from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable, TypeException

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Optional, TypeAlias, Union

  MaybeWidget: TypeAlias = Optional[QWidget]
  WidgetField: TypeAlias = Union[QWidget, Field]


class LiveWindow(BaseObject):
  """
  LiveWindow shows a widget as a top-level window and blocks on
  'QTest.qWaitForWindowExposed' until it is mapped and painted, then
  returns it. The window is raised and activated first so it can receive
  synthesised input in the authentic mode. Disposal is left to the test
  harness, which snapshots and deletes the windows each test opens.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __expose_timeout__: int = 5000  # milliseconds to wait for the expose

  #  Private Variables
  __the_widget__: MaybeWidget = None

  #  Public Variables
  widget: WidgetField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @widget.GET
  def _getWidget(self, ) -> QWidget:
    """The 'widget' getter returns the widget shown by this window."""
    if self.__the_widget__ is None:
      raise MissingVariable(self, '__the_widget__', QWidget)
    if isinstance(self.__the_widget__, QWidget):
      return self.__the_widget__
    raise TypeException('__the_widget__', self.__the_widget__, QWidget)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def show(self, ) -> QWidget:
    """The 'show' method shows the widget, raises and activates it (in a
    run that takes no focus, 'QTEST_NO_FOCUS', neither: shown without
    activating, taking no focus), and blocks until it is exposed and
    painted, then returns it."""
    widget = self.widget
    if os.environ.get('QTEST_NO_FOCUS') == '1':
      widget.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
      widget.setWindowFlag(Qt.WindowType.WindowDoesNotAcceptFocus, True)
      widget.show()
    else:
      widget.show()
      widget.raise_()
      widget.activateWindow()
    QTest.qWaitForWindowExposed(widget, self.__expose_timeout__)
    return widget

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, widget: QWidget) -> None:
    if not isinstance(widget, QWidget):
      raise TypeException('widget', widget, QWidget)
    self.__the_widget__ = widget
