from PyQt5.uic import loadUiType
# from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QMessageBox, QErrorMessage, QFileDialog
import matplotlib
matplotlib.use('Qt5Agg')

import os, sys
from os.path import join
import pickle

from matplotlib.backends.backend_qt5agg import (
        NavigationToolbar2QT as NavigationToolbar
)

sys.path.insert(0, '/home/ryan/projects/ctpt_segm')
sys.path.insert(0, '/home/ryan/projects/ctpt_segm/TCIA_Scripts')

import pyVizHelpers as pvh
from constants import *

# Load QT UI as main window
# change cwd to that which contains the entry module (this file/run script)
try:
    os.chdir(os.path.dirname(sys.argv[0]))
except:
    pass

# compile the gui layout
Ui_MainWindow, QMainWindow = loadUiType('window.ui')

# GUI window subclass def
class Main(QMainWindow, Ui_MainWindow):
    def __init__(self):
        # initialize the gui window
        super(Main, self).__init__()
        self.setupUi(self)

        # init cache variables
        self.lastValidPath = None
        self.lastValidFile = None

        ## Setup Signal/slot connections
        # self.combo_ModeSelect.currentIndexChanged['QString'].connect(self.__slot_changefig_figselect__)
        self.txtPath.editingFinished.connect(self.__slot_txtPath_editingFinished__)
        self.num_Slice.setKeyboardTracking(False)
        # self.num_Slice.valueChanged.connect(self.__slot_changefig_sliceNum__)
        self.btn_PrevSlice.clicked.connect(self.__slot_PrevSlice_clicked__)
        self.btn_NextSlice.clicked.connect(self.__slot_NextSlice_clicked__)
        self.btn_Open.clicked.connect(self.__openFileDialog__)
        self.listImages.currentTextChanged.connect(self.__slot_listGeneric_currentTextChanged__)
        self.listMasks.currentTextChanged.connect(self.__slot_listMasks_currentTextChanged__)

        # self.__refresh_feature_names__(self.txtPath.text())
        self.figdef = pvh.FigureDefinition_Summary()
        self.figdef.Build()
        self.__updateCanvas__(self.figdef)

    def __updateCanvas__(self, figdef):
        self.__clearCanvas__()
        self.mplvl.addWidget(figdef.canvas)
        self.mplvl.addWidget(NavigationToolbar(figdef.canvas, self.mplWindow, coordinates=True))

    def __clearCanvas__(self):
        for cnt in reversed(range(self.mplvl.count())):
            widget = self.mplvl.takeAt(cnt).widget()
            if widget is not None:
                # widget will be None if the item is a layout
                try:
                    widget.figure.close()
                except:
                    print('couldn\'t close figure')
                widget.close()
            #self.mplvl.removeWidget(self.canvas)
            #self.canvas.close()
            #self.mplvl.removeWidget(self.toolbar)
            #self.toolbar.close()
            #self.canvas.draw()

    # def __get_CurrentFigBuilder__(self):
    #     return self.dict_key2figBuilder[self.dict_name2key[self.combo_ModeSelect.currentText()]]

    # def __slot_changefig_figselect__(self, figname):
    #     figname = str(figname)
    #     rootPath = str(self.lastValidPath)
    #     sliceNum = int(self.num_Slice.value())
    #     self.__changefig__(figname, rootPath, sliceNum)

    def setSliceNum(self, n):
        self.num_Slice.setValue(int(n))

    def getSliceNum(self):
        return int(self.num_Slice.value())

    def __slot_listGeneric_currentTextChanged__(self, currentText):
        if currentText:
            # self.setSliceNum(0)
            self.__updateImage__()

    def __slot_listMasks_currentTextChanged__(self, currentText):
        if currentText:
            self.__updateImage__()

    def __updateImage__(self):
        # get CT filepath
        if self.listImages.currentItem():
            currentText = self.listImages.currentItem().text()
            basepath = str(self.txtPath.text())
            relpath = currentText.lstrip('./')
            fullpath = os.path.join(basepath, relpath)
            self.lastValidFile = fullpath
        else: fullpath = None

        # get mask filepath
        if self.listMasks.currentItem():
            currentText = self.listMasks.currentItem().text()
            basepath = str(self.txtPath.text())
            relpath = currentText.lstrip('./')
            fullpath_mask = os.path.join(basepath, relpath)
        else: fullpath_mask = None

        slicenum = self.getSliceNum()

        if fullpath:
            ctdata = self.figdef.ctprovider.getImageSlice(fullpath, slicenum)
            self.figdef.drawImage(self.figdef.ax_ct, ctdata)
            if fullpath_mask:
                maskdata = self.figdef.maskprovider.getImageSlice(fullpath_mask, slicenum)
                self.figdef.drawContour(self.figdef.ax_ct, maskdata)
            else: self.figdef.clearContour(self.figdef.ax_ct)


    def __slot_txtPath_editingFinished__(self):
        filePath = str(self.txtPath.text())
        if self.__loadDirectory__(filePath):
            self.figdef.clearAxes()

    def __loadDirectory__(self, root):
        """recursively find all BaseVolume objects contained in pickle files under root"""
        if (not root == self.lastValidPath):
            if (os.path.exists(root)):
                # self.__refresh_feature_names__(filePath)
                self.statusBar.showMessage('Rebuilding Data List, wait...')
                # self.__changefig__(figname, filePath, sliceNum)
                # self.num_Slice.setMinimum(0)
                # self.num_Slice.setMaximum(self.dict_key2figBuilder[self.dict_name2key[figname]].slicecount-1)
                self.lastValidPath = root
                img_path_list, mask_path_list, feature_path_list = getImageFiles(root, recursive=True)
                self.listImages.clear()
                self.listImages.addItems(sorted(img_path_list))
                self.listMasks.clear()
                self.listMasks.addItems(mask_path_list)
                self.listFeatures.clear()
                self.listFeatures.addItems(feature_path_list)
                self.statusBar.clearMessage()
                return True
            else:
                self.statusBar.showMessage('Invalid Path Supplied, Try again.')
                return False


    # def __slot_changefig_sliceNum__(self, sliceNum):
    #     if (sliceNum >= 0 and sliceNum < self.__get_CurrentFigBuilder__().slicecount):
    #         figname = str(self.combo_ModeSelect.currentText())
    #         rootPath = str(self.lastValidPath)
    #         sliceNum = int(sliceNum)
    #         self.__changefig__(figname, rootPath, sliceNum)

    # def __changefig__(self, figname, filePath, sliceNum, feature_filename=None):
    #     self.statusBar.showMessage('Loading, wait...')
    #     figkey = self.dict_name2key[figname]
    #     args = {'filePath': filePath,
    #             'sliceNum': sliceNum,
    #             'feature_filename': feature_filename}
    #     fig = self.dict_key2figBuilder[figkey].get_figure(args)
    #     if (fig == False):
    #         self.statusBar.showMessage('Invalid Path Supplied, Try again.')
    #         return False
    #     else:
    #         self.__drawfig__(fig)
    #         self.statusBar.clearMessage()
    #         return True

    def __slot_PrevSlice_clicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum > 0 and currentSliceNum < self.figdef.sliceCount(self.lastValidFile)):
            self.num_Slice.setValue(currentSliceNum-1)
            self.__updateImage__()
            return True
        else:
            return False

    def __slot_NextSlice_clicked__(self, checkedbool):
        currentSliceNum = int(self.num_Slice.value())
        if (currentSliceNum >= 0 and currentSliceNum < self.figdef.sliceCount(self.lastValidFile)-1):
            self.num_Slice.setValue(currentSliceNum+1)
            self.__updateImage__()
            return True
        else:
            return False

    def __openFileDialog__(self, checkedbool):
        if (self.lastValidPath):
            default_dir = os.path.dirname(self.lastValidPath)
        else: default_dir = None
        foldername = QFileDialog.getExistingDirectory(self, 'Open DOI', directory=default_dir)
        if foldername is not None and foldername!='':
            self.txtPath.setText(foldername)
            self.__slot_txtPath_editingFinished__()

def getImageFiles(root, recursive=True):
    image_path_list = []
    mask_path_list = []
    feature_path_list = []
    for head, dirs, files in os.walk(root):
        for f in files:
            if (os.path.splitext(f)[1].lower() == '.pickle'):
                fullfilepath = os.path.join(head, f)
                with open(fullfilepath, mode='rb') as pf:
                    obj = pickle.load(pf)
                    cls = obj.__class__.__name__
                    fullfilepath = fullfilepath.replace(root.rstrip('/')+'/', './')
                    if ('basevolumepickle' in cls.lower() or
                        'maskablevolumepickle' in cls.lower()):
                        image_path_list.append(fullfilepath)
                        # if not obj.feature_label:
                        #     image_path_list.append(fullfilepath)
                        # else: feature_path_list.append(fullfilepath)
                    elif ('roi' in cls.lower()):
                        mask_path_list.append(fullfilepath)
                    # else: print('{!s} is pickle but classname={!s}'.format(fullfilepath, cls))
                    del obj
            elif (os.path.splitext(f)[1].lower() == '.dcm'):
                image_path_list.append(head.replace(root.rstrip('/')+'/', './'))
                break
        if not recursive:
            del dirs[:]
    return (image_path_list, mask_path_list, feature_path_list)


# Start GUI window
if __name__ == '__main__':
    import sys
    from PyQt5 import QtWidgets

    app = QtWidgets.QApplication(sys.argv)
    main = Main()
    ##################################
    debugpath = '/media/hdd1/projects/radio/TCIA_NSCLC-RADIOMICS_LUNG1/DICOM_DATA/LUNG1-001/'
    main.txtPath.setText(debugpath)
    # main.addfigBuilder('Summary (CT and Feature)', pvh.FigBuilder_Summary('summary'))
    ##################################
    main.show()
    sys.exit(app.exec_())
