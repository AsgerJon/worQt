"""
Testing __init__ in multiple inheritance scenario.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations


class A:
  def __init__(self, *args, **kwargs) -> None:
    print('A before super')
    super().__init__(*args, **kwargs)
    print('A.__init__ called')


class B:
  def __init__(self, *args, **kwargs) -> None:
    print('B before super')
    # super().__init__(*args, **kwargs)
    print('B.__init__ called')


class C(A, B):
  def __init__(self, *args, **kwargs) -> None:
    print('C before super')
    super().__init__(*args, **kwargs)
    print('C.__init__ called')
