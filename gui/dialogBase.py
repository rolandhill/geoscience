# -*- coding: utf-8 -*-
"""
Created on Thu Jul 05 07:55:31 2018

@author: HillR
"""
from PyQt5 import QtCore
from qgis.gui import QgsFieldComboBox

# Dialog functions shared by mutliple dialogs, s oput them in a base class
class dialogBase():
    
    # Select the supplied layer in the supplied comboBox. If the layer is not valid, 
    # then guess which of the strings in the comboBox is the correct one by matching it 
    # to one of te supplied list of strings.
    def initLayer(self, inLayer, cb, guessList):
        if inLayer is not None:
            try:
                if inLayer.isValid():
                    cb.setLayer(inLayer)
            except:
                # Iterate through list of common strings to guess the correct entry in the comboBox
                self.guessName(cb, guessList)
        else:
            # Iterate through list of common strings to guess the correct entry in the comboBox
            self.guessName(cb, guessList)
        
    # Select the supplied Field Name in the supplied comboBox. If the field name is not valid, 
    # then guess which of the strings in the comboBox is the correct one by matching it 
    # to one of te supplied list of strings.
    def initField(self, inField, cb, guessList):
        index = -1
        if inField:
            index = cb.findText(inField, QtCore.Qt.MatchContains)
            
        if index > -1:
            cb.setCurrentIndex(index)
        else:
            self.guessName(cb, guessList)
            
    # From the list of common strings supplied, guess which comboBox entry is the correct one and select it
    def guessName(self, cb, list):
        cb.setCurrentIndex(-1)
        for str in list:
            index = cb.findText(str, QtCore.Qt.MatchContains)
            if index > -1:
                cb.setCurrentIndex(index)
                break
            
    def selectAll(self, listWidget, state):
        if state == True:
            for index in range(listWidget.count()):
                listWidget.item(index).setCheckState(QtCore.Qt.Checked)
        else:
            for index in range(listWidget.count()):
                listWidget.item(index).setCheckState(QtCore.Qt.Unchecked)
            
