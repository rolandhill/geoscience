import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/desurveyhole_dialog_base.ui'))


class DesurveyHoleDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(DesurveyHoleDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        # Setup ComboBox filters
        self.lbCollarLayer.setFilters(QgsMapLayerProxyModel.PointLayer)
        self.lbSurveyLayer.setFilters(QgsMapLayerProxyModel.NoGeometry)

        # Initialise local variables and ComboBoxes
        self.checkDownDipNegative.setChecked(self.drillManager.downDipNegative)
#        self.teDefaultSectionWidth.setText(str(self.drillManager.defaultSectionWidth))
#        self.teDefaultSectionStep.setText(str(self.drillManager.defaultSectionStep))
        self.sbDesurveyLength.setValue(self.drillManager.desurveyLength)
        self.initLayer(self.drillManager.collarLayer, self.lbCollarLayer, ["collar", "hole"])
        self.initLayer(self.drillManager.surveyLayer, self.lbSurveyLayer, ["survey"])
    
        self.lbCollarLayer.layerChanged.connect(self.onCollarLayerChanged)
        self.lbSurveyLayer.layerChanged.connect(self.onSurveyLayerChanged)

        self.onCollarLayerChanged()
        self.onSurveyLayerChanged()

    def onCollarLayerChanged(self):
        layer = self.lbCollarLayer.currentLayer()
        if layer is not None and layer.isValid():
            self.fbCollarId.setLayer(layer)
            self.initField(self.drillManager.collarId, self.fbCollarId, ["holeid", "bhid", "id", "hole", "name"])
            self.fbCollarDepth.setLayer(layer)
            self.initField(self.drillManager.collarDepth, self.fbCollarDepth, ["eoh", "e.o.h", "totaldepth", "depth", "length"])
            self.fbCollarEast.setLayer(layer)
            self.initField(self.drillManager.collarEast, self.fbCollarEast, ["east", "x"])
            self.fbCollarNorth.setLayer(layer)
            self.initField(self.drillManager.collarNorth, self.fbCollarNorth, ["north", "y"])
            self.fbCollarElev.setLayer(layer)
            self.initField(self.drillManager.collarElev, self.fbCollarElev, ["elev", "rl", "z"])
            self.fbCollarAz.setLayer(layer)
            self.initField(self.drillManager.collarAz, self.fbCollarAz, ["azimuth", "az"])
            self.fbCollarDip.setLayer(layer)
            self.initField(self.drillManager.collarDip, self.fbCollarDip, ["dip", "incl"])
        else:
            self.fbCollarId.setCurrentIndex(-1)
            self.fbCollarEast.setCurrentIndex(-1)
            self.fbCollarNorth.setCurrentIndex(-1)
            self.fbCollarElev.setCurrentIndex(-1)
            self.fbCollarAz.setCurrentIndex(-1)
            self.fbCollarDip.setCurrentIndex(-1)
        
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
        
