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
import numpy as np

def refreshLayers():
    for layer in iface.mapCanvas().layers():
        layer.triggerRepaint()
        
def gridInterval(request):
    intervals = [1, 2, 2.5, 4, 5]
    logIntervals = []
    for f in intervals:
        logIntervals.append(math.log10(f))
    
    logReq = math.log10(request)
    iremain = math.floor(logReq)
    remain = logReq - iremain
    
    for i in range(len(intervals) - 1, -1, -1):
        if logIntervals[i] < remain:
            res = 10.0 ** (float(iremain) + logIntervals[i])
            return res
        
def gridStart(start, interval):
        x0 = math.floor(start / interval) * interval
        if x0 < start:
            x0 = x0 + interval
        return x0

def groupExtent(group):
    tLayers = group.findLayers()
    extent = QgsRectangle()
    for tl in tLayers:
        if tl.parent().name() == 'Decorations':
            continue
        l = tl.layer()
        if l is not None:
            rect = l.extent()
            if rect is not None:
                extent.combineExtentWith(rect)
    return extent

def clearLayer(layer):
    with edit(layer):
        ids = [f.id() for f in layer.getFeatures()]
        for f in layer.getFeatures():
            layer.deleteFeatures(ids)                    
    
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
    
def readProjectDouble(entry, default):
    val, ok = QgsProject.instance().readDoubleEntry ("Geoscience", entry)
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

def writeProjectDataDouble(entry, val):
    QgsProject.instance().writeEntryDouble("Geoscience", entry, val)

def removeProjectEntry(entry):
    QgsProject.instance().removeEntry("Geoscience", entry)
    
# Calculate an interpolated 3D point at given depth from the supplied polyline.
# The polyline must have constant segment lengths given by segLength
def interpPolyline(depth, segLength, polyline):
    p = QgsPoint()
    findex = float(depth) / float(segLength)
    i0 = math.floor(findex)
    p0 = polyline[i0]

    # We need to check if this is the last segment because the last segment might not be segLength long
    if(len(polyline) > 2 and i0 == len(polyline) - 2):
        p1 = polyline[i0 + 1]
        dx = p1.x() - p0.x();
        dy = p1.y() - p0.y();
        dz = p1.z() - p0.z();
        segl = math.sqrt(dx * dx, dy * dy, dz * dz)
        ratio = segl / (depth - i0 * segLength)
    else:
        ratio = findex - float(i0)

    if ratio > 0.0:
        p1 = polyline[i0 + 1]
        p = QgsPoint(p0.x() + (p1.x() - p0.x()) * ratio, p0.y() + (p1.y() - p0.y()) * ratio, p0.z() + (p1.z() - p0.z()) * ratio)
    else:
        p = p0
    return p, findex

def coreVector(depth, segLength, polyline):
    findex = float(depth) / float(segLength)
    i0 = math.floor(findex)
    # ratio = findex - float(i0)

    # Check if we are at the end of hole. If so, we use the up vector of the last segment
    if i0 == len(polyline) - 1:
        i0 = i0 - 1
    p0 = polyline[i0]
    p1 = polyline[i0+1]

    # Calculate up hole vector
    v0 = np.array([p0.x(), p0.y(), p0.z()])
    v1 = np.array([p1.x(), p1.y(), p1.z()])
    v = v1 - v0

    v = v/np.linalg.norm(v)
   
    return v

# Process the url to provide a valid filename
def uriToFile(url):
    fileName = url
    if fileName.startswith("file:///"):
        if platform.system() == 'Windows':
            fileName = fileName[8:]
        elif platform.system() == 'Linux':
            fileName = fileName[7:]
        elif platform.system() == 'Darwin':
            fileName = fileName[6:] 
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
        if layer.type() == QgsMapLayer.VectorLayer and layer.name()[:2] != "S_" and layer.name() != "Section_Plan":
            if QgsWkbTypes.coordDimensions(layer.wkbType()) >= 3:
                listLayerZ.append(layer)
    
    for layer in listLayerZ:
        addLayerToListWidget(layer, listWidget)

def fillRasterLayersForSection(listWidget):
    listWidget.clear()
    
    listLayerZ = []
    layers = QgsProject.instance().mapLayers()
    for name, layer in layers.items():
        if layer.type() == QgsMapLayer.RasterLayer:
            if layer.bandCount() == 1:
                listLayerZ.append(layer)
    
    for layer in listLayerZ:
        addLayerToListWidget(layer, listWidget)
        
def getCheckedLayers(listWidget):
    layers = []
    for index in range(listWidget.count()):
        if listWidget.item(index).checkState():
            layers.append(listWidget.item(index).data(QtCore.Qt.UserRole))
    return layers

def layersExtent(layers):
    extent = QgsRectangle()
    for layer in layers:
        rect = layer.extent()
        if rect is not None:
            extent.combineExtentWith(rect)
    return extent