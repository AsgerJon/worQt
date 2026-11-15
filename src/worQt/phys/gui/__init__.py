"""
The 'worQt.phys.gui' package looks at the lab's physics: 'PhysView'
paints an assembly in 3D, 'PhysWindow' runs the tower on the hexapod
live, 'PhysApp' opens it; 'BallsWindow' runs balls with a prism
launched across them, a click pushing what it lands on, 'BallsApp'
opens it; 'RingWindow' runs the giant hjulleje's outer ring with balls
in its groove, 'RingApp' opens it; 'WalkWindow' walks a person round
a yard seen through their eyes, a grabber in their hands ('WalkView'),
'WalkApp' opens it; 'CarWindow' drives the car from behind it
('CarView'), 'CarApp' opens it; 'Recorder' writes what a view paints
into a video and a log of what each frame was painted from.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._balls import BallsApp, BallsWindow
from ._car import CarApp, CarView, CarWindow
from ._ring import RingApp, RingWindow
from ._recorder import Recorder
from ._view import PhysView
from ._walk import WalkApp, WalkView, WalkWindow
from ._window import PhysWindow, PhysApp

__all__ = (
  'PhysView',
  'PhysWindow',
  'PhysApp',
  'BallsWindow',
  'BallsApp',
  'RingWindow',
  'RingApp',
  'WalkView',
  'WalkWindow',
  'WalkApp',
  'CarView',
  'CarWindow',
  'CarApp',
  'Recorder',
)
