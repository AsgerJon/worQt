"""
A harness fixture: a test module that fails while it is being imported.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

raise RuntimeError('the fixture module fails to import')
