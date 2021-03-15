# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Geoscience
                                 A QGIS plugin
 Tools for Geoscience & Exploration
                              -------------------
        begin                : 2018-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Roland Hill / MMG
        email                : roland.hill@mmg.com
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices
from PyQt5.QtWidgets import QAction, QMenu, QDialog

from qgis.core import *
from qgis.utils import *
from qgis.gui import *


# Initialize Qt resources from file resources.py
from .resources import *
from .drill.drillManager import *
from .gui.localGrid_dialog import localGridDialog

import os

""" Main Class"""    
class Geoscience:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface

        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(self.plugin_dir, 'i18n', 'Geoscience_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Initiate the DrillManager to handle all drill related operations
        self.drillManager = drillManager()

        # Read all saved Geoscience parameters from the QGIS project file
        self.readProjectData()
        
        # Declare instance attributes
        self.actions = []
        self.toolbar = self.iface.addToolBar(u'Geoscience')
        self.toolbar.setObjectName(u'Geoscience')
        

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
        return QCoreApplication.translate('Geoscience', message)


    def initGui(self):
        # Respond to signal so that we read saved parameters every time a Project is loaded
        QgsProject.instance().readProject.connect(self.onReadProject)

        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        actions = self.iface.mainWindow().menuBar().actions()
        """ Create main menu."""
        lastAction = actions[-1]
        self.menu = QMenu( u'&Geoscience', self.iface.mainWindow().menuBar() )
        self.iface.mainWindow().menuBar().insertMenu( lastAction, self.menu )
        
        """Create Drill menu."""
        self.menuDrill = self.menu.addMenu("Drilling")

        self.menuDb = self.menuDrill.addMenu("Database")
        self.menuAdd = self.menuDrill.addMenu("Add")

        action = self.menuDb.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "New")
        action.triggered.connect(self.drillManager.onNewDb)
        action.setEnabled(True)
#        self.toolbar.addAction(action)
#        self.actions.append(action)

        action = self.menuDb.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "Open")
        action.triggered.connect(self.drillManager.onOpenDb)
        action.setEnabled(True)

        action = self.menuDb.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "Close")
        action.triggered.connect(self.drillManager.onCloseDb)
        action.setEnabled(True)


        action = self.menuAdd.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "Collars")
        action.triggered.connect(self.drillManager.onAddCollars)
        action.setEnabled(True)
#        self.toolbar.addAction(action)
#        self.actions.append(action)

        action = self.menuAdd.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "Surveys")
        action.triggered.connect(self.drillManager.onAddSurveys)
        action.setEnabled(True)

        action = self.menuAdd.addAction(QIcon(self.plugin_dir + "/icon/DrillSetup.png"), "Downhole Intervals")
        action.triggered.connect(self.drillManager.onAddDownholeIntervals)
        action.setEnabled(True)

        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/Desurvey.png"), "Desurvey Holes...")
        action.triggered.connect(self.drillManager.onDesurveyHole)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)

#        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillPlan.png"), "Add Downhole Intervals...")
#        action.triggered.connect(self.drillManager.onDownholeData)
#        action.setEnabled(True)
#        self.toolbar.addAction(action)
#        self.actions.append(action)
        
        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillSection.png"), "Section Manager...")
        action.triggered.connect(self.drillManager.onDrillSectionManager)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)

        self.toolbar.addSeparator()
        
        """Create Vector menu."""
        self.menuVector = self.menu.addMenu("Vector")

        action = self.menuVector.addAction(QIcon(self.plugin_dir + "/icon/ReverseLine.png"), "Reverse Line Direction")
        action.triggered.connect(self.onReverseLine)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        
        """Create Raster menu."""
        self.menuRaster = self.menu.addMenu("Raster")

        action = self.menuRaster.addAction(QIcon(self.plugin_dir + "/icon/WhiteTransparent.png"), "Transparent White")
        action.triggered.connect(self.onRasterTransparentWhite)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        
        action = self.menuRaster.addAction(QIcon(self.plugin_dir + "/icon/BlackTransparent.png"), "Transparent Black")
        action.triggered.connect(self.onRasterTransparentBlack)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        
        """Other choices."""
        action = self.menu.addAction(QIcon(self.plugin_dir + "/icon/LocalGrid.png"), "Create Local CRS...")
        action.triggered.connect(self.onCreateLocalCRS)
        action.setEnabled(True)
        # self.toolbar.addAction(action)
        self.actions.append(action)
        
        """Create Help menu."""
        action = self.menu.addAction(QIcon(self.plugin_dir + "/icon/Help.png"), "Help")
        action.triggered.connect(self.onHelp)
        action.setEnabled(True)
        self.actions.append(action)
        
        
    def onHelp(self):
        docDir = "https://www.spatialintegration.com/"
#        docDir = "file:///" + self.plugin_dir + "/index.html"
#        docDir = docDir.replace("\\", "/")
        QDesktopServices.openUrl(QUrl(docDir))

    def onReadProject(self):
        self.drillManager.readProjectData()
       
    # Reverse the node sequence in all selected lines on hte current layer
    # Useful if you are using a non-symmetric line style (eg Normal Fault)
    def onReverseLine(self):
        # Get the currently selected layer
        layer = self.iface.mapCanvas().currentLayer()
        
        #Loop through all selected features
        for feature in layer.selectedFeatures():
            geom = feature.geometry()
            wkbType = geom.wkbType()
            if wkbType == QgsWkbTypes.MultiLineString:
                for nodes in geom.asMultiPolygon():
                    nodes.reverse()
            else:
                
                # Get the geometry as a Polyline. This is 2D only
                # ToDo: Convert to 3D
                nodes = geom.asPolyline()
                nodes.reverse() 
                newgeom = QgsGeometry.fromPolylineXY(nodes)
                # Put the new geometry into the feature
                layer.changeGeometry(feature.id(),newgeom)
            
            # Refresh the screen
            layer.triggerRepaint()
        
    # Set the white pixels of all selected raster layers to be transparent
    def onRasterTransparentWhite(self):
        self.rasterTransparent(255, 255, 255)

    # Set the black pixels of all selected raster layers to be transparent
    def onRasterTransparentBlack(self):
        self.rasterTransparent(0, 0, 0)

    # Set the pixels of the supplied colour of all selected raster layers to be transparent
    def rasterTransparent(self, r, g, b):
        # Create a list of colours to make transparent
        tr_list = []
        # Create a transparent pixel value and add it to the list
        ltr = QgsRasterTransparency.TransparentThreeValuePixel()
        ltr.red = r
        ltr.green = g
        ltr.blue = b
        ltr.percentTransparent = 100
        tr_list.append(ltr)
        
        # Get all selected layers
        if Qgis.QGIS_VERSION_INT < 30000 :
            sl = self.iface.legendInterface().selectedLayers(True)
        else:
            sl = self.iface.layerTreeView().selectedLayers()
        # Loop through the layers
        for layer in sl:
            # Get the renderer and set the transparent pixel list to ours
        	raster_transparency  = layer.renderer().rasterTransparency()
        	raster_transparency.setTransparentThreeValuePixelList(tr_list)
            # Repaint the screen
        	layer.triggerRepaint()

    def onCreateLocalCRS(self):
        self.createLocalCRS()

    def createLocalCRS(self):
        dlg = LocalGridDialog(self)
        dlg.exec_()
        dlg.close()

    def readProjectData(self):
        pass

    def writeProjectData(self):
        pass
    
    # Remove interface items when the plugin closes
    def unload(self):
        self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        del self.menu
        # remove the toolbar
        del self.toolbar

    # Default method called to do something. 
    # We wait for signals from the menus and toolbar
    def run(self):
        pass
