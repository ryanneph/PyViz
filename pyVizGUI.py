from PyQt4.uic import loadUiType
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtGui import QMessageBox, QErrorMessage
import os, sys

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)

# Load QT UI as main window
try:
    os.chdir(os.path.dirname(sys.argv[0]))
except:
    pass

Ui_MainWindow, QMainWindow = loadUiType('window.ui')

# GUI window subclass def
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super(Main, self).__init__()
        self.setupUi(self)
        # setup for figure changing
        self.dict_key2figBuilder = {}
        self.dict_name2key = {}
        self.currentFigBuilder = None
        self.lastValidPath = None

        ## Setup Signal/slot connections
        self.combo_ModeSelect.currentIndexChanged['QString'].connect(self.__slot_changefig_figselect__)
        self.txtPath.editingFinished.connect(self.__slot_changefig_txtPath__)
        self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)
        self.btn_PrevSlice.clicked.connect(self.__prevSliceClicked__)
        self.btn_NextSlice.clicked.connect(self.__nextSliceClicked__)
        figblank = Figure()
        self.__drawfig__(figblank)

    def addfigBuilder(self, name, figBuilder):
        self.dict_name2key[name] = figBuilder.key
        self.dict_key2figBuilder[figBuilder.key] = figBuilder
        self.combo_ModeSelect.addItem(name)

    def __drawfig__(self, fig):
        self.__clearfig__()
        self.canvas = FigureCanvas(fig)
        self.canvas.draw()
        self.mplvl.addWidget(self.canvas)
        self.toolbar = NavigationToolbar(self.canvas, self.mplFigs, coordinates=True)
        self.mplvl.addWidget(self.toolbar)

    def __clearfig__(self):
        for cnt in reversed(range(self.mplvl.count())):
            # takeAt does both the jobs of itemAt and removeWidget
            # namely it removes an item and returns it
            widget = self.mplvl.takeAt(cnt).widget()
            if widget is not None:
                # widget will be None if the item is a layout
                widget.close()
            #self.mplvl.removeWidget(self.canvas)
            #self.canvas.close()
            #self.mplvl.removeWidget(self.toolbar)
            #self.toolbar.close()
            #self.canvas.draw()

    def __get_CurrentFigBuilder__(self):
        return self.dict_key2figBuilder[self.dict_name2key[self.combo_ModeSelect.currentText()]]

    def __slot_changefig_figselect__(self, figname):
        figname = str(figname)
        rootPath = str(self.lastValidPath)
        sliceNum = int(self.num_Slice.value())
        self.__changefig__(figname, rootPath, sliceNum)

    def __slot_changefig_txtPath__(self):
        import pyVizHelpers as pvh
        figname = str(self.combo_ModeSelect.currentText())
        rootPath = str(self.txtPath.text())
        sliceNum = int(self.num_Slice.value())
        if (os.path.exists(rootPath) and len(pvh.__getFiles__(rootPath + pvh.imagePaths['source'])) > 0):
            self.statusBar.showMessage('Rebuilding figure cache, wait...')
            self.__changefig__(figname, rootPath, sliceNum)
            self.num_Slice.setMinimum(0)
            self.num_Slice.setMaximum(self.dict_key2figBuilder[self.dict_name2key[figname]].slicecount-1)
            self.lastValidPath = rootPath
            self.statusBar.clearMessage()
        else:
            self.statusBar.showMessage('Invalid Path Supplied, Try again.')

    def __slot_changefig_sliceNum__(self, sliceNum):
        if (sliceNum >= 0 and sliceNum < self.__get_CurrentFigBuilder__().slicecount):
            figname = str(self.combo_ModeSelect.currentText())
            rootPath = str(self.lastValidPath)
            sliceNum = int(sliceNum)
            self.__changefig__(figname, rootPath, sliceNum)

    def __changefig__(self, figname, rootPath, sliceNum):
        self.statusBar.showMessage('Loading, wait...')
        figkey = self.dict_name2key[figname]
        fig = self.dict_key2figBuilder[figkey].get_figure(rootPath, sliceNum)
        if (fig == False):
            self.statusBar.showMessage('Invalid Path Supplied, Try again.')
            return False
        else:
            self.__drawfig__(fig)
            self.statusBar.clearMessage()
            return True

    def __prevSliceClicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum > 0 and currentSliceNum < self.__get_CurrentFigBuilder__().slicecount):
            self.num_Slice.setValue(currentSliceNum-1)
            return True
        else:
            return False

    def __nextSliceClicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum >= 0 and currentSliceNum < self.__get_CurrentFigBuilder__().slicecount-1):
            self.num_Slice.setValue(currentSliceNum+1)
            return True
        else:
            return False


# Start GUI window
if __name__ == '__main__':
    import sys
    from PyQt4 import QtGui

    app = QtGui.QApplication(sys.argv)
    main = Main()
    ##################################
    #import matplotlib.pyplot as plt
    import pyVizHelpers as pvh

    debugpath = '/Users/Ryan/Desktop/14_20_left_uvw/'
    main.lastValidPath = debugpath
    main.txtPath.setText(debugpath)
    main.addfigBuilder('STW', pvh.FigBuilder_STW('stw'))
    main.addfigBuilder('Summary (2x3)',pvh.FigBuilder_Summary('summary'))
    main.addfigBuilder('Compare (1x3)',pvh.FigBuilder_Compare('compare'))
    main.addfigBuilder('Subtraction (1x3)',pvh.FigBuilder_Subtract('subtract'))
    ##################################
    main.show()
    sys.exit(app.exec_())
