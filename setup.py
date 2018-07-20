#!/usr/bin/env python

from distutils.core import setup

setup(name="PyViz",
      version='1.0',
      description="Simple and flexible raw data viewer (2d & 3d image data)",
      author="Ryan Neph",
      author_email="neph320@gmail.com",
      url="https://github.com/ryanneph/PyViz",
      packages=['pyviz',],
      entry_points={
          'gui_scripts': ['pyviz = pyviz.__main__:main'],
      },
      package_data={'pyviz': ['pyviz/window.ui']},
      install_requires=[
          'matplotlib>=0.1',
          'scipy >=1.0.1',
          'h5py >=2.7.1',
          'pyqt5 >=5.9.2',
          'numpy >=1.14.2',
          ],
      dependency_links=[
          'git+git://github.com/ryanneph/Sparse2Dense.git#egg=sparse2dense',
          'git+git://github.com/ryanneph/PyMedImage.git#egg=pymedimage',
      ]
      )
