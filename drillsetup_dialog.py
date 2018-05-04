import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'drillsetup_dialog_base.ui'))


class DrillSetupDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(DrillSetupDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.lbCollarLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.lbSurveyLayer.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer0.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer1.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer2.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer3.setFilters(QgsMapLayerProxyModel.NoGeometry)

        self.lbCollarLayer.layerChanged.connect(self.onCollarLayerChanged)

        self.onCollarLayerChanged()

    def onCollarLayerChanged(self):
        self.collarLayer = self.lbCollarLayer.currentLayer()
        if self.collarLayer.isValid():
            self.fbCollarId.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarId, ["holeid", "id", "hole", "name"])
            self.fbCollarEast.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarEast, ["east", "x"])
            self.fbCollarNorth.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarNorth, ["north", "y"])
            self.fbCollarElev.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarElev, ["elev", "rl", "z"])
            self.fbCollarAz.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarAz, ["azimuth", "az"])
            self.fbCollarDip.setLayer(self.collarLayer)
            self.guessFieldName(self.fbCollarDip, ["dip", "incl"])
        else:
            self.fbCollarId.setLayer(Null)
        
    def guessFieldName(self, fcb, list):
        fcb.setCurrentIndex(-1)
        for str in list:
            index = fcb.findText(str, QtCore.Qt.MatchContains)
            if index > -1:
                fcb.setCurrentIndex(index)
                break
            
        
    

