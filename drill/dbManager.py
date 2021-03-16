#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Nov  6 07:31:50 2020

@author: roland
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:41:08 2019

@author: Roland Hill
roleyhill@gmail.com
"""

import os
import sqlite3
import pickle

from PyQt5.QtCore import QVariant
from PyQt5.QtWidgets import QProgressDialog, qApp

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from ..utils.utils import *

# The SectionManager class manipulates and keeps track of all the sections
class dbManager:
    def __init__(self, drillManager):
        self.drillManager = drillManager
        self.dbReg = [] #FilePath of registered databases
        self.currentDb = '' # FilePath of currently selected DB
        self.currentParameterLayer = None
        self.currentCrs = None
        
    def currentDbIndex(self):
        try:
            index = self.dbReg.index(self.currentDb)
        except:
            if len(self.dbReg) > 0:
                self.setCurrentDbFromIndex(0)
                index = 0
            else:
                index = -1
                
        return index
        
    def createDb(self, filePath, crs):
        if os.path.isfile(filePath):
            try:
                os.remove(filePath)
            except:
                iface.messageBar().pushMessage("Error", "Failed to delete existing file: %s"%(filePath), level=Qgis.Critical)
            
        lc = self.createCollarLayer(filePath, crs)
        if lc is None:
            iface.messageBar().pushMessage("Error", "Failed to create new database: %s"%(filePath), level=Qgis.Critical)
        else:    
            temp = self.currentDb
            self.currentDb = filePath
            conn = self.getDbConnection()
            c = conn.cursor()
            c.execute("CREATE TABLE Parameters (name TEXT NOT NULL UNIQUE, value TEXT, PRIMARY KEY(name))")
            c.execute("CREATE TABLE dhIntervals (name TEXT NOT NULL UNIQUE, PRIMARY KEY(name))")
            c.execute("CREATE TABLE dhPoints (name TEXT NOT NULL UNIQUE, PRIMARY KEY(name))")
    
            conn.commit()
            conn.close()        
            
        
#        l = QgsVectorLayer('None?field=name:string&field=value:string','Parameters', 'memory')
#        
#        options = QgsVectorFileWriter.SaveVectorOptions()
#        options.driverName = 'GPKG'
#        options.layerName = 'Parameters'
#        write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,filePath,options)
##        QgsProject.instance().removeMapLayer(l)
#        if write_result == QgsVectorFileWriter.NoError:
#            self.dbReg.append(filePath)
#            self.currentCrs = crs
#            
#            l = QgsVectorLayer(filePath + "|layername=Parameters", 'Parameters', 'ogr')
#            self.currentParameterLayer = l
#            
#            #Write basic data
            self.setParameter('VersionMajor', str(self.drillManager.dbVersionMajor) )
            self.setParameter('VersionMinor', str(self.drillManager.dbVersionMinor) )
            self.setParameter('CRS', crs.toWkt(variant=QgsCoordinateReferenceSystem.WktVariant.WKT2_2018))

            self.currentDb = temp
#
#            # Force the current DB to refresh incase the user has written over the same filename with the new one
#            self.setCurrentDb(filePath, force=True)
#
#            iface.messageBar().pushMessage("Geoscience", "New drill hole database created: %s"%(filePath), level=Qgis.Info)
#            
#        else:
#            iface.messageBar().pushMessage("Error", "Failed to create new database: %s"%(error_message), level=Qgis.Critical)

    
    def openDb(self, filePath):
        if not (filePath in self.dbReg):
            self.dbReg.append(filePath)
        self.setCurrentDb(filePath)
        
        self.writeProjectData()

    def closeDb():
        self.dbReg.remove(self.currentDb)
        if len(self.dbReg) > 0:
            self.setCurrentDbFromIndex(0)
        self.writeProjectData()
        
    def setCurrentDbFromIndex(self, regIndex):
        filePath = self.dbReg[regIndex]
        self.setCurrentDb(filePath)

    def setCurrentDb(self, filePath, force=False):
        if filePath != self.currentDb or force == True:
            # Test if the new DB is valid
            oldDb = self.currentDb
            self.currentDb = filePath
            ver = self.parameter('VersionMajor')
            if ver:
#                self.currentDb = filePath
                self.currentCrs = QgsCoordinateReferenceSystem.fromWkt(self.parameter('CRS', ''))
                self.drillManager.readParameters()
            else:
                self.currentDb = oldDb
                iface.messageBar().pushMessage("Error", "Attempt to open invalid database: %s"%(filePath), level=Qgis.Critical)
        
    def getOrCreateCollarLayer(self, clear = False):
        l = QgsVectorLayer(self.currentDb + "|layername=Collar", 'Collar', 'ogr')
        if l.isValid():
            if clear:
                with edit(l):
                    listOfIds = [feat.id() for feat in l.getFeatures()]
                    l.deleteFeatures( listOfIds )
        else:
            l = self.createCollarLayer(self.currentDb, self.currentCrs)
#            l = QgsVectorLayer('PointZ?crs=EPSG:4326','Collar', 'memory')
#            l.setCrs(self.currentCrs)
#            
#            options = QgsVectorFileWriter.SaveVectorOptions()
#            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
#            options.layerName = 'Collar'
#
#            write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,self.currentDb,options)
#            if write_result == QgsVectorFileWriter.NoError:
#                l = QgsVectorLayer(self.currentDb + "|layername=Collar", 'Collar', 'ogr')
#                atts = []
#                atts.append(QgsField("Id",  QVariant.String, "string", 16))
#                atts.append(QgsField("East",  QVariant.Double, "double", 12, 3))
#                atts.append(QgsField("North",  QVariant.Double, "double", 12, 3))
#                atts.append(QgsField("Elev",  QVariant.Double, "double", 8, 3))
#                atts.append(QgsField("Depth",  QVariant.Double, "double", 8, 3))
#                atts.append(QgsField("Az",  QVariant.Double, "double", 6, 2))
#                atts.append(QgsField("Dip",  QVariant.Double, "double", 6, 2))
#                
#                # Add all the attributes to the new layer
#                dp = l.dataProvider()
#                dp.addAttributes(atts)
#                
#                # Tell the vector layer to fetch changes from the provider
#                l.updateFields() 
#            else:
#                l = None
#                iface.messageBar().pushMessage("Error", "Failed to create collar layer", level=Qgis.Critical)

        return l
        
    def createCollarLayer(self, filePath, crs):
        l = QgsVectorLayer('PointZ?crs=EPSG:4326','Collar', 'memory')
        l.setCrs(crs)
        
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
#        options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
        options.layerName = 'Collar'
    
        write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,filePath,options)
        if write_result == QgsVectorFileWriter.NoError:
            l = QgsVectorLayer(filePath + "|layername=Collar", 'Collar', 'ogr')
            atts = []
            atts.append(QgsField("Id",  QVariant.String, "string", 16))
            atts.append(QgsField("East",  QVariant.Double, "double", 12, 3))
            atts.append(QgsField("North",  QVariant.Double, "double", 12, 3))
            atts.append(QgsField("Elev",  QVariant.Double, "double", 8, 3))
            atts.append(QgsField("Depth",  QVariant.Double, "double", 8, 3))
            atts.append(QgsField("Az",  QVariant.Double, "double", 6, 2))
            atts.append(QgsField("Dip",  QVariant.Double, "double", 6, 2))
            
            # Add all the attributes to the new layer
            dp = l.dataProvider()
            dp.addAttributes(atts)
            
            # Tell the vector layer to fetch changes from the provider
            l.updateFields() 
        else:
            l = None
            iface.messageBar().pushMessage("Error", "Failed to create collar layer", level=Qgis.Critical)

        return l       
    
    def getOrCreateSurveyLayer(self, clear = False):
        l = QgsVectorLayer(self.currentDb + "|layername=Survey", 'Survey', 'ogr')
        if l.isValid():
            if clear:
                with edit(l):
                    listOfIds = [feat.id() for feat in l.getFeatures()]
                    l.deleteFeatures( listOfIds )
        else:
#        l = QgsVectorLayer('None?field=name:string&field=value:string','Parameters', 'memory')
            l = QgsVectorLayer('None','Survey', 'memory')
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.layerName = 'Survey'

            write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,self.currentDb,options)
            if write_result == QgsVectorFileWriter.NoError:
                l = QgsVectorLayer(self.currentDb + "|layername=Survey", 'Survey', 'ogr')
                atts = []
                atts.append(QgsField("Id",  QVariant.String, "string", 16))
                atts.append(QgsField("Depth",  QVariant.Double, "double", 8, 3))
                atts.append(QgsField("Az",  QVariant.Double, "double", 6, 2))
                atts.append(QgsField("Dip",  QVariant.Double, "double", 6, 2))
                
                # Add all the attributes to the new layer
                dp = l.dataProvider()
                dp.addAttributes(atts)
                
                # Tell the vector layer to fetch changes from the provider
                l.updateFields() 
            else:
                l = None
                iface.messageBar().pushMessage("Error", "Failed to create survey layer", level=Qgis.Critical)

        return l

    def getOrCreateTraceLayer(self, clear = False):
            
        l = QgsVectorLayer(self.currentDb + "|layername=Trace", 'Trace', 'ogr')
        if l.isValid():
            if clear:
                with edit(l):
                    listOfIds = [feat.id() for feat in l.getFeatures()]
                    l.deleteFeatures( listOfIds )
        else:
            l = QgsVectorLayer('LineStringZ?crs=EPSG:4326','Trace', 'memory')
            l.setCrs(self.currentCrs)
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.layerName = 'Trace'

            write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,self.currentDb,options)
            if write_result == QgsVectorFileWriter.NoError:
                l = QgsVectorLayer(self.currentDb + "|layername=Trace", 'Trace', 'ogr')
                atts = []
                atts.append(QgsField("Id",  QVariant.String, "string", 16))
                
                # Add all the attributes to the new layer
                dp = l.dataProvider()
                dp.addAttributes(atts)
                
                # Tell the vector layer to fetch changes from the provider
                l.updateFields() 
            else:
                l = None
                iface.messageBar().pushMessage("Error", "Failed to create trace layer", level=Qgis.Critical)

        return l
        
    def createDrillholeTable(self):
        conn = self.getDbConnection()
        c = conn.cursor()
        c.execute("drop table if exists gs_drillhole")
        c.execute("CREATE TABLE gs_drillhole (Id TEXT NOT NULL UNIQUE, East REAL, North REAL, Elev REAL, Depth REAL, DesurveyLength REAL, Surveys BLOB, DesurveyPts BLOB, PRIMARY KEY(Id))")

        conn.commit()
        conn.close()        

    def insertDrillhole(self, curr, d):
            sdata = pickle.dumps(d._surveys, pickle.HIGHEST_PROTOCOL)
#            sdata = marshal.dumps(d._surveys)
            dsdata = pickle.dumps(d._desurveyPts, pickle.HIGHEST_PROTOCOL)
#            dsdata = marshal.dumps(d._desurveyPts)
            curr.execute("insert into gs_drillhole(Id, East, North, Elev, Depth, DesurveyLength, Surveys, DesurveyPts) values (?,?,?,?,?,?,?,?)", (d._collar._id, d._collar._east, d._collar._north, d._collar._elev, d._collar._depth, d._desurveyLength, sqlite3.Binary(sdata), sqlite3.Binary(dsdata)))
#            curr.execute("insert into gs_drillhole('Id', 'East', 'North', 'Elev', 'Depth') values (?,?,?,?,?)", (collar._id, collar._east, collar._north, collar._elev, collar._depth))

        
    def getDbConnection(self):
        conn = sqlite3.connect(self.currentDb)
        return conn
        
#    def setParameterLayer(self, name, layer):
#        val = 'None'
#        try:
#            val = layer.name()
#        except:
#            val = 'None'
#        self.setParameter(name, val)
#        
    def currentDbName(self):
        return os.path.splitext(os.path.basename(self.currentDb))[0]

    def setParameter(self, name, val):
        conn = self.getDbConnection()
        c = conn.cursor()
        c.execute("INSERT OR IGNORE INTO Parameters (name, value) VALUES (?, ?)", (name, val) )
        c.execute("UPDATE Parameters SET value = ? WHERE name=?", (val, name) )
# INSERT OR IGNORE INTO my_table (name, age) VALUES ('Karen', 34)
#UPDATE my_table SET age = 34 WHERE name='Karen'
        conn.commit()
        conn.close()        

#        if self.currentParameterLayer is not None:
#            f = self.parameterFeature(name)
#            self.currentParameterLayer.startEditing()
#            if f is not None:
#                f["value"] = val
#                self.currentParameterLayer.updateFeature(f)
#            else:
#                f = QgsFeature(self.currentParameterLayer.fields())
#
#                # Set the attributes for the new feature
#                f.setAttribute('name', name)
#                f.setAttribute('value', val)
#                self.currentParameterLayer.dataProvider().addFeature(f)
#            self.currentParameterLayer.commitChanges()

    def setParameterInt(self, name, val):
        self.setParameter(name, str(val))
        
    def setParameterBool(self, name, val):
        self.setParameterInt(name, 0 if val==False else 1)

    def setParameterFloat(self, name, val):
        self.setParameter(name, str(val))
        
    def parameter(self, name, default=''):
        result = default
        
        conn = self.getDbConnection()
        c = conn.cursor()
        c.execute("SELECT value FROM Parameters WHERE name = ?", (name,))
        results = c.fetchall()
        if len(results) > 0:
            result = results[0][0]
        conn.commit()
        conn.close()        
        
        return result

#        if self.currentParameterLayer is not None:
#            f = self.parameterFeature(name)
#            if f is not None:
#                return f.attributes()[2]
#            else:
#                return default
#        else:
#            return default
        
    def parameterInt(self, name, default):
        val = default
        res = self.parameter(name, '')
        if res != '':
            val = int(res)
        return val

    def parameterBool(self, name, default):
        val = self.parameterInt(name, 0 if default==False else 1)
        return val != 0

    def parameterFloat(self, name, default):
        val = default
        res = self.parameter(name, '')
        if res != '':
            val = float(res)
        return val

#    def parameterFeature(self, name):
#        self.currentParameterLayer.selectByExpression( '"name"=\'%s\''%(name) )
#        sel = self.currentParameterLayer.selectedFeatures()
#        if sel is not None and len(sel)>0:
#            return sel[0]
#        else:
#            return None
#            
    def dbRelPaths(self):
        rp = []
        projPath = projectPath()
        
        for path in self.dbReg:
            rp.append(os.path.relpath(path, projPath))

        return rp
    
    def writeProjectData(self):
        #We first need to remove excess section entries
        numDb = readProjectNum("DrillDBCount", 0)
        if numDb > len(self.dbReg):
            for index in range( len(self.dbReg), numDb):
                key = 'DB{:02d}_Name'.format(index)
                removeProjectEntry(key)
        
#         Now, write over with the needed ones        
#        msg = 'WriteData numSections: {:d}'.format(len(self.sectionReg))
#        iface.messageBar().pushMessage("Debug", msg, level=Qgis.Info)
        writeProjectData("DrillDBCount", len(self.dbReg))
        for index, name in enumerate(self.dbReg):
            key = 'DB{:02d}_Name'.format(index)
            writeProjectData(key, name)

        # Write the name of the current DB
        writeProjectData("CurrentDB", self.currentDb)
        
    def readProjectData(self):
        self.dbReg.clear()
        numDb= readProjectNum("DrillDBCount", 0)
        for index in range(numDb):
            key = 'DB{:02d}_Name'.format(index)
#            iface.messageBar().pushMessage("Debug", key, level=Qgis.Info)
            name = readProjectText(key, '')
            if not (name in self.dbReg):
                self.dbReg.append(name)
            
        # Read the name of the current DB
        self.setCurrentDb(readProjectText('CurrentDB', ''))
        