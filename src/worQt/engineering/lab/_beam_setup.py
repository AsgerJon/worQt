"""
BeamSetup is a beam on its rig, set up for a test, and its text: what a
'.beam' file holds.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.desc import Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from .._numbers import formatNumber, parseNumber
from ._bar_layer import BarLayer
from ._rc_beam import RCBeam
from ._rig import Rig
from ._rig_parts import Actuator, Control, Support
from ._stirrups import Stirrups

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Callable

_MATERIALS = ('fcm', 'fy', 'Es')
_LOOP = ('rate', 'limit', 'step', 'kp', 'ki', 'kd', 'speed')
_PARTS = ('support', 'actuator', 'transducer')
_ONCE = ('beam', 'bottom', 'top', 'stirrups', 'control', 'stroke')


def _listed(names: tuple[str, ...]) -> str:
  """'names' as words: 'fcm, fy and Es'."""
  return '%s and %s' % (', '.join(names[:-1]), names[-1])


def _shapeOf(form: str, words: list[str]) -> ValueError:
  """The error of a line not of 'form'."""
  infoSpec = """expected '%s', not '%s'"""
  return ValueError(infoSpec % (form, ' '.join(words)))


def _diameter(word: str) -> float:
  """The diameter in 'word', 'Ø12' or '12'."""
  return parseNumber(str.lstrip(word, 'Øø'), 'diameter')


def _index(word: str, letter: str) -> int:
  """The index in 'word', 'A1' the first actuator, 0."""
  number = word[1:]
  if word[:1] != letter or not str.isdecimal(number) or not int(number):
    infoSpec = """expected %s1, %s2 and so on, not '%s'"""
    raise ValueError(infoSpec % (letter, letter, word))
  return int(number) - 1


def _named(words: list[str], names: tuple, defaults: tuple) -> tuple:
  """The numbers named in 'words', a name and a number each, in the
  order of 'names', any left out its default."""
  if len(words) % 2:
    infoSpec = """each of %s is a name and a number: '%s'"""
    raise ValueError(infoSpec % (_listed(names), ' '.join(words)))
  values = {}
  for name, word in zip(words[::2], words[1::2]):
    if name not in names:
      infoSpec = """expected %s, not '%s'"""
      raise ValueError(infoSpec % (_listed(names), name))
    if name in values:
      raise ValueError("""'%s' is given twice""" % name)
    values[name] = parseNumber(word, name)
  return (*[values.get(name, default)
            for name, default in zip(names, defaults)],)


def _beamLine(words: list[str]) -> tuple[float, ...]:
  """The beam's dimensions and materials from its line."""
  if len(words) < 6 or words[2:5:2] != ['x', 'x']:
    raise _shapeOf('beam L x H x W fcm FCM fy FY Es ES', words)
  dims = [parseNumber(word, name) for word, name in zip(
      words[1:6:2], ('length', 'height', 'width'))]
  defaults = RCBeam.__fallback_materials__
  return (*dims, *_named(words[6:], _MATERIALS, defaults))


def _barLine(words: list[str]) -> BarLayer:
  """A layer of bars from its line."""
  if len(words) != 5 or words[3] != 'cover':
    raise _shapeOf('%s N ØD cover C' % words[0], words)
  count = parseNumber(words[1], 'number of bars')
  if count < 0 or int(count) != count:
    infoSpec = """a layer has a whole number of bars, not '%s'"""
    raise ValueError(infoSpec % words[1])
  return BarLayer(int(count), _diameter(words[2]),
                  parseNumber(words[4], 'cover'))


def _stirrupLine(words: list[str]) -> Stirrups:
  """The stirrups from their line, their gaps after them."""
  gaps = words[4:]
  if (len(words) < 4 or words[2] != 'c/c' or len(gaps) % 3
      or gaps[::3] != ['gap'] * (len(gaps) // 3)):
    raise _shapeOf('stirrups ØD c/c S gap FROM TO', words)
  spans = [(parseNumber(start, 'gap'), parseNumber(end, 'gap'))
           for start, end in zip(gaps[1::3], gaps[2::3])]
  return Stirrups(_diameter(words[1]), parseNumber(words[3], 'spacing'),
                  (*spans,))


def _supportLine(words: list[str]) -> Support:
  """A support from its line."""
  if len(words) != 3:
    raise _shapeOf('support AT KIND', words)
  if words[2] not in Support.kinds():
    infoSpec = """a support is a pin, a roller or fixed, not '%s'"""
    raise ValueError(infoSpec % words[2])
  return Support(parseNumber(words[1], 'place'), words[2])


def _actuatorLine(words: list[str]) -> Actuator:
  """An actuator from its line: driven, or following another."""
  at = parseNumber(words[1], 'place') if len(words) > 1 else 0.0
  if words[2:] == ['driven']:
    return Actuator(at, -1, 1.0)
  if len(words) != 6 or words[2:5:2] != ['follows', 'share']:
    form = "actuator AT driven' or 'actuator AT follows A1 share S"
    raise _shapeOf(form, words)
  return Actuator(at, _index(words[3], 'A'),
                  parseNumber(words[5], 'share'))


def _transducerLine(words: list[str]) -> float:
  """Where a transducer is, from its line."""
  if len(words) != 2:
    raise _shapeOf('transducer AT', words)
  return parseNumber(words[1], 'place')


def _controlLine(words: list[str]) -> Control:
  """The control loop from its line."""
  if len(words) < 3:
    raise _shapeOf('control T1 A1 rate RATE limit LIMIT ...', words)
  defaults = Rig.__fallback_control__
  return Control(_index(words[1], 'T'), _index(words[2], 'A'),
                 *_named(words[3:], _LOOP, defaults))


def _strokeLine(words: list[str]) -> float:
  """How far the actuators move, from its line."""
  if len(words) != 2:
    raise _shapeOf('stroke MM', words)
  return parseNumber(words[1], 'stroke')


class BeamSetup(BaseObject):
  """
  BeamSetup is a beam set up on its rig for a test, as a '.beam' file
  holds it: the 'beam' and the 'rig', which fits it. Its text is a line
  a part, which 'BeamSetup(text)' reads back:

  beam 1600 x 200 x 120 fcm 38 fy 550 Es 200000
  bottom 2 Ø12 cover 25
  top 2 Ø8 cover 25
  stirrups Ø6 c/c 100 gap 150 550
  support 100 pin
  support 1500 roller
  actuator 600 driven
  actuator 1000 follows A1 share 1
  transducer 600
  transducer 1000
  transducer 800
  control T3 A1 rate -0.1 limit -50 step 0.004 kp 0.5 ki 0.05 kd 0 speed 1
  stroke 150

  The lines come in any order, but the parts of a kind are numbered in
  theirs: A1 is the first actuator line, T3 the third transducer line.
  A diameter of nought is no bars or no stirrups. The materials, the
  control's numbers and the stroke may be left out, taking the lab's
  own, and so may the 'Ø'. A text that is no setup is refused, saying
  the line and why.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __setup_parts__: tuple[RCBeam, Rig] | None = None

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  rig: Field[Rig] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _getParts(self, ) -> tuple[RCBeam, Rig]:
    if self.__setup_parts__ is None:
      raise MissingVariable(self, '__setup_parts__', tuple)
    return self.__setup_parts__

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam set up."""
    return self._getParts()[0]

  @rig.GET
  def _getRig(self, ) -> Rig:
    """The 'rig' getter returns the rig the beam is set up on."""
    return self._getParts()[1]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  Python API   # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __str__(self, ) -> str:
    """The setup's text: the beam, its bars and stirrups, then the rig's
    parts, its control and its stroke."""
    return '\n'.join((*self._beamLines(), *self._rigLines()))

  def __repr__(self, ) -> str:
    return """%s('''%s''')""" % (type(self).__name__, str(self))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(RCBeam, Rig)
  def __init__(self, beam: RCBeam, rig: Rig) -> None:
    rig.check(beam)
    self.__setup_parts__ = (beam, rig)

  @overload(str)
  def __init__(self, text: str) -> None:
    once, parts = self._sorted(text)
    beam = RCBeam(*self._read(self._line(once, 'beam'), _beamLine),
                  self._read(self._line(once, 'bottom'), _barLine),
                  self._read(self._line(once, 'top'), _barLine),
                  self._read(self._line(once, 'stirrups'), _stirrupLine))
    self.__init__(beam, self._rigOf(once, parts))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _beamLines(self, ) -> list[str]:
    """The lines of the beam, its bars and its stirrups."""
    beam = self.beam
    dims = (*map(formatNumber, (beam.length, beam.height, beam.width)),)
    words = ['beam %s x %s x %s' % dims]
    for name, value in zip(_MATERIALS, (beam.fcm, beam.fy, beam.Es)):
      words.append('%s %s' % (name, formatNumber(value)))
    lines = [' '.join(words)]
    for name, layer in (('bottom', beam.bottom), ('top', beam.top)):
      lines.append('%s %d Ø%s cover %s' % (
        name, layer.count, formatNumber(layer.diameter),
        formatNumber(layer.cover)))
    stirrups = beam.stirrups
    words = ['stirrups Ø%s c/c %s' % (formatNumber(stirrups.diameter),
                                      formatNumber(stirrups.spacing))]
    for start, end in stirrups.gaps:
      words.append('gap %s %s' % (formatNumber(start), formatNumber(end)))
    return [*lines, ' '.join(words)]

  def _rigLines(self, ) -> list[str]:
    """The lines of the rig's parts, its control and its stroke."""
    rig = self.rig
    lines = ['support %s %s' % (formatNumber(support.at), support.kind)
             for support in rig.supports]
    for index, actuator in enumerate(rig.actuators):
      line = 'actuator %s' % formatNumber(actuator.at)
      if index == rig.driven:
        lines.append('%s driven' % line)
        continue
      lines.append('%s follows A%d share %s' % (
        line, actuator.follows + 1, formatNumber(actuator.share)))
    lines += ['transducer %s' % formatNumber(x) for x in rig.transducers]
    control = rig.control
    words = ['control T%d A%d' % (control.transducer + 1,
                                  control.actuator + 1)]
    for name, value in zip(_LOOP, control[2:]):
      words.append('%s %s' % (name, formatNumber(value)))
    lines.append(' '.join(words))
    return [*lines, 'stroke %s' % formatNumber(rig.stroke)]

  @staticmethod
  def _sorted(text: str) -> tuple[dict, dict]:
    """The words of the lines of 'text', each with its number: those
    there is one of by their keyword, the parts in lists by theirs."""
    once, parts = {}, {keyword: [] for keyword in _PARTS}
    for number, line in enumerate(str.splitlines(text), 1):
      words = str.split(line)
      if not words:
        continue
      keyword = words[0]
      if keyword in parts:
        parts[keyword].append((number, words))
      elif keyword in once:
        infoSpec = """line %d: a setup has one '%s' line"""
        raise ValueError(infoSpec % (number, keyword))
      elif keyword in _ONCE:
        once[keyword] = (number, words)
      else:
        infoSpec = """line %d: expected %s, not '%s'"""
        raise ValueError(infoSpec % (number, _listed((*_ONCE, *_PARTS)),
                                     str.strip(line)))
    return once, parts

  @staticmethod
  def _line(once: dict, keyword: str) -> tuple[int, list[str]]:
    """The line of 'keyword' sorted, there being one."""
    if keyword not in once:
      raise ValueError("""a setup has a '%s' line""" % keyword)
    return once[keyword]

  def _rigOf(self, once: dict, parts: dict) -> Rig:
    """The rig of the lines sorted, its actuator driven the one its
    control drives."""
    supports = [self._read(entry, _supportLine)
                for entry in parts['support']]
    actuators = [self._read(entry, _actuatorLine)
                 for entry in parts['actuator']]
    transducers = [self._read(entry, _transducerLine)
                   for entry in parts['transducer']]
    control = self._read(self._line(once, 'control'), _controlLine)
    driven = [index for index, actuator in enumerate(actuators)
              if actuator.follows < 0]
    if actuators and driven != [control.actuator]:
      infoSpec = """A%d, which the control drives, is the one actuator
      driven"""
      raise ValueError(' '.join(infoSpec.split()) % (control.actuator + 1))
    stroke = Rig.__fallback_stroke__
    if 'stroke' in once:
      stroke = self._read(once['stroke'], _strokeLine)
    return Rig((*supports,), (*actuators,), (*transducers,), control,
               stroke)

  @staticmethod
  def _read(entry: tuple[int, list[str]], reader: Callable) -> object:
    """What 'reader' reads from the words of 'entry', a line and its
    number, an error saying the line."""
    number, words = entry
    try:
      return reader(words)
    except ValueError as exception:
      message = """line %d: %s""" % (number, exception)
      raise ValueError(message) from exception
