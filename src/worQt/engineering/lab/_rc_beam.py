"""
RCBeam is a beam of reinforced concrete, as cast for a test.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._bar_layer import BarLayer
from ._stirrups import Stirrups

_LEAST_GAP = 20.0  # mm: the least clear gap between bars side by side


class RCBeam(BaseObject):
  """
  RCBeam is a beam of reinforced concrete as cast for a test, in mm, N
  and MPa: 'length', 'height' and 'width'; its concrete's strength
  'fcm', the mean cylinder strength, as the concrete tested has it; its
  bars' yield strength 'fy' and modulus 'Es'; its 'bottom' and 'top'
  'BarLayer's, either of which may have no bars; and its 'stirrups',
  links round the bars every so far along it, but in the gaps left
  without, of the bars' steel.

  The rest of the concrete follows from 'fcm' by EN 1992-1-1, table 3.1:
  'fck' = fcm - 8, the modulus 'Ecm' = 22000 (fcm / 10)^0.3, the
  tensile strength 'fctm' = 0.3 fck^(2/3) (2.12 ln(1 + fcm / 10) above
  C50), the strain at the peak 'epsC1' = 0.7 fcm^0.31 per mille (at
  most 2.8) and where it crushes 'epsCu1' (3.5 per mille up to C50).
  The bars are of class B: they stretch 'epsUk' = 5 % before they
  snap, by when they are 'hardening' = 1.08 times as strong as at
  yield.

  The bars must fit: side by side with at least their diameter and
  20 mm between them and their cover at either side, and the two layers
  apart.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_dims__ = (3300.0, 300.0, 200.0)
  __fallback_materials__ = (38.0, 550.0, 200000.0)
  __fallback_bottom__ = BarLayer(3, 16.0, 30.0)
  __fallback_top__ = BarLayer(2, 10.0, 30.0)
  __fallback_stirrups__ = Stirrups(8.0, 150.0, ())
  __fallback_eps_uk__ = 0.05
  __fallback_hardening__ = 1.08

  #  Private Variables
  __beam_dims__: tuple[float, float, float] | None = None
  __beam_materials__: tuple[float, float, float] | None = None
  __beam_layers__: tuple[BarLayer, BarLayer] | None = None
  __beam_stirrups__: Stirrups | None = None

  #  Virtual Variables
  length: Field[float] = Field()
  height: Field[float] = Field()
  width: Field[float] = Field()
  fcm: Field[float] = Field()
  fy: Field[float] = Field()
  Es: Field[float] = Field()
  bottom: Field[BarLayer] = Field()
  top: Field[BarLayer] = Field()
  stirrups: Field[Stirrups] = Field()
  fck: Field[float] = Field()
  Ecm: Field[float] = Field()
  fctm: Field[float] = Field()
  epsC1: Field[float] = Field()
  epsCu1: Field[float] = Field()
  epsUk: Field[float] = Field()
  hardening: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getDims(self, ) -> tuple[float, float, float]:
    if self.__beam_dims__ is None:
      raise MissingVariable(self, '__beam_dims__', tuple)
    return self.__beam_dims__

  def _getMaterials(self, ) -> tuple[float, float, float]:
    if self.__beam_materials__ is None:
      raise MissingVariable(self, '__beam_materials__', tuple)
    return self.__beam_materials__

  def _getLayers(self, ) -> tuple[BarLayer, BarLayer]:
    if self.__beam_layers__ is None:
      raise MissingVariable(self, '__beam_layers__', tuple)
    return self.__beam_layers__

  @length.GET
  def _getLength(self, ) -> float:
    """The 'length' getter returns the beam's length, in mm."""
    return self._getDims()[0]

  @height.GET
  def _getHeight(self, ) -> float:
    """The 'height' getter returns the beam's height, in mm."""
    return self._getDims()[1]

  @width.GET
  def _getWidth(self, ) -> float:
    """The 'width' getter returns the beam's width, in mm."""
    return self._getDims()[2]

  @fcm.GET
  def _getFcm(self, ) -> float:
    """The 'fcm' getter returns the concrete's mean cylinder strength,
    in MPa."""
    return self._getMaterials()[0]

  @fy.GET
  def _getFy(self, ) -> float:
    """The 'fy' getter returns the bars' yield strength, in MPa."""
    return self._getMaterials()[1]

  @Es.GET
  def _getEs(self, ) -> float:
    """The 'Es' getter returns the bars' modulus, in MPa."""
    return self._getMaterials()[2]

  @bottom.GET
  def _getBottom(self, ) -> BarLayer:
    """The 'bottom' getter returns the bars along the bottom."""
    return self._getLayers()[0]

  @top.GET
  def _getTop(self, ) -> BarLayer:
    """The 'top' getter returns the bars along the top."""
    return self._getLayers()[1]

  @stirrups.GET
  def _getStirrups(self, ) -> Stirrups:
    """The 'stirrups' getter returns the links round the bars."""
    if self.__beam_stirrups__ is None:
      raise MissingVariable(self, '__beam_stirrups__', Stirrups)
    return self.__beam_stirrups__

  @fck.GET
  def _getFck(self, ) -> float:
    """The 'fck' getter returns the characteristic strength, fcm - 8."""
    return self.fcm - 8.0

  @Ecm.GET
  def _getEcm(self, ) -> float:
    """The 'Ecm' getter returns the concrete's modulus, in MPa."""
    return 22000.0 * (self.fcm / 10.0) ** 0.3

  @fctm.GET
  def _getFctm(self, ) -> float:
    """The 'fctm' getter returns the concrete's tensile strength, in
    MPa."""
    if self.fck <= 50.0:
      return 0.3 * max(self.fck, 0.0) ** (2.0 / 3.0)
    return 2.12 * math.log(1.0 + self.fcm / 10.0)

  @epsC1.GET
  def _getEpsC1(self, ) -> float:
    """The 'epsC1' getter returns the strain at the concrete's peak."""
    return min(0.7 * self.fcm ** 0.31, 2.8) / 1000.0

  @epsCu1.GET
  def _getEpsCu1(self, ) -> float:
    """The 'epsCu1' getter returns the strain the concrete crushes at."""
    if self.fck < 50.0:
      return 0.0035
    return (2.8 + 27.0 * ((98.0 - self.fcm) / 100.0) ** 4) / 1000.0

  @epsUk.GET
  def _getEpsUk(self, ) -> float:
    """The 'epsUk' getter returns the strain the bars snap at."""
    return self.__fallback_eps_uk__

  @hardening.GET
  def _getHardening(self, ) -> float:
    """The 'hardening' getter returns how many times stronger the bars
    are when they snap than at yield."""
    return self.__fallback_hardening__

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(%g x %g x %g, fcm %g, fy %g, bottom %s, top %s)"""
    return infoSpec % (type(self).__name__, self.length, self.height,
                       self.width, self.fcm, self.fy, self.bottom,
                       self.top)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(float, float, float, float, float, float, BarLayer, BarLayer,
            Stirrups)
  def __init__(
      self, length: float, height: float, width: float, fcm: float,
      fy: float, Es: float, bottom: BarLayer, top: BarLayer,
      stirrups: Stirrups,
  ) -> None:
    self._build((length, height, width), (fcm, fy, Es), (bottom, top))
    self._buildStirrups(stirrups)

  @overload(float, float, float, float, float, float, BarLayer, BarLayer)
  def __init__(
      self, length: float, height: float, width: float, fcm: float,
      fy: float, Es: float, bottom: BarLayer, top: BarLayer,
  ) -> None:
    self.__init__(length, height, width, fcm, fy, Es, bottom, top,
                  self.__fallback_stirrups__)

  @overload()
  def __init__(self, ) -> None:
    self._build(self.__fallback_dims__, self.__fallback_materials__,
                (self.__fallback_bottom__, self.__fallback_top__))
    self._buildStirrups(self.__fallback_stirrups__)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def values(self, ) -> tuple:
    """The 'values' method returns what the beam is made of, in the
    order its constructor takes them."""
    return (*self._getDims(), *self._getMaterials(), *self._getLayers(),
            self.stirrups)

  def withStirrups(self, stirrups: Stirrups) -> RCBeam:
    """The 'withStirrups' method returns the beam with 'stirrups'."""
    values = [*self.values()]
    values[8] = stirrups
    return RCBeam(*values)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _build(self, dims: tuple, materials: tuple, layers: tuple) -> None:
    """Sets what the beam is, each part checked."""
    names = ('length', 'height', 'width', 'fcm', 'fy', 'Es')
    for name, value in zip(names, (*dims, *materials)):
      if not value > 0:
        raise ValueError("""a beam's %s is more than 0, not %r"""
                         % (name, value))
    if materials[0] <= 8.0:
      raise ValueError('a concrete is stronger than 8 MPa')
    length, height, width = map(float, dims)
    if length < 4 * height:
      raise ValueError('a beam is at least 4 times as long as high')
    for layer in layers:
      self._checkLayer(layer, width)
    bottom, top = layers
    room = height - bottom.depth - top.depth
    room -= (bottom.diameter + top.diameter) / 2
    if bottom.count and top.count and room < _LEAST_GAP:
      raise ValueError('the bars at the top and the bottom must not meet')
    if bottom.count and bottom.depth + bottom.diameter / 2 > height:
      raise ValueError('the bottom bars must be inside the beam')
    self.__beam_dims__ = (length, height, width)
    self.__beam_materials__ = (*map(float, materials),)
    self.__beam_layers__ = (BarLayer(*bottom), BarLayer(*top))

  def _buildStirrups(self, stirrups: Stirrups) -> None:
    """Sets the stirrups, checked: a diameter of nought or more, a
    spacing of at least 50 mm, and each gap a stretch of the beam."""
    diameter, spacing, gaps = stirrups
    if diameter < 0:
      raise ValueError('stirrups have a diameter, or none, not %r'
                       % diameter)
    if spacing < 50.0:
      raise ValueError('stirrups are at least 50 mm apart, not %g'
                       % spacing)
    for start, end in gaps:
      if not 0 <= start < end <= self.length:
        infoSpec = """a gap in the stirrups is a stretch of the beam,
        not %g to %g mm"""
        raise ValueError(' '.join(infoSpec.split()) % (start, end))
    self.__beam_stirrups__ = Stirrups(float(diameter), float(spacing),
                                      (*[(float(start), float(end))
                                         for start, end in gaps],))

  @staticmethod
  def _checkLayer(layer: BarLayer, width: float) -> None:
    """Raises unless the bars of 'layer' fit side by side in 'width'."""
    count, diameter, cover = layer
    if count < 0 or int(count) != count:
      raise ValueError('a layer has a whole number of bars, not %r'
                       % count)
    if not count:
      return
    if not (diameter > 0 and cover > 0):
      raise ValueError('bars have a diameter and a cover')
    gap = max(diameter, _LEAST_GAP)
    needed = count * diameter + (count - 1) * gap + 2 * cover
    if needed > width:
      infoSpec = """%d Ø%g with cover %g need %g mm of width, not %g"""
      raise ValueError(infoSpec % (count, diameter, cover, needed, width))
