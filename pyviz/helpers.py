import sys
import os
from os.path import join, exists
import re
import struct

import numpy as np
from scipy.io import loadmat, savemat, whosmat
import h5py

import matplotlib as mpl
import matplotlib.pyplot as plt
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
        self.canvas.draw()
        self.__initialized__ = True

class FigureDefinition_Summary(baseFigureDefinition):
    def __init__(self):
        super().__init__()
        self.ax_ct = None
        self.ax_colorbar = None
        self.colorbar_enabled = True
        self.origin = None
        self.autoscale = True

    def Build(self):
        fig = Figure()
        if self.colorbar_enabled:
            self.ax_ct = fig.add_axes([0.0,0.025,0.85,0.95])
            self.ax_colorbar = fig.add_axes([0.85,0.025,0.06,0.95])
        else:
            self.ax_ct = fig.add_axes([0.0,0.0,1.0,1.0])

        self.ax_ct.set_axis_off()
        #  for ax in fig.get_axes():
        #      ax.set_axis_off()

        if not self.__initialized__:
            # setup imagedataproviders
            self.ctprovider = ImageDataProvider()
            self.featureprovider = ImageDataProvider()

        # must call last and pass figure instance
        super().Build(fig)

    def rebuild(self):
        self.ax_ct = None
        self.ax_colorbar = None
        plt.close(self.figure)
        self.Build()

    def clearAxes(self, ax=None):
        if not ax:
            ax_list = [x for x in self.figure.get_axes()]
        else: ax_list = [ax]

        for ax in ax_list:
            for item in ax.get_images():
                item.remove()
            self.clearContour(ax)
        self.canvas.draw()

    def drawImage(self, ax, data, cmap='gray', flipy=False, colorbar=False):
        """update ax with new image data"""
        if (not self.__initialized__): self.Build()
        if (self.colorbar_enabled != colorbar):
            self.colorbar_enabled = colorbar
            self.rebuild()
            ax = self.ax_ct

        origin = 'lower' if flipy else 'upper'
        if origin != self.origin:
            self.origin = origin
            self.clearAxes()

        # if nothing is drawn yet, add axes instance
        if len(ax.get_images()) == 0:
            try:
                ax_img = ax.imshow(data, cmap=cmap, origin=origin)
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
            if self.autoscale:
                ax_img.autoscale()  # scale colormap to current data (vmin/vmax)
        if self.colorbar_enabled:
            plt.colorbar(ax_img, self.ax_colorbar)
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

class BaseDataProvider:
    __metaclass__ = ABCMeta
    def __init__(self):
        self.__cachedimage__ = None
        self.__cachedimagepath__ = None

    def __checkCached__(self, filepath):
        if (self.__cachedimage__ is not None and filepath == self.__cachedimagepath__):
            return True
        else: return False

    @abstractmethod
    def __fileLoader__(self, filepath):
        return

    def load(self, filepath, size=None):
        if (self.__loadFile__(filepath, size)):
            return self.__cachedimage__
        else: return None

    def __loadFile__(self, filepath, size=None):
        try:
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
                    if self.__cachedimage__ is not None:
                        status = True
                        self.__cachedimagepath__ = filepath
        except Exception as e:
            print(e)
            status = False
        return status

    def getImageSlice(self, filepath, slicenum, orientation=0, size=None):
        try:
            if self.__loadFile__(filepath, size=size):
                if self.__cachedimage__ is not None:
                    if orientation==0:
                        slice = self.__cachedimage__[slicenum, :, :]
                    elif orientation==1:
                        slice = self.__cachedimage__[:, slicenum, :]
                    else:
                        slice = self.__cachedimage__[:, :, slicenum]
                    return slice
        except Exception as e:
            print(e)

    def getSliceCount(self, filepath, orientation=0, size=None):
        if self.__loadFile__(filepath, size=size):
            return self.__cachedimage__.shape[orientation]
        else: return 0

class ImageDataProvider(BaseDataProvider):
    def __init__(self):
        super().__init__()
        self.valid_exts = set()
        self.loaders = []
        self._addLoader(self._loadFromMat, ['.mat'])
        self._addLoader(self._loadFromLegacyDoseMat, ['.mat'])
        self._addLoader(self._loadFromNpy, ['.npy', '.npz'])
        self._addLoader(self._loadFromH5, ['.h5', '.hdf5', '.dose', '.fmap'])
        self._addLoader(self._loadFromDicom, ['', '.dcm', '.dicom'])
        self._addLoader(self._loadFromBinWithSize, ['', '.bin', '.raw'])
        self._addLoader(self._loadFromCTIBin, ['.cti', '.ctislice', '.seg'])
        self._addLoader(self._loadFromBin, ['', '.bin', '.raw'])

        self._cached_size = None

    def _addLoader(self, callable, valid_exts=[]):
        self.loaders.append({"callable": callable, "valid_exts": [str(x).lower() for x in valid_exts]})
        for ext in valid_exts:
            self.valid_exts.add(ext)

    def getSize(self):
        return self._cachedsize

    def getValidExtensions(self):
        return list(self.valid_exts)

    def resetCache(self):
        self.__cachedimage__ = None
        self.__cachedimagepath__ = None
        self._cachedsize = None

    def _loadFromBinWithSize(self, filepath, *args, **kwargs):
        with open(filepath, 'rb') as fd:
            sizebuf = fd.read(struct.calcsize('I'*3))
            databuf = fd.read()
        size = np.array(struct.unpack('I'*3, sizebuf))
        arr = np.array(struct.unpack('f'*np.product(size), databuf)).reshape(size[::-1])
        #  arr = np.transpose(arr, [0, 2, 1])
        return arr

    def _loadFromBin(self, filepath, size, *args, **kwargs):
        if size is None:
            raise ValueError("size must be 3-tuple")
        with open(filepath, 'rb') as fd:
            buf = fd.read()
        except_msgs = []
        for type in ['f', 'd']:
            try:
                arr = np.array(struct.unpack(type*np.product(size), buf)).reshape(size[::-1])
                break
            except Exception as e:
                except_msgs.append(str(e))
                continue
        if arr is None:
            raise Exception("\n".join(except_msgs))
        return arr

    def _loadFromCTIBin(self, filepath, size, *args, **kwargs):
        if size is None:
            raise ValueError("size must be 3-tuple")
        with open(filepath, 'rb') as fd:
            buf = fd.read()
        arr = np.array(struct.unpack('h'*np.product(size), buf)).reshape(size[::-1])
        arr = np.transpose(arr, [0, 2, 1])
        return arr

    def _loadFromH5(self, filepath, *args, **kwargs):
        with h5py.File(filepath, 'r') as fd:
            excepts = []
            for k in ["data", "volume", "arraydata"]:
                try:
                    return fd[k][:]
                except Exception as e:
                    excepts.append(e)
                    continue
            raise Exception('\n'.join(excepts))

    def _loadFromMat(self, filepath, *args, **kwargs):
        # Load from matlab (matrad "cube")
        d = loadmat(filepath)
        return d['ct']['cube'][0,0][0,0].transpose((2,0,1))

    def _loadFromLegacyDoseMat(self, filepath, *args, **kwargs):
        import sparse2dense.recon
        vol = sparse2dense.recon.reconstruct_from_dosecalc_mat(filepath)
        return vol

    def _loadFromNpy(self, filepath, *args, **kwargs):
        data = np.load(filepath)
        if isinstance(data, np.ndarray):
            return data
        else:
            return next(iter(data.values()))

    def _loadFromDicom(self, filepath, *args, **kwargs):
        import pymedimage.rttypes as rttypes
        if os.path.splitext(filepath)[1] == '':
            if not os.path.isdir(filepath):
                raise TypeError('file must be a directory containing dicom files or a single dicom file')
            return rttypes.BaseVolume.fromDir(filepath).data
        else:
            return rttypes.BaseVolume.fromDicom(filepath).data
        return None

    def __fileLoader__(self, filepath, size=None):
        excepts = []
        attempts = 0
        while attempts < len(self.loaders):
            attempts += 1
            try:
                loader = self.loaders[attempts-1]
                if os.path.splitext(filepath)[1].lower() not in loader['valid_exts']:
                    raise ValueError("file doesn't match valid valid extensions: [{!s}]".format(', '.join(loader['valid_exts'])))
                vol = loader['callable'](filepath, size)
                if vol is not None:
                    self._cachedsize = vol.shape[::-1]
                    return vol
            except Exception as e:
                excepts.append(e)
                self.resetCache()

        print("Failed to load image with errors:")
        for e in excepts:
            print(e, '\n')
        return None # failed to open
