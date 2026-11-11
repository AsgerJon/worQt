"""
PusherPanel subclasses 'PaintedWidget' and keeps the books of a coin
pusher: the player's purse, the coins in and out, and that the machine
keeps none.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent

  from ....utils import WPainter
  from ....utils.geom import Rect
  from .._machine_worker import Snapshot

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop
_WRAP = _LEFT | Qt.TextFlag.TextWordWrap
_ROW = 24.0  # pixels a row of the books takes


class PaintPusherPanel(AbstractPaintOp):
  """
  PaintPusherPanel subclasses 'AbstractPaintOp' and paints a
  'PusherPanel': the purse, large; the coins on the machine, in the
  tray, dropped in and won out; and a word on the books and how to
  play, or that the machine is starting.
  """

  #  Annotations
  widget: PusherPanel

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the books."""
    widget = self.widget
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setPen(widget.dividerColor.Q)
    painter.drawLine(QPointF(0.5, 0.0), QPointF(0.5, float(widget.height())))
    margin, width = 20.0, widget.width() - 40.0
    snapshot = widget.snapshot
    painter.setFont(widget.font)
    if snapshot is None:
      painter.setPen(widget.font.color.Q)
      words = QRectF(margin, 20.0, width, widget.height() - 40.0)
      painter.drawText(words, _WRAP, widget.starting())
      return rect
    painter.setPen(widget.dimColor.Q)
    painter.drawText(QRectF(margin, 20.0, width, _ROW), _LEFT, 'Purse')
    painter.setFont(widget.bigFont)
    painter.setPen(widget.goldColor.Q)
    painter.drawText(QRectF(margin, 40.0, width, 50.0), _LEFT,
                     '%d coins' % snapshot.purse)
    painter.setFont(widget.font)
    top = 110.0
    for name, value in widget.rows():
      painter.setPen(widget.dimColor.Q)
      painter.drawText(QRectF(margin, top, width, _ROW), _LEFT, name)
      painter.setPen(widget.font.color.Q)
      painter.drawText(QRectF(margin + 140.0, top, width - 140.0, _ROW),
                       _LEFT, value)
      top += _ROW
    painter.setPen(widget.font.color.Q)
    words = QRectF(margin, top + 16.0, width, widget.height() - top - 36.0)
    painter.drawText(words, _WRAP, widget.words())
    return rect


class PusherPanel(PaintedWidget):
  """
  PusherPanel subclasses 'PaintedWidget' and keeps the books of the
  machine as its last 'snapshot' has them: the player's purse; the
  coins on the machine and in the tray, dropped in and won out, and
  net; that purse, machine and tray hold every coin there is, the
  machine keeping none; and that the machine is empty or filling, or
  how to play, or that the purse is empty. With no snapshot yet it says
  the machine is starting.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_dim_color__ = Color(140, 144, 152)
  __fallback_gold_color__ = Color(229, 192, 123)

  #  Private Variables
  __panel_snapshot__: Snapshot | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPusherPanel()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      11,
      Color(212, 212, 212),
  )
  bigFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      26,
      Color(229, 192, 123),
  )

  #  Virtual Variables
  snapshot: Field[Snapshot] = Field()
  dividerColor: Field[Color] = Field()
  dimColor: Field[Color] = Field()
  goldColor: Field[Color] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @snapshot.GET
  def _getSnapshot(self, ) -> Snapshot | None:
    """The 'snapshot' getter returns the machine as last shown, or
    'None'."""
    return self.__panel_snapshot__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  @dimColor.GET
  def _getDimColor(self, ) -> Color:
    return self.__fallback_dim_color__

  @goldColor.GET
  def _getGoldColor(self, ) -> Color:
    return self.__fallback_gold_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @snapshot.SET
  def _setSnapshot(self, snapshot: Snapshot) -> None:
    """The 'snapshot' setter keeps the books of 'snapshot'."""
    self.__panel_snapshot__ = snapshot
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(320, 600)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(320, 400)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def rows(self, ) -> tuple[tuple[str, str], ...]:
    """The 'rows' method returns the books, each row a name and its
    number: on the machine, in the tray, dropped in, won out, net."""
    s = self.snapshot
    return (('On the machine', '%d' % s.onMachine),
            ('In the tray', '%d' % s.inTray),
            ('Dropped in', '%d' % s.dropped),
            ('Won out', '%d' % s.won),
            ('Net', '%+d' % (s.won - s.dropped)))

  def words(self, ) -> str:
    """The 'words' method says the books balance, the machine keeping
    none, and how to play, or that the purse is empty."""
    s = self.snapshot
    lines = [
      'The books: %d in the purse, %d on the machine and %d in the tray '
      'make %d, every coin there is. This machine keeps nothing: solid '
      'walls at the sides, a level table.' % (
        s.purse, s.onMachine, s.inTray, s.purse + s.onMachine + s.inTray),
      '',
    ]
    if s.filling:
      lines.append('The house is pouring its coins in. Once they lie, the '
                   'chutes open.')
    elif not s.started:
      lines.append('The machine is empty. Press Start game: the house '
                   'pours its coins in.')
    elif s.purse < 1:
      lines.append('Your purse is empty: wait for the tray to give some '
                   'back, or start a new game.')
    else:
      lines.append('Drop a coin down the left or the right chute: the '
                   'buttons above, or the arrow keys. It lands on the '
                   'shelf, the pusher\'s top; as the shelf draws back the '
                   'back wall pushes its coins off onto the table, and '
                   'the pusher shoves the coins there on. Those pushed '
                   'over the front edge fall into your tray, and back '
                   'into your purse once they lie still.')
    return '\n'.join(lines)

  def starting(self, ) -> str:
    """The 'starting' method says the machine is starting: the first
    time on a computer, the coin solver is compiled first."""
    return ('Starting the machine...\n\nThe first time on this computer '
            'the coin solver is compiled first: that takes a minute. '
            'After that it starts at once.')
