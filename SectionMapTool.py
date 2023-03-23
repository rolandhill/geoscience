# -*- coding: utf-8 -*-
"""
Created on Thu May  2 17:56:42 2019

@author: HillR
"""
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsMessageBar
from qgis.core import Qgis, QgsWkbTypes
from qgis.utils import iface

from PyQt5 import QtCore, Qt

import numpy as np

from .Utils import *
from .sectionMapCanvas_dialog import SectionMapCanvasDialog


class SectionMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.sectionManagerDlg = parent
        self.drillManager = self.sectionManagerDlg.drillManager
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas)
        self.rubberBand.setColor(QtCore.Qt.red)
        self.rubberBand.setWidth(1)
        
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)

    def canvasPressEvent(self, e):
        self.startPoint = self.toMapCoordinates(e.pos())
        self.endPoint = self.startPoint
        self.isEmittingPoint = True
        self.showLine(self.startPoint, self.endPoint)

    def canvasReleaseEvent(self, e):
        self.endPoint = self.toMapCoordinates(e.pos())
        self.isEmittingPoint = False

        # Get the layers to incude in the section from a dlg
        dlg = SectionMapCanvasDialog()
        dlg.leName.setText(self.suggestName())
        result = dlg.exec_()
        if result:
            self.drillManager.sectionName = dlg.leName.text()
#            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = getCheckedLayers(dlg.listLayers)
            self.drillManager.elevationLayers = getCheckedLayers(dlg.listElevation)

        dlg.close()
        
        if result:
            s = self.drillManager.sectionManager.createSection(self.drillManager.sectionName, \
               self.startPoint.x(), self.startPoint.y(), self.endPoint.x(), self.endPoint.y(), \
               self.drillManager.sectionWidth, self.drillManager.sectionLayers, self.drillManager.elevationLayers)
        
            self.sectionManagerDlg.fillSectionList()
            
            self.sectionManagerDlg.sectionManager.showSection(s)
            
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        iface.mapCanvas().setMapTool(self.oldMapTool)

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showLine(self.startPoint, self.endPoint)

    def suggestName(self):
        dir = 'N'
        if abs(self.endPoint.y() - self.startPoint.y()) > abs(self.endPoint.x() - self.startPoint.x()):
            dir = 'E'
        
        name = "00"
        if dir == 'N':
            name = "{:d}".format(int((self.endPoint.y() + self.startPoint.y())/2.0)) + dir
        else:
            name = "{:d}".format(int((self.endPoint.x() + self.startPoint.x())/2.0)) + dir
        
        return name
        
    def showLine(self, startPoint, endPoint):
        if startPoint == endPoint:
            return
        start = np.array([startPoint.x(), startPoint.y(), 0.0])
        end = np.array([endPoint.x(), endPoint.y(), 0.0])
        v = end - start
        u = v / np.linalg.norm(v)
        n = np.cross(np.array([0.0, 0.0, 1.0]), u)
        width = self.drillManager.sectionWidth
        nw = n * (width*0.5)
        qnw = QgsVector(nw[0], nw[1])
        p0 = endPoint + qnw
        p1 = startPoint + qnw
        p2 = startPoint - qnw
        p3 = endPoint - qnw
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
        self.rubberBand.addPoint(startPoint, False)
        self.rubberBand.addPoint(endPoint, False)  # true to update canvas
        self.rubberBand.addPoint(p0, False)
        self.rubberBand.addPoint(p1, False)
        self.rubberBand.addPoint(p2, False)
        self.rubberBand.addPoint(p3, False)
        self.rubberBand.addPoint(endPoint, True)  # true to update canvas
        self.rubberBand.show()

#    def rectangle(self):
#        if self.startPoint is None or self.endPoint is None:
#            return None
#        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
#            return None
#
#        return QgsRectangle(self.startPoint, self.endPoint)