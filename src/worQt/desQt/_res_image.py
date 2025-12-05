"""
The 'resImage' function takes an image name as argument and attempts to
locate an image file with that name in /etc/resources/images/.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

import os

from worktoy.utilities import textFmt
from worktoy.work_io import validateExistingFile

from . import Etc, ImgExtensions


class _R:
  images = Etc('resources', 'images')
  extensions = ImgExtensions()


def resImage(name: str, fallback: str = None) -> str:
  """
  Takes an image name as argument and attempts to locate an image file
  with that name in '/etc/resources/images/'.

  Args:
    name (str): The name of the image file to locate.
    fallback (str, optional): A fallback image name to use if the primary
      name is not found. Defaults to None.

  Returns:
    str: The full path to the located image file.
  """
  if os.path.isabs(name):
    if os.path.isfile(name):
      return validateExistingFile(name)
    infoSpec = """The provided absolute image path '%s' does not point to a
    valid file!"""
    info = textFmt(infoSpec % name)
    raise FileNotFoundError(info)
  _r = _R()
  for item in os.listdir(_r.images):
    for part in name.lower().split('.'):
      if part in _r.extensions:
        continue
      if part in item.lower():
        return os.path.join(_r.images, item)
  if fallback is not None:
    if os.path.isabs(fallback):
      return validateExistingFile(fallback)
    try:
      out = resImage(fallback)
    except FileNotFoundError:
      pass  # Continue to raise below.
    else:
      return validateExistingFile(out)
  infoSpec = """Unable to locate image resource with name '%s'!"""
  info = textFmt(infoSpec % name)
  raise FileNotFoundError(info)
