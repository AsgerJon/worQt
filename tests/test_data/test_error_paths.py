"""
TestDataErrorPaths exercises the guard and error branches across the
'worQt.data' field, file and document layer: the type/missing guards on
'AbstractField'/'SingleField'/'ArrayField'/'ArrayLike', the encoder/decoder
resolution, the atomic-save and load failure handling on 'AbstractFile',
the path validation on 'MainFile'/'LocalFile', and the document field
registries.
"""
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
from __future__ import annotations

import os
from typing import TYPE_CHECKING

from worktoy.waitaminute import (TypeException, MissingVariable,
                                 SubclassException)

from worQt.data import (SingleField, ArrayField, ArrayLike, AbstractFile,
                        MainFile, LocalFile, AbstractDocument, AbstractItem,
                        NotifyBox)

from . import DataTest

if TYPE_CHECKING:  # pragma: no cover
  from typing import Any


class _Pt(AbstractItem):
  """A trivial array item."""
  x = NotifyBox[int](0)


class _Doc(AbstractDocument):
  """A document with one encoded single field, for clone/encode tests."""
  val = SingleField[int](0)

  @val.setEncoder
  def _enc(self, value: int) -> str:
    return str(value)

  @val.setDecoder
  def _dec(self, value: str) -> int:
    return int(value)


class _SubDoc(_Doc):
  """A subclass, so accessing 'val' triggers the clone-on-subclass path."""


class _Fixed(AbstractFile):
  """An 'AbstractFile' with an explicit, settable path."""

  def __init__(self, path: str) -> None:
    self._p = path

  @AbstractFile.filePath.GET
  def _getFilePath(self, **kwargs) -> str:
    return self._p


class TestDataErrorPaths(DataTest):
  """Guard and error branches across the data layer."""

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT FIELD  # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_value_type_missing(self) -> None:
    """A field with no type subscript has no value type."""
    with self.assertRaises(MissingVariable):
      SingleField()._getValueType()

  def test_keys_missing(self) -> None:
    """Unset encode/decode keys raise 'MissingVariable'."""
    field = SingleField[int]
    with self.assertRaises(MissingVariable):
      field._getEncodeKey()
    with self.assertRaises(MissingVariable):
      field._getDecodeKey()

  def test_keys_and_type_wrong_slot(self) -> None:
    """Non-string keys / non-type value-type slots raise 'TypeException'."""
    field = SingleField[int]
    field.__encode_key__ = 123
    field.__decode_key__ = 123
    field.__value_type__ = 'x'
    with self.assertRaises(TypeException):
      field._getEncodeKey()
    with self.assertRaises(TypeException):
      field._getDecodeKey()
    with self.assertRaises(TypeException):
      field._getValueType()

  def test_set_keys_type_guard(self) -> None:
    """The key setters reject non-strings."""
    field = SingleField[int]
    with self.assertRaises(TypeException):
      field._setEncodeKey(123)
    with self.assertRaises(TypeException):
      field._setDecodeKey(123)

  def test_class_getitem_non_type(self) -> None:
    """Subscripting a field with a non-type raises 'TypeException'."""
    with self.assertRaises(TypeException):
      _ = SingleField[123]

  def test_encoder_decoder_cached(self) -> None:
    """The encoder and decoder are resolved once and cached."""
    self.assertIs(_Doc.val._getEncoderFunction(),
                  _Doc.val._getEncoderFunction())
    self.assertIsNotNone(_Doc.val._getDecoderFunction())

  def test_encoder_decoder_recursion_guard(self) -> None:
    """A direct recursive call with an empty cache raises."""
    field = SingleField[int]
    with self.assertRaises(RecursionError):
      field._getEncoderFunction(_recursion=True)
    with self.assertRaises(RecursionError):
      field._getDecoderFunction(_recursion=True)

  def test_encoder_decoder_wrong_slot(self) -> None:
    """A non-callable cached encoder/decoder raises 'TypeException'."""
    field = SingleField[int]
    field.__cached_encoder__ = 123
    field.__cached_decoder__ = 123
    with self.assertRaises(TypeException):
      field._getEncoderFunction()
    with self.assertRaises(TypeException):
      field._getDecoderFunction()

  def test_get_clone_on_subclass(self) -> None:
    """Accessing an inherited field through a subclass clones it."""
    self.assertEqual(_SubDoc().val, 0)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  SINGLE FIELD  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_single_call_type_guard(self) -> None:
    """A default of the wrong type is rejected."""
    with self.assertRaises(TypeException):
      _Doc.val('not an int')

  def test_single_set_type_guard(self) -> None:
    """Setting a wrong-typed value is rejected."""
    with self.assertRaises(TypeException):
      _Doc.val.__instance_set__(_Doc(), 'not an int')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ARRAY FIELD  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_array_subscript_guards(self) -> None:
    """'ArrayField' rejects non-types and non-'AbstractItem' types."""
    with self.assertRaises(TypeException):
      _ = ArrayField[123]
    with self.assertRaises(SubclassException):
      _ = ArrayField[int]

  def test_array_call_rejects_items(self) -> None:
    """An array field takes no default contents."""
    with self.assertRaises(TypeError):
      ArrayField[_Pt]('default')

  def test_array_type_guards(self) -> None:
    """The item/array guards reject wrong types."""
    field = ArrayField[_Pt]
    with self.assertRaises(TypeException):
      field._itemTypeGuard(object())
    with self.assertRaises(TypeException):
      field._arrayTypeGuard('not an array')
    with self.assertRaises(TypeException):
      field._arrayTypeGuard(ArrayLike([object()]))

  def test_array_set_blocked(self) -> None:
    """An array field cannot be wholesale-assigned."""
    with self.assertRaises(TypeError):
      ArrayField[_Pt].__instance_set__(_Doc(), 1)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ARRAY LIKE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_array_like_unowned(self) -> None:
    """An 'ArrayLike' with no owner has no field or document."""
    array = ArrayLike()
    with self.assertRaises(MissingVariable):
      _ = array.owningField
    with self.assertRaises(MissingVariable):
      _ = array.owningDocument

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT FILE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_load_error_callback(self) -> None:
    """A missing file with a swallowing error callback yields '{}'."""
    fixed = _Fixed(os.path.join(self.tempDir.directory, 'missing.json'))
    self.assertEqual(fixed.load(lambda f: f.read(), lambda exc: True), {})

  def test_load_error_reraises(self) -> None:
    """A missing file with no callback re-raises."""
    fixed = _Fixed(os.path.join(self.tempDir.directory, 'missing.json'))
    with self.assertRaises(FileNotFoundError):
      fixed.load(lambda f: f.read())

  def test_save_open_error_callback(self) -> None:
    """An open failure with a swallowing callback returns 'None'."""
    target = os.path.join(self.tempDir.directory, 't.json')
    os.makedirs(target + '.tmp')  # blocks the temp-file open
    try:
      fixed = _Fixed(target)
      self.assertIsNone(fixed.save(lambda f: f.write('x'), lambda exc: True))
      with self.assertRaises(OSError):
        fixed.save(lambda f: f.write('x'))
    finally:
      os.rmdir(target + '.tmp')

  def test_save_callback_error_removes_temp(self) -> None:
    """A callback that raises removes the temp file and re-raises."""
    target = os.path.join(self.tempDir.directory, 'u.json')
    fixed = _Fixed(target)

    def boom(handle: Any) -> None:
      raise RuntimeError('boom')

    with self.assertRaises(RuntimeError):
      fixed.save(boom)
    self.assertFalse(os.path.exists(target + '.tmp'))

  def test_save_callback_error_temp_already_gone(self) -> None:
    """If the temp file is already gone when the callback raises, the error
    still propagates without a second removal attempt."""
    target = os.path.join(self.tempDir.directory, 'v.json')
    fixed = _Fixed(target)

    def vanish(handle: Any) -> None:
      os.remove(target + '.tmp')  # temp gone before the raise
      raise RuntimeError('boom')

    with self.assertRaises(RuntimeError):
      fixed.save(vanish)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  MAIN FILE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_main_file_dir_wrong_slot(self) -> None:
    """A non-string 'dirPath' slot raises on read."""
    main = MainFile()
    main.__dir_path__ = 123
    with self.assertRaises(TypeException):
      _ = main.dirPath

  def test_main_file_setters(self) -> None:
    """The path setters validate type and absoluteness."""
    main = MainFile()
    with self.assertRaises(TypeException):
      main.dirPath = 123
    with self.assertRaises(ValueError):
      main.dirPath = 'relative/path'
    with self.assertRaises(TypeException):
      main.fileName = 123
    with self.assertRaises(TypeException):
      main.filePath = 123
    with self.assertRaises(ValueError):
      main.filePath = 'relative'

  def test_main_file_dir_not_a_directory(self) -> None:
    """Pointing 'dirPath' at a file raises 'NotADirectoryError'."""
    afile = os.path.join(self.tempDir.directory, 'afile')
    open(afile, 'w').close()
    with self.assertRaises(NotADirectoryError):
      MainFile().dirPath = afile

  def test_main_file_name_recursion_and_type(self) -> None:
    """The 'fileName' recursion guard and slot type guard fire."""
    with self.assertRaises(RecursionError):
      MainFile()._getFileName(_recursion=True)
    main = MainFile()
    main.__file_name__ = 123
    with self.assertRaises(TypeException):
      _ = main.fileName

  def test_main_file_next_name_overflow(self) -> None:
    """With every candidate name taken, name generation gives up."""
    open(os.path.join(self.tempDir.directory, 'untitled_999.json'),
         'w').close()
    main = MainFile(self.tempDir.directory)
    with self.assertRaises(RecursionError):
      main._getNextName(_startCounter=999)

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  LOCAL FILE  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_local_file_missing_and_type(self) -> None:
    """Unset / wrong-typed 'mainFile' and 'fileName' raise."""
    blank = LocalFile.__new__(LocalFile)
    with self.assertRaises(MissingVariable):
      _ = blank.mainFile
    blank.__main_file__ = 123
    with self.assertRaises(TypeException):
      _ = blank.mainFile
    blank2 = LocalFile.__new__(LocalFile)
    with self.assertRaises(MissingVariable):
      _ = blank2.fileName
    blank2.__file_name__ = 123
    with self.assertRaises(TypeException):
      _ = blank2.fileName

  def test_local_file_setters(self) -> None:
    """The setters validate type, bare-name and same-directory rules."""
    local = LocalFile(MainFile(self.tempDir.directory), 'a.txt')
    with self.assertRaises(TypeException):
      local.mainFile = 123
    with self.assertRaises(ValueError):
      local.fileName = 'sub/x.txt'
    with self.assertRaises(ValueError):
      local.filePath = os.path.join('/elsewhere', 'x.txt')

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  ABSTRACT DOCUMENT  # # # # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_document_field_registries_wrong_slot(self) -> None:
    """Corrupt field registries raise 'TypeException'."""

    class _BadSingle(AbstractDocument):
      pass

    _BadSingle.__single_fields__ = 'bad'
    with self.assertRaises(TypeException):
      _BadSingle._getSingleFields()

    class _BadArray(AbstractDocument):
      pass

    _BadArray.__array_fields__ = 'bad'
    with self.assertRaises(TypeException):
      _BadArray._getArrayFields()

  def test_document_main_dir_round_trip(self) -> None:
    """'mainDir' reads from and writes to the main file's directory."""
    document = AbstractDocument(self.tempDir.directory)
    self.assertEqual(document.mainDir, self.tempDir.directory)
    document.mainDir = self.tempDir.directory

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
  #  RECURSION / CLONE GUARDS  # # # # # # # # # # # # # # # # # # # # # # # #
  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

  def test_field_get_clone_recursion_guard(self) -> None:
    """A '__get__' on a foreign owner that re-enters with the recursion
    flag set raises 'RecursionError'."""
    with self.assertRaises(RecursionError):
      _Doc.val.__get__(None, _SubDoc, _recursion=True)

  def test_field_get_clone_missing_name(self) -> None:
    """Cloning an unbound field (no field name) raises 'MissingVariable'."""
    with self.assertRaises(MissingVariable):
      SingleField[int].__get__(None, _Doc)

  def test_document_registry_recursion_guards(self) -> None:
    """The single/array field registry getters guard against re-entry."""

    class _Empty(AbstractDocument):
      pass

    with self.assertRaises(RecursionError):
      _Empty._getSingleFields(_recursion=True)
    with self.assertRaises(RecursionError):
      _Empty._getArrayFields(_recursion=True)

  def test_array_item_guard_accepts_valid(self) -> None:
    """'_itemTypeGuard' returns an item of the right type unchanged."""
    point = _Pt()
    self.assertIs(ArrayField[_Pt]._itemTypeGuard(point), point)

  def test_array_get_recursion_guard(self) -> None:
    """The array '__instance_get__' guards against a failed default seed."""
    field = ArrayField[_Pt]
    field.__field_name__ = 'arr'
    with self.assertRaises(RecursionError):
      field.__instance_get__(_Doc(), _Doc, _recursion=True)

  def test_array_like_from_field(self) -> None:
    """An 'ArrayLike' built from a field records it as the owning field."""
    array = ArrayLike(ArrayField[_Pt])
    self.assertIsInstance(array.owningField, ArrayField)

  def test_single_get_recursion_guard(self) -> None:
    """The single '__instance_get__' guards against a failed default seed."""
    document = _Doc()
    desc = _Doc.val
    desc.createContext(document, _Doc)
    try:
      with self.assertRaises(RecursionError):
        desc.__instance_get__(document, _Doc, _recursion=True)
    finally:
      desc.exitContext()

  def test_single_get_wrong_slot(self) -> None:
    """A wrongly-typed stored value raises 'TypeException' on read."""
    document = _Doc()
    setattr(document, _Doc.val.getPrivateName(), 'bad')
    with self.assertRaises(TypeException):
      _ = document.val

  def test_local_file_setter_type_guards(self) -> None:
    """The 'fileName'/'filePath' setters reject non-strings, and the
    single-argument constructor binds only the main file."""
    local = LocalFile(MainFile(self.tempDir.directory), 'a.txt')
    with self.assertRaises(TypeException):
      local.fileName = 123
    with self.assertRaises(TypeException):
      local.filePath = 123
    bare = LocalFile(MainFile(self.tempDir.directory))
    self.assertEqual(bare.dirPath, self.tempDir.directory)
