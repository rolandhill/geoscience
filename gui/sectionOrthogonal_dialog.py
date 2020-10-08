import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
from PyQt5.QtGui import QDoubleValidator
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from ..utils.utils import *
from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/sectionOrthogonal_dialog_base.ui'))


class sectionOrthogonalDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, dirWestEast=True, parent=None):
        """Constructor."""
        super(sectionOrthogonalDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        self.dirWestEast = dirWestEast
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)

#        self.leSectionWidth.setText(str(self.drillManager.sectionWidth))
        
        if dirWestEast == True:
            self.leCenter.setText(str(self.drillManager.sectionNorth))
            self.leLimitMin.setText(str(self.drillManager.sectionLimitWest))
            self.leLimitMax.setText(str(self.drillManager.sectionLimitEast))
            self.leName.setText(self.drillManager.sectionWEName)
        else:
            self.setWindowTitle("Create South-North section")
            self.lCenter.setText("East")
            self.lLimitMin.setText("South Limit")
            self.lLimitMax.setText("North Limit")
            
            self.leCenter.setText(str(self.drillManager.sectionEast))
            self.leLimitMin.setText(str(self.drillManager.sectionLimitSouth))
            self.leLimitMax.setText(str(self.drillManager.sectionLimitNorth))
            self.leName.setText(self.drillManager.sectionSNName)
    
        self.leCenter.setValidator(QDoubleValidator())
        self.leLimitMin.setValidator(QDoubleValidator())
        self.leLimitMax.setValidator(QDoubleValidator())
#        self.leSectionWidth.setValidator(QDoubleValidator())
        self.checkSelectAllLayers.setChecked(True)
        self.checkSelectAllElevation.setChecked(True)

        fillVectorLayersForSection(self.listLayers)
        fillRasterLayersForSection(self.listElevation)
        
        self.checkSelectAllLayers.toggled.connect(self.onSelectAllCheckedLayers)
        self.checkSelectAllElevation.toggled.connect(self.onSelectAllCheckedElevation)
        self.leCenter.textChanged.connect(self.onCenterTextChanged)
        
        self.nameManual = False

    def onCenterTextChanged(self, str):
        if not self.nameManual:
#            str = self.leCenter.text()
            if self.dirWestEast:
                str = str.strip() + "N"
            else:
                str = str.strip() + "E"
            self.leName.setText(str)

    def onSelectAllCheckedLayers(self):
        self.selectAll(self.listLayers, self.checkSelectAllLayers.isChecked())
            
    def onSelectAllCheckedElevation(self):
        self.selectAll(self.listElevation, self.checkSelectAllElevation.isChecked())
            
            
