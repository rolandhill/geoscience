import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import QDoubleValidator
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectionorthogonal_dialog_base.ui'))


class SectionOrthogonalDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, manager, dirWestEast=True, parent=None):
        """Constructor."""
        super(SectionOrthogonalDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        self.dirWestEast = dirWestEast
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

        self.leSectionWidth.setText(str(self.drillManager.sectionWidth))
        self.leName.setText(self.drillManager.sectionName)
        
        if dirWestEast == True:
            self.leCenter.setText(str(self.drillManager.sectionNorth))
            self.leLimitMin.setText(str(self.drillManager.sectionLimitWest))
            self.leLimitMax.setText(str(self.drillManager.sectionLimitEast))
        else:
            self.setWindowTitle("Create South-North section")
            self.lCenter.setText("East")
            self.lLimitMin.setText("South Limit")
            self.lLimitMax.setText("North Limit")
            
            self.leCenter.setText(str(self.drillManager.sectionEast))
            self.leLimitMin.setText(str(self.drillManager.sectionLimitSouth))
            self.leLimitMax.setText(str(self.drillManager.sectionLimitNorth))
    
        self.leCenter.setValidator(QDoubleValidator())
        self.leLimitMin.setValidator(QDoubleValidator())
        self.leLimitMax.setValidator(QDoubleValidator())
        self.leSectionWidth.setValidator(QDoubleValidator())

        self.listLayers.clear()
        layers = QgsProject.instance().mapLayers()
        for name, layer in layers.items():
            if layer.name()[:2] != "S_":
                if layer.name().find("_Desurvey") > -1 or layer.name().find("_Downhole_") > -1:
                    item = QtWidgets.QListWidgetItem()
                    item.setText(layer.name())
                    item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                    item.setCheckState(QtCore.Qt.Checked)
                    item.setData(QtCore.Qt.UserRole, layer)
                    self.listLayers.addItem(item)
        
        self.leCenter.textChanged.connect(self.onCenterTextChanged)
        
        self.nameManual = False

    def onCenterTextChanged(self, str):
        if not self.nameManual:
#            str = self.leCenter.text()
            if self.dirWestEast:
                str = str + "N"
            else:
                str = str + "E"
            self.leName.setText(str)
            
            