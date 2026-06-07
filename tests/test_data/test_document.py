"""
TestDocument subclasses 'DataTest' and provides tests for the
'worQt.data.AbstractDocument' class.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from .examples import SampleDocument
from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class TestDocument(DataTest):
  """
  TestDocument subclasses 'DataTest' and provides tests for the
  'worQt.data.AbstractDocument' class.
  """

  def test_document(self) -> None:
    """
    Test the 'SampleDocument' class.
    """
    document = SampleDocument()
    self.assertFalse(os.path.exists(document.mainFile.filePath))
    document.save()
    self.assertTrue(os.path.exists(document.mainFile.filePath))
    doc2 = SampleDocument()
    doc2.titleField = """Never gonna give you up"""
    doc2.numberField = 420
    self.assertNotEqual(document.titleField, doc2.titleField)
    self.assertNotEqual(document.numberField, doc2.numberField)
    doc2.load()
    self.assertEqual(document.titleField, doc2.titleField)
    self.assertEqual(document.numberField, doc2.numberField)
