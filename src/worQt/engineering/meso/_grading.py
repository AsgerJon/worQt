"""
Grading is the grading curve of an aggregate, its 'kornkurve': the share
of it, by volume, passing each sieve.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

import torch
from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from numpy.random import Generator

#  The standard sieves, in mm, as EN 933-2 and ISO 565 have them
SIEVES = (
  0.063, 0.125, 0.25, 0.5, 1.0, 2.0, 4.0, 5.6, 8.0, 11.2, 16.0,
  22.4, 31.5, 45.0, 63.0
)
_BATCH = 256  # stones drawn at a time while a size class fills


class Grading(BaseObject):
  """
  Grading is the grading curve of an aggregate, its 'kornkurve': the
  'sieves', in mm, rising, and the share of the aggregate, by volume,
  'passing' each, never falling, all of it passing the last, which is
  the largest size, 'maxSize'. It is any sieve table, as read off a
  datasheet; 'fuller' makes Fuller's curve, (d / D) ** q at the standard
  sieves.

  Between two sieves the curve runs straight on log-log paper, as a
  datasheet's curve is drawn, so a power law such as Fuller's is exact
  between its sieves too, and below the finest sieve it carries on as it
  runs from it; 'passingAt' reads it at any size.

  'sample' draws the sizes of the stones of a volume of aggregate from
  a smallest size up: each size class between two sieves filled to the
  share of the volume the curve gives it, its sizes spread as the curve
  runs through it, largest first, the order stones are placed in.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __grading_sieves__: tuple[float, ...] | None = None
  __grading_passing__: tuple[float, ...] | None = None

  #  Virtual Variables
  sieves: Field[tuple[float, ...]] = Field()
  passing: Field[tuple[float, ...]] = Field()
  maxSize: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @sieves.GET
  def _getSieves(self, ) -> tuple[float, ...]:
    """The 'sieves' getter returns the sieves, in mm, rising."""
    if self.__grading_sieves__ is None:
      raise MissingVariable(self, '__grading_sieves__', tuple)
    return self.__grading_sieves__

  @passing.GET
  def _getPassing(self, ) -> tuple[float, ...]:
    """The 'passing' getter returns the share passing each sieve."""
    if self.__grading_passing__ is None:
      raise MissingVariable(self, '__grading_passing__', tuple)
    return self.__grading_passing__

  @maxSize.GET
  def _getMaxSize(self, ) -> float:
    """The 'maxSize' getter returns the largest size, the last sieve."""
    return self.sieves[-1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple)
  def __init__(self, sieves: tuple, passing: tuple) -> None:
    sieves = (*[float(sieve) for sieve in sieves],)
    passing = (*[float(share) for share in passing],)
    self._checkTable(sieves, passing)
    self.__grading_sieves__ = sieves
    self.__grading_passing__ = passing

  @classmethod
  def fuller(cls, maxSize: float, exponent: float) -> Grading:
    """The 'fuller' method returns Fuller's curve up to 'maxSize':
    (d / maxSize) ** exponent passing the sieve of d, at the standard
    sieves below 'maxSize' and at 'maxSize' itself."""
    maxSize = float(maxSize)
    sieves = (*[sieve for sieve in SIEVES if sieve < maxSize], maxSize)
    passing = [(sieve / maxSize) ** exponent for sieve in sieves]
    return cls(sieves, (*passing[:-1], 1.0))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def passingAt(self, size: float) -> float:
    """The 'passingAt' method returns the share passing a sieve of
    'size', read straight on log-log paper between the sieves."""
    sieves, passing = self.sieves, self.passing
    if size >= sieves[-1]:
      return 1.0
    index = 0
    while index < len(sieves) - 2 and size > sieves[index + 1]:
      index += 1
    low, high = sieves[index], sieves[index + 1]
    lowShare, highShare = passing[index], passing[index + 1]
    if lowShare <= 0.0:
      if size <= low:
        return 0.0
      return highShare * (size - low) / (high - low)
    exponent = math.log(highShare / lowShare) / math.log(high / low)
    return lowShare * (size / low) ** exponent

  def sample(
      self, rng: Generator, volume: float,
      smallest: float, ) -> torch.Tensor:
    """
    The 'sample' method returns, as a tensor, the sizes in mm of the
    stones from 'smallest' up of a 'volume' of aggregate in mm³, all of
    it, fines too: each size class filled to the share of 'volume' the
    curve gives it, largest first.
    """
    edges = [smallest]
    edges.extend(sieve for sieve in self.sieves if sieve > smallest)
    sizes = []
    for low, high in zip(edges[:-1], edges[1:]):
      share = self.passingAt(high) - self.passingAt(low)
      if share > 0.0:
        sizes.append(self._fillClass(rng, low, high, share * volume))
    if not sizes:
      return torch.zeros(0).double()
    out = torch.cat(sizes)
    return torch.sort(out, 0, True).values

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @staticmethod
  def _checkTable(sieves: tuple, passing: tuple) -> None:
    """Raises 'ValueError' unless the table is a grading curve."""
    if len(sieves) < 2 or len(sieves) != len(passing):
      raise ValueError('a grading needs a share for each of its sieves')
    if sieves[0] <= 0.0:
      raise ValueError('a sieve must be more than nought')
    for low, high in zip(sieves[:-1], sieves[1:]):
      if high <= low:
        raise ValueError('the sieves must rise')
    for low, high in zip(passing[:-1], passing[1:]):
      if high < low:
        raise ValueError('what passes the sieves cannot fall')
    if passing[0] < 0.0 or passing[-1] != 1.0:
      raise ValueError('all of the aggregate must pass the last sieve')

  def _localExponent(self, low: float, high: float) -> float:
    """The power the curve rises by between 'low' and 'high'."""
    lowShare, highShare = self.passingAt(low), self.passingAt(high)
    if lowShare <= 0.0:
      return 1.0
    return math.log(highShare / lowShare) / math.log(high / low)

  def _fillClass(
      self, rng: Generator, low: float, high: float,
      volume: float, ) -> torch.Tensor:
    """
    The sizes of a class from 'low' to 'high' filling 'volume': drawn
    with as many stones of each size as the curve's power q through the
    class gives, d ** (q - 4) of them, until the next would overfill it
    by more than it would underfill it.
    """
    power = self._localExponent(low, high) - 3.0
    drawn = torch.zeros(0).double()
    filled = 0.0
    while filled < volume:
      draws = torch.from_numpy(rng.random(_BATCH))
      if abs(power) < 1e-12:
        batch = low * (high / low) ** draws
      else:
        start, span = low ** power, high ** power - low ** power
        batch = (start + draws * span) ** (1.0 / power)
      drawn = torch.cat([drawn, batch])
      filled = (math.pi / 6 * drawn ** 3).sum().item()
    total = torch.cumsum(math.pi / 6 * drawn ** 3, 0)
    count = int(torch.searchsorted(total, torch.tensor([volume]).double()))
    if count < len(drawn):
      over = total[count].item() - volume
      under = volume - (total[count - 1].item() if count else 0.0)
      count += 1 if over < under else 0
    return drawn[:count]
