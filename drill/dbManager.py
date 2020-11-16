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
        return self.dbReg.index(self.currentDb)
        
    def createDb(self, filePath, crs):
        l = QgsVectorLayer('None?field=name:string&field=value:string','Parameters', 'memory')
        
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'Parameters'
        write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,filePath,options)
        if write_result == QgsVectorFileWriter.NoError:
            self.dbReg.append(filePath)
            self.currentCrs = crs
            self.setCurrentDb(filePath, force=True)
            
            #Write basic data
            self.setParameter('VersionMajor', str(self.drillManager.dbVersionMajor) )
            self.setParameter('VersionMinor', str(self.drillManager.dbVersionMinor) )
            self.setParameter('CRS', crs.toWkt(variant=QgsCoordinateReferenceSystem.WktVariant.WKT2_2018))

            iface.messageBar().pushMessage("Geoscience", "New drill hole database created: %s"%(filePath), level=Qgis.Info)
            
        else:
            iface.messageBar().pushMessage("Error", "Failed to create new database: %s"%(error_message), level=Qgis.Critical)

    
    def openDb(self, filePath):
        self.dbReg.append(filePath)
        self.setCurrentDb(filePath)

    def setCurrentDbFromIndex(self, regIndex):
        filePath = self.dbReg[regIndex]
        self.setCurrentDb(filePath)

    def setCurrentDb(self, filePath, force=False):
        if filePath != self.currentDb or force == True:
            l = QgsVectorLayer(filePath + "|layername=Parameters", 'Parameters', 'ogr')
            if l.isValid():
#                if self.currentParameterLayer is not None and self.currentParameterLayer.isValid():
#                    QgsProject.instance().removeMapLayers( [self.currentParameterLayer.id()] )
                self.currentDb = filePath
                self.currentParameterLayer = l
#                crs = self.parameter('CRS', '')
                self.currentCrs = QgsCoordinateReferenceSystem.fromWkt(self.parameter('CRS', ''))
#                if not self.currentCrs.isValid():
#                    iface.messageBar().pushMessage("Error", "CRS is invalid: %s"%(crs), level=Qgis.Critical)
                self.drillManager.collarLayer = self.getOrCreateCollarLayer()
                self.drillManager.readParameters()
            else:
                self.currentDb = ''
                self.currentParameterLayer = None
                self.drillManager.collarLayer = None
        
    def setParameter(self, name, val):
        if self.currentParameterLayer is not None:
            f = self.parameterFeature(name)
            self.currentParameterLayer.startEditing()
            if f is not None:
                f.setAttribute('value', val)
            else:
                f = QgsFeature(self.currentParameterLayer.fields())

                # Set the attributes for the new feature
                f.setAttribute('name', name)
                f.setAttribute('value', val)
                self.currentParameterLayer.dataProvider().addFeature(f)
            self.currentParameterLayer.commitChanges()

    def getOrCreateCollarLayer(self):
        l = QgsVectorLayer(self.currentDb + "|layername=Collar", 'Collar', 'ogr')
        if not l.isValid():
            l = QgsVectorLayer('PointZ?crs=EPSG:4326','Collar', 'memory')
            l.setCrs(self.currentCrs)
            
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.actionOnExistingFile = QgsVectorFileWriter.CreateOrOverwriteLayer
            options.layerName = 'Collar'

            write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,self.currentDb,options)
            if write_result == QgsVectorFileWriter.NoError:
                atts = []
                atts.append(QgsField("Id",  QVariant.String, "string", 12, 3))
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
        
#    def setParameterLayer(self, name, layer):
#        val = 'None'
#        try:
#            val = layer.name()
#        except:
#            val = 'None'
#        self.setParameter(name, val)
#        
    def setParameterInt(self, name, val):
        self.setParameter(name, str(val))
        
    def setParameterFloat(self, name, val):
        self.setParameter(name, str(val))
        
    def parameter(self, name, default=''):
        if self.currentParameterLayer is not None:
            f = self.parameterFeature(name)
            if f is not None:
                return f.attributes()[2]
            else:
                return default
        else:
            return default
        
    def parameterInt(self, name, default):
        val = default
        res = self.parameter(name, '')
        if res != '':
            val = int(res)
        return val

    def parameterFloat(self, name, default):
        val = default
        res = self.parameter(name, '')
        if res != '':
            val = float(res)
        return val

    def parameterFeature(self, name):
        sel = self.currentParameterLayer.selectByExpression( '"name"=%s'%(name) )
        if sel is not None:
            return sel[0]
        else:
            return None
            
    def dbRelPaths(self):
        rp = []
        projPath = projectPath()
        
        for path in self.dbReg:
            rp.append(os.path.relpath(path, projPath))

        return rp
    
    def writeProjectData(self):
        #We first need to remove excess section entries
        numDb = readProjectNum("DrillDBCount", 0)
        if numDb> len(self.dbReg):
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
            
        # Read the name of the current DB
        self.setCurrentDb(readProjectText('CurrentDB', ''))
        