"""
The 'worQt.gaming.billiards.gui' package shows a three-cushion table in
3D, drawn by Qt Quick 3D:

- roomLight, radianceBytes: the light of the room round the table, an
  HDR image the scene is lit by and the balls mirror, and its '.hdr'
  bytes.
- Prism: a piece of the table's triangles, or a ball's trail, for Qt
  Quick 3D.
- handPicture, cuePicture, HAND_LENGTH, HAND_WIDTH, STROKE_MOST: a
  gloved bridge hand and the cue in it, seen from above, two pictures
  laid behind ball 1 with the last shot's trails, the cue sliding back
  and forth through the bridge as it strikes, as 'cueBackAt' has it:
  drawn back, held, sent on to meet the ball, following through
  'FOLLOW_SHARE' of the backswing over 'FOLLOW_SECONDS'.
- TableView: the table and its balls, 'carom.qml' in a 'QQuickWidget';
  a drag turns round the table, the wheel comes nearer.
- HitPicker, PaintHitPicker: the cue ball's face, the point struck
  chosen on it.
- ShotPanel, PaintShotPanel: where a shot is set up and taken: the cue
  ball, the point struck, the power, 'Shoot'.
- UnfoldedMap, PaintUnfoldedMap: the table unfolded beside it, its
  mirrored copies and the arc of the English across them.
- BilliardsSounds: what a shot shown sounds like, played in a process
  of its own.
- BilliardsToolBar: the buttons above the table, the field of view,
  the aim step and the hand's box.
- BilliardsWindow: the window round it, the balls moving on the
  cloth.
- BilliardsApp: the application, run with 'python -m
  worQt.gaming.billiards'.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ._room_light import radianceBytes, roomLight
from ._prism import Prism
from ._hand_picture import HAND_LENGTH, HAND_WIDTH, STROKE_MOST
from ._hand_picture import FOLLOW_SECONDS, FOLLOW_SHARE
from ._hand_picture import cueBackAt, cuePicture, handPicture
from ._table_view import TableView
from ._billiards_tool_bar import BilliardsToolBar
from ._hit_picker import HitPicker, PaintHitPicker
from ._shot_panel import ShotPanel, PaintShotPanel
from ._unfolded_map import UnfoldedMap, PaintUnfoldedMap
from ._billiards_sounds import BilliardsSounds
from ._billiards_window import BilliardsWindow
from ._billiards_app import BilliardsApp

__all__ = (
  'radianceBytes',
  'roomLight',
  'Prism',
  'HAND_LENGTH',
  'HAND_WIDTH',
  'handPicture',
  'cuePicture',
  'cueBackAt',
  'STROKE_MOST',
  'FOLLOW_SECONDS',
  'FOLLOW_SHARE',
  'TableView',
  'BilliardsToolBar',
  'HitPicker',
  'PaintHitPicker',
  'ShotPanel',
  'PaintShotPanel',
  'UnfoldedMap',
  'PaintUnfoldedMap',
  'BilliardsSounds',
  'BilliardsWindow',
  'BilliardsApp',
)
