import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/addCollars_dialog_base.ui'))


class addCollarsDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(addCollarsDialog, self).__init__(parent)
        
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

        # Initialise local variables and ComboBoxes
        self.initLayer(self.drillManager.collarLayer, self.lbCollarLayer, ["collar", "hole"])
    
        self.lbCollarLayer.layerChanged.connect(self.onCollarLayerChanged)

        self.onCollarLayerChanged()

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
        
