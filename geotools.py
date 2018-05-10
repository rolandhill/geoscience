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
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QMenu, QDialog

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

#from scipy import interpolate

# Initialize Qt resources from file resources.py
from .resources import *
from .drillsetup_dialog import DrillSetupDialog
from .ChangeDriveLetter_dialog import ChangeDriveLetterDialog

import os.path

def getLayerByName(name):
    layer=None
    layerList = QgsProject.instance().mapLayersByName(name)
    if len(layerList) > 0:
        layer = layerList[0]

    return layer

def getFieldByName(layer, name):
    field = QgsField()
    if layer is not None and layer.isValid() and name != "None":
        dp = layer.dataProvider()
        index = dp.fieldNameIndex(name)
        if index > -1:
            field = dp.field(index)
    return field
    
def readProjectLayer(entry):
    name, ok = QgsProject.instance().readEntry ("GeoTools", entry)
    if ok and name != "None":
        layer = getLayerByName(name)
        if layer != None:
            return layer
        else:
            return None
    else:
        return None

def writeProjectLayer(entry, layer):
    if layer is not None:
        QgsProject.instance().writeEntry("GeoTools", entry, layer.name())
    else:
        QgsProject.instance().writeEntry("GeoTools", entry, "None")
        
def readProjectField(layer, entry):
    name, ok = QgsProject.instance().readEntry ("GeoTools", entry)
    return name

def writeProjectField(entry, field):
    QgsProject.instance().writeEntry("GeoTools", entry, field)
        
def readProjectNum(entry, default):
    val, ok = QgsProject.instance().readNumEntry ("GeoTools", entry)
    if ok:
        return val
    else:
        return default
    
def readProjectBool(entry, default):
    val, ok = QgsProject.instance().readBoolEntry ("GeoTools", entry)
    if ok:
        return val
    else:
        return default

def writeProjectData(entry, val):
    QgsProject.instance().writeEntry("GeoTools", entry, val)

class DrillManager:
    def __init__(self):
        self.readProjectData()
    
    def onDrillSetup(self):
        dlg = DrillSetupDialog(self)
        dlg.show()
        result = dlg.exec_()
        if result:
            self.downDipNegative = dlg.checkDownDipNegative.isChecked()
            self.desurveyLength = dlg.sbDesurveyLength.value()
            self.defaultSectionWidth = dlg.teDefaultSectionWidth.text()
            self.defaultSectionStep = dlg.teDefaultSectionStep.text()
            self.collarLayer = dlg.lbCollarLayer.currentLayer()
            self.surveyLayer = dlg.lbSurveyLayer.currentLayer()
            self.dataLayer0 = dlg.lbDataLayer0.currentLayer()
            self.dataLayer1 = dlg.lbDataLayer1.currentLayer()
            self.dataLayer2 = dlg.lbDataLayer2.currentLayer()
            self.dataLayer3 = dlg.lbDataLayer3.currentLayer()
            self.collarId = dlg.fbCollarId.currentField()
            self.collarDepth = dlg.fbCollarDepth.currentField()
            self.collarEast = dlg.fbCollarEast.currentField()
            self.collarNorth = dlg.fbCollarNorth.currentField()
            self.collarElev = dlg.fbCollarElev.currentField()
            self.collarAz = dlg.fbCollarAz.currentField()
            self.collarDip = dlg.fbCollarDip.currentField()
            self.surveyId = dlg.fbSurveyId.currentField()
            self.surveyDepth = dlg.fbSurveyDepth.currentField()
            self.surveyAz = dlg.fbSurveyAz.currentField()
            self.surveyDip = dlg.fbSurveyDip.currentField()
            self.dataId0 = dlg.fbDataId0.currentField()
            self.dataFrom0 = dlg.fbDataFrom0.currentField()
            self.dataTo0 = dlg.fbDataTo0.currentField()
            self.dataId1 = dlg.fbDataId1.currentField()
            self.dataFrom1 = dlg.fbDataFrom1.currentField()
            self.dataTo1 = dlg.fbDataTo1.currentField()
            self.dataId2 = dlg.fbDataId2.currentField()
            self.dataFrom2 = dlg.fbDataFrom2.currentField()
            self.dataTo2 = dlg.fbDataTo2.currentField()
            self.dataId3 = dlg.fbDataId3.currentField()
            self.dataFrom3 = dlg.fbDataFrom3.currentField()
            self.dataTo3 = dlg.fbDataTo3.currentField()
            
            self.writeProjectData()
        dlg.close()

    def onDrillDisplayTraces(self):
        pass

    def onDesurveyData(self):
        self.desurveyData()

    def onDrillCreateSection(self):
        pass

    def desurveyData(self):
        # Build Collar array (Id, east, north, elev, eoh, az, dip)
        count = self.collarLayer.featureCount()
        self.arrCollarId = [str] * count
        self.arrCollarEast = [float] * count
        self.arrCollarNorth = [float] * count
        self.arrCollarElev = [float] * count
        self.arrCollarDepth = [float] * count
        self.arrCollarAz = [float] * count
        self.arrCollarDip = [float] * count
        
        # Build Survey array (Id, depth, az, dip)
        
        # Create new layer for the desurveyed 3D coordinates. PolyLine, 1 row per collar, 1 attribute (Id)
        
        #Loop through collars
            #Build array of surveys for this collar, including the top az and dip in collar layer. Repeat last survey at EOH.
            
            #Calculate the azimuth and dip splines
            
            #Build drill trace every desurveyLength to EOH
        
        pass
    
    def readProjectData(self):
        self.defaultSectionWidth = readProjectNum("DefaultSectionWidth", 50)
        self.defaultSectionStep= readProjectNum("DefaultSectionStep", 50)
        self.desurveyLength = readProjectNum("DesurveyLength", 1)
        self.downDipNegative = readProjectBool("DownDipNegative", True)
        self.collarLayer = readProjectLayer("CollarLayer")
        self.surveyLayer = readProjectLayer("SurveyLayer")
        self.dataLayer0 = readProjectLayer("DataLayer0")
        self.dataLayer1 = readProjectLayer("DataLayer1")
        self.dataLayer2 = readProjectLayer("DataLayer2")
        self.dataLayer3 = readProjectLayer("DataLayer3")
        self.collarId = readProjectField(self.collarLayer, "CollarID")
        self.collarDepth = readProjectField(self.collarLayer, "CollarDepth")
        self.collarEast = readProjectField(self.collarLayer, "CollarEast")
        self.collarNorth = readProjectField(self.collarLayer, "CollarNorth")
        self.collarElev = readProjectField(self.collarLayer, "CollarElev")
        self.collarAz = readProjectField(self.collarLayer, "CollarAz")
        self.collarDip = readProjectField(self.collarLayer, "CollarDip")
        self.surveyId = readProjectField(self.surveyLayer, "SurveyID")
        self.surveyDepth = readProjectField(self.surveyLayer, "SurveyDepth")
        self.surveyAz = readProjectField(self.surveyLayer, "SurveyAz")
        self.surveyDip = readProjectField(self.surveyLayer, "SurveyDip")
        self.dataId0 = readProjectField(self.dataLayer0, "DataID0")
        self.dataFrom0 = readProjectField(self.dataLayer0, "DataFrom0")
        self.dataTo0 = readProjectField(self.dataLayer0, "DataTo0")
        self.dataId1 = readProjectField(self.dataLayer1, "DataID1")
        self.dataFrom1 = readProjectField(self.dataLayer1, "DataFrom1")
        self.dataTo1 = readProjectField(self.dataLayer1, "DataTo1")
        self.dataId2 = readProjectField(self.dataLayer2, "DataID2")
        self.dataFrom2 = readProjectField(self.dataLayer2, "DataFrom2")
        self.dataTo2 = readProjectField(self.dataLayer2, "DataTo2")
        self.dataId3 = readProjectField(self.dataLayer3, "DataID3")
        self.dataFrom3 = readProjectField(self.dataLayer3, "DataFrom3")
        self.dataTo3 = readProjectField(self.dataLayer3, "DataTo3")

    def writeProjectData(self):
        writeProjectData("DefaultSectionWidth", self.defaultSectionWidth)
        writeProjectData("DefaultSectionStep", self.defaultSectionStep)
        writeProjectData("DesurveyLength", self.desurveyLength)
        writeProjectData("DownDepthNegative", self.downDipNegative)
        writeProjectLayer("CollarLayer", self.collarLayer)
        writeProjectLayer("SurveyLayer", self.surveyLayer)
        writeProjectLayer("DataLayer0", self.dataLayer0)
        writeProjectLayer("DataLayer1", self.dataLayer1)
        writeProjectLayer("DataLayer2", self.dataLayer2)
        writeProjectLayer("DataLayer3", self.dataLayer3)
        writeProjectField("CollarID", self.collarId)
        writeProjectField("CollarDepth", self.collarDepth)
        writeProjectField("CollarEast", self.collarEast)
        writeProjectField("CollarNorth", self.collarNorth)
        writeProjectField("CollarElev", self.collarElev)
        writeProjectField("CollarAz", self.collarAz)
        writeProjectField("CollarDip", self.collarDip)
        writeProjectField("SurveyID", self.surveyId)
        writeProjectField("SurveyDepth", self.surveyDepth)
        writeProjectField("SurveyAz", self.surveyAz)
        writeProjectField("SurveyDip", self.surveyDip)
        writeProjectField("DataID0", self.dataId0)
        writeProjectField("DataFrom0", self.dataFrom0)
        writeProjectField("DataTo0", self.dataTo0)
        writeProjectField("DataID1", self.dataId1)
        writeProjectField("DataFrom1", self.dataFrom1)
        writeProjectField("DataTo1", self.dataTo1)
        writeProjectField("DataID2", self.dataId2)
        writeProjectField("DataFrom2", self.dataFrom2)
        writeProjectField("DataTo2", self.dataTo2)
        writeProjectField("DataID3", self.dataId3)
        writeProjectField("DataFrom3", self.dataFrom3)
        writeProjectField("DataTo3", self.dataTo3)

    
""" Main Class"""    
class GeoTools:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'GeoTools_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        self.drillManager = DrillManager()

        self.readProjectData()
        
        # Declare instance attributes
        self.actions = []
        #self.menu = self.tr(u'&GeoTools')
        # TODO: We are going to let the user set this up in a future iteration
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
                    
                #data = data.replace("D:", "G:")
                #iface.messageBar().pushMessage("Debug", "Data: " + data, level=Qgis.Info)
                data = data.replace("file:///"+oldDrive[0]+":/", "file:///"+newDrive[0]+":/")
                with open(pf, 'w') as pfile:
                    pfile.write(data)
                
        dlg.close()
        
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
