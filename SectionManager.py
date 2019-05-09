# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:41:08 2019

@author: HillR
"""

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
import numpy as np

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
    def __init__(self, name, startX, startY, endX, endY, width, layerList):
#        iface.messageBar().pushMessage("Debug", "In Section Constructor", level=Qgis.Warning)
        self.name = name
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = width
        self.needToGenerate = True
        self.sourceLayers = layerList
        self.sectionLayers = []
        
        self.westEast = startY == endY
        self.southNorth = startX == endX

        self.group = QgsLayerTreeGroup(self.name)
        self.group.setExpanded(False)

        # Find equation of the plane and the normal to the plane
        self.plane = verticalPlane(startX, startY, endX, endY)

        self.window = None
        
    def create(self):
        self.sectionLayers = self.sectionThroughLayers(self.sourceLayers)
        
    def createWindow(self):
        self.window = SectionWindow(self.sectionLayers)
        self.window.show()
#        extent = self.groupExtent(s.group)
#        extent.grow(10)
#        s.window.canvas.setExtent(extent)
        
    def sectionThroughLayers(self, layers):
        #Create new layers for the section based on the requested plan layers
        sectionLayers = []
        
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
                # !!!! ToDo: Can we check the bounding box to reject entire features
                
                # Variable to hold a feature
                feature = QgsFeature()
    
                # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                # We therefore get a vertex iterator for the abstractGeometry and build our own list
                tracePolyline = []
                vi = lf.geometry().vertices()
                while vi.hasNext():
                    p = vi.next()
                    tracePolyline.append(qgsToNp(p))

                # Create an array to hold the distance of each point from the plane
                distance = []
                
                # Calculate the distance of each point from the plane
                for pt in tracePolyline:
                    d = distancePointFromPlane(pt, self.plane)
                    distance.append(d)
#                    msg = 'p:  {:f} {:f} {:f}   plane:  {:f} {:f} {:f} {:f}    d: {:f}'.format(p[0], p[1], p[2] , plane[0], plane[1], plane[2], plane[3], d)
#                    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
                        
                # List of points to represent the portion of the line within the section
                pointList = []
                
                # Build new feature pointlist only for line segments that are inside or cross the section
                # Loop through the distance array and check each point pair
                distlen = len(distance)
                for index, d in enumerate(distance):
                    if d > self.width:
                        # The point is in front of the section so check if the line segment passes through
                        # Check that we're nopt on the last point
                        if index < distlen - 1:
                            if distance[index+1] < self.width:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(self.plane, self.width, tracePolyline[index], tracePolyline[index + 1])
                                if pi is not None:
                                    pointList.append(projectPointToPlane(self.plane, pi))
                    elif d >= -self.width:
                        # The point is within the section, so add it to the list
                        pp = projectPointToPlane(self.plane, tracePolyline[index])
                        pointList.append(pp)
                        # We still need to check if the following line segment passes out of the section
                        if index < distlen - 1:
                            if distance[index+1] > self.width:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(self.plane, self.width, tracePolyline[index], tracePolyline[index + 1])
                                if pi is not None:
                                    pointList.append(projectPointToPlane(self.plane, pi))
                            elif distance[index+1] < -self.width:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(self.plane, -self.width, tracePolyline[index], tracePolyline[index + 1])
                                if pi is not None:
                                    pointList.append(projectPointToPlane(self.plane, pi))
                    else:
                        # The point is behind the section so check if line segment passes through
                        # Check that we're not on the last point
                        if index < distlen - 1:
                            if distance[index+1] > -self.width:
                                # Find intersection of line segment with plane
                                pi = lineIntersectOffsetPlane(self.plane, -self.width, tracePolyline[index], tracePolyline[index + 1])
                                if pi is not None:
                                    pointList.append(projectPointToPlane(self.plane, pi))
                # Translate the projected points into a plane based coordinate system
                qPointList = []
                # Is this a west-east section
                if self.westEast:
                    for pt in pointList:
                        qPointList.append(QgsPoint(pt[0], pt[2], pt[1]))
                # Or maybe a south-north section
                elif self.southNorth:
                    for pt in pointList:
                        qPointList.append(QgsPoint(pt[1], pt[2], pt[0]))
                # Then it must be an oblique section
                else:
                    x0 = np.array([self.startX, self.startY, 0.0])
                    for pt in pointList:
                        v0 = pt - x0
                        qPointList.append(QgsPoint(v0[0], v0[2], v0[1]))
                    
                # Set the geometry for the new downhole feature
                fvalid = False
                if QgsWkbTypes.flatType(sectionLayer.wkbType()) == QgsWkbTypes.Point:
                    if len(pointList) > 0:
                        fvalid = True
                        feature.setGeometry(QgsGeometry(QgsPoint(qPointList[0].x(), qPointList[0].y(), qPointList[0].z())))
                else:
                    if len(pointList) > 1:
                        fvalid = True
                        feature.setGeometry(QgsGeometry.fromPolyline(qPointList))

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
        layer.setCrs(baseLayer.sourceCrs())
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
            
        
    
# The SectionManager class manipulates and keeps track of all the sections
class SectionManager:
    def __init__(self, drillManager):
        self.drillManager = drillManager
        self.sectionReg = []
        
    def createSection(self, name, startX, startY, endX, endY, width, layerList, writeProjectData = True):
#        iface.messageBar().pushMessage("Debug", "In CreateSection", level=Qgis.Warning)
        sectionGroup = self.sectionGroup()
        
        s = Section(name, startX, startY, endX, endY, width, layerList)
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
        
        if section.group != None:
            section.group.removeAllChildren()
            self.sectionGroup().removeChildNode(section.group)
        
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

#            msg = 'Creating Section: {:s}'.format(name)
#            iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
            self.createSection(name, startx, starty, endx, endy, width, layerList, False)
            
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
        