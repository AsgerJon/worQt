"""
SignalSpy records every emission of a Qt signal together with its
arguments, so a test can assert how often a signal fired and with what.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.mcls import BaseObject
from worktoy.utilities import maybe

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any, Iterator, Optional, TypeAlias, Union

  from PySide6.QtCore import SignalInstance

  Emission: TypeAlias = tuple[Any, ...]
  Emissions: TypeAlias = list[Emission]
  MaybeEmissions: TypeAlias = Optional[Emissions]
  EmissionsField: TypeAlias = Union[Emissions, Field]
  EmissionField: TypeAlias = Union[Emission, Field]
  IntField: TypeAlias = Union[int, Field]


class SignalSpy(BaseObject):
  """
  SignalSpy connects to a Qt signal on construction and records every
  emission's arguments as a tuple. A test reads 'count' to assert how many
  times the signal fired, 'args' for the most recent emission, and
  'emissions' for the full list in order. It never blocks; pair it with a
  'SignalWaiter' when the emission is asynchronous.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __the_signal__ = None
  __recorded_emissions__: MaybeEmissions = None

  #  Public Variables
  emissions: EmissionsField = Field()
  count: IntField = Field()
  args: EmissionField = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @emissions.GET
  def _getEmissions(self, ) -> Emissions:
    """The 'emissions' getter returns the recorded emissions in order,
    each a tuple of the arguments the signal carried."""
    return maybe(self.__recorded_emissions__, [])

  @count.GET
  def _getCount(self, ) -> int:
    """The 'count' getter returns how many times the signal has fired."""
    return len(self.emissions)

  @args.GET
  def _getArgs(self, ) -> Emission:
    """The 'args' getter returns the arguments of the most recent
    emission, raising 'IndexError' when the signal has not fired."""
    emissions = self.emissions
    if not emissions:
      raise IndexError('The signal has not been emitted!')
    return emissions[-1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _record(self, *args) -> None:
    """The '_record' slot appends one emission's arguments. It is the slot
    connected to the spied signal."""
    existing = self.emissions
    self.__recorded_emissions__ = [*existing, (*args,)]

  def clear(self, ) -> None:
    """The 'clear' method drops every recorded emission."""
    self.__recorded_emissions__ = None

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, signal: SignalInstance) -> None:
    self.__the_signal__ = signal
    signal.connect(self._record)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __len__(self, ) -> int:
    return self.count

  def __bool__(self, ) -> bool:
    return True if self.emissions else False

  def __iter__(self, ) -> Iterator[Emission]:
    yield from self.emissions
