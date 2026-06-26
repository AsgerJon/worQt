"""Main Tester Script"""
#  Apache-2.0 license
#  Copyright (c) 2023-2026 Asger Jon Vistisen
from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject

here = os.path.dirname(os.path.abspath(__file__))
src = os.path.join(here, 'src')
sys.path.append(here)
sys.path.append(src)

from icecream import ic

from worQt.qtest import testMeBro

ic.configureOutput(includeContext=True)

from PySide6.QtCore import QTimer
from worktoy.core.sentinels import THIS

from worQt.app import AbstractApplication, App
from worQt.widgets import LabelWidget, TextWidget, PaintedWidget
from worQt.windows import MainWindow
from worQt.paint_ops import PaintBoxModel
from worQt.utils.geom import InSets, Size
from worQt.utils.qee_num import ColorNum
from yolo import yolo, runTests

if TYPE_CHECKING:  # pragma: no cover
  pass

_LEGEND = (
  'One custom widget, drawn entirely by worQt. The coloured bands are its '
  'box model — blue MARGIN, dark BORDER, orange PADDING, grey CONTENT — '
  'each a value you set in Python. Watch them breathe: the same widget, '
  'repainting live as those values change.'
)


class BoxModelDemo(PaintedWidget):
  """A 'PaintedWidget' that shows its own box model as a centred, vividly
  coloured nested rectangle. The band thicknesses are plain 'AttriBox[int]'
  values; overriding the box-model getters feeds them to the inherited
  'PaintBoxModel' paint op, so changing one and calling 'update()'
  repaints."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  boxOp = PaintBoxModel()
  marginThick = AttriBox[int](24)
  borderThick = AttriBox[int](14)
  paddingThick = AttriBox[int](24)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getRequiredSize(self, ) -> Size:
    return Size(200, 96)

  def _getMarginsDims(self, **kwargs) -> InSets:
    return InSets(self.marginThick)

  def _getBordersDims(self, **kwargs) -> InSets:
    return InSets(self.borderThick)

  def _getPaddingsDims(self, **kwargs) -> InSets:
    return InSets(self.paddingThick)

  def _getMarginsColor(self, **kwargs):
    return ColorNum.ROYAL_BLUE.value

  def _getBordersColor(self, **kwargs):
    return ColorNum.CHARCOAL.value

  def _getPaddingsColor(self, **kwargs):
    return ColorNum.ORANGE.value


class DemoWindow(MainWindow):
  """A worQt showcase whose star is one 'BoxModelDemo' widget: a big, gently
  animated nested box that makes the margin/border/padding/content model
  visible at a glance. Every widget is an 'AttriBox' field built lazily with
  the window as parent ('THIS'); 'initUI' only places and animates them."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Widgets (lazily built children; never constructed in a method body)
  caption = AttriBox[LabelWidget](THIS, 'worQt — the box model, live')
  hero = AttriBox[BoxModelDemo](THIS)
  legend = AttriBox[TextWidget](THIS, _LEGEND)
  beat = AttriBox[QTimer](THIS)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def initUI(self, ) -> None:
    super().initUI()
    self.setWindowTitle('worQt — the box model, live')
    self.resize(620, 480)
    self._phase = 0
    grid = self.baseLayout
    grid.addWidget(self.caption, 0, 0)
    grid.addWidget(self.hero, 1, 0)
    grid.addWidget(self.legend, 2, 0)
    self.caption.font.fontSize = 20
    self.hero.xr = 18
    self.hero.yr = 18
    self.beat.setInterval(40)
    self.beat.timeout.connect(self._tick)
    self.beat.start()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _tick(self, ) -> None:
    """Breathe the box model: margins and paddings swell out of phase, so
    the same widget visibly re-lays-out itself every frame."""
    self._phase = (self._phase + 1) % 160
    swing = self._phase if self._phase < 80 else 160 - self._phase  #
    # 0..80..0
    self.hero.marginThick = 8 + swing // 3
    self.hero.paddingThick = 8 + (80 - swing) // 3
    self.hero.update()


class DemoApp(App):
  """An 'App' that knows which window to build."""
  __window_class__ = DemoWindow


def tester02(*args, ) -> int:
  """Pops up the worQt painted-widget demo window. Set the 'SHOT' env var
  (with 'QT_QPA_PLATFORM=offscreen') to render one frame to that path and
  quit, instead of running the live event loop."""
  with DemoApp(sys.argv) as app:
    window = app.window
    window.show()
    shot = os.environ.get('SHOT')
    if shot:
      QTimer.singleShot(120, lambda: (window.grab().save(shot), app.quit()))
  return app.returnCode
