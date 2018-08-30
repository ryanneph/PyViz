#!/usr/bin/env python

from distutils.core import setup

import pyviz.version

setup(name="PyViz",
      version=pyviz.version.get_version(),
      description="Simple and flexible raw data viewer (2d & 3d image data)",
      author="Ryan Neph",
      author_email="neph320@gmail.com",
      url="https://github.com/ryanneph/PyViz",
      packages=['pyviz',],
      entry_points={
          'gui_scripts': ['pyviz = pyviz.gui:start_gui'],
      },
      package_data={'pyviz': ['window.ui']},
      install_requires=[
          'matplotlib',
          'scipy',
          'h5py',
          'pyqt5',
          'numpy',
          'pydicom',
          'dicom-numpy',
          ],
      )
