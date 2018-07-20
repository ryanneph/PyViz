# PyViz - Data Visualization

PyViz grew out of a necessity to be able to easily view volumetric image data common to CT/MRI scans in the medical field. This project is implemented in python using matplotlib for image rendering. It is a simple slice-by-slice viewer that supports re-orienting the view into the 3 orthogonal cartesian planes, referred to as axial, coronal, and sagittal by the medical community.

This project currently supports the following types of data:
* raw/bin - linear packing of float/double data, assumed to be in C-major ordering (z-index: slowest, x-index: fastest)
* dicom - either as a single dicom slice (.dcm file) or as a directory containing all slices in a series.

The functionality can be easily extended for other proprietary formats as well.

## Demo
![demo](images/pyviz_demo.gif)

## Installing
Open a terminal window and enter:
``` bash
pip install --process-dependency-links git+git://github.com/ryanneph/PyViz.git#egg=PyViz
```

## Development
Open a terminal window and enter:
``` bash
git clone https://github.com/ryanneph/PyViz.git
cd PyViz
pip install -e --process-dependency-links .
```

## Running
Open a terminal window and enter:
``` bash
pyviz
```
* Select a directory which will be recursively searched for `.bin`/`.raw`/`.dcm` files
* For dicom files, simply select from the list and the array size will be automatically detected
* For raw/bin files, first enter the X, Y, Z array sizes into the text fields below the list, then select the file


---------
Please open an issue describing a problem or contact Ryan Neph at neph320@gmail.com to get involved.
