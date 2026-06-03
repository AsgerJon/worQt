"""
CADSettings is the 'Settings' subclass for the worQt structural-drawing app.
It gathers two tabs: 'Colours', collecting every colour the canvas paints
with, and 'Defaults', the view/grid/geometry defaults (pixels per grid cell,
snap tolerance, zoom limits, marker radii). The default values mirror the
constants in 'CADWidget', so this is the single editable home for the
palette and the view defaults. It persists to '.worQtCAD.config'.

Pure (Qt-free): it only describes values, so it builds and tests without a
'QApplication'. Wiring these values back onto a live 'CADWidget' is a
separate, UI-side concern.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.dispatch import overload

from ..settings import Settings

if TYPE_CHECKING:  # pragma: no cover
  pass


class CADSettings(Settings):
  """The worQt drawing app's settings: a 'Colours' tab and a 'Defaults'
  tab, defaulting to the canvas constants. Saved to '.worQtCAD.config'."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  DOMAIN SPECIFIC  # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def _defineColours(self, ) -> None:
    """Build the 'Colours' tab: every hue the canvas paints with."""
    tab = self.addTab('colours', 'Colours')
    tab.define('background', '#1e1e1e').withLabel('Background')
    tab.define('grid', '#2a3628').withLabel('Grid lines')
    tab.define('axes', '#3a3f4b').withLabel('Origin axes')
    tab.define('module', '#6f9a58').withLabel('Module line')
    tab.define('moduleSelected', '#a6e07a').withLabel('Module (selected)')
    tab.define('anchor', '#c678dd').withLabel('Anchor node')
    tab.define('member', '#61afef').withLabel('Member')
    tab.define('support', '#56b6c2').withLabel('Support')
    tab.define('load', '#e06c75').withLabel('Load arrow')
    tab.define('settlement', '#d19a66').withLabel('Settlement arrow')
    tab.define('dimension', '#ffd24a').withLabel('Dimension')
    tab.define('preview', '#e5c07b').withLabel('Preview rubber band')
    tab.define('halo', '#ffe082').withLabel('Selection halo')

  def _defineDefaults(self, ) -> None:
    """Build the 'Defaults' tab: the view, grid and geometry defaults."""
    tab = self.addTab('defaults', 'Defaults')
    grid = tab.define('gridTargetPx', 24).withLabel('Grid spacing (px)')
    grid.withHelp('Target pixels per grid cell')
    tab.define('snapPixels', 10).withLabel('Snap tolerance (px)')
    tab.define('pointRadius', 4).withLabel('Point radius (px)')
    tab.define('anchorRadius', 5).withLabel('Anchor radius (px)')
    tab.define('perpTolPx', 2).withLabel('Perpendicular-lock tol (px)')
    tab.define('defaultScale', 1.0).withLabel('Default zoom (px/mm)')
    tab.define('minScale', 0.1).withLabel('Minimum zoom (px/mm)')
    tab.define('maxScale', 4000.0).withLabel('Maximum zoom (px/mm)')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  CONSTRUCTORS  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  @overload()
  def __init__(self, ) -> None:
    Settings.__init__(self, 'worQtCAD')
    self._defineColours()
    self._defineDefaults()
