"""
QuestsToolBar subclasses 'CircuitsToolBar' and is the row of buttons
above a quest's circuit.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from ...circuits.gui import CircuitsToolBar


class QuestsToolBar(CircuitsToolBar):
  """
  QuestsToolBar subclasses 'CircuitsToolBar' and is the row of buttons
  above a quest's circuit: the circuits' own buttons without 'Examples';
  a part's button greyed out until its kind is unlocked.
  """

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  NAMESPACE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  #  Fallback Variables
  __fallback_groups__ = (2,)  # the buttons groups start at
  __fallback_examples__ = False  # whether there is an 'Examples' button
