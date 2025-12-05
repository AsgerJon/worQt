"""
ActionMeta provides the metaclass for resources associated with actions.
"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

from typing import TYPE_CHECKING

from worktoy.core import MetaType
from worktoy.utilities import maybe, textFmt

from . import ActionResource

if TYPE_CHECKING:  # pragma: no cover
  from typing import Iterator, Any, Never, TypeAlias, Type, Self

  Bases: TypeAlias = tuple[Type[Any], ...]
  Space: TypeAlias = dict[str, Any]


class ActionMeta(MetaType):
  """
  ActionMeta provides the metaclass for resources associated with actions.
  """

  __resource_names__ = None

  def __new__(mcls, name: str, bases: Bases, space: Space, **kw) -> Self:
    try:
      toQ_ = space['toQ']
    except KeyError:
      infoSpec = """When trying to create class '%s' no implementation of 
      the required method 'toQ' was found!"""
      info = infoSpec % name
      raise TypeError(textFmt(info))
    else:
      return super().__new__(mcls, name, bases, space, **kw)

  def _getResources(cls) -> dict[str, ActionResource]:
    return maybe(cls.__resource_names__, dict())

  def _registerIconName(cls, name: str, iconName: ActionResource) -> None:
    existing = cls._getResources()
    existing[name] = iconName
    cls.__resource_names__ = existing

  def __iter__(cls, ) -> Iterator[tuple[str, ActionResource]]:
    yield from cls._getResources().items()

  def __getattr__(cls, name: str) -> ActionResource:
    for fieldName, resourceName in cls:
      for part in resourceName.nameParts():
        if part not in name:
          break
      else:
        return resourceName
    return type.__getattribute__(cls, name)

  def toQ(cls, resource: ActionResource) -> Never:
    """
    Derived classes must implement this method to provide the resource as
    appropriate. An icon resource for example should return a QIcon
    object. The implementation on the metaclass raises 'TypeError',
    but this will happen only for derived classes not implementing the
    method.
    """

  def __call__(cls, *args, **kwargs) -> Any:
    for arg in args:
      if isinstance(arg, ActionResource):
        return cls.toQ(arg)
      if isinstance(arg, str):
        if hasattr(cls, arg):
          return cls.toQ(getattr(cls, arg))
      return cls.toQ(ActionResource(arg))
    return super().__call__(*args, **kwargs)
