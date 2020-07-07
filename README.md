# QGIS Geoscience Plugin
## Now with drill sections!

*Author: Roland Hill - Please contribute and make this a better, more comprehensive geoscience tool.*

**Geoscience** provides useful tools to geoscientists. This includes drill hole processing, display of downhole data in plan. Version 1.0 also brings creation and display of drill sections with downhole data and elevation layers. Other utilities help with raster and vector manipulation.

See https://www.spatialintegration.com/geoscience-plugin-for-qgis/ for detailed instructions.

## Drill Tools 

Tools to display drill holes, down hole data and sections in QGIS. This includes de-surveying the holes using collar azimuth and dip or a survey table if available. Prior to using Drill Tools you need to open the collar, survey (optional) and down hole data (optional) tables in QGIS. You can use any local format supported by QGIS including shapefiles, MapInfo Tab files or CSV files. To open data using CSV, use the existing Delimited Text tool 

**Drill Tools will only work with projected coordinate systems (ie not latitude and longitude)**

## Vector Tools

![https://rolandhill.github.io/geoscience/icon/ReverseLine.png](https://rolandhill.github.io/geoscience/icon/ReverseLine.png)

Reverses the order of all the nodes in the selected line features, in effect reversing the direction of the line. This is necessary when using asymmetric line styles such as reverse and normal fault symbols. Note that the layer must be editable before using the tool.

## Raster Tools

![https://rolandhill.github.io/geoscience/icon/WhiteTransparent.png](https://rolandhill.github.io/geoscience/icon/WhiteTransparent.png)

Sets the transparent colour to **white** for all the raster images selected in the project tree. To use, first select all the rasters you wish to process using control and shift left clicks, then choose this menu entry or
toolbar button. Ideal for image sets such as EM channels or hyperspectral images.

![https://rolandhill.github.io/geoscience/icon/BlackTransparent.png](https://rolandhill.github.io/geoscience/icon/BlackTransparent.png)

Sets the transparent colour to **black** for all the raster images selected in the project tree. To use, first select all the rasters you wish to process using control and shift left clicks, then choose this menu entry or toolbar button. Ideal for image sets such as EM channels or hyperspectral images.

## Local Grid
Calcualtes the WKT representation of a local grid from 2 or more coordinates known in both the local and recognised base projected coordinate system (eg WGS84 UTM55S, GDA94 MGA55 etc). If you have 3 or more points then the local grid definition will be 3 dimensional (make sure there is separation in Z value a well). If the coordinate pairs have error in them then a best fit will be used. The generated local grid CRS must then be manually pasted into a Custom CRS definition. A local CRS can be re-projected on the fly, converted etc like any other CRS.

## What's Next?
* Pack all layers for a section into a single geopackage
* Better bad data handling & reporting
* Downhole graphs
* Easy dip symbol display
* Export section in real-world 3D coordinates

* Released under GPL license.
