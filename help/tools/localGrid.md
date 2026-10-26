# Local Grids

Geoscience for QGIS can create local grid definitions.

Once you have your local grid CRS (Coordinate Reference System) you can assign it to your vector or raster data, overlay local data on data in a standard CRS, reproject into a standard CRS or even use the map canvas in your local CRS. In fact, you can do anything that you normally do with one of the thousands of CRS already defined in QGIS.

You need two or more points with known coordinates in both your local grid and a standard grid. Geoscience then calculates the affine parameters and constructs a Well Known Text (WKT) definition for your grid, which can be added to QGIS as a custom CRS. With three or more points the local grid definition is three dimensional, so make sure there is separation in the Z values as well. If the coordinate pairs contain errors, a best fit is used.

## Creating a Local CRS

Choose **Geoscience > Create Local CRS...**, enter the name of your local grid and select the base CRS. The base CRS has to be projected, not geographic. That usually means it has eastings and northings rather than latitude and longitude. Then enter your coordinates in both the base and local grids.

![Local Grid dialog](help://tools/image/LocalGrid.png)

Once you have filled in the name, base CRS and coordinate pairs, click **Calculate**. The new local CRS in WKT format appears in the box. Click **Copy** to copy it to the clipboard (paste it into a text file for safe keeping before you close!) and click **Close**.

Go to **Settings > Custom Projections**, click the green add button, then type in your local CRS name. Check that the Format is set to WKT, then paste your new definition into the box. Click **Validate** to make sure it's formatted correctly, then **OK**.

> [!IMPORTANT]
> Check some of your known points to make sure that your new CRS is working properly **before** using it in production! It has been tested with the local grids at hand, but they are a small sample.

You can now use your custom CRS just like any of the other CRS already defined in QGIS.

## Acknowledgements

Thanks to Gabriel De Luca for posting instructions on how to create affine CRS and for the affine source code: [https://github.com/gabriel-de-luca/simil](https://github.com/gabriel-de-luca/simil)
