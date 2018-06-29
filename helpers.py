import sys
import os
from os.path import join, exists
import re
import numpy as np

from pymedimage.rttypes import MaskableVolume, ROI
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)

def sanitize(string, dirty_chars=['.']):
    for c in dirty_chars:
        string = string.replace(c, '\{}'.format(c))
    return string

def isFileByExt(fname, exts=None):
    if not exts: return True
    if isinstance(exts, str): exts=[exts]
    for e in [sanitize(x) for x in exts]:
        m = re.search(r'{}$'.format(e), fname, re.IGNORECASE)
        if m is not None:
            return True
    return False


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
        self.ax_ct = fig.add_axes([0.0,0.0,1.0, 1.0])

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
        try:
            if self.contours is not None:
                for c in self.contours.collections:
                    c.remove()
                self.canvas.draw()
        except:
            pass

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

    def __loadFile__(self, filepath, size=None):
        status = False
        if filepath:
            status = True
            if not self.__checkCached__(filepath):
                status = False
                # [re]load data volume from file
                if not os.path.exists(filepath):
                    raise FileNotFoundError
                del self.__cachedimage__
                self.__cachedimage__ = self.__fileLoader__(filepath, size)
                if self.__cachedimage__:
                    status = True
                    self.__cachedimagepath__ = filepath
        return status

    def getImageSlice(self, filepath, slicenum, orientation=0, size=None):
        if self.__loadFile__(filepath, size=size):
            if self.__cachedimage__:
                slice = self.__cachedimage__.getSlice(slicenum, orientation)
                if orientation == 2:
                    slice = slice.transpose()
                return slice
        return None

    def getSliceCount(self, filepath, orientation=0, size=None):
        if self.__loadFile__(filepath, size=size):
            return self.__cachedimage__.frameofreference.size[2-orientation]
        else: return 0

class ImageDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()
    def __fileLoader__(self, filepath, size=None):
        common_sizes = [
            (44,64,44), (85, 176, 201), (300, 300, 300), (350, 350, 350), (400, 400, 298),
            #  (48,60,48), (51,63,51), (83,505,505), (181,253, 295),(181, 253, 295),
            #  (88,88,88), (176,176,176), (116,228,116), (57,41,57), (113,81,112), (112, 200, 112), (800,800,800), (146,417,449), (150,115,125), (240, 677, 677),
            #  (635,635,635), (600,600,404), (615,615,615), (401,101,399), (315,315,315),
            #  (147,280,147), (147,147,147), (327,327,327),
            #  (161,321,159), (176,336,176), (342,302,302), (300,300,156), (173,261,261), (187,144,156),
            #  (182,422,422), (88,168,88), (81,161,80), (621,621,600), (323,323,323),
            #  (480,480,250), (240,240,125), (150,115,125), (128,171,184), (450,450,450), (350,350,350), (700, 700, 700), (500, 500, 500), (600,600,600),
            #    (166,171,171), (136,171,184), (187,171,171), (163,171,171), (187,171,184), (187,171,184),
            #  (126,157,169), (134,261,281), (166,469,469),
            #  (267,267,267),
            #  (342,302,332),
            #  (342,482,482),
            #  (450,450,300),
            #  (320,334,320),
            #  (220,171,220),
            #  (334, 167, 200),
            #  (173, 112, 134),
            #  (176,336,176),
            #  (161,321,159),
            #  (88,168,88),
            #  (10,10, 1), (40,40,1), (32,32,1), (200, 200, 1), (20, 20, 1),
            #  (24,8, 1),
            (24,10, 1),
            (24,1,1),
            (32,1,1),
        ]
        try:
            return rttypes.MaskableVolume.load(filepath)
        except Exception as e:
            print(e)
            if size is not None:
                common_sizes.insert(0, size)
            for size in common_sizes:
                try: return rttypes.MaskableVolume.fromBinary(filepath, size)
                except Exception as e: print(e)
        sys.stdout.write('image size: {!s} bytes did not match any common_sizes\n'.format(os.path.getsize(filepath)))
        return None # failed to open



class MaskDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()

    def __fileLoader__(self, filepath):
        if isFileByExt(filepath, '.h5'):
            return rttypes.ROI.fromHDF5(filepath).makeDenseMask()
        elif isFileByExt(filepath, '.pickle'):
            return rttypes.ROI.fromPickle(filepath).makeDenseMask()
        else: return None
