# Processing Drill Holes

The Geoscience plugin includes tools to display drill holes, downhole data and [sections](help://drill/sections.md) in QGIS. This includes desurveying the holes using collar azimuth and dip and/or survey data.

Prior to using the drill tools you need to open the collar, survey (optional) and downhole data (optional) tables in QGIS. You can use any format supported by QGIS, including shapefiles, MapInfo Tab files or CSV files. To open CSV files, use the existing Delimited Text tool ![Delimited Text](help://drill/image/csv.png).

> [!NOTE]
> Geoscience doesn't support database layers. If your data is in a database, first export your layers as GeoPackage, Shapefile, CSV etc.

> [!IMPORTANT]
> The drill tools only work with projected coordinate systems (ie not latitude and longitude).

Geoscience will create new layers with names based on the original file names. It's suggested to give your original files short, simple names (eg. `Collar.shp`, `Assay.csv`). Once Geoscience has created a file name you shouldn't change it, because Geoscience might not be able to identify the file again.

> [!TIP]
> There are collar, survey and assay CSV files, plus a raster DEM, in the `testdata` directory under the plugin installation directory, in case you just want to try the drill hole functions.

The workflow to display the surface projection of drill traces follows. You will also need to do this if you want to display sections.

## Load Data

![Delimited Text import of a collar file](help://drill/image/csv_importer.png)

1. Open the **Collar** layer. If using the Delimited Text tool in QGIS, select **Point Geometry** and the appropriate columns for **Easting** and **Northing**, followed by the Coordinate Reference System. Do not put anything in the Z or M fields, because Geoscience expects this to be a 2D layer.
2. (Optional) Open the **Survey** layer. If using the Delimited Text tool in QGIS, select **No Geometry** to just import the data columns.
3. (Optional) Open the **Downhole data** layers. You can use multiple layers (eg. lithology and assay). If you are using the Delimited Text tool in QGIS, select **No Geometry** to just import the data columns.

## Desurvey Holes

1. Choose **Geoscience > Drilling > Desurvey Holes...** or click the ![Desurvey](help://../icon/Desurvey.png) button on the toolbar.
2. Select the appropriate fields. All fields are guessed by Geoscience if sensible names have been used.
3. Choose the **Desurvey Length**. Drill holes are reconstructed using straight line segments of this length.
4. Click **OK**. A new layer is created and loaded in QGIS, and you can now see the surface projection of the drill holes.

Want to know more about [desurveying drill holes](help://drill/desurvey.md)?

## Process Downhole Data

![Downhole Data dialog](help://drill/image/DownholeDlg-1.png)

Choose **Geoscience > Drilling > Downhole Data...** or click the ![Downhole Data](help://../icon/DrillPlan.png) button on the toolbar.

1. Select the desurveyed hole layer. You can have multiple sets of drill hole data loaded at once, or you might want to use a desurveyed layer in a different QGIS project.
2. Choose the source downhole data layer and the appropriate attribute fields for **HoleID**, **From** and **To**. These are chosen automatically if sensible names are used.
3. Check all the attribute fields that you want to include in the downhole data layer to be created. You will use these for symbology on the line segments, so be sure to include any attributes that you will need.
4. **Provide a brief descriptive name** to be appended to the layer name. A default is provided, but this will depend on how your layers are named.
5. The downhole data layer is created with the name `CollarLayerName_Downhole_Name`, using the name from the step above, then loaded into QGIS. It contains one polyline for each From-To interval in the source layer.
6. Symbolise the new layer to display the attributes as you desire.

![Downhole data displayed in plan](help://drill/image/DrillTrace.png)

You are now ready to [create sections](help://drill/sections.md).
