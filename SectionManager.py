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
    msg = 'plane:  {:f} {:f} {:f} {:f}'.format(a, b, c, d)
    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
    
    return np.array([a, b, c, d])

#def planeNormal(p):
#    return p[:3]

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
        self.name = name
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = width
        self.sourceLayers = layerList
        
        self.westEast = startY == endY
        self.southNorth = startX == endX

        self.group = QgsLayerTreeGroup(self.name)

        # Find equation of the plane and the normal to the plane
        self.plane = verticalPlane(startX, startY, endX, endY)

        self.sectionLayers = self.sectionThroughLayers(self.sourceLayers)
        
        self.window = SectionWindow(self.sectionLayers)
        self.window.show()
        
    def sectionThroughLayers(self, layers):
        #Create new layers for the section based on the requested plan layers
        sectionLayers = []
        
        for layer in layers:
            #Create a new layer
            sectionLayer = self.createSectionLayer(layer, self.name)

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
                if len(pointList) > 1:
                    feature.setGeometry(QgsGeometry.fromPolyline(qPointList))
    
                    # Set the attributes for the new feature
                    feature.setAttributes(lf.attributes())
            
                    # Add the new feature to the new Trace_ layer
                    sectionLayer.startEditing()
                    sectionLayer.addFeature(feature)
                    sectionLayer.commitChanges()
    
            sectionLayers.append(sectionLayer)

            QgsProject.instance().addMapLayer(sectionLayer)
            
        return sectionLayers

    def createSectionLayer(self, baseLayer, sectionName):
        #Create a new memory layer
        layer = QgsVectorLayer("LineStringZ?crs=EPSG:4326", baseLayer.name() + "_" + sectionName, "memory")
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

    
# The SectionManager class manipulates and keeps track of all the sections
class SectionManager:
    def __init__(self):
        self.sectionReg = []
        
    def createSection(self, name, startX, startY, endX, endY, width, layerList):
        sectionGroup = self.sectionGroup()
        
        s = Section(name, startX, startY, endX, endY, width, layerList)
        sectionGroup.addChildNode(s.group)

        self.sectionReg.append(s)

    def sectionGroup(self):
        group = None
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == "Sections":
                group = child
                break
        
        if group == None:
            group = root.insertGroup(0, "Sections")
            
        return group
    
    