# Structural Measurements

You can use the Geoscience plugin to convert alpha and beta angles into dip and dip direction, then use those values in sections and maps.

Choose **Geoscience > Drilling > Downhole Structure...** and define your **HoleID**, **Depth**, **Alpha** and **Beta** fields. These are combined with your previously [desurveyed holes](help://drill/drill.md) to produce a new layer with dip and dip direction (fields named `_Dip` and `_DipDir`), a 3D coordinate and a 3D polygon representing the oriented plane. These can be used to generate [sections](help://drill/sections.md).

![Structure polygons on a section](help://drill/image/Section_StructurePolygons.png)

Rotations are performed assuming that beta angles are measured clockwise looking down the hole, from the orientation line on the bottom of the core around to the longest part of the ellipse down the hole. Angles should be in degrees.

For those interested, all rotations are performed on the structural plane normal using quaternions. The only trigonometric functions used are right at the end, to convert the final plane normal back into dip and dip direction.

## Apparent Dip on Sections

If you use the new structural layer in a drill section, Geoscience detects the `_Dip` and `_DipDir` fields, combines them with the orientation of the section line and generates a new field named `_Section_Dip`, which contains the apparent dip of the structure. This only appears in the structure layers within the section groups. You can apply a style to the apparent dip to display an appropriately dipping line. Try the [RH_section_apparent_dip](help://drill/image/RH_section_apparent_dip.qml) style file.

> [!TIP]
> If you already have dip and dip direction calculated, rename the fields `_Dip` and `_DipDir` to have Geoscience use them when making a section.

![Apparent dip symbols on a section](help://drill/image/Section_ApparentDip.png)
