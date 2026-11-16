# -*- mode: python ; coding: utf-8 -*-
#  Apache-2.0 license
#  Copyright (c) 2026 Asger Jon Vistisen
"""
PyInstaller's recipe for Keglebillard (worQt's billiard room alone): on
the Mac an app ('Keglebillard.app', the icon 'icon.png'), elsewhere a
folder; everything in it (Python, Qt with Qt Quick 3D, numpy, Warp and
its compiler, worktoy, the billiards). Warp compiles its kernels from
their Python source, so worQt's and Warp's sources go in beside their
bytecode. Built from the repo's root:

  pyinstaller --noconfirm packaging/keglebillard/keglebillard.spec
"""
import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files
from PyInstaller.utils.hooks import collect_dynamic_libs
from PyInstaller.utils.hooks import collect_submodules

HERE = Path(SPECPATH)
SRC = HERE.parent.parent / 'src'
NAME = 'Keglebillard'
#  What the billiards never asks for (the other labs' heavy kit, Qt's
#  web views and the like).
UNUSED = ['torch', 'scipy', 'matplotlib', 'tkinter', 'IPython',
          'openseespy'] + ['PySide6.Qt%s' % name for name in (
  'WebEngineCore', 'WebEngineWidgets', 'WebEngineQuick', 'WebView',
  '3DCore', '3DRender', 'Charts', 'DataVisualization', 'Graphs', 'Pdf',
  'PdfWidgets', 'Bluetooth', 'Nfc', 'Sensors', 'SerialPort',
  'Positioning', 'Location', 'RemoteObjects')]
#  Warp's own libraries (its kernels' runtime and its compiler: named
#  'warp.so' and 'warp-clang.so' on Linux, '*.dylib' on the Mac; the
#  hooks' own patterns look only for 'lib*.so').
WARP_LIBS = ['*.so', '*.dylib', '*.dll']

analysis = Analysis(
  [str(HERE / 'keglebillard.py')],
  pathex=[str(SRC)],
  binaries=collect_dynamic_libs('warp', search_patterns=WARP_LIBS),
  datas=(collect_data_files('worQt.gaming.billiards')
         + collect_data_files('warp', excludes=['examples', 'tests'])),
  hiddenimports=(collect_submodules('worQt.gaming.billiards')
                 + ['worQt.gaming.pusher._sound_player',
                    'PySide6.QtMultimedia', 'PySide6.QtQuick3D']),
  excludes=UNUSED,
  module_collection_mode={'worQt': 'pyz+py', 'warp': 'pyz+py'},
  noarchive=False,
)
#  Qt's parts the billiards never loads (its QML imports only QtQuick,
#  QtQuick3D and QtQuick3D.Helpers): the hooks bring every QML plugin
#  and what they need (the web engine alone is 200 MB), so they go here
#  by name, libraries, plugins and QML alike.
DROPPED = ('WebEngine', 'WebView', 'WebChannel', 'WebSockets', 'Pdf',
           'Qt3D', 'Qt63D', 'Charts', 'Graphs', 'DataVisualization',
           'Location', 'Positioning', 'VirtualKeyboard', 'Quick3DPhysics',
           'Quick3DXr', 'Scxml', 'StateMachine', 'Sensors', 'SerialPort',
           'SerialBus', 'Bluetooth', 'Nfc', 'RemoteObjects', 'TextToSpeech',
           'SpatialAudio', 'HttpServer', 'Designer', 'QtHelp', 'Qt6Help',
           'Qt5Compat', 'Qt6Core5Compat', 'QtCore5Compat')


def kept(entries: list) -> list:
  """Returns the entries (destination first) not of a dropped part."""
  return [entry for entry in entries
          if not any(name in entry[0] for name in DROPPED)]


analysis.binaries = kept(analysis.binaries)
analysis.datas = kept(analysis.datas)
archive = PYZ(analysis.pure)
program = EXE(
  archive,
  analysis.scripts,
  [],
  exclude_binaries=True,
  name=NAME,
  debug=False,
  strip=False,
  upx=False,
  console=sys.platform != 'darwin',
)
folder = COLLECT(
  program,
  analysis.binaries,
  analysis.datas,
  strip=False,
  upx=False,
  name=NAME,
)
if sys.platform == 'darwin':
  app = BUNDLE(
    folder,
    name='%s.app' % NAME,
    icon=str(HERE / 'icon.png'),
    bundle_identifier='io.github.asgerjon.keglebillard',
    info_plist={'CFBundleDisplayName': NAME,
                'CFBundleShortVersionString': '1.0',
                'NSHighResolutionCapable': True,
                'LSMinimumSystemVersion': '13.0'},
  )
