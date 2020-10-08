import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .sectionOrthogonal_dialog import sectionOrthogonalDialog
from .dialogBase import dialogBase
from .sectionMapTool import sectionMapTool
from ..utils.utils import *

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/sectionManager_dialog_base.ui'))


class sectionManagerDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, drillManager, parent=None):
        """Constructor."""
        super(sectionManagerDialog, self).__init__(parent)
        
        # Keep a reference to the DrillManager
        self.drillManager = drillManager
        self.sectionManager = self.drillManager.sectionManager
        self.sectionMapTool = SectionMapTool(iface.mapCanvas(), self)
        
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        self.leSectionWidth.setText(str(self.drillManager.sectionWidth))
        
        self.fillSectionList()

        self.pbMapCanvas.pressed.connect(self.onMapCanvasPressed)        
        self.pbWestEast.pressed.connect(self.onWestEastPressed)
        self.pbSouthNorth.pressed.connect(self.onSouthNorthPressed)
        self.pbDeleteSection.pressed.connect(self.onDeletePressed)
        self.pbShowSection.pressed.connect(self.onShowPressed)
        self.pbNewWindow.pressed.connect(self.onNewWindowPressed)
        self.pbRecreate.pressed.connect(self.onRecreatePressed)
        self.listSection.itemDoubleClicked.connect(self.onListItemdoubleClicked)
        self.checkSelectAll.toggled.connect(self.onSelectAllChecked)

    def fillSectionList(self)        :
        self.listSection.clear()
        if len(self.sectionManager.sectionReg) > 0:
            self.sectionManager.sectionReg.sort(key = lambda x: x.name)                        
            for s in self.sectionManager.sectionReg:
                item = QtWidgets.QListWidgetItem()
                item.setText(s.name)
                item.setFlags(item.flags() | QtCore.Qt.ItemIsUserCheckable)
                item.setCheckState(QtCore.Qt.Unchecked)
                item.setData(QtCore.Qt.UserRole, s)
                self.listSection.addItem(item)
        
    def onMapCanvasPressed(self):
        self.drillManager.sectionWidth = float(self.leSectionWidth.text())
        iface.mapCanvas().activateWindow()
        self.sectionMapTool.oldMapTool = iface.mapCanvas().mapTool()
        iface.mapCanvas().setMapTool( self.sectionMapTool ) 
    
    def onWestEastPressed(self):
        self.drillManager.sectionWidth = float(self.leSectionWidth.text())
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=True)
        result = dlg.exec_()
        if result:
            self.drillManager.sectionNorth = float(dlg.leCenter.text())
            self.drillManager.sectionLimitWest = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitEast = float(dlg.leLimitMax.text())
            self.drillManager.sectionWEName = dlg.leName.text()
#            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            self.drillManager.sectionLayers = getCheckedLayers(dlg.listLayers)
            self.drillManager.elevationLayers = getCheckedLayers(dlg.listElevation)

        dlg.close()
        
        if result:
            s = self.sectionManager.createSection(self.drillManager.sectionWEName, \
              self.drillManager.sectionLimitWest, self.drillManager.sectionNorth, \
              self.drillManager.sectionLimitEast, self.drillManager.sectionNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers, self.drillManager.elevationLayers)
            
            self.fillSectionList()

            self.sectionManager.showSection(s)
        
    def onSouthNorthPressed(self):
        self.drillManager.sectionWidth = float(self.leSectionWidth.text())
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=False)
        result = dlg.exec_()
        if result:
            self.drillManager.sectionEast = float(dlg.leCenter.text())
            self.drillManager.sectionLimitSouth = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitNorth = float(dlg.leLimitMax.text())
            self.drillManager.sectionSNName = dlg.leName.text()
#            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            self.drillManager.sectionLayers = getCheckedLayers(dlg.listLayers)
            self.drillManager.elevationLayers = getCheckedLayers(dlg.listElevation)

        dlg.close()
        
        if result:
            s = self.sectionManager.createSection(self.drillManager.sectionSNName, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitSouth, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers, self.drillManager.elevationLayers)

            self.fillSectionList()
            
            self.sectionManager.showSection(s)

    def onDeletePressed(self):
        #Build a list of sections from all checked ones, or if none checked, the currently selected one
        sList = self.checkedSections()
        if len(sList) == 0:
            cs = self.currentSection()
            if cs is not None:
                sList.append( cs )

        for s in sList:
            self.sectionManager.deleteSection(s)

        self.fillSectionList()
            
    def onRecreatePressed(self):
        #Build a list of sections from all checked ones, or if none checked, the currently selected one
        sList = self.checkedSections()
        if len(sList) == 0:
            cs = self.currentSection()
            if cs is not None:
                sList.append( cs )

        for s in sList:
            self.sectionManager.recreateSection(s)

        #If there was only 1 section to recreate, then show it as well
        if len(sList) == 0:
            self.sectionManager.showSection(s)
            
    def onShowPressed(self):
        self.showCurrentSelection()
            
    def onNewWindowPressed(self):
        cs = self.currentSection()
        if cs is not None:
            cs.createWindow()

    def onListItemdoubleClicked(self):
        self.showCurrentSelection()
        
    def onSelectAllChecked(self):
        self.selectAll(self.listSection, self.checkSelectAll.isChecked())
            
    def showCurrentSelection(self):
        cs = self.currentSection()
        if cs != None:
            self.sectionManager.showSection(cs)
        
    def currentSection(self):
        cs = None
        item = self.listSection.currentItem()
        if item is not None:
            cs = item.data(QtCore.Qt.UserRole)
        
        return cs
        
    def checkedSections(self):
        sList = []
        for index in range(self.listSection.count()):
            if self.listSection.item(index).checkState():
                s = self.listSection.item(index).data(QtCore.Qt.UserRole)
                sList.append(s)
        return sList
    