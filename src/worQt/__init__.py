"""
The 'worQt' library provides a general purpose Qt application based on the
Qt for Python framework (PySide6) and the general purpose 'worktoy'
library. The library takes advantage of the 'worktoy' library to implement
advanced python features without requiring boilerplate code. Of particular
significance is the following novel syntax:

class ComplexNumber:
  #  Complex number implementation

  realPart = AttriBox[float](0.0)
  imagPart = AttriBox[float](0.0)

The above lines of code uses the brackets to specify the type of the
descriptor variables. What is of particular interest here is that no
'float' object has actually been created at this point in the class body.
The 'AttriBox' descriptor has recorded the intended type and the arguments
it will later use to instantiate the 'float' object.

The 'AttriBox' descriptor in 'worktoy' was in fact motivated by the unique
requirements of the PySide6 framework. The special 'QObject' class
provided by PySide6 require a running 'QCoreApplication' instance before
'QObject' instances may be instantiated. Attempting to instantiate without
a running application will cause an exception outside the Python
interpreter but instead in the C++ layer of the PySide6 framework, where a
segmentation fault will occur.

The application logic generally consists of multiple classes in hierarchy
beginning at the running application instance followed by window classes
and then widgets, menus and other components. The main window class will
generally be a subclass of 'QMainWindow' and will own a 'QWidget'
instance and a 'QLayout' instance. Because of the requirement for a
running application instance, the main window class must not instantiate
any 'QObject' instances of any kind in its class body. Traditionally,
example applications would dynamically set attributes such as these during
'__init__'.

While the main window class cannot instantiate any 'QObject' in its class
body, it can instantiate 'AttriBox' descriptors that wrap the 'QObject'
subclass. Now typically, 'QObject' subclasses such as 'QWidget' generally
expect their parent widget to be passed to its constructor, but there is
no way to pass the main window class to the 'AttriBox' descriptor in the
class body, as it instantiates before the main window class even exists.
When the arguments intended for future instantiation are expected by the
'AttriBox' descriptor, the class does not yet exist.

This very problem motivated to 'THIS' sentinel object implemented in the
'worktoy' library

class MainWindow(QMainWindow):
  #  Main window implementation

  baseWidget = AttriBox[QWidget](THIS)
  ...  # Remaining implementation omitted for brevity

When an instance of the 'MainWindow' class accesses the 'baseWidget'
AttriBox descriptor, the 'THIS' sentinel object is replaced with the
instance itself. Effectively, the following code is executed:

main = MainWindow()
main.baseWidget = QWidget(main)

When setting the 'baseWidget' attribute, all positional and keyword
arguments will later be passed to the constructor of the 'type' specified
in the brackets.

"""
#  AGPL-3.0 license
#  Copyright (c) 2025 Asger Jon Vistisen
from __future__ import annotations

try:
  from icecream import ic
except ImportError:  # pragma: no cover
  ic = lambda *_: None
else:
  ic.configureOutput(includeContext=True)

from ._qt_box import QtBox
from . import desQt
from ._abstract_base import AbstractBase
from . import nums
from . import core
from . import app
from . import menus
from . import widgets
from . import windows

__all__ = [
    'ic',
    'QtBox',
    'AbstractBase',
    'core',
    'desQt',
    'nums',
    'app',
    'menus',
    'widgets',
    'windows',
]
