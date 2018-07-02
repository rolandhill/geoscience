# -*- coding: utf-8 -*-
"""
/***************************************************************************
 GeoTools
                                 A QGIS plugin
 Tools for Geoscience & Exploration
                              -------------------
        begin                : 2018-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Roland Hill / MMG
        email                : roland.hill@mmg.com
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QDialog

from qgis.core import *
from qgis.utils import *
from qgis.gui import *


# Initialize Qt resources from file resources.py
from .resources import *
from .ChangeDriveLetter_dialog import ChangeDriveLetterDialog
from .DrillManager import *

import os.path

""" Main Class"""    
class GeoTools:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'GeoTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.drillManager = DrillManager()

        self.readProjectData()
        
        # Declare instance attributes
        self.actions = []
        self.toolbar = self.iface.addToolBar(u'GeoTools')
        self.toolbar.setObjectName(u'GeoTools')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('GeoTools', message)


    def initGui(self):
        QgsProject.instance().readProject.connect(self.onReadProject)

        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        actions = self.iface.mainWindow().menuBar().actions()
        """ Create main menu."""
        lastAction = actions[-1]
        self.menu = QMenu( u'&GeoTools', self.iface.mainWindow().menuBar() )
        self.iface.mainWindow().menuBar().insertMenu( lastAction, self.menu )
        
        """Create Drill menu."""
        self.menuDrill = self.menu.addMenu("Drilling")

        action = self.menuDrill.addAction("Drill Setup")
        action.triggered.connect(self.drillManager.onDrillSetup)
        action.setEnabled(True)
        self.actions.append(action)

        action = self.menuDrill.addAction("Desurvey Data")
        action.triggered.connect(self.drillManager.onDesurveyData)
        action.setEnabled(True)
        self.actions.append(action)

        action = self.menuDrill.addAction("Display Traces")
        action.triggered.connect(self.drillManager.onDrillDisplayTraces)
        action.setEnabled(True)
        self.actions.append(action)
        
        action = self.menuDrill.addAction("Create Section")
        action.triggered.connect(self.drillManager.onDrillCreateSection)
        action.setEnabled(True)
        self.actions.append(action)
        
        """Create Vector menu."""
        self.menuVector = self.menu.addMenu("Vector")

        action = self.menuVector.addAction(QIcon(":/plugins/geotools/ReverseLine.png"), "Reverse Line Direction")
        action.triggered.connect(self.onReverseLine)
        action.setEnabled(True)
        self.iface.addToolBarIcon(action)
        self.actions.append(action)
        
        """Create Raster menu."""
        self.menuRaster = self.menu.addMenu("Raster")

        action = self.menuRaster.addAction("Transparent White")
        action.triggered.connect(self.onRasterTransparentWhite)
        action.setEnabled(True)
        self.actions.append(action)
        
        action = self.menuRaster.addAction("Transparent Black")
        action.triggered.connect(self.onRasterTransparentBlack)
        action.setEnabled(True)
        self.actions.append(action)
        
        """Create Project menu."""
        self.menuProject = self.menu.addMenu("Project")

        action = self.menuProject.addAction("Change drive letter")
        action.triggered.connect(self.onProjectChangeDriveLetter)
        action.setEnabled(True)
        self.actions.append(action)
        
        

#        icon_path = ':/plugins/geotools/icon.png'
#        self.add_action(
#            icon_path,
#            text=self.tr(u'GeoTools'),
#            callback=self.run,
#            parent=self.iface.mainWindow())

    def onReadProject(self):
        self.drillManager.readProjectData()
        
    def onProjectChangeDriveLetter(self):
        dlg = ChangeDriveLetterDialog(self)
        dlg.show()
        result = dlg.exec_()
        if result:
            pf = dlg.cbProject.filePath()
            oldDrive = dlg.leOriginalDrive.text()
            newDrive = dlg.leNewDrive.text()
            data = str
            
            if len(oldDrive) > 0 and len(newDrive) > 0:
                with open(pf, 'r') as pfile:
                    data = pfile.read()
                    
                data = data.replace("file:///"+oldDrive[0]+":/", "file:///"+newDrive[0]+":/")
                with open(pf, 'w') as pfile:
                    pfile.write(data)
                
        dlg.close()
        
    def onReverseLine(self):
        layer = self.iface.mapCanvas().currentLayer()
        for feature in layer.selectedFeatures():
            geom = feature.geometry()
            nodes = geom.asPolyline()
            nodes.reverse() 
            newgeom = QgsGeometry.fromPolylineXY(nodes)
            layer.changeGeometry(feature.id(),newgeom)
            layer.triggerRepaint()
        
    def onRasterTransparentWhite(self):
        self.rasterTransparent(255, 255, 255)

    def onRasterTransparentBlack(self):
        self.rasterTransparent(0, 0, 0)

    def rasterTransparent(self, r, g, b):
        tr_list = []
        ltr = QgsRasterTransparency.TransparentThreeValuePixel()
        ltr.red = r
        ltr.green = g
        ltr.blue = b
        ltr.percentTransparent = 100
        tr_list.append(ltr)
        
        if Qgis.QGIS_VERSION_INT < 30000 :
            sl = self.iface.legendInterface().selectedLayers(True)
        else:
            sl = self.iface.layerTreeView().selectedLayers()
        for layer in sl:
        	raster_transparency  = layer.renderer().rasterTransparency()
        	raster_transparency.setTransparentThreeValuePixelList(tr_list)
        	layer.triggerRepaint()

    def readProjectData(self):
        pass

    def writeProjectData(self):
        pass
    
    def unload(self):
        self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        del self.menu
        # remove the toolbar
        del self.toolbar


    def run(self):
        pass
