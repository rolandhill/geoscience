import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'downholepoints_dialog_base.ui'))


class DownholePointsDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """
        Constructor for the DownholePointDialog class.

        param manager: DrillManager object.
        type manager: DrillManager
        param parent: Parent widget (optional).
        type parent: QWidget
        """
        super(DownholePointsDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Initialise and set filters for layers lists.
        self.lbDesurveyLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.initLayer(self.drillManager.desurveyLayer, self.lbDesurveyLayer, ["desurvey"])

        # Initialise layers and UI elements.
        self.lePointSeparation.setText(str(self.drillManager.pointSeparation))
        self.cbIncZero.setChecked(self.drillManager.pointIncZero)
        self.cbIncEOH.setChecked(self.drillManager.pointIncEOH)
