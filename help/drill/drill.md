# Processing Drill Holes

Geoscience includes tools to display drill holes, downhole data and [sections](help://drill/sections.md) in QGIS. Holes are desurveyed using the collar azimuth and dip, survey data, or both.

Before using the drill tools, open the collar table in QGIS, plus any survey and downhole data tables you have. You can use any format supported by QGIS, including shapefiles, MapInfo Tab files or CSV files. To open CSV files, use the existing Delimited Text tool ![Delimited Text](help://drill/image/csv.png).

> [!NOTE]
> Geoscience doesn't support database layers. If your data is in a database, first export your layers as GeoPackage, Shapefile, CSV etc.

> [!IMPORTANT]
> The drill tools only work with projected coordinate systems (e.g. UTM), not latitude and longitude.

Geoscience names the layers it creates after your original layers, so give your files short, simple names (e.g. `Collar.shp`, `Assay.csv`). Don't rename the layers and files that Geoscience creates, or it may not be able to find them again.

> [!TIP]
> There are collar, survey and assay CSV files, plus a raster DEM, in the `testdata` directory under the plugin installation directory, if you just want to try out the drill hole tools.

The steps below display the drill traces in plan. You need to follow them before you can create sections.

## Load Data

![Delimited Text import of a collar file](help://drill/image/csv_importer.png)

1. Open the **Collar** layer. If using the Delimited Text tool in QGIS, select **Point Coordinates**, choose the **Easting** and **Northing** columns, then set the Coordinate Reference System. Leave the Z and M fields empty, because Geoscience expects a 2D layer.
2. (Optional) Open the **Survey** layer. If using the Delimited Text tool in QGIS, select **No Geometry** to just import the data columns.
3. (Optional) Open the **Downhole data** layers. You can use multiple layers (e.g. lithology and assay). If you are using the Delimited Text tool in QGIS, select **No Geometry** to just import the data columns.

## Desurvey Holes

1. Choose **Geoscience > Drilling > Desurvey Holes...** or click the ![Desurvey](help://../icon/Desurvey.png) button on the toolbar.
2. Select the **Collar Layer** and its fields, then the **Survey Layer** and its fields if you have one. Geoscience fills in the fields for you if they have sensible names.
3. Leave **Down dip is negative** checked if downward dips are negative (e.g. -60 for a hole dipping 60° down). Uncheck it if downward dips are positive.
4. Enter the **Desurvey length**. Each hole is rebuilt from straight line segments of this length.
5. Click **OK**. A new layer named `CollarLayerName_Desurvey` is created and loaded in QGIS, showing the drill traces in plan.

![Desurvey Hole dialog](help://drill/image/DesurveyDlg.png)

Want to know more about [desurveying drill holes](help://drill/desurvey.md)?

## Process Downhole Data

![Downhole Data dialog](help://drill/image/DownholeDlg-1.png)

1. Choose **Geoscience > Drilling > Downhole Data...** or click the ![Downhole Data](help://../icon/DrillPlan.png) button on the toolbar.
2. Select the **Desurveyed Hole Layer**. You can have several sets of drill holes loaded at once, so make sure you pick the right one.
3. Choose the downhole data **Layer** and its **HoleID**, **From/Depth** and **To** fields. Geoscience fills in the fields for you if they have sensible names.
4. Enter a short **Filename suffix** that describes the data (e.g. `Lith`, `Assay`, `MagSusc`).
5. Check the attribute fields to include in the new layer. You will use these to style the drill traces, so include everything you need.
6. Click **OK**. A new layer named `CollarLayerName_Downhole_Suffix` is created and loaded into QGIS. It contains one line for each From-To interval in the data layer.
7. Style the new layer to display the attributes the way you want.

![Downhole data displayed in plan](help://drill/image/DrillTrace.png)

To mark depths along the holes, see [Downhole Points](help://drill/points.md). You are now ready to [create sections](help://drill/sections.md).
