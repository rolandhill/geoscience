# -*- coding: utf-8 -*-
"""
Created on Wed May  8 17:45:45 2019

@author: HillR
"""

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from .Utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectionMapCanvas_dialog_base.ui'))


class SectionMapCanvasDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(SectionMapCanvasDialog, self).__init__(parent)
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        fillVectorLayersForSection(self.listLayers)
