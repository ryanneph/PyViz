import os
import numpy as np

# Setup relative paths dict
imagePaths = {'source': '/source',
         'target': '/target',
         'warp': '/warp',
         'jacobian': '/Jac',
         'u': '/U',
         'v': '/V',
         'w': '/W'}

def __getFiles__(rootDirPath):
    #Return a list of filepaths in the first level of the rootDirPath
    returnFileList = []
    for dirName, subdirList, fileList in os.walk(rootDirPath):
        for fname in fileList:
            if ('File' in fname) and ('.txt' in fname):
                returnFileList.append(dirName + '/' + fname)
        del subdirList[:] #keep the walk from recursing
    return returnFileList

def __importTextImage__(filePath):
    #reads a text image format and creates an np.array that can be used with pyplot.imshow
    array2d = [[]]
    with open(filePath) as file:
        array2d = [[float(digit) for digit in line.split()] for line in file]
    return array2d

def getTextImage(rootPath, imagetype, sliceNum):
    return __importTextImage__(__getFiles__(rootPath + imagePaths[imagetype])[sliceNum])

from abc import ABCMeta, abstractmethod
class baseFigBuilder:
    __metaclass__ = ABCMeta

    def __init__(self, key):
        self.key = key
        self.dict_figures = {}
        self.last_figure = None #will hold built figure after Build() is called
        self.last_rootPath = None
        self.last_sliceNum = None
        self.slicecount = 0

    def __refreshSliceCount__(self, rootPath):
        slicelist = __getFiles__(rootPath + imagePaths['source'])
        self.slicecount = len(slicelist)
        return self.slicecount

    @abstractmethod
    def __Build__(self, rootPath, sliceNum):
        pass

    def __BuildSliceCache__(self, rootPath):
        self.__refreshSliceCount__(rootPath)
        if self.slicecount > 0:
            for key in list(self.dict_figures):
                self.dict_figures[key].clear()
            self.dict_figures.clear()
            try: self.last_figure.clear()
            except: pass
            self.last_figure = None
            self.last_sliceNum = None
            self.last_rootPath = rootPath
            for sliceNum in range(0,self.slicecount):
                self.dict_figures[sliceNum] = self.__Build__(rootPath, sliceNum)

    def get_figure(self, rootPath, sliceNum):
        if os.path.exists(rootPath):
            if (sliceNum > self.slicecount-1):
                self.__refreshSliceCount__(rootPath)
            sliceNum = max(min(sliceNum, self.slicecount-1),0)
            if (rootPath == self.last_rootPath and sliceNum == self.last_sliceNum and sliceNum>=0 and sliceNum<self.slicecount):
                returnfigure = self.last_figure
            elif (rootPath == self.last_rootPath and sliceNum != self.last_sliceNum):
                # use cached slice figure
                returnfigure = self.dict_figures[sliceNum]
            else:
                self.__BuildSliceCache__(rootPath)
                returnfigure = self.dict_figures[sliceNum]
            self.last_figure = returnfigure
            self.last_sliceNum = sliceNum
            return returnfigure
        else:
            #invalid rootPath
            return False

class FigBuilder_Summary(baseFigBuilder):
    def __Build__(self, rootPath, sliceNum):
        super().__Build__(rootPath,sliceNum)
        from matplotlib.figure import Figure
        imaxes = []
        g_alpha = 0.4
        fig = Figure()
        fig.suptitle('{0} - Slice{1:04d}'.format(rootPath, sliceNum))

        ax1 = fig.add_subplot(231)
        ax1.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        ax1.hold(True)
        cax = ax1.imshow(getTextImage(rootPath, 'u', sliceNum), alpha=g_alpha)
        fig.colorbar(cax)
        imaxes.append(ax1)
        ax1.set_title('U/source')

        ax2 = fig.add_subplot(232)
        ax2.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        ax2.hold(True)
        cax = ax2.imshow(getTextImage(rootPath, 'v', sliceNum), alpha=g_alpha)
        fig.colorbar(cax)
        imaxes.append(ax2)
        ax2.set_title('V/source')

        ax3 = fig.add_subplot(233)
        ax3.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        ax3.hold(True)
        cax = ax3.imshow(getTextImage(rootPath, 'w', sliceNum), alpha=g_alpha)
        fig.colorbar(cax)
        imaxes.append(ax3)
        ax3.set_title('W/source')

        ax4 = fig.add_subplot(234)
        ax4.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        imaxes.append(ax4)
        ax4.set_title('source')

        ax5 = fig.add_subplot(235)
        ax5.imshow(getTextImage(rootPath, 'target', sliceNum),cmap='Greys_r')
        imaxes.append(ax5)
        ax5.set_title('target')

        ax6 = fig.add_subplot(236)
        ax6.imshow(getTextImage(rootPath, 'warp', sliceNum),cmap='Greys_r')
        imaxes.append(ax6)
        ax6.set_title('warp')

        for ax in imaxes:
            ax.set_axis_off()
        self.last_figure = fig
        return fig

class FigBuilder_STW(baseFigBuilder):
    def __Build__(self, rootPath, sliceNum):
        super().__Build__(rootPath,sliceNum)
        from matplotlib.figure import Figure
        imaxes = []
        fig = Figure()
        fig.suptitle('{0} - Slice{1:04d}'.format(rootPath, sliceNum))

        ax1 = fig.add_subplot(131)
        ax1.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        imaxes.append(ax1)
        ax1.set_title('source')

        ax2 = fig.add_subplot(132)
        ax2.imshow(getTextImage(rootPath, 'target', sliceNum),cmap='Greys_r')
        imaxes.append(ax2)
        ax2.set_title('target')

        ax3 = fig.add_subplot(133)
        ax3.imshow(getTextImage(rootPath, 'warp', sliceNum),cmap='Greys_r')
        ax3.hold(True)
        imaxes.append(ax3)
        ax3.set_title('warp')

        for ax in imaxes:
            ax.set_axis_off()
        self.last_figure = fig
        return fig

class FigBuilder_Compare(baseFigBuilder):
    def __Build__(self, rootPath, sliceNum):
        super().__Build__(rootPath,sliceNum)
        from matplotlib.figure import Figure
        imaxes = []
        g_alpha = 0.6
        fig = Figure()
        fig.suptitle('{0} - Slice{1:04d}'.format(rootPath, sliceNum))

        ax1 = fig.add_subplot(131)
        ax1.imshow(getTextImage(rootPath, 'source', sliceNum),cmap='Greys_r')
        imaxes.append(ax1)
        ax1.set_title('source')

        ax2 = fig.add_subplot(132)
        ax2.imshow(getTextImage(rootPath, 'target', sliceNum),cmap='Greys_r')
        imaxes.append(ax2)
        ax2.set_title('target')

        ax3 = fig.add_subplot(133)
        ax3.imshow(getTextImage(rootPath, 'target', sliceNum),cmap='Greys_r')
        ax3.hold(True)
        cax = ax3.imshow(getTextImage(rootPath, 'warp', sliceNum),alpha=g_alpha,cmap='Purples')
        imaxes.append(ax3)
        ax3.set_title('warp/target')

        for ax in imaxes:
            ax.set_axis_off()
        self.last_figure = fig
        return fig

class FigBuilder_Subtract(baseFigBuilder):
    def __Build__(self, rootPath, sliceNum):
        super().__Build__(rootPath,sliceNum)
        from matplotlib.figure import Figure
        imaxes = []
        fig = Figure()
        fig.suptitle('{0} - Slice{1:04d}'.format(rootPath, sliceNum))

        ax1 = fig.add_subplot(131)
        ax1.imshow(getTextImage(rootPath, 'target', sliceNum),cmap='Greys_r')
        imaxes.append(ax1)
        ax1.set_title('target')

        ax2 = fig.add_subplot(132)
        ax2.imshow(getTextImage(rootPath, 'warp', sliceNum),cmap='Greys_r')
        imaxes.append(ax2)
        ax2.set_title('warp')

        ax3 = fig.add_subplot(133)
        ax3.imshow(np.subtract(getTextImage(rootPath, 'target', sliceNum), getTextImage(rootPath, 'warp', sliceNum)),cmap='Greys_r')
        imaxes.append(ax3)
        ax3.set_title('target-warp')

        for ax in imaxes:
            ax.set_axis_off()
        self.last_figure = fig
        return fig
