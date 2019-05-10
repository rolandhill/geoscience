# -*- coding: utf-8 -*-
"""
Created on Thu May  2 17:56:42 2019

@author: HillR
"""
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsMessageBar
from qgis.core import Qgis, QgsWkbTypes
from qgis.utils import iface

from PyQt5 import QtCore

from .Utils import *
from .sectionMapCanvas_dialog import SectionMapCanvasDialog

class SectionMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas, parent):
        self.canvas = canvas
        self.sectionManagerDlg = parent
        self.drillManager = self.sectionManagerDlg.drillManager
        QgsMapToolEmitPoint.__init__(self, self.canvas)
        self.rubberBand = QgsRubberBand(self.canvas, True)
#        self.rubberBand.setColor(Qt.red)
        self.reset()

    def reset(self):
        self.startPoint = self.endPoint = None
        self.isEmittingPoint = False
        self.rubberBand.reset(True)

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
        dlg.leSectionWidth.setText(str(self.drillManager.sectionWidth))
        result = dlg.exec_()
        if result:
            self.drillManager.sectionName = dlg.leName.text()
            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = getCheckedLayers(dlg.listLayers)
            self.drillManager.elevationLayers = getCheckedLayers(dlg.elevationLayers)

        dlg.close()
        
        if result:
            s = self.drillManager.sectionManager.createSection(self.drillManager.sectionName, \
               self.startPoint.x(), self.startPoint.y(), self.endPoint.x(), self.endPoint.y(), \
               self.drillManager.sectionWidth, self.drillManager.sectionLayers, self.drillManager.elevationLayers)
        
            self.sectionManagerDlg.fillSectionList()
            
            self.sectionManagerDlg.sectionManager.showSection(s)
            
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
        self.rubberBand.reset(QgsWkbTypes.LineGeometry)
#        if startPoint.x() == endPoint.x() or startPoint.y() == endPoint.y():
#            return

#        point1 = QgsPointXY(startPoint.x(), startPoint.y())
#        point2 = QgsPointXY(startPoint.x(), endPoint.y())
#        point3 = QgsPointXY(endPoint.x(), endPoint.y())
#        point4 = QgsPointXY(endPoint.x(), startPoint.y())

        self.rubberBand.addPoint(startPoint, False)
#        self.rubberBand.addPoint(point2, False)
#        self.rubberBand.addPoint(point3, False)
        self.rubberBand.addPoint(endPoint, True)  # true to update canvas
        self.rubberBand.show()

#    def rectangle(self):
#        if self.startPoint is None or self.endPoint is None:
#            return None
#        elif self.startPoint.x() == self.endPoint.x() or self.startPoint.y() == self.endPoint.y():
#            return None
#
#        return QgsRectangle(self.startPoint, self.endPoint)