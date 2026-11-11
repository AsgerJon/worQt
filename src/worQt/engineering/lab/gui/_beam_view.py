"""
BeamView subclasses 'PaintedWidget' and shows a beam on its rig, as the
lab sees it, and moves the rig's parts by dragging them.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPointF, QRectF, QSize, Signal
from PySide6.QtWidgets import QWidget
from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload

from ....paint_ops import PaintBoxModel
from ....utils import WFont, Color
from ....utils.font_nums import GenericFamilyNum, FontWeightNum
from ....utils.geom import InSets, Size
from ....widgets import PaintedWidget
from ...gui import CRACK_LEAST
from .. import Actuator, BeamExperiment, RCBeam, Rig, Support
from ._paint_beam import PaintBeam

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtGui import QKeyEvent, QMouseEvent
  from PySide6.QtCore import QEvent

_ROOM_ABOVE = 150.0  # pixels over the beam, at least: the actuators
_FLOOR = 112.0  # pixels under the beam: the strong floor
_UNDER_FLOOR = 26.0  # pixels under the floor: the cracks' scale
_SIDES = 40.0  # pixels either side of the beam
_SNAP = 10.0  # mm the rig's parts are dragged to
_GRIP = 16.0  # pixels: how near a part must be to be taken hold of


class BeamView(PaintedWidget):
  """
  BeamView subclasses 'PaintedWidget' and shows the 'beam' on its 'rig'
  as the lab sees it, to scale and at its true deflection: its supports
  on the strong floor, pins, rollers and clamps; its actuators hung
  from the frame above, each pushing the beam through a plate, the one
  the control drives named so and each other with the share of the
  force it follows; and the transducers under it, each reading how far
  the beam has moved down, the one the control reads named so; the bars
  inside the beam, the cracks as they open from the face pulled,
  coloured by how wide they are, and the concrete where it crushes.

  A click selects a part of the rig, 'selected' ('support', 'actuator'
  or 'transducer' and its index), emitting 'selectionChanged' with it,
  or with 'None' for a click on nothing. Before a test, a part is moved
  by dragging it along the beam, to the centimetre, emitting
  'rigEdited' with the rig moved; nothing moves where the rig would not
  fit the beam. Delete removes the part selected, emitting 'rigEdited',
  or 'refused' with why it cannot be. While the 'experiment' runs, or
  after, nothing moves.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_margins_dims__ = InSets(0, 0, 0, 0)
  __fallback_borders_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_dims__ = InSets(0, 0, 0, 0)
  __fallback_paddings_color__ = Color(30, 31, 34)
  __fallback_concrete_color__ = Color(120, 122, 126)
  __fallback_edge_color__ = Color(170, 172, 176)
  __fallback_steel_color__ = Color(86, 156, 214)
  __fallback_rig_color__ = Color(150, 154, 162)
  __fallback_accent_color__ = Color(229, 192, 123)
  __fallback_control_color__ = Color(152, 195, 121)
  __fallback_crushed_color__ = Color(190, 60, 60)
  __fallback_text_color__ = Color(170, 174, 182)

  #  Private Variables
  __shown_beam__: RCBeam | None = None
  __shown_rig__: Rig | None = None
  __shown_test__: BeamExperiment | None = None
  __selected_part__: tuple[str, int] | None = None
  __held_part__: tuple[str, int] | None = None
  __hovered_part__: tuple[str, int] | None = None

  #  Public Variables
  boxModelOp = PaintBoxModel()
  beamOp = PaintBeam()
  font = AttriBox[WFont](
      GenericFamilyNum.SANS,
      FontWeightNum.NORMAL,
      10,
      Color(170, 174, 182),
  )

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  rig: Field[Rig] = Field()
  experiment: Field[BeamExperiment] = Field()
  selected: Field[tuple[str, int]] = Field()
  editable: Field[bool] = Field()
  held: Field[tuple[str, int]] = Field()
  hovered: Field[tuple[str, int]] = Field()
  concreteColor: Field[Color] = Field()
  edgeColor: Field[Color] = Field()
  steelColor: Field[Color] = Field()
  rigColor: Field[Color] = Field()
  accentColor: Field[Color] = Field()
  controlColor: Field[Color] = Field()
  crushedColor: Field[Color] = Field()
  textColor: Field[Color] = Field()

  #  Signals
  rigEdited = Signal(object)
  beamEdited = Signal(object)
  selectionChanged = Signal(object)
  refused = Signal(str)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam shown, the standard one until
    another is set."""
    if self.__shown_beam__ is None:
      self.__shown_beam__ = RCBeam()
    return self.__shown_beam__

  @rig.GET
  def _getRig(self, ) -> Rig:
    """The 'rig' getter returns the rig shown, the standard one until
    another is set."""
    if self.__shown_rig__ is None:
      self.__shown_rig__ = Rig.standard(self.beam)
    return self.__shown_rig__

  @experiment.GET
  def _getExperiment(self, ) -> BeamExperiment | None:
    """The 'experiment' getter returns the test shown, or 'None'."""
    return self.__shown_test__

  @selected.GET
  def _getSelected(self, ) -> tuple[str, int] | None:
    """The 'selected' getter returns the part selected, or 'None'."""
    return self.__selected_part__

  @editable.GET
  def _getEditable(self, ) -> bool:
    """The 'editable' getter tells whether the rig may be changed:
    before a test."""
    return True if self.experiment is None else False

  @held.GET
  def _getHeld(self, ) -> tuple[str, int] | None:
    """The 'held' getter returns the part being dragged, or 'None'."""
    return self.__held_part__

  @hovered.GET
  def _getHovered(self, ) -> tuple[str, int] | None:
    """The 'hovered' getter returns the part under the mouse, or
    'None'."""
    return self.__hovered_part__

  @concreteColor.GET
  def _getConcreteColor(self, ) -> Color:
    return self.__fallback_concrete_color__

  @edgeColor.GET
  def _getEdgeColor(self, ) -> Color:
    return self.__fallback_edge_color__

  @steelColor.GET
  def _getSteelColor(self, ) -> Color:
    return self.__fallback_steel_color__

  @rigColor.GET
  def _getRigColor(self, ) -> Color:
    return self.__fallback_rig_color__

  @accentColor.GET
  def _getAccentColor(self, ) -> Color:
    return self.__fallback_accent_color__

  @controlColor.GET
  def _getControlColor(self, ) -> Color:
    return self.__fallback_control_color__

  @crushedColor.GET
  def _getCrushedColor(self, ) -> Color:
    return self.__fallback_crushed_color__

  @textColor.GET
  def _getTextColor(self, ) -> Color:
    return self.__fallback_text_color__

  def _getRequiredSize(self, ) -> Size:
    """The content size for the box model: the whole view."""
    return Size(self.paintView.width, self.paintView.height)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @beam.SET
  def _setBeam(self, beam: RCBeam) -> None:
    """The 'beam' setter shows 'beam', letting go of a selected gap in
    its stirrups gone."""
    self.__shown_beam__ = beam
    selected = self.__selected_part__
    if selected is not None and selected[0] == 'gap':
      if selected[1] >= len(beam.stirrups.gaps):
        self.select(None)
    self.update()

  @rig.SET
  def _setRig(self, rig: Rig) -> None:
    """The 'rig' setter shows 'rig', letting go of a selection gone."""
    self.__shown_rig__ = rig
    if self.__selected_part__ is not None:
      kind, index = self.__selected_part__
      if index >= len(self._partsOf(kind)):
        self.select(None)
    self.update()

  @experiment.SET
  def _setExperiment(self, experiment: BeamExperiment | None) -> None:
    """The 'experiment' setter shows 'experiment', or no test for
    'None'; a test shows its own beam and rig."""
    self.__shown_test__ = experiment
    if experiment is not None:
      self.__shown_beam__ = experiment.beam
      self.__shown_rig__ = experiment.rig
      self.__held_part__ = None
      self.__hovered_part__ = None
    self.update()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PySide6 API  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def sizeHint(self, ) -> QSize:
    return QSize(900, 500)

  def minimumSizeHint(self, ) -> QSize:
    return QSize(480, 400)

  def mousePressEvent(self, event: QMouseEvent) -> None:
    """Selects the part under the mouse and takes hold of it."""
    if event.button() != Qt.MouseButton.LeftButton:
      return PaintedWidget.mousePressEvent(self, event)
    part = self.partAt(event.position())
    self.select(part)
    if self.editable:
      self.__held_part__ = part
    self.update()

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    """Drags the part held along the beam, or marks the part under the
    mouse."""
    point = event.position()
    if self.__held_part__ is not None:
      self.drag(self.__held_part__, self.toBeam(point.x()))
      return
    hovered = self.partAt(point)
    if hovered != self.__hovered_part__:
      self.__hovered_part__ = hovered
      shape = Qt.CursorShape.ArrowCursor
      if hovered is not None and self.editable:
        shape = Qt.CursorShape.SizeHorCursor
      self.setCursor(shape)
      self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    """Lets go of the part held."""
    self.__held_part__ = None
    self.update()

  def leaveEvent(self, event: QEvent) -> None:
    self.__hovered_part__ = None
    self.update()

  def keyPressEvent(self, event: QKeyEvent) -> None:
    """Delete removes the part selected."""
    if event.key() in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
      self.removeSelected()
      return
    PaintedWidget.keyPressEvent(self, event)

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
    self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def scale(self, ) -> float:
    """The 'scale' method returns the pixels to a millimetre."""
    beam = self.beam
    across = (self.width() - 2 * _SIDES) / beam.length
    room = self.height() - _ROOM_ABOVE - _FLOOR - _UNDER_FLOOR
    return max(min(across, room / beam.height), 1e-3)

  def floor(self, ) -> float:
    """The 'floor' method returns where the strong floor is, near the
    bottom: the beam stands on it, the room above it the actuators'."""
    return self.height() - _UNDER_FLOOR

  def beamRect(self, ) -> QRectF:
    """The 'beamRect' method returns where the beam is at rest."""
    beam, scale = self.beam, self.scale()
    width, height = beam.length * scale, beam.height * scale
    bottom = self.floor() - _FLOOR
    return QRectF(
      (self.width() - width) / 2, bottom - height, width,
      height
      )

  def toScreen(self, x: float, y: float) -> QPointF:
    """The 'toScreen' method returns the pixel of the point 'x' along
    the beam and 'y' up from its underside, in mm, where the beam has
    moved it."""
    box, scale = self.beamRect(), self.scale()
    down = self.deflectionAt(x)
    return QPointF(
      box.left() + x * scale,
      box.bottom() - (y - down) * scale
      )

  def toBeam(self, x: float) -> float:
    """The 'toBeam' method returns how far along the beam the pixel
    column 'x' is, in mm."""
    return (x - self.beamRect().left()) / self.scale()

  def deflectionAt(self, x: float) -> float:
    """The 'deflectionAt' method returns how far the beam has moved down
    at 'x', in mm: between its nodes as a straight line."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return 0.0
    nodes = experiment.nodes
    deflections = experiment.latest.deflections
    if x <= nodes[0]:
      return deflections[0]
    for index in range(len(nodes) - 1):
      left, right = nodes[index], nodes[index + 1]
      if x <= right:
        share = (x - left) / (right - left)
        return (deflections[index] * (1 - share)
                + deflections[index + 1] * share)
    return deflections[-1]

  def cracks(self, ) -> list[tuple[float, float, float, float]]:
    """The 'cracks' method returns each crack open on the beam's face:
    where its middle is along and up the beam, in mm, the way it runs,
    in radians from along the beam, square to the strain pulling it
    open, and how wide it is, in mm: the stretch past what the concrete
    takes over the size of its cell."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return []
    beam, mesh = self.beam, experiment.mesh
    xs, ys = mesh.xs, mesh.ys
    nx = len(xs) - 1
    found = []
    for index, (most, pull, _) in enumerate(experiment.latest.cells):
      i, j = index % nx, index // nx
      cracking = mesh.cellStrength(i, j) / beam.Ecm
      size = math.sqrt((xs[i + 1] - xs[i]) * (ys[j + 1] - ys[j]))
      width = (most - cracking) * size
      if width < CRACK_LEAST:
        continue
      found.append(((xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2,
                    pull + math.pi / 2, width))
    return found

  def crushed(self, ) -> list[tuple[float, float, float, float]]:
    """The 'crushed' method returns each cell of the face where the
    concrete has crushed: from and to where it is along the beam, and
    from and to how high, in mm."""
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return []
    limit = -self.beam.epsCu1
    xs, ys = experiment.mesh.xs, experiment.mesh.ys
    nx = len(xs) - 1
    found = []
    for index, (_, _, least) in enumerate(experiment.latest.cells):
      if least <= limit:
        i, j = index % nx, index // nx
        found.append((xs[i], xs[i + 1], ys[j], ys[j + 1]))
    return found

  def stirrups(self, ) -> list[tuple[float, float]]:
    """The 'stirrups' method returns each stirrup: where it stands along
    the beam, and how far it is stretched, as a share of its yield, at
    the latest reading."""
    beam = self.beam
    experiment = self.experiment
    if experiment is None or not experiment.readings:
      return [(x, 0.0) for x in beam.stirrups.places(beam.length)]
    yields = beam.fy / beam.Es
    strains = experiment.latest.stirrups
    return [(x, strain / yields) for x, strain
            in zip(experiment.mesh.stirrupPlaces, strains)]

  def parts(self, ) -> list[tuple[tuple[str, int], QRectF]]:
    """The 'parts' method returns the parts that can be taken hold of,
    each with where it is on screen: the gaps in the stirrups, the
    supports, the actuators and the transducers."""
    rig, box = self.rig, self.beamRect()
    found = []
    for index, (start, end) in enumerate(self.beam.stirrups.gaps):
      left = self.toScreen(start, 0.0).x()
      right = self.toScreen(end, 0.0).x()
      found.append((('gap', index),
                    QRectF(left, box.top() + 0.3 * box.height(),
                           right - left, 0.4 * box.height())))
    for index, support in enumerate(rig.supports):
      point = self.toScreen(support.at, 0.0)
      found.append((('support', index),
                    QRectF(point.x() - _GRIP, box.bottom(), 2 * _GRIP,
                           36.0)))
    for index, actuator in enumerate(rig.actuators):
      point = self.toScreen(actuator.at, self.beam.height)
      found.append((('actuator', index),
                    QRectF(point.x() - _GRIP, point.y() - 120.0,
                           2 * _GRIP, 120.0)))
    for index, x in enumerate(rig.transducers):
      point = self.toScreen(x, 0.0)
      found.append((('transducer', index),
                    QRectF(point.x() - _GRIP, box.bottom() + 40.0,
                           2 * _GRIP, 70.0)))
    return found

  def partAt(self, point: QPointF) -> tuple[str, int] | None:
    """The 'partAt' method returns the part at 'point', or 'None'."""
    for part, rect in reversed(self.parts()):
      if rect.contains(point):
        return part
    return None

  def partName(self, part: tuple[str, int]) -> str:
    """The 'partName' method names 'part' as the lab does: 'Support 1',
    'A2', 'T3' or 'Gap 1'."""
    kind, index = part
    names = {'support': 'Support %d', 'actuator': 'A%d',
             'transducer': 'T%d', 'gap': 'Gap %d'}
    return names[kind] % (index + 1)

  def drag(self, part: tuple[str, int], x: float) -> None:
    """The 'drag' method moves 'part' to 'x' along the beam, to the
    centimetre, if it fits there: a part of the rig emitting
    'rigEdited' with the rig moved, a gap in the stirrups, moved whole,
    its middle to 'x', 'beamEdited' with the beam so."""
    if not self.editable:
      return
    x = round(x / _SNAP) * _SNAP
    if part[0] == 'gap':
      return self._dragGap(part[1], x)
    try:
      moved = self.movedTo(self.rig, part, x)
      moved.check(self.beam)
    except ValueError:
      return
    self.rig = moved
    self.rigEdited.emit(moved)

  @staticmethod
  def movedTo(rig: Rig, part: tuple[str, int], x: float) -> Rig:
    """The 'movedTo' method returns 'rig' with 'part' moved to 'x'."""
    kind, index = part
    if kind == 'support':
      supports = [*rig.supports]
      supports[index] = Support(x, supports[index].kind)
      return rig.withSupports(*supports)
    if kind == 'actuator':
      actuators = [*rig.actuators]
      old = actuators[index]
      actuators[index] = Actuator(x, old.follows, old.share)
      return rig.withActuators(*actuators)
    transducers = [*rig.transducers]
    transducers[index] = x
    return rig.withTransducers(*transducers)

  def select(self, part: tuple[str, int] | None) -> None:
    """The 'select' method selects 'part', or none for 'None', and emits
    'selectionChanged'."""
    if part == self.__selected_part__:
      return
    self.__selected_part__ = part
    self.selectionChanged.emit(part)
    self.update()

  def removeSelected(self, ) -> None:
    """The 'removeSelected' method removes the part selected, before a
    test: a gap in the stirrups, filled, emitting 'beamEdited'; a part
    of the rig, if the rig still fits the beam, emitting 'rigEdited',
    else 'refused' with why."""
    part = self.__selected_part__
    if part is None or not self.editable:
      return
    kind, index = part
    if kind == 'gap':
      beam = self.beam
      self.select(None)
      self.beam = beam.withStirrups(beam.stirrups.withoutGap(index))
      self.beamEdited.emit(self.beam)
      return
    rig = self.rig
    try:
      if kind == 'support':
        removed = rig.withoutSupport(index)
      elif kind == 'actuator':
        removed = rig.withoutActuator(index)
      else:
        removed = rig.withoutTransducer(index)
      removed.check(self.beam)
    except ValueError as exception:
      self.refused.emit('%s stays: %s.' % (self.partName(part),
                                           exception))
      return
    self.select(None)
    self.rig = removed
    self.rigEdited.emit(removed)

  def _dragGap(self, index: int, x: float) -> None:
    """Moves the gap of 'index' whole, its middle to 'x', kept on the
    beam."""
    beam = self.beam
    start, end = beam.stirrups.gaps[index]
    half = (end - start) / 2
    middle = min(max(x, half), beam.length - half)
    gaps = beam.stirrups.withGapAt(index, middle - half, middle + half)
    self.beam = beam.withStirrups(gaps)
    self.beamEdited.emit(self.beam)

  def _partsOf(self, kind: str) -> tuple:
    """The parts of 'kind'."""
    rig = self.rig
    if kind == 'support':
      return rig.supports
    if kind == 'actuator':
      return rig.actuators
    if kind == 'gap':
      return self.beam.stirrups.gaps
    return rig.transducers
