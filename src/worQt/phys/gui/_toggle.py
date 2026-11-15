"""
Toggle is a button that stays in or out and says which, in words and
in colour: its name, then 'on' (lit green) or 'off' (dim). (The user,
of a plain checkable button: it is "particularly difficult to know if
they are on or not".) The phys windows' switches are Toggles.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtWidgets import QPushButton

TOGGLE_STYLE = ('QPushButton { padding: 4px 12px; border-radius: 4px; '
                'border: 1px solid #555a62; background: #2a2d32; '
                'color: #8d939b; } '
                'QPushButton:checked { background: #2f9e5b; '
                'border: 1px solid #5fd08c; color: white; }')


class Toggle(QPushButton):
  """Toggle is a button that stays in or out and says which: its
  'name', then 'on' (lit) or 'off' (dim); 'tip' says what it does."""

  def __init__(self, name: str, tip: str, on: bool) -> None:
    QPushButton.__init__(self)
    self.name = name
    self.setCheckable(True)
    self.setToolTip(tip)
    self.setStyleSheet(TOGGLE_STYLE)
    self.toggled.connect(self._said)
    self.setChecked(on)
    self._said(on)

  def _said(self, on: bool) -> None:
    """Says on the button whether it is on."""
    self.setText('%s: %s' % (self.name, 'on' if on else 'off'))
