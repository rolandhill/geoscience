import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

# Load the UI file
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'downholestructure_dialog_base.ui'))


class DownholeStructureDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    """Dialog for managing downhole structures."""
    def __init__(self, manager, parent=None):
        """
        Constructor for DownholeStructureDialog.

        Args:
            manager (DrillManager): Instance of DrillManager.
            parent (QWidget): Parent widget (default is None).
        """
        super(DownholeStructureDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        # Set up initial configurations
        self.lbDesurveyLayer.setFilters(QgsMapLayerProxyModel.LineLayer)
        self.initLayer(self.drillManager.desurveyLayer, self.lbDesurveyLayer, ["desurvey"])
        self.lbDataLayer.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.initLayer(self.drillManager.structureLayer, self.lbDataLayer, ["struc"])
        self.checkSelectAll.setChecked(True)
        self.leSymbolSize.setText(str(self.drillManager.structureScale))

        # Connect signals to slots
        self.lbDataLayer.layerChanged.connect(self.onDataLayerChanged)
        self.checkSelectAll.toggled.connect(self.onSelectAllChecked)

        # Initialize configurations
        self.onDataLayerChanged()

    def onDataLayerChanged(self):
        """Handle changes in the data layer."""
        layer = self.lbDataLayer.currentLayer()
        if layer is not None and layer.isValid():
            self.fbDataId.setLayer(layer)
            self.initField(self.drillManager.structureId, self.fbDataId, ["holeid", "id", "hole", "name"])
            self.fbDataDepth.setLayer(layer)
            self.initField(self.drillManager.structureDepth, self.fbDataDepth, ["depth", "start", "from"])
            self.fbDataAlpha.setLayer(layer)
            self.initField(self.drillManager.structureAlpha, self.fbDataAlpha, ["alpha"])
            self.fbDataBeta.setLayer(layer)
            self.initField(self.drillManager.structureBeta, self.fbDataBeta, ["beta"])

            #Load the list widget
            self.listFields.clear()
            for field in layer.fields():
                item = QtWidgets.QListWidgetItem()
                item.setText(field.name())
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked)
                self.listFields.addItem(item)
        else:
            self.fbDataId.setCurrentIndex(-1)
            self.fbDataDepth.setCurrentIndex(-1)
            self.fbDataAlpha.setCurrentIndex(-1)
            self.fbDataBeta.setCurrentIndex(-1)
            self.listFields.clear()

    def onSelectAllChecked(self):
        """Handle 'Select All' checkbox state changes."""
        self.selectAll(self.listFields, self.checkSelectAll.isChecked())
