"""
BeamExperiment is a test of a reinforced concrete beam on a rig, its
control loop moving one actuator and the others following its force,
reckoned by OpenSees on the beam as a solid.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from worktoy.desc import AttriBox, Field
from worktoy.dispatch import overload
from worktoy.mcls import BaseObject
from worktoy.waitaminute import MissingVariable

from worksees import Model, Session, Worker

from ._beam_mesh import BeamMesh, QUERIES
from ._rc_beam import RCBeam
from ._reading import LabEvent, Reading
from ._rig import Rig
from ._rig_parts import Control

if TYPE_CHECKING:  # pragma: no cover, no mutate
  from worksees import Result

_FALLEN = 0.8  # of its peak, the force the test ends at, past the peak
_HELD_CYCLES = 10  # cycles the reading must keep to the command's limit
_HELD_WITHIN = 0.005  # of the limit, how near it is kept
_HELD_LEAST = 0.01  # mm, how near it is kept, a limit of nought too
_DIAGONAL = math.radians(25)  # a crack this far from upright is a shear
_SEED = 1


class BeamExperiment(BaseObject):
  """
  BeamExperiment is a test of an 'RCBeam' on a 'Rig', reckoned by
  OpenSees in a 'Session' on its 'mesh', the beam as a solid of bricks
  with its bars and stirrups through it, the way a lab runs one. Each
  cycle of the rig, the control reads its transducer, compares the
  reading, its feedback, with its command, a ramp to a limit, and turns
  the error by its PID gains into how fast the actuator it drives
  moves, at most its speed; the actuator moves that far, and OpenSees
  finds the force it must push with to get there. Every other actuator
  pushes its share of that force, found with it, so a chain of
  actuators pushes as one. The beam bends and shears as a solid does:
  where it has no stirrups, a diagonal crack can open and break it
  before its bars yield. Its own weight is left out; nothing is tuned.

  Every reading is up positive, as the transducers under the beam read
  their plungers: the beam bending down reads less than nought, and so
  do the actuators pushing it, their displacements and their forces on
  it; a command ramping down has a rate below nought.

  'retune' changes the control loop's ramp, step, gains and top speed
  as the test runs, the command going on from where it is, a new limit
  beginning a new ramp there. 'stepLength' is how far the command moves
  a step now, in mm, and 'cycle' how many seconds that takes.

  'advance' runs on and returns the 'Reading's of the cycles run;
  'begin' starts a cycle and returns at once, 'ready' tells when it is
  done and 'collect' reads it, so a window answers while OpenSees
  reckons. 'readings' holds them all, 'latest' the last and 'peak' the
  one of the greatest total force either way. 'events' are what
  happened to the beam, once each, in order: 'first crack', 'bars
  yield', 'stirrups yield', 'concrete crushes' and 'bars snap'. The
  test is 'finished' when a bar snaps; when the force falls to 80 % of
  its peak, once the bars have yielded, the concrete crushed or a
  diagonal crack opened (before that, it dips as the beam cracks and
  climbs again as the bars take over); when the control has held its
  command at its limit for 10 cycles; when the actuator driven reaches
  the end of its stroke; or when the beam cannot be pushed further, as
  a brittle failure leaves it. 'ending' says which: whether it failed
  in shear, crushed, or broke at its first crack, its bars too few,
  told from the last reading where no further step could be found.
  'nodes' are where the mesh's lines are along the beam, 'rows' up it.
  'close' ends the session, unless it shares the 'Worker' it was
  given.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Private Variables
  __test_mesh__: BeamMesh | None = None
  __test_rig__: Rig | None = None
  __test_worker__: Worker | None = None
  __test_seed__: int = _SEED
  __test_session__: Session | None = None
  __test_pending__: tuple | None = None
  __test_readings__: list[Reading] | None = None
  __test_events__: list[LabEvent] | None = None
  __test_peak__: Reading | None = None
  __test_ending__: str = ''
  __control_integral__: float = 0.0
  __control_command__: float = 0.0
  __control_start__: float = 0.0
  __control_time__: float = 0.0
  __control_cycle__: float = 1.0
  __control_held__: int = 0

  #  Public Variables
  finished = AttriBox[bool](False)

  #  Virtual Variables
  beam: Field[RCBeam] = Field()
  rig: Field[Rig] = Field()
  mesh: Field[BeamMesh] = Field()
  seed: Field[int] = Field()
  nodes: Field[tuple[float, ...]] = Field()
  rows: Field[tuple[float, ...]] = Field()
  readings: Field[tuple[Reading, ...]] = Field()
  latest: Field[Reading] = Field()
  peak: Field[Reading] = Field()
  events: Field[tuple[LabEvent, ...]] = Field()
  ending: Field[str] = Field()
  command: Field[float] = Field()
  stepLength: Field[float] = Field()
  cycle: Field[float] = Field()
  pending: Field[bool] = Field()
  crackStrain: Field[float] = Field()
  yieldStrain: Field[float] = Field()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  GETTERS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @mesh.GET
  def _getMesh(self, ) -> BeamMesh:
    """The 'mesh' getter returns the beam on its rig as a solid."""
    if self.__test_mesh__ is None:
      raise MissingVariable(self, '__test_mesh__', BeamMesh)
    return self.__test_mesh__

  @beam.GET
  def _getBeam(self, ) -> RCBeam:
    """The 'beam' getter returns the beam tested."""
    return self.mesh.beam

  @rig.GET
  def _getRig(self, ) -> Rig:
    """The 'rig' getter returns the rig the beam is tested on, its
    control as it is now."""
    if self.__test_rig__ is None:
      raise MissingVariable(self, '__test_rig__', Rig)
    return self.__test_rig__

  @seed.GET
  def _getSeed(self, ) -> int:
    """The 'seed' getter returns what the concrete's scatter is drawn
    from."""
    return self.__test_seed__

  @nodes.GET
  def _getNodes(self, ) -> tuple[float, ...]:
    """The 'nodes' getter returns where the mesh's lines are along the
    beam."""
    return self.mesh.xs

  @rows.GET
  def _getRows(self, ) -> tuple[float, ...]:
    """The 'rows' getter returns where the mesh's lines are up the
    beam."""
    return self.mesh.ys

  @readings.GET
  def _getReadings(self, ) -> tuple[Reading, ...]:
    """The 'readings' getter returns what was read at each cycle."""
    return (*self.__test_readings__,)

  @latest.GET
  def _getLatest(self, ) -> Reading:
    """The 'latest' getter returns the last reading, or the beam at
    rest before the first."""
    if self.__test_readings__:
      return self.__test_readings__[-1]
    return self._atRest()

  @peak.GET
  def _getPeak(self, ) -> Reading:
    """The 'peak' getter returns the reading of the greatest total
    force, the first if more than one."""
    if self.__test_peak__ is None:
      return self._atRest()
    return self.__test_peak__

  @events.GET
  def _getEvents(self, ) -> tuple[LabEvent, ...]:
    """The 'events' getter returns what happened to the beam, in
    order."""
    return (*self.__test_events__,)

  @ending.GET
  def _getEnding(self, ) -> str:
    """The 'ending' getter says why the test ended, if it has."""
    return self.__test_ending__

  @command.GET
  def _getCommand(self, ) -> float:
    """The 'command' getter returns the control's command now, in
    mm."""
    return self.__control_command__

  @stepLength.GET
  def _getStepLength(self, ) -> float:
    """The 'stepLength' getter returns how far the command moves a
    step, in mm: the control's share of its ramp, from where the ramp
    began to its limit."""
    control = self.rig.control
    return control.step * abs(control.limit - self.__control_start__)

  @cycle.GET
  def _getCycle(self, ) -> float:
    """The 'cycle' getter returns the seconds between two looks of the
    control: a step at the ramp's rate, or the last cycle's while the
    command holds where its ramp began."""
    length = self.stepLength
    if length > 0:
      return length / abs(self.rig.control.rate)
    return self.__control_cycle__

  @pending.GET
  def _getPending(self, ) -> bool:
    """The 'pending' getter tells whether a cycle has begun and not yet
    been collected."""
    return False if self.__test_pending__ is None else True

  @crackStrain.GET
  def _getCrackStrain(self, ) -> float:
    """The 'crackStrain' getter returns the strain the concrete cracks
    at, fctm / Ecm."""
    return self.beam.fctm / self.beam.Ecm

  @yieldStrain.GET
  def _getYieldStrain(self, ) -> float:
    """The 'yieldStrain' getter returns the strain the bars yield at."""
    return self.beam.fy / self.beam.Es

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS   # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload(RCBeam, Rig, int, Worker)
  def __init__(self, beam: RCBeam, rig: Rig, seed: int,
               worker: Worker) -> None:
    self.__test_worker__ = worker
    self.__init__(beam, rig, seed)

  @overload(RCBeam, Rig, int)
  def __init__(self, beam: RCBeam, rig: Rig, seed: int) -> None:
    rig.check(beam)
    self.__test_seed__ = seed
    self.__test_mesh__ = BeamMesh(beam, rig, seed)
    self.__test_rig__ = rig
    self.__test_readings__ = []
    self.__test_events__ = []

  @overload(RCBeam, Rig)
  def __init__(self, beam: RCBeam, rig: Rig) -> None:
    self.__init__(beam, rig, _SEED)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  PUBLIC METHODS   # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def advance(self, cycles: int) -> tuple[Reading, ...]:
    """The 'advance' method runs the test on 'cycles' cycles, fewer if
    it ends, and returns the readings of the cycles run."""
    made = []
    for _ in range(cycles):
      if self.finished:
        break
      self.begin()
      reading = self.collect()
      if reading is not None:
        made.append(reading)
    return (*made,)

  def begin(self, ) -> None:
    """The 'begin' method starts the next cycle, if none is under way
    and the test is not finished, and returns at once."""
    if self.finished or self.__test_pending__ is not None:
      return
    session = self._session()
    self.__test_pending__ = session.submit(self._move(), 1, *QUERIES)

  def ready(self, ) -> bool:
    """The 'ready' method tells whether the cycle begun is done."""
    pending = self.__test_pending__
    if pending is None:
      return False
    return self._session().ready(pending)

  def collect(self, ) -> Reading | None:
    """The 'collect' method reads the cycle begun, waiting for it if it
    is not done, and returns its reading; or 'None', the test ended, if
    the beam could not be pushed further, or if none was begun."""
    pending = self.__test_pending__
    if pending is None:
      return None
    self.__test_pending__ = None
    results = self._session().collect(pending)
    if not results:
      self._end(self._stuck())
      return None
    reading = self._read(results[0])
    self.__test_readings__.append(reading)
    if abs(reading.force) > abs(self.peak.force):
      self.__test_peak__ = reading
    self._notice(reading)
    return reading

  def run(self, ) -> None:
    """The 'run' method runs the test until it ends."""
    while not self.finished:
      self.advance(50)

  def happened(self, name: str) -> LabEvent | None:
    """The 'happened' method returns the event named 'name', or 'None'
    if it has not happened."""
    for event in self.__test_events__:
      if event.name == name:
        return event
    return None

  def retune(self, control: Control) -> None:
    """The 'retune' method has the control loop run on as 'control'
    from the next cycle, as a servo controller is retuned during a
    test: its ramp's rate and limit, its step, its gains and its top
    speed; the command goes on from where it is, so nothing jumps, and
    a ramp turned back unloads the beam. It reads the same transducer
    and drives the same actuator, the beam being built so, and its ramp
    must reach its limit from the command now; else it raises
    'ValueError'."""
    old = self.rig.control
    if (control.transducer, control.actuator) != (old.transducer,
                                                  old.actuator):
      raise ValueError('a test reads the transducer and drives the '
                       'actuator it began with')
    command = self.__control_command__
    if control.rate * (control.limit - command) < 0:
      infoSpec = """a ramp at %g mm/s from %g mm never reaches %g mm"""
      raise ValueError(infoSpec % (control.rate, command, control.limit))
    self.__control_cycle__ = self.cycle
    if control.limit != old.limit:
      self.__control_start__ = command
    self.__test_rig__ = self.rig.withControl(control)

  def close(self, ) -> None:
    """The 'close' method ends the test's session."""
    if self.__test_session__ is not None:
      if self.__test_pending__ is not None:
        self.__test_session__.collect(self.__test_pending__)
        self.__test_pending__ = None
      self.__test_session__.close()
    self.__test_session__ = None

  def model(self, ) -> Model:
    """The 'model' method returns the beam on its rig as OpenSees is
    given it: its mesh's model."""
    return self.mesh.model()

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _session(self, ) -> Session:
    """The session the beam is pushed in, opened on first use, pushing
    the node of the actuator driven."""
    if self.__test_session__ is None:
      mesh = self.mesh
      model = mesh.model()
      if self.__test_worker__ is None:
        session = Session(model, mesh.driven, 2)
      else:
        session = Session(model, mesh.driven, 2, self.__test_worker__)
      self.__test_session__ = session
    return self.__test_session__

  def _move(self, ) -> float:
    """How far the actuator driven moves this cycle, up positive as its
    feedback is: the control's PID on the error between its command and
    its feedback, as fast as the servo valve lets it, its integral kept
    from winding up while the valve is open full."""
    control, cycle = self.rig.control, self.cycle
    latest = self.latest
    error = latest.command - latest.feedback
    if len(self.__test_readings__) > 1:
      before = self.__test_readings__[-2].feedback
    else:
      before = 0.0
    slope = (latest.feedback - before) / cycle
    integral = self.__control_integral__ + error * cycle
    speed = control.kp * error + control.ki * integral
    speed -= control.kd * slope
    if abs(speed) > control.speed:
      speed = math.copysign(control.speed, speed)
    else:
      self.__control_integral__ = integral
    return speed * cycle

  def _read(self, result: Result) -> Reading:
    """What the instruments read at a cycle, up positive: the forces on
    the beam from the load factor, in kN, less than nought pushing
    down."""
    rig, mesh = self.rig, self.mesh
    read = mesh.read(result)
    forces = (*[-result.loadFactor * share / 1000.0
                for share in rig.shares],)
    transducers = (*[mesh.liftAt(x, read['lifts'])
                     for x in rig.transducers],)
    step = len(self.__test_readings__) + 1
    self.__control_time__ += self.cycle
    return Reading(step, self.__control_time__, self._nextCommand(),
                   transducers[rig.control.transducer], read['stroke'],
                   forces, sum(forces), transducers, read['deflections'],
                   read['cells'], read['bottomBars'], read['topBars'],
                   read['stirrups'])

  def _nextCommand(self, ) -> float:
    """The command a step on: a step along its ramp, held at its limit
    once there."""
    control = self.rig.control
    command = self.__control_command__
    command += math.copysign(self.stepLength, control.rate)
    if (command - control.limit) * control.rate > 0:
      command = control.limit
    self.__control_command__ = command
    return command

  def _atRest(self, ) -> Reading:
    """The beam before the first cycle."""
    rig, mesh = self.rig, self.mesh
    cells = (len(mesh.xs) - 1) * (len(mesh.ys) - 1)
    stretches = len(mesh.xs) - 1
    return Reading(0, 0.0, 0.0, 0.0, 0.0, (0.0,) * len(rig.actuators),
                   0.0, (0.0,) * len(rig.transducers),
                   (0.0,) * len(mesh.xs), ((0.0, 0.0, 0.0),) * cells,
                   (0.0,) * stretches, (0.0,) * stretches,
                   (0.0,) * len(mesh.stirrupPlaces))

  def widest(self, reading: Reading) -> tuple[int, float, float, float]:
    """The 'widest' method returns the cell most pulled in 'reading':
    its index, where it is along and up the beam, in mm, and how far
    its crack leans from upright, in radians."""
    mesh = self.mesh
    nx = len(mesh.xs) - 1
    _, index = max((cell[0], index)
                   for index, cell in enumerate(reading.cells))
    i, j = index % nx, index // nx
    x = (mesh.xs[i] + mesh.xs[i + 1]) / 2
    y = (mesh.ys[j] + mesh.ys[j + 1]) / 2
    return index, x, y, abs(reading.cells[index][1])

  def _notice(self, reading: Reading) -> None:
    """Notes what has happened to the beam by 'reading', and ends the
    test if it is over."""
    beam, mesh = self.beam, self.mesh
    nx = len(mesh.xs) - 1
    for index, (most, _, least) in enumerate(reading.cells):
      i, j = index % nx, index // nx
      where = (mesh.xs[i] + mesh.xs[i + 1]) / 2
      if most > mesh.cellStrength(i, j) / beam.Ecm:
        self._happen('first crack', reading, where)
      if least <= -beam.epsCu1:
        self._happen('concrete crushes', reading, where)
    for bars in (reading.bottomBars, reading.topBars):
      for i, strain in enumerate(bars):
        where = (mesh.xs[i] + mesh.xs[i + 1]) / 2
        if strain >= self.yieldStrain:
          self._happen('bars yield', reading, where)
        if strain >= beam.epsUk:
          self._happen('bars snap', reading, where)
    for where, strain in zip(mesh.stirrupPlaces, reading.stirrups):
      if strain >= self.yieldStrain:
        self._happen('stirrups yield', reading, where)
    self._judge(reading)

  def _happen(self, name: str, reading: Reading, where: float) -> None:
    """Notes the event 'name' at 'reading', unless it has happened; a
    crack lets go as it opens, so its force is the greater of the
    cycle's and the cycle's before."""
    if self.happened(name) is not None:
      return
    force = reading.force
    if name == 'first crack' and reading.step > 1:
      before = self.__test_readings__[reading.step - 2].force
      force = before if abs(before) > abs(force) else force
    self.__test_events__.append(LabEvent(name, reading.step,
                                         reading.stroke, force, where))

  def _judge(self, reading: Reading) -> None:
    """Ends the test if it is over. A fall of the force ends it only
    once the bars have yielded, the concrete crushed or the widest
    crack is diagonal, a shear failure: before that, the force dips as
    the beam cracks, and climbs again as the bars take what the
    concrete let go."""
    if self.happened('bars snap') is not None:
      return self._end('a bar snapped')
    peak = self.peak
    fallen = abs(reading.force) < _FALLEN * abs(peak.force)
    yielded = self.happened('bars yield')
    crushed = self.happened('concrete crushes')
    if fallen and self._shear(reading):
      return self._end(self._shear(reading))
    bare = not (self.beam.bottom.count or self.beam.top.count)
    if bare and fallen:
      return self._end('it broke at its first crack: it has no bars')
    if fallen and yielded is not None and peak.step < yielded.step:
      return self._end('it broke at its first crack: too few bars')
    if fallen and crushed is not None:
      if yielded is None or yielded.step > crushed.step:
        return self._end('the concrete crushed before the bars yielded')
      return self._end('the concrete crushed')
    if fallen and yielded is not None:
      return self._end('the force fell to 80 % of its peak')
    if abs(reading.stroke) >= self.rig.stroke:
      return self._end('the actuator reached the end of its stroke')
    self._judgeHeld(reading)

  def _stuck(self, ) -> str:
    """Why the beam could not be pushed further, as far as its last
    reading tells: a diagonal crack opened, its concrete crushed, or its
    bars yielded; a beam failing so suddenly that no step of it can be
    found."""
    words = 'the beam could not be pushed further'
    if not self.__test_readings__:
      return words
    shear = self._shear(self.latest)
    if shear:
      return shear
    if self.happened('concrete crushes') is not None:
      return 'the concrete crushed: %s' % words
    if self.happened('bars yield') is not None:
      return 'its bars yielded: %s' % words
    return words

  def _shear(self, reading: Reading) -> str:
    """Whether the beam fails in shear at 'reading', and how: its
    widest crack diagonal, leaning 25° or more, where it has no
    stirrups, or where its stirrups yield; nothing if it is not."""
    _, where, _, lean = self.widest(reading)
    if lean < _DIAGONAL:
      return ''
    stirrups = self.beam.stirrups
    near = [x for x in stirrups.places(self.beam.length)
            if abs(x - where) <= stirrups.spacing]
    held = 'its stirrups holding it'
    if not near:
      held = 'no stirrups there'
    elif self.happened('stirrups yield') is not None:
      held = 'its stirrups yielding'
    return ('it failed in shear: a diagonal crack opened at %.0f mm, '
            '%s' % (where, held))

  def _judgeHeld(self, reading: Reading) -> None:
    """Ends the test once the control has held its command at its limit
    for 10 cycles."""
    limit = self.rig.control.limit
    within = max(_HELD_WITHIN * abs(limit), _HELD_LEAST)
    near = abs(reading.feedback - limit) <= within
    if reading.command == limit and near:
      self.__control_held__ += 1
    else:
      self.__control_held__ = 0
    if self.__control_held__ >= _HELD_CYCLES:
      self._end('the control held its command at its limit')

  def _end(self, ending: str) -> None:
    """Ends the test, saying why."""
    self.__test_ending__ = ending
    self.finished = True
