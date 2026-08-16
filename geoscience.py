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
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, QUrl
from qgis.PyQt.QtGui import QIcon, QDesktopServices
from qgis.PyQt.QtWidgets import QAction, QMenu, QDialog, QApplication, QInputDialog

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

# Initialize Qt resources from file resources.py
from .resources import *

# from .ChangeDriveLetter_dialog import ChangeDriveLetterDialog
from .DrillManager import *
from .localgrid_dialog import LocalGridDialog
from .SI_Link import SI_Link, DEFAULT_PORT

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

        # Spatial Integration link. Created on first use so that merely loading the plugin
        # never opens a socket.
        self.silink = None

        # Canvas layers whose change signals are currently connected. Only populated
        # while the Spatial Integration link runs, since nothing else needs the notifications.
        self._watchedLayers = []

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
        
        action = self.menuDrill.addAction(QIcon(self.plugin_dir + "/icon/DrillPoints.png"), "Downhole Points...")
        action.triggered.connect(self.drillManager.onDownholePoints)
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
        
        # Create Spatial Integration link menu.
        self.menuTileServer = self.menu.addMenu("Spatial Integration Link")

        self.actionTileServerStart = self.menuTileServer.addAction("Start Link")
        self.actionTileServerStart.triggered.connect(self.onStartTileServer)
        self.actions.append(self.actionTileServerStart)

        self.actionTileServerStop = self.menuTileServer.addAction("Stop Link")
        self.actionTileServerStop.triggered.connect(self.onStopTileServer)
        self.actions.append(self.actionTileServerStop)

        self.actionTileServerCopyUrl = self.menuTileServer.addAction("Copy Connection String")
        self.actionTileServerCopyUrl.triggered.connect(self.onCopyTileServerUrl)
        self.actions.append(self.actionTileServerCopyUrl)

        self.menuTileServer.addSeparator()

        self.actionTileServerPort = self.menuTileServer.addAction("Set Port...")
        self.actionTileServerPort.triggered.connect(self.onSetTileServerPort)
        self.actions.append(self.actionTileServerPort)

        self.updateTileServerActions()

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

    def tileServerPort(self):
        """
        The port the Spatial Integration link should listen on, as saved with the project.
        """
        return readProjectNum("TileServerPort", DEFAULT_PORT)

    def isTileServerRunning(self):
        """
        Returns True if the Spatial Integration link is currently listening.
        """
        return self.silink is not None and self.silink.isRunning()

    def updateTileServerActions(self):
        """
        Enable only the server actions that make sense for the current state.
        """
        running = self.isTileServerRunning()
        self.actionTileServerStart.setEnabled(not running)
        self.actionTileServerStop.setEnabled(running)
        self.actionTileServerCopyUrl.setEnabled(running)

    def onStartTileServer(self):
        """
        Start serving the visible canvas layers as XYZ tiles on localhost.
        """
        if self.silink is None:
            # Serve exactly what the canvas shows: already filtered by visibility and
            # in render order, so tiles match what the user sees.
            self.silink = SI_Link(lambda: self.iface.mapCanvas().layers())

        port = self.tileServerPort()
        try:
            self.silink.start(port)
        except RuntimeError as e:
            self.iface.messageBar().pushCritical("Geoscience", str(e))
            return

        writeProjectData("TileServerPort", port)
        self._connectTileServerWatches()
        self.iface.messageBar().pushSuccess("Geoscience", "Spatial Integration link running at %s" % self.silink.urlTemplate())
        self.updateTileServerActions()

    def onStopTileServer(self):
        """
        Stop the Spatial Integration link.
        """
        self._disconnectTileServerWatches()
        if self.silink is not None:
            self.silink.stop()
        self.updateTileServerActions()

    def onCopyTileServerUrl(self):
        """
        Put the XYZ URL template on the clipboard, ready to paste into the client
        application as a tile source.
        """
        if not self.isTileServerRunning():
            return
        url = self.silink.urlTemplate()
        QApplication.clipboard().setText(url)
        self.iface.messageBar().pushInfo("Geoscience", "Copied %s" % url)

    def onSetTileServerPort(self):
        """
        Ask for the port the Spatial Integration link should listen on and save it with
        the project. A running link is restarted so that the new port takes effect now
        rather than at the next start.
        """
        current = self.tileServerPort()
        # Ports below 1024 are privileged, so they would fail to bind rather than be
        # merely a poor choice.
        port, ok = QInputDialog.getInt(self.iface.mainWindow(), "Spatial Integration Link",
                                       "Listen on 127.0.0.1 port:", current, 1024, 65535)
        if not ok or port == current:
            return

        writeProjectData("TileServerPort", port)

        if self.isTileServerRunning():
            self.onStopTileServer()
            self.onStartTileServer()
        else:
            self.iface.messageBar().pushInfo("Geoscience", "Spatial Integration link port set to %d" % port)

    def _connectTileServerWatches(self):
        """
        Watch the canvas for anything that changes what the tiles should look like, so
        the client can notice and re-request them.
        """
        self.iface.mapCanvas().layersChanged.connect(self.onCanvasLayersChanged)
        self._rewireLayerWatches()

    def _disconnectTileServerWatches(self):
        """
        Drop the canvas watches. Safe to call when they were never connected.
        """
        try:
            self.iface.mapCanvas().layersChanged.disconnect(self.onCanvasLayersChanged)
        except (TypeError, RuntimeError):
            pass
        self._clearLayerWatches()

    def _clearLayerWatches(self):
        """
        Disconnect the per-layer watches and forget the layers.
        """
        for layer in self._watchedLayers:
            try:
                layer.repaintRequested.disconnect(self.onTileSourceChanged)
                layer.styleChanged.disconnect(self.onTileSourceChanged)
            except (TypeError, RuntimeError):
                # Never connected, or the layer has been removed and its C++ object
                # already deleted. Either way there is nothing left to disconnect.
                pass
        self._watchedLayers = []

    def _rewireLayerWatches(self):
        """
        Re-attach the per-layer watches to the current canvas layers.

        The layers are watched individually rather than through the canvas as a whole:
        the canvas repaints on pan and zoom too, which changes no tile and would have
        the client refreshing constantly for nothing.
        """
        self._clearLayerWatches()

        for layer in self.iface.mapCanvas().layers():
            # repaintRequested covers edits and most symbology; styleChanged catches the
            # rest, including labeling.
            layer.repaintRequested.connect(self.onTileSourceChanged)
            layer.styleChanged.connect(self.onTileSourceChanged)
            self._watchedLayers.append(layer)

    def onCanvasLayersChanged(self):
        """
        The canvas layer set changed: a layer was added, removed or toggled.
        """
        self._rewireLayerWatches()
        self.onTileSourceChanged()

    def onTileSourceChanged(self):
        """
        Something that affects the rendered map changed. Tell the Spatial Integration link.
        """
        if self.silink is not None:
            self.silink.bump()

    def onReadProject(self):
        """
        Read project data.
        """
        self.drillManager.readProjectData()

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
        dlg.exec()
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
        # Release the listening socket, or a reload leaves the port bound.
        self._disconnectTileServerWatches()
        if self.silink is not None:
            self.silink.stop()
            self.silink = None

        # Undo the connection made in initGui(), otherwise a reload stacks a duplicate
        # connection and keeps this instance alive.
        try:
            QgsProject.instance().readProject.disconnect(self.onReadProject)
        except TypeError:
            pass

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
