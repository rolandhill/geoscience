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
import pickle

from ..external.quaternion import Quaternion

# Initialize Qt resources from file resources.py
from ..resources import *
from ..gui.newDb_dialog import newDbDialog
from ..gui.openDb_dialog import openDbDialog
from ..gui.addCollars_dialog import addCollarsDialog
from ..gui.addSurveys_dialog import addSurveysDialog
#from ..gui.addDownhole import addDownholeDialog
from ..gui.desurveyHole_dialog import desurveyHoleDialog
from ..gui.downHoleData_dialog import downholeDataDialog
from ..gui.sectionManager_dialog import sectionManagerDialog

from .sectionManager import *
from .dbManager import *
from ..utils.utils import *

import os.path
import math
import platform

class Collar:
#    def __init__(self, id, east, north, elev, depth, az=None, dip=None): 
    def __init__(self, id=None, east=None, north=None, elev=None, depth=None, az=None, dip=None): 
        self._id = id
        self._east = east
        self._north = north
        self._elev = elev
        self._depth = depth
        self._az = az
        self._dip = dip
        
    _id = ''
    _east = 0.0
    _north = 0.0
    _elev = 0.0
    _depth = 0.0
    _az = 0.0
    _dip = 0.0

class Survey:
    def __init__(self, depth=None, az=None, dip=None):
        self._depth = depth
        self._az = az
        self._dip = dip
        
    _depth = 0.0
    _az = 0.0
    _dip = 0.0
    
class DesurveyedPt:
    def __init__(self, depth, x, y, z):
        self._depth = depth
        self._x = x
        self._y = y
        self._z = z
        
class Drillhole:
    
    def __init__(self, collar, surveys = [], desurveyPts = [], desurveyLength = 1.0):
        self._collar = collar
        self._surveys = surveys
        self._desurveyPts = desurveyPts
        self._desurveyLength = desurveyLength
        
    def desurvey(self, desurveyLength):
        self._desurveyLength = desurveyLength
        self._desurveyPts.clear()
        
        # Create a quaternion for each survey
        quat = []
        for j, s in enumerate(self._surveys):
            # Rotate about positive X axis by dip degrees (depends on downDipNegative flag)
            qdip = Quaternion(axis=[1, 0, 0], degrees=s._dip)

            # Rotate about positive Z axis by -Az degrees                        
            qaz = Quaternion(axis=[0, 0, 1], degrees=-s._az)
            
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
            
        # Is the hole straight? If so, we can take short cuts
        holeStraight = (len(self._surveys) == 1)

        #Build drill trace every desurveyLength to EOH
        xs = []
        if holeStraight:
            xs.append(0.0)
        else:
            sz = int(self._collar._depth / self._desurveyLength) + 1
            depth = 0.0
            for d in range(0, sz):
                xs.append(depth)
                depth += self._desurveyLength
            if xs[-1] > self._collar._depth:
                xs[-1] = self._collar._depth
            if xs[-1] < self._collar._depth:
                xs.append(self._collar._depth)
            
        # We'll create a pointlist to hold all the 3D points
#        pointList = []
        # We start by adding the collar coordinates
        self._desurveyPts.append([0.0, self._collar._east, self._collar._north, self._collar._elev])
        # It's easier with a straight hole
        if holeStraight:
            # Calculate the offset of the bottom of hole from the top of hole in a single segment
            offset = quat[0].rotate(np.array([0.0, 1.0, 0.0])) * self._collar._depth
            # Add the offset to the collar
            p0 = self._desurveyPts[0]
            self._desurveyPts.append([self._collar._depth, p0[1] + offset[0], p0[2] + offset[1], p0[3] + offset[2]])
        else:
            # We're going to keep iterating through the survey list looking for the bracketing surveys.
            # We therefore record the start point of the iteration as it will only go up. Saves time.
            idx0 = 0
            # We already added the location at point0 (the collar) so start from 1
            for i in range(1, len(xs)):
                q = Quaternion()
                # Find the lowest survey equal or less than xs
                for j in range(idx0, len(self._surveys)):
                    # Is there a survey exactly at this point?
                    if self._surveys[j]._depth == xs[i]:
                        # Update the iteration start point
                        idx0 = j
                        q = quat[j]
                        break
                    # Are there surveys bracketing this depth? If so, interpolate point
                    if self._surveys[j]._depth < xs[i] and self._surveys[j+1]._depth >= xs[i]:
                        # Update the iteration start point
                        idx0 = j
                        # How far are we between bracketing surveys?
                        ratio = (xs[i] - self._surveys[j]._depth) / (self._surveys[j+1]._depth - self._surveys[j]._depth)
                        # Interpolate between bracketing survey rotations
                        q = Quaternion.slerp(quat[j], quat[j+1], ratio)
                        break

                # Calculate the deviation of this segment of the hole
                offset = q.rotate(np.array([0.0, 1.0, 0.0])) * self._desurveyLength
                # Calculate the new point by adding the offset to the old point
                p0 = self._desurveyPts[i-1]
                self._desurveyPts.append([xs[i], p0[0] + offset[0], p0[1] + offset[1], p0[2] + offset[2]])
       
# The DrillManager class controls all drill related data and methods 
class drillManager:
    def __init__(self):
        
        self.dbVersionMajor = 1
        self.dbVersionMinor = 0

        self.sectionManager = sectionManager(self)
        self.sectionManagerDlg = None
        
        self.dbManager = dbManager(self)
        
        # Project data is normally read in response to a readProject signal.
        # We also do it here for when the plugin is loaded other than at startup
        self.readProjectData()

        # Create a log file        
#        self.openLogFile()

    # Open a log file in the Collar Layer's directory
#    def openLogFile(self):
#        pass
#        # Maintain a log file in case of data errors
#        if self.collarLayer and self.collarLayer.isValid():
#            path=self.collarLayer.dataProvider().dataSourceUri()
#            fileName = uriToFile(os.path.join(os.path.split(path)[0], 'Geoscience_DrillManager_log.txt'))
#            self.logFile = open(fileName,'w')
#            if not self.logFile:
#                self.logFile = open(os.path.join(os.path.expanduser("~"), "Geoscience_DrillManager_log.txt"),'w')
#            self.logFile.write("Geoscience - DrillManager log file\n")
#            self.logFile.write("  Note: This file is overwritten each time you run Geoscience.\n")
#            self.logFile.write("  Make a copy if you want to keep the results.\n")
#            # We flush the buffers in case the plugin crashes without writing the message to the file
#            self.logFile.flush()

    # Setup and run the Drill Setup dialog        
    def onNewDb(self):
        dlg = newDbDialog(self)
        result = dlg.exec_()
        if result:
            filePath = dlg.fwNewDatabase.filePath()
            crs = dlg.wCrs.crs()
        dlg.close()

        if result:
            self.dbManager.createDb(filePath, crs)

    # Setup and run the Drill Setup dialog        
    def onOpenDb(self):
        dlg = openDbDialog(self)
        result = dlg.exec_()
        if result:
            filePath = dlg.fwDatabase.filePath()
        dlg.close()

        if result and filePath:
            self.dbManager.openDb(filePath)
            if self.dbManager.currentDb != '':
                pass
                # Create the group
                # Load collars, traces etc
                # Load sectionPlan

            # Setup and run the Drill Setup dialog        
    def onCloseDb(self):
        pass
    
    def checkValidDb(self):
        if self.dbManager.currentDb == '':
            self.onOpenDb();
            
    def onAddCollars(self):
        self.checkValidDb()
        dlg = addCollarsDialog(self)
        result = dlg.exec_()
        # If OK button clicked then retrieve and update values
        if result:
            self.dbManager.setCurrentDbFromIndex(dlg.cbCurrentDb.currentIndex())
            self.collarLayer = dlg.lbCollarLayer.currentLayer()
            self.collarId = dlg.fbCollarId.currentField()
            self.collarDepth = dlg.fbCollarDepth.currentField()
            self.collarEast = dlg.fbCollarEast.currentField()
            self.collarNorth = dlg.fbCollarNorth.currentField()
            self.collarElev = dlg.fbCollarElev.currentField()
            self.collarAz = dlg.fbCollarAz.currentField()
            self.collarDip = dlg.fbCollarDip.currentField()
        dlg.close()
            
        if result:
            self.dbManager.setParameter('CollarLayer', self.collarLayer.name())
            self.dbManager.setParameter('CollarId', self.collarId)
            self.dbManager.setParameter('CollarDepth', self.collarDepth)
            self.dbManager.setParameter('CollarEast', self.collarEast)
            self.dbManager.setParameter('CollarNorth', self.collarNorth)
            self.dbManager.setParameter('CollarElev', self.collarElev)
            self.dbManager.setParameter('CollarAz', self.collarAz)
            self.dbManager.setParameter('CollarDip', self.collarDip)

            self.addCollars()


    def onAddSurveys(self):
        self.checkValidDb()
        dlg = addSurveysDialog(self)
        result = dlg.exec_()
        # If OK button clicked then retrieve and update values
        if result:
            self.dbManager.setCurrentDbFromIndex(dlg.cbCurrentDb.currentIndex())
            self.surveyLayer = dlg.lbSurveyLayer.currentLayer()
            self.surveyId = dlg.fbSurveyId.currentField()
            self.surveyDepth = dlg.fbSurveyDepth.currentField()
            self.surveyAz = dlg.fbSurveyAz.currentField()
            self.surveyDip = dlg.fbSurveyDip.currentField()
        dlg.close()

        if result:
            self.dbManager.setParameter('SurveyLayer', self.surveyLayer.name())
            self.dbManager.setParameter('SurveyId', self.surveyId)
            self.dbManager.setParameter('SurveyDepth', self.surveyDepth)
            self.dbManager.setParameter('SurveyAz', self.surveyAz)
            self.dbManager.setParameter('SurveyDip', self.surveyDip)
            
            self.addSurveys()

    def onAddDownhole(self):
        pass
    
        # Setup and run the Drill Desurvey dialog        
    def onDesurveyHole(self):
        dlg = desurveyHoleDialog(self)
        result = dlg.exec_()
        # If OK button clicked then retrieve and update values
        if result:
            self.downDipNegative = dlg.checkDownDipNegative.isChecked()
            self.desurveyLength = dlg.sbDesurveyLength.value()
        dlg.close()

        if result:
            self.dbManager.setParameterFloat('DesurveyLength', self.desurveyLength)
            self.dbManager.setParameterBool('DownDipNegative', self.downDipNegative)

            self.desurveyHoles()


    # Setup and run the Drill Trace dialog
    def onAddDownhole(self):
        dlg = downholeDataDialog(self)
#        dlg.show()
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

#    # Desurvey the data        
#    def onDesurveyHole(self):
#        self.desurveyData()
#
    # Create a section
    def onDrillSectionManager(self):
        if self.sectionManagerDlg is None:
            self.sectionManagerDlg = sectionManagerDialog(self)

        self.sectionManagerDlg.show()
        self.sectionManagerDlg.activateWindow()
        self.sectionManagerDlg.fillSectionList()

    # Create the down hole traces    
    def createDownholeData(self):
#        self.logFile.write("\nCreating Downhole Data Layer.\n")
#        self.logFile.flush()
        
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

        # Create memory layer
        layer = self.createDownholeLayer()

        # Get the fields from the data layer
        dp = self.dataLayer.dataProvider()
        idxId = dp.fieldNameIndex(self.dataId)
        idxFrom = dp.fieldNameIndex(self.dataFrom)
        idxTo = dp.fieldNameIndex(self.dataTo)
        # Create a list of attribute indices from the desired attribute field names
        idxAttList = []
        for name in self.dataFields:
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
                dataTo = float(attrs[idxTo])
            except:
                floatConvError = True
                
            if (dataId==NULL) or (dataFrom==NULL) or (dataTo==NULL):
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

                
            # Create line representing the downhole value using From and To
            pointList = []
            # Calculate indices spanning the from and to depths, then linearly interpolate a position
            try:
                pFrom, iFrom = interpPolyline(dataFrom, currentTraceSegLength, currentTracePolyline)
            except:
#                self.logFile.write("Error interpolating from polyline for hole: %s From: %f in row: %d.\n" % (dataId, dataFrom, index))
                continue

            try:
                pTo, iTo = interpPolyline(dataTo, currentTraceSegLength, currentTracePolyline)
            except:
#                self.logFile.write("Error interpolating from polyline for hole: %s To: %f in row: %d.\n" % (dataId, dataTo, index))
                continue

            # Add the first (From) point to the list
            pointList.append(pFrom)
            # Add all the intermediate points (so a long interval accurately reflects the bend of the hole)
            if math.floor(iTo) - math.ceil(iFrom) > 1:
                for i in range(math.ceil(iFrom), math.floor(iTo)):
                    pointList.append(currentTracePolyline[i])
            # Add the last (To) point
            pointList.append(pTo)
            
            # Set the geometry for the new downhole feature
            feature.setGeometry(QgsGeometry.fromPolyline(pointList))

            # Create a list of the attributes to be included in new file
            # These are just copied from the original down hole layer
            # according to whether the user selected the check boxes
            attList = []
            for idx in idxAttList:
                attList.append(attrs[idx])

            # Also append the 3D desurveyed From, To and Mid points
            attList.append(pointList[0].x())
            attList.append(pointList[0].y())
            attList.append(pointList[0].z())
            attList.append(pointList[1].x())
            attList.append(pointList[1].y())
            attList.append(pointList[1].z())
            attList.append((pointList[0].x()+pointList[1].x())*0.5)
            attList.append((pointList[0].y()+pointList[1].y())*0.5)
            attList.append((pointList[0].z()+pointList[1].z())*0.5)

            # Set the attributes for the new feature
            feature.setAttributes(attList)

            # Add the new feature to the new Trace_ layer
            layer.startEditing()
            layer.addFeature(feature)
            layer.commitChanges()

        # Flush the log file in case anything was written
#        self.logFile.flush()
        
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
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, fileName, "CP1250", self.desurveyLayer.crs(), layerOptions=['OVERWRITE=YES'])
            
        # Load the one we just saved and add it to the map
        layer = QgsVectorLayer(fileName+".gpkg", label)
        QgsProject.instance().addMapLayer(layer)
        
    def addCollars(self):
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
#        arrCollar = []

        # Update the progress bar
        pd.setWindowTitle("Adding Collars")
        pd.setMaximum(numCollars)
        pd.setValue(0)
        
        floatConvError = False
        nullDataError = False

        l = self.dbManager.getOrCreateCollarLayer()
        
        # Loop through the collar layer and build list of collars
        for index, feature in enumerate(self.collarLayer.getFeatures()):
            # Update progress bar
            pd.setValue(index)
            
            # get the feature's attributes
            attrs = feature.attributes()
            c = Collar()
            # Check all the data is valid
            c._id = str(attrs[idxCollarId])
            try:
                c._east = float(attrs[idxCollarEast])
                c._north = float(attrs[idxCollarNorth])
                c._elev = float(attrs[idxCollarElev])
                c._depth = float(attrs[idxCollarDepth])
            except:
                floatConvError = True
                
            if (c._id==NULL) or (c._east==NULL) or (c._north==NULL) or (c._elev==NULL) or (c._depth==NULL):
                nullDataError = True
                continue
            c._id = c._id.strip()
            if useCollarAzDip:
                az = attrs[idxCollarAz]
                if az==NULL:
                    az = 0.0
                dip = attrs[idxCollarDip]
                if dip==NULL:
                    dip = -90 if self.downDipNegative else 90
#            arrCollar.append(c)
            
            #Create a new 3D point feature and copy the attributes
            f = QgsFeature(l.fields())
#            p = QPointF(c.east, c.north, c.elev)
            f.setGeometry(QgsGeometry(QgsPoint(c._east, c._north, c._elev, wkbType = QgsWkbTypes.PointZ)))
            # Add in the field attributes
            f.setAttribute('Id', c._id)
            f.setAttribute('East', c._east)
            f.setAttribute('North', c._north)
            f.setAttribute('Elev', c._elev)
            f.setAttribute('Depth', c._depth)
            if useCollarAzDip:
                f.setAttribute('Az', az)
                f.setAttribute('Dip', dip)
#            f.setAttribute(attrs)
            # Add the feature to the layer
            l.startEditing()
            l.addFeature(f)
            l.commitChanges()
            
            
        if (floatConvError):
            iface.messageBar().pushMessage("Warning", "Some 'East', 'North', 'Collar' or 'Depth' values are not numbers", level=Qgis.Warning)
        if (nullDataError):
            iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'East', 'North', 'Collar' or 'Depth' values are NULL. These have been skipped", level=Qgis.Warning)

        
    def addSurveys(self):
        # Set up a progress bar
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        
        # Get the attribute indices
        dp = self.surveyLayer.dataProvider()
        idxSurveyId = dp.fieldNameIndex(self.surveyId)
        idxSurveyDepth = dp.fieldNameIndex(self.surveyDepth)
        idxSurveyAz = dp.fieldNameIndex(self.surveyAz)
        idxSurveyDip = dp.fieldNameIndex(self.surveyDip)

        # Build Survey array (Id, depth, az, dip)
        numSurveys = self.surveyLayer.featureCount()
        arrSurvey = []
        l = self.dbManager.getOrCreateSurveyLayer()
            
        # Update progress bar
        pd.setWindowTitle("Adding Surveys")
        pd.setMaximum(numSurveys)
        pd.setValue(0)
        
        floatConvError = False
        nullDataError = False
        
        #Loop through Survey layer and build list of surveys
        for index, feature in enumerate(self.surveyLayer.getFeatures()):
            pd.setValue(index)
            
            # get the feature's attributes
            attrs = feature.attributes()
            s = Survey()
            id = str(attrs[idxSurveyId])
            try:
                s._depth = float(attrs[idxSurveyDepth])
                s._az = float(attrs[idxSurveyAz])
                s._dip = float(attrs[idxSurveyDip])
            except:
                floatConvError = True
                
            if (id==NULL) or (s._depth==NULL) or (s._az==NULL) or (s._dip==NULL):
                nullDataError = True
                continue
            id = id.strip()
            arrSurvey.append(s)
    
            #Create a new 3D point feature and copy the attributes
            f = QgsFeature(l.fields())
            # Add in the field attributes
            f.setAttribute('Id', id)
            f.setAttribute('Depth', s._depth)
            f.setAttribute('Az', s._az)
            f.setAttribute('Dip', s._dip)
            # Add the feature to the layer
            l.startEditing()
            l.addFeature(f)
            l.commitChanges()
            
        if (floatConvError):
            iface.messageBar().pushMessage("Warning", "Some survey 'Depth', 'Azimuth' or 'Dip' values are not numbers", level=Qgis.Warning)
        if (nullDataError):
            iface.messageBar().pushMessage("Warning", "Some 'HoleId', 'Depth', 'Azimuth' or 'Dip' values are NULL. These have been skipped", level=Qgis.Warning)
            
    def surveysForHole(self, curr, collar):
        #Build array of surveys for this collar, including the top az and dip in collar layer. Repeat last survey at EOH.
        surveys = []
        
        curr.execute("SELECT * FROM Survey WHERE id = '%s'" % collar._id)
        for row in curr:
            s = Survey(row[2], row[3], row[4] if self.downDipNegative else -row[4])
            surveys.append(s)

#            if len(arrSurvey) > 0:
#                # Harvest surveys for this collar from Survey layer list
#                for survey in arrSurvey:
#                    if survey.id == collar.id:
#                        s = Surveys()
#                        s.depth = survey.depth
#                        s.az = survey.az
#                        s.dip = survey.dip
#                        surveys.append(s)
#
        # If the az and dip from the collar are to be used, then insert them at depth 0.0
        # We only do this if there are no surveys from the Survey layer
        if len(surveys) == 0 and collar._az is not None and collar._dip is not None:
            s = Survey(0.0, collar._az, collar._dip)
            surveys.append(s)
        
        # If there are no surveys, then the assume hole is vertical
        if len(surveys) == 0:
            s = Survey(0.0, 0.0, -90.0)
            surveys.append(s)
            
        # Is the hole straight? If so, we can take short cuts
        holeStraight = (len(surveys) == 1)

        # We only replicate survey to the beginning and end if the hole is not straight
        if not holeStraight:
            # Sort the surveys array by depth
            surveys.sort(key = lambda x: x._depth)                        
        
            # If surveys exist, but there isn't one at 0.0, then replicate first survey at 0.0
            if not surveys[0]._depth == 0.0:
                s = Survey()
                surveys.insert(0, s)
                s._depth = 0.0
                surveys[0]._az = surveys[1]._az
                surveys[0]._dip = surveys[1]._dip
                
            # If the last survey isn't at the end of hole, then repeat the last one at eoh
            if len(surveys) > 0 and surveys[-1]._depth < collar._depth:
                s = Survey()
                s._depth = collar._depth
                s._az = surveys[-1]._az
                s._dip = surveys[-1]._dip
                surveys.append(s)
                
        return surveys

        
    def desurveyHoles(self):
        # Set up a progress bar
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        
        lc = self.dbManager.getOrCreateCollarLayer()
        ls = self.dbManager.getOrCreateSurveyLayer()
        
        self.dbManager.createDrillholeTable()
        conn = self.dbManager.getDbConnection()
        curr = conn.cursor()
        
        #Loop through collar list and desurvey each one
        # Update Progress bar
        pd.setWindowTitle("Desurvey Progress")
        pd.setMaximum(lc.featureCount())
        pd.setValue(0)
        #Calculate optimum update interval
        updateInt = max(100, int(lc.featureCount()/100))
        
        dp = lc.dataProvider()
        iId = dp.fieldNameIndex('Id')
        iEast = dp.fieldNameIndex('East')
        iNorth = dp.fieldNameIndex('North')
        iElev = dp.fieldNameIndex('Elev')
        iDepth = dp.fieldNameIndex('Depth')
        iAz = dp.fieldNameIndex('Az')
        iDip = dp.fieldNameIndex('Dip')

        # We count how many drill holes are inserted so we can use the value later
        # It's not efficient to read it from SQLite3 tables
        self.numDrillholes = 0
        # Enter collar loop
        for index, feature in enumerate(lc.getFeatures()):
            pd.setValue(index)
            # Force update the progress bar visualisation every 1% as it normally only happens in idle time
            if index%updateInt == 0:
                qApp.processEvents()

            att = feature.attributes()
            collar = Collar(att[iId], att[iEast], att[iNorth], att[iElev], att[iDepth], att[iAz], att[iDip])
#            az = att[iAz]
#            dip = att[iDip]
            
            # Check the id exists                
            if not collar._id:
                continue

            surveys = self.surveysForHole(curr, collar)            
            d = Drillhole(collar, surveys)
            d.desurvey(self.desurveyLength)
            
            self.dbManager.insertDrillhole(curr, d)
            self.numDrillholes += 1
        conn.commit()
        conn.close()      
        
        self.dbManager.setParameterInt('NumDrillholes', self.numDrillholes)

    def drillTrace():
        # Set up a progress bar
        pd = QProgressDialog()
        pd.setAutoReset(False)
        pd.setMinimumWidth(500)
        pd.setMinimum(0)
        
        # Update Progress bar
        pd.setWindowTitle("Create Trace Layer Progress")
        pd.setMaximum(self.numDrillholes)
        pd.setValue(0)
        #Calculate optimum update interval
        updateInt = max(100, int(self.numDrillholes/100.0))

        lt = self.dbManager.getOrCreateTraceLayer()
        
        conn = self.dbManager.getDbConnection()
        curr = conn.cursor()
        
        curr.execute("SELECT * FROM gs_drillhole")

        #Loop through collar list and desurvey each one
        for row in curr:
<--------------------------------------
            
        conn.commit()
        conn.close()        


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
    
#    def createCollarLayer(self):
#        #Find CRS of collar layer
#        crs = self.collarLayer.crs()
#        
#        #Create a new memory layer
#        layer = QgsVectorLayer("PointZ?crs=EPSG:4326", "geoscience_Temp", "memory")
#        layer.setCrs(crs)
#
#        atts = []
#        # Loop through the list of desired field names that the user checked
#        for field in self.collarLayer.fields():
#            atts.append(field)
#        
#        # Add all the attributes to the new layer
#        dp = layer.dataProvider()
#        dp.addAttributes(atts)
#        
#        # Tell the vector layer to fetch changes from the provider
#        layer.updateFields() 
#        return layer
#    
    def createDownholeLayer(self):
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

#    def setCollarFields(self, id, depth, east, north, elev, az, dip):
#        self.collarId = id
#        self.collarDepth = depth
#        self.collarEast = east
#        self.collarNorth = north
#        self.collarElev = elev
#        self.collarAz = az
#        self.collarDip = dip
#
#        self.dbManager.setParameter('CollarId', self.collarId)
#        self.dbManager.setParameter('CollarDepth', self.collarDepth)
#        self.dbManager.setParameter('CollarEast', self.collarEast)
#        self.dbManager.setParameter('CollarNorth', self.collarNorth)
#        self.dbManager.setParameter('CollarElev', self.collarElev)
#        self.dbManager.setParameter('CollarAz', self.collarAz)
#        self.dbManager.setParameter('CollarDip', self.collarDip)
        
    def readParameters(self):
        self.collarLayer = self.dbManager.parameter('CollarLayer')
        self.collarId = self.dbManager.parameter('CollarId')
        self.collarDepth = self.dbManager.parameter('CollarDepth')
        self.collarEast = self.dbManager.parameter('CollarEast')
        self.collarNorth = self.dbManager.parameter('CollarNorth')
        self.collarElev = self.dbManager.parameter('CollarElev')
        self.collarAz = self.dbManager.parameter('CollarAz')
        self.collarDip = self.dbManager.parameter('CollarDip')

        self.surveyLayer = self.dbManager.parameter('SurveyLayer')
        self.surveyId = self.dbManager.parameter('SurveyId')
        self.surveyDepth = self.dbManager.parameter('SurveyDepth')
        self.surveyAz = self.dbManager.parameter('SurveyAz')
        self.surveyDip = self.dbManager.parameter('SurveyDip')
        
        self.numDrillholes = self.dbManager.parameterInt('NumDrillholes')
        
        self.desurveyLength = self.dbManager.parameterFloat('DesurveyLength', 1.0)
        self.downDipNegative = self.dbManager.parameterBool('DownDipNegative', True)

    # Read all the saved DrillManager parameters from the QGIS project        
    def readProjectData(self):
        self.dbManager.readProjectData()
        
#       Desurvey & Downhole Data
#        self.currentDb = readProjectNum("CurrentDb", '')
#        self.desurveyLength = readProjectNum("DesurveyLength", 1)
#        self.downDipNegative = readProjectBool("DownDipNegative", True)
#        self.desurveyLayer = readProjectLayer("DesurveyLayer")
#        self.collarLayer = readProjectLayer("CollarLayer")
#        self.surveyLayer = readProjectLayer("SurveyLayer")
#        self.dataLayer = readProjectLayer("DataLayer")
#        self.collarId = readProjectField("CollarID")
#        self.collarDepth = readProjectField("CollarDepth")
#        self.collarEast = readProjectField("CollarEast")
#        self.collarNorth = readProjectField("CollarNorth")
#        self.collarElev = readProjectField("CollarElev")
#        self.collarAz = readProjectField("CollarAz")
#        self.collarDip = readProjectField("CollarDip")
#        self.surveyId = readProjectField("SurveyID")
#        self.surveyDepth = readProjectField("SurveyDepth")
#        self.surveyAz = readProjectField("SurveyAz")
#        self.surveyDip = readProjectField("SurveyDip")
        self.dataId = readProjectField("DataID")
        self.dataFrom = readProjectField("DataFrom")
        self.dataTo = readProjectField("DataTo")
        self.dataSuffix = readProjectField("DataSuffix")
#       Section Data
        self.sectionWEName = readProjectText("SectionWEName", '')
        self.sectionSNName = readProjectText("SectionSNName", '')
        self.sectionName = readProjectText("SectionName", '')
        self.sectionWidth = readProjectNum("SectionWidth", 20)
        self.sectionStep = readProjectNum("SectionStep", 50)
        self.sectionNorth = readProjectNum("SectionNorth", 0)
        self.sectionEast = readProjectNum("SectionEast", 0)
        self.sectionLimitWest = readProjectNum("SectionLimitWest", 0)
        self.sectionLimitEast = readProjectNum("SectionLimitEast", 1)
        self.sectionLimitSouth = readProjectNum("SectionLimitSouth", 0)
        self.sectionLimitNorth = readProjectNum("SectionLimitNorth", 1)

        self.sectionManager.readProjectData()        

        # Collar layer might have changed, so re-open the log file
#        self.openLogFile()

    # Write all DrillManager parameters to the QGIS project file
    def writeProjectData(self):
        self.dbManager.writeProjectData()
        
#       Desurvey & Downhole Data
        writeProjectData("DesurveyLength", self.desurveyLength)
        writeProjectData("DownDepthNegative", self.downDipNegative)
#        writeProjectLayer("DesurveyLayer", self.desurveyLayer)
#        writeProjectLayer("CollarLayer", self.collarLayer)
#        writeProjectLayer("SurveyLayer", self.surveyLayer)
#        writeProjectLayer("DataLayer", self.dataLayer)
#        writeProjectField("CollarID", self.collarId)
#        writeProjectField("CollarDepth", self.collarDepth)
#        writeProjectField("CollarEast", self.collarEast)
#        writeProjectField("CollarNorth", self.collarNorth)
#        writeProjectField("CollarElev", self.collarElev)
#        writeProjectField("CollarAz", self.collarAz)
#        writeProjectField("CollarDip", self.collarDip)
#        writeProjectField("SurveyID", self.surveyId)
#        writeProjectField("SurveyDepth", self.surveyDepth)
#        writeProjectField("SurveyAz", self.surveyAz)
#        writeProjectField("SurveyDip", self.surveyDip)
        writeProjectField("DataID", self.dataId)
        writeProjectField("DataFrom", self.dataFrom)
        writeProjectField("DataTo", self.dataTo)
        writeProjectField("DataSuffix", self.dataSuffix)
#       Section Dialog Data
        writeProjectData("SectionWEName", self.sectionWEName)
        writeProjectData("SectionSNName", self.sectionSNName)
        writeProjectData("SectionName", self.sectionName)
        writeProjectData("SectionWidth", self.sectionWidth)
        writeProjectData("SectionStep", self.sectionStep)
        writeProjectData("SectionNorth", self.sectionNorth)
        writeProjectData("SectionEast", self.sectionEast)
        writeProjectData("SectionLimitWest", self.sectionLimitWest)
        writeProjectData("SectionLimitEast", self.sectionLimitEast)
        writeProjectData("SectionLimitSouth", self.sectionLimitSouth)
        writeProjectData("SectionLimitNorth", self.sectionLimitNorth)

#       Sections
        self.sectionManager.writeProjectData()
            