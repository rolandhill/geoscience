# -*- coding: utf-8 -*-
"""
Created on Thu May 10 17:13:18 2018

@author: Roland Hill
"""

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ChangeDriveLetter_dialog_base.ui'))


class ChangeDriveLetterDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(ChangeDriveLetterDialog, self).__init__(parent)
        self.setupUi(self)
        
