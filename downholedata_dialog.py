import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'downholedata_dialog_base.ui'))


class DownholeDataDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """
        Constructor for the DownholeDataDialog class.

        param manager: DrillManager object.
        type manager: DrillManager
        param parent: Parent widget (optional).
        type parent: QWidget
        """
        super(DownholeDataDialog, self).__init__(parent)
        
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
        self.lbDataLayer.setFilters(QgsMapLayerProxyModel.NoGeometry)
        self.initLayer(self.drillManager.dataLayer, self.lbDataLayer, ["lith", "geol"])
        self.checkSelectAll.setChecked(True)

        # Connect signals to slots.
        self.lbDataLayer.layerChanged.connect(self.onDataLayerChanged)
        self.checkSelectAll.toggled.connect(self.onSelectAllChecked)

        # Trigger initial data and setup dialog based on the current data layer.
        self.onDataLayerChanged()

    def onDataLayerChanged(self):
        """
        Handle changes in the selected data layer.

        This method is called when the user selects a different data layer.
        """
        layer = self.lbDataLayer.currentLayer()

        if layer is not None and layer.isValid():
            # Set up the data ID field combo box
            self.fbDataId.setLayer(layer)
            self.initField(self.drillManager.dataId, self.fbDataId, ["holeid", "id", "hole", "name"])
            # Set up the data "from" field combo box
            self.fbDataFrom.setLayer(layer)
            self.initField(self.drillManager.dataFrom, self.fbDataFrom, ["from", "start", "depth"])
            # Set up the data "to" field combo box
            self.fbDataTo.setLayer(layer)
            self.initField(self.drillManager.dataTo, self.fbDataTo, ["to","end"])
            # Clear the Suffix text
            self.teSuffix.clear()
            # Load the list widget with fields from the selected layer
            self.listFields.clear()
            for field in layer.fields():
                item = QtWidgets.QListWidgetItem()
                item.setText(field.name())
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Checked)
                self.listFields.addItem(item)
            self.setSuffix()
        else:
            self.fbDataId.setCurrentIndex(-1)
            self.fbDataFrom.setCurrentIndex(-1)
            self.fbDataTo.setCurrentIndex(-1)
            self.listFields.clear()

    def onSelectAllChecked(self):
        """
        Handles the "Select All" checkbox state change.

        This method is called when the user checks or unchecks the "Select All" checkbox.
        """
        self.selectAll(self.listFields, self.checkSelectAll.isChecked())
            
    def setSuffix(self):
        """
        Set the Suffix text based on the selected data layer's name.
        """
        str = self.lbDataLayer.currentLayer().name()
        loc = str.find("_")
        if loc > -1:
            str = str[loc+1:]
        self.teSuffix.setText(str)
        