"""
TestRobot covers the robot driver ('RobotDriver') and its recorder
('VibrationRecorder'): the oval's line ('ovalAt') is where the oval's
own placer ('ovalPlaceOf') finds it, going the way it says; the robot,
from the start line, drives the car up to its speed down the front
straight and into the first turn, never far off its line; the recorder
reads the car standing on the bank as an accelerometer would (gravity,
tipped as the bank and the body's roll down it, nothing turning), and
writes a CSV of its channels with their units and meanings beside
it. The racing robot ('RacingRobot') plans each turn at the speed its
banking and curve allow with the grip it dares (by hand), flat out on
the straights, braking down in time; its line runs 2 m above the
inside edge; the learning racer ('LearningRacer') learns, part by
part, each scored with its neighbours, toward the trials that scored
better (time, the apron punished), never from a crawl, and from where
it was stranded; stuck on the throttle a robot backs out, and making no
way it is stranded; and from a standing start
it races a lap (at 'LIVE' fidelity, a window's) in under 46 s, never
sliding past 10 degrees, hardly on the apron.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import json
import math
import os
import tempfile

import numpy

from worQt.phys._laps import LapTimer
from worQt.phys._robot import APRON_COST, BACKING, CHANNELS
from worQt.phys._robot import LEARN_FROM, LEARN_REACH, RACE_BRAKING
from worQt.phys._robot import RACE_GRIP, RACE_MARGIN, RESCUE
from worQt.phys._robot import RESCUE_GAIN, STUCK, LearningRacer
from worQt.phys._robot import RacingRobot, RobotDriver
from worQt.phys._robot import VibrationRecorder, channelsOf, robotLaps
from worQt.phys._terrain import OVAL_BANKS, OVAL_LENGTH, OVAL_RADIUS
from worQt.phys._terrain import OVAL_STRAIGHT, OVAL_WIDTHS, ovalAt
from worQt.phys._terrain import ovalPlaceOf
from worQt.phys import FULL, LIVE, carBuilt, carPlaced, conjugate
from worQt.phys import ovalWorld, rotated

from . import PhysTest


class TestRobot(PhysTest):
  """Tests for the robot driver and its recorder."""

  #  The springs' world's car, stepped in its world's one thread: minutes
  #  a class (killed at the harness's 30 s, the user's run of 2026-11-14).
  __time_out__ = 3600.0

  def test_line(self) -> None:
    """Points round the oval, on and off its middle line, are found
    again where they were put (to a micrometre), the line going the way
    'ovalAt' says; the start line is at the origin, driven along +x."""
    for step in range(200):
      along = step * OVAL_LENGTH / 200.0 + 0.37
      for out in (-6.0, 0.0, 7.5):
        x, y, heading = ovalAt(along, out)
        found = ovalPlaceOf(x, y)
        self.assertNear(found[0], out, 1e-6)
        if out == 0.0:
          self.assertNear(found[1], along, 1e-6)
        ahead = ovalAt(along + 1e-4, out)
        way = math.atan2(ahead[1] - y, ahead[0] - x)
        self.assertLess(abs((way - heading + math.pi) % (2.0 * math.pi)
                            - math.pi), 1e-5)
    self.assertNear(ovalAt(0.5 * OVAL_STRAIGHT, 0.0), (0.0, 0.0, 0.0),
                    1e-12)

  def test_standing(self) -> None:
    """The car let stand two seconds on the start line (the bank 9
    degrees), read for a third of a second: the accelerometer reads
    gravity, 9.81 m/s² (within 0.05), tipped as the bank and the body's
    roll down it on its springs (9 to 10.5 degrees; 9.85 when measured),
    the gyro all but nothing (under 0.005 rad/s; let stand only half a
    second, the body still rocked at 0.036)."""
    car, world = carBuilt(0.5, FULL), ovalWorld(FULL)
    terrain = world.ground.terrain
    states = carPlaced(car.states, (0.0, 0.0, terrain.heightAt(0.0, 0.0)),
                       terrain.normalAt(0.0, 0.0))
    robot = RobotDriver(car, 0.0, 0.0)
    recorder = VibrationRecorder(car, robot)
    states = world.advancedAll(car.assembly, states, 2.0)
    for count in range(36):
      states = world.advancedAll(car.assembly, states, 0.01,
                                 2.0 + 0.01 * count)
      recorder.sample(states, 0.01 * count)
    names = [name for name, _, _ in channelsOf()]
    rows = numpy.array(recorder.rows)
    self.assertEqual(rows.shape, (35, len(names)))
    force = rows[:, names.index('ax'):names.index('az') + 1].mean(0)
    self.assertNear(float(numpy.linalg.norm(force)), 9.81, 0.05)
    tipped = math.degrees(math.atan2(math.hypot(force[0], force[1]),
                                     force[2]))
    self.assertGreater(tipped, 9.0)
    self.assertLess(tipped, 10.5)
    for name in ('wx', 'wy', 'wz'):
      self.assertLess(float(abs(rows[:, names.index(name)]).max()), 0.005)

  def test_drives(self) -> None:
    """From the start line at 30 m/s, 100 samples a second, the robot
    has the car at its speed (within 1.5 m/s) 15 s later, into the
    first turn, never more than 1.5 m off its line; its recording,
    saved, reads back as written with every channel's unit and
    meaning."""
    recorder, laps, states = robotLaps(0.25, 30.0, 0.0, 100.0, FULL)
    names = [name for name, _, _ in channelsOf()]
    rows = numpy.array(recorder.rows)
    self.assertEqual(laps, ())
    self.assertGreater(rows[-1, names.index('along')],
                       0.25 * OVAL_LENGTH - 1.0)
    self.assertLess(float(abs(rows[:, names.index('off')]).max()), 1.5)
    self.assertNear(float(rows[-1, names.index('speed')]), 30.0, 1.5)
    with tempfile.TemporaryDirectory() as folder:
      path, side = recorder.saved(os.path.join(folder, 'run.csv'),
                                  {'speed': 30.0})
      read = numpy.loadtxt(path, delimiter=',', skiprows=1)
      with open(path) as file:
        header = file.readline().strip().split(',')
      with open(side) as file:
        about = json.load(file)
    self.assertEqual(header, names)
    self.assertNear(tuple(read[-1]), tuple(rows[-1]),
                    1e-6 * float(abs(rows).max()))
    self.assertEqual(about['samples'], len(rows))
    self.assertEqual(about['speed'], 30.0)
    self.assertEqual([c['name'] for c in about['channels']], names)
    self.assertEqual(len(CHANNELS) + 4 * 5, len(names))

  def test_race_plan(self) -> None:
    """The racing robot's line runs 'RACE_MARGIN' over the inside edge;
    in the middle of a turn it plans the speed the banking and the curve
    allow with 'RACE_GRIP' (by hand, within 1 %), on a straight none
    short of without end; just before a turn, no more than it can brake
    down from in time."""
    robot = RacingRobot(None)
    middle = OVAL_STRAIGHT + 0.5 * math.pi * OVAL_RADIUS
    for along, width in ((0.5 * OVAL_STRAIGHT, OVAL_WIDTHS[0]),
                         (middle, OVAL_WIDTHS[1])):
      self.assertNear(robot.lineAt(along), RACE_MARGIN - 0.5 * width,
                      1e-9)
    bank = OVAL_BANKS[1]
    radius = OVAL_RADIUS + robot.lineAt(middle)
    wanted = math.sqrt(9.81 * radius * (math.sin(bank) + RACE_GRIP
                                        * math.cos(bank))
                       / (math.cos(bank) - RACE_GRIP * math.sin(bank)))
    self.assertNear(robot.capAt(middle) / wanted, 1.0, 0.01)
    self.assertEqual(robot.capAt(0.5 * OVAL_STRAIGHT), math.inf)
    before = OVAL_STRAIGHT - 100.0
    self.assertLess(robot.wantedAt(before, 0.0), math.sqrt(
      robot.capAt(OVAL_STRAIGHT + 50.0) ** 2 + 2.0 * RACE_BRAKING * 160.0))

  def test_learner(self) -> None:
    """The learning racer ('LearningRacer') scores a part only once it
    has passed the 'LEARN_REACH' parts either side of it too, one after
    the other, the first come into at 'LEARN_FROM' m/s or more, a lap on
    from where it started: their scores together, first as its
    baseline; a trial that scores better moves its pace (its own and
    the one all parts share) and lane toward the trial, one that scores
    worse away from it; from a crawl, parts
    not one after the other, or in its first lap, it learns nothing; a
    pass with half a second on the apron scores 'APRON_COST' half
    seconds worse than the same pass clean; its brain carries over to a
    new one (one scored otherwise, its paces and lanes only; one of
    another form, nothing)."""
    window = range(5 - LEARN_REACH, 6 + LEARN_REACH)
    racer = LearningRacer(None, None, 7)
    racer.along = OVAL_LENGTH
    for part in window:
      racer.partDone(part, 1.2, 0.0, 0.0, LEARN_FROM + 1.0)
    together = -1.2 * len(window)
    self.assertNear(racer.means[5], together, 1e-12)
    self.assertEqual(sum(mean is not None for mean in racer.means), 1)
    for score, way in ((together + 0.2, 1.0), (together - 0.4, -1.0)):
      before = (racer.pace[5], racer.lane[5], racer.shared)
      racer.trials[5] = (0.02, 0.4)
      racer.learned(5, score)
      self.assertGreater(way * (racer.pace[5] - before[0]), 0.0)
      self.assertGreater(way * (racer.lane[5] - before[1]), 0.0)
      self.assertGreater(way * (racer.shared - before[2]), 0.0)
    for parts, speed, along in (
            (window, LEARN_FROM - 1.0, OVAL_LENGTH),
            ([part + (part > 5) for part in window], LEARN_FROM + 1.0,
             OVAL_LENGTH),
            (window, LEARN_FROM + 1.0, OVAL_LENGTH - 1.0)):
      idle = LearningRacer(None, None, 2)
      idle.along = along
      for part in parts:
        idle.partDone(part, 1.2, 0.0, 0.0, speed)
      self.assertEqual(idle.means, [None] * len(idle.means))
    clean = LearningRacer(None, None, 1)
    dirty = LearningRacer(None, None, 1)
    clean.partDone(2, 1.2, 0.0, 0.0, 40.0)
    dirty.partDone(2, 1.2, 0.0, 0.5, 40.0)
    self.assertNear(clean.score - dirty.score, 0.5 * APRON_COST, 1e-12)
    again = LearningRacer(None, racer.brain, 3)
    self.assertEqual((again.pace, again.lane, again.means, again.shared),
                     (racer.pace, racer.lane, racer.means, racer.shared))
    older = dict(racer.brain, reach=None)
    again = LearningRacer(None, older, 3)
    self.assertEqual((again.pace, again.lane, again.means),
                     (racer.pace, racer.lane, [None] * len(racer.means)))
    oldest = dict(racer.brain, form=None)
    fresh = LearningRacer(None, None, 3)
    again = LearningRacer(None, oldest, 3)
    self.assertEqual((again.pace, again.lane, again.means, again.learnt),
                     (fresh.pace, fresh.lane, fresh.means, 0))

  def test_gave_up(self) -> None:
    """Stranded in a part, the learning racer scores it as left then
    (the time it has spent there so far), learning from it for the part
    'LEARN_REACH' before."""
    racer = LearningRacer(None, None, 4)
    racer.along = OVAL_LENGTH
    for part in range(5 - 2 * LEARN_REACH, 5):
      racer.partDone(part, 1.2, 0.0, 0.0, LEARN_FROM + 1.0)
    racer._part, racer._entered, racer._clock = 5, 0.0, 25.0
    racer._worst, racer.apron, racer._speed = 0.0, 0.0, 30.0
    racer.gaveUp()
    self.assertNear(racer.means[5 - LEARN_REACH],
                    -1.2 * 2 * LEARN_REACH - 25.0, 1e-12)
    self.assertIsNone(racer._part)

  def test_unstuck(self) -> None:
    """On the throttle but standing still, a robot backs out once
    'STUCK' s have passed (to a step), full back for 'BACKING' s; making
    no 'RESCUE_GAIN' m of way for 'RESCUE' s it is stranded, and is not
    once it makes way again."""
    robot, step, waited = RobotDriver(None, 30.0, 0.0), 0.01, 0.0
    while robot.backing == 0.0:
      robot.throttle = 1.0
      robot._unstuck(0.0, step)
      waited += step
    self.assertNear(waited, STUCK, 1.5 * step)
    self.assertEqual(robot.backing, BACKING)
    robot.throttle = 1.0
    robot._unstuck(0.0, step)
    waited += step
    self.assertEqual(robot.throttle, -1.0)
    self.assertNear(robot.backing, BACKING - step, 1e-12)
    while waited < RESCUE + 1.0:
      self.assertEqual(robot.stranded, waited > RESCUE)
      robot._unstuck(0.0, step)
      waited += step
    self.assertTrue(robot.stranded)
    robot.along = RESCUE_GAIN + 1.0
    robot._unstuck(5.0, step)
    self.assertFalse(robot.stranded)

  def test_race_lap(self) -> None:
    """From the start line, at 'LIVE' fidelity, the racing robot races
    its first lap (standing) in under 46 s (41.97 when measured: the
    roadster's engine at twice its power, through its five-speed
    gearbox, on 3 Hz springs), never sliding past 10 degrees above 5 m/s
    (6.38) nor more than 12 m off its line (5.23; 10.4 before its
    steering was damped against its drift), a wheel on the apron under
    5 s of it (none; 3.2 undamped, 10 before its hands trimmed it up the
    banking)."""
    car, world = carBuilt(0.5, LIVE), ovalWorld(LIVE)
    terrain = world.ground.terrain
    states = carPlaced(car.states, (0.0, 0.0, terrain.heightAt(0.0, 0.0)),
                       terrain.normalAt(0.0, 0.0))
    robot, timer = RacingRobot(car), LapTimer(0.0)
    time, frame, apron = 0.0, 1.0 / 60.0, 0.0
    while not timer.laps and time < 46.0:
      robot.take(states, frame)
      states = world.advancedAll(car.assembly, states, frame, time)
      time += frame
      chassis = states[car.chassis]
      timer.seen(chassis.place[0], chassis.place[1], time)
      self.assertLess(abs(robot.off), 12.0)
      local = rotated(conjugate(chassis.turn), chassis.velocity)
      if local[0] > 5.0:
        self.assertLess(abs(math.degrees(math.atan2(local[1], local[0]))),
                        10.0)
      if robot.onApron(states):
        apron += frame
    self.assertEqual(len(timer.laps), 1)
    self.assertLess(timer.laps[0], 46.0)
    self.assertLess(apron, 5.0)
