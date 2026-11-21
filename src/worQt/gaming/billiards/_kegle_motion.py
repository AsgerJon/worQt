"""
KegleMotion moves keglebillard's balls and pins together, KegleHits
steps them through what they meet, and KegleRecorder plays a
keglebillard shot at once and samples it, the pins with the balls.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import NamedTuple, TYPE_CHECKING

import numpy

from ._carom_table import Ball
from ._kegle_pin import KeglePin
from ._kegle_pins import PinContacts, PinField
from ._kegle_table import HOLE_NAMES, KegleTable
from ._motion import CUSHIONS, Glide, Motion, Touch
from ._motion import _TOUCH, _firstQuarticRoot
from ._recorder import _DUE, Recording, Stretch, _rowsOf

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from typing import Iterator

ZONE = 1.0  # mm: a ball moving this near a pin's reach is stepped with it

#  A zone round a pin, seen from above: its middle, 'x' and 'y', and its
#  size, how far from the middle a ball's middle comes into it.
Zone = tuple[float, float, float]


class KegleMotion(NamedTuple):
  """
  KegleMotion moves keglebillard's balls and pins together on its
  'table': the balls as 'motion' has them, the pins shaped as 'shape',
  meeting things as 'contacts' has it ('PinField'); 'motion' is on the
  carom table 'table' is drilled from.

  On the cloth each ball moves exactly, as 'Motion' moves it, until one
  comes moving into a pin's zone ('zonesOf'): a ball's radius, the
  pin's widest and 'ZONE' round its axis seen from above. From then on,
  through any hit on a cushion or a ball, and while any pin moves, every
  ball and every pin is stepped together in one compiled kernel
  ('KegleHits'), until no ball touches a cushion or a ball, no pin moves
  and no ball moves in a pin's zone; then the balls are on the cloth
  exactly again. Each contact beginning is logged as 'Motion' logs it,
  and a ball meeting a pin as a 'Touch' of kind 'pin', its 'second' the
  pin's number. Through a hit a ball is stepped on the cloth, not moved
  exactly, a hair off, and its roll ends without the felt's push back.

  The pockets are drilled into the table ('KegleTable.pockets'): the
  cushions open over their slots, the slots' jaws meeting a ball as a
  nose does ('engine', a 'Motion' with them); a ball whose middle comes
  over a hole goes into it, logged as a 'Touch' of kind 'pocket', its
  'second' the hole's name ('HOLE_NAMES'), and is kept far off the table
  while the shot goes on ('KegleTable.parkedAt'), met by nothing.
  """

  table: KegleTable = KegleTable()
  motion: Motion = Motion()
  shape: KeglePin = KeglePin()
  contacts: PinContacts = PinContacts()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def engine(self, ) -> Motion:
    """The 'engine' method returns 'motion' with the table's pockets:
    the cushions open over the slots, the jaws meeting the balls."""
    return _engineOf(self.motion, self.table)

  def captured(self, balls: tuple[Ball, ...]) -> tuple[tuple, tuple]:
    """The 'captured' method returns 'balls' with each whose middle is
    over a hole gone into it, kept far off the table, and those going in,
    each a 'Touch' of kind 'pocket'."""
    pockets = self.table.pockets()
    out, touches = [], []
    for ball in balls:
      if self.table.pocketOf(ball) < 0:
        for k, (hx, hy) in enumerate(pockets.holes):
          if math.hypot(ball.x - hx, ball.y - hy) <= pockets.radius + 1e-6:
            ball = Ball(ball.name, *self.table.parkedAt(k), ball.turn)
            touches.append(Touch('pocket', ball.name, HOLE_NAMES[k]))
            break
      out.append(ball)
    return tuple(out), tuple(touches)

  def fieldOf(self, numbers: tuple = None) -> PinField:
    """The 'fieldOf' method returns the pins 'numbers', all five if
    'None', standing on their spots, asleep."""
    return PinField(self.table, numbers, self.shape, self.contacts)

  def zonesOf(self, field: PinField) -> tuple[Zone, ...]:
    """The 'zonesOf' method returns each pin's zone, as the kernel has
    it ('_kegle_kernels.zoneOf'): round the middle of its axis seen from
    above, half that axis's length seen so, a ball's radius, the pin's
    widest and 'ZONE' out; none for a pin off the table."""
    radius = self.motion.table.radius
    out = []
    for pin in field.pins:
      if pin.off:
        continue
      foot, top = field._axis(pin)
      half = 0.5 * math.sqrt((top[0] - foot[0]) ** 2
                             + (top[1] - foot[1]) ** 2)
      out.append((0.5 * (foot[0] + top[0]), 0.5 * (foot[1] + top[1]),
                  half + radius + field.widest + ZONE))
    return tuple(out)

  def nearing(self, ball: Ball, zones: tuple[Zone, ...]) -> bool:
    """The 'nearing' method tells whether 'ball' moves in one of
    'zones', or on its edge moving in."""
    vx, vy = ball.vx, ball.vy
    if math.sqrt(vx * vx + vy * vy) <= 0.0:
      return False
    for cx, cy, size in zones:
      dx, dy = ball.x - cx, ball.y - cy
      off = math.sqrt(dx * dx + dy * dy) - size
      if off < 0.0 or (off < _TOUCH and dx * vx + dy * vy < 0.0):
        return True
    return False

  def busy(self, balls: tuple[Ball, ...], field: PinField) -> bool:
    """The 'busy' method tells whether 'balls' and the pins of 'field'
    are to be stepped together: a ball touching a cushion or a ball, a
    pin moving, or a ball moving near a pin."""
    if field.awake() or self.engine().inContact(balls):
      return True
    zones = self.zonesOf(field)
    return any(self.nearing(ball, zones) for ball in balls)

  def resting(self, balls: tuple[Ball, ...], field: PinField) -> bool:
    """The 'resting' method tells whether every ball is still, touching
    nothing it moves into, and no pin moves."""
    if self.busy(balls, field):
      return False
    cloth, radius = self.motion.cloth, self.motion.table.radius
    return all(cloth.phaseOf(ball, radius) == 'still' for ball in balls)

  def glided(self, balls: tuple[Ball, ...], field: PinField,
             most: float) -> Glide:
    """The 'glided' method returns the 'Glide' of 'balls', none busy
    ('busy'), over the cloth as 'Motion.glided' has it, the pockets'
    slots open and their jaws met ('engine'), ending also as a ball comes
    into a pin's zone or over a hole ('captured' then takes it)."""
    motion = self.engine()
    cloth, radius = motion.cloth, motion.table.radius
    pockets = self.table.pockets()
    zones = self.zonesOf(field) + tuple(
      (hx, hy, pockets.radius) for hx, hy in pockets.holes)
    first = most
    for ball in balls:
      phase = cloth.phaseOf(ball, radius)
      if phase not in ('sliding', 'rolling'):
        continue
      span = min(first, cloth.phaseTime(ball, phase, radius))
      for zone in zones:
        time = _zoneTime(motion, ball, phase, zone, span)
        if time is not None and time < first:
          first = time
    return motion.glided(balls, first)

  def hitsOf(self, balls: tuple[Ball, ...], field: PinField,
             settles: bool = False) -> KegleHits:
    """The 'hitsOf' method returns 'KegleHits' stepping 'balls' and the
    pins of 'field' together, to be run on as long as asked: the steps
    come out the same however the runs cut them; 'settles', they end as
    the balls rest with pins still moving that no longer matter (a shot
    recorded, 'KegleHits.settled')."""
    return KegleHits(self, balls, field, settles)

  def played(self, balls: tuple[Ball, ...], field: PinField,
             seconds: float) -> tuple[tuple[Ball, ...], tuple]:
    """The 'played' method returns 'balls' as they are 'seconds' later,
    the pins of 'field' moved on with them, and the contacts that began
    meanwhile, in order, each a 'Touch' once; as 'Motion.played' does,
    a contact going on as the time ends has its last step cut short."""
    balls, passed, log = tuple(balls), 0.0, []
    while passed < seconds:
      left, used = seconds - passed, 0.0
      if self.busy(balls, field):
        balls, used, touches = self.hitsOf(balls, field).run(left, False)
        log.extend(touches)
      if used <= 0.0:
        glide = self.glided(balls, field, left)
        balls, used = glide.after, glide.span
        log.extend(glide.touches)
      balls, caught = self.captured(balls)
      log.extend(caught)
      passed += used
    return balls, tuple(log)


class KegleHits:
  """
  KegleHits steps keglebillard's balls and pins together, for its
  'motion', through their hits on the cushions, on each other and on
  the pins, and while any pin moves ('_kegle_kernels.kegleRun'): made of
  the balls and the 'field' of pins as they begin
  ('KegleMotion.hitsOf'), 'run' steps them on for so long, as often as
  asked, until all are clear, 'over', or, if it 'settles' (a shot
  recorded), the balls rest with pins still moving that can neither
  stand again nor move a ball, 'over' and 'settled' (the user: only
  the balls must settle); 'balls' are the balls now, and
  the field's pins are kept as they are now after each run. The steps
  are whole and the same however the runs cut them, so a shot sampled at
  any rate comes out the same, to the last digit.
  """

  __slots__ = ('motion', 'field', 'names', 'arrays', 'rules', 'red',
               'used', 'over', 'settled', 'settles')

  def __init__(self, motion: KegleMotion, balls: tuple[Ball, ...],
               field: PinField, settles: bool = False) -> None:
    import warp as wp

    from ._kegle_pins import _rulesOf as pinRulesOf
    from ._motion import _rulesOf as hitRulesOf
    wp.init()
    self.motion, self.field = motion, field
    self.names = [ball.name for ball in balls]
    self.red = self.names.index('red') if 'red' in self.names else -1
    self.rules = (hitRulesOf(motion.motion), pinRulesOf(field),
                  _pocketRulesOf(motion.table))
    self.used, self.over, self.settled = 0.0, False, False
    self.settles = True if settles else False
    pins, names = field.pins, self.names
    values = {
      'spheres': (wp.vec2d, [(z, size) for _, _, z, size in field.spheres]),
      'place': (wp.vec2d, [(each.x, each.y) for each in balls]),
      'turn': (wp.vec4d, [tuple(each.turn) for each in balls]),
      'speed': (wp.vec2d, [(each.vx, each.vy) for each in balls]),
      'spin': (wp.vec3d, [(each.wx, each.wy, each.wz) for each in balls]),
      'settling': (wp.int32, [1 if each.settling else 0 for each in balls]),
      'going': (wp.int32, _goingOf(motion.engine(), balls)),
      'pinGoing': (wp.int32, [0] * len(balls)),
      'pinNow': (wp.int32, [0] * len(balls)),
      'lifts': (wp.float64, [0.0] * len(balls)),
      'pinP': (wp.vec3d, [tuple(pin.p) for pin in pins]),
      'pinV': (wp.vec3d, [tuple(pin.v) for pin in pins]),
      'pinQ': (wp.quatd, [(pin.q[1], pin.q[2], pin.q[3], pin.q[0])
                          for pin in pins]),
      'pinW': (wp.vec3d, [tuple(pin.w) for pin in pins]),
      'awake': (wp.int32, [2 if pin.off else 1 if pin.awake else 0
                           for pin in pins]),
      'credit': (wp.int32, [names.index(pin.credit) if pin.credit in names
                            else -1 for pin in pins]),
      'mover': (wp.int32, [names.index(pin.mover) if pin.mover in names
                           else -1 for pin in pins]),
      'quiet': (wp.float64, [pin.quiet for pin in pins]),
      'held': (wp.int32, [0] * len(pins)),
      'holes': (wp.vec2d, list(motion.table.pockets().holes)),
      'jaws': (wp.vec3d, [(x, y, float(side))
                          for x, y, side in motion.engine().jawsOf()])}
    self.arrays = {name: wp.array(data, dtype, None, None, None, None,
                                  'cpu')
                   for name, (dtype, data) in values.items()}
    self.arrays['events'] = wp.zeros(1024, wp.vec4i, 'cpu')
    self.arrays['out'] = wp.zeros(4, wp.float64, 'cpu')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def balls(self, ) -> tuple[Ball, ...]:
    """The 'balls' method returns the balls now."""
    got = {name: self.arrays[name].numpy() for name in (
      'place', 'turn', 'speed', 'spin', 'settling')}
    out = []
    for k, name in enumerate(self.names):
      x, y = (float(value) for value in got['place'][k])
      vx, vy = (float(value) for value in got['speed'][k])
      wx, wy, wz = (float(value) for value in got['spin'][k])
      turn = tuple(float(value) for value in got['turn'][k])
      out.append(Ball(name, x, y, turn, vx, vy, wx, wy, wz,
                      bool(got['settling'][k])))
    return tuple(out)

  def run(self, seconds: float,
          whole: bool) -> tuple[tuple[Ball, ...], float, tuple]:
    """The 'run' method steps the balls and pins on together for
    'seconds', or until all are clear, 'over'; unless the steps are
    'whole', the last is cut short to end at 'seconds'; whole, it may
    end up to a step past it. Returns the balls, how long it took, and
    the contacts that began meanwhile, in order; the field's pins are
    left as they are now."""
    import warp as wp

    from . import _kegle_kernels as kernels
    a, (hits, rules, pockets) = self.arrays, self.rules
    begun, log = self.used, []
    while not self.over and self.used - begun < seconds:
      wp.launch(kernels.kegleRun, 1,
                [hits, rules, pockets, a['holes'], a['jaws'],
                 a['spheres'], a['place'], a['turn'],
                 a['speed'], a['spin'], a['settling'], a['going'],
                 a['pinGoing'], a['pinNow'], a['lifts'], a['pinP'],
                 a['pinV'], a['pinQ'], a['pinW'], a['awake'], a['credit'],
                 a['mover'], a['quiet'], a['held'], self.red, float(begun),
                 float(self.used), float(seconds), 1 if whole else 0,
                 100000000, 1 if self.settles else 0, a['events'],
                 a['out']], [], [], [], 'cpu')
      used, _, clear, logged = (float(value)
                                for value in a['out'].numpy()[:4])
      log.extend(self._touchesOf(a['events'].numpy()[:int(logged)]))
      self.used = used
      if clear:
        self.over = True
        self.settled = clear > 1.5
    self._pinsBack()
    return self.balls(), self.used - begun, tuple(log)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _touchesOf(self, events: numpy.ndarray) -> list:
    """Returns the contacts the kernel logged as 'events', (step, kind,
    first, second), each a 'Touch', in order: by step, sorted within
    one."""
    names, pins = self.names, self.field.pins
    groups = {}
    for step, kind, first, second in events:
      one = names[first]
      if kind == 0:
        touch = Touch('cushion', one, CUSHIONS[second])
      elif kind == 1:
        touch = Touch('ball', one, names[second])
      elif kind == 2:
        touch = Touch('pin', one, str(pins[second].number))
      else:
        touch = Touch('pocket', one, HOLE_NAMES[second])
      groups.setdefault(int(step), []).append(touch)
    out = []
    for step in sorted(groups):
      out.extend(sorted(groups[step]))
    return out

  def _pinsBack(self, ) -> None:
    """Sets the field's pins as the kernel has them now."""
    got = {name: self.arrays[name].numpy() for name in (
      'pinP', 'pinV', 'pinQ', 'pinW', 'awake', 'credit', 'mover',
      'quiet')}
    names = self.names
    for k, pin in enumerate(self.field.pins):
      pin.p = [float(value) for value in got['pinP'][k]]
      pin.v = [float(value) for value in got['pinV'][k]]
      x, y, z, w = (float(value) for value in got['pinQ'][k])
      pin.q = [w, x, y, z]
      pin.w = [float(value) for value in got['pinW'][k]]
      pin.awake = int(got['awake'][k]) == 1
      pin.off = int(got['awake'][k]) == 2
      credit, mover = int(got['credit'][k]), int(got['mover'][k])
      pin.credit = names[credit] if credit >= 0 else ''
      pin.mover = names[mover] if mover >= 0 else ''
      pin.quiet = float(got['quiet'][k])


class KegleRecorder(NamedTuple):
  """
  KegleRecorder plays keglebillard shots on the table of 'motion' at
  once and samples them, as 'Recorder' samples three-cushion: 'rate'
  times a second, 'size' samples a 'Stretch', each shot followed until
  every ball rests, 'longest' seconds at most: only the balls must
  settle (the user), pins moving on then unless one may stand again,
  is in the air, or may yet reach a ball ('KegleHits.settled'); a pin
  still moving at the end is down for good, counted so ('fallenOf').
  The pins
  'numbers' stand on their spots as each shot begins (the rules: always
  set up, those clear of the balls, 'KegleTable.pinsPlaced'), and each
  sample holds them too, 'Stretch.pins'. As the 'Recorder', the samples
  do not change the shot: it is the one 'KegleMotion.played' gives over
  its whole length at once, whatever the rate. 'flung' are pins sent
  flying as the shot begins (the window's debug 'Fling pins', the user:
  to see one go over a cushion at will), each (number, vx, vy, vz, wx,
  wy, wz), mm/s and rad/s, as the cue sends a ball: from then on all as
  the physics has it.
  """

  motion: KegleMotion = KegleMotion()
  rate: float = 1000.0
  size: int = 50
  longest: float = 60.0
  numbers: tuple = (0, 1, 2, 3, 4)
  flung: tuple = ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def fieldOf(self, ) -> PinField:
    """The 'fieldOf' method returns the pins as a shot begins: 'numbers'
    on their spots, asleep."""
    return self.motion.fieldOf(self.numbers)

  def flungOf(self, ) -> PinField:
    """The 'flungOf' method returns the pins as a shot begins, as
    'fieldOf' does, those 'flung' sent flying, awake."""
    field = self.fieldOf()
    for number, vx, vy, vz, wx, wy, wz in self.flung:
      for pin in field.pins:
        if pin.number == number:
          pin.v, pin.w = [vx, vy, vz], [wx, wy, wz]
          pin.awake = True
    return field

  def stretches(self, balls: tuple[Ball, ...]) -> Iterator[Stretch]:
    """The 'stretches' method plays 'balls' on from now, the pins set
    up, until all rest, yielding the samples a 'Stretch' at a time, the
    last one 'over'."""
    motion, field = self.motion, self.flungOf()
    cloth, radius = motion.motion.cloth, motion.motion.table.radius
    names, every = tuple(ball.name for ball in balls), 1.0 / self.rate
    balls, passed, hits, settled = tuple(balls), 0.0, None, False
    rows, pins, touches, count, first = [], [], [], 0, 0
    while True:
      while count * every <= passed + _DUE:
        rows.append(_rowsOf(balls))
        pins.append(field.rows(names))
        count += 1
      over = settled or motion.resting(balls, field) or (
        passed >= self.longest)
      if over:
        rows.append(_rowsOf(balls))
        pins.append(field.rows(names))
        count += 1
      if over or len(rows) >= self.size:
        yield Stretch(first, numpy.array(rows), tuple(touches), over,
                      numpy.array(pins))
        if over:
          return
        rows, pins, touches, first = [], [], [], count
      if hits is not None or motion.busy(balls, field):
        if hits is None:
          hits = motion.hitsOf(balls, field, True)
        balls, used, began = hits.run(count * every - passed, True)
        passed += used
        touches.extend((passed, touch) for touch in began)
        if hits.over:
          settled = hits.settled
          hits = None
        if used > 0.0 or settled:
          continue
      glide = motion.glided(balls, field, self.longest - passed)
      end, inner, at = passed + glide.span, balls, passed
      still = field.rows(names)
      while count * every < end - _DUE:
        span = count * every - at
        inner = tuple(cloth.moved(ball, phase, span, radius)
                      for ball, phase in zip(inner, glide.phases))
        at = count * every
        rows.append(_rowsOf(inner))
        pins.append(still)
        count += 1
        if len(rows) >= self.size:
          yield Stretch(first, numpy.array(rows), tuple(touches), False,
                        numpy.array(pins))
          rows, pins, touches, first = [], [], [], count
      balls, passed = glide.after, end
      touches.extend((end, touch) for touch in glide.touches)
      balls, caught = motion.captured(balls)
      touches.extend((end, touch) for touch in caught)

  def recorded(self, balls: tuple[Ball, ...]) -> Recording:
    """The 'recorded' method returns the whole shot of 'balls', played
    on until all rest, as a 'Recording', the pins' samples with it."""
    recording = Recording(tuple(ball.name for ball in balls), self.rate)
    for stretch in self.stretches(balls):
      recording = recording.joined(stretch)
    return recording

  def fallenOf(self, recording: Recording) -> tuple[tuple[int, str], ...]:
    """The 'fallenOf' method returns the pins 'recording' leaves knocked
    over, each its number and the ball it is credited to, as
    'PinField.fallen' gives them."""
    field = self.fieldOf()
    field.setRows(recording.lastPins(), recording.names)
    return field.fallen()


def flingOf(table: KegleTable, gravity: float, number: int, rise: float,
            tumble: float) -> tuple:
  """The 'flingOf' function returns how pin 'number' of 'table' is flung
  (a debug, the window's 'Fling pins'; the user: to see a pin go over a
  cushion at will), as 'KegleRecorder.flung' takes it: out of the cross
  the way it stands from its middle (the middle pin between two arms),
  to the long cushion for those on the long arm, up at 'rise' mm/s, as
  fast across as brings it over the cushion's nose at the top of its
  flight under 'gravity', tumbling forward at 'tumble' rad/s."""
  carom = table.table
  mx, my = table.middle()
  x, y = table.pinSpots()[number]
  if abs(x - mx) > 1.0:
    dx, dy = math.copysign(1.0, x - mx), 0.0
  elif abs(y - my) > 1.0:
    dx, dy = -1.0, 0.0
  else:
    dx, dy = -math.sqrt(0.5), -math.sqrt(0.5)
  reaches = []
  if dx:
    reaches.append(((carom.width - x) if dx > 0.0 else x) / abs(dx))
  if dy:
    reaches.append(((carom.length - y) if dy > 0.0 else y) / abs(dy))
  across = min(reaches) * gravity / rise
  return (number, across * dx, across * dy, rise, -tumble * dy,
          tumble * dx, 0.0)


@functools.lru_cache(maxsize=16)
def _engineOf(motion: Motion, table: KegleTable) -> Motion:
  """Returns 'motion' with the pockets of 'table'."""
  return Motion(motion.table, motion.cloth, motion.cushion, motion.carom,
                table.pockets())


@functools.lru_cache(maxsize=16)
def _pocketRulesOf(table: KegleTable) -> object:
  """Returns the kernel's 'PocketRules' for the pockets of 'table'."""
  from . import _kegle_kernels as kernels
  from ._kegle_table import PARKED, PARKED_APART
  pockets = table.pockets()
  rules = kernels.PocketRules()
  rules.corner, rules.half = float(pockets.corner), float(pockets.half)
  rules.radius, rules.parked = float(pockets.radius), PARKED
  rules.apart = PARKED_APART
  return rules


def _goingOf(motion: Motion, balls: tuple[Ball, ...]) -> list:
  """Returns the contacts of 'balls' now as the kernels hold them: each
  ball's four cushions as bits, then a bit, 4 on, each ball it meets."""
  names = [ball.name for ball in balls]
  out = [0] * len(balls)
  for touch in motion.touchesOf(balls):
    k = names.index(touch.first)
    if touch.kind == 'cushion':
      out[k] |= 1 << CUSHIONS.index(touch.second)
    elif touch.kind == 'ball':
      j = names.index(touch.second)
      out[k] |= 1 << (4 + j)
      out[j] |= 1 << (4 + k)
  return out


def _zoneTime(motion: Motion, ball: Ball, phase: str, zone: Zone,
              span: float) -> float | None:
  """Returns how long until 'ball', in 'phase' on the cloth, comes into
  'zone', if it does within 'span'; 'None' if it does not, or is on its
  edge already. Its path is quadratic, so the square of its distance
  from the zone's middle is a quartic in the time."""
  cx, cy, size = zone
  ax, ay = motion.cloth.accelerationOf(ball, phase, motion.table.radius)
  px, py = ball.x - cx, ball.y - cy
  gap = px * px + py * py - size * size
  if gap <= 2.0 * size * _TOUCH:
    return None
  bx, by, hx, hy = ball.vx, ball.vy, 0.5 * ax, 0.5 * ay
  coefficients = [hx * hx + hy * hy, 2.0 * (hx * bx + hy * by),
                  bx * bx + by * by + 2.0 * (hx * px + hy * py),
                  2.0 * (bx * px + by * py), gap]
  return _firstQuarticRoot(coefficients, span)
