"""
Minecart is the loop's first vehicle (user, 2026-11-16: "it's loop
time! let's get a 'minecart' but fr on that track"; "deploy that shit":
the spec "Trains: the math first"'s two-axle cart with axleboxes), now
shaped as a racing car (user, 2026-11-16: "make the cart be sort of
fomula one shaped kinda but with real rail wheel wheelbase
dimensions"): an open-wheeled body on two real wheelsets a standard
two-axle wagon's wheelbase apart, each journal held in an axlebox
(rubber, Palmgren's bearing); the body solid in the world (sat in,
loaded, punted), the wheels rolled by the rail world. A powered one
(user, 2026-11-16: "do all the things": a train) has a traction motor
in every axlebox, worked by a throttle and a reverser beside its brake;
a cart may be coupled to the one ahead of it by a drawbar.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import functools
import math
from typing import TYPE_CHECKING

from worQt.phys._assembly import Contact, Spring, Tie
from worQt.phys._body import Body, State
from worQt.phys._shape import Shape, boxShape, cylinderShape
from worQt.phys._vectors import UNTURNED, product, turnAbout, turnOf
from worQt.phys.rail import JOURNAL_AT, Axlebox, wheelsetBody, wheelsetOn
from worQt.phys.rail._wheelset import AXLE, AXLE_END, BACK, FACE
from worQt.phys.rail._wheelset import FLANGE_HIGH, NOMINAL, RADIUS
from worQt.phys.rail._wheelset import ROOT_AT

from worQt.gaming.sandbox._fourthpeep import FourthPeep
from worQt.gaming.sandbox._vehicle import Vehicle

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worQt.gaming.sandbox import World

#  Half the wheelbase, m: the shorter of the standard two-axle wagons'
#  6 and 8 m (UIC 571-1); a racing car's is 3.6 m at most.
HALF_BASE = 3.0
#  The body's mass, kg: about a racing car's without its driver and its
#  wheels (798 kg with the driver, 2022-2025 rules); its pieces are
#  solid, all of one density making it so.
BODY_MASS = 700.0
#  The body's pieces, m, in its own frame (x along the track, the nose
#  ahead; y to the left; z up from the rails' top at the track's
#  middle), each a block between two cross sections (x, y from, y to, z
#  from, z to), behind and ahead; those marked 'both' on either side
#  (the cross section's y on the left). Kept clear: of each axle (0.08
#  m round, 0.46 up) by 0.16 m along and up and down (the axleboxes give
#  ~70 mm at the loop's ~5 g), of each wheel (0.92 m across, 0.66-0.815
#  out); over the rails (0.72-0.79 out) 0.30 m where between the axles
#  (over a crest of 20 m radius the middle comes 0.225 m nearer the
#  rails) and 0.53 m ahead of and behind them (in the 10 m loop a point
#  0.95 m past an axle comes 0.33 m nearer; at its entry, the front
#  wheels in it and the back ones not, the body pitches and its back
#  end came within 29 mm of the rails at 0.48 m).
PIECES = (
  ('floor', (-2.40, -0.80, 0.80, 0.30, 0.35),
   (2.40, -0.80, 0.80, 0.30, 0.35), False),
  ('cockpit wall', (-0.45, 0.33, 0.45, 0.35, 0.85),
   (0.40, 0.33, 0.45, 0.35, 0.85), True),
  ('footwell', (0.40, -0.45, 0.45, 0.35, 0.85),
   (2.40, -0.28, 0.28, 0.35, 0.78), False),
  ('nose', (2.40, -0.28, 0.28, 0.66, 0.78),
   (3.20, -0.20, 0.20, 0.66, 0.74), False),
  ('nose tip', (3.20, -0.20, 0.20, 0.66, 0.74),
   (3.75, -0.08, 0.08, 0.58, 0.64), False),
  ('front wing', (3.55, -0.95, 0.95, 0.53, 0.58),
   (3.95, -0.95, 0.95, 0.53, 0.58), False),
  ('front endplate', (3.55, 0.95, 0.98, 0.47, 0.67),
   (3.95, 0.95, 0.98, 0.47, 0.67), True),
  ('front fork', (2.93, 0.98, 1.11, 0.39, 0.56),
   (3.95, 0.98, 1.11, 0.39, 0.56), True),
  ('sidepod', (-1.60, 0.45, 0.62, 0.35, 0.55),
   (1.30, 0.45, 0.82, 0.35, 0.75), True),
  ('engine cover', (-2.45, -0.22, 0.22, 0.35, 0.80),
   (-0.45, -0.45, 0.45, 0.35, 1.08), False),
  ('gearbox', (-3.50, -0.16, 0.16, 0.66, 0.80),
   (-2.45, -0.16, 0.16, 0.66, 0.80), False),
  ('rear beam', (-3.95, -0.98, 0.98, 0.53, 0.61),
   (-3.55, -0.98, 0.98, 0.53, 0.61), False),
  ('beam post', (-3.55, -0.10, 0.10, 0.53, 0.80),
   (-3.50, -0.10, 0.10, 0.53, 0.80), False),
  ('rear fork', (-3.95, 0.98, 1.11, 0.39, 0.56),
   (-2.93, 0.98, 1.11, 0.39, 0.56), True),
  ('wing pillar', (-3.70, -0.03, 0.03, 0.61, 0.98),
   (-3.58, -0.03, 0.03, 0.61, 0.98), False),
  ('rear wing', (-3.95, -0.50, 0.50, 0.98, 1.04),
   (-3.55, -0.50, 0.50, 0.98, 1.04), False),
  ('rear flap', (-3.90, -0.50, 0.50, 1.07, 1.12),
   (-3.68, -0.50, 0.50, 1.07, 1.12), False),
  ('rear endplate', (-3.98, 0.50, 0.53, 0.70, 1.15),
   (-3.52, 0.50, 0.53, 0.70, 1.15), True))
#  The axleboxes: stiff rubber along and across, N/m, soft up and down
#  (the loop's helix twists the track 4.8 mrad a metre: over the
#  wheelbase its journals stand ~15 mm off one plane, which these take
#  as ~1.8 kN; the body bounces at ~4 Hz on them), damped, N s/m.
BOX_STIFFNESS = (2e6, 2e6, 1.2e5)
BOX_DAMPING = (1.3e4, 1.3e4, 2.8e3)
#  How the body touches what it meets (the small steps take only its
#  grip): stiffness, damping, grip, bristle, its damping, its edges met
#  every 0.1 m.
BODY_LAW = (1e6, 1.0, 0.5, 1e6, 2e3, 0.1)
#  How the body of a derailed cart touches the track and the island, its
#  edges (and theirs) met every 0.2 m (every 0.1 m a wreck lying on the
#  track was 45 ms a frame on the GPU).
WRECK_LAW = BODY_LAW[:5] + (0.2,)
#  Where a rider's ball is held: in the cockpit, on the floor, m.
SEAT = (0.0, 0.0, 0.35 + 0.305)
#  The brake (user, 2026-11-16: "4peep, send it!", the FourthPeep's first
#  lever): its lever on the cockpit's floor right of the seat (pivot, m,
#  the body's own frame), its handle long, m, turning about the body's
#  left from leaning ahead (released) to leaning back (pulled), rad (its
#  knob within the cockpit's opening, just over its walls: leaning
#  further ahead it went into the footwell); its
#  shoes at full pull hold each wheel this hard against turning in its
#  box, N m (2 kN m a wheelset, ~4.3 kN at the rails: ~0.33 g for the
#  2.7 t cart, about what the rails grip: pulled hard the wheels may
#  slide).
LEVER = (0.05, -0.27, 0.35)
LEVER_LONG, LEVER_NEAR, LEVER_FAR = 0.55, 0.35, -0.55
BRAKE_MOST = 1000.0
#  A powered cart's throttle, left of the seat as the brake is right of
#  it, and its reverser behind the throttle (pivots, m, as the brake's;
#  thrown back each: open, reversed); each box's motor at full throttle,
#  N m and W (2.4 kN m on the two wheelsets, ~5.2 kN at the rails: ~1.3
#  kN a wheel against the ~2 kN its rail grips; 200 kW all four, so its
#  torque holds up to ~38 m/s).
THROTTLE = (0.05, 0.27, 0.35)
REVERSER = (-0.30, 0.27, 0.35)
DRIVE_MOST, POWER_MOST = 600.0, 50e3
#  The coupling (a drawbar, steel, square, 'BAR_THICK' m, on a ball
#  joint at either end): its joints on the cars' noses and tails (the
#  front wing's and the rear beam's faces, x, m) at the same height (z,
#  m), the gap between the cars, m (in the 10 m loop the cars' ends
#  close up on the inside: their tops, 1.15 m up, ~0.5 m of it); how
#  far apart the coupled cars' middles are, m.
NOSE, TAIL, HITCH_UP = 3.95, -3.95, 0.56
BAR_THICK, COUPLER_GAP = 0.1, 1.2
COUPLED = NOSE - TAIL + COUPLER_GAP
STEEL = 7850.0
#  A wheelset off its rails (user, 2026-11-16: "derail shouldn't mean
#  RuntimeError!") is a free body of the world: the wheelset's own mass,
#  centre and inertia, its shape two wheels (each its flange and its
#  tread) and the axle as cylinders of so many sides, held in each box
#  by a spring and a damper as stiff and as damped as the box along the
#  track ('offRailsBody', 'Minecart.derailed').
WHEEL_SIDES, AXLE_SIDES = 24, 10
#  A box's faces (as 'boxShape' winds them, its corners numbered by the
#  bits x, y, z).
_FACES = boxShape(1.0, 1.0, 1.0).faces


def _block(back: tuple, front: tuple) -> Shape:
  """Returns the block between the cross sections 'back' and 'front',
  each (x, y from, y to, z from, z to) (its faces flat: each side's
  edges at either end are square to x)."""
  points = []
  for i in range(8):
    x, y0, y1, z0, z1 = front if i & 1 else back
    points.append((x, y1 if i & 2 else y0, z1 if i & 4 else z0))
  return Shape(tuple(points), _FACES)


@functools.lru_cache(None)
def cartBody() -> Body:
  """Returns the cart's body: its 'PIECES' as one, weighing
  'BODY_MASS'."""
  shape = None
  for _, back, front, both in PIECES:
    sides = [(back, front)]
    if both:
      sides.append(tuple((x, -y1, -y0, z0, z1)
                         for x, y0, y1, z0, z1 in (back, front)))
    for ends in sides:
      piece = _block(*ends)
      shape = piece if shape is None else shape.joined(piece)
  return Body.of(shape, BODY_MASS / shape.moments()[0])


@functools.lru_cache(None)
def offRailsBody() -> Body:
  """Returns a wheelset off its rails: the wheelset's mass, centre and
  inertia, its shape cylinders of 'WHEEL_SIDES' (each wheel's flange and
  tread) and 'AXLE_SIDES' (the axle, journal to journal), its axle along
  its own z as the wheelset's."""
  wheels = wheelsetBody()
  root = NOMINAL + ROOT_AT
  shape = cylinderShape(AXLE, 2.0 * AXLE_END, AXLE_SIDES)
  for side in (1.0, -1.0):
    for radius, low, high in ((RADIUS + FLANGE_HIGH, BACK, root),
                              (RADIUS, root, FACE)):
      shape = shape.joined(cylinderShape(radius, high - low, WHEEL_SIDES)
                           .moved((0.0, side * 0.5 * (low + high), 0.0),
                                  UNTURNED))
  shape = shape.moved((0.0, 0.0, 0.0), turnAbout((1.0, 0.0, 0.0),
                                                 0.5 * math.pi))
  return Body(wheels.mass, wheels.centre, wheels.inertia, shape)


class Minecart(Vehicle):
  """
  Minecart is a cart on its world's track 'line' (its index among the
  world's 'tracks', ribbons) at 'along' m (standing still where it is
  put): its body ('cartBody', the frame: the seat 'SEAT' in its
  cockpit) and two wheelsets ('wheelsets') 'HALF_BASE' m either side,
  each journal in an 'Axlebox' at the end of a fork; its world steps the
  wheelsets in a rail world. Its 'lever' (a 'FourthPeep' beside the
  seat) works its brake: each box's shoes hold 'BRAKE_MOST' times how
  far it is pulled. A 'powered' one has a motor in each box, its
  'throttle' left of the seat (each box driving 'DRIVE_MOST' within
  'POWER_MOST' times how far it is opened) and its 'reverser' behind it
  (thrown back: driving backward). One coupled to 'leading' (the cart
  ahead of it, already placed; None: none) holds it by a drawbar from
  its nose to that one's tail, a ball joint at either end (the bar a
  body of its own, among its 'bodies', last). It acts each step:
  a wheelset the rail world found off the rails ('derailed') it makes a
  free body of the world ('offRailsBody', held in its boxes by springs
  and dampers), and its body then meets the track and the island too;
  put back, it is made as it was ('restored').
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Class Variables
  seat = SEAT
  name = 'Minecart'

  #  Public Variables
  along: float
  line: int
  powered: bool
  leading: object
  wheelsets: tuple
  boxes: tuple
  off: dict
  lever: FourthPeep
  throttle: FourthPeep
  reverser: FourthPeep

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def __init__(self, along: float, line: int, powered: bool,
               leading: object) -> None:
    Vehicle.__init__(self, )
    self.along, self.line, self.powered = along, line, powered
    self.leading, self.wheelsets, self.boxes, self.off = leading, (), (), {}
    self.lever = self.throttle = self.reverser = None
    self._apart, self._touching = frozenset(), ()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PARENT METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def placed(self, world: World) -> None:
    """The 'placed' method puts the body on the track at 'along' and the
    wheelsets under its forks, still, and holds each journal in its
    axlebox. The body touches what is spawned (riders, items, carts) and
    the world's 'buffers' (its buffer stops, if it has any), not the
    rest of the world's own bodies (the track, the island): held over
    the rails by its wheels it cannot reach them, and the wheels
    leaving the rails stops the rail world loudly first."""
    track, body = world.tracks[self.line], cartBody()
    place, frame = track.frameAt(self.along)
    rows = tuple(tuple(float(x) for x in row) for row in frame)
    centre = tuple(float(place[i]) + sum(rows[i][j] * body.centre[j]
                                         for j in range(3))
                   for i in range(3))
    apart = world.still - set(getattr(world, 'buffers', ()))
    index = world.spawned(body, State(centre, turnOf(rows)), BODY_LAW,
                          'powered' if self.powered else 'cart', apart)
    self._apart = frozenset(apart)
    wheels, wheelsets, boxes = wheelsetBody(), [], []
    for x in (HALF_BASE, -HALF_BASE):
      wheelset = world.spawned(wheels, wheelsetOn(track, self.along + x,
                                                  0.0), BODY_LAW, 'wheel')
      wheelsets.append(wheelset)
      for side in (1.0, -1.0):
        box = Axlebox(wheelset, side, index, (x, side * JOURNAL_AT, RADIUS),
                      BOX_STIFFNESS, BOX_DAMPING)
        world.connected(box)
        boxes.append(box)
    self.world, self.wheelsets = world, tuple(wheelsets)
    self.bodies, self.boxes = (index,) + self.wheelsets, tuple(boxes)
    if self.leading is not None:
      self.bodies += (self._coupled(world, track),)
    self.lever = self._levered('brake', LEVER, None)
    if self.powered:
      self.throttle = self._levered('throttle', THROTTLE, (
        'Open the throttle', 'Close the throttle'))
      self.reverser = self._levered('reverser', REVERSER, (
        'Reverse', 'Drive ahead'))
    world.addActor(self)

  def acted(self, states: list, seconds: float) -> None:
    """The 'acted' method takes over each of its wheelsets the rail world
    found off the rails in its last call ('derailed'), and sets each
    box's brake as its lever stands."""
    derailed = getattr(self.world.solver, 'derailed', ())
    for index in self.wheelsets:
      if index in derailed and index not in self.off:
        self.derailed(index, states)
    opened = self.throttle.value if self.powered else 0.0
    way = -1.0 if self.powered and self.reverser.value > 0.5 else 1.0
    for box in self.boxes:
      box.brake = BRAKE_MOST * self.lever.value
      box.drive, box.power = way * DRIVE_MOST * opened, POWER_MOST * opened

  def readout(self, states: tuple) -> str:
    """The 'readout' method returns what the cart says of itself: its
    speed and how far its brake is pulled (powered, how far its throttle
    is open and which way it drives)."""
    text = '%s    brake %.0f %%' % (Vehicle.readout(self, states),
                                    100.0 * self.lever.value)
    if self.powered:
      text += '    throttle %.0f %% %s' % (
        100.0 * self.throttle.value, 'reversed'
        if self.reverser.value > 0.5 else 'ahead')
    return text

  def derailed(self, index: int, states: list) -> None:
    """The 'derailed' method makes the wheelset at 'index' a free body of
    the world in 'states' ('offRailsBody'): its axleboxes let go, a
    spring and a damper from each box to its journal instead; it no
    longer passes through the body (their contact let go: the forks hold
    its journals); put back at its boxes, moving as they move, spinning
    as it spun (the rail world held it where it left the rails, up to a
    call back); and the body now meets the track and the island (what
    it was apart from: on its wheels it never could)."""
    world, frame = self.world, self.frame
    body, carried = world.assembly.bodies[frame], states[frame]
    boxes = [box for box in self.boxes if box.wheelset == index]
    springs, contacts = [], [
      c for c in world.assembly.connections if isinstance(c, Contact)
      and {c.first, c.second} == {frame, index}]
    for box in boxes:
      world.loosened(box)
      spring = Spring(frame, box.box, index, (0.0, 0.0, box.side
                                              * JOURNAL_AT),
                      BOX_STIFFNESS[0], 0.0, BOX_DAMPING[0])
      world.connected(spring)
      springs.append(spring)
    for contact in contacts:
      world.loosened(contact)
    world.swapped(index, offRailsBody())
    middle = (boxes[0].box[0], 0.0, RADIUS)
    states[index] = State(
      body.placeOf(carried, middle),
      product(carried.turn, turnAbout((1.0, 0.0, 0.0), -0.5 * math.pi)),
      body.velocityOf(carried, middle), states[index].spin)
    self.off[index] = (tuple(boxes), tuple(springs), tuple(contacts))
    if not self._touching:
      touching = []
      for other in sorted(self._apart):
        contact = Contact(other, frame, *WRECK_LAW)
        world.connected(contact)
        touching.append(contact)
      self._touching = tuple(touching)

  def restored(self, ) -> None:
    """The 'restored' method puts its wheelsets taken over back on the
    rails as they were made: the wheelset's body, its axleboxes and its
    contact with the body; the body apart from the track again."""
    world = self.world
    for index, (boxes, springs, contacts) in self.off.items():
      world.swapped(index, wheelsetBody())
      for spring in springs:
        world.loosened(spring)
      for connection in boxes + contacts:
        world.connected(connection)
    for contact in self._touching:
      world.loosened(contact)
    self.off, self._touching = {}, ()

  def rumble(self, states: tuple) -> tuple | None:
    """The 'rumble' method returns how the cart sounds: the body's
    speed, its wheels' load (all four rails' points, as the rail world
    last pressed them) over the cart standing, the gauge corners'
    (flanges') share of it; None till the rail world has rolled it."""
    solver = self.world.solver
    rolling = getattr(solver, 'rolling', None)
    if not rolling:
      return None
    total = flanged = 0.0
    for index in self.wheelsets:
      if index in self.off:
        continue
      for (_, kind), load in rolling.get(index, {}).get('loads',
                                                         {}).items():
        total += load
        if kind == 1:
          flanged += load
    bodies = self.world.assembly.bodies
    standing = 9.81 * sum(bodies[index].mass for index in (
      self.frame,) + self.wheelsets)
    speed = sum(v * v for v in states[self.frame].velocity) ** 0.5
    return speed, total / standing, flanged / total if total > 0.0 else 0.0

  def _levered(self, name: str, pivot: tuple, prompts: tuple) -> FourthPeep:
    """Returns a lever working 'name' at 'pivot' on the body (turning as
    the brake's does: thrown back), put in the world among its levers."""
    lever = FourthPeep(name, self.frame, pivot, (0.0, 1.0, 0.0), LEVER_LONG,
                       LEVER_NEAR, LEVER_FAR, prompts)
    self.world.addFourthPeep(lever)
    return lever

  def _coupled(self, world: World, track: object) -> int:
    """Puts the drawbar between this cart's nose and the tail of the cart
    ahead ('leading') in 'world' and returns its index: a steel bar from
    one to the other, a ball joint ('Tie') at either end, touching
    nothing in the world yet (what is spawned later meets it)."""
    ahead, frame = self.leading, self.frame
    body = world.assembly.bodies[frame]
    states = world.states
    tail = world.assembly.bodies[ahead.frame].placeOf(
      states[ahead.frame], (TAIL, 0.0, HITCH_UP))
    nose = body.placeOf(states[frame], (NOSE, 0.0, HITCH_UP))
    long = math.dist(tail, nose)
    bar = Body.of(boxShape(long, BAR_THICK, BAR_THICK), STEEL)
    along = tuple((t - n) / long for t, n in zip(tail, nose))
    up = (0.0, 0.0, 1.0)
    left = (up[1] * along[2] - up[2] * along[1],
            up[2] * along[0] - up[0] * along[2],
            up[0] * along[1] - up[1] * along[0])
    size = math.sqrt(sum(x * x for x in left))
    left = tuple(x / size for x in left)
    up = (along[1] * left[2] - along[2] * left[1],
          along[2] * left[0] - along[0] * left[2],
          along[0] * left[1] - along[1] * left[0])
    rows = tuple((along[i], left[i], up[i]) for i in range(3))
    middle = tuple(0.5 * (t + n) for t, n in zip(tail, nose))
    index = world.spawned(bar, State(middle, turnOf(rows)), BODY_LAW,
                          'coupler', frozenset(range(len(states))))
    world.connected(Tie(index, (0.5 * long, 0.0, 0.0), ahead.frame,
                        (TAIL, 0.0, HITCH_UP)))
    world.connected(Tie(index, (-0.5 * long, 0.0, 0.0), frame,
                        (NOSE, 0.0, HITCH_UP)))
    return index
