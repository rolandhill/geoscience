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
from PyQt5.QtWidgets import QAction, QDialog, QProgressBar, QProgressDialog, qApp

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
import numpy as np

from .quaternion import Quaternion

# Initialize Qt resources from file resources.py
from .resources import *
from .drillsetup_dialog import DrillSetupDialog
from .drilltrace_dialog import DrillTraceDialog

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
        try:
            QgsProject.instance().writeEntry("GeoTools", entry, layer.name())
        except:
            QgsProject.instance().writeEntry("GeoTools", entry, "None")
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
        
        self.openLogFile()

    def openLogFile(self):
        # Maintain a log file in case of data errors
#        base, ext = os.path.splitext(self.collarLayer.dataProvider().dataSourceUri())
        if self.collarLayer and self.collarLayer.isValid():
            fileName = self.collarLayer.dataProvider().dataSourceUri()
            if fileName.startswith("file:///"):
                fileName = fileName[8:]
            self.logFile = open(os.path.join(os.path.dirname(fileName), "GeoTools_DrillManager_log.txt"),'w')
            self.logFile.write("GeoTools - DrillManager log file\n")
            self.logFile.write("  Note: This file is overwritten each time you run GeoTools.\n")
            self.logFile.write("  Make a copy if you want to keep the results.\n")
            self.logFile.flush()

        
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
            
            self.writeProjectData()
            self.openLogFile()
        dlg.close()


    def onDrillDisplayTraces(self):
        dlg = DrillTraceDialog(self)
        dlg.show()
        result = dlg.exec_()
        if result:
            self.dataLayer = dlg.lbDataLayer.currentLayer()
            self.dataId = dlg.fbDataId.currentField()
            self.dataFrom = dlg.fbDataFrom.currentField()
            self.dataTo = dlg.fbDataTo.currentField()
            self.dataSuffix = dlg.teSuffix.text()
            self.dataFields = []
            for index in range(dlg.listFields.count()):
                if dlg.listFields.item(index).checkState():
                    self.dataFields.append(dlg.listFields.item(index).text())
                    
            self.writeProjectData()
        dlg.close()
        
        self.createDownholeTrace()
        
    def onDesurveyData(self):
        self.desurveyData()

    def onDrillCreateSection(self):
        pass

    def createDownholeTrace(self):
        self.logFile.write("\nCreating Trace Layer.\n")
        # Check that desurvey layer is available
        if not self.traceLayer.isValid() or not self.dataLayer.isValid():
            return
        
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setWindowTitle("Build Trace Layer")
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        pd.setMaximum(self.dataLayer.featureCount())
        pd.setValue(0)

        # Create memory layer
        layer = self.createDownholeLayer()

        # Get the fields from the data layer
        dp = self.dataLayer.dataProvider()
        idxId = dp.fieldNameIndex(self.dataId)
        idxFrom = dp.fieldNameIndex(self.dataFrom)
        idxTo = dp.fieldNameIndex(self.dataTo)
        idxAttList = []
        for name in self.dataFields:
            idx = dp.fieldNameIndex(name)
            idxAttList.append(idx)
        
        # Get the fields from the desurveyed trace layer
        tdp = self.traceLayer.dataProvider()
        idxTraceId = tdp.fieldNameIndex("CollarID")
        idxTraceSegLength = tdp.fieldNameIndex("SegLength")

        # Store the relevant desurveyed drill trace so that it's persistent between loops
        # This way we should be able to re-use it instead of re-fetching it.
        traceFeature = QgsFeature()
        currentTraceCollar = ""
        currentTraceSegLength = 1.0
        currentTracePolyline = None
        
        #Loop through downhole layer features
        updateInt = max(self.dataLayer.featureCount() ,int(self.dataLayer.featureCount()/100))
        for index, df in enumerate(self.dataLayer.getFeatures()):
            pd.setValue(index)
            if index%updateInt == 0:
                qApp.processEvents()
            feature = QgsFeature()

            # get the feature's attributes
            attrs = df.attributes()
            # Check all the data is valid
            dataId = attrs[idxId].strip()
            dataFrom = attrs[idxFrom]
            dataTo = attrs[idxTo]
            if (not dataId) or (not dataFrom) or (not dataTo):
                continue
            
            # Get the desurvey drill trace relevant to this collar
            if not currentTraceCollar == dataId:
                # Get the correct trace feature via a query
                query = '''"CollarID" = '%s' ''' % (dataId)
                selection = self.traceLayer.getFeatures(QgsFeatureRequest().setFilterExpression(query))
                if selection.isValid():
                    selection.nextFeature(traceFeature)
                    currentTraceCollar = dataId
                    currentTraceSegLength = traceFeature.attributes()[idxTraceSegLength]
                    # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                    # We therefore get a vertex iterator for the abstractGeometry and build our own list
                    vi = traceFeature.geometry().vertices()
                    currentTracePolyline = []
                    while vi.hasNext():
                        currentTracePolyline.append(vi.next())
#                    currentTracePolyline = traceFeature.geometry().asPolyline()
                else:
                    continue
                
            # Create line representing the downhole value using From and To
            pointList = []
            # Calculate indices spanning the from and to depths, then linearly interpolate a position
            i = dataFrom / currentTraceSegLength
            i0 = int(i)
            ratio = i - i0
            try:
                p0 = currentTracePolyline[i0]
                if ratio > 0.01:
                    p1 = currentTracePolyline[i0+1]
                    dx = (p1.x() - p0.x()) * ratio
                    dy = (p1.y() - p0.y()) * ratio
                    dz = (p1.z() - p0.z()) * ratio
                    pointList.append(QgsPoint(p0.x() + dx, p0.y() + dy, p0.z() + dz))
#                    pointList.append(QgsPoint(p0.x() + dx, p0.y() + dy, 0.0))
                else:
                    pointList.append(QgsPoint(p0.x(), p0.y(), p0.z()))
            except:
                self.logFile.write("! Error calculating 'From' index. Id: %s, From: %f\n" % (dataId, dataFrom))
                self.logFile.flush()
                continue
            
            i = dataTo / currentTraceSegLength
            i0 = int(i)
            ratio = i - i0
            try:
                p0 = currentTracePolyline[i0]
                if ratio > 0.01:
                    p1 = currentTracePolyline[i0+1]
                    dx = (p1.x() - p0.x()) * ratio
                    dy = (p1.y() - p0.y()) * ratio
                    dz = (p1.z() - p0.z()) * ratio
                    pointList.append(QgsPoint(p0.x() + dx, p0.y() + dy, p0.z() + dz))
#                    pointList.append(QgsPoint(p0.x() + dx, p0.y() + dy, 0.0))
                else:
                    pointList.append(QgsPoint(p0.x(), p0.y(), p0.z()))
            except:
                self.logFile.write("! Error calculating 'To' index. Id: %s, To: %f\n" % (dataId, dataTo))
                self.logFile.flush()
                continue
            
            feature.setGeometry(QgsGeometry.fromPolyline(pointList))

            # Create a list of the attributes to be included in new file
            attList = []
            for idx in idxAttList:
                attList.append(attrs[idx])

            attList.append(pointList[0].x())
            attList.append(pointList[0].y())
            attList.append(pointList[0].z())
            attList.append(pointList[1].x())
            attList.append(pointList[1].y())
            attList.append(pointList[1].z())

            feature.setAttributes(attList)

            layer.startEditing()
            layer.addFeature(feature)
            layer.commitChanges()
        
        # Build the new filename
        base, ext = os.path.splitext(self.traceLayer.dataProvider().dataSourceUri())
        fileName = base + "_%s" % (self.dataSuffix)
        if fileName.startswith("file:///"):
            fileName = fileName[8:]

        #Save memory layer to Geopackage file
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", self.traceLayer.sourceCrs(), layerOptions=['OVERWRITE=YES'])
            
        #Load the newly created layer from disk
        label = os.path.splitext(os.path.basename(fileName))[0]
        # Remove trace layer from project if it already exists
        oldLayer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(oldLayer)
        # Load the one we just saved
        layer = QgsVectorLayer(fileName+".gpkg", label)
        QgsProject.instance().addMapLayer(layer)
        
    def desurveyData(self):
        self.logFile.write("\nDesurveying data.\n")
        self.logFile.flush()
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        
        dp = self.collarLayer.dataProvider()
        idxCollarId = dp.fieldNameIndex(self.collarId)
        idxCollarEast = dp.fieldNameIndex(self.collarEast)
        idxCollarNorth = dp.fieldNameIndex(self.collarNorth)
        idxCollarElev = dp.fieldNameIndex(self.collarElev)
        idxCollarDepth = dp.fieldNameIndex(self.collarDepth)
        idxCollarAz = dp.fieldNameIndex(self.collarAz)
        idxCollarDip = dp.fieldNameIndex(self.collarDip)

        # Are we using azimuths and dips from the collar file?
        useCollarAzDip = (idxCollarAz > -1) and (idxCollarDip > -1)
        
        # Build Collar array (Id, east, north, elev, eoh, az, dip)
        numCollars = self.collarLayer.featureCount()
        arrCollar = []

        pd.setWindowTitle("Build Collar Array")
        pd.setMaximum(numCollars)
        pd.setValue(0)
        for index, feature in enumerate(self.collarLayer.getFeatures()):
            pd.setValue(index)
            # get the feature's attributes
            attrs = feature.attributes()
            c = Collar()
            # Check all the data is valid
            c.id = attrs[idxCollarId].strip()
            c.east = attrs[idxCollarEast]
            c.north = attrs[idxCollarNorth]
            c.elev = attrs[idxCollarElev]
            c.depth = attrs[idxCollarDepth]
            if (c.id==NULL) or (c.east==NULL) or (c.north==NULL) or (c.elev==NULL) or (c.depth==NULL):
                continue
            if useCollarAzDip:
                c.az = attrs[idxCollarAz]
                if c.az==NULL:
                    c.az = 0.0
                c.dip = attrs[idxCollarDip]
                if c.dip==NULL:
                    c.dip = -90 if self.downDipNegative else 90
            arrCollar.append(c)
            
        # Build Survey array (Id, depth, az, dip)
        arrSurvey = []
        if self.surveyLayer is not None and self.surveyLayer.isValid():
            numSurveys = self.surveyLayer.featureCount()
    
            dp = self.surveyLayer.dataProvider()
            idxSurveyId = dp.fieldNameIndex(self.surveyId)
            idxSurveyDepth = dp.fieldNameIndex(self.surveyDepth)
            idxSurveyAz = dp.fieldNameIndex(self.surveyAz)
            idxSurveyDip = dp.fieldNameIndex(self.surveyDip)
            
            pd.setWindowTitle("Build Survey Array")
            pd.setMaximum(numSurveys)
            pd.setValue(0)
            for index, feature in enumerate(self.surveyLayer.getFeatures()):
                pd.setValue(index)
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
        
        #Loop through collars
        pd.setWindowTitle("Desurvey Progress")
        pd.setMaximum(len(arrCollar))
        pd.setValue(0)
        updateInt = max(len(arrCollar), int(len(arrCollar)/100))
        
        for index, collar in enumerate(arrCollar):
            pd.setValue(index)
            if index%updateInt == 0:
                qApp.processEvents()
                
            if not collar.id:
                continue
            #Build array of surveys for this collar, including the top az and dip in collar layer. Repeat last survey at EOH.
            surveys = []

            if len(arrSurvey) > 0:
                for survey in arrSurvey:
                    if survey.id == collar.id:
                        s = Surveys()
                        s.depth = survey.depth
                        s.az = survey.az
                        s.dip = survey.dip
                        surveys.append(s)

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
                
            holeStraight = False
            if len(surveys) == 1:
                holeStraight = True

            if not holeStraight:
                # Sort the surveys array by depth
                surveys.sort(key = lambda x: x.depth)                        
            
                # If surveys exist, but there isn't one at 0.0, then replicate first survey at 0.0
                if not surveys[0].depth == 0.0:
                    s = Surveys()
                    surveys.insert(0, s)
                    s.depth = 0.0
                    surveys[0].az = surveys[1].az
                    surveys[0].dip = surveys[1].dip
                    
                # If the last survey isn't at the end of hole, then repeat the last one at eoh
                if len(surveys) > 0 and surveys[-1].depth < collar.depth:
                    s = Surveys()
                    s.depth = collar.depth
                    s.az = surveys[-1].az
                    s.dip = surveys[-1].dip
                    surveys.append(s)
                
            # Create a quaternion for each survey
            quat = []
            for j, s in enumerate(surveys):
                qdip = Quaternion(axis=[1, 0, 0], degrees=(s.dip  if self.downDipNegative else -s.dip))
                        
                qaz = Quaternion(axis=[0, 0, 1], degrees=-s.az)
                q = qaz * qdip
                if j > 0:
                    if np.dot(quat[j-1].elements, q.elements) < 0.0:
                        q = -q
                quat.append(q)
                
            #Build drill trace every desurveyLength to EOH
            xs = []
            if not holeStraight:
                sz = int(collar.depth / self.desurveyLength) + 1
                depth = 0.0
                for d in range(0, sz):
                    xs.append(depth)
                    depth += self.desurveyLength
                if xs[-1] > collar.depth:
                    xs[-1] = collar.depth
                if xs[-1] < collar.depth:
                    xs.append(collar.depth)
            else:
                xs.append(0.0)
                
            # Create linestring
            feature = QgsFeature()
            pointList = []
            pointList.append(QgsPoint(collar.east, collar.north, collar.elev))
            if not holeStraight:
                idx0 = 0
                # We already added the location at point0 (the collar) so start from 1
                for i in range(1, len(xs)):
                    q = Quaternion()
                    # Find the lowest survey equal or less than xs
                    for j in range(idx0, len(surveys)):
                        if surveys[j].depth == xs[i]:
                            idx0 = j
                            q = quat[j]
                            break
                        if surveys[j].depth < xs[i] and surveys[j+1].depth >= xs[i]:
                            idx0 = j
                            ratio = (xs[i] - surveys[j].depth) / (surveys[j+1].depth - surveys[j].depth)
                            q = Quaternion.slerp(quat[j], quat[j+1], ratio)
                            break

                    offset = q.rotate(np.array([0.0, 1.0, 0.0])) * self.desurveyLength
                    p0 = pointList[i-1]
                    pointList.append(QgsPoint(p0.x() + offset[0], p0.y() + offset[1], p0.z() + offset[2]))
            else:
                offset = quat[0].rotate(np.array([0.0, 1.0, 0.0])) * collar.depth
                p0 = pointList[0]
                pointList.append(QgsPoint(p0.x() + offset[0], p0.y() + offset[1], p0.z() + offset[2]))
                

            feature.setGeometry(QgsGeometry.fromPolyline(pointList))
            feature.setAttributes([collar.id, collar.depth if holeStraight else self.desurveyLength])
            self.traceLayer.startEditing()
            self.traceLayer.addFeature(feature)
                
            self.traceLayer.commitChanges()

        self.traceLayer.triggerRepaint()

        fileName = self.createTraceFilename()
        
        path="%s.gpkg" % (fileName)
        label = os.path.splitext(os.path.basename(fileName))[0]
        # Remove trace layer from project if it already exists
        layer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(layer)
        #Save memory layer to GeoPackage
        error = QgsVectorFileWriter.writeAsVectorFormat(self.traceLayer, fileName, "CP1250", self.collarLayer.sourceCrs(), layerOptions=['OVERWRITE=YES'])

        self.traceLayer = QgsVectorLayer(path, label)
        QgsProject.instance().addMapLayer(self.traceLayer)

    def createTraceFilename(self):
        # Build the new filename
        base, ext = os.path.splitext(self.collarLayer.dataProvider().dataSourceUri())
        fileName = base + "_Trace"
        if fileName.startswith("file:///"):
            fileName = fileName[8:]
        return fileName
    
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
        self.traceLayer = layer
    
    def createDownholeLayer(self):
        #Create a new memory layer
        layer = QgsVectorLayer("LineString?crs=EPSG:4326", "gt_Trace", "memory")
        layer.setCrs(self.traceLayer.sourceCrs())
        atts = []
        for field in self.dataLayer.fields():
            if field.name() in self.dataFields:
                atts.append(field)
        atts.append(QgsField("_From_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_From_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_From_z",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_z",  QVariant.Double, "double", 12, 3))
        
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        layer.updateFields() # tell the vector layer to fetch changes from the provider
#        QgsProject.instance().addMapLayer(layer)

        return layer
        
    def readProjectData(self):
        self.defaultSectionWidth = readProjectNum("DefaultSectionWidth", 50)
        self.defaultSectionStep= readProjectNum("DefaultSectionStep", 50)
        self.desurveyLength = readProjectNum("DesurveyLength", 1)
        self.downDipNegative = readProjectBool("DownDipNegative", True)
        self.collarLayer = readProjectLayer("CollarLayer")
        self.surveyLayer = readProjectLayer("SurveyLayer")
        self.dataLayer = readProjectLayer("DataLayer")
        self.traceLayer = readProjectLayer("TraceLayer")
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
        self.dataId = readProjectField(self.dataLayer, "DataID")
        self.dataFrom = readProjectField(self.dataLayer, "DataFrom")
        self.dataTo = readProjectField(self.dataLayer, "DataTo")
        self.dataSuffix = readProjectField(self.dataLayer, "DataSuffix")
        
        self.openLogFile()

    def writeProjectData(self):
        writeProjectData("DefaultSectionWidth", self.defaultSectionWidth)
        writeProjectData("DefaultSectionStep", self.defaultSectionStep)
        writeProjectData("DesurveyLength", self.desurveyLength)
        writeProjectData("DownDepthNegative", self.downDipNegative)
        writeProjectLayer("CollarLayer", self.collarLayer)
        writeProjectLayer("SurveyLayer", self.surveyLayer)
        writeProjectLayer("DataLayer", self.dataLayer)
        writeProjectLayer("TraceLayer", self.traceLayer)
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
        writeProjectField("DataID", self.dataId)
        writeProjectField("DataFrom", self.dataFrom)
        writeProjectField("DataTo", self.dataTo)
        writeProjectField("DataSuffix", self.dataSuffix)
    
