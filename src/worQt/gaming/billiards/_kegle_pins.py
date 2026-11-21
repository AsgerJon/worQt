"""
PinField moves keglebillard's pins: each a rigid body standing on the
cloth, rocked, knocked over, sliding and rolling, struck by the balls
and by each other, remembering the ball that set it going.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import NamedTuple

from ._carom_table import Ball
from ._kegle_pin import KeglePin
from ._kegle_table import KegleTable

GRAVITY = 9810.0  # mm/s²
_FOOT_POINTS = 8  # points round the foot's edge meeting the cloth


class PinContacts(NamedTuple):
  """
  PinContacts is how a pin meets things, in mm, g and s, every value
  adjustable, to be balanced against how pins fall on a real table (the
  user's six: a ball may pass between two pins; one pin is common; all
  five from one pass are rare...). Steps: none longer than lets
  anything meeting a pin close 'closeBy' mm. The cloth is stiff and
  dead under a
  pin, 'cloth' g/s² and 'clothDamping' g/s a point, 'clothFriction' its
  grip, 'rolling' how far ahead of where it bears the felt pushes back
  on a pin turning on it, mm, as it does under a ball ('Cloth.rolling'
  of its radius), so a pin rolling on its side comes to a stop;
  a ball meets a pin for 'ballTime' s, giving back 'ballLively' of the
  speed they met at, 'ballFriction' its grip; two pins meet for
  'pinTime' s, 'pinLively', 'pinFriction'; a pin meets a cushion as a
  ball does. Steps: 'fine' through a knock, 'coarse' while the pins
  only rock, slide or fall on the cloth. A pin 'settles', asleep again,
  once slower than 'still' mm/s and 'still' over its length in rad/s
  for 'settle' s, upright, lying, or leaning on a cushion, a ball or a
  pin, never caught leaning free (falling, or balanced on its foot's
  edge a moment); asleep, it wakes only for something coming into it
  faster than 'still', holding as the cloth does against anything
  slower (else two pins leaning on each other woke each other in turn,
  never both asleep, and the shot ran to its end).
  """

  cloth: float = 1.25e8
  clothDamping: float = 3.5e4
  clothFriction: float = 0.35
  rolling: float = 0.3
  ballTime: float = 4e-4
  ballLively: float = 0.7
  ballFriction: float = 0.2
  pinTime: float = 4e-4
  pinLively: float = 0.6
  pinFriction: float = 0.3
  fine: float = 2e-5
  coarse: float = 1e-4
  closeBy: float = 0.1
  still: float = 8.0
  settle: float = 0.05


class Pin:
  """
  Pin is one pin as it moves, in mm, g and s: its 'number', where it
  stands in the cross; its centre of mass 'p' and its speed 'v'; how it
  is turned, 'q', a unit quaternion, scalar first, from the pin's own
  axes, its foot's middle at nought and its axis up z, to the table's;
  its spin 'w' about the table's axes; whether it is 'awake', moving,
  and whether it is 'off' the table, flown over a cushion and
  evaporated where it crossed (the user: as in Portal's grid), out of
  play; the ball it is credited to, 'credit', the one that
  first set it going (8.1), and the ball that pushed it last, 'mover';
  how long it has been still, 'quiet'; whether it leans on a cushion, a
  ball or a pin this step, 'held'.
  """

  __slots__ = ('number', 'p', 'v', 'q', 'w', 'awake', 'off', 'credit',
               'mover', 'quiet', 'held')

  def __init__(self, number: int, x: float, y: float,
               centre: float) -> None:
    self.number = number
    self.p = [x, y, centre]
    self.v = [0.0, 0.0, 0.0]
    self.q = [1.0, 0.0, 0.0, 0.0]
    self.w = [0.0, 0.0, 0.0]
    self.awake = False
    self.off = False
    self.credit = ''
    self.mover = ''
    self.quiet = 0.0
    self.held = False


class PinField:
  """
  PinField moves the pins standing in a keglebillard table's cross
  ('KegleTable'), each a rigid body shaped as 'KeglePin', under gravity
  on the cloth: standing on its foot's edge, it rocks and comes back
  tipped a little, past 'KeglePin.tipping' it falls; lying, it slides
  and rolls, dying on the cloth. Balls push it where they meet its
  surface, and it them back, and pins push each other, with friction;
  the cushions and rails are blocks the table's 'top' high, reaching
  its 'cushion' and 'rail' out past the noses: a pin meets their faces
  and tops, and may fly over them: its middle over a cushion, past the
  noses' line, it is off the table, evaporated where it crossed (the
  user: as in Portal's grid), out of play, knocked over. 'KegleMotion'
  moves the pins with the balls, compiled ('_kegle_kernels'); 'step' is
  the plain Python it is checked against, moving the pins on and pushing
  the balls given, rows as 'Motion' keeps them, the balls themselves
  moved elsewhere ('playedSlowly'). Only the pins awake are moved; a pin
  wakes when something comes into it faster than 'still' (slower, it
  holds as the cloth does) and sleeps once it has lain still a while,
  upright, lying, or leaning on something holding it. Each pin is
  credited to the ball that first set it going, directly or through the
  pins between, red when red and a white do so at once (8.1). 'stands'
  and 'fallen' say how they stand, as the rules count it
  ('KegleTable.pinStands'); 'rows' and 'setRows' hold them as a sample
  does.
  """

  __slots__ = ('table', 'shape', 'contacts', 'pins', 'spheres', 'foot',
               'centre', 'inertia', 'reach', 'widest')

  def __init__(self, table: KegleTable, numbers: tuple = None,
               shape: KeglePin = None,
               contacts: PinContacts = None) -> None:
    self.table = table
    self.shape = shape or KeglePin()
    self.contacts = contacts or PinContacts()
    self.centre = self.shape.centre()
    self.inertia = self.shape.inertia()
    self.spheres = tuple((0.0, 0.0, z - self.centre, size)
                         for z, size in self.shape.spheres())
    radius = self.shape.foot()
    self.foot = tuple((radius * math.cos(2.0 * math.pi * k / _FOOT_POINTS),
                       radius * math.sin(2.0 * math.pi * k / _FOOT_POINTS),
                       -self.centre) for k in range(_FOOT_POINTS))
    self.reach = max(math.hypot(z, size) + size
                     for _, _, z, size in self.spheres)
    self.widest = max(size for _, _, _, size in self.spheres)
    spots = table.pinSpots()
    if numbers is None:
      numbers = tuple(range(len(spots)))
    self.pins = [Pin(k, *spots[k], self.centre) for k in numbers]

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def awake(self, ) -> bool:
    """The 'awake' method tells whether any pin is moving."""
    return any(pin.awake for pin in self.pins)

  def stepFor(self, balls: list) -> float:
    """The 'stepFor' method returns how long the next step may be: so
    nothing about to meet a pin closes more than 'closeBy' mm in it,
    between a 'fine' and a 'coarse' step."""
    contacts = self.contacts
    speed = self._closing(balls, contacts.coarse)
    if speed <= 0.0:
      return contacts.coarse
    return max(contacts.fine, min(contacts.coarse,
                                  contacts.closeBy / speed))

  def step(self, balls: list, dt: float) -> None:
    """The 'step' method moves the pins on 'dt' s, pushed by the cloth,
    the 'balls' (rows as 'Motion' keeps them, pushed back in turn), each
    other and the cushions; the balls are not moved."""
    for pin in self.pins:
      pin.held = False
    for pin in self.pins:
      if not pin.off:
        self._ballsMeet(pin, balls, dt)
    awake = [pin for pin in self.pins if pin.awake]
    for i, pin in enumerate(awake):
      for other in self.pins:
        if other is not pin and not other.off and (
            not other.awake
            or self.pins.index(other) > self.pins.index(pin)):
          self._pinsMeet(pin, other, dt)
    for pin in self.pins:
      if pin.awake:
        self._clothMeets(pin, dt)
        self._wallsMeet(pin, dt)
        self._moved(pin, dt)
        if self._offTable(pin):
          continue
        self._settled(pin, dt)

  def rows(self, names: tuple) -> list:
    """The 'rows' method returns the pins as a sample holds them, each
    'PIN_STATE' numbers ('Stretch.pins'): its number, its centre of
    mass, its turn, whether awake, and the ball it is credited to, by
    its place in the balls' 'names', -1 for none."""
    out = []
    for pin in self.pins:
      credit = names.index(pin.credit) if pin.credit in names else -1
      state = 2.0 if pin.off else 1.0 if pin.awake else 0.0
      out.append([float(pin.number), *pin.p, *pin.q, state,
                  float(credit)])
    return out

  def setRows(self, rows: object, names: tuple) -> None:
    """The 'setRows' method sets the pins as the sample 'rows' holds
    them ('rows'), the field's pins those numbers, still."""
    pins = []
    for row in rows:
      values = [float(value) for value in row]
      pin = Pin(int(values[0]), 0.0, 0.0, 0.0)
      pin.p = values[1:4]
      pin.q = values[4:8]
      pin.awake = 0.5 < values[8] < 1.5
      pin.off = values[8] > 1.5
      credit = int(values[9])
      pin.credit = names[credit] if 0 <= credit < len(names) else ''
      pins.append(pin)
    self.pins = pins

  def playedSlowly(self, balls: tuple, seconds: float,
                   cloth: object) -> tuple:
    """The 'playedSlowly' method returns 'balls' after 'seconds' among
    the pins, the pins moved meanwhile, in plain Python, step by step
    ('step'), the balls moved on 'cloth' only, meeting no cushion and no
    other ball: what the kernel ('KegleMotion') is checked against."""
    rows, passed = [list(ball) for ball in balls], 0.0
    radius = self.table.table.radius
    while passed < seconds:
      dt = min(self.stepFor(rows), seconds - passed)
      self.step(rows, dt)
      rows = [list(cloth.advanced(Ball(*row), dt, radius)) for row in rows]
      passed += dt
    return tuple(Ball(*row) for row in rows)

  def tilt(self, pin: Pin) -> float:
    """The 'tilt' method returns how far 'pin' leans from upright, in
    radians."""
    axis = _rotated(pin.q, (0.0, 0.0, 1.0))
    return math.acos(max(-1.0, min(1.0, axis[2])))

  def footAt(self, pin: Pin) -> tuple[float, float, float]:
    """The 'footAt' method returns where the middle of 'pin's foot is."""
    down = _rotated(pin.q, (0.0, 0.0, -self.centre))
    return pin.p[0] + down[0], pin.p[1] + down[1], pin.p[2] + down[2]

  def stands(self, pin: Pin) -> bool:
    """The 'stands' method tells whether 'pin' stands as it was set up,
    as the rules count it: upright on its foot, the foot wholly inside
    its ring ('KegleTable.pinStands')."""
    if pin.off:
      return False
    x, y, z = self.footAt(pin)
    upright = self.tilt(pin) < math.radians(3.0) and z < 1.0
    return self.table.pinStands(pin.number, x, y, upright)

  def fallen(self, ) -> tuple[tuple[int, str], ...]:
    """The 'fallen' method returns the pins knocked over, each its
    number and the ball it is credited to, as 'KegleShot.fallen' takes
    them."""
    return tuple((pin.number, pin.credit or '?') for pin in self.pins
                 if not self.stands(pin))

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PRIVATE METHODS  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _closing(self, balls: list, dt: float) -> float:
    """Returns the fastest a ball or a pin may meet a pin within 'dt'
    s, mm/s, each pin taken as its axis fattened by its widest; nought
    if none may."""
    radius, fastest = self.table.table.radius, 0.0
    for pin in self.pins:
      if pin.off:
        continue
      foot, top = self._axis(pin)
      speed = math.sqrt(_dot(pin.v, pin.v)) + \
        self.reach * math.sqrt(_dot(pin.w, pin.w))
      for row in balls:
        centre = (row[1], row[2], radius)
        gap = _toSegment(centre, foot, top) - radius - self.widest
        both = math.hypot(row[4], row[5]) + speed
        if gap < both * dt + 1.0:
          fastest = max(fastest, both, 1.0)
      if pin.awake:
        for other in self.pins:
          if other is pin:
            continue
          gap = _segments(foot, top, *self._axis(other)) - \
            2.0 * self.widest
          if gap < 2.0 * speed * dt + 1.0:
            fastest = max(fastest, 2.0 * speed, 1.0)
    return fastest

  def _axis(self, pin: Pin) -> tuple[tuple, tuple]:
    """Returns where 'pin's axis runs, from its foot to its top."""
    foot = self._world(pin, (0.0, 0.0, -self.centre))[0]
    top = self._world(pin, (0.0, 0.0, self.shape.height()
                            - self.centre))[0]
    return foot, top

  def _world(self, pin: Pin, local: tuple, matrix: tuple = None) -> tuple:
    """Returns where the point 'local' of 'pin', from its centre of mass
    in its own axes, is on the table, and its arm from the centre;
    'matrix', its turn, if already known."""
    m = matrix or _matrixOf(pin.q)
    x, y, z = local
    arm = (m[0][0] * x + m[0][1] * y + m[0][2] * z,
           m[1][0] * x + m[1][1] * y + m[1][2] * z,
           m[2][0] * x + m[2][1] * y + m[2][2] * z)
    return (pin.p[0] + arm[0], pin.p[1] + arm[1], pin.p[2] + arm[2]), arm

  def _invInertia(self, pin: Pin) -> tuple:
    """Returns the rows of the inverse of 'pin's inertia about the
    table's axes, 1/(g mm²)."""
    along, across = self.inertia
    matrix = _matrixOf(pin.q)
    inverse = (1.0 / across, 1.0 / across, 1.0 / along)
    return tuple(tuple(sum(matrix[i][k] * inverse[k] * matrix[j][k]
                           for k in range(3)) for j in range(3))
                 for i in range(3))

  def _push(self, pin: Pin, arm: tuple, impulse: tuple,
            inverse: tuple) -> None:
    """Gives 'pin' the 'impulse', g mm/s, at 'arm' from its centre of
    mass, 'inverse' its inverse inertia."""
    mass = self.shape.mass
    for k in range(3):
      pin.v[k] += impulse[k] / mass
    torque = _cross(arm, impulse)
    for i in range(3):
      pin.w[i] += sum(inverse[i][j] * torque[j] for j in range(3))

  def _pointSpeed(self, pin: Pin, arm: tuple) -> tuple:
    """Returns how fast the point of 'pin' at 'arm' moves."""
    spin = _cross(pin.w, arm)
    return tuple(pin.v[k] + spin[k] for k in range(3))

  def _give(self, pin: Pin, arm: tuple, way: tuple,
            inverse: tuple) -> float:
    """Returns how much the point of 'pin' at 'arm' gives along 'way',
    a unit, to an impulse along it: 1/mass and its turning."""
    turned = _cross(arm, way)
    spun = tuple(sum(inverse[i][j] * turned[j] for j in range(3))
                 for i in range(3))
    return 1.0 / self.shape.mass + _dot(_cross(spun, arm), way)

  def _clothMeets(self, pin: Pin, dt: float) -> None:
    """Pushes 'pin' up off the cloth where its foot's edge or its
    surface presses into it, with friction, and pulls it down."""
    contacts = self.contacts
    pin.v[2] -= GRAVITY * dt
    matrix = _matrixOf(pin.q)
    inverse = None
    touching, pressed = False, 0.0
    points = [(local, 0.0) for local in self.foot]
    #  Leaning less than about 66 degrees, only the foot's edge reaches
    #  the cloth: the body, 10 mm round 28 mm up, does once cos < 0.4.
    if matrix[2][2] < 0.4:
      points += [((x, y, z), size) for x, y, z, size in self.spheres]
    for local, size in points:
      place, arm = self._world(pin, local, matrix)
      depth = size - place[2]
      if depth <= 0.0:
        continue
      touching = True
      if inverse is None:
        inverse = self._invInertia(pin)
      arm = (arm[0], arm[1], arm[2] - size)
      speed = self._pointSpeed(pin, arm)
      push = max(contacts.cloth * depth - contacts.clothDamping * speed[2],
                 0.0) * dt
      pressed += push
      self._push(pin, arm, (0.0, 0.0, push), inverse)
      speed = self._pointSpeed(pin, arm)
      slip = math.hypot(speed[0], speed[1])
      if slip > 0.0:
        way = (speed[0] / slip, speed[1] / slip, 0.0)
        #  Half the slip a step at most: the foot's points, taken in
        #  turn, else hand each other a jitter.
        held = min(contacts.clothFriction * push,
                   0.5 * slip / self._give(pin, arm, way, inverse))
        self._push(pin, arm, (-held * way[0], -held * way[1], 0.0),
                   inverse)
    if touching:
      self._rolledAgainst(pin, pressed)

  def _rolledAgainst(self, pin: Pin, pressed: float) -> None:
    """Slows 'pin's turning across the cloth, as the felt pushing back
    'rolling' ahead of where it bears, 'pressed' the cloth's push on it
    this step; never turning it the other way."""
    turning = (pin.w[0], pin.w[1], 0.0)
    size = math.hypot(turning[0], turning[1])
    if size <= 0.0:
      return
    inverse = self._invInertia(pin)
    torque = tuple(-self.contacts.rolling * pressed / size * value
                   for value in turning)
    resist = [sum(inverse[i][j] * torque[j] for j in range(3))
              for i in range(3)]
    lost = -_dot(resist, turning) / size
    if lost > size:
      resist = [value * size / lost for value in resist]
    pin.w = [pin.w[k] + resist[k] for k in range(3)]

  def _wallsMeet(self, pin: Pin, dt: float) -> None:
    """Pushes 'pin' off the cushions and rails where it meets them,
    blocks the table's 'top' high reaching 'cushion' and 'rail' out past
    the noses' lines: their faces, their tops, their edges."""
    carom = self.table.table
    contacts = self.contacts
    inverse = self._invInertia(pin)
    stiff, damp = _spring(self.shape.mass, contacts.ballTime,
                          contacts.ballLively)
    out = carom.cushion + carom.rail
    for x, y, z, size in self.spheres:
      place, arm = self._world(pin, (x, y, z))
      for axis, edge, sign in ((0, 0.0, 1.0), (0, carom.width, -1.0),
                               (1, 0.0, 1.0), (1, carom.length, -1.0)):
        beyond = sign * (edge - place[axis])
        du = beyond - min(max(beyond, 0.0), out)
        dz = place[2] - min(place[2], carom.top)
        apart = math.sqrt(du * du + dz * dz)
        depth, nu, nz = size - apart, 0.0, 0.0
        if apart > 0.0:
          nu, nz = du / apart, dz / apart
        elif beyond < carom.top - place[2]:
          depth, nu = size + beyond, -1.0
        else:
          depth, nz = size + carom.top - place[2], 1.0
        if depth <= 0.0:
          continue
        pin.held = True
        way = [0.0, 0.0, nz]
        way[axis] = -sign * nu
        reach = [arm[k] - size * way[k] for k in range(3)]
        speed = self._pointSpeed(pin, reach)
        push = max(stiff * depth - damp * _dot(speed, way), 0.0) * dt
        self._push(pin, reach, tuple(push * value for value in way),
                   inverse)

  def _ballsMeet(self, pin: Pin, balls: list, dt: float) -> None:
    """Pushes 'pin' and the 'balls' it meets apart, with friction, the
    pin woken and credited to the first ball to set it going; asleep and
    met no faster than 'still', it holds as the cloth does, the ball
    alone pushed."""
    radius = self.table.table.radius
    contacts = self.contacts
    met = []
    for row in balls:
      if math.hypot(row[1] - pin.p[0], row[2] - pin.p[1]) > \
          radius + self.reach:
        continue
      centre = (row[1], row[2], radius)
      inverse = self._invInertia(pin)
      for x, y, z, size in self.spheres:
        place, arm = self._world(pin, (x, y, z))
        gap = _distance(place, centre)
        depth = radius + size - gap
        if depth <= 0.0 or gap <= 0.0:
          continue
        pin.held = True
        way = tuple((place[k] - centre[k]) / gap for k in range(3))
        reach = tuple(arm[k] - size * way[k] for k in range(3))
        ballArm = tuple(radius * way[k] for k in range(3))
        ballSpeed = (row[4] + row[7] * ballArm[2] - row[8] * ballArm[1],
                     row[5] + row[8] * ballArm[0] - row[6] * ballArm[2],
                     row[6] * ballArm[1] - row[7] * ballArm[0])
        pinSpeed = self._pointSpeed(pin, reach)
        closing = _dot(tuple(ballSpeed[k] - pinSpeed[k]
                             for k in range(3)), way)
        both = 1.0 / (1.0 / self.shape.mass + 1.0 / _BALL_MASS)
        stiff, damp = _spring(both, contacts.ballTime, contacts.ballLively)
        push = max(stiff * depth + damp * closing, 0.0) * dt
        if push <= 0.0:
          continue
        moved = pin.awake or closing > contacts.still
        if moved:
          pin.awake = True
          met.append(row[0])
          self._push(pin, reach, tuple(push * value for value in way),
                     inverse)
        _ballPushed(row, ballArm, tuple(-push * value for value in way),
                    radius)
        pinSpeed = self._pointSpeed(pin, reach)
        slip = tuple(ballSpeed[k] - pinSpeed[k] for k in range(3))
        across = _dot(slip, way)
        slip = tuple(slip[k] - across * way[k] for k in range(3))
        size = math.sqrt(_dot(slip, slip))
        if size > 0.0:
          unit = tuple(value / size for value in slip)
          give = 3.5 / _BALL_MASS
          if moved:
            give += self._give(pin, reach, unit, inverse)
          gripped = min(contacts.ballFriction * push, size / give)
          if moved:
            self._push(pin, reach, tuple(gripped * value for value in unit),
                       inverse)
          _ballPushed(row, ballArm, tuple(-gripped * value
                                          for value in unit), radius)
    if met:
      mover = 'red' if 'red' in met else met[0]
      pin.mover = mover
      if not pin.credit:
        pin.credit = mover

  def _pinsMeet(self, pin: Pin, other: Pin, dt: float) -> None:
    """Pushes the pins 'pin' and 'other' apart where they meet; the
    other woken, credited to the one moving it; but asleep and met no
    faster than 'still', it holds as the cloth does, 'pin' alone
    pushed. Both are 'held'."""
    otherFoot, otherTop = self._axis(other)
    if _segments(*self._axis(pin), otherFoot, otherTop) > \
        2.0 * self.widest:
      return
    contacts = self.contacts
    stiff, damp = _spring(0.5 * self.shape.mass, contacts.pinTime,
                          contacts.pinLively)
    inverse, otherInverse = self._invInertia(pin), self._invInertia(other)
    myTurn, otherTurn = _matrixOf(pin.q), _matrixOf(other.q)
    others = [(*self._world(other, (ox, oy, oz), otherTurn), otherSize)
              for ox, oy, oz, otherSize in self.spheres]
    for x, y, z, size in self.spheres:
      place, arm = self._world(pin, (x, y, z), myTurn)
      if _toSegment(place, otherFoot, otherTop) > size + self.widest:
        continue
      for there, otherArm, otherSize in others:
        gap = _distance(place, there)
        depth = size + otherSize - gap
        if depth <= 0.0 or gap <= 0.0:
          continue
        pin.held = other.held = True
        way = tuple((there[k] - place[k]) / gap for k in range(3))
        reach = tuple(arm[k] + size * way[k] for k in range(3))
        otherReach = tuple(otherArm[k] - otherSize * way[k]
                           for k in range(3))
        mine = self._pointSpeed(pin, reach)
        theirs = self._pointSpeed(other, otherReach)
        closing = _dot(tuple(mine[k] - theirs[k] for k in range(3)), way)
        push = max(stiff * depth + damp * closing, 0.0) * dt
        if push <= 0.0:
          continue
        if not other.awake and closing <= contacts.still:
          self._push(pin, reach, tuple(-push * value for value in way),
                     inverse)
          continue
        if not other.awake:
          other.awake = True
        if pin.mover and not other.credit:
          other.credit = pin.mover
        if pin.mover:
          other.mover = pin.mover
        self._push(pin, reach, tuple(-push * value for value in way),
                   inverse)
        self._push(other, otherReach, tuple(push * value for value in way),
                   otherInverse)

  def _moved(self, pin: Pin, dt: float) -> None:
    """Moves 'pin' on 'dt' at its speed and spin."""
    for k in range(3):
      pin.p[k] += pin.v[k] * dt
    pin.q = _turned(pin.q, pin.w, dt)

  def _offTable(self, pin: Pin) -> bool:
    """Tells whether 'pin' has flown over a cushion, its middle past
    the noses' line, off the table, and if so evaporates it there (the
    user: as in Portal's grid), stopped where it crossed, out of
    play."""
    carom = self.table.table
    x, y = pin.p[0], pin.p[1]
    if 0.0 <= x <= carom.width and 0.0 <= y <= carom.length:
      return False
    pin.v, pin.w = [0.0, 0.0, 0.0], [0.0, 0.0, 0.0]
    pin.awake, pin.off, pin.quiet = False, True, 0.0
    return True

  def _settled(self, pin: Pin, dt: float) -> None:
    """Puts 'pin' to sleep once it has lain still 'settle' s: upright,
    lying, or leaning on a cushion, a ball or a pin; leaning free it is
    falling, or balanced on its foot's edge a moment, never asleep."""
    contacts = self.contacts
    speed = math.sqrt(_dot(pin.v, pin.v))
    spin = math.sqrt(_dot(pin.w, pin.w)) * self.shape.height()
    tilt = self.tilt(pin)
    resting = (tilt < math.radians(2.0) or tilt > math.radians(80.0)
               or pin.held)
    if resting and speed < contacts.still and spin < contacts.still:
      pin.quiet += dt
    else:
      pin.quiet = 0.0
    if pin.quiet >= contacts.settle:
      pin.awake = False
      pin.v = [0.0, 0.0, 0.0]
      pin.w = [0.0, 0.0, 0.0]
      pin.quiet = 0.0


_BALL_MASS = 207.0  # g, as DDBU's material rules have a ball


def _spring(mass: float, time: float, lively: float) -> tuple:
  """Returns the stiffness and the damping, g/s² and g/s, of a contact
  between bodies of 'mass' together, lasting 'time' and giving back
  'lively' of the speed they met at."""
  fall = math.log(lively)
  ratio = -fall / math.sqrt(math.pi ** 2 + fall ** 2)
  swing = math.pi / (time * math.sqrt(1.0 - ratio * ratio))
  return mass * swing * swing, 2.0 * ratio * swing * mass


def _rulesOf(field: PinField) -> object:
  """Returns the kernel's 'PinRules' for 'field'."""
  from . import _kegle_kernels as kernels
  from ._cloth import Cloth
  rules = kernels.PinRules()
  contacts, shape = field.contacts, field.shape
  carom = field.table.table
  along, across = field.inertia
  both = 1.0 / (1.0 / shape.mass + 1.0 / _BALL_MASS)
  ballStiff, ballDamp = _spring(both, contacts.ballTime,
                                contacts.ballLively)
  pinStiff, pinDamp = _spring(0.5 * shape.mass, contacts.pinTime,
                              contacts.pinLively)
  wallStiff, wallDamp = _spring(shape.mass, contacts.ballTime,
                                contacts.ballLively)
  cloth = Cloth()
  #  The least the felt slows a pin moving on it, mm/s²: rolling like a
  #  log on its widest, against the felt's push 'rolling' ahead.
  slowest = GRAVITY * contacts.rolling * field.widest * shape.mass / (
    shape.mass * field.widest * field.widest + along)
  values = {
    'mass': shape.mass, 'centre': field.centre, 'height': shape.height(),
    'widest': field.widest, 'reach': field.reach, 'invAlong': 1.0 / along,
    'invAcross': 1.0 / across, 'foot': shape.foot(), 'gravity': GRAVITY,
    'cloth': contacts.cloth, 'clothDamping': contacts.clothDamping,
    'clothFriction': contacts.clothFriction, 'rolling': contacts.rolling,
    'slowest': max(slowest, 1e-9), 'ballStiff': ballStiff,
    'ballDamp': ballDamp,
    'ballFriction': contacts.ballFriction, 'pinStiff': pinStiff,
    'pinDamp': pinDamp, 'pinFriction': contacts.pinFriction,
    'wallStiff': wallStiff, 'wallDamp': wallDamp, 'fine': contacts.fine,
    'coarse': contacts.coarse, 'closeBy': contacts.closeBy,
    'still': contacts.still, 'settle': contacts.settle,
    'radius': carom.radius, 'ballMass': _BALL_MASS,
    'sliding': cloth.sliding, 'rollingDecay': cloth.rollingDecay(),
    'spinDecay': cloth.spinDecay(carom.radius), 'spinTail': cloth.spinTail,
    'spinStop': cloth.spinStop, 'width': carom.width,
    'length': carom.length, 'top': carom.top,
    'out': carom.cushion + carom.rail}
  for name, value in values.items():
    setattr(rules, name, float(value))
  return rules


def _ballPushed(row: list, arm: tuple, impulse: tuple,
                radius: float) -> None:
  """Gives the ball in 'row' the 'impulse', g mm/s, at 'arm' from its
  middle: its speed along the cloth and its spin; up and down the slate
  takes it."""
  inertia = 0.4 * _BALL_MASS * radius * radius
  row[4] += impulse[0] / _BALL_MASS
  row[5] += impulse[1] / _BALL_MASS
  torque = _cross(arm, impulse)
  row[6] += torque[0] / inertia
  row[7] += torque[1] / inertia
  row[8] += torque[2] / inertia


def _dot(a: tuple, b: tuple) -> float:
  """Returns the dot product of 'a' and 'b'."""
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: tuple, b: tuple) -> tuple:
  """Returns the cross product of 'a' and 'b'."""
  return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2],
          a[0] * b[1] - a[1] * b[0])


def _distance(a: tuple, b: tuple) -> float:
  """Returns how far 'a' and 'b' are apart."""
  return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2
                   + (a[2] - b[2]) ** 2)


def _toSegment(point: tuple, start: tuple, end: tuple) -> float:
  """Returns how far 'point' is from the segment 'start' to 'end'."""
  way = tuple(end[k] - start[k] for k in range(3))
  length = _dot(way, way)
  share = 0.0
  if length > 0.0:
    off = tuple(point[k] - start[k] for k in range(3))
    share = max(0.0, min(1.0, _dot(off, way) / length))
  return _distance(point, tuple(start[k] + share * way[k]
                                for k in range(3)))


def _segments(a0: tuple, a1: tuple, b0: tuple, b1: tuple) -> float:
  """Returns how far the segments 'a0'-'a1' and 'b0'-'b1' come to
  each other."""
  d1 = tuple(a1[k] - a0[k] for k in range(3))
  d2 = tuple(b1[k] - b0[k] for k in range(3))
  r = tuple(a0[k] - b0[k] for k in range(3))
  a, e, f = _dot(d1, d1), _dot(d2, d2), _dot(d2, r)
  c, b = _dot(d1, r), _dot(d1, d2)
  denom = a * e - b * b
  s = max(0.0, min(1.0, (b * f - c * e) / denom)) if denom > 1e-12 \
    else 0.0
  t = (b * s + f) / e if e > 0.0 else 0.0
  if t < 0.0:
    t, s = 0.0, max(0.0, min(1.0, -c / a)) if a > 0.0 else 0.0
  elif t > 1.0:
    t, s = 1.0, max(0.0, min(1.0, (b - c) / a)) if a > 0.0 else 0.0
  return _distance(tuple(a0[k] + s * d1[k] for k in range(3)),
                   tuple(b0[k] + t * d2[k] for k in range(3)))


def _rotated(q: list, v: tuple) -> tuple:
  """Returns 'v' turned by the unit quaternion 'q', scalar first."""
  w, x, y, z = q
  tx = 2.0 * (y * v[2] - z * v[1])
  ty = 2.0 * (z * v[0] - x * v[2])
  tz = 2.0 * (x * v[1] - y * v[0])
  return (v[0] + w * tx + y * tz - z * ty,
          v[1] + w * ty + z * tx - x * tz,
          v[2] + w * tz + x * ty - y * tx)


def _matrixOf(q: list) -> tuple:
  """Returns the rows of the turn 'q', scalar first, as a matrix."""
  w, x, y, z = q
  return ((1 - 2 * (y * y + z * z), 2 * (x * y - w * z),
           2 * (x * z + w * y)),
          (2 * (x * y + w * z), 1 - 2 * (x * x + z * z),
           2 * (y * z - w * x)),
          (2 * (x * z - w * y), 2 * (y * z + w * x),
           1 - 2 * (x * x + y * y)))


def _turned(q: list, w: list, dt: float) -> list:
  """Returns 'q' turned on by the spin 'w', rad/s about the table's
  axes, for 'dt' s, kept of length one."""
  angle = math.sqrt(_dot(w, w)) * dt
  if angle < 1e-15:
    return q
  share = math.sin(0.5 * angle) / (angle / dt)
  a = (math.cos(0.5 * angle), w[0] * share, w[1] * share, w[2] * share)
  b = q
  out = [a[0] * b[0] - a[1] * b[1] - a[2] * b[2] - a[3] * b[3],
         a[0] * b[1] + a[1] * b[0] + a[2] * b[3] - a[3] * b[2],
         a[0] * b[2] - a[1] * b[3] + a[2] * b[0] + a[3] * b[1],
         a[0] * b[3] + a[1] * b[2] - a[2] * b[1] + a[3] * b[0]]
  size = math.sqrt(sum(value * value for value in out))
  return [value / size for value in out]
