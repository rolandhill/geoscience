# -*- coding: utf-8 -*-
"""
Created on Thu Mar 28 17:41:08 2019

@author: HillR
"""

from qgis.core import *
from qgis.utils import *
from qgis.gui import *
import numpy as np

class Section:
    def __init__(self, name, startX, startY, endX, endY):
        self.name = name
        self.startX = startX
        self.startY = startY
        self.endX = endX
        self.endY = endY

        self.group = QgsLayerTreeGroup(self.name)
    
# The SectionManager class manipulates and keeps track of all the sections
class SectionManager:
    def __init__(self):
        self.sectionReg = []
        
    def createSection(self, name, startX, startY, endX, endY):
        sectionGroup = self.sectionGroup()
        s = Section(name, startX, startY, endX, endY)
        sectionGroup.addChildNode(s.group)
        
        self.sectionReg.append(s)

    def sectionGroup(self):
        group = None
        root = QgsProject.instance().layerTreeRoot()
        for child in root.children():
            if isinstance(child, QgsLayerTreeGroup) and child.name() == "Sections":
                group = child
                break
        
        if group == None:
            group = root.insertGroup(0, "Sections")
            
        return group
    
    