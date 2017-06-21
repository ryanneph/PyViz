import __link_pymedimage__
import sys
import os
from os.path import join, exists
import numpy as np

from pymedimage.rttypes import MaskableVolume, ROI
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)
from constants import *

# def __getFiles__(rootDirPath, recursive=False):
#     #Return a list of filepaths in the first level of the rootDirPath
#     returnFileList = []
#     for dirName, subdirList, fileList in os.walk(rootDirPath):
#         for fname in fileList:
#             if ('.pickle' in fname.lower()) and not ('roi' in fname.lower()):
#                 returnFileList.append(join(dirName, fname))
#             if ('.dcm' in fname.lower()):
#                 returnFileList.append(dirName)
#         if (not recursive):
#             del subdirList[:]  # keep the walk from recursing
#     return sorted(returnFileList)


from abc import ABCMeta, abstractmethod
class baseFigureDefinition:
    __metaclass__ = ABCMeta
    def __init__(self):
        self.figure = None
        self.canvas = None
        self.contours = None
        self.__initialized__ = None

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
        self.origin = None

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

    def drawImage(self, ax, data, cmap='gray', flipy=False):
        """update ax with new image data"""
        if (not self.__initialized__): self.Build()

        origin = 'lower' if flipy else 'upper'
        if origin != self.origin:
            self.clearAxes()

        # if nothing is drawn yet, add axes instance
        if len(ax.get_images()) == 0:
            try:
                ax.imshow(data, cmap=cmap, origin=origin)
            except Exception as e:
                print(e)
                return
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
        if self.contours is not None:
            for c in self.contours.collections:
                c.remove()
            self.canvas.draw()

    def drawContour(self, ax, maskdata):
        self.clearContour(ax)
        self.contours = ax.contour(maskdata, levels=[0], colors=['red'])
        # ax.relim()
        # ax.autoscale_view()
        self.canvas.draw()

    def sliceCount(self, filepath, orientation=0):
        return self.ctprovider.getSliceCount(filepath, orientation)

from pymedimage import rttypes as rttypes
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
        status = False
        if filepath:
            status = True
            if not self.__checkCached__(filepath):
                status = False
                # [re]load data volume from file
                if not os.path.exists(filepath):
                    raise FileNotFoundError
                del self.__cachedimage__
                self.__cachedimage__ = self.__fileLoader__(filepath)
                if self.__cachedimage__:
                    status = True
                    self.__cachedimagepath__ = filepath
        return status

    def getImageSlice(self, filepath, slicenum, orientation=0):
        if self.__loadFile__(filepath):
            if self.__cachedimage__:
                return self.__cachedimage__.getSlice(slicenum, orientation)
        return None

    def getSliceCount(self, filepath, orientation=0):
        if self.__loadFile__(filepath):
            return self.__cachedimage__.frameofreference.size[2-orientation]
        else: return 0

class ImageDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()

    def __fileLoader__(self, filepath):
        common_sizes = [(256,256,256), # iso vol
                        (40,40, 1),    # fmap
                        (140,110,65),  # calc_bbox
                        (140,100,134), # calc_box (body contour)
                        (502,502,502), # full_max_bev_size
                        (248,248,248), # max_bev_size
                        (210,155,210)  # pillar_grid_test
                        ]
        if os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() == '.pickle':
            return rttypes.MaskableVolume.fromPickle(filepath)
        if os.path.isfile(filepath) and os.path.splitext(filepath)[1].lower() == '.mat':
            return rttypes.MaskableVolume.fromMatlab(filepath)
        elif os.path.isdir(filepath):
            return rttypes.MaskableVolume.fromDir(filepath, recursive=True)
        elif (os.path.isfile(filepath)):
            for size in common_sizes:
                try: return rttypes.MaskableVolume.fromBinary(filepath, size)
                except: pass
        sys.stdout.write('image size: {!s} bytes did not match any common_sizes\n'.format(os.path.getsize(filepath)))
        return None # failed to open



class MaskDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()

    def __fileLoader__(self, filepath):
        return rttypes.ROI.fromPickle(filepath).makeDenseMask()
