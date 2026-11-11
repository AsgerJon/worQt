"""
QuestPanel subclasses 'PaintedWidget' and is the list of quests, the
quest played and how far it is from its goal.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QLineF, QPointF, QRectF, QSize, Signal
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...circuits import Bit, BusIn, BusProbe, Led
from ...gui import ToolButton
from ...gui._paint_panel import PaintPanel
from .. import COMPUTER, MAIN, Progress, QUESTS, SUPER

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtCore import QEvent
  from PySide6.QtGui import QMouseEvent, QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap
_ACCENT = QColor(229, 192, 123)
_DONE = QColor(152, 195, 121)
_OPEN = QColor(190, 194, 202)
_SHUT = QColor(90, 94, 102)
_ROW = 24  # pixels a quest's row takes
_TOP = 12  # pixels down to the first heading
_HEAD = 28  # pixels a section's heading takes
SANDBOX = -1  # the row of the sandbox, after the quests
#  The sections of the quests: each its name, its first quest and the
#  one after its last
SECTIONS = (
  ('Quests', 0, len(MAIN)),
  ('Super quests', len(MAIN), len(MAIN) + len(SUPER)),
  ('Computer', len(MAIN) + len(SUPER),
   len(MAIN) + len(SUPER) + len(COMPUTER)),
  ('Microprocessor', len(MAIN) + len(SUPER) + len(COMPUTER), len(QUESTS)),
)


def sectionOf(row: int) -> int:
  """The 'sectionOf' function returns the section the quest of 'row' is
  in."""
  for index, (_, first, after) in enumerate(SECTIONS):
    if first <= row < after:
      return index
  return 0


def kindName(kind: object) -> str:
  """The 'kindName' function returns the name of a kind of part, or of
  chip, as a button says it."""
  if isinstance(kind, str):
    return kind
  names = {Led: 'LED', Bit: 'Input', BusIn: 'Bus input',
           BusProbe: 'Bus probe'}
  return names.get(kind, kind.__name__)


class PaintQuestPanel(AbstractPaintOp):
  """
  PaintQuestPanel subclasses 'AbstractPaintOp' and paints a
  'QuestPanel': its heading, a row a quest, each with a tick done, a
  ring open or a padlock shut, the one played lit, the sandbox last;
  then the quest played, its brief, how far it is from its goal and
  what it unlocks.
  """

  #  Annotations
  widget: QuestPanel

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the panel's words and rows."""
    widget = self.widget
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    for section in range(len(SECTIONS)):
      self._paintHeading(painter, section)
    for row in (*range(len(QUESTS)), SANDBOX):
      if widget.rowRect(row) is not None:
        self._paintRow(painter, row)
    painter.setFont(widget.headingFont)
    painter.setPen(widget.headingFont.color.Q)
    box = widget.textRect()
    painter.drawText(QRectF(box.left(), box.top(), box.width(), 22.0),
                     _LEFT, widget.title())
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    words = QRectF(box.left(), box.top() + 28.0, box.width(),
                   box.height() - 28.0)
    painter.drawText(words, _WRAP, widget.words())
    return rect

  def _paintHeading(self, painter: WPainter, section: int) -> None:
    """The heading of 'section': a wedge, pointing down when open, its
    name, and how many of its quests are done."""
    widget = self.widget
    box = widget.headingRect(section)
    name, first, after = SECTIONS[section]
    done = sum(1 for row in range(first, after)
               if widget.progress.isDone(row))
    if section == widget.hoveredSection:
      fill = QColor(_OPEN)
      fill.setAlpha(18)
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(fill))
      painter.drawRoundedRect(box, 4.0, 4.0)
    x, y = box.left() + 14.0, box.center().y()
    painter.setPen(self.emptyPen)
    painter.setBrush(QBrush(widget.headingFont.color.Q))
    if section == widget.openSection:
      wedge = [QPointF(x - 5.0, y - 3.0), QPointF(x + 5.0, y - 3.0),
               QPointF(x, y + 4.0)]
    else:
      wedge = [QPointF(x - 3.0, y - 5.0), QPointF(x - 3.0, y + 5.0),
               QPointF(x + 4.0, y)]
    painter.drawPolygon(QPolygonF(wedge))
    painter.setFont(widget.headingFont)
    painter.setPen(widget.headingFont.color.Q)
    text = QRectF(box.left() + 30.0, box.top(), box.width() - 34.0,
                  box.height())
    painter.drawText(text, _LEFT, name)
    painter.setFont(widget.font)
    painter.setPen(_DONE if done == after - first else _OPEN)
    painter.drawText(text.adjusted(0.0, 0.0, -6.0, 0.0), _RIGHT,
                     '%d of %d' % (done, after - first))

  def _paintRow(self, painter: WPainter, row: int) -> None:
    """The row of the quest 'row', or of the sandbox."""
    widget = self.widget
    box = widget.rowRect(row)
    state = widget.stateOf(row)
    if row == widget.shown:
      fill = QColor(_ACCENT)
      fill.setAlpha(40)
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(fill))
      painter.drawRoundedRect(box, 4.0, 4.0)
    elif row == widget.hovered and state != 'shut':
      fill = QColor(_OPEN)
      fill.setAlpha(18)
      painter.setPen(self.emptyPen)
      painter.setBrush(QBrush(fill))
      painter.drawRoundedRect(box, 4.0, 4.0)
    mark = QPointF(box.left() + 14.0, box.center().y())
    self._paintMark(painter, mark, state)
    painter.setFont(widget.font)
    painter.setPen(_SHUT if state == 'shut' else _OPEN)
    if row == widget.shown:
      painter.setPen(_ACCENT)
    text = 'Sandbox' if row == SANDBOX else '%d. %s' % (row + 1,
                                                         QUESTS[row].name)
    painter.drawText(QRectF(box.left() + 30.0, box.top(), box.width()
                            - 34.0, box.height()), _LEFT, text)

  def _paintMark(self, painter: WPainter, at: QPointF, state: str) -> None:
    """The mark of a row's state at 'at': a tick done, a ring open, a
    padlock shut, a box for the sandbox."""
    x, y = at.x(), at.y()
    painter.setBrush(Qt.BrushStyle.NoBrush)
    if state == 'done':
      pen = QPen(_DONE, 2.2)
      pen.setCapStyle(Qt.PenCapStyle.RoundCap)
      painter.setPen(pen)
      painter.drawLine(QLineF(x - 5.0, y, x - 1.5, y + 4.0))
      painter.drawLine(QLineF(x - 1.5, y + 4.0, x + 5.0, y - 4.5))
    elif state == 'shut':
      painter.setPen(QPen(_SHUT, 1.6))
      painter.drawRect(QRectF(x - 5.0, y - 1.0, 10.0, 7.0))
      painter.drawArc(QRectF(x - 3.5, y - 7.0, 7.0, 10.0), 0, 180 * 16)
    elif state == 'sandbox':
      painter.setPen(QPen(_OPEN, 1.6))
      painter.drawRect(QRectF(x - 5.0, y - 5.0, 10.0, 10.0))
    else:
      painter.setPen(QPen(_OPEN, 1.6))
      painter.drawEllipse(at, 5.0, 5.0)


class QuestPanel(PaintedWidget):
  """
  QuestPanel subclasses 'PaintedWidget' and is the list of quests: a row
  a quest, ticked when done, a ring when it may be played, a padlock
  when one before it is not done yet, in sections, the quests, the super
  quests and the computer, each under its heading saying how many are
  done, only the open section's rows shown, a click on a heading opening
  it; and the sandbox last, always open.
  A click on a row that may be played emits 'questChosen' with its
  index, the sandbox's -1. Under them 'startButton', 'Start over', puts
  the quest played back as it began; under that the quest played, its
  brief, how far it is from its goal, in words, and what it unlocks, or
  has unlocked.

  'showQuest' shows the progress, the quest played, the goal's words
  and whether it is reached.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(37, 38, 42)
  __fallback_panel_color__ = Color(37, 38, 42)
  __fallback_divider_color__ = Color(58, 61, 65)
  __fallback_panel_width__ = 320
  __fallback_side_margin__ = 16

  #  Private Variables
  __shown_progress__: Progress | None = None
  __shown_quest__: int | None = None
  __shown_words__: str = ''
  __hovered_row__: int | None = None
  __hovered_section__: int | None = None
  __open_section__: int = 0

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintPanel()
  questOp = PaintQuestPanel()
  reached = AttriBox[bool](False)
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(160, 164, 172),
  )
  headingFont = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.BOLD,
      11,
      Color(212, 212, 212),
  )
  startButton = AttriBox[ToolButton](THIS)

  #  Virtual Variables
  progress: Field[Progress] = Field()
  shown: Field[int] = Field()
  hovered: Field[int] = Field()
  hoveredSection: Field[int] = Field()
  openSection: Field[int] = Field()
  panelColor: Field[Color] = Field()
  dividerColor: Field[Color] = Field()

  #  Signals
  questChosen = Signal(int)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @progress.GET
  def _getProgress(self, ) -> Progress:
    """The 'progress' getter returns the progress shown."""
    if self.__shown_progress__ is None:
      self.__shown_progress__ = Progress()
    return self.__shown_progress__

  @shown.GET
  def _getShown(self, ) -> int | None:
    """The 'shown' getter returns the quest played, -1 for the sandbox,
    or 'None'."""
    return self.__shown_quest__

  @hovered.GET
  def _getHovered(self, ) -> int | None:
    """The 'hovered' getter returns the row under the mouse, or
    'None'."""
    return self.__hovered_row__

  @hoveredSection.GET
  def _getHoveredSection(self, ) -> int | None:
    """The 'hoveredSection' getter returns the heading under the mouse,
    or 'None'."""
    return self.__hovered_section__

  @openSection.GET
  def _getOpenSection(self, ) -> int:
    """The 'openSection' getter returns the section whose quests are
    shown, the others folded to their headings."""
    return self.__open_section__

  @panelColor.GET
  def _getPanelColor(self, ) -> Color:
    return self.__fallback_panel_color__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 640)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_panel_width__, 480)

  def resizeEvent(self, event: QResizeEvent) -> None:
    PaintedWidget.resizeEvent(self, event)
    self._place()

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """A click on the row of a quest that may be played, or of the
    sandbox, chooses it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    section = self.sectionAt(event.position())
    if section is not None:
      self.__open_section__ = section
      self._place()
      return self.update()
    row = self.rowAt(event.position())
    if row is not None and self.stateOf(row) != 'shut':
      self.questChosen.emit(row)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Lights the row under the mouse."""
    row = self.rowAt(event.position())
    section = self.sectionAt(event.position())
    if (row, section) != (self.__hovered_row__, self.__hovered_section__):
      self.__hovered_row__ = row
      self.__hovered_section__ = section
      self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.__hovered_row__ = None
    self.__hovered_section__ = None
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(QWidget)
  def __init__(self, parent: QWidget) -> None:
    PaintedWidget.__init__(self, parent)

  @overload()
  def __init__(self, ) -> None:
    PaintedWidget.__init__(self, )

  @overload.finalize
  def __init__(self, *args) -> None:
    self.setMouseTracking(True)
    self.startButton.text = 'Start over'
    self._place()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def showQuest(self, progress: Progress, quest: int | None, words: str,
                reached: bool) -> None:
    """The 'showQuest' method shows 'progress', the quest played,
    'quest', -1 the sandbox, how far it is from its goal, 'words', and
    whether it is 'reached'."""
    self.__shown_progress__ = progress
    if quest != self.__shown_quest__ and quest not in (None, SANDBOX):
      self.__open_section__ = sectionOf(quest)
      self._place()
    self.__shown_quest__ = quest
    self.__shown_words__ = words
    self.reached = True if reached else False
    self.startButton.setEnabled(True if quest is not None else False)
    self.update()

  def stateOf(self, row: int) -> str:
    """The 'stateOf' method returns the state of the row 'row': 'done',
    'open', 'shut', or 'sandbox'."""
    if row == SANDBOX:
      return 'sandbox'
    if self.progress.isDone(row):
      return 'done'
    return 'open' if self.progress.isOpen(row) else 'shut'

  def headingRect(self, section: int) -> QRectF:
    """The 'headingRect' method returns where the heading of 'section'
    is: after the headings before it and the rows of the open one."""
    margin = self.__fallback_side_margin__
    top = _TOP + section * _HEAD
    if section > self.openSection:
      _, first, after = SECTIONS[self.openSection]
      top += (after - first) * _ROW
    return QRectF(margin - 6.0, top, self.width() - 2 * margin + 12.0,
                  _HEAD - 2.0)

  def rowRect(self, row: int) -> QRectF | None:
    """The 'rowRect' method returns where the row 'row' is: under its
    section's heading if that is open, else 'None'; the sandbox's after
    every heading."""
    margin = self.__fallback_side_margin__
    _, first, after = SECTIONS[self.openSection]
    if row == SANDBOX:
      top = _TOP + len(SECTIONS) * _HEAD + (after - first) * _ROW
    elif sectionOf(row) == self.openSection:
      top = self.headingRect(self.openSection).top() + _HEAD
      top += (row - first) * _ROW
    else:
      return None
    return QRectF(margin - 6.0, top, self.width() - 2 * margin + 12.0,
                  _ROW - 2.0)

  def rowAt(self, pixel: QPointF) -> int | None:
    """The 'rowAt' method returns the row under 'pixel', or 'None'."""
    for row in (*range(len(QUESTS)), SANDBOX):
      box = self.rowRect(row)
      if box is not None and box.contains(pixel):
        return row
    return None

  def sectionAt(self, pixel: QPointF) -> int | None:
    """The 'sectionAt' method returns the heading under 'pixel', or
    'None'."""
    for section in range(len(SECTIONS)):
      if self.headingRect(section).contains(pixel):
        return section
    return None

  def textRect(self, ) -> QRectF:
    """The 'textRect' method returns where the quest played is said,
    under the button starting it over."""
    margin = self.__fallback_side_margin__
    top = self.startButton.y() + self.startButton.height() + 18.0
    return QRectF(margin, top, self.width() - 2 * margin,
                  max(self.height() - top - 16.0, 40.0))

  def title(self, ) -> str:
    """The 'title' method names the quest played."""
    quest = self.shown
    if quest is None:
      return 'Choose a quest'
    if quest == SANDBOX:
      return 'Sandbox'
    return QUESTS[quest].name

  def words(self, ) -> str:
    """The 'words' method says what the quest played asks, how far it is
    from it, and what it unlocks; for the sandbox, the parts to build
    with."""
    quest = self.shown
    if quest is None:
      return 'Click a quest to play it.'
    parts = ', '.join(map(kindName, self.progress.unlocked))
    if quest == SANDBOX:
      return ('Build anything with the parts unlocked: %s. Quests unlock '
              'more.' % parts)
    reward = ', '.join(map(kindName, QUESTS[quest].reward))
    lines = [QUESTS[quest].brief, '', self.__shown_words__, '']
    done = self.reached or self.progress.isDone(quest)
    if quest == len(QUESTS) - 1:
      lines.append('Done! You built a microprocessor from transistors up, '
                   'and programmed it.' if done else 'The last quest.')
    elif not reward:
      lines.append('Done!' if done else 'It unlocks nothing new: what you '
                                        'have is yours to program.')
    elif done:
      lines.append('Done! Unlocked: %s.' % reward)
    else:
      lines.append('Reaching it unlocks: %s.' % reward)
    lines += ['', 'To build with: %s.' % parts]
    return '\n'.join(lines)

  def dividerLine(self, ) -> tuple[QPointF, QPointF]:
    """The 'dividerLine' method returns the divider along the right,
    facing the circuit."""
    right = self.width() - 0.5
    return QPointF(right, 0.0), QPointF(right, float(self.height()))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, ) -> None:
    """Places 'Start over' under the rows."""
    margin = self.__fallback_side_margin__
    top = self.rowRect(SANDBOX).bottom() + 10.0
    height = self.startButton.sizeHint().height()
    self.startButton.setGeometry(margin, int(top),
                                 self.width() - 2 * margin, height)
