"""
RunView covers what 'PhysView' paints where: at every pixel the body a
ray from the eye meets first, as 'hitOf' finds it, away from edges. A
ball sunk halfway into a slab shows above the slab's top and is hidden
below it (the slab's top plane runs through the ball); a ball behind a
wall shows only past the wall's end; a ball before a wall shows whole.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import math

from PySide6.QtGui import QColor

from worQt.phys import Assembly, Body, Sphere, State, boxShape, hitOf
from worQt.phys import plus, scaled
from worQt.phys.gui import PhysView
from worQt.qtest import WidgetTest

SLAB = Body.of(boxShape(1.0, 1.0, 0.2), 1000.0)
WALL = Body.of(boxShape(0.6, 0.05, 0.5), 1000.0)
BALL = Body.of(Sphere(0.1), 1000.0)
TONES = {0: QColor(200, 60, 60), 1: QColor(60, 190, 60),
         2: QColor(70, 90, 230), 3: QColor(220, 200, 40)}


class RunView(WidgetTest):
  """Tests for what 'PhysView' paints where."""

  def seenAs(self, view: PhysView, assembly: Assembly,
             states: tuple) -> float:
    """Returns the share of pixels, on a grid away from any edge, where
    the body painted (by its tone's hue) is the one a ray from the eye
    meets first."""
    image = view.grab().toImage()
    eye, right, up, forward = view.camera()
    width, height = view.width(), view.height()
    focal = 0.9 * min(width, height)
    agreed = counted = 0
    for y in range(6, height - 6, 8):
      for x in range(6, width - 6, 8):
        hits = set()
        for dx, dy in ((0, 0), (-4, 0), (4, 0), (0, -4), (0, 4)):
          way = plus(forward, plus(
            scaled(right, (x + dx - 0.5 * width) / focal),
            scaled(up, (0.5 * height - y - dy) / focal)))
          hit = hitOf(assembly, states, eye, way, ())
          hits.add(None if hit is None else hit[0])
        if len(hits) != 1:
          continue
        wanted = hits.pop()
        if wanted is None:
          continue
        color = image.pixelColor(x, y)
        tone = TONES[wanted]
        counted += 1
        if abs(color.hueF() - tone.hueF()) < 0.04 \
            and color.saturationF() > 0.3:
          agreed += 1
    self.assertGreater(counted, 200)
    return agreed / counted

  def showOf(self, assembly: Assembly, states: tuple) -> PhysView:
    """Returns a view of 'assembly' in 'states', each body in its tone,
    the camera low and to the side, shown live."""
    view = PhysView()
    view.resize(800, 600)
    view.tones = dict(TONES)
    view.dither = False
    view.target, view.distance = (0.0, 0.0, 0.1), 1.2
    view.yaw, view.pitch = 1.2, 0.25
    view.show_(assembly, states, math.inf)
    self.showLive(view)
    return view

  def run_ball_sunk_in_slab(self) -> None:
    """A ball whose middle is 4 cm over the slab's top, of 10 cm: the
    slab hides its bottom, it hides the slab behind its top."""
    assembly = Assembly((SLAB, BALL))
    states = (State((0.0, 0.0, -0.1)), State((0.0, 0.0, 0.04)))
    view = self.showOf(assembly, states)
    self.assertGreater(self.seenAs(view, assembly, states), 0.98)

  def run_ball_behind_and_before_wall(self) -> None:
    """On the slab a wall, a ball behind it, poking out past its end,
    and a ball before it: each shows where it is met first."""
    assembly = Assembly((SLAB, WALL, BALL, BALL))
    eye = PhysView()
    eye.target, eye.distance, eye.yaw, eye.pitch = (0.0, 0.0, 0.1), 1.2, \
      1.2, 0.25
    way = eye.camera()[3]
    behind = (-0.33 + 0.2 * way[0], 0.2 * way[1], 0.1)
    before = (-0.25 * way[0] + 0.2, -0.25 * way[1] - 0.1, 0.1)
    states = (State((0.0, 0.0, -0.1)), State((0.0, 0.0, 0.25)),
              State(behind), State(before))
    view = self.showOf(assembly, states)
    self.assertGreater(self.seenAs(view, assembly, states), 0.98)
