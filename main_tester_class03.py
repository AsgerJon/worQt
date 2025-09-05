"""
Testing multiple inheritance combining QObject and normal classes.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from PySide6.QtCore import QObject
from PySide6.QtWidgets import QWidget


class AbstractBase(QObject):  # Second base
  """
  AbstractBase provides a general abstract base class for abstract classes
  across the worQt framework. It includes functionality
  """

  pass


class AbstractWidget(QWidget, AbstractBase):  # First base
  """
  AbstractWidget provides a base class for widgets in the worQt framework.
  """
