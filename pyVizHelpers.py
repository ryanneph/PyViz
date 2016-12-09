import sys
sys.path.insert(0, '/home/ryan/projects/ctpt_segm')
sys.path.insert(0, '/home/ryan/projects/ctpt_segm/TCIA_Scripts')
import os
from os.path import join, exists
import numpy as np

from utils.rttypes import MaskableVolume, ROI
import matplotlib as mpl
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt4agg import (
        FigureCanvasQTAgg as FigureCanvas,
        NavigationToolbar2QT as NavigationToolbar)
from TCIA_constants import *

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

    # def __refreshSliceCount__(self, doi):
    #     # filelist = __getFiles__(filePath, recursive=True)
    #     activevol = MaskableVolume().fromPickle(join(p_DCM_DATA, doi, f_CT_PICKLE))
    #     self.slicecount = activevol.frameofreference.size[2]
    #     return self.slicecount

    # must be redefined by subclass
    @abstractmethod
    def Build(self, fig):
        self.figure = fig
        self.canvas = FigureCanvas(self.figure)
        self.__initialized__ = True

    # def __BuildSliceCache__(self, args):
    #     doi = args['doi']
    #     self.__refreshSliceCount__(doi)
    #     if self.slicecount > 0:
    #         for key in list(self.dict_figures):
    #             self.dict_figures[key].clear()
    #         self.dict_figures.clear()
    #         try: self.last_figure.clear()
    #         except: pass
    #         self.last_figure = None
    #         self.last_sliceNum = None
    #         self.last_doi = doi
    #         for sliceNum in range(0,self.slicecount):
    #             args['sliceNum'] = sliceNum
    #             self.dict_figures[sliceNum] = self.__Build__(args)

    # def get_figure(self, args):
    #     # unpack args
    #     filePath = args['filePath']
    #     sliceNum = args['sliceNum']
    #     feature_filename = args['feature_filename']

    #     if exists(filePath):
    #         doi = os.path.basename(filePath.rstrip('/'))
    #         args['doi'] = doi

    #         if (sliceNum > self.slicecount-1):
    #             self.__refreshSliceCount__(doi)
    #         sliceNum = max(0, min(sliceNum, self.slicecount-1))
    #         if (doi == self.last_doi and sliceNum == self.last_sliceNum and sliceNum>=0 and sliceNum<self.slicecount
    #             and feature_filename == self.last_feature_filename):
    #             returnfigure = self.last_figure
    #         elif (doi == self.last_doi and feature_filename == self.last_feature_filename and sliceNum != self.last_sliceNum):
    #             # use cached slice figure
    #             returnfigure = self.dict_figures[sliceNum]
    #         else:
    #             self.__BuildSliceCache__(args)
    #             returnfigure = self.dict_figures[sliceNum]
    #         self.last_figure = returnfigure
    #         self.last_sliceNum = sliceNum
    #         return returnfigure
    #     else:
    #         #invalid filePath
    #         return False

class FigureDefinition_Summary(baseFigureDefinition):
    def __init__(self):
        super().__init__()

    def Build(self):
        fig = Figure()

        # ct_vol = MaskableVolume().fromPickle(join(p_DCM_DATA, doi, f_CT_PICKLE))
        # roi = ROI.fromPickle(join(p_DCM_DATA, doi, f_ROI_PICKLE))
        # roi_densemask = roi.makeDenseMask(ct_vol.frameofreference)

        self.ax_ct = fig.add_axes([0,0,1,1])
        # self.ax_ct.contour(roi_densemask.getSlice(sliceNum), levels=[0], colors=[(0,1,0.1)])
        # fig.tight_layout()
        self.ax_ct.set_title('CT')

        # self.ax_feat = fig.add_subplot(1,2,2)
        # try:
        #     feat_vol_path = join(p_FEATURES, doi, f_FEATURE_PICKLE)
        # except:
        #     feat_vol_path = None
        # if (f_FEATURE_PICKLE and exists(feat_vol_path)):
        #     feat_vol = MaskableVolume().fromPickle(feat_vol_path)
        #     ax2.imshow(feat_vol.getSlice(sliceNum), cmap='gray')
        #     ax1.hold(True)
        #     ax2.set_title('Feature: {!s}'.format(f_FEATURE_PICKLE))
        # else:
        #     ax2.text(0.5, 0.5, 'Feature not found', horizontalalignment='center', verticalalignment='center')

        for ax in fig.get_axes():
            ax.set_axis_off()

        # setup imagedataproviders
        self.ctprovider = ImageDataProvider()
        self.maskprovider = MaskDataProvider()
        self.featureprovider = ImageDataProvider()

        super().Build(fig)

    def drawImage(self, ax, data):
        """update ax with new image data"""
        if (not self.__initialized__): self.Build()

        # if nothing is drawn yet, add axes instance
        if len(ax.get_images()) == 0:
            ax.imshow(data, cmap='gray')
            # fit imageAxes to current data extents
            ax.autoscale()
        else:
            ax_img = ax.get_images()[0]
            ax_img.set_array(data)
            ax.relim()  # update axes limits
            ax_img.autoscale()  # scale colormap to current data (vmin/vmax)
        self.canvas.draw()

    def drawContour(self, ax, maskdata):
        ax.collections = []
        ax.contour(maskdata, levels=[0], colors=['red'])

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

