import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/addSurveys_dialog_base.ui'))


class addSurveysDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(addSurveysDialog, self).__init__(parent)
        
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

        # Setup ComboBox filters
        self.lbSurveyLayer.setFilters(QgsMapLayerProxyModel.NoGeometry)

        # Initialise local variables and ComboBoxes
        self.initLayer(self.drillManager.surveyLayer, self.lbSurveyLayer, ["survey"])
    
        self.lbSurveyLayer.layerChanged.connect(self.onSurveyLayerChanged)

        self.onSurveyLayerChanged()

    def onSurveyLayerChanged(self):
        layer = self.lbSurveyLayer.currentLayer()
        if layer is not None and layer.isValid():
            self.fbSurveyId.setLayer(layer)
            self.initField(self.drillManager.surveyId, self.fbSurveyId, ["holeid", "bhid", "id", "hole", "name"])
            self.fbSurveyDepth.setLayer(layer)
            self.initField(self.drillManager.surveyDepth, self.fbSurveyDepth, ["depth", "at"])
            self.fbSurveyAz.setLayer(layer)
            self.initField(self.drillManager.surveyAz, self.fbSurveyAz, ["azimuth", "az"])
            self.fbSurveyDip.setLayer(layer)
            self.initField(self.drillManager.surveyDip, self.fbSurveyDip, ["dip", "incl"])
        else:
            self.fbSurveyId.setCurrentIndex(-1)
            self.fbSurveyDepth.setCurrentIndex(-1)
            self.fbSurveyAz.setCurrentIndex(-1)
            self.fbSurveyDip.setCurrentIndex(-1)
        