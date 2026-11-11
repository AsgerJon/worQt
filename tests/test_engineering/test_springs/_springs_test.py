"""
SpringsTest and SpringsWidgetTest are the base classes for the tests of
'worQt.engineering.springs': 'SpringsTest' subclasses 'BaseTest' for the
model, which needs no Qt; 'SpringsWidgetTest' subclasses 'WidgetTest'
for the widgets.

'hanging' is a mass of 2 kg hanging from an anchor 3 m up on a spring of
50 N/m and a metre at rest: by hand it rests 1 + m g / k = 1.3924 m
below the anchor, bobs at sqrt(k / m) = 5 rad/s and swings, a pendulum
as long, at sqrt(g / L) = 2.654 rad/s. 'chain' is three masses of 1 kg
on four springs of 100 N/m between two anchors 4 m apart along x,
stretched from 0.8 m to 1 m each, without gravity: it stretches along
the line at sqrt(2 - sqrt 2), sqrt 2 and sqrt(2 + sqrt 2) times
sqrt(k / m), and swings across it, either way, the same, of the
tension over the length, T / L = 20 N/m, for k.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from worktoy.work_test import BaseTest

from worQt.engineering.springs import Point, Spring, System
from worQt.qtest import WidgetTest


def hanging() -> System:
  """The 'hanging' function returns a mass hanging from an anchor on a
  spring, at the spring's rest length below it."""
  points = (Point((0.0, 0.0, 3.0), 1.0, ''),
            Point((0.0, 0.0, 2.0), 2.0, 'xyz'))
  return System(points, (Spring(0, 1, 50.0, 1.0),), ())


def chain() -> System:
  """The 'chain' function returns three masses on four springs between
  two anchors, stretched, without gravity."""
  points = [Point((0.0, 0.0, 0.0), 1.0, '')]
  points += [Point((float(x), 0.0, 0.0), 1.0, 'xyz') for x in (1, 2, 3)]
  points += [Point((4.0, 0.0, 0.0), 1.0, '')]
  springs = (*[Spring(i, i + 1, 100.0, 0.8) for i in range(4)],)
  return System((*points,), springs, (), 0.0)


class SpringsTest(BaseTest):
  """Base class for the tests of the springs' model."""


class SpringsWidgetTest(WidgetTest):
  """Base class for the tests of the springs' widgets."""
