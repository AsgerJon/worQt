"""
TestReport is a test's results written to a PDF file.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import time
from typing import TYPE_CHECKING

from PySide6.QtCore import Qt, QPoint, QRectF
from PySide6.QtGui import QColor, QFont, QPageSize, QPainter, QPdfWriter
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .. import Cylinder, Lattice3D, LatticeBase, UniaxialTest

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from PySide6.QtWidgets import QWidget

_LEFT = Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
_WRAP = Qt.AlignmentFlag.AlignLeft | Qt.TextFlag.TextWordWrap


class TestReport(BaseObject):
  """
  TestReport is a test's results, of a 'cylinder' and its 'lattice',
  written to a PDF file. 'sections' are what it says, a heading to each
  and a label and a value to each line: the specimen, the lattice, the
  ingredients and the result; 'note' says plainly that the results are
  simulated, not measured. 'write' writes it on an A4 page, the
  cylinder and the stress-strain curve drawn below, as the widgets given
  show them.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_resolution__ = 200  # dots to an inch
  __fallback_margin__ = 18.0  # mm round the page
  __fallback_label_width__ = 34.0  # mm: the labels' column
  __fallback_note__ = (
    'Simulated from its ingredients by worQt: a lattice of the '
    'concrete\'s stones, paste and bond, loaded step by step as a '
    'testing machine loads a cylinder. It is not a measured result.')

  #  Private Variables
  __report_cylinder__: Cylinder | None = None
  __report_lattice__: LatticeBase | None = None
  __report_test__: UniaxialTest | None = None

  #  Virtual Variables
  cylinder: Field[Cylinder] = Field()
  lattice: Field[LatticeBase] = Field()
  test: Field[UniaxialTest] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @cylinder.GET
  def _getCylinder(self, ) -> Cylinder:
    """The 'cylinder' getter returns the cylinder reported on."""
    if self.__report_cylinder__ is None:
      raise MissingVariable(self, '__report_cylinder__', Cylinder)
    return self.__report_cylinder__

  @lattice.GET
  def _getLattice(self, ) -> LatticeBase:
    """The 'lattice' getter returns the lattice tested."""
    if self.__report_lattice__ is None:
      raise MissingVariable(self, '__report_lattice__', LatticeBase)
    return self.__report_lattice__

  @test.GET
  def _getTest(self, ) -> UniaxialTest:
    """The 'test' getter returns the test reported on."""
    if self.__report_test__ is None:
      raise MissingVariable(self, '__report_test__', UniaxialTest)
    return self.__report_test__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(Cylinder, LatticeBase, UniaxialTest)
  def __init__(
      self, cylinder: Cylinder, lattice: LatticeBase,
      test: UniaxialTest, ) -> None:
    self.__report_cylinder__ = cylinder
    self.__report_lattice__ = lattice
    self.__report_test__ = test

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def title(self, ) -> str:
    """The 'title' method names the test."""
    if self.test.direction < 0:
      return 'Compression test'
    return 'Tension test'

  def note(self, ) -> str:
    """The 'note' method says plainly that the results are simulated."""
    return self.__fallback_note__

  def sections(self, ) -> list[tuple[str, list[tuple[str, str]]]]:
    """The 'sections' method returns what the report says: a heading to
    each section, and a label and a value to each line."""
    return [
      ('Specimen', self._specimen()),
      ('Lattice', self._lattice()),
      ('Ingredients', self._ingredients()),
      ('Result', self._result()),
    ]

  def write(self, path: str, curve: QWidget, view: QWidget = None) -> None:
    """The 'write' method writes the report to a PDF file at 'path', the
    'curve' and the cylinder's 'view' drawn below the text as they
    show them."""
    writer = QPdfWriter(path)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(self.__fallback_resolution__)
    writer.setTitle('%s, cylinder %d' % (self.title(), self.cylinder.seed))
    writer.setCreator('worQt')
    painter = QPainter(writer)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    millimetre = self.__fallback_resolution__ / 25.4
    margin = self.__fallback_margin__ * millimetre
    width = writer.width() - 2 * margin
    top = self._writeText(painter, margin, margin, width, millimetre)
    bottom = writer.height() - margin - 16 * millimetre
    self._writeFigures(
      painter, QRectF(
        margin, top + 6 * millimetre, width,
        bottom - top - 6 * millimetre
        ),
      curve, view
      )
    painter.setFont(self._font(8.0, False))
    painter.setPen(QColor(90, 90, 90))
    painter.drawText(
      QRectF(
        margin, bottom + 2 * millimetre, width,
        14 * millimetre
        ), _WRAP, self.note()
      )
    painter.end()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _specimen(self, ) -> list[tuple[str, str]]:
    """What the cylinder is."""
    cylinder = self.cylinder
    grading = cylinder.grading
    share = 100 * cylinder.stoneVolume / cylinder.slabVolume
    return [
      ('Cylinder', 'Ø%g × %g mm' % (cylinder.diameter, cylinder.height)),
      (
        'Aggregate', 'graded up to %g mm, %.0f %% of the concrete, '
                     '%.0f %% of it passing %g mm' % (
          grading.maxSize, 100 * cylinder.aggregateFraction,
          100 * grading.passingAt(cylinder.smallest),
          cylinder.smallest
        )
      ),
      (
        'Stones', '%d from %g mm up, %.1f %% of the concrete by volume' % (
        len(cylinder.stones), cylinder.smallest, share
      )
      ),
      ('Cast', 'seed %d' % cylinder.seed),
    ]

  def _lattice(self, ) -> list[tuple[str, str]]:
    """What the lattice is."""
    lattice = self.lattice
    if isinstance(lattice, Lattice3D):
      where = 'the whole cylinder, in space'
    else:
      where = 'the section through the axis, in the plane'
    return [
      ('Of', where),
      (
        'Cells', '%d, at least %g mm apart' % (
        lattice.nodeCount,
        lattice.spacing
      )
      ),
      ('Springs', '%d' % len(lattice.phases)),
    ]

  def _ingredients(self, ) -> list[tuple[str, str]]:
    """What the concrete is made of, as the test had it."""
    stone, paste, bond = self.test.materials
    return [
      (
        'Stone', 'E %.0f GPa, ft %.1f MPa, Gf %.0f N/m' % (
        stone.stiffness / 1000, stone.tension, stone.toughness * 1000
      )
      ),
      (
        'Paste', 'E %.0f GPa, ft %.1f MPa, Gf %.0f N/m, c %.1f MPa, '
                 'μ %.2f' % (
          paste.stiffness / 1000, paste.tension,
          paste.toughness * 1000, paste.cohesion,
          paste.friction
        )
      ),
      (
        'Bond', 'ft %.1f MPa, Gf %.0f N/m' % (
        bond.tension,
        bond.toughness * 1000
      )
      ),
    ]

  def _result(self, ) -> list[tuple[str, str]]:
    """What came out."""
    test = self.test
    if test.finished:
      state = 'finished after %d steps' % test.step
    else:
      state = 'stopped after %d steps, unfinished' % test.step
    name = 'fc' if test.direction < 0 else 'ft'
    strength = '%s = %.3g MPa at %.3g ‰' % (
      name, test.strength,
      test.strengthStrain * 1e3
    )
    return [
      ('Test', self.title()),
      ('State', state),
      ('Strength', strength),
      ('Stiffness', 'E = %.3g GPa' % (test.stiffness / 1e3)),
      (
        'Cracked faces', '%d at the strength, %d at the end' % (
        test.strengthCracks, test.crackedCount
      )
      ),
      ('Reckoned on', test.device),
    ]

  @staticmethod
  def _font(points: float, bold: bool) -> QFont:
    """A plain font of 'points'."""
    font = QFont('Sans')
    font.setPointSizeF(points)
    font.setBold(bold)
    return font

  def _writeText(
      self, painter: QPainter, left: float, top: float,
      width: float, millimetre: float, ) -> float:
    """Writes the title and the sections from 'top' down, and returns
    where the text ends."""
    painter.setPen(QColor(20, 20, 20))
    painter.setFont(self._font(17.0, True))
    line = 9 * millimetre
    painter.drawText(QRectF(left, top, width, line), _LEFT, self.title())
    top += line
    painter.setFont(self._font(9.0, False))
    painter.setPen(QColor(90, 90, 90))
    stamp = 'Cylinder %d, %s' % (
      self.cylinder.seed,
      time.strftime('%Y-%m-%d %H:%M')
    )
    painter.drawText(
      QRectF(left, top, width, 6 * millimetre), _LEFT,
      stamp
      )
    top += 9 * millimetre
    labels = self.__fallback_label_width__ * millimetre
    for heading, rows in self.sections():
      painter.setPen(QColor(20, 20, 20))
      painter.setFont(self._font(11.0, True))
      painter.drawText(
        QRectF(left, top, width, 7 * millimetre), _LEFT,
        heading
        )
      top += 7 * millimetre
      painter.setFont(self._font(9.5, False))
      for label, value in rows:
        painter.setPen(QColor(90, 90, 90))
        painter.drawText(
          QRectF(left, top, labels, 5.5 * millimetre),
          _LEFT, label
          )
        painter.setPen(QColor(20, 20, 20))
        painter.drawText(
          QRectF(
            left + labels, top, width - labels,
            5.5 * millimetre
            ), _LEFT, value
          )
        top += 5.5 * millimetre
      top += 3 * millimetre
    return top

  @staticmethod
  def _writeFigures(
      painter: QPainter, room: QRectF, curve: QWidget,
      view: QWidget | None, ) -> None:
    """Draws the cylinder at the left of 'room' and the curve at its
    right, each scaled to fit as its widget shows it."""
    figures = [widget for widget in (view, curve) if widget is not None]
    gap = 0.03 * room.width()
    widths = [widget.width() for widget in figures]
    heights = [widget.height() for widget in figures]
    scale = min(
      (room.width() - gap * (len(figures) - 1)) / sum(widths),
      room.height() / max(heights)
      )
    left = room.left()
    for widget in figures:
      painter.save()
      painter.translate(left, room.top())
      painter.scale(scale, scale)
      widget.render(painter, QPoint(0, 0))
      painter.restore()
      left += widget.width() * scale + gap
