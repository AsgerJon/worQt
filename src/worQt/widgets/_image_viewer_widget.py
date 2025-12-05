"""
ImageViewerWidget provides a lower level widget displaying tensors as
images.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from . import BaseWidget


class ImageViewerWidget(BaseWidget):
  """
  ImageViewerWidget provides a lower level widget displaying tensors as
  images.

  The widget is intended as a child of a more complex widget. It fills the
  area assigned to it with the image. The image subclasses the BoxWidget
  which provides a traditional box model with padding, borders and
  margins. Each of these are defined by a 'Margins' object and a 'Color'
  object. 
  """
