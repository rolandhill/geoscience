import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .sectionorthogonal_dialog import SectionOrthogonalDialog
from .dialogBase import dialogBase

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectionmanager_dialog_base.ui'))


class SectionManagerDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(SectionManagerDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = manager
        self.sectionManager = self.drillManager.sectionManager
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.fillSectionList()
        
        self.pbWestEast.pressed.connect(self.onWestEastPressed)
        self.pbSouthNorth.pressed.connect(self.onSouthNorthPressed)

    def fillSectionList(self)        :
        self.listSection.clear()
        self.sectionManager.sectionReg.sort(key = lambda x: x.name)                        
        for s in self.sectionManager.sectionReg:
            item = QtWidgets.QListWidgetItem()
            item.setText(s.name)
#            item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
#            item.setCheckState(QtCore.Qt.Checked)
            item.setData(QtCore.Qt.UserRole, s)
            self.listSection.addItem(item)
        
    def onWestEastPressed(self):
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=True)
        dlg.show()
        result = dlg.exec_()
        if result:
            self.drillManager.sectionNorth = float(dlg.leCenter.text())
            self.drillManager.sectionLimitWest = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitEast = float(dlg.leLimitMax.text())
            self.drillManager.sectionName = dlg.leName.text()
            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = []
            for index in range(dlg.listLayers.count()):
                if dlg.listLayers.item(index).checkState():
                    self.drillManager.sectionLayers.append(dlg.listLayers.item(index).data(QtCore.Qt.UserRole))

            self.drillManager.writeProjectData()
            
        dlg.close()
        
        if result:
            self.sectionManager.createSection(self.drillManager.sectionName, \
              self.drillManager.sectionLimitWest, self.drillManager.sectionNorth, \
              self.drillManager.sectionLimitEast, self.drillManager.sectionNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers)
            
            self.fillSectionList()
        
    def onSouthNorthPressed(self):
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=False)
        dlg.show()
        result = dlg.exec_()
        if result:
            self.drillManager.sectionEast = float(dlg.leCenter.text())
            self.drillManager.sectionLimitSouth = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitNorth = float(dlg.leLimitMax.text())
            self.drillManager.sectionName = dlg.leName.text()
            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = []
            for index in range(dlg.listLayers.count()):
                if dlg.listLayers.item(index).checkState():
                    self.drillManager.sectionLayers.append(dlg.listLayers.item(index).data(QtCore.Qt.UserRole))

            self.drillManager.writeProjectData()
            
        dlg.close()
        
        if result:
            self.sectionManager.createSection(self.drillManager.sectionName, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitSouth, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers)

            self.fillSectionList()
