import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'drillsetup_dialog_base.ui'))


class DrillSetupDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(DrillSetupDialog, self).__init__(parent)
        
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
        self.lbDataLayer0.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer1.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer2.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.lbDataLayer3.setFilters(QgsMapLayerProxyModel.NoGeometry)

        # Initialise local variables and ComboBoxes
        self.checkDownNegative.setChecked(self.drillManager.downDipNegative)
        self.defaultSectionWidth.setText(str(self.drillManager.defaultSectionWidth))
        self.defaultSectionStep.setText(str(self.drillManager.defaultSectionStep))
        self.desurveyLength.setValue(self.drillManager.desurveyLength)
        self.initLayer(self.drillManager.collarLayer, self.lbCollarLayer, ["collar", "hole"])
        self.initLayer(self.drillManager.surveyLayer, self.lbSurveyLayer, ["survey"])
        self.initLayer(self.drillManager.dataLayer0, self.lbDataLayer0, ["lith", "geol"])
        self.initLayer(self.drillManager.dataLayer1, self.lbDataLayer1, ["assay"])
        self.initLayer(self.drillManager.dataLayer2, self.lbDataLayer2, ["susc"])
        self.initLayer(self.drillManager.dataLayer3, self.lbDataLayer3, ["dens"])
    
        self.lbCollarLayer.layerChanged.connect(self.onCollarLayerChanged)
        self.lbSurveyLayer.layerChanged.connect(self.onSurveyLayerChanged)
        self.lbDataLayer0.layerChanged.connect(self.onDataLayer0Changed)
        self.lbDataLayer1.layerChanged.connect(self.onDataLayer1Changed)
        self.lbDataLayer2.layerChanged.connect(self.onDataLayer2Changed)
        self.lbDataLayer3.layerChanged.connect(self.onDataLayer3Changed)

        self.onCollarLayerChanged()
        self.onSurveyLayerChanged()
        self.onDataLayer0Changed()
        self.onDataLayer1Changed()
        self.onDataLayer2Changed()
        self.onDataLayer3Changed()

    
    def initLayer(self, inLayer, cb, guessList):
        if inLayer is not None:
            if inLayer.isValid():
                cb.setLayer(inLayer)
            else:
                self.guessName(cb, guessList)
        
    def initField(self, inField, cb, guessList):
        index = -1
        if inField:
#            iface.messageBar().pushMessage("Debug", "InField name: " + inField.name(), level=Qgis.Info)
            index = cb.findText(inField, QtCore.Qt.MatchContains)
            
        if index > -1:
            cb.setCurrentIndex(index)
        else:
            self.guessName(cb, guessList)
            
    def onCollarLayerChanged(self):
        layer = self.lbCollarLayer.currentLayer()
        if layer is not None and layer.isValid():
            self.fbCollarId.setLayer(layer)
            self.initField(self.drillManager.collarId, self.fbCollarId, ["holeid", "bhid", "id", "hole", "name"])
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
        
    def onDataLayer0Changed(self):
        layer = self.lbDataLayer0.currentLayer()
        if layer is not None and layer.isValid():
            self.fbDataId0.setLayer(layer)
            self.initField(self.drillManager.dataId0, self.fbDataId0, ["holeid", "id", "hole", "name"])
            self.fbDataFrom0.setLayer(layer)
            self.initField(self.drillManager.dataFrom0, self.fbDataFrom0, ["from", "start", "depth"])
            self.fbDataTo0.setLayer(layer)
            self.initField(self.drillManager.dataTo0, self.fbDataTo0, ["to","end"])
        else:
            self.fbDataId0.setCurrentIndex(-1)
            self.fbDataFrom0.setCurrentIndex(-1)
            self.fbDataTo0.setCurrentIndex(-1)
        
    def onDataLayer1Changed(self):
        layer = self.lbDataLayer1.currentLayer()
        if layer is not None and layer.isValid():
            self.fbDataId1.setLayer(layer)
            self.initField(self.drillManager.dataId1, self.fbDataId1, ["holeid", "id", "hole", "name"])
            self.fbDataFrom1.setLayer(layer)
            self.initField(self.drillManager.dataFrom1, self.fbDataFrom1, ["from", "start", "depth"])
            self.fbDataTo1.setLayer(layer)
            self.initField(self.drillManager.dataTo1, self.fbDataTo1, ["to","end"])
        else:
            self.fbDataId1.setCurrentIndex(-1)
            self.fbDataFrom1.setCurrentIndex(-1)
            self.fbDataTo1.setCurrentIndex(-1)
        
    def onDataLayer2Changed(self):
        layer = self.lbDataLayer2.currentLayer()
        if layer is not None and layer.isValid():
            self.fbDataId2.setLayer(layer)
            self.initField(self.drillManager.dataId2, self.fbDataId2, ["holeid", "id", "hole", "name"])
            self.fbDataFrom2.setLayer(layer)
            self.initField(self.drillManager.dataFrom2, self.fbDataFrom2, ["from", "start", "depth"])
            self.fbDataTo2.setLayer(layer)
            self.initField(self.drillManager.dataTo2, self.fbDataTo2, ["to","end"])
        else:
            self.fbDataId2.setCurrentIndex(-1)
            self.fbDataFrom2.setCurrentIndex(-1)
            self.fbDataTo2.setCurrentIndex(-1)
        
    def onDataLayer3Changed(self):
        layer = self.lbDataLayer3.currentLayer()
        if layer is not None and layer.isValid():
            self.fbDataId3.setLayer(layer)
            self.initField(self.drillManager.dataId3, self.fbDataId3, ["holeid", "id", "hole", "name"])
            self.fbDataFrom3.setLayer(layer)
            self.initField(self.drillManager.dataFrom3, self.fbDataFrom3, ["from", "start", "depth"])
            self.fbDataTo3.setLayer(layer)
            self.initField(self.drillManager.dataTo3, self.fbDataTo3, ["to","end"])
        else:
            self.fbDataId3.setCurrentIndex(-1)
            self.fbDataFrom3.setCurrentIndex(-1)
            self.fbDataTo3.setCurrentIndex(-1)
        
    def guessName(self, cb, list):
        cb.setCurrentIndex(-1)
        for str in list:
            index = cb.findText(str, QtCore.Qt.MatchContains)
            if index > -1:
                cb.setCurrentIndex(index)
                break
            
        
    

