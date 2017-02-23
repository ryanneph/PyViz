import sys
sys.path.insert(0, '/home/ryan/projects/python_libs/')
sys.path.insert(0, '/home/ryan/projects/ctpt_segm/HYPO_Scripts')
import os
from os.path import join, exists
import numpy as np

from utils.rttypes import MaskableVolume, ROI
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)
from constants import *

def __getFiles__(rootDirPath, recursive=False):
    #Return a list of filepaths in the first level of the rootDirPath
    returnFileList = []
    for dirName, subdirList, fileList in os.walk(rootDirPath):
        for fname in fileList:
            if ('.pickle' in fname.lower()) and not ('roi' in fname.lower()):
                returnFileList.append(join(dirName, fname))
        if (not recursive):
            del subdirList[:]  # keep the walk from recursing
    return sorted(returnFileList)


from abc import ABCMeta, abstractmethod
class baseFigureDefinition:
    __metaclass__ = ABCMeta
    def __init__(self):
        pass

    # must be redefined by subclass
    @abstractmethod
    def Build(self, fig):
        self.figure = fig
        self.canvas = FigureCanvas(self.figure)
        self.__initialized__ = True

class FigureDefinition_Summary(baseFigureDefinition):
    def __init__(self):
        super().__init__()
        self.ax_ct = None

    def Build(self):
        fig = Figure()
        self.ax_ct = fig.add_axes([0.05,0.05,0.9, 0.9])

        for ax in fig.get_axes():
            ax.set_axis_off()

        # setup imagedataproviders
        self.ctprovider = ImageDataProvider()
        self.maskprovider = MaskDataProvider()
        self.featureprovider = ImageDataProvider()

        # must call last and pass figure instance
        super().Build(fig)

    def clearAxes(self, ax=None):
        if not ax:
            ax_list = [x for x in self.figure.get_axes()]
        else: ax_list = [ax]

        for ax in ax_list:
            for item in ax.get_images():
                item.remove()
            self.clearContour(ax)
        self.canvas.draw()

    def drawImage(self, ax, data):
        """update ax with new image data"""
        if (not self.__initialized__): self.Build()

        # if nothing is drawn yet, add axes instance
        if len(ax.get_images()) == 0:
            ax.imshow(data, cmap='gray')
            # fit imageAxes to current data extents
            # ax.autoscale(enable=True)
        else:
            ax_img = ax.get_images()[0]
            ax_img.set_array(data)
            # ax.relim()  # update axes limits
            ax.autoscale_view()
            ax_img.autoscale()  # scale colormap to current data (vmin/vmax)
        self.canvas.draw()

    def clearContour(self, ax):
        ax.collections = []
        self.canvas.draw()

    def drawContour(self, ax, maskdata):
        self.clearContour(ax)
        ax.contour(maskdata, levels=[0], colors=['red'])
        # ax.relim()
        # ax.autoscale_view()
        self.canvas.draw()

    def sliceCount(self, filepath):
        return self.ctprovider.getSliceCount(filepath)

from utils import rttypes as rttypes
class BaseDataProvider:
    __metaclass__ = ABCMeta
    def __init__(self):
        self.__cachedimage__ = None
        self.__cachedimagepath__ = None

    def __checkCached__(self, filepath):
        if (self.__cachedimage__ and filepath == self.__cachedimagepath__):
            return True
        else: return False

    @abstractmethod
    def __fileLoader__(self, filepath):
        return

    def __loadFile__(self, filepath):
        if not self.__checkCached__(filepath):
            # [re]load data volume from file
            if not os.path.exists(filepath):
                raise FileNotFoundError
            del self.__cachedimage__
            self.__cachedimage__ = self.__fileLoader__(filepath)
            self.__cachedimagepath__ = filepath

    def getImageSlice(self, filepath, slicenum):
        self.__loadFile__(filepath)
        return self.__cachedimage__.getSlice(slicenum)

    def getSliceCount(self, filepath):
        self.__loadFile__(filepath)
        return self.__cachedimage__.frameofreference.size[2]

class ImageDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()

    def __fileLoader__(self, filepath):
        return rttypes.MaskableVolume().fromPickle(filepath)

class MaskDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()

    def __fileLoader__(self, filepath):
        return rttypes.ROI.fromPickle(filepath).makeDenseMask()

