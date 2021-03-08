import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/desurveyHole_dialog_base.ui'))


class desurveyHoleDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(desurveyHoleDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.cbCurrentDb.addItems(manager.dbManager.dbRelPaths())
        self.cbCurrentDb.setCurrentIndex(self.drillManager.dbManager.currentDbIndex())
        
        # Initialise local variables and ComboBoxes
        self.checkDownDipNegative.setChecked(self.drillManager.downDipNegative)
        self.sbDesurveyLength.setValue(self.drillManager.desurveyLength)
    
