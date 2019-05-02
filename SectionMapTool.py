# -*- coding: utf-8 -*-
"""
Created on Thu May  2 17:56:42 2019

@author: HillR
"""
from qgis.gui import QgsMapToolEmitPoint, QgsRubberBand, QgsMessageBar
from qgis.core import Qgis, QgsWkbTypes
from qgis.utils import iface

class SectionMapTool(QgsMapToolEmitPoint):
    def __init__(self, canvas):
        self.canvas = canvas
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
        self.isEmittingPoint = False
        msg = 'start: {:f}, {:f}  end: {:f}, {:f}'.format(self.startPoint.x(), self.startPoint.y(), self.endPoint.x() , self.endPoint.y())
        iface.messageBar().pushMessage("Debug", msg, level=Qgis.Warning)
#        r = self.rectangle()
#        if r is not None:
#            print("Rectangle:", r.xMinimum(), r.yMinimum(), r.xMaximum(), r.yMaximum())
#            self._iface.actionPan().trigger()

    def canvasMoveEvent(self, e):
        if not self.isEmittingPoint:
            return

        self.endPoint = self.toMapCoordinates(e.pos())
        self.showLine(self.startPoint, self.endPoint)

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