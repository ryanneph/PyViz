#!/usr/bin/env python

import sys
import os
import pyviz.gui
from PyQt5 import QtWidgets

# Start GUI window
def main(args=None):
    app = QtWidgets.QApplication(sys.argv)
    main = pyviz.gui.Main()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        path = sys.argv[1]
    else:
        path = os.path.expanduser('~')
    main.txtPath.setText(path)
    main.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

