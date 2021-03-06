#!/usr/bin/env python
import sys
import os

FILE_DIR = os.path.abspath(os.path.dirname(__file__))

from PyQt5.uic import loadUiType
# from PyQt5.QtCore import pyqtSlot
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMessageBox, QErrorMessage, QFileDialog
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.cm as cm
matplotlib.use('Qt5Agg')

import os, sys
from os.path import join
import pickle
import numpy as np

from matplotlib.backends.backend_qt5agg import (
        NavigationToolbar2QT as NavigationToolbar
)
from matplotlib.colors import ListedColormap

sys.path.insert(0, FILE_DIR)
import helpers as pvh
from helpers import isFileByExt
import version

# Load QT UI as main window
# change cwd to that which contains the entry module (this file/run script)
try:
    os.chdir(os.path.dirname(sys.argv[0]))
except:
    pass

# compile the gui layout
Ui_MainWindow, QMainWindow = loadUiType(os.path.join(FILE_DIR, 'window.ui'))

# GUI window subclass def
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # initialize the gui window
        super(Main, self).__init__()
        self.setupUi(self)
        self.setWindowTitle("PyViz - Volumetric Data Viewer (v{!s})".format(version.get_version()))

        # init cache variables
        self.lastValidPath = None
        self.lastValidFile = None

        # state variables
        self.cmap_manual_sel = False

        ########### Setup Signal/slot connections #################
        #  self.chk_recursive.stateChanged.connect(self.__slot_chk_recursive_statechanged__)
        self.chk_autoscale.stateChanged.connect(self.__slot_autoscale_changed)
        self.chk_colorbar.stateChanged.connect(self.__slot_colorbar_changed)
        self.combo_cmap.activated.connect(self.__slot_change_cmap__)
        self.combo_orientslice.activated.connect(self.__slot_orient_changed)
        self.chk_flipx.stateChanged.connect(self.__slot_refreshImage)
        self.chk_flipy.stateChanged.connect(self.__slot_refreshImage)
        # self.combo_ModeSelect.currentIndexChanged['QString'].connect(self.__slot_changefig_figselect__)
        self.txtPath.editingFinished.connect(self.__slot_txtPath_editingFinished__)
        self.num_Slice.setKeyboardTracking(False)
        self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)
        self.btn_PrevSlice.clicked.connect(self.__slot_PrevSlice_clicked__)
        self.btn_NextSlice.clicked.connect(self.__slot_NextSlice_clicked__)
        self.btn_Open.clicked.connect(self.__openFileDialog__)
        self.listImages.currentTextChanged.connect(self.__slot_listGeneric_currentTextChanged__)
        #  self.listMasks.currentTextChanged.connect(self.__slot_listMasks_currentTextChanged__)
        self.btn_Refresh.clicked.connect(self.__slot_refreshImage)
        self.btn_ReloadPath.clicked.connect(self.__slot_reloadPath)
        ###########################################################

        # get list of cmap names
        #  self.combo_cmap.addItems(list(plt.cm.datad)+list(plt.cm.cmaps_listed))
        self.combo_cmap.addItems(list(cm.cmap_d.keys()))

        # self.__refresh_feature_names__(self.txtPath.text())
        self.figdef = pvh.FigureDefinition_Summary()
        self.figdef.colorbar_enabled = self.chk_colorbar.isChecked()
        self.figdef.Build()
        self.__updateCanvas__(self.figdef)

    def __slot_autoscale_changed(self, state):
        self.figdef.autoscale = (state==2)
        self.__updateImage__()

    def __slot_colorbar_changed(self, state):
        self.figdef.colorbar_enabled = state
        self.figdef.rebuild()
        self.__slot_refreshImage()
        self.__updateCanvas__(self.figdef)

    def __slot_orient_changed(self, idx):
        orientation = self.combo_orientslice.currentText()
        if (orientation.lower() == 'coronal (y)'):
            self.chk_flipy.setChecked(True)
        elif (orientation.lower() == 'sagittal (x)'):
            self.chk_flipy.setChecked(True)
        else:
            self.chk_flipy.setChecked(False)
        self.figdef.rebuild()
        self.__updateImage__(idx)
        self.__updateCanvas__(self.figdef)

    def __slot_change_cmap__(self, idx):
        self.cmap_manual_sel = True
        self.figdef.clearAxes()
        self.__updateImage__()

    def __updateCanvas__(self, figdef):
        self.__clearCanvas__()
        self.mplvl.addWidget(figdef.canvas)
        self.mplvl.addWidget(NavigationToolbar(figdef.canvas, self.mplWindow, coordinates=True))

    def __clearCanvas__(self):
        for cnt in reversed(range(self.mplvl.count())):
            widget = self.mplvl.takeAt(cnt).widget()
            if widget is not None:
                # widget will be None if the item is a layout
                widget.close()

    def setSliceNum(self, n):
        self.num_Slice.valueChanged.disconnect(self.__slot_changefig_sliceNum__)
        self.num_Slice.setValue(int(n))
        self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)

    def setSliceMax(self, n):
        self.num_Slice.valueChanged.disconnect(self.__slot_changefig_sliceNum__)
        self.num_Slice.setMaximum(int(n))
        self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)

    def setSliceMin(self, n):
        self.num_Slice.valueChanged.disconnect(self.__slot_changefig_sliceNum__)
        self.num_Slice.setMinimum(int(n))
        self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)


    def getSliceNum(self):
        return int(self.num_Slice.value())

    def __slot_refreshImage(self, *args):
        self.figdef.ctprovider.resetCache()
        self.__updateImage__()

    def __slot_listGeneric_currentTextChanged__(self, currentText):
        if currentText:
            # self.setSliceNum(0)
            self.__updateImage__()

    #  def __slot_listMasks_currentTextChanged__(self, currentText):
    #      if currentText:
    #          self.__updateImage__()

    def __updateImage__(self, *args):
        # get CT filepath
        if self.listImages.currentItem():
            currentText = self.listImages.currentItem().text()
            basepath = str(self.txtPath.text())
            relpath = currentText.lstrip('./')
            fullpath = os.path.join(basepath, relpath)
            if self.lastValidFile != fullpath:
                redraw_canvas = True
            else:
                redraw_canvas = False
            self.lastValidFile = fullpath
        else: fullpath = None

        slicenum = self.getSliceNum()

        if fullpath:
            # cmap selection
            if not self.cmap_manual_sel:
                cmap='viridis'
                try: self.combo_cmap.setCurrentIndex(self.combo_cmap.findText(cmap))
                except: pass
            else:
                cmap = self.combo_cmap.currentText()

            try: manual_size = (int(self.txt_nx.text()), int(self.txt_ny.text()), int(self.txt_nz.text()))
            except: manual_size = None

            orientation = self.combo_orientslice.currentText()
            if (orientation.lower() == 'coronal (y)'):
                orientation = 1
            elif (orientation.lower() == 'sagittal (x)'):
                orientation = 2
            else:
                orientation = 0 # axial

            xaxis_flip = self.chk_flipx.isChecked()
            yaxis_flip = self.chk_flipy.isChecked()

            realslicecount = self.figdef.ctprovider.getSliceCount(fullpath, orientation, manual_size)
            if realslicecount <= slicenum:
                slicenum = realslicecount-1
                self.setSliceNum(slicenum)

            self.setSliceMax(realslicecount-1)
            self.setSliceMin(0)

            realsize = self.figdef.ctprovider.getSize()
            aspect_ratio = self.figdef.ctprovider.getAspect(orientation)
            if realsize is None:
                realsize = ['', '', '']
            self.txt_nx.setText(str(realsize[0]))
            self.txt_ny.setText(str(realsize[1]))
            self.txt_nz.setText(str(realsize[2]))

            ctdata = self.figdef.ctprovider.getImageSlice(fullpath, slicenum, orientation, size=manual_size)
            if ctdata is not None:
                if redraw_canvas:
                    #TODO this works but is overkill, we just need to reset the scaling of the current canvas
                    self.figdef.rebuild()
                    self.__updateCanvas__(self.figdef)
                self.figdef.drawImage(self.figdef.ax_ct, ctdata, cmap=cmap, flipx=xaxis_flip, flipy=yaxis_flip, aspect_ratio=aspect_ratio)
            else: self.figdef.clearContour(self.figdef.ax_ct)


    def __slot_txtPath_editingFinished__(self):
        filePath = str(self.txtPath.text())
        if self.__loadDirectory__(filePath):
            self.figdef.clearAxes()
            # reset auto cmap selection
            self.cmap_manual_sel = False

    def __slot_reloadPath(self):
        self.lastValidPath = ''
        self.__slot_txtPath_editingFinished__()

    def __loadDirectory__(self, root):
        """recursively find all BaseVolume objects contained in pickle files under root"""
        if (not root == self.lastValidPath):
            if (os.path.exists(root)):
                self.statusBar.showMessage('Rebuilding Data List, wait...')
                self.lastValidPath = root
                img_path_list, mask_path_list, feature_path_list = self.getImageFiles(root, recursive=self.chk_recursive.isChecked())
                self.listImages.clear()
                self.listImages.addItems(sorted(img_path_list))
                #  self.listMasks.clear()
                #  self.listMasks.addItems(mask_path_list)
                #  self.listFeatures.clear()
                #  self.listFeatures.addItems(feature_path_list)
                self.statusBar.clearMessage()
                return True
            else:
                self.statusBar.showMessage('Invalid Path Supplied, Try again.')
                return False


    def __slot_changefig_sliceNum__(self, sliceNum):
        self.__updateImage__()

    def __slot_PrevSlice_clicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum > 0 and currentSliceNum < self.figdef.sliceCount(self.lastValidFile)):
            self.setSliceNum(currentSliceNum-1)
            self.__updateImage__()
            return True
        else:
            return False

    def __slot_NextSlice_clicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum >= 0 and currentSliceNum < self.figdef.sliceCount(self.lastValidFile)-1):
            self.setSliceNum(currentSliceNum+1)
            self.__updateImage__()
            return True
        else:
            return False

    def __openFileDialog__(self, checkedbool):
        if (self.lastValidPath):
            default_dir = os.path.dirname(self.lastValidPath)
        else: default_dir = None
        foldername = QFileDialog.getExistingDirectory(self, 'Open DOI')#, directory=default_dir)
        if foldername is not None and foldername!='':
            self.txtPath.setText(foldername)
            self.__slot_txtPath_editingFinished__()

    def getImageFiles(self, root, recursive=True, ext=None):
        ignore_dirs = ['.git']
        ext = self.figdef.ctprovider.getValidExtensions()
        image_path_list = []
        mask_path_list = []
        feature_path_list = []
        for head, dirs, files in os.walk(root, followlinks=True):
            try:
                if os.path.basename(head) in ignore_dirs:
                    del dirs[:]; del files[:]; continue
                for f in files:
                    if os.path.splitext(f)[1].lower() in ext:
                        fullfilepath = os.path.join(head, f).replace(root.rstrip('/')+'/', './')
                        image_path_list.append(fullfilepath)
                for d in dirs:
                    for _f in os.listdir(os.path.join(head, d)):
                        if os.path.splitext(_f)[1] in ['.dcm', '.dicom']:
                            image_path_list.append(os.path.join(head, d).replace(root.rstrip('/')+'/', './'))
                            break
            except Exception as e:
                print(e)
            if not recursive:
                del dirs[:]
        return (image_path_list, mask_path_list, feature_path_list)


def start_gui():
    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    if len(sys.argv) > 1 and os.path.exists(sys.argv[1]):
        path = sys.argv[1]
    else:
        path = os.path.expanduser('~')
    main.txtPath.setText(path)
    main.show()
    return app.exec_()

# Start GUI window
if __name__ == '__main__':
    sys.exit(start_gui())
