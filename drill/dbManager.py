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
        
    def currentDbIndex(self):
        return self.dbReg.index(self.currentDb)
        
    def createDb(self, filePath):
        l = QgsVectorLayer('None?field=name:string&field=value:string','Parameters', 'memory')
        
        options = QgsVectorFileWriter.SaveVectorOptions()
        options.driverName = 'GPKG'
        options.layerName = 'Parameters'
        write_result, error_message = QgsVectorFileWriter.writeAsVectorFormat(l,filePath,options)
        if write_result == QgsVectorFileWriter.NoError:
            self.dbReg.append(filePath)
            self.setCurrentDb(filePath)
            
            #Write basic data
            self.setParameter('VersionMajor', str(self.drillManager.dbVersionMajor) )
            self.setParameter('VersionMinor', str(self.drillManager.dbVersionMinor) )

            iface.messageBar().pushMessage("Geoscience", "New drill hole database created: %s"%(filePath), level=Qgis.Info)
            
        else:
            iface.messageBar().pushMessage("Error", "Failed to create new database: %s"%(error_message), level=Qgis.Critical)

    
    def openDb(self, filePath):
        self.dbReg.append(filePath)
        self.setCurrentDb(filePath)

    def setCurrentDbFromIndex(self, regIndex):
        filePath = self.dbReg[regIndex]
        self.setCurrentDb(filePath)

    def setCurrentDb(self, filePath):
        if filePath != self.currentDb:
            l = QgsVectorLayer(filePath + "|layername=Parameters", 'Parameters', 'ogr')
            if l.isValid():
                if self.currentParameterLayer is not None and self.currentParameterLayer.isValid():
                    QgsProject.instance().removeMapLayers( [self.currentParameterLayer.id()] )
                self.currentDb = filePath
                self.currentParameterLayer = l
            else:
                self.currentDb = ''
                self.currentParameterLayer = None
        
    def setParameter(self, name, val):
        if self.currentParameterLayer is not None:
            f = self.getParameterFeature(name)
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

    def getParameter(self, name, default):
        if self.currentParameterLayer is not None:
            f = self.getParameterFeature(name)
            if f is not None:
                return f.attributes()[2]
            else:
                return default
        else:
            return default
        
    def getParameterInt(self, name, default):
        return int(self.getParameter(name, default))

    def getParameterFloat(self, name, default):
        return float(self.getParameter(name, default))

    def getParameterFeature(self, name):
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