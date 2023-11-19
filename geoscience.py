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

# from .ChangeDriveLetter_dialog import ChangeDriveLetterDialog
from .DrillManager import *
from .localgrid_dialog import LocalGridDialog

import os

class Geoscience:
    """
    Main class for the Geoscience plugin.
    """
    def __init__(self, iface):
        """
        Constructor for Geoscience class.

        Args:
            iface: QGIS interface object.
        """
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
        self.drillManager = DrillManager()

        # Read all saved Geoscience parameters from the QGIS project file
        self.readProjectData()
        
        # Declare instance attributes
        self.actions = []
        self.toolbar = self.iface.addToolBar(u'Geoscience')
        self.toolbar.setObjectName(u'Geoscience')

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        Args:
        param message: String for translation.
        type message: str, QString

        Returns:
        Translated version of message.
        rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Geoscience', message)


    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Respond to signal so that we read saved parameters every time a Project is loaded
        QgsProject.instance().readProject.connect(self.onReadProject)

        actions = self.iface.mainWindow().menuBar().actions()

        # Create main menu.
        lastAction = actions[-1]
        self.menu = QMenu( u'&Geoscience', self.iface.mainWindow().menuBar() )
        self.iface.mainWindow().menuBar().insertMenu( lastAction, self.menu )
        
        # Create Drill menu.
        self.menuDrill = self.menu.addMenu("Drilling")

        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/Desurvey.png"), "Desurvey Holes...")
        action.triggered.connect(self.drillManager.onDesurveyHole)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)

        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillPlan.png"), "Downhole Data...")
        action.triggered.connect(self.drillManager.onDownholeData)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        
        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillStructure.png"), "Downhole Structure...")
        action.triggered.connect(self.drillManager.onDownholeStructure)
        action.setEnabled(True)
        self.actions.append(action)

        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillSection.png"), "Section Manager...")
        action.triggered.connect(self.drillManager.onDrillSectionManager)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        self.toolbar.addSeparator()
        
        # Create Vector menu.
        self.menuVector = self.menu.addMenu("Vector")

        action = self.menuVector.addAction(QIcon(self.plugin_dir + "/icon/ReverseLine.png"), "Reverse Line Direction")
        action.triggered.connect(self.onReverseLine)
        action.setEnabled(True)
        self.toolbar.addAction(action)
        self.actions.append(action)
        
        # Create Raster menu.
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
        
        # Other choices.
        action = self.menu.addAction(QIcon(self.plugin_dir + "/icon/LocalGrid.png"), "Create Local CRS...")
        action.triggered.connect(self.onCreateLocalCRS)
        action.setEnabled(True)
        self.actions.append(action)

        # Create Help menu.
        action = self.menu.addAction(QIcon(self.plugin_dir + "/icon/Help.png"), "Help")
        action.triggered.connect(self.onHelp)
        action.setEnabled(True)
        self.actions.append(action)
        
        
    def onHelp(self):
        """
        Open the help documentation in a web browser.
        """
        docDir = "https://www.spatialintegration.com/"
        QDesktopServices.openUrl(QUrl(docDir))

    def onReadProject(self):
        """
        Read project data.
        """
        self.drillManager.readProjectData()

    def onReverseLine(self):
        """
        Reverse the node sequence in all selected lines on the current layer.
        Useful if you are using a non-symmetric line style (eg Normal Fault).
        """
        # Get the currently selected layer
        layer = self.iface.mapCanvas().currentLayer()
        
        # Loop through all selected features
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

    def onRasterTransparentWhite(self):
        """
        Set the white pixels of all selected raster layers to be transparent.
        """
        self.rasterTransparent(255, 255, 255)

    def onRasterTransparentBlack(self):
        """
        Set the black pixels of all selected raster layers to be transparent.
        """
        self.rasterTransparent(0, 0, 0)

    def rasterTransparent(self, r, g, b):
        """
        Set the pixels of the supplied color of all selected raster layers to be transparent.

        Args:
            r (int): Red value.
            g (int): Green value.
            b (int): Blue value.
        """
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
        """
        Create a local Coordinate Reference System (CRS).
        """
        self.createLocalCRS()

    def createLocalCRS(self):
        """
        Create a local Coordinate Reference System (CRS).
        """
        dlg = LocalGridDialog(self)
        dlg.exec_()
        dlg.close()

    def readProjectData(self):
        """
        Read project data.
        """
        pass  # Placeholder for the method

    def writeProjectData(self):
        """
        Write project data.
        """
        pass  # Placeholder for the method

    def unload(self):
        """
        Remove interface items when the plugin closes.
        """
        self.iface.mainWindow().menuBar().removeAction(self.menu.menuAction())
        del self.menu

        # remove the toolbar
        del self.toolbar

    def run(self):
        """
        Default method called to do something.
        Wait for signals from the menus and toolbar
        """
        pass  # Placeholder for the method
