# -*- coding: utf-8 -*-
"""
Created on Thu Jul 05 07:55:31 2018

@author: HillR
"""
from PyQt5 import QtCore
from qgis.gui import QgsFieldComboBox

class QgisDialogBase():
    def initLayer(self, inLayer, cb, guessList):
        if inLayer is not None:
            try:
                if inLayer.isValid():
                    cb.setLayer(inLayer)
            except:
                self.guessName(cb, guessList)
        else:
            self.guessName(cb, guessList)
        
    def initField(self, inField, cb, guessList):
        index = -1
        if inField:
            index = cb.findText(inField, QtCore.Qt.MatchContains)
            
        if index > -1:
            cb.setCurrentIndex(index)
        else:
            self.guessName(cb, guessList)
            
    def guessName(self, cb, list):
        cb.setCurrentIndex(-1)
        for str in list:
            index = cb.findText(str, QtCore.Qt.MatchContains)
            if index > -1:
                cb.setCurrentIndex(index)
                break
            
