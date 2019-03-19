# QGIS Geoscience Plugin

*Author: Roland Hill, Your name here! - Please contribute and make this a better, more comprehensive geoscience tool.*

**Geoscience** has the following tools available from the Geoscience menu or
accessible from the Geoscience toolbar.

![https://rolandhill.github.io/geoscience/icon/DrillSection.png](https://rolandhill.github.io/geoscience/icon/DrillSection.png) - Drill Hole Display: **Desurvey holes, project drill hole traces to
    surface and create surface projects of down hole data.

![https://rolandhill.github.io/geoscience/icon/ReverseLine.png](https://rolandhill.github.io/geoscience/icon/ReverseLine.png) - Reverse Line Direction: **Reverse the direction of lines. This is needed
    when using non-symmetric line symbology (eg normal faults).

![https://rolandhill.github.io/geoscience/icon/BlackTransparent.png](https://rolandhill.github.io/geoscience/icon/BlackTransparent.png) - Transparent Rasters: **Transparent black or white pixels for all selected
    images (great for EM channels, remote sensing channels etc).

# Table of Contents
  * [Drill Tools](#Drill_Tools)
  * [Vector Tools](#Vector_Tools)
  * [Raster Tools](#Raster_Tools)
  * [What's Next](#What_Next)

## Drill Tools <a name="Drill_Tools"></a> 

![https://rolandhill.github.io/geoscience/icon/DrillSection.png](https://rolandhill.github.io/geoscience/icon/DrillSection.png)

Tools to display drill holes and down hole data in QGIS. This includes de-surveying the holes using collar azimuth and dip or a survey table if
available. Prior to using Drill Tools you need to open the collar, survey (optional) and down hole data (optional) tables in QGIS. You can use any format
supported by QGIS including shapefiles, MapInfo Tab files or CSV files. To open data using CSV, use the existing Delimited Text tool 

![https://rolandhill.github.io/geoscience/doc/csv.png](https://rolandhill.github.io/geoscience/doc/csv.png)

**Drill Tools will only work with projected coordinate systems (ie not latitude and longitude)**

The workflow to display the surface projection of drill traces is:

1.  Open the **Collar** layer. If using the Delimited Text tool in QGIS,
    select **Point Geometry** and the appropriate columns for Easting and
    Northing, followed by the Coordinate Reference System.

2.  (Optional) Open the **Survey** layer. If using the Delimited Text tool in
    QGIS, select **No Geometry** to just import the data columns.

3.  (Optional) Open the **Down hole data** layers. You can use multiple layers
    (eg. lithology and assay) and if you are using the Delimited Text tool in
    QGIS, select **No Geometry** to just import the data columns.

4.  Choose *Geoscience -\> Drilling -\> Drill Setup*. Fill in the dialog with
    the Collar and Survey (if available) layers, then choose the appropriate
    attribute fields. All will be guessed by Geoscience if sensible names have
    been used.

5.  Choose the **Desurvey Length**. Drill holes will be reconstructed using
    straight line segments of this length.

6.  Choose *Geoscience -\> Drilling -\> Desurvey Data*. A new layer is created
    and loaded in QGIS. You can now see the surface projection of drill holes.

7.  Choose *Geoscience -\> Drilling -\> Display Traces*. Choose the source
    Downhole Data layer and the appropriate attribute fields. Again, these are
    chosen automatically if sensible names are used. Check all the attribute
    fields that you want to include in the downhole data layer to be
    created. **You also need to provide a brief descriptive name** to be
    appended to the layer name.

8.  The downhole trace layer is created and loaded into QGIS with each row
    containing one line segment for each interval from the source. You then need
    to Symbolise the new layer to display the attributes as you desire.

## Vector Tools <a name="Vector_Tools"></a>

![https://rolandhill.github.io/geoscience/icon/ReverseLine.png](https://rolandhill.github.io/geoscience/icon/ReverseLine.png)

Reverses the order of all the nodes in the selected line features, in effect reversing the direction of the line. This is necessary when using asymmetric line styles such as reverse and normal fault symbols. Note that the layer must be editable before using the tool.

## Raster Tools <a name="Raster_Tools"></a>

![https://rolandhill.github.io/geoscience/icon/WhiteTransparent.png](https://rolandhill.github.io/geoscience/icon/WhiteTransparent.png)

Sets the transparent colour to **white** for all the raster images selected in the project tree. To use, first select all the rasters you wish to process using control and shift left clicks, then choose this menu entry or
toolbar button. Ideal for image sets such as EM channels or hyperspectral images.

![https://rolandhill.github.io/geoscience/icon/BlackTransparent.png](https://rolandhill.github.io/geoscience/icon/BlackTransparent.png)

Sets the transparent colour to **black** for all the raster images selected in the project tree. To use, first select all the rasters you wish to process using control and shift left clicks, then choose this menu entry or toolbar button. Ideal for image sets such as EM channels or hyperspectral images.

## What's Next?  <a name="What_Next"></a>

-   Better bad data handling & reporting

-   Drill sections

-   Downhole graphs

-   Downhole labels

-   Easy dip symbol display

Released under GPL license.
