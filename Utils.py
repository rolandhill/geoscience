# -*- coding: utf-8 -*-
"""
Created on Tue Apr  2 17:37:07 2019

@author: HillR
"""
from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from PyQt5 import QtWidgets

import os.path
import math
import platform

def getLayerByName(name):
    layer=None
    layerList = QgsProject.instance().mapLayersByName(name)
    if len(layerList) > 0:
        layer = layerList[0]

    return layer

def getFieldByName(layer, name):
    field = QgsField()
    if layer is not None and layer.isValid() and name != "None":
        dp = layer.dataProvider()
        index = dp.fieldNameIndex(name)
        if index > -1:
            field = dp.field(index)
    return field

# Retrieve the name of the layer from the QGIS project file with the supplied entry label
def readProjectLayer(entry):
    name, ok = QgsProject.instance().readEntry ("Geoscience", entry)
    if ok and name != "None":
        layer = getLayerByName(name)
        if layer != None:
            return layer
        else:
            return None
    else:
        return None

# Write the supplied layer name into the QGIS project file next to the supplied entry label
def writeProjectLayer(entry, layer):
    if layer is not None:
        try:
            QgsProject.instance().writeEntry("Geoscience", entry, layer.name())
        except:
            QgsProject.instance().writeEntry("Geoscience", entry, "None")
    else:
        QgsProject.instance().writeEntry("Geoscience", entry, "None")
        
# Retrieve the name of the field from the QGIS project file with the supplied entry label
def readProjectField(entry):
    name, ok = QgsProject.instance().readEntry ("Geoscience", entry)
    return name

# Write the supplied field name into the QGIS project file next to the supplied entry label
def writeProjectField(entry, field):
    QgsProject.instance().writeEntry("Geoscience", entry, field)
        
# Retrieve a string from the QGIS project file with the supplied entry label
def readProjectText(entry, default):
    val, ok = QgsProject.instance().readEntry("Geoscience", entry)
    if ok:
        return val
    else:
        return default
    
# Retrieve a number from the QGIS project file with the supplied entry label
def readProjectNum(entry, default):
    val, ok = QgsProject.instance().readNumEntry ("Geoscience", entry)
    if ok:
        return val
    else:
        return default
    
# Retrieve a bool from the QGIS project file with the supplied entry label
def readProjectBool(entry, default):
    val, ok = QgsProject.instance().readBoolEntry ("Geoscience", entry)
    if ok:
        return val
    else:
        return default

# Write the supplied value (number or bool) into the QGIS project file next to the supplied entry label
def writeProjectData(entry, val):
    QgsProject.instance().writeEntry("Geoscience", entry, val)

def removeProjectEntry(entry):
    QgsProject.instance().removeEntry("Geoscience", entry)
    
# Calculate an interpolated 3D point at given depth from the supplied polyline.
# The polyline must have constant segment lengths given by segLength
def interpPolyline(depth, segLength, polyline):
    p = QgsPoint()
    i = depth / segLength
    i0 = int(i)
    ratio = i - i0

    p0 = polyline[i0]
    if ratio > 0.0:
        p1 = polyline[i0 + 1]
        dp = (p1 - p0) * ratio
        p = p0 + dp
    else:
        p = p0
    return p, i

# Process the url to provide a valid filename
def uriToFile(url):
    fileName = url
    if fileName.startswith("file:///"):
        if platform.system() == 'Windows':
            fileName = fileName[8:]
        elif platform.system() == 'Linux':
            fileName = fileName[7:]
    fileName = fileName.replace("%20", " ")
    fileName = os.path.normpath(fileName)
    return fileName
    
def addLayerToListWidget(layer, listWidget):
    item = QtWidgets.QListWidgetItem()
    item.setText(layer.name())
    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
    item.setCheckState(QtCore.Qt.Checked)
    item.setData(QtCore.Qt.UserRole, layer)
    listWidget.addItem(item)
        
def fillVectorLayersForSection(listWidget):
    listWidget.clear()
    
    listLayerZ = []
    layers = QgsProject.instance().mapLayers()
    for name, layer in layers.items():
        if layer.type() == QgsMapLayer.VectorLayer and layer.name()[:2] != "S_":
            if QgsWkbTypes.coordDimensions(layer.wkbType()) >= 3:
                listLayerZ.append(layer)
    
    for layer in listLayerZ:
        addLayerToListWidget(layer, listWidget)
    