# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:41:08 2019

@author: HillR
"""

from PyQt5.QtWidgets import QProgressDialog, qApp

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
import numpy as np
import math

from .quaternion import Quaternion
from .SectionWindow import *
from .Utils import *

class layerMap:
    original = QgsVectorLayer()
    section = QgsVectorLayer()
    
def verticalPlane(startx, starty, endx, endy):
    p1 = np.array([startx, starty, 0.0])
    p2 = np.array([endx, endy, 0.0])
    p3 = np.array([startx, starty, -100])
    
    v1 = p2 - p1
    v2 = p3 - p1
    
    cp = np.cross(v1, v2)
    cp = cp/np.linalg.norm(cp)
    a, b, c = cp
    
    d = -np.dot(cp, p3)
    
    return np.array([a, b, c, d])

def qgsToNp(pt):
    return np.array([pt.x(), pt.y(), pt.z()])

def npToQgs(pt):
    return QgsPoint(pt[0], pt[1], pt[2])

def distancePointFromPlane(p, plane):
    n = plane[:3]
    return p.dot(n) + plane[3]

def lineVector(p0, p1):
    vec = p1-p0
    vec = vec/np.linalg.norm(vec)
    return vec

def lineIntersectPlane(plane, p0, p1):
    td = plane[0]*(p1[0]-p0[0]) + plane[1]*(p1[1]-p0[1]) + plane[2]*(p1[2]-p0[2])
    if td == 0:
        return None
    t = -(plane[0]*p0[0] + plane[1]*p0[1] + plane[2]*p0[2] + plane[3]) / td
    pi = np.array([ p0[0]+t*(p1[0]-p0[0]), p0[1]+t*(p1[1]-p0[1]), p0[2]+t*(p1[2]-p0[2])])
#    msg = 'pi: {:f} {:f} {:f}'.format(pi[0], pi[1], pi[2])
#    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
    return pi
    
def lineIntersectOffsetPlane(plane, offset, p0, p1):
    newPlane = np.array([plane[0], plane[1], plane[2], plane[3] - offset])
    return lineIntersectPlane(newPlane, p0, p1)
    
def projectPointToPlane(plane, pt):
#    The projection of a point q = (x, y, z) onto a plane given by a point p = (a, b, c) and a normal n = (d, e, f) is
#    q_proj = q - dot(q - p, n) * n
    n = plane[:3]
    p0 = n * -plane[3]
    
    pi = pt - np.dot(pt - p0, n) * n
#    pi = np.dot(pt - p0, n) * n - pt
    
    return pi

class Section:
    def __init__(self, name, startX, startY, endX, endY, width, layerList, elevationList):
#        iface.messageBar().pushMessage("Debug", "In Section Constructor", level=Qgis.Warning)
        self.name = name
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = width
        self.sourceLayers = layerList
        self.sourceElevation = elevationList

        self.origin = np.array([self.startX, self.startY, 0.0])
        
        # Calculate angle of rotation around startPoint from +X axis
        # Translate the end point to make the start point the origin
        ptx = self.endX - self.startX
        pty = self.endY - self.startY
        # Anticlockwise angle from +X axis
        angle = np.arctan2(pty, ptx)  
        # Now, let's create a quaternion to represent the rotation from the real life section back to +X axis
        self.quat = Quaternion(axis=[0, 0, 1], radians=-angle)
        
        # These are different from the start and end variables as a section may be defined 'backwards'
        self.minX = min(self.startX, self.endX)
        self.maxX = max(self.startX, self.endX)
        self.minY = min(self.startY, self.endY)
        self.maxY = max(self.startY, self.endY)
        
        self.sectionLayers = []

        self.needToGenerate = True
        self.sectionLength = math.sqrt((self.endX-self.startX)*(self.endX-self.startX) + (self.endY-self.startY)*(self.endY-self.startY))
        self.westEast = (startY == endY)
        self.southNorth = (startX == endX)

        self.group = QgsLayerTreeGroup(self.name)
        self.group.setExpanded(False)

        # Find equation of the plane and the normal to the plane
        self.plane = verticalPlane(startX, startY, endX, endY)

        self.window = None
        
    def create(self):
        self.sectionLayers = self.sectionThroughLayers(self.sourceLayers)
        
        layers = self.sectionThroughElevation(self.sourceElevation)
        for layer in layers:
            self.sectionLayers.append(layer)
        
    def createWindow(self):
        self.window = SectionWindow(self.sectionLayers)
        self.window.show()
        extent = layersExtent(self.sectionLayers)
        extent.grow(10)
        self.window.canvas.setExtent(extent)
        
    def sectionThroughElevation(self, layers):
        #Create new layers for the section based on the requested plan layers
        elevationLayers = []
        
        for layer in layers:
            #Try and match the layer to be created with one already under the section.group, else create a new layer
            newName = self.createSectionLayerName(layer, self.name)
            elevLayer = self.matchLayer(newName)
            usingNewLayer = False
            if elevLayer == None:
                elevLayer = self.createSectionElevationLayer(layer, newName)
                usingNewLayer = True

            # List of points to represent the portion of the line within the section
            pointList = []

            dp = layer.dataProvider()
            step = min(abs(layer.rasterUnitsPerPixelX()), abs(layer.rasterUnitsPerPixelY()))
            steps =  math.ceil(self.sectionLength / step) + 1
            dx = (self.maxX - self.minX) / step
            dy = (self.maxY - self.minY) / step
            x = self.minX
            y = self.minY
            dist = 0.0
            for i in range(steps):
                ht, ok = dp.sample(QgsPointXY(x, y), 1)
                if ok:
                    pointList.append(QgsPoint(dist, ht, 0.0))
                x = x + dx
                y = y + dy
                dist = dist + step
                
            # Is this a west-east section
            if self.westEast:
                for pt in pointList:
                    pt.setX(pt.x() + self.minX)
            # Or maybe a south-north section
            elif self.southNorth:
                for pt in pointList:
                    pt.setX(pt.x() + self.minY)
            
            if len(pointList) > 1:
                # Variable to hold a feature
                feature = QgsFeature()
                feature.setGeometry(QgsGeometry.fromPolyline(pointList))
        
                # Add the new feature to the new Trace_ layer
                elevLayer.startEditing()
                elevLayer.addFeature(feature)
                elevLayer.commitChanges()

                elevationLayers.append(elevLayer)

                if usingNewLayer:
                    QgsProject.instance().addMapLayer(elevLayer, False)
                    self.group.addLayer(elevLayer)
            
        return elevationLayers
    
    def sectionThroughLayers(self, layers):
        #Create new layers for the section based on the requested plan layers
        sectionLayers = []

        # Total number of features for progress bar
        totalFeatures = 0
        for layer in layers:
            totalFeatures = totalFeatures + layer.featureCount()
        pdInc = totalFeatures / 100
        pdVal = 0
        pdCount = 0
        
        # Set up a progress bar
        pd = QProgressDialog()
        pd.setWindowTitle("Building Section")
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        pd.setMaximum(100)
        pd.setValue(0)
        
        for layer in layers:
            #Try and match the layer to be created with one already under the section.group, else create a new layer
            newName = self.createSectionLayerName(layer, self.name)
            sectionLayer = self.matchLayer(newName)
            usingNewLayer = False
            if sectionLayer == None:
                sectionLayer = self.createSectionLayer(layer, newName)
                usingNewLayer = True

            #Loop through plan layer
            for lf in layer.getFeatures():
                pdCount = pdCount + 1
                if pdCount >= pdInc:
                    pdVal = pdVal + 1
                    pdCount = 0
                    pd.setValue(pdVal)
                    qApp.processEvents()
                    
                # Variable to hold a feature
                feature = QgsFeature()
    
                # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                # We therefore get a vertex iterator for the abstractGeometry and build our own list
                tracePolyline = []
                vi = lf.geometry().vertices()
                while vi.hasNext():
                    p = vi.next()
                    tracePolyline.append(qgsToNp(p))

                # Build array of points transalted to the +X axis
                pr = []
                for p in tracePolyline:
                    pt = p - self.origin
                    pr.append(self.quat.rotate(pt))
                
                # List of points to represent the portion of the line within the section
                # Note that the pointList array is in Section2D coordinates
                pointList = []
                
                # Build new feature pointlist only for line segments that are inside or cross the section
                # Loop through the distance array and check each point pair
                prlen = len(pr)
                plane = np.array([0.0, 1.0, 0.0, 0.0])
                halfWidth = self.width/2.0
                for index, p in enumerate(pr):
                    # We are in Section3D coordinates, so we can reject anything with X less than 0 or greater
                    #   then the section length
                    if p[0] < 0 or p[0] > self.sectionLength:
                        continue
                    
                    #Now, the distance from the section plane is equivalent to the Y coordinate
                    if p[1] > halfWidth:
                        # The point is in front of the section so check if the line segment passes through
                        # Check that we're nopt on the last point
                        if index < prlen - 1:
                            if pr[index+1][1] < halfWidth:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(plane, halfWidth, p, pr[index + 1])
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[2], 0.0))
                    elif p[1] >= -halfWidth:
                        # The point is within the section, so add it to the list
                        pointList.append(QgsPoint(p[0], p[2], 0.0))
                        # We still need to check if the following line segment passes out of the section
                        if index < prlen - 1:
                            if pr[index+1][1] > halfWidth:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(plane, halfWidth, p, pr[index + 1])
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[2], 0.0))
                            elif pr[index+1][1] < -halfWidth:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(plane, -halfWidth, p, pr[index + 1])
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[2], 0.0))
                    else:
                        # The point is behind the section so check if line segment passes through
                        # Check that we're not on the last point
                        if index < prlen - 1:
                            if p[1] > -halfWidth:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(plane, -halfWidth, p, pr[index + 1])
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[2], 0.0))
                    
                # Set the geometry for the new downhole feature
                fvalid = False
                if QgsWkbTypes.flatType(sectionLayer.wkbType()) == QgsWkbTypes.Point:
                    if len(pointList) > 0:
                        fvalid = True
                        feature.setGeometry(QgsGeometry(pointList[0]))
                else:
                    if len(pointList) > 1:
                        fvalid = True
                        feature.setGeometry(QgsGeometry.fromPolyline(pointList))

                if fvalid:                        
                    # Set the attributes for the new feature
                    feature.setAttributes(lf.attributes())
            
                    # Add the new feature to the new Trace_ layer
                    sectionLayer.startEditing()
                    sectionLayer.addFeature(feature)
                    sectionLayer.commitChanges()
            
            styleNames = layer.styleManager().styles()
            currentStyleName = layer.styleManager().currentStyle()
            
            for styleName in styleNames:
                style = layer.styleManager().style(styleName)
                renamed = sectionLayer.styleManager().renameStyle(styleName, "temp")
                sectionLayer.styleManager().addStyle(styleName, style)
                if renamed:
                    sectionLayer.styleManager().removeStyle("temp")
            
            sectionLayer.styleManager().setCurrentStyle(currentStyleName)
            
            sectionLayer.updateExtents(True)
    
            sectionLayers.append(sectionLayer)

            if usingNewLayer:
                QgsProject.instance().addMapLayer(sectionLayer, False)
                self.group.addLayer(sectionLayer)
            
        return sectionLayers

    
    def matchLayer(self, name):
        layer = None
        for child in self.group.children():
            if child.name() == name:
                layer = child.layer()
                break
        return layer

    def createSectionLayerName(self, baseLayer, sectionName):
        name = "S_" + sectionName + "_" + baseLayer.name()[baseLayer.name().rfind("_"):]
        return name

    def createSectionLayer(self, baseLayer, name):
        #Create a new memory layer
        layer = QgsVectorLayer("PointZ?crs=EPSG:4326" if QgsWkbTypes.flatType(baseLayer.wkbType()) == QgsWkbTypes.Point else "LineStringZ?crs=EPSG:4326", name, "memory")
        layer.setCrs(baseLayer.crs())
        atts = []
        # Loop through the list of desired field names that the user checked
        for field in baseLayer.fields():
            atts.append(field)
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 

        return layer

    def createSectionElevationLayer(self, baseLayer, name):
        #Create a new memory layer
        layer = QgsVectorLayer("LineStringZ?crs=EPSG:4326", name, "memory")
        layer.setCrs(baseLayer.crs())

        return layer
    
    def writeProjectData(self, index):
        key = 'S{:02d}_Name'.format(index)
        writeProjectData(key, self.name)
        key = 'S{:02d}_StartX'.format(index)
        writeProjectData(key, self.startX)
        key = 'S{:02d}_StartY'.format(index)
        writeProjectData(key, self.startY)            
        key = 'S{:02d}_EndX'.format(index)
        writeProjectData(key, self.endX)            
        key = 'S{:02d}_EndY'.format(index)
        writeProjectData(key, self.endY)            
        key = 'S{:02d}_Width'.format(index)
        writeProjectData(key, self.width)

        key = 'S{:02d}_SourceLayers'.format(index)
        writeProjectData(key, len(self.sourceLayers))
        for li, layer in enumerate(self.sourceLayers):
            key = 'S{:02d}_SourceLayer{:02d}'.format(index, li)
            writeProjectData(key, layer.name())
            
        key = 'S{:02d}_ElevationLayers'.format(index)
        writeProjectData(key, len(self.sourceElevation))
        for li, layer in enumerate(self.sourceElevation):
            key = 'S{:02d}_ElevationLayer{:02d}'.format(index, li)
            writeProjectData(key, layer.name())
        
    
# The SectionManager class manipulates and keeps track of all the sections
class SectionManager:
    def __init__(self, drillManager):
        self.drillManager = drillManager
        self.sectionReg = []
        
    def createSection(self, name, startX, startY, endX, endY, width, layerList, elevationList, writeProjectData = True):
#        iface.messageBar().pushMessage("Debug", "In CreateSection", level=Qgis.Warning)
        sectionGroup = self.sectionGroup()
        
        s = Section(name, startX, startY, endX, endY, width, layerList, elevationList)
        # Re-assign the layerTreeGroup if a matching one already exists
        group = self.matchGroup(s)
        if group != None:
#            iface.messageBar().pushMessage("Debug", group.name(), level=Qgis.Warning)
            s.group = group
        else:
            sectionGroup.addChildNode(s.group)
        
        self.sectionReg.append(s)

        if writeProjectData:
            self.drillManager.writeProjectData()
        
        return s

    def matchGroup(self, section):
        group = None
        sgroup = self.sectionGroup()
        for child in sgroup.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == section.name:
                group = child
                break
        return group

    def groupExtent(self, group):
        tLayers = group.findLayers()
        extent = QgsRectangle()
        for tl in tLayers:
            l = tl.layer()
            if l is not None:
                rect = l.extent()
                if rect is not None:
                    extent.combineExtentWith(rect)
        return extent
                    
    #Return the root group for all sections or create it if it doesn't exist
    def sectionGroup(self):
        group = None
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == "Sections":
                group = child
                break
        
        if group == None:
            group = root.insertGroup(0, "Sections")
            group.setIsMutuallyExclusive(True)
            
        return group

    def showSection(self, section):
        # Generate the section data if it hasn't already been done (ie it has no sectionLayers).
        if len(section.sectionLayers) == 0:
            section.create()
            
        for s in self.sectionReg:
            if s == section:
                s.group.setItemVisibilityChecked( True )
            else:
                s.group.setItemVisibilityChecked( False )
                
        extent = self.groupExtent(section.group)
        if not extent.isEmpty():
            extent.grow(10)
            iface.mapCanvas().setExtent(extent)

    def recreateSection(self, section):
        section.sectionLayers.clear()
        section.create()
        
    def deleteSection(self, section):
        if section.window != None:
            section.window.close()
            section.window = None
        
        try:
            if section.group != None:
                section.group.removeAllChildren()
                self.sectionGroup().removeChildNode(section.group)
        except:
            # The user probably already removed the section group
            pass
        
        self.removeSection(section)
        self.drillManager.writeProjectData()
        
    def removeSections(self, sectionList):
        for s in sectionList:
            self.removeSection(s)
        
    def removeSection(self, section):
        self.sectionReg.remove(section)
        
    def readProjectData(self):
        self.sectionReg.clear()
#        self.sectionGroup().removeAllChildren()
        
        numSections = readProjectNum("Sections", 0)
        for index in range(numSections):
            key = 'S{:02d}_Name'.format(index)
#            iface.messageBar().pushMessage("Debug", key, level=Qgis.Info)
            name = readProjectText(key, "")
            key = 'S{:02d}_StartX'.format(index)
            startx = readProjectNum(key, 0)
            key = 'S{:02d}_StartY'.format(index)
            starty = readProjectNum(key, 0)            
            key = 'S{:02d}_EndX'.format(index)
            endx = readProjectNum(key, 100)            
            key = 'S{:02d}_EndY'.format(index)
            endy = readProjectNum(key, 0)            
            key = 'S{:02d}_Width'.format(index)
            width = readProjectNum(key, 20)

            key = 'S{:02d}_SourceLayers'.format(index)
            numLayers = readProjectNum(key, 0)
            layerList = []
            for li in range(numLayers):
                key = 'S{:02d}_SourceLayer{:02d}'.format(index, li)
                layerName = readProjectText(key, "")
                if layerName != "":
                    layer = getLayerByName(layerName)
                    if layer != None:
                        layerList.append(layer)

            key = 'S{:02d}_ElevationLayers'.format(index)
            numLayers = readProjectNum(key, 0)
            elevationList = []
            for li in range(numLayers):
                key = 'S{:02d}_ElevationLayer{:02d}'.format(index, li)
                layerName = readProjectText(key, "")
                if layerName != "":
                    layer = getLayerByName(layerName)
                    if layer != None:
                        elevationList.append(layer)

#            msg = 'Creating Section: {:s}'.format(name)
#            iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
            self.createSection(name, startx, starty, endx, endy, width, layerList, elevationList, False)
            
        if self.drillManager.sectionManagerDlg != None:
            self.drillManager.sectionManagerDlg.fillSectionList()
    
    def writeProjectData(self):
        #We first need to remove excess section entries
        numSections = readProjectNum("Sections", 0)
        if numSections > len(self.sectionReg):
            for index in range( len(self.sectionReg), numSections):
                # We first remove the layer list
                key = 'S{:02d}_SourceLayers'.format(index)
                numLayers = readProjectNum(key, 0)
                removeProjectEntry(key)
                for li in range(numLayers):
                    key = 'S{:02d}_SourceLayer{:02d}'.format(index, li)
                    removeProjectEntry(key)

                # and the elevation list
                key = 'S{:02d}_ElevationLayers'.format(index)
                numLayers = readProjectNum(key, 0)
                removeProjectEntry(key)
                for li in range(numLayers):
                    key = 'S{:02d}_ElevationLayer{:02d}'.format(index, li)
                    removeProjectEntry(key)
                
                key = 'S{:02d}_Name'.format(index)
                removeProjectEntry(key)
                key = 'S{:02d}_StartX'.format(index)
                removeProjectEntry(key)
                key = 'S{:02d}_StartY'.format(index)
                removeProjectEntry(key)
                key = 'S{:02d}_EndX'.format(index)
                removeProjectEntry(key)
                key = 'S{:02d}_EndY'.format(index)
                removeProjectEntry(key)
                key = 'S{:02d}_Width'.format(index)
                removeProjectEntry(key)
    
        
#         Now, write over the needed ones        
#        msg = 'WriteData numSections: {:d}'.format(len(self.sectionReg))
#        iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
        writeProjectData("Sections", len(self.sectionReg))
        for index, s in enumerate(self.sectionReg):
            self.sectionReg[index].writeProjectData(index)
        