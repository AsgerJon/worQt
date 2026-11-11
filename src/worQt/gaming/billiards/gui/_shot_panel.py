"""
ShotPanel subclasses 'PaintedWidget' and is where a shot is set up and
the game is kept: the score, the referee's call, the choices the rules
give, the cue ball, the point struck on it, the power, and the shot.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.core.sentinels import THIS
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....engineering.gui import QuantitySlider, ToolButton
from ....paint_ops import AbstractPaintOp, PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from . import HitPicker

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QPaintEvent, QResizeEvent

  from ....utils import WPainter
  from ....utils.geom import Rect

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_RIGHT = Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | (
  Qt.TextFlag.TextWordWrap)
_MARGIN = 20  # pixels in from the panel's edges
_ROW = 22  # pixels a line of words takes
_GAP = 10  # pixels between parts


class PaintShotPanel(AbstractPaintOp):
  """
  PaintShotPanel subclasses 'AbstractPaintOp' and paints a 'ShotPanel':
  how the game stands; what each part sets; the point struck in words,
  while it may be set there; and how the shot is aimed.
  """

  #  Annotations
  widget: ShotPanel

  def paint(self, painter: WPainter, rect: Rect, e: QPaintEvent) -> Rect:
    """The 'paint' method paints the words between the controls."""
    widget = self.widget
    painter.fillRect(rect.Q, widget.paddingsColor.fillBrush)
    painter.setPen(widget.dividerColor.Q)
    painter.drawLine(QPointF(0.5, 0.0), QPointF(0.5, float(widget.height())))
    width = widget.width() - 2.0 * _MARGIN
    places = widget.places()
    painter.setFont(widget.font)
    painter.setPen(widget.font.color.Q)
    painter.drawText(QRectF(_MARGIN, places['status'], width, 2 * _ROW),
                     _WRAP, widget.status)
    painter.setPen(widget.dimColor.Q)
    labels = [('cueLabel', 'Cue ball'), ('lookLabel', 'Look from')]
    if widget.controlsLive():
      labels.append(('hitLabel', 'Point struck'))
    for name, text in labels:
      painter.drawText(QRectF(_MARGIN, places[name], width, _ROW), _LEFT,
                       text)
    if widget.controlsLive():
      painter.setPen(widget.font.color.Q)
      painter.drawText(QRectF(_MARGIN, places['hitWords'], width, _ROW),
                       _LEFT, widget.hitWords())
    painter.setPen(widget.dimColor.Q)
    painter.drawText(QRectF(_MARGIN, places['aimWords'], width, 3 * _ROW),
                     _WRAP, widget.aimWords())
    return rect


class ShotPanel(PaintedWidget):
  """
  ShotPanel subclasses 'PaintedWidget' and is where a shot is set up and
  the game kept, beside the table, top to bottom: the 'heading', the
  mode; in a game, the score, 'scoreRows', each a row of whether that
  player is to play, his name and ball, points, innings, average and
  best run; how the game stands, 'status'; the referee's last call,
  'callWords'; the choices the rules give now, shown by 'showChoices':
  'Break' or 'Let the other break' after a lag ('breakChosen'), 'Left
  spot' or 'Right spot' while the balls lie as a game opens, the cue
  ball on spot 4 or 5, on the left or the right of the head spot as the
  player breaking sees it ('spotChosen', 4 or 5; 'showSpot' lights the
  one it lies on), 'Respot' when the cue ball is frozen to another
  ('respotAsked'); the cue ball, 'White' or
  'Yellow', free in the sandbox ('cueFree'), 'cueChanged'; the ball the
  camera turns round, 'Look from' 'White', 'Yellow' or 'Red', always
  free, or the 'Ghost' while a mark is there ('setGhostAvailable'),
  'lookName', 'lookChanged', the cue ball again whenever the cue ball
  changes; the point struck, chosen on the ball's face, 'picker',
  'Centre' taking the middle again; the 'power'; the point struck and
  the power set here only while the full map shows ('setControlsLive',
  the user: in the regular view they show what the keys and the
  stroke's pull set, output only); 'ready' while a shot may be taken
  (the stroke is the only way one is, the user); '▸▸ Fast', held down
  to play the shot under way five times as fast ('fast'), greyed out
  while none is ('setFastAvailable'); and, while a game is at its lag,
  'Skip lag' ('skipAsked', 'setSkipAvailable'). The score, the
  heading and the referee's call are kept ('scoreRows', 'heading',
  'callWords') but shown on the club boards in the room, not here (the
  user: the GUI too cluttered).
  Looking from another ball than the cue ball, 'Mark' shows before
  '▸▸ Fast', 'markAsked': a dry run on that ball, as a player lays the
  cue on ball 2 to see the hit, greyed out unless 'ready'. In
  keglebillard the choice is who lays out ('setChooseWords'); before
  the lag 'To 400' steps the distance played to ('distanceAsked',
  'setDistance'); and with red in hand 'Place red' lets a drag put it
  down ('placeAsked', 'showPlacing').
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
  __fallback_call_color__ = Color(229, 192, 123)
  __fallback_width__ = 320  # pixels across
  __fallback_power__ = 2.0  # m/s the panel opens at
  __ball_colors__ = {
    'white': Color(242, 236, 217),
    'yellow': Color(245, 178, 27),
    'red': Color(224, 38, 45),
  }

  #  Private Variables
  __cue_name__: str = 'white'
  __look_name__: str = 'white'
  __controls_live__: bool = True
  __panel_heading__: str = 'Sandbox'
  __panel_status__: str = ''
  __panel_call__: str = ''
  __panel_rows__: tuple = ()
  __panel_choices__: tuple = ()
  __panel_kegler__: bool = False

  #  Public Variables
  boxModelOp = PaintBoxModel()
  panelOp = PaintShotPanel()
  breakButton = AttriBox[ToolButton](THIS)
  passButton = AttriBox[ToolButton](THIS)
  distanceButton = AttriBox[ToolButton](THIS)
  redButton = AttriBox[ToolButton](THIS)
  spotFourButton = AttriBox[ToolButton](THIS)
  spotFiveButton = AttriBox[ToolButton](THIS)
  respotButton = AttriBox[ToolButton](THIS)
  whiteButton = AttriBox[ToolButton](THIS)
  yellowButton = AttriBox[ToolButton](THIS)
  lookWhiteButton = AttriBox[ToolButton](THIS)
  lookYellowButton = AttriBox[ToolButton](THIS)
  lookRedButton = AttriBox[ToolButton](THIS)
  lookGhostButton = AttriBox[ToolButton](THIS)
  picker = AttriBox[HitPicker](THIS)
  centreButton = AttriBox[ToolButton](THIS)
  powerSlider = AttriBox[QuantitySlider](THIS)
  markButton = AttriBox[ToolButton](THIS)
  fastButton = AttriBox[ToolButton](THIS)
  skipButton = AttriBox[ToolButton](THIS)
  cueFree = AttriBox[bool](True)
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      11,
      Color(212, 212, 212),
  )

  #  Virtual Variables
  cueName: Field[str] = Field()
  lookName: Field[str] = Field()
  top: Field[float] = Field()
  side: Field[float] = Field()
  speed: Field[float] = Field()
  ready: Field[bool] = Field()
  heading: Field[str] = Field()
  status: Field[str] = Field()
  callWords: Field[str] = Field()
  scoreRows: Field[tuple] = Field()
  dividerColor: Field[Color] = Field()
  dimColor: Field[Color] = Field()
  fast: Field[bool] = Field()
  callColor: Field[Color] = Field()

  #  Signals
  skipAsked = Signal()
  markAsked = Signal()
  cueChanged = Signal(str)
  lookChanged = Signal(str)
  breakChosen = Signal(bool)
  spotChosen = Signal(int)
  respotAsked = Signal()
  distanceAsked = Signal()
  placeAsked = Signal()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cueName.GET
  def _getCueName(self, ) -> str:
    """The 'cueName' getter returns the cue ball's name."""
    return self.__cue_name__

  @lookName.GET
  def _getLookName(self, ) -> str:
    """The 'lookName' getter returns the name of the ball the camera
    turns round."""
    return self.__look_name__

  @top.GET
  def _getTop(self, ) -> float:
    """The 'top' getter returns how far up the point struck is, a share
    of the radius."""
    return self.picker.top

  @side.GET
  def _getSide(self, ) -> float:
    """The 'side' getter returns how far right the point struck is, a
    share of the radius."""
    return self.picker.side

  @speed.GET
  def _getSpeed(self, ) -> float:
    """The 'speed' getter returns the speed the ball sets off at, in
    mm/s."""
    return 1000.0 * self.powerSlider.quantity

  @ready.GET
  def _getReady(self, ) -> bool:
    """The 'ready' getter tells whether a shot may be taken, and so a
    mark made."""
    return True if self.markButton.isEnabled() else False

  @heading.GET
  def _getHeading(self, ) -> str:
    return self.__panel_heading__

  @status.GET
  def _getStatus(self, ) -> str:
    return self.__panel_status__

  @callWords.GET
  def _getCallWords(self, ) -> str:
    return self.__panel_call__

  @scoreRows.GET
  def _getScoreRows(self, ) -> tuple:
    return self.__panel_rows__

  @dividerColor.GET
  def _getDividerColor(self, ) -> Color:
    return self.__fallback_divider_color__

  @dimColor.GET
  def _getDimColor(self, ) -> Color:
    return self.__fallback_dim_color__

  @callColor.GET
  def _getCallColor(self, ) -> Color:
    return self.__fallback_call_color__

  @fast.GET
  def _getFast(self, ) -> bool:
    """The 'fast' getter tells whether the shot under way is played
    fast: while '▸▸ Fast' is held down."""
    button = self.fastButton
    return True if button.pressed and button.isEnabled() else False

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cueName.SET
  def _setCueName(self, name: str) -> None:
    """The 'cueName' setter makes the ball 'name' the cue ball, its
    button lit and the face painted its colour, and tells of it."""
    if name not in self.__ball_colors__:
      raise ValueError(name)
    changed = name != self.__cue_name__
    self.__cue_name__ = name
    self.whiteButton.checked = name == 'white'
    self.yellowButton.checked = name == 'yellow'
    self.whiteButton.update()
    self.yellowButton.update()
    self.picker.ballColor = self.colourOf(name)
    if changed:
      self.lookName = name
      self.cueChanged.emit(name)
    else:
      self._showMark()

  @lookName.SET
  def _setLookName(self, name: str) -> None:
    """The 'lookName' setter turns the camera round the ball 'name', its
    button lit, 'Mark' shown unless it is the cue ball, and tells of
    it."""
    if name not in ('white', 'yellow', 'red', 'ghost'):
      raise ValueError(name)
    if name == 'ghost' and not self.lookGhostButton.isEnabled():
      return
    changed = name != self.__look_name__
    self.__look_name__ = name
    for button, ball in ((self.lookWhiteButton, 'white'),
                         (self.lookYellowButton, 'yellow'),
                         (self.lookRedButton, 'red'),
                         (self.lookGhostButton, 'ghost')):
      button.checked = ball == name
      button.update()
    self._showMark()
    if changed:
      self.lookChanged.emit(name)

  @ready.SET
  def _setReady(self, ready: bool) -> None:
    """The 'ready' setter tells whether a shot may be taken, 'Mark'
    greyed out unless."""
    self.markButton.setEnabled(True if ready else False)
    self.markButton.update()

  @heading.SET
  def _setHeading(self, text: str) -> None:
    self.__panel_heading__ = text
    self.update()

  @status.SET
  def _setStatus(self, text: str) -> None:
    self.__panel_status__ = text
    self.update()

  @callWords.SET
  def _setCallWords(self, text: str) -> None:
    self.__panel_call__ = text
    self.update()

  @scoreRows.SET
  def _setScoreRows(self, rows: tuple) -> None:
    """The 'scoreRows' setter shows the score so, none outside a game,
    the parts below moving to make room."""
    self.__panel_rows__ = tuple(rows)
    self._place()
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(self.__fallback_width__, 800)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(self.__fallback_width__, 700)

  def resizeEvent(self, event: QResizeEvent) -> None:
    PaintedWidget.resizeEvent(self, event)
    self._place()

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
    texts = ((self.breakButton, 'Break'),
             (self.passButton, 'Let the other break'),
             (self.spotFourButton, 'Left spot'),
             (self.spotFiveButton, 'Right spot'),
             (self.respotButton, 'Respot'), (self.whiteButton, 'White'),
             (self.yellowButton, 'Yellow'), (self.lookWhiteButton, 'White'),
             (self.lookYellowButton, 'Yellow'),
             (self.lookRedButton, 'Red'), (self.lookGhostButton, 'Ghost'),
             (self.centreButton, 'Centre'),
             (self.markButton, 'Mark'), (self.fastButton, '▸▸ Fast'),
             (self.skipButton, 'Skip lag'),
             (self.distanceButton, 'To 400'),
             (self.redButton, 'Place red'))
    for button, text in texts:
      button.text = text
    self.powerSlider.text = 'Power'
    self.powerSlider.setScale(0.2, 10.0, 'm/s', 1)
    self.powerSlider.quantity = self.__fallback_power__
    self.whiteButton.clicked.connect(lambda: self.chooseCue('white'))
    self.yellowButton.clicked.connect(lambda: self.chooseCue('yellow'))
    self.lookWhiteButton.clicked.connect(lambda: self.chooseLook('white'))
    self.lookYellowButton.clicked.connect(
      lambda: self.chooseLook('yellow'))
    self.lookRedButton.clicked.connect(lambda: self.chooseLook('red'))
    self.lookGhostButton.clicked.connect(lambda: self.chooseLook('ghost'))
    self.centreButton.clicked.connect(self.picker.centre)
    self.markButton.clicked.connect(self.markAsked.emit)
    self.skipButton.clicked.connect(self.skipAsked.emit)
    self.breakButton.clicked.connect(lambda: self.breakChosen.emit(True))
    self.passButton.clicked.connect(lambda: self.breakChosen.emit(False))
    self.spotFourButton.clicked.connect(lambda: self.spotChosen.emit(4))
    self.spotFiveButton.clicked.connect(lambda: self.spotChosen.emit(5))
    self.respotButton.clicked.connect(self.respotAsked.emit)
    self.distanceButton.clicked.connect(self.distanceAsked.emit)
    self.redButton.clicked.connect(self.placeAsked.emit)
    self.picker.hitChanged.connect(lambda *_: self.update())
    self.chooseCue('white')
    self.chooseLook('white')
    self.setGhostAvailable(False)
    self.showChoices(())
    self.setFastAvailable(False)
    self.setSkipAvailable(False)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def chooseCue(self, name: str) -> None:
    """The 'chooseCue' method makes the ball 'name' the cue ball."""
    self.cueName = name

  def chooseLook(self, name: str) -> None:
    """The 'chooseLook' method turns the camera round the ball
    'name'."""
    self.lookName = name

  def setGhostAvailable(self, available: bool) -> None:
    """The 'setGhostAvailable' method lets the camera look from the
    ghost, a mark being there, or not; not, and looking from it, the
    camera looks from the cue ball again."""
    self.lookGhostButton.setEnabled(True if available else False)
    self.lookGhostButton.update()
    if not available and self.__look_name__ == 'ghost':
      self.lookName = self.__cue_name__

  def marking(self, ) -> bool:
    """The 'marking' method tells whether 'Mark' is there, another ball
    than the cue ball looked from."""
    return self.__look_name__ != self.__cue_name__

  def setCueFree(self, free: bool) -> None:
    """The 'setCueFree' method lets the cue ball be chosen, in the
    sandbox, or not, in a game, where the match says it."""
    self.cueFree = True if free else False
    self.whiteButton.setEnabled(self.cueFree)
    self.yellowButton.setEnabled(self.cueFree)

  def showChoices(self, choices: tuple) -> None:
    """The 'showChoices' method shows the choices the rules give now,
    any of 'choose', who breaks or lays out; 'spot', where; 'respot',
    the cue ball frozen; 'distance', how far a keglebillard match is
    played; 'red', red in hand put down; the others hidden."""
    self.__panel_choices__ = tuple(choices)
    shown = {self.breakButton: 'choose' in choices,
             self.passButton: 'choose' in choices,
             self.spotFourButton: 'spot' in choices,
             self.spotFiveButton: 'spot' in choices,
             self.respotButton: 'respot' in choices,
             self.distanceButton: 'distance' in choices,
             self.redButton: 'red' in choices}
    for button, visible in shown.items():
      button.setVisible(visible)
    self._place()
    self.update()

  def colourOf(self, name: str) -> Color:
    """The 'colourOf' method returns the colour of the ball 'name': in
    keglebillard the marked white, 'yellow', is white (the user)."""
    if self.__panel_kegler__ and name == 'yellow':
      return self.__ball_colors__['white']
    return self.__ball_colors__[name]

  def setKegler(self, kegler: bool) -> None:
    """The 'setKegler' method has the panel speak of keglebillard's
    balls, two whites, one marked, or of three-cushion's, white and
    yellow."""
    self.__panel_kegler__ = True if kegler else False
    words = 'Marked' if kegler else 'Yellow'
    self.yellowButton.text = words
    self.lookYellowButton.text = words
    self.picker.ballColor = self.colourOf(self.__cue_name__)
    self._place()
    self.update()

  def setChooseWords(self, take: str, give: str) -> None:
    """The 'setChooseWords' method words the lag winner's choice: to
    'take' the first shot, or to 'give' it to the other."""
    if (self.breakButton.text, self.passButton.text) == (take, give):
      return
    self.breakButton.text = take
    self.passButton.text = give
    self._place()
    self.update()

  def setDistance(self, distance: int) -> None:
    """The 'setDistance' method has the distance's button say the
    points a keglebillard match is played to."""
    words = 'To %d' % distance
    if self.distanceButton.text != words:
      self.distanceButton.text = words
      self._place()
      self.distanceButton.update()

  def showPlacing(self, placing: bool) -> None:
    """The 'showPlacing' method lights 'Place red' while a drag puts red
    down, in hand."""
    self.redButton.checked = True if placing else False
    self.redButton.update()

  def showSpot(self, number: int) -> None:
    """The 'showSpot' method lights 'Left spot' while the cue ball lies
    on spot 4, 'Right spot' while on spot 5, neither for any other."""
    self.spotFourButton.checked = number == 4
    self.spotFiveButton.checked = number == 5
    self.spotFourButton.update()
    self.spotFiveButton.update()

  def places(self, ) -> dict:
    """The 'places' method returns how far down each painted part is:
    the score, the status, the call, the cue ball's label, the point's
    label, its words, and the aim's words."""
    out = {}
    top = 16
    out['status'] = float(top)
    top += 2 * _ROW + _GAP
    out['choices'] = float(top)
    if self.__panel_choices__:
      top += self.breakButton.sizeHint().height() + _GAP
    out['cueLabel'] = float(top)
    top += _ROW
    out['cueButtons'] = float(top)
    top += self.whiteButton.sizeHint().height() + _GAP
    out['lookLabel'] = float(top)
    top += _ROW
    out['lookButtons'] = float(top)
    top += self.lookWhiteButton.sizeHint().height() + _GAP
    out['hitLabel'] = float(top)
    if self.__controls_live__:
      top += _ROW
    out['picker'] = float(top)
    if self.__controls_live__:
      top += self.picker.sizeHint().height() + 6
    out['hitWords'] = float(top)
    if self.__controls_live__:
      top += _ROW + 6
    out['power'] = float(top)
    if self.__controls_live__:
      top += self.powerSlider.sizeHint().height() + _GAP
    out['aimWords'] = float(top)
    top += 3 * _ROW + _GAP
    out['shoot'] = float(top)
    return out

  def setControlsLive(self, live: bool) -> None:
    """The 'setControlsLive' method shows the point struck, its words
    and 'Centre', and the power, to be set here, 'live', while the full
    map shows; else they are gone from the panel (the user: the GUI too
    cluttered), set by the keys and the stroke's pull alone."""
    live = True if live else False
    self.__controls_live__ = live
    for widget in (self.picker, self.centreButton, self.powerSlider):
      if not live:
        widget.clearFocus()
      widget.setVisible(live)
    self._place()
    self.update()

  def controlsLive(self, ) -> bool:
    """The 'controlsLive' method tells whether the point struck and the
    power may be set here ('setControlsLive')."""
    return self.__controls_live__

  def setFastAvailable(self, available: bool) -> None:
    """The 'setFastAvailable' method lets '▸▸ Fast' be held, while a
    shot is under way, or greys it out, let go."""
    button = self.fastButton
    if not available:
      button.pressed = False
    button.setEnabled(True if available else False)
    button.update()

  def setSkipAvailable(self, available: bool) -> None:
    """The 'setSkipAvailable' method shows 'Skip lag' beside '▸▸ Fast',
    while a game is at its lag, or hides it."""
    self.skipButton.setVisible(True if available else False)
    self._place()

  def hitWords(self, ) -> str:
    """The 'hitWords' method says the point struck: how far up or down
    and right or left of the middle, a share of the radius."""
    top, side = self.top, self.side
    if abs(top) < 0.005 and abs(side) < 0.005:
      return 'The middle: it slides off without spin'
    parts = []
    if abs(top) >= 0.005:
      way = 'up' if top > 0.0 else 'down'
      parts.append('%.2f R %s' % (abs(top), way))
    if abs(side) >= 0.005:
      way = 'right' if side > 0.0 else 'left'
      parts.append('%.2f R %s' % (abs(side), way))
    return ', '.join(parts)

  def aimWords(self, ) -> str:
    """The 'aimWords' method says how the shot is aimed, or what a mark
    shows."""
    if self.__look_name__ == 'ghost':
      return ('Facing the way the cue ball leaves the ball after the hit: '
              'turn the view to choose it, and the ghost moves to the hit.')
    if self.marking():
      return ('Turn round this ball the way it should go: Mark leaves a '
              'ghost where the cue ball must meet it.')
    if self.__controls_live__:
      return ('Set the point struck and the power here to see the shot '
              'on the map; strike it from the table.')
    return ('Hold the right button and pull back, the way the camera '
            'faces: the further, the harder; let go to strike. W A S D '
            'move the point struck meanwhile, the arrows any time.')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _place(self, ) -> None:
    """Places the parts top to bottom, as 'places' says."""
    places = self.places()
    width = max(self.width() - 2 * _MARGIN, 120)
    row = int(places['choices'])
    left = _MARGIN
    for button in (self.breakButton, self.passButton, self.spotFourButton,
                   self.spotFiveButton, self.respotButton,
                   self.distanceButton, self.redButton):
      if not self._shownChoice(button):
        continue
      size = button.sizeHint()
      button.setGeometry(left, row, size.width(), size.height())
      left += size.width() + 8
    row = int(places['cueButtons'])
    size = self.whiteButton.sizeHint()
    self.whiteButton.setGeometry(_MARGIN, row, size.width(), size.height())
    other = self.yellowButton.sizeHint()
    self.yellowButton.setGeometry(_MARGIN + size.width() + 8, row,
                                  other.width(), other.height())
    row, left = int(places['lookButtons']), _MARGIN
    for button in (self.lookWhiteButton, self.lookYellowButton,
                   self.lookRedButton, self.lookGhostButton):
      size = button.sizeHint()
      button.setGeometry(left, row, size.width(), size.height())
      left += size.width() + 6
    face = self.picker.sizeHint()
    row = int(places['picker'])
    self.picker.setGeometry(_MARGIN, row, face.width(), face.height())
    centre = self.centreButton.sizeHint()
    self.centreButton.setGeometry(_MARGIN + face.width() + 12, row,
                                  centre.width(), centre.height())
    height = self.powerSlider.sizeHint().height()
    self.powerSlider.setGeometry(_MARGIN, int(places['power']), width,
                                 height)
    mark = self.markButton.sizeHint()
    fast, skip = self.fastButton.sizeHint(), self.skipButton.sizeHint()
    row, left = int(places['shoot']), _MARGIN
    if not self.markButton.isHidden():
      self.markButton.setGeometry(left, row, mark.width(), mark.height())
      left += mark.width() + 8
    self.fastButton.setGeometry(left, row, fast.width(), mark.height())
    left += fast.width() + 8
    self.skipButton.setGeometry(left, row, skip.width(), mark.height())

  def _showMark(self, ) -> None:
    """Shows 'Mark' while another ball than the cue ball is looked from,
    else hides it."""
    self.markButton.setVisible(self.marking())
    self._place()
    self.markButton.update()
    self.update()

  def _shownChoice(self, button: ToolButton) -> bool:
    """Tells whether 'button' is among the choices shown now."""
    choices = self.__panel_choices__
    if button in (self.breakButton, self.passButton):
      return 'choose' in choices
    if button in (self.spotFourButton, self.spotFiveButton):
      return 'spot' in choices
    if button is self.distanceButton:
      return 'distance' in choices
    if button is self.redButton:
      return 'red' in choices
    return 'respot' in choices
