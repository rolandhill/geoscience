# -*- coding: utf-8 -*-
"""
Created on Tue May 21 17:16:49 2019

@author: HillR
"""

from PyQt5.QtCore import QVariant
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsMessageBar
from qgis.core import Qgis, QgsWkbTypes, QgsProject

from PyQt5 import QtCore, Qt, QtGui

from .Utils import *
from .SectionManager import *


# The DrillManager class controls all drill related data and methods 
class SectionGrid:
    def __init__(self, section, crs):
        self.section = section
        self.crs = crs
        
    def create(self):
        layers = []
        
        # These are real world coordinates
        dx = self.section.maxX - self.section.minX
        dy = self.section.maxY - self.section.minY

        # Approximate number of grid lines to display
        numGridLines = 3.0
        
        # This is section2D cooridnates
        extent = groupExtent(self.section.group)
        extent.grow(10)

        # Build the X grid
        name = self.createSectionGridLayerName(self.section.name) + 'X'
        layer = self.section.matchDecorationLayer(name)
        usingNewLayer = False
        if layer == None:
            layer = self.createSectionGridLayer(name, self.crs)
            usingNewLayer = True
        else:
            clearLayer(layer)
            
        intx = 0    
        if dx != 0:
            intx = gridInterval(dx / numGridLines)
            x = gridStart(self.section.minX, intx)
#            msg = "dx: %f    intx: %f" % (dx, intx)
#            iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
            while x < self.section.maxX:
                y = ((x - self.section.startX)/(self.section.endX - self.section.startX)) * (self.section.endY - self.section.startY) + self.section.startY
                pt = np.array([x - self.section.startX, y - self.section.startY, 0.0])
                rpt = self.section.quat.rotate(pt)
                pointList = []
                pointList.append(QgsPoint(rpt[0], extent.yMaximum(), 0.0))
                pointList.append(QgsPoint(rpt[0], extent.yMinimum(), 0.0))
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPolyline(pointList))
                
                # Set the attributes for the new feature
                f.setAttributes([x])
        
                # Add the new feature to the new Trace_ layer
                layer.startEditing()
                layer.addFeature(f)
                layer.commitChanges()
                
                x = x + intx

        layers.append(layer)
            
        if usingNewLayer:
            self.setStyle(layer, 'E')
            QgsProject.instance().addMapLayer(layer, False)
            self.section.decorationGroup().addLayer(layer)
            if dx < dy*0.25:
                QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked( False )
                

        # Build the Y grid
        name = self.createSectionGridLayerName(self.section.name) + 'Y'
        layer = self.section.matchDecorationLayer(name)
        usingNewLayer = False
        if layer == None:
            layer = self.createSectionGridLayer(name, self.crs)
            usingNewLayer = True
        else:
            clearLayer(layer)

        inty = 0    
        if dy != 0:
            inty = gridInterval(dy / numGridLines)
            y = gridStart(self.section.minY, inty)
            while y < self.section.maxY:
                x = ((y - self.section.startY)/(self.section.endY - self.section.startY)) * (self.section.endX - self.section.startX) + self.section.startX
                pt = np.array([x - self.section.startX, y - self.section.startY, 0.0])
                rpt = self.section.quat.rotate(pt)
                pointList = []
                pointList.append(QgsPoint(rpt[0], extent.yMaximum(), 0.0))
                pointList.append(QgsPoint(rpt[0], extent.yMinimum(), 0.0))
                f = QgsFeature()
                f.setGeometry(QgsGeometry.fromPolyline(pointList))
                
                # Set the attributes for the new feature
                f.setAttributes([y])
        
                # Add the new feature to the new Trace_ layer
                layer.startEditing()
                layer.addFeature(f)
                layer.commitChanges()
                
                y = y + inty
        
        layers.append(layer)
            
        if usingNewLayer:
            self.setStyle(layer, 'N')
            QgsProject.instance().addMapLayer(layer, False)
            self.section.decorationGroup().addLayer(layer)
            if dy < dx*0.25:
                QgsProject.instance().layerTreeRoot().findLayer(layer.id()).setItemVisibilityChecked( False )

        # Build the Z grid
        name = self.createSectionGridLayerName(self.section.name) + 'Z'
        layer = self.section.matchDecorationLayer(name)
        usingNewLayer = False
        if layer == None:
            layer = self.createSectionGridLayer(name, self.crs)
            usingNewLayer = True
        else:
            clearLayer(layer)
            
        intz = max(intx, inty)
        z = gridStart(extent.yMinimum(), intz)
        while z < extent.yMaximum():
            pointList = []
            pointList.append(QgsPoint(extent.xMinimum(), z, 0.0))
            pointList.append(QgsPoint(extent.xMaximum(), z, 0.0))
            f = QgsFeature()
            f.setGeometry(QgsGeometry.fromPolyline(pointList))
            
            # Set the attributes for the new feature
            f.setAttributes([z])
    
            # Add the new feature to the new Trace_ layer
            layer.startEditing()
            layer.addFeature(f)
            layer.commitChanges()
            
            z = z + intz
        
        layers.append(layer)
            
        if usingNewLayer:
            self.setStyle(layer, 'RL')
            QgsProject.instance().addMapLayer(layer, False)
            self.section.decorationGroup().addLayer(layer)

        # Build the Border
        name = self.createSectionGridLayerName(self.section.name) + 'Border'
        layer = self.section.matchDecorationLayer(name)
        usingNewLayer = False
        if layer == None:
            layer = self.createSectionGridLayer(name, self.crs)
            usingNewLayer = True
        else:
            clearLayer(layer)

        pointList = []
        pointList.append(QgsPoint(extent.xMinimum(), extent.yMinimum(), 0.0))
        pointList.append(QgsPoint(extent.xMinimum(), extent.yMaximum(), 0.0))
        pointList.append(QgsPoint(extent.xMaximum(), extent.yMaximum(), 0.0))
        pointList.append(QgsPoint(extent.xMaximum(), extent.yMinimum(), 0.0))
        pointList.append(QgsPoint(extent.xMinimum(), extent.yMinimum(), 0.0))
        f = QgsFeature()
        f.setGeometry(QgsGeometry.fromPolyline(pointList))
        
        # Set the attributes for the new feature
        f.setAttributes([0.0])

        # Add the new feature to the new Trace_ layer
        layer.startEditing()
        layer.addFeature(f)
        layer.commitChanges()

        layers.append(layer)

        if usingNewLayer:
            self.setStyle(layer, labels=False)
            QgsProject.instance().addMapLayer(layer, False)
            self.section.decorationGroup().addLayer(layer)



        return layers
        
        
    def setStyle(self, layer, labelSuffix='', labels=True):
        # Set the line style
        r = layer.renderer()
        r.symbol().setColor(QtGui.QColor('grey'))
        r.symbol().setOpacity(0.5)

        #Set the label style
        if labels:
            settings = QgsPalLayerSettings()
            textFormat = QgsTextFormat()
            textFormat.setFont(QtGui.QFont("Arial", 10))
            textFormat.setColor(QtGui.QColor('grey'))
            textFormat.setOpacity(0.5)
            settings.setFormat(textFormat)
            if labelSuffix == '':
                settings.fieldName = 'Label'
            else:
    #            settings.fieldName = 'Label'
                settings.fieldName = str.format("format( '%%1%%2',  format_number(Label, 0), ' %s')" % labelSuffix)
                settings.isExpression = True
            settings.formatNumbers = True
            settings.decimals = 0
            settings.placement = QgsPalLayerSettings.Line
            labeling = QgsVectorLayerSimpleLabeling(settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)        
        
    def createSectionGridLayerName(self, sectionName):
        name = "S_" + sectionName + "_Grid"
        return name
    
        

    def createSectionGridLayer(self, name, crs):
        #Create a new memory layer
        layer = QgsVectorLayer("LineStringZ?crs=EPSG:4326", name, "memory")
        layer.setCrs(crs)
        atts = []
        # Loop through the list of desired field names that the user checked
        atts.append(QgsField("Label",  QVariant.Double, "double", 9, 3))
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 

        return layer

        
        