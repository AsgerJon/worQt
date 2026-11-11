"""
Rig is how a beam is set up for a test: what it rests on, the actuators
pushing it, the transducers measuring it and the control loop driving
the test.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from ._rig_parts import Actuator, Control, Support

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from ._rc_beam import RCBeam


class Rig(BaseObject):
  """
  Rig is how a beam is set up for a test, in mm from the beam's left
  end: its 'supports', any number, each a pin, a roller or a fixed
  clamp; its 'actuators', any number, pushing it; its 'transducers',
  any number, under the beam, each reading how far its underside moves
  up where it is, so less than nought as it bends down; and its
  'control', the loop
  reading one transducer and moving one actuator, the one driven, to
  make the reading follow the control's command. Every other actuator
  follows another, pushing a share of its force: 'shares' are the
  forces the actuators push with as shares of the force of the one
  driven. The control looks every 'cycle' seconds, its command moving
  a step, a share of its ramp, at its rate, each a step of OpenSees; an
  actuator moves at most 'stroke' mm.

  A rig is made only whole: an actuator driven, the one the control
  moves, and every other following one that leads, through the chain,
  to it; the control reading a transducer there is. 'check' raises
  'ValueError' unless the rig fits a beam: its parts on the beam, its
  supports holding it, along and across and from turning, and its
  control's ramp reaching its limit from nought.
  'standard' sets a beam up for four point bending: a pin and a roller
  150 mm in from its ends, two actuators at the thirds of the span, the
  second pushing as hard as the first, a transducer under each and one
  at midspan, the control reading the one at midspan, ramping it down
  0.1 mm a second, a rate of -0.1 mm/s, to -150 mm, a thousandth of
  that a step.

  'withSupports', 'withActuators', 'withTransducers' and 'withControl'
  return the rig with those changed; 'withoutSupport',
  'withoutActuator' and 'withoutTransducer' return it without a part,
  the indices after it moved down, refusing to take away the actuator
  driven, one another follows, or the transducer the control reads;
  'driving' returns it driving another actuator, the one driven before
  following it. 'stretched' returns it stretched, for a longer or a
  shorter beam.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_stroke__ = 150.0  # mm
  __fallback_overhang__ = 150.0  # mm, the beam past each end support
  __fallback_control__ = (-0.1, -150.0, 0.001, 0.5, 0.05, 0.0, 1.0)

  #  Private Variables
  __rig_parts__: tuple[tuple, tuple, tuple] | None = None
  __rig_control__: Control | None = None
  __rig_stroke__: float | None = None

  #  Virtual Variables
  supports: Field[tuple[Support, ...]] = Field()
  actuators: Field[tuple[Actuator, ...]] = Field()
  transducers: Field[tuple[float, ...]] = Field()
  control: Field[Control] = Field()
  cycle: Field[float] = Field()
  stroke: Field[float] = Field()
  driven: Field[int] = Field()
  shares: Field[tuple[float, ...]] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple[tuple, tuple, tuple]:
    if self.__rig_parts__ is None:
      raise MissingVariable(self, '__rig_parts__', tuple)
    return self.__rig_parts__

  @supports.GET
  def _getSupports(self, ) -> tuple[Support, ...]:
    """The 'supports' getter returns what the beam rests on, in the
    order added."""
    return self._getParts()[0]

  @actuators.GET
  def _getActuators(self, ) -> tuple[Actuator, ...]:
    """The 'actuators' getter returns the actuators, in the order
    added."""
    return self._getParts()[1]

  @transducers.GET
  def _getTransducers(self, ) -> tuple[float, ...]:
    """The 'transducers' getter returns where the transducers are, in
    the order added."""
    return self._getParts()[2]

  @control.GET
  def _getControl(self, ) -> Control:
    """The 'control' getter returns the control loop."""
    if self.__rig_control__ is None:
      raise MissingVariable(self, '__rig_control__', Control)
    return self.__rig_control__

  @cycle.GET
  def _getCycle(self, ) -> float:
    """The 'cycle' getter returns the seconds between two looks of the
    control: a step of its command at its rate."""
    return self.control.cycle

  @stroke.GET
  def _getStroke(self, ) -> float:
    """The 'stroke' getter returns how far an actuator moves at most,
    in mm."""
    if self.__rig_stroke__ is None:
      raise MissingVariable(self, '__rig_stroke__', float)
    return self.__rig_stroke__

  @driven.GET
  def _getDriven(self, ) -> int:
    """The 'driven' getter returns the index of the actuator the control
    moves."""
    return self.control.actuator

  @shares.GET
  def _getShares(self, ) -> tuple[float, ...]:
    """The 'shares' getter returns the force each actuator pushes with,
    as a share of the force of the one driven."""
    return (
      *[self._shareOf(index)
        for index in range(len(self.actuators))],
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __repr__(self, ) -> str:
    infoSpec = """%s(supports %r, actuators %r, transducers %r, %r)"""
    return infoSpec % (
      type(self).__name__, self.supports, self.actuators,
      self.transducers, self.control
    )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(tuple, tuple, tuple, Control, float)
  def __init__(
      self, supports: tuple, actuators: tuple,
      transducers: tuple, control: Control, stroke: float, ) -> None:
    supports = (*[Support(float(s.at), s.kind) for s in supports],)
    for support in supports:
      if support.kind not in Support.kinds():
        infoSpec = """a support is a pin, a roller or fixed, not '%s'"""
        raise ValueError(infoSpec % support.kind)
    actuators = (
      *[Actuator(float(a.at), int(a.follows), float(a.share))
        for a in actuators],
    )
    transducers = (*map(float, transducers),)
    control = Control(
      int(control.transducer), int(control.actuator),
      *map(float, control[2:])
      )
    if not stroke > 0:
      raise ValueError('the actuators move')
    self.__rig_parts__ = (supports, actuators, transducers)
    self.__rig_control__ = control
    self.__rig_stroke__ = float(stroke)
    self._checkWhole()

  @overload(tuple, tuple, tuple, Control)
  def __init__(
      self, supports: tuple, actuators: tuple,
      transducers: tuple, control: Control
      ) -> None:
    self.__init__(
      supports, actuators, transducers, control,
      self.__fallback_stroke__
      )

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @classmethod
  def standard(cls, beam: RCBeam) -> Rig:
    """The 'standard' method returns 'beam' set up for four point
    bending, the control reading midspan."""
    overhang = min(cls.__fallback_overhang__, beam.length / 10)
    left, right = overhang, beam.length - overhang
    third = (right - left) / 3
    first, second = left + third, right - third
    supports = (Support(left, 'pin'), Support(right, 'roller'))
    actuators = (Actuator(first, -1, 1.0), Actuator(second, 0, 1.0))
    control = Control(2, 0, *cls.__fallback_control__)
    return cls(
      supports, actuators, (first, second, (left + right) / 2),
      control
      )

  def check(self, beam: RCBeam) -> None:
    """The 'check' method raises 'ValueError' unless the rig fits
    'beam': its parts on it, and its supports holding it."""
    places = [('a support', s.at) for s in self.supports]
    places += [('an actuator', a.at) for a in self.actuators]
    places += [('a transducer', x) for x in self.transducers]
    for name, x in places:
      if not 0 <= x <= beam.length:
        raise ValueError('%s is off the beam, at %g mm' % (name, x))
    reason = self.unheld()
    if reason:
      raise ValueError(reason)
    control = self.control
    if control.rate * control.limit <= 0:
      infoSpec = """a ramp at %g mm/s from nought never reaches %g mm"""
      raise ValueError(infoSpec % (control.rate, control.limit))

  def unheld(self, ) -> str:
    """The 'unheld' method says why the supports do not hold a beam, or
    nothing if they do: something must hold it along, and across at two
    places or by a clamp, so it neither slides nor turns."""
    holds = [support.holds for support in self.supports]
    if not any(along for along, _, _ in holds):
      return 'nothing holds the beam along: it needs a pin or a clamp'
    across = {support.at for support in self.supports}
    clamped = any(turning for _, _, turning in holds)
    if len(across) < 2 and not clamped:
      return 'the beam can turn: it needs two supports or a clamp'
    return ''

  def withSupports(self, *supports: Support) -> Rig:
    """The 'withSupports' method returns the rig on 'supports'."""
    return self._made(
      supports, self.actuators, self.transducers,
      self.control
      )

  def withActuators(self, *actuators: Actuator) -> Rig:
    """The 'withActuators' method returns the rig with 'actuators'."""
    return self._made(
      self.supports, actuators, self.transducers,
      self.control
      )

  def withTransducers(self, *transducers: float) -> Rig:
    """The 'withTransducers' method returns the rig with transducers at
    'transducers'."""
    return self._made(
      self.supports, self.actuators, transducers,
      self.control
      )

  def withControl(self, control: Control) -> Rig:
    """The 'withControl' method returns the rig with 'control'."""
    return self._made(
      self.supports, self.actuators, self.transducers,
      control
      )

  def withoutSupport(self, index: int) -> Rig:
    """The 'withoutSupport' method returns the rig without the support
    of 'index'."""
    supports = [*self.supports]
    del supports[index]
    return self.withSupports(*supports)

  def withoutActuator(self, index: int) -> Rig:
    """The 'withoutActuator' method returns the rig without the actuator
    of 'index', refusing the one driven and one another follows."""
    if index == self.driven:
      raise ValueError(
        'the control drives that actuator: have it drive '
        'another first'
        )
    for other, actuator in enumerate(self.actuators):
      if other != self.driven and actuator.follows == index:
        raise ValueError('A%d follows that actuator' % (other + 1))
    actuators = []
    for other, actuator in enumerate(self.actuators):
      if other == index:
        continue
      follows = actuator.follows
      follows -= 1 if follows > index else 0
      actuators.append(Actuator(actuator.at, follows, actuator.share))
    driven = self.driven - (1 if self.driven > index else 0)
    control = self.control.changed('actuator', driven)
    return self._made(
      self.supports, actuators, self.transducers,
      control
      )

  def withoutTransducer(self, index: int) -> Rig:
    """The 'withoutTransducer' method returns the rig without the
    transducer of 'index', refusing the one the control reads."""
    reads = self.control.transducer
    if index == reads:
      raise ValueError(
        'the control reads that transducer: have it read '
        'another first'
        )
    transducers = [*self.transducers]
    del transducers[index]
    reads -= 1 if reads > index else 0
    return self._made(
      self.supports, self.actuators, transducers,
      self.control.changed('transducer', reads)
      )

  def driving(self, index: int) -> Rig:
    """The 'driving' method returns the rig with the control driving the
    actuator of 'index', the one driven before following it, pushing as
    hard."""
    old = self.driven
    if index == old:
      return self
    if not 0 <= index < len(self.actuators):
      raise ValueError('there is no actuator A%d' % (index + 1))
    actuators = [*self.actuators]
    actuators[old] = Actuator(actuators[old].at, index, 1.0)
    actuators[index] = Actuator(actuators[index].at, -1, 1.0)
    return self._made(
      self.supports, actuators, self.transducers,
      self.control.changed('actuator', index)
      )

  def stretched(self, factor: float) -> Rig:
    """The 'stretched' method returns the rig with every part 'factor'
    times as far from the beam's left end, to the centimetre."""

    def place(x: float) -> float:
      return round(x * factor / 10) * 10.0

    supports = [Support(place(s.at), s.kind) for s in self.supports]
    actuators = [Actuator(place(a.at), a.follows, a.share)
                 for a in self.actuators]
    transducers = [place(x) for x in self.transducers]
    return self._made(supports, actuators, transducers, self.control)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _made(
      self, supports: tuple | list, actuators: tuple | list,
      transducers: tuple | list, control: Control
      ) -> Rig:
    """A rig like this one, of the parts given."""
    return Rig(
        (*supports,), (*actuators,), (*transducers,), control,
        self.stroke
        )

  def _checkWhole(self, ) -> None:
    """Raises unless the rig is whole: an actuator driven, every other
    following one that leads to it, the control reading a transducer
    there is."""
    actuators, control = self.actuators, self.control
    if not actuators:
      raise ValueError('a rig has an actuator, for the control to drive')
    if not 0 <= control.actuator < len(actuators):
      raise ValueError('the control drives an actuator there is')
    if not 0 <= control.transducer < len(self.transducers):
      raise ValueError('the control reads a transducer there is')
    if not control.rate or not control.speed > 0:
      raise ValueError('the control ramps, and its actuator moves')
    if not 0 < control.step <= 1:
      infoSpec = """a step is a share of the ramp, above 0 and at most 1,
      not %g"""
      raise ValueError(' '.join(infoSpec.split()) % control.step)
    for index in range(len(actuators)):
      self._shareOf(index)

  def _shareOf(self, index: int) -> float:
    """The force the actuator of 'index' pushes with, as a share of the
    force of the one driven, through the chain it follows; raises if
    the chain does not lead there."""
    share, seen = 1.0, set()
    while index != self.driven:
      if index in seen:
        raise ValueError('the actuators follow each other round')
      seen.add(index)
      actuator = self.actuators[index]
      if not 0 <= actuator.follows < len(self.actuators):
        raise ValueError(
          'A%d follows an actuator there is not'
          % (index + 1)
          )
      share *= actuator.share
      index = actuator.follows
    return share
