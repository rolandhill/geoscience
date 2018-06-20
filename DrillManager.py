# -*- coding: utf-8 -*-
"""
/***************************************************************************
 DrillManager
                              -------------------
        begin                : 2018-04-13
        git sha              : $Format:%H$
        copyright            : (C) 2018 by Roland Hill / MMG
        email                : roland.hill@mmg.com
 ***************************************************************************/
"""
from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QAction, QDialog

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
import numpy as np

from .rotation_matrix_3d import rotation_from_angles

# Initialize Qt resources from file resources.py
from .resources import *
from .drillsetup_dialog import DrillSetupDialog
from .spline import spline

import os.path
import copy

class Collar:
    id = ''
    east = 0.0
    north = 0.0
    elev = 0.0
    depth = 0.0
    az = 0.0
    dip = 0.0

class Survey:
    id = ''
    depth = 0.0
    az = 0.0
    dip = 0.0
    
class Surveys:
    depth = 0.0
    az = 0.0
    dip = 0.0
    
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
        # Project data is normally read in response to a readProject signal.
        # We also do it here for when the plugin is loaded other than at startup
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
        logFile = open("D:\hillr\Data\DrillTest\log.txt",'w')
        
        dp = self.collarLayer.dataProvider()
        idxCollarId = dp.fieldNameIndex(self.collarId)
        idxCollarEast = dp.fieldNameIndex(self.collarEast)
        idxCollarNorth = dp.fieldNameIndex(self.collarNorth)
        idxCollarElev = dp.fieldNameIndex(self.collarElev)
        idxCollarDepth = dp.fieldNameIndex(self.collarDepth)
        idxCollarAz = dp.fieldNameIndex(self.collarAz)
        idxCollarDip = dp.fieldNameIndex(self.collarDip)

        # Are we using azimtuhs and dips from the collar file?
        useCollarAzDip = (idxCollarAz > -1) and (idxCollarDip > -1)
        
        # Build Collar array (Id, east, north, elev, eoh, az, dip)
        numCollars = self.collarLayer.featureCount()
        arrCollar = []

        for feature in self.collarLayer.getFeatures():
            # get the feature's attributes
            attrs = feature.attributes()
            c = Collar()
            # Check all the data is valid
            c.id = attrs[idxCollarId].strip()
            c.east = attrs[idxCollarEast]
            c.north = attrs[idxCollarNorth]
            c.elev = attrs[idxCollarElev]
            c.depth = attrs[idxCollarDepth]
            if (not c.id) or (not c.east) or (not c.north) or (not c.elev) or (not c.depth):
                continue
            if useCollarAzDip:
                c.az = attrs[idxCollarAz]
                if not c.az:
                    c.az = 0.0
                c.dip = attrs[idxCollarDip]
                if not c.dip:
                    c.dip = -90 if self.downDipNegative else 90
            arrCollar.append(c)
            
        # Build Survey array (Id, depth, az, dip)
        numSurveys = self.surveyLayer.featureCount()
        arrSurvey = []

        dp = self.surveyLayer.dataProvider()
        idxSurveyId = dp.fieldNameIndex(self.surveyId)
        idxSurveyDepth = dp.fieldNameIndex(self.surveyDepth)
        idxSurveyAz = dp.fieldNameIndex(self.surveyAz)
        idxSurveyDip = dp.fieldNameIndex(self.surveyDip)
        
        for feature in self.surveyLayer.getFeatures():
            # get the feature's attributes
            attrs = feature.attributes()
            s = Survey()
            s.id = attrs[idxSurveyId].strip()
            s.depth = attrs[idxSurveyDepth]
            s.az = attrs[idxSurveyAz]
            s.dip = attrs[idxSurveyDip]
            arrSurvey.append(s)
            
        # Create new layer for the desurveyed 3D coordinates. PolyLine, 1 row per collar, 1 attribute (Id)
        self.createDesurveyLayer()
#        
        #Loop through collars
        for collar in arrCollar:
            if not collar.id:
                continue
#        for collar in range(0, 1):
#            logFile.write("Count/2: %d %d\n" % (count, count2))
#            logFile.write("%s \n" % (arrCollar[collar].id))
            #Build array of surveys for this collar, including the top az and dip in collar layer. Repeat last survey at EOH.
            surveys = []
            for survey in arrSurvey:
                if survey.id == collar.id:
                    s = Surveys()
                    s.depth = survey.depth
                    s.az = survey.az
                    s.dip = survey.dip
                    surveys.append(s)

#            if collar.id == "DR351":
#                logFile.write("Hole number DR351 ***********\n")
#                for s in surveys:
#                    logFile.write("%f\n" % (s.depth))
#                logFile.flush()
#                
            # If the az and dip from the collar are to be used, then insert them at depth 0.0
            if len(surveys) == 0 and useCollarAzDip:
                s = Surveys()
                s.depth = 0.0
                s.az = collar.az
                s.dip = collar.dip
                surveys.append(s)
            
            # If there are no surveys, then the hole is vertical
            if len(surveys) == 0:
                s = Surveys()
                s.depth = 0.0
                s.az = 0.0
                s.dip = -90 if self.downDipNegative else 90
                surveys.append(s)
                
            # Sort the surveys array by depth
            surveys.sort(key = lambda x: x.depth)                        
            
            # If surveys exist, then we shouldn't use the az & dip from the collar file, so overwrite them with the first survey.                    
            if not surveys[0].depth == 0.0:
                s = surveys[0]
                s.depth = 0.0
                surveys.insert(0, s)
                
            # If the last survey isn't at the end of hole, then repeat the last one at eoh
            if len(surveys) > 0 and surveys[-1].depth < collar.depth:
                s = Surveys()
                s.depth = collar.depth
                s.az = surveys[-1].az
                s.dip = surveys[-1].dip
                surveys.append(s)
                
            # If there are only 2 surveys, then we add a third in the middle as an average.
            # This way we can use the spline.
            if len(surveys) == 2:
                s = Surveys()
                s.depth = collar.depth * 0.5
                s.az = (surveys[0].az + surveys[1].az) * 0.5
                s.dip = (surveys[0].dip + surveys[1].dip) * 0.5
                surveys.insert(1, s)
                
            #Build drill trace every desurveyLength to EOH
#            success = False
            logFile.write("%s \n" % (collar.id))
            logFile.flush()

            sz = int(collar.depth / self.desurveyLength) + 1
            if collar.depth % self.desurveyLength > 0.0:
                sz += 1
            xs = []
            depth = 0.0
            for d in range(0, sz):
                xs.append(depth)
                depth += self.desurveyLength
            if xs[-1] > collar.depth:
                xs[-1] = collar.depth
                
            #Calculate the azimuth and dip splines
            x = []
            az = []
            dip = []
            for s in surveys:
                x.append(s.depth)
                az.append(s.az)
                dip.append(s.dip)

            try:            
                azs = spline(x, az, xs)
                dips = spline(x, dip, xs)
            except:                
                pass
                for val in x:
                    logFile.write("%f\n" % (val))
                logFile.flush()
                    
                    
            # Create linestring
            feature = QgsFeature()
            pointList = []
            pointList.append(QgsPoint(collar.east, collar.north, collar.elev))
            count = 1
            for i in range(0, len(xs)):
                dip = dips[count] if self.downDipNegative else (-1.0 * dips[count])
                rot = rotation_from_angles([dip/180.0*np.pi, azs[count]/180.0*np.pi, 0.0], 'XYZ')
                offset = rot.dot(np.array([0.0, self.desurveyLength, 0.0]))
                p0 = pointList[count-1]
                pointList.append(QgsPoint(p0.x() + offset[0], p0.y() + offset[1], p0.z() + offset[2]))
                count =+ 1
            feature.setGeometry(QgsGeometry.fromPolyline(pointList))
            feature.setAttributes([collar.id, self.desurveyLength])
            self.traceLayer.startEditing()
            self.traceLayer.addFeature(feature)
                
            self.traceLayer.commitChanges()
            
    def createDesurveyLayer(self):
        #Find CRS of collar layer
        crs = self.collarLayer.sourceCrs()
        
        #Create a new memory layer
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "gt_Trace", "memory")
        layer.setCrs(crs)
        dp = layer.dataProvider()
        dp.addAttributes([
            QgsField("CollarID",  QVariant.String, "string", 16),
            QgsField("SegLength",  QVariant.Double, "double", 5, 2)
            ])
        layer.updateFields() # tell the vector layer to fetch changes from the provider
#        QgsProject.instance().addMapLayer(layer)

        # Build the new filename
        base, ext = os.path.splitext(self.collarLayer.dataProvider().dataSourceUri())
        fileName = base + "_Trace"
        if fileName.startswith("file:///"):
            fileName = fileName[8:]

        #Save memory layer to shapefile
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", crs, "ESRI Shapefile")
#        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", crs, "GPKG")
#        if error != QgsVectorFileWriter.NoError:
            #msg = "[Index: {0}]".format(index)
#            iface.messageBar().pushMessage("File Error", "Trace layer failed to write to disc!", level=Qgis.Critical)
#            iface.messageBar().pushMessage("File Error", "Trace layer failed to write to disc!: "+ str(error), level=Qgis.Critical)
            
        #Load the newly created layer from disk
#        fileName = QFileDialog.getSaveFileName(self, 'New Point Table Filename', self.lastDir, '*.shp')
        label = os.path.splitext(os.path.basename(fileName))[0]
#        iface.messageBar().pushMessage("Debug", "Label: " + label, level=Qgis.Info)
        # Remove trace layer from project if it already exists
        layer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(layer)
        self.traceLayer = QgsVectorLayer(fileName+".shp", label, "ogr")
#        if self.traceLayer.isValid():
        QgsProject.instance().addMapLayer(self.traceLayer)
#        else:
#            iface.messageBar().pushMessage("Layer Error", "Failed to create Trace layer: "+fileName, level=Qgis.Critical)
    
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

    
