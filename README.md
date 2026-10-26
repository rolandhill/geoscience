# Geoscience for QGIS

*Author: Roland Hill*

**Geoscience** is a free plugin that adds drill hole and other geoscience tools to QGIS. With it you can:

- Desurvey drill holes from collar and survey data
- Display downhole data, depth ticks and structural measurements in plan
- Create and manage drill sections with downhole data and elevation rasters
- Convert oriented core alpha and beta angles to dip and dip direction
- Create local grid coordinate systems
- Stream your live QGIS map into [Spatial Integration](https://spatialintegration.com/) in 3D
- Make white or black transparent on raster images

All commands are on the **Geoscience** menu and toolbar. Choose **Geoscience > Help** for full instructions, or see https://spatialintegration.com/help/geoscience/.

Version 2 requires QGIS 4. Older versions of the plugin work with QGIS 3.

## Drill Tools

The drill tools desurvey holes using the collar azimuth and dip, survey data, or both, then display the holes, downhole data and sections in QGIS. Before using them, open your collar table in QGIS, plus any survey and downhole data tables you have. You can use any file format QGIS supports, including GeoPackage, shapefiles, MapInfo TAB and CSV. Open CSV files with the QGIS Delimited Text tool.

**The drill tools only work with projected coordinate systems (e.g. UTM), not latitude and longitude.**

![Desurvey](https://rolandhill.github.io/geoscience/icon/Desurvey.png) **Desurvey Holes** builds a 3D trace of each hole from its collar and survey data.

![Downhole Data](https://rolandhill.github.io/geoscience/icon/DrillPlan.png) **Downhole Data** turns From-To interval data, such as assays and lithology, into 3D lines along the drill traces, ready to style.

![Downhole Points](https://rolandhill.github.io/geoscience/icon/DrillPoints.png) **Downhole Points** places points at regular depths down each hole, for depth ticks and labels.

![Downhole Structure](https://rolandhill.github.io/geoscience/icon/DrillStructure.png) **Downhole Structure** converts alpha and beta angles into dip and dip direction and draws each measurement as an oriented 3D plane. On sections, Geoscience also calculates the apparent dip.

![Section Manager](https://rolandhill.github.io/geoscience/icon/DrillSection.png) **Section Manager** creates, displays, recreates and deletes drill sections. Draw a section line on the map, or enter a west-east or south-north line. Sections are saved with your QGIS project and include grids and an elevation profile from any raster you choose.

There are collar, survey, assay and structure CSV files and a DEM in the `testdata` directory of the plugin, if you want to try the drill tools.

## Spatial Integration Link

The Spatial Integration Link serves your live QGIS map to [Spatial Integration](https://spatialintegration.com/), which drapes it over a surface in 3D. Whatever the QGIS map canvas shows appears in Spatial Integration and updates as you change it. The link runs only on your own computer (`127.0.0.1`), so nothing is shared with your network. Start it from **Geoscience > Spatial Integration Link > Start Link**.

## Local Grids

![Local Grid](https://rolandhill.github.io/geoscience/icon/LocalGrid.png) **Create Local CRS** calculates a WKT definition of a local grid from two or more points with known coordinates in both the local grid and a projected base CRS (e.g. WGS 84 / UTM 55S, GDA94 / MGA 55). With three or more points the definition is three dimensional, so make sure the points have a spread of Z values as well. If the coordinates contain errors, a best fit is used. Paste the result into a custom CRS in QGIS, then use it like any other CRS: reproject on the fly, convert data and so on.

## Raster Tools

![Transparent White](https://rolandhill.github.io/geoscience/icon/WhiteTransparent.png) **Transparent White** and ![Transparent Black](https://rolandhill.github.io/geoscience/icon/BlackTransparent.png) **Transparent Black** set the transparent colour to white or black for every raster selected in the Layers panel. They are ideal for sets of images such as EM channels or hyperspectral bands.

## Contributing

Ideas, bug reports and contributions are welcome. Please use the [issue tracker](https://github.com/rolandhill/geoscience/issues).

Released under the GPL licence.
