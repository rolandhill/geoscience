# -*- coding: utf-8 -*-
"""
/***************************************************************************
 CreateSectionTool
                              -------------------
        begin                : 2018-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Roland Hill / MMG
        email                : roland.hill@mmg.com
 ***************************************************************************/
"""
#from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
#from PyQt5.QtWidgets import

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

class CreateSectionTool(QgsMapTool):
    
    def __init__(self, iface, parent):
        QgsMapTool.__init__(self, iface.mapCanvas())
        self.iface = iface
        self.canvas = iface.mapCanvas()
        
    def activate(self):
        '''When activated set the cursor to a crosshair.'''
        self.canvas.setCursor(Qt.CrossCursor)
        
    def canvasPressEvent(self, event):
        '''Capture the coordinates when the user click on the mouse for measurements.'''
        pt = event.mapPoint()
        button = event.button()
        canvasCRS = self.canvas.mapSettings().destinationCrs()
#        if canvasCRS != epsg4326:
#            transform = QgsCoordinateTransform(canvasCRS, epsg4326, QgsProject.instance())
#            pt = transform.transform(pt.x(), pt.y())
        
    def canvasMoveEvent(self, event):
        pass