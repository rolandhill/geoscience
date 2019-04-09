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
    p3 = np.array([endx, endy, 100])
    
    v1 = p3 - p1
    v2 = p2 - p1
    
    cp = np.cross(v2, v1)
    cp = cp/np.linalg.norm(cp)
    a, b, c = cp
    
    d = np.dot(cp, p3)
#    msg = 'plane:  {:f} {:f} {:f} {:f}'.format(a, b, c, d)
#    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
    
    return np.array([a, b, c, d])

#def planeNormal(p):
#    return p[:3]

def distancePointFromPlane(p, plane):
    n = plane[:3]
    return p.dot(n) - plane[3]

def lineVector(p0, p1):
    vec = p1-p0
    vec = vec/np.linalg.norm(vec)
    return vec

def lineIntersectPlane(plane, p0, p1):
    np0 = np.array([p0.x(), p0.y(), p0.z()])
    np1 = np.array([p1.x(), p1.y(), p1.z()])
    msg = 'plane:  {:f} {:f} {:f} {:f} np0: {:f} {:f} {:f}  np1: {:f} {:f} {:f}'.format(plane[0], plane[1], plane[2], plane[3], np0[0], np0[1], np0[2], np1[0], np1[1], np1[2])
    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
    td = plane[0]*(np1[0]-np0[0]) + plane[1]*(np1[1]-np0[1]) + plane[2]*(np1[2]-np0[2])
    if td == 0:
        return None
    t = -(plane[0]*np0[0] + plane[1]*np0[1] + plane[2]*np0[2] - plane[3]) / td
    pi = np.array([ np0[0]+t*(np1[0]-np0[0]), np0[1]+t*(np1[1]-np0[1]), np0[2]+t*(np1[2]-np0[2])])
    msg = 'pi: {:f} {:f} {:f}'.format(pi[0], pi[1], pi[2])
    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
    return pi
    
def lineIntersectPlane2(plane, p0, p1):
    np0 = np.array([p0.x(), p0.y(), p0.z()])
    np1 = np.array([p1.x(), p1.y(), p1.z()])
    u = np1 - np0
    n = plane[:3]
    nlen = np.linalg.norm(n)
#    msg = 'u:  {:f} {:f} {:f}'.format(u[0], u[1], u[2])
#    msg = 'n:  {:f} {:f} {:f}'.format(n[0], n[1], n[2])
#    msg = 'u:  {:f} {:f} {:f}   n:  {:f} {:f} {:f}'.format(u[0], u[1], u[2] , n[0], n[1], n[2])
#    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
    dot = n.dot(u)
    if (abs(dot) > 1.0e-6):
        p_co = n * (-plane[3] / (nlen * nlen))
        w = np0 - p_co
        fac = -(n * w) / dot
        return np0 + (u * fac)
    else:
        return None

def lineIntersectOffsetPlane(plane, offset, p0, p1):
    newPlane = np.array([plane[0], plane[1], plane[2], plane[3] + offset])
    return lineIntersectPlane(newPlane, p0, p1)
    
class Section:
    def __init__(self, name, startX, startY, endX, endY, width, layerList):
        self.name = name
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY
        self.width = width

        self.layers = layerList
        
        self.group = QgsLayerTreeGroup(self.name)
        
        self.window = SectionWindow(self.layers)
        self.window.show()
        
    
# The SectionManager class manipulates and keeps track of all the sections
class SectionManager:
    def __init__(self):
        self.sectionReg = []
        
    def createSection(self, name, startX, startY, endX, endY, width, layerList):
        sectionGroup = self.sectionGroup()
        
        # Find equation of the plane and the normal to the plane
        plane = verticalPlane(startX, startY, endX, endY)
#        n = planeNormal(plane)
#        msg = 'n: {:f} {:f} {:f}'.format(n[0], n[1], n[2])
#        iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
        
        #Create new layers for the section based on the requested plan layers
        sectionLayers = []
        for layer in layerList:
            #Create a new layer
            sectionLayer = self.createSectionLayer(layer, name)

            #Loop through plan layer
            for index, lf in enumerate(layer.getFeatures()):
                # !!!! ToDo: Can we check the bounding box to reject entire holes
                
                # Variable to hold a feature
                feature = QgsFeature()
    
                # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                # We therefore get a vertex iterator for the abstractGeometry and build our own list
                tracePolyline = []
                vi = lf.geometry().vertices()
                while vi.hasNext():
                    p = vi.next()
                    tracePolyline.append(p)
#                    msg = 'vi:  {:f} {:f} {:f}'.format(p.x(), p.y(), p.z())
#                    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)

                # Create an array to hold the distance of each point from the plane
                distance = []
                
                # Calculate the distance of each point from the plane
                for pt in tracePolyline:
                    p = np.array([pt.x(), pt.y(), pt.z()])
                    d = distancePointFromPlane(p, plane)
                    distance.append(d)
#                    msg = 'p:  {:f} {:f} {:f}   plane:  {:f} {:f} {:f} {:f}    d: {:f}'.format(p[0], p[1], p[2] , plane[0], plane[1], plane[2], plane[3], d)
#                    iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
                        
                # List of points to represent the portion of the line within the section
                pointList = []
                
                # Build new feature pointlist only for line segments that are inside or cross the section
                # Loop through the distance array and check each point pair
                distlen = len(distance)
                for index, d in enumerate(distance):
                    if d > width:
                        # The point is in front of the section so check if the line segment passes through
                        # Check that we're nopt on the last point
                        if index < distlen - 1:
                            if distance[index+1] < width:
                                #check that the line segment isn't parallel to the plane
                                p0 = tracePolyline[index]
                                p1 = tracePolyline[index + 1]
                                pi = lineIntersectOffsetPlane(plane, width, p0, p1)
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[1], pi[2]))
                    elif d >= -width:
                        # The point is within the section, so add it to the list
                        pointList.append(tracePolyline[index])
                        # We still need to check if the following line segment passes out of the section
                        if index < distlen - 1:
                            if distance[index+1] > width:
                                #check that the line segment isn't parallel to the plane
                                p0 = tracePolyline[index]
                                p1 = tracePolyline[index + 1]
                                pi = lineIntersectOffsetPlane(plane, width, p0, p1)
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[1], pi[2]))
                            elif distance[index+1] < -width:
                                #check that the line segment isn't parallel to the plane
                                p0 = tracePolyline[index]
                                p1 = tracePolyline[index + 1]
                                pi = lineIntersectOffsetPlane(plane, -width, p0, p1)
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[1], pi[2]))
                    else:
                        # The point is behind the section so check if line segment passes through
                        # Check that we're nopt on the last point
                        if index < distlen - 1:
                            if distance[index+1] > -width:
                                #check that the line segment isn't parallel to the plane
                                p0 = tracePolyline[index]
                                p1 = tracePolyline[index + 1]
                                pi = lineIntersectOffsetPlane(plane, -width, p0, p1)
                                if pi is not None:
                                    pointList.append(QgsPoint(pi[0], pi[1], pi[2]))

                # Set the geometry for the new downhole feature
                if len(pointList) > 1:
                    feature.setGeometry(QgsGeometry.fromPolyline(pointList))
    
                    # Set the attributes for the new feature
                    feature.setAttributes(lf.attributes())
            
                    # Add the new feature to the new Trace_ layer
                    sectionLayer.startEditing()
                    sectionLayer.addFeature(feature)
                    sectionLayer.commitChanges()
    
            sectionLayers.append(sectionLayer)
            
            QgsProject.instance().addMapLayer(sectionLayer)
        
        s = Section(name, startX, startY, endX, endY, width, sectionLayers)
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

    