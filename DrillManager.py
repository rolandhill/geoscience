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
from .desurveyhole_dialog import DesurveyHoleDialog
from .downholedata_dialog import DownholeDataDialog
from .downholestructure_dialog import DownholeStructureDialog
from .sectionmanager_dialog import SectionManagerDialog

from .SectionManager import *
from .Utils import *

import os.path
import math
import platform

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
    
# The DrillManager class controls all drill related data and methods 
class DrillManager:
    def __init__(self):
        
        self.sectionManager = SectionManager(self)
        self.sectionManagerDlg = None
        
        # Project data is normally read in response to a readProject signal.
        # We also do it here for when the plugin is loaded other than at startup
        self.readProjectData()

        # Create a log file        
        self.openLogFile()

    # Open a log file in the Collar Layer's directory
    def openLogFile(self):
        # Maintain a log file in case of data errors
        if self.collarLayer and self.collarLayer.isValid():
            path=self.collarLayer.dataProvider().dataSourceUri()
            # fileName = uriToFile(os.path.join(os.path.split(path)[0], 'Geoscience_DrillManager_log.txt'))
            # self.logFile = open(fileName,'w')
            # if not self.logFile:
            #     self.logFile = open(os.path.join(os.path.expanduser("~"), "Geoscience_DrillManager_log.txt"),'w')
            # self.logFile.write("Geoscience - DrillManager log file\n")
            # self.logFile.write("  Note: This file is overwritten each time you run Geoscience.\n")
            # self.logFile.write("  Make a copy if you want to keep the results.\n")
            # # We flush the buffers in case the plugin crashes without writing the message to the file
            # self.logFile.flush()

    # Setup and run the Drill Setup dialog        
    def onDesurveyHole(self):
        dlg = DesurveyHoleDialog(self)
        result = dlg.exec_()
        # If OK button clicked then retrieve and update values
        if result:
            self.downDipNegative = dlg.checkDownDipNegative.isChecked()
            self.desurveyLength = float(dlg.leDesurveyLength.text())
#            self.defaultSectionWidth = dlg.teDefaultSectionWidth.text()
#            self.defaultSectionStep = dlg.teDefaultSectionStep.text()
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

            # Save updated values to QGIS project file            
            self.writeProjectData()
            
            # The collar layer might have changed, so re-open log file
            # self.openLogFile()
        dlg.close()

        if result:
            self.desurveyHole()


    # Setup and run the Downhole Data dialog
    def onDownholeData(self):
        dlg = DownholeDataDialog(self)
        result = dlg.exec_()
        if result:
            self.desurveyLayer = dlg.lbDesurveyLayer.currentLayer()
            self.dataLayer = dlg.lbDataLayer.currentLayer()
            self.dataId = dlg.fbDataId.currentField()
            self.dataFrom = dlg.fbDataFrom.currentField()
            self.dataTo = dlg.fbDataTo.currentField()
            self.dataSuffix = dlg.teSuffix.text()
            # Save the name of each checked attribute field in a list
            self.dataFields = []
            for index in range(dlg.listFields.count()):
                if dlg.listFields.item(index).checkState():
                    self.dataFields.append(dlg.listFields.item(index).text())
                    
            self.writeProjectData()

        dlg.close()

        if result:
            # Create the down hole traces        
            self.createDownholeData()

    # Setup and run the Downhole Structure dialog
    def onDownholeStructure(self):
        dlg = DownholeStructureDialog(self)
        result = dlg.exec_()
        if result:
            self.desurveyLayer = dlg.lbDesurveyLayer.currentLayer()
            self.structureLayer = dlg.lbDataLayer.currentLayer()
            self.structureId = dlg.fbDataId.currentField()
            self.structureDepth = dlg.fbDataDepth.currentField()
            self.structureAlpha = dlg.fbDataAlpha.currentField()
            self.structureBeta = dlg.fbDataBeta.currentField()
            self.structureScale = float(dlg.leSymbolSize.text())
            # Save the name of each checked attribute field in a list
            self.structureFields = []
            for index in range(dlg.listFields.count()):
                if dlg.listFields.item(index).checkState():
                    self.structureFields.append(dlg.listFields.item(index).text())
                    
            self.writeProjectData()

        dlg.close()

        if result:
            # Create the down hole traces        
            self.createDownholeStructure()

#    # Desurvey the data        
#    def onDesurveyHole(self):
#        self.desurveyData()
#
    # Create a section
    def onDrillSectionManager(self):
        if self.sectionManagerDlg is None:
            self.sectionManagerDlg = SectionManagerDialog(self)

        self.sectionManagerDlg.show()
        self.sectionManagerDlg.activateWindow()
        self.sectionManagerDlg.fillSectionList()

    # Create the down hole data (interval) traces    
    def createDownholeData(self):
        # self.logFile.write("\nCreating Downhole Data Layer.\n")
        # self.logFile.flush()
        
        # Check that desurvey layer is available
        if not self.desurveyLayer.isValid() or not self.dataLayer.isValid():
            return
        
        # Set up a progress display
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setWindowTitle("Build Downhole Data Layer")
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        pd.setMaximum(self.dataLayer.featureCount())
        pd.setValue(0)

        # Get the fields from the data layer
        dp = self.dataLayer.dataProvider()
        idxId = dp.fieldNameIndex(self.dataId)
        idxFrom = dp.fieldNameIndex(self.dataFrom)
        # idxTo will be -1 if no field was chosen (ie point rather than interval data)
        idxTo = dp.fieldNameIndex(self.dataTo)
        # Create a list of attribute indices from the desired attribute field names
        idxAttList = []
        for name in self.dataFields:
            idx = dp.fieldNameIndex(name)
            idxAttList.append(idx)
        
        # Create memory layer
        if(idxTo > -1):
            layer = self.createDownholeIntervalLayer()
        else:
            layer = self.createDownholePointLayer()

        # Get the fields from the desurveyed trace layer
        tdp = self.desurveyLayer.dataProvider()
        idxTraceId = tdp.fieldNameIndex("CollarID")
        idxTraceSegLength = tdp.fieldNameIndex("SegLength")

        # Store the relevant desurveyed drill trace so that it's persistent between loops
        # This way we should be able to re-use it instead of re-fetching it.
        traceFeature = QgsFeature()
        currentTraceCollar = ""
        currentTraceSegLength = 1.0
        currentTracePolyline = None
        
    #Loop through downhole layer features
        # Calculate an optimum update interval for the progress bar (updating gui items is expensive)
        updateInt = max(100, long(self.dataLayer.featureCount()/100))
        floatConvError = False
        nullDataError = False
        for index, df in enumerate(self.dataLayer.getFeatures()):
            # Update the Progress bar
            if index%updateInt == 0:
                pd.setValue(index)
                qApp.processEvents()
            
            # Variable to hold a feature
            feature = QgsFeature()

            # get the feature's attributes
            attrs = df.attributes()
            # Check all the data is valid
            dataId = str(attrs[idxId])
            try:
                dataFrom = float(attrs[idxFrom])
                if (idxTo > -1):
                    dataTo = float(attrs[idxTo])
            except:
                floatConvError = True
                
            if (dataId==NULL) or (dataFrom==NULL) or (idxTo > -1 and dataTo==NULL):
                nullDataError = True
                continue
            dataId = dataId.strip()
            
            # Get the desurvey drill trace relevant to this collar, checking first that we don't already have it
            if not currentTraceCollar == dataId:
                # Get the correct trace feature via a query
                query = '''"CollarID" = '%s' ''' % (dataId)
                selection = self.desurveyLayer.getFeatures(QgsFeatureRequest().setFilterExpression(query))
                # We have a selection of features
                if selection.isValid():
                    # There should be just 1, so get the first feature
                    selection.nextFeature(traceFeature)
                    # Is the feature valid?
                    if traceFeature.isValid():
                        # Update information for the current feature
                        currentTraceCollar = dataId
                        currentTraceSegLength = traceFeature.attributes()[idxTraceSegLength]
                        # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                        # We therefore get a vertex iterator for the abstractGeometry and build our own list
                        currentTracePolyline = []
                        vi = traceFeature.geometry().vertices()
                        while vi.hasNext():
                            currentTracePolyline.append(vi.next())
                    else:
                        continue
                else:
                    continue
            if (floatConvError):
                iface.messageBar().pushMessage("Warning", "Some 'From' or 'To' values are not numbers", level=Qgis.Warning)
            if (nullDataError):
                iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'From' or 'To' values are NULL. These have been skipped", level=Qgis.Warning)

                
            # Calculate indices spanning the from and to depths, then linearly interpolate a position
            try:
                pFrom, iFrom = interpPolyline(dataFrom, currentTraceSegLength, currentTracePolyline)
            except:
                # self.logFile.write("Error interpolating from polyline for hole: %s From: %f in row: %d.\n" % (dataId, dataFrom, index))
                continue
            
            if (idxTo > -1):
                try:
                    pTo, iTo = interpPolyline(dataTo, currentTraceSegLength, currentTracePolyline)
                except:
                    # self.logFile.write("Error interpolating from polyline for hole: %s To: %f in row: %d.\n" % (dataId, dataTo, index))
                    continue

            
            # Set the geometry for the new downhole feature
            if (idxTo > -1):
            # Create line representing the downhole value using From and To
                pointList = []

                # Add the first (From) point to the list
                pointList.append(pFrom)

                # Add intervening points and last point if this is an interval
                if (idxTo > -1):
                    # Add all the intermediate points (so a long interval accurately reflects the bend of the hole)
                    if math.floor(iTo) - math.ceil(iFrom) > self.desurveyLength:
                        for i in range(math.ceil(iFrom), math.floor(iTo)):
                            pointList.append(currentTracePolyline[i])
                    # Add the last (To) point
                    pointList.append(pTo)

                feature.setGeometry(QgsGeometry.fromPolyline(pointList))
            else:
                feature.setGeometry(QgsGeometry(QgsPoint(pFrom.x(), pFrom.y(), pFrom.z(), wkbType = QgsWkbTypes.PointZ)))

            # Create a list of the attributes to be included in new file
            # These are just copied from the original down hole layer
            # according to whether the user selected the check boxes
            attList = []
            for idx in idxAttList:
                attList.append(attrs[idx])

            # Also append the 3D desurveyed From, To and Mid points
            if (idxTo > -1):
                idxLast = len(pointList) - 1
                attList.append(pointList[0].x())
                attList.append(pointList[0].y())
                attList.append(pointList[0].z())
                attList.append(pointList[idxLast].x())
                attList.append(pointList[idxLast].y())
                attList.append(pointList[idxLast].z())
                attList.append((pointList[0].x()+pointList[idxLast].x())*0.5)
                attList.append((pointList[0].y()+pointList[idxLast].y())*0.5)
                attList.append((pointList[0].z()+pointList[idxLast].z())*0.5)
            else:
                attList.append(pFrom.x())
                attList.append(pFrom.y())
                attList.append(pFrom.z())

            # Set the attributes for the new feature
            feature.setAttributes(attList)

            # Add the new feature to the new Trace_ layer
            layer.startEditing()
            layer.addFeature(feature)
            layer.commitChanges()

        # Flush the log file in case anything was written
        # self.logFile.flush()
        
        # Build the new filename for saving to disk. We are using GeoPackages
        path=self.desurveyLayer.dataProvider().dataSourceUri()
        fileName=os.path.join(os.path.split(path)[0], self.desurveyLayer.name())
        fileName = fileName.replace("_Desurvey","_Downhole")
        fileName = uriToFile(fileName + "_%s" % (self.dataSuffix))

        # Generate a layer label
        label = os.path.splitext(os.path.basename(fileName))[0]

        # Remove trace layer from project if it already exists
        oldLayer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(oldLayer)

        #Save memory layer to Geopackage file
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.includeZ = True
        # options.overrideGeometryType = memLayer.wkbType()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # error = QgsVectorFileWriter.writeAsVectorFormatV3(layer, fileName, QgsProject.instance().transformContext(), options)
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", self.desurveyLayer.crs(), layerOptions=['OVERWRITE=YES'])
            
        # Load the one we just saved and add it to the map
        layer = QgsVectorLayer(fileName+".gpkg", label)
        QgsProject.instance().addMapLayer(layer)
        
    # Create the down hole data (interval) traces    
    def createDownholeStructure(self):
        # self.logFile.write("\nCreating Downhole Structure Layer.\n")
        # self.logFile.flush()
        
        # Check that desurvey layer is available
        if not self.desurveyLayer.isValid() or not self.structureLayer.isValid():
            return
        
        # Set up a progress display
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setWindowTitle("Build Downhole Structure Layer")
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        pd.setMaximum(self.structureLayer.featureCount())
        pd.setValue(0)

        # Create memory layer
        layer = self.createDownholeStructureLayer()

        # Get the fields from the data layer
        dp = self.structureLayer.dataProvider()
        idxId = dp.fieldNameIndex(self.structureId)
        idxDepth = dp.fieldNameIndex(self.structureDepth)
        idxAlpha = dp.fieldNameIndex(self.structureAlpha)
        idxBeta = dp.fieldNameIndex(self.structureBeta)
        # Create a list of attribute indices from the desired attribute field names
        idxAttList = []
        for name in self.structureFields:
            idx = dp.fieldNameIndex(name)
            idxAttList.append(idx)
        
        # Get the fields from the desurveyed trace layer
        tdp = self.desurveyLayer.dataProvider()
        idxTraceId = tdp.fieldNameIndex("CollarID")
        idxTraceSegLength = tdp.fieldNameIndex("SegLength")

        # Store the relevant desurveyed drill trace so that it's persistent between loops
        # This way we should be able to re-use it instead of re-fetching it.
        traceFeature = QgsFeature()
        currentTraceCollar = ""
        currentTraceSegLength = 1.0
        currentTracePolyline = None
        
    #Loop through downhole layer features
        # Calculate an optimum update interval for the progress bar (updating gui items is expensive)
        updateInt = max(100, long(self.structureLayer.featureCount()/100))
        floatConvError = False
        nullDataError = False
        for index, df in enumerate(self.structureLayer.getFeatures()):
            # Update the Progress bar
            if index%updateInt == 0:
                pd.setValue(index)
                qApp.processEvents()
            
            # Variable to hold a feature
            feature = QgsFeature()

            # get the feature's attributes
            attrs = df.attributes()
            # Check all the data is valid
            dataId = str(attrs[idxId])
            dataDepth = NULL
            dataAlpha = NULL
            dataBeta = NULL
            try:
                dataDepth = float(attrs[idxDepth])
                dataAlpha = float(attrs[idxAlpha])
                dataBeta = float(attrs[idxBeta])
            except:
                floatConvError = True
                
            if (dataId==NULL) or (dataDepth==NULL) or (dataAlpha==NULL) or (dataBeta==NULL):
                nullDataError = True
                continue
            dataId = dataId.strip()

            # iface.messageBar().pushMessage("Debug", "%s  %f  %f  %f"%(dataId, dataDepth, dataAlpha, dataBeta), level=Qgis.Info)

            # Get the desurvey drill trace relevant to this collar, checking first that we don't already have it
            if not currentTraceCollar == dataId:
                # Get the correct trace feature via a query
                query = '''"CollarID" = '%s' ''' % (dataId)
                selection = self.desurveyLayer.getFeatures(QgsFeatureRequest().setFilterExpression(query))
                # We have a selection of features
                if selection.isValid():
                    # There should be just 1, so get the first feature
                    selection.nextFeature(traceFeature)
                    # Is the feature valid?
                    if traceFeature.isValid():
                        # Update information for the current feature
                        currentTraceCollar = dataId
                        currentTraceSegLength = traceFeature.attributes()[idxTraceSegLength]
                        # The normal asPolyline() function only returns QgsPointXY, yet we need the Z coordinate as well
                        # We therefore get a vertex iterator for the abstractGeometry and build our own list
                        currentTracePolyline = []
                        vi = traceFeature.geometry().vertices()
                        while vi.hasNext():
                            currentTracePolyline.append(vi.next())
                    else:
                        continue
                else:
                    continue
            if (floatConvError):
                iface.messageBar().pushMessage("Warning", "Some 'Depth', 'Alpha' or 'Beta' values are not numbers", level=Qgis.Warning)
            if (nullDataError):
                iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'Alpha' or 'Beta' values are NULL. These have been skipped", level=Qgis.Warning)

                
            # Create line representing the downhole value using From and To
            # pointList = []
            # Calculate indices spanning the from and to depths, then linearly interpolate a position
            try:
                pDepth, iDepth = interpPolyline(dataDepth, currentTraceSegLength, currentTracePolyline)
            except:
                # self.logFile.write("Error interpolating from polyline for hole: %s From: %f in row: %d.\n" % (dataId, dataDepth, index))
                continue

            # Get the desurveyed core axis vector
            vCore = np.array([0.0, 0.0, 1.0])
            try:
                vCore = coreVector(dataDepth, currentTraceSegLength, currentTracePolyline)
            except:
                # self.logFile.write("Error getting up vector: %s To: %f in row: %d.\n" % (dataId, dataDepth, index))
                continue

            # We can't work with vertical drill holes
            if abs(np.dot(vCore, np.array([0.0, 0.0, 1.0]))) > 0.9999:
                continue

            # Create a quat to rotate an alpha = 0, beta = 0 plane normal into the measured plane normal
            # We start with the measured plane being parallel with a vertical drill hole with the normal pointing north
            n = np.array([0.0, 1.0, 0.0])

            # Rotate the plane according to the alpha angle
            q = Quaternion(axis=[-1.0, 0.0, 0.0], degrees=dataAlpha)
            n = q.rotate(n)

            # Rotate the plane according to the beta angle
            q = Quaternion(axis=[0.0, 0.0, -1.0], degrees=dataBeta)
            n = q.rotate(n)

            # Calculate the dip angle of the desurveyed core by comparing its down vector with vertical
            a = math.acos(np.dot(np.array([0.0, 0.0, -1.0]), vCore))

            # Rotate the measured plane to account for the core's dip
            q = Quaternion(axis=[1.0, 0.0, 0.0], radians=a)
            n = q.rotate(n)

            # Calculate the dip direction (azimuth) of the core by setting the z component to 0
            dd = np.array([vCore[0], vCore[1], 0.0])
            # and normalise
            dd = dd/np.linalg.norm(dd)

            # Calculate the angle in the horizontal plane between the core azimuth and north
            a = math.acos(np.dot(np.array([0.0, 1.0, 0.0]), dd))
            # Cos only covers 0 - 180 degrees, so check if should be in the -180 - 0 range
            if vCore[0] < 0:
                a = -a

            # Rotate the measured plane by the core azimuth
            q = Quaternion(axis=[0.0, 0.0, -1.0], radians=a)
            n = q.rotate(n) # Final measured plane normal

            #Dips are always measured from 0-90 degrees downwards, so lets check if the rotations
            # have turned the plane upside down and flip it over if it has.
            if n[2] < 0:
                n = -n

            # Calculate dip direction from the x & y components of the normal
            dipdir = math.degrees(math.atan2(n[0], n[1]))
            # And make it 0 - 360 instead of -180 - 180
            if dipdir < 0:
                dipdir = 360 + dipdir
            
            # The dip is the angle between the normal and up vector
            dip = math.degrees(math.acos(np.dot(np.array([0.0, 0.0, 1.0]), n)))

            # We need to calculate two more vectors so that we can draw symbols
            # The strike vector is horizontal and the dip vector is vertical
            vstrike = np.cross(n, dd)
            vdip = np.cross(n, vstrike)

            # qpstrike = QgsPoint(vstrike[0], vstrike[1], vstrike[2])
            # qpdip = QgsPoint(vdip[0], vdip[1], vdip[2])

            # Set the geometry for the new downhole feature
            scale = self.structureScale
            p0 = QgsPoint(pDepth.x() + vstrike[0] * scale + vdip[0] * scale, pDepth.y() + vstrike[1] * scale + vdip[1] * scale, pDepth.z() + vstrike[2] * scale + vdip[2] * scale)
            p1 = QgsPoint(pDepth.x() - vstrike[0] * scale + vdip[0] * scale, pDepth.y() - vstrike[1] * scale + vdip[1] * scale, pDepth.z() - vstrike[2] * scale + vdip[2] * scale)
            p2 = QgsPoint(pDepth.x() - vstrike[0] * scale - vdip[0] * scale, pDepth.y() - vstrike[1] * scale - vdip[1] * scale, pDepth.z() - vstrike[2] * scale - vdip[2] * scale)
            p3 = QgsPoint(pDepth.x() + vstrike[0] * scale - vdip[0] * scale, pDepth.y() + vstrike[1] * scale - vdip[1] * scale, pDepth.z() + vstrike[2] * scale - vdip[2] * scale)
            # pointList = [p0, p1, p2, p3, p0]

            # poly = QgsPolygon()
            # poly.insertVertex(QgsVertexId(0, 0, 0), p0)
            # poly.insertVertex(QgsVertexId(0, 0, 1), p1)
            # poly.insertVertex(QgsVertexId(0, 0, 2), p2)
            # poly.insertVertex(QgsVertexId(0, 0, 3), p3)
            # poly.insertVertex(QgsVertexId(0, 0, 4), p0)

            wkt = 'POLYGONZ (('
            wkt = wkt + '%f %f %f, '%(p0.x(), p0.y(), p0.z())
            wkt = wkt + '%f %f %f, '%(p1.x(), p1.y(), p1.z())
            wkt = wkt + '%f %f %f, '%(p2.x(), p2.y(), p2.z())
            wkt = wkt + '%f %f %f, '%(p3.x(), p3.y(), p3.z())
            wkt = wkt + '%f %f %f'%(p0.x(), p0.y(), p0.z())
            wkt = wkt + '))'

            # iface.messageBar().pushMessage("WKT: %s"%(wkt), level=Qgis.Info)

            poly = QgsGeometry.fromWkt(wkt)

            feature.setGeometry(QgsGeometry(poly))

            # Create a list of the attributes to be included in new file
            # These are just copied from the original down hole layer
            # according to whether the user selected the check boxes
            attList = []
            for idx in idxAttList:
                attList.append(attrs[idx])

            # Also append the 3D desurveyed From, To and Mid points
            attList.append(pDepth.x())
            attList.append(pDepth.y())
            attList.append(pDepth.z())
            # attList.append(float(n[0]))
            # attList.append(float(n[1]))
            # attList.append(float(n[2]))
            attList.append(dipdir)
            attList.append(dip)

            # Set the attributes for the new feature
            feature.setAttributes(attList)

            # Add the new feature to the new Trace_ layer
            layer.startEditing()
            layer.addFeature(feature)
            layer.commitChanges()

        # Flush the log file in case anything was written
        # self.logFile.flush()
        
        # Build the new filename for saving to disk. We are using GeoPackages
        path=self.desurveyLayer.dataProvider().dataSourceUri()
        fileName=os.path.join(os.path.split(path)[0], self.desurveyLayer.name())
        fileName = fileName.replace("_Desurvey","_Structure")

        # Generate a layer label
        label = os.path.splitext(os.path.basename(fileName))[0]

        # Remove trace layer from project if it already exists
        oldLayer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(oldLayer)

        #Save memory layer to Geopackage file
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.includeZ = True
        # options.overrideGeometryType = memLayer.wkbType()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # error = QgsVectorFileWriter.writeAsVectorFormatV3(layer, fileName, QgsProject.instance().transformContext(), options)
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", self.desurveyLayer.crs(), layerOptions=['OVERWRITE=YES'])
            
        # Load the one we just saved and add it to the map
        layer = QgsVectorLayer(fileName+".gpkg", label)
        QgsProject.instance().addMapLayer(layer)
        
    def desurveyHole(self):
        # Write to the log file
        # self.logFile.write("\nDesurveying data.\n")
        # self.logFile.flush()
        
        # Set up a progress bar
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        
        # Get the relevant attribute indices
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

        # Update the progress bar
        pd.setWindowTitle("Build Collar Array")
        pd.setMaximum(numCollars)
        pd.setValue(0)
        
        floatConvError = False
        nullDataError = False

        # Create a new Collar 3D layer to hold 3D points. This will be used for section creation.
        collar3D = self.createCollarLayer()
        
        # Loop through the collar layer and build list of collars
        for index, feature in enumerate(self.collarLayer.getFeatures()):
            # Update progress bar
            pd.setValue(index)
            
            # get the feature's attributes
            attrs = feature.attributes()
            c = Collar()
            # Check all the data is valid
            c.id = str(attrs[idxCollarId])
            try:
                c.east = float(attrs[idxCollarEast])
                c.north = float(attrs[idxCollarNorth])
                c.elev = float(attrs[idxCollarElev])
                c.depth = float(attrs[idxCollarDepth])
            except:
                floatConvError = True
                
            if (c.id==NULL) or (c.east==NULL) or (c.north==NULL) or (c.elev==NULL) or (c.depth==NULL):
                nullDataError = True
                continue
            c.id = c.id.strip()
            if useCollarAzDip:
                c.az = attrs[idxCollarAz]
                if c.az==NULL:
                    c.az = 0.0
                c.dip = attrs[idxCollarDip]
                if c.dip==NULL:
                    c.dip = -90 if self.downDipNegative else 90
            arrCollar.append(c)
            
            #Create a new 3D point feature and copy the attributes
            f = QgsFeature()
#            p = QPointF(c.east, c.north, c.elev)
            f.setGeometry(QgsGeometry(QgsPoint(c.east, c.north, c.elev, wkbType = QgsWkbTypes.PointZ)))
            # Add in the field attributes
            f.setAttributes(attrs)
            # Add the feature to the layer
            collar3D.startEditing()
            collar3D.addFeature(f)
            collar3D.commitChanges()
            
            
        if (floatConvError):
            iface.messageBar().pushMessage("Warning", "Some 'East', 'North', 'Collar' or 'Depth' values are not numbers", level=Qgis.Warning)
        if (nullDataError):
            iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'East', 'North', 'Collar' or 'Depth' values are NULL. These have been skipped", level=Qgis.Warning)

            
        # Build Survey array (Id, depth, az, dip)
        arrSurvey = []
        if self.surveyLayer is not None and self.surveyLayer.isValid():
            numSurveys = self.surveyLayer.featureCount()
    
            # Get the attribute indices
            dp = self.surveyLayer.dataProvider()
            idxSurveyId = dp.fieldNameIndex(self.surveyId)
            idxSurveyDepth = dp.fieldNameIndex(self.surveyDepth)
            idxSurveyAz = dp.fieldNameIndex(self.surveyAz)
            idxSurveyDip = dp.fieldNameIndex(self.surveyDip)
            
            # Update progress bar
            pd.setWindowTitle("Build Survey Array")
            pd.setMaximum(numSurveys)
            pd.setValue(0)
            
            floatConvError = False
            nullDataError = False
            
            #Loop through Survey layer and build list of surveys
            for index, feature in enumerate(self.surveyLayer.getFeatures()):
                pd.setValue(index)
                ok = True
                
                # get the feature's attributes
                attrs = feature.attributes()
                s = Survey()
                s.id = str(attrs[idxSurveyId])
                try:
                    s.depth = float(attrs[idxSurveyDepth])
                    s.az = float(attrs[idxSurveyAz])
                    s.dip = float(attrs[idxSurveyDip])
                except:
                    ok = False
                    iface.messageBar().pushMessage("Warning", "HoleID %s   Depth %f"%(s.id, s.depth), level=Qgis.Warning)
                    floatConvError = True
                    
                if (s.id==NULL) or (s.depth==NULL) or (s.az==NULL) or (s.dip==NULL):
                    ok = False
                    nullDataError = True
                    continue

                if ok:
                    s.id = s.id.strip()
                    arrSurvey.append(s)

            if (floatConvError):
                iface.messageBar().pushMessage("Warning", "Some survey 'Depth', 'Azimuth' or 'Dip' values are not numbers", level=Qgis.Warning)
            if (nullDataError):
                iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'Depth', 'Azimuth' or 'Dip' values are NULL. These have been skipped", level=Qgis.Warning)
            
        # Create new layer for the desurveyed 3D coordinates. PolyLine, 1 row per collar, 2 attribute (Id, Segment Length)
        self.createDesurveyLayer()
        
        #Loop through collar list and desurvey each one
        # Update Progress bar
        pd.setWindowTitle("Desurvey Progress")
        pd.setMaximum(len(arrCollar))
        pd.setValue(0)
        #Calculate optimum update interval
        updateInt = max(100, int(len(arrCollar)/100))
        
        # Enter collar loop
        for index, collar in enumerate(arrCollar):
            pd.setValue(index)
            # Force update the progress bar visualisation every 1% as it normally only happens in idle time
            if index%updateInt == 0:
                qApp.processEvents()

            # Check the id exists                
            if not collar.id:
                continue
            
            #Build array of surveys for this collar, including the top az and dip in collar layer. Repeat last survey at EOH.
            surveys = []

            zeroDepth = False;
            if len(arrSurvey) > 0:
                # Harvest surveys for this collar from Survey layer list
                for survey in arrSurvey:
                    if survey.id == collar.id and survey.depth <= collar.depth:
                        s = Surveys()
                        s.depth = survey.depth
                        s.az = survey.az
                        s.dip = survey.dip
                        surveys.append(s)
                        if s.depth == 0.0:
                            zeroDepth = True;

            # If the az and dip from the collar are to be used, then append them at depth 0.0
            # We only do this if there is no survey from 0 depth in the Survey layer
            if zeroDepth == False and useCollarAzDip:
                if (not collar.az == NULL) and (not collar.dip == NULL):
                    s = Surveys()
                    s.depth = 0.0
                    s.az = collar.az
                    s.dip = collar.dip
                    surveys.append(s)
            
            # If there are no surveys, then the assume hole is vertical
            if len(surveys) == 0:
                s = Surveys()
                s.depth = 0.0
                s.az = 0.0
                s.dip = -90 if self.downDipNegative else 90
                surveys.append(s)
                
            # Is the hole straight? If so, we can take short cuts
            holeStraight = False
            if len(surveys) == 1:
                holeStraight = True

            # We only replicate survey to the beginning and end if the hole is not straight
            if not holeStraight:
                # Sort the surveys array by depth
                surveys.sort(key = lambda x: x.depth)                        
            
                # If surveys exist, but there isn't one at 0.0, then replicate first survey at 0.0
                if not surveys[0].depth == 0.0:
                    s = Surveys()
                    s.depth = 0.0
                    s.az = surveys[1].az
                    s.dip = surveys[1].dip
                    surveys.insert(0, s)
                    
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
                # Rotate about positive X axis by dip degrees (depends on downDipNegative flag)
                qdip = Quaternion(axis=[1, 0, 0], degrees=(s.dip  if self.downDipNegative else -s.dip))

                # Rotate about positive Z axis by -Az degrees                        
                qaz = Quaternion(axis=[0, 0, 1], degrees=-s.az)
                
                # Combine the dip and azimuth (order is important!)
                q = qaz * qdip
                
                #Ensure the quaternion rotates the shortest way around. This can go wrong when we cross 0/360 deg.
                # If the dot product of the quats is negative then it's the wrong way,
                # so we negate the quat.
                # But, don't do it on the first one
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
                
            # Create linestring to record the desurveyed points every Segment Length
            # This can then be used to interpolate intervening points
            feature = QgsFeature()
            # We'll create a pointlist to hold all the 3D points
            pointList = []
            # We start by adding the collar coordinates
            pointList.append(QgsPoint(collar.east, collar.north, collar.elev))
            # It's easier with a straight hole
            if not holeStraight:
                # We're going to keep iterating through the survey list looking for the bracketing surveys.
                # We therefore record the start point of the iteration as it will only go up. Saves time.
                idx0 = 0
                # We already added the location at point0 (the collar) so start from 1
                for i in range(1, len(xs)):
                    q = Quaternion()
                    # Find the lowest survey equal or less than xs
                    for j in range(idx0, len(surveys)):
                        # Is there a survey exactly at this point?
                        if surveys[j].depth == xs[i]:
                            # Update the iteration start point
                            idx0 = j
                            q = quat[j]
                            break
                        # Are there surveys bracketing this depth? If so, interpolate point
                        if surveys[j].depth < xs[i] and surveys[j+1].depth >= xs[i]:
                            # Update the iteration start point
                            idx0 = j
                            # How far are we between bracketing surveys?
                            ratio = (xs[i] - surveys[j].depth) / (surveys[j+1].depth - surveys[j].depth)
                            # Interpolate between bracketing survey rotations
                            q = Quaternion.slerp(quat[j], quat[j+1], ratio)
                            break

                    # Calculate the deviation of this segment of the hole
                    offset = q.rotate(np.array([0.0, 1.0, 0.0])) * self.desurveyLength
                    # Calculate the new point by adding the offset to the old point
                    p0 = pointList[i-1]
                    pointList.append(QgsPoint(p0.x() + offset[0], p0.y() + offset[1], p0.z() + offset[2]))
            else:
                # Calculate the offset of the bottom of hole from the top of hole in a single segment
                offset = quat[0].rotate(np.array([0.0, 1.0, 0.0])) * collar.depth
                # Add the offset to the collar
                p0 = pointList[0]
                pointList.append(QgsPoint(p0.x() + offset[0], p0.y() + offset[1], p0.z() + offset[2]))
                
            # Create new geometry (Polyline) for the feature
            feature.setGeometry(QgsGeometry.fromPolyline(pointList))
            # Add in the field attributes
            feature.setAttributes([collar.id, collar.depth if holeStraight else self.desurveyLength])
            
            # Add the feature to the layer
            self.desurveyLayer.startEditing()
            self.desurveyLayer.addFeature(feature)
            self.desurveyLayer.commitChanges()

        self.desurveyLayer = self.writeVectorLayerFromMemory(self.desurveyLayer, self.createDesurveyFilename(), self.collarLayer.crs())
        self.writeVectorLayerFromMemory(collar3D, self.createCollarFilename(), self.collarLayer.crs())
#        QgsProject.instance().addMapLayer(collar3D)


    def writeVectorLayerFromMemory(self, memLayer, fileBaseName, crs):
        # Calculate the filename for the on disk file
        path="%s.gpkg" % (fileBaseName)
        
        # work out a label for the layer from the file name
        label = os.path.splitext(os.path.basename(fileBaseName))[0]
        
        # Remove layer from project if it already exists
        layer = getLayerByName(label)
        QgsProject.instance().removeMapLayer(layer)
        
        #Save memory layer to GeoPackage
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = "GPKG"
        options.includeZ = True
        options.overrideGeometryType = memLayer.wkbType()
        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer

        # error = QgsVectorFileWriter.writeAsVectorFormatV3(memLayer, path, QgsProject.instance().transformContext(), options)
        # iface.messageBar().pushMessage("Debug", "Error code %d File: %s"%(error[0], path), level=Qgis.Warning)
        # error = QgsVectorFileWriter.writeAsVectorFormatV2(memLayer, fileBaseName, "CP1250", crs, 
        #         layerOptions=['OVERWRITE=YES'], overrideGeometryType=memLayer.wkbType())

        error = QgsVectorFileWriter.writeAsVectorFormat(memLayer, fileBaseName, "CP1250", crs, 
                layerOptions=['OVERWRITE=YES'], overrideGeometryType=memLayer.wkbType())

        # Load the layer we just saved so the user can manipulate a real layer
        fileLayer = QgsVectorLayer(path, label)
        QgsProject.instance().addMapLayer(fileLayer)
        return fileLayer
        
    def createCollarFilename(self):
        # Build the new filename
        path=self.collarLayer.dataProvider().dataSourceUri()
        fileName = uriToFile(os.path.join(os.path.split(path)[0], self.collarLayer.name()+'_3D'))
        return fileName
    
    def createDesurveyFilename(self):
        # Build the new filename
        path=self.collarLayer.dataProvider().dataSourceUri()
        fileName = uriToFile(os.path.join(os.path.split(path)[0], self.collarLayer.name()+'_Desurvey'))
        return fileName
    
    def createCollarLayer(self):
        #Find CRS of collar layer
        crs = self.collarLayer.crs()
        
        #Create a new memory layer
        layer = QgsVectorLayer("PointZ?crs=EPSG:4326", "geoscience_Temp", "memory")
        layer.setCrs(crs)

        atts = []
        # Loop through the list of desired field names that the user checked
        for field in self.collarLayer.fields():
            atts.append(field)
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 
        return layer
    
    def createDesurveyLayer(self):
        #Find CRS of collar layer
        crs = self.collarLayer.crs()
        
        #Create a new memory layer
        layer = QgsVectorLayer("LineStringZ?crs=EPSG:4326", "geoscience_Temp", "memory")
        layer.setCrs(crs)
        dp = layer.dataProvider()
        dp.addAttributes([
            QgsField("CollarID",  QVariant.String, "string", 16),
            QgsField("SegLength",  QVariant.Double, "double", 5, 2)
            ])
        layer.updateFields() # tell the vector layer to fetch changes from the provider
        self.desurveyLayer = layer
    
    def createDownholeIntervalLayer(self):
        #Create a new memory layer
        layer = QgsVectorLayer("LineStringZ?crs=EPSG:4326", "geoscience_Temp", "memory")
        layer.setCrs(self.desurveyLayer.crs())
        atts = []
        # Loop through the list of desired field names that the user checked
        for field in self.dataLayer.fields():
            if field.name() in self.dataFields:
                atts.append(field)
        # Also add fields for the desurveyed coordinates
        atts.append(QgsField("_From_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_From_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_From_z",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_To_z",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Mid_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Mid_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Mid_z",  QVariant.Double, "double", 12, 3))
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 

        return layer

    def createDownholePointLayer(self):
        #Create a new memory layer
        layer = QgsVectorLayer("PointZ?crs=EPSG:4326", "geoscience_Temp", "memory")
        layer.setCrs(self.desurveyLayer.crs())
        atts = []
        # Loop through the list of desired field names that the user checked
        for field in self.dataLayer.fields():
            if field.name() in self.dataFields:
                atts.append(field)
        # Also add fields for the desurveyed coordinates
        atts.append(QgsField("_Depth_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Depth_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Depth_z",  QVariant.Double, "double", 12, 3))
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 

        return layer

    def createDownholeStructureLayer(self):
        #Create a new memory layer
        layer = QgsVectorLayer("PolygonZ?crs=EPSG:4326", "geoscience_Temp", "memory")
        layer.setCrs(self.desurveyLayer.crs())
        atts = []
        # Loop through the list of desired field names that the user checked
        for field in self.structureLayer.fields():
            if field.name() in self.structureFields:
                atts.append(field)
        # Also add fields for the desurveyed coordinates
        atts.append(QgsField("_Depth_x",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Depth_y",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Depth_z",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_DipDir",  QVariant.Double, "double", 12, 3))
        atts.append(QgsField("_Dip",  QVariant.Double, "double", 12, 3))
        
        # Add all the attributes to the new layer
        dp = layer.dataProvider()
        dp.addAttributes(atts)
        
        # Tell the vector layer to fetch changes from the provider
        layer.updateFields() 

        return layer

    # Read all the saved DrillManager parameters from the QGIS project        
    def readProjectData(self):
#       Desurvey & Downhole Data
        self.desurveyLength = readProjectDouble("DesurveyLength", 1.0)
        self.downDipNegative = readProjectBool("DownDipNegative", True)
        self.desurveyLayer = readProjectLayer("DesurveyLayer")
        self.collarLayer = readProjectLayer("CollarLayer")
        self.surveyLayer = readProjectLayer("SurveyLayer")
        self.dataLayer = readProjectLayer("DataLayer")
        self.structureLayer = readProjectLayer("StructureLayer")
        self.collarId = readProjectField("CollarID")
        self.collarDepth = readProjectField("CollarDepth")
        self.collarEast = readProjectField("CollarEast")
        self.collarNorth = readProjectField("CollarNorth")
        self.collarElev = readProjectField("CollarElev")
        self.collarAz = readProjectField("CollarAz")
        self.collarDip = readProjectField("CollarDip")
        self.surveyId = readProjectField("SurveyID")
        self.surveyDepth = readProjectField("SurveyDepth")
        self.surveyAz = readProjectField("SurveyAz")
        self.surveyDip = readProjectField("SurveyDip")
        self.dataId = readProjectField("DataID")
        self.dataFrom = readProjectField("DataFrom")
        self.dataTo = readProjectField("DataTo")
        self.dataSuffix = readProjectField("DataSuffix")
        self.structureId = readProjectField("StructureID")
        self.structureDepth = readProjectField("StructureDepth")
        self.structureAlpha = readProjectField("StructureAlpha")
        self.structureBeta = readProjectField("StructureBeta")
        self.structureScale = readProjectDouble("StructureScale", 1)
#       Section Data
        self.sectionWEName = readProjectText("SectionWEName", '')
        self.sectionSNName = readProjectText("SectionSNName", '')
        self.sectionName = readProjectText("SectionName", '')
        self.sectionWidth = readProjectDouble("SectionWidth", 20)
        self.sectionStep = readProjectDouble("SectionStep", 50)
        self.sectionNorth = readProjectDouble("SectionNorth", 0)
        self.sectionEast = readProjectDouble("SectionEast", 0)
        self.sectionLimitWest = readProjectDouble("SectionLimitWest", 0)
        self.sectionLimitEast = readProjectDouble("SectionLimitEast", 1)
        self.sectionLimitSouth = readProjectDouble("SectionLimitSouth", 0)
        self.sectionLimitNorth = readProjectDouble("SectionLimitNorth", 1)

        self.sectionManager.readProjectData()        

        # Collar layer might have changed, so re-open the log file
        # self.openLogFile()

    # Write all DrillManager parameters to the QGIS project file
    def writeProjectData(self):
#       Desurvey & Downhole Data
        writeProjectDataDouble("DesurveyLength", self.desurveyLength)
        writeProjectData("DownDepthNegative", self.downDipNegative)
        writeProjectLayer("DesurveyLayer", self.desurveyLayer)
        writeProjectLayer("CollarLayer", self.collarLayer)
        writeProjectLayer("SurveyLayer", self.surveyLayer)
        writeProjectLayer("DataLayer", self.dataLayer)
        writeProjectLayer("StructureLayer", self.structureLayer)
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
        writeProjectField("StructureID", self.structureId)
        writeProjectField("StructureDepth", self.structureDepth)
        writeProjectField("StructureAlpha", self.structureAlpha)
        writeProjectField("StructureBeta", self.structureBeta)
        writeProjectDataDouble("StructureScale", self.structureScale)
#       Section Dialog Data
        writeProjectData("SectionWEName", self.sectionWEName)
        writeProjectData("SectionSNName", self.sectionSNName)
        writeProjectData("SectionName", self.sectionName)
        writeProjectDataDouble("SectionWidth", self.sectionWidth)
        writeProjectDataDouble("SectionStep", self.sectionStep)
        writeProjectDataDouble("SectionNorth", self.sectionNorth)
        writeProjectDataDouble("SectionEast", self.sectionEast)
        writeProjectDataDouble("SectionLimitWest", self.sectionLimitWest)
        writeProjectDataDouble("SectionLimitEast", self.sectionLimitEast)
        writeProjectDataDouble("SectionLimitSouth", self.sectionLimitSouth)
        writeProjectDataDouble("SectionLimitNorth", self.sectionLimitNorth)

#       Sections
        self.sectionManager.writeProjectData()
            