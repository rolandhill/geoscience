# -*- coding: utf-8 -*-
"""
Created on Wed May  8 17:45:45 2019

@author: HillR
"""

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from .Utils import *
from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectionMapCanvas_dialog_base.ui'))


class SectionMapCanvasDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SectionMapCanvasDialog, self).__init__(parent)
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.checkSelectAllLayers.setChecked(True)
        self.checkSelectAllElevation.setChecked(True)

        self.checkSelectAllLayers.toggled.connect(self.onSelectAllCheckedLayers)
        self.checkSelectAllElevation.toggled.connect(self.onSelectAllCheckedElevation)

        fillVectorLayersForSection(self.listLayers)
        fillRasterLayersForSection(self.listElevation)

    def onSelectAllCheckedLayers(self):
        self.selectAll(self.listLayers, self.checkSelectAllLayers.isChecked())
            
    def onSelectAllCheckedElevation(self):
        self.selectAll(self.listElevation, self.checkSelectAllElevation.isChecked())
            
            
