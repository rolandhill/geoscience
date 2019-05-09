import os

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets
#from PyQt5 import QtGui

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from .sectionorthogonal_dialog import SectionOrthogonalDialog
from .dialogBase import dialogBase
from .SectionMapTool import SectionMapTool

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'sectionmanager_dialog_base.ui'))


class SectionManagerDialog(QtWidgets.QDialog, dialogBase, FORM_CLASS):
    def __init__(self, drillManager, parent=None):
        """Constructor."""
        super(SectionManagerDialog, self).__init__(parent)
        
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
        
        self.fillSectionList()

        self.pbMapCanvas.pressed.connect(self.onMapCanvasPressed)        
        self.pbWestEast.pressed.connect(self.onWestEastPressed)
        self.pbSouthNorth.pressed.connect(self.onSouthNorthPressed)
        self.pbDeleteSection.pressed.connect(self.onDeletePressed)
        self.pbShowSection.pressed.connect(self.onShowPressed)
        self.pbNewWindow.pressed.connect(self.onNewWindowPressed)
        self.pbRecreate.pressed.connect(self.onRecreatePressed)

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
        iface.mapCanvas().activateWindow()
        iface.mapCanvas().setMapTool( self.sectionMapTool ) 
    
    def onWestEastPressed(self):
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=True)
        result = dlg.exec_()
        if result:
            self.drillManager.sectionNorth = float(dlg.leCenter.text())
            self.drillManager.sectionLimitWest = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitEast = float(dlg.leLimitMax.text())
            self.drillManager.sectionWEName = dlg.leName.text()
            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = []
            for index in range(dlg.listLayers.count()):
                if dlg.listLayers.item(index).checkState():
                    self.drillManager.sectionLayers.append(dlg.listLayers.item(index).data(QtCore.Qt.UserRole))

        dlg.close()
        
        if result:
            s = self.sectionManager.createSection(self.drillManager.sectionWEName, \
              self.drillManager.sectionLimitWest, self.drillManager.sectionNorth, \
              self.drillManager.sectionLimitEast, self.drillManager.sectionNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers)
            
            self.fillSectionList()

            self.sectionManager.showSection(s)
        
    def onSouthNorthPressed(self):
        dlg = SectionOrthogonalDialog(self.drillManager, dirWestEast=False)
        result = dlg.exec_()
        if result:
            self.drillManager.sectionEast = float(dlg.leCenter.text())
            self.drillManager.sectionLimitSouth = float(dlg.leLimitMin.text())
            self.drillManager.sectionLimitNorth = float(dlg.leLimitMax.text())
            self.drillManager.sectionSNName = dlg.leName.text()
            self.drillManager.sectionWidth = float(dlg.leSectionWidth.text())
            
            # Save the name of each checked attribute field in a list
            self.drillManager.sectionLayers = []
            for index in range(dlg.listLayers.count()):
                if dlg.listLayers.item(index).checkState():
                    self.drillManager.sectionLayers.append(dlg.listLayers.item(index).data(QtCore.Qt.UserRole))

        dlg.close()
        
        if result:
            s = self.sectionManager.createSection(self.drillManager.sectionSNName, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitSouth, \
              self.drillManager.sectionEast, self.drillManager.sectionLimitNorth, \
              self.drillManager.sectionWidth, \
              self.drillManager.sectionLayers)

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
        cs = self.currentSection()
        if cs != None:
            self.sectionManager.showSection(cs)
            
    def onNewWindowPressed(self):
        cs = self.currentSection()
        if cs is not None:
            cs.createWindow()
        
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
    