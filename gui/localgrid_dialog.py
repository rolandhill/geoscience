# -*- coding: utf-8 -*-
"""
Created on March 30 2020

@author: Roland Hill
"""

from PyQt5 import QtCore, uic
from PyQt5 import QtWidgets

from qgis.core import *
from qgis.utils import *
from qgis.gui import *

from decimal import Decimal
from ..external import simil

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), '../ui/localgrid_dialog_base.ui'))

import numpy as np

# Calcualte affine parameters from a set of coordinates in base and local systems
def calcAffine(base, local):

    # find the similaity transformation parameters
    m, r, t = simil.process(base, local)

    # scale the rotation matrix
    mr = m * r

    a0 = t[0][0]
    a1 = mr[0][0]
    a2 = mr[0][1]
    b0 = t[1][0]
    b1 = mr[1][0]
    b2 = mr[1][1]
        
    return a0, a1, a2, b0, b1, b2

def createAffineLengthParameterWkt(label, val, epsg):
    txt = ',' \
    'PARAMETER["' + label + '",' + str(val) + ',' \
    'LENGTHUNIT["metre",1],' \
    'ID["EPSG",' + epsg + ']]'
    
    return txt
    
def createAffineScaleParameterWkt(label, val, epsg):
    txt = ',' \
    'PARAMETER["' + label + '",' + str(val) + ',' \
    'SCALEUNIT["coefficient",1],' \
    'ID["EPSG",' + epsg + ']]'
    
    return txt
    
def createAffineWkt(a0, a1, a2, b0, b1, b2):
    txt = 'DERIVINGCONVERSION["Affine",' \
    'METHOD["Affine parametric transformation",' \
    'ID["EPSG",9624' \
    ']' \
    ']'
    txt = txt + createAffineLengthParameterWkt("A0", a0, '8623')
    txt = txt + createAffineScaleParameterWkt("A1", a1, '8624')
    txt = txt + createAffineScaleParameterWkt("A2", a2, '8625')
    txt = txt + createAffineLengthParameterWkt("B0", b0, '8639')
    txt = txt + createAffineScaleParameterWkt("B1", b1, '8640')
    txt = txt + createAffineScaleParameterWkt("B2", b2, '8641')
    
    txt = txt + ']'
    
    return txt
    
    
class LocalGridDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, manager, parent=None):
        """Constructor."""
        super(LocalGridDialog, self).__init__(parent)
        self.setupUi(self)
        
        self.crsBase.setCrs(iface.mapCanvas().mapSettings().destinationCrs())
        self.tblCoords.setHorizontalHeaderLabels(["Base X", "Base Y", "Base Z", "Local X", "Local Y", "Local Z"])
        self.tblCoords.setRowCount(20)
        self.tblCoords.setCurrentCell(0, 0)
        self.tblCoords.editItem(self.tblCoords.item(0, 0))
        self.pteWkt.setPlaceholderText("Local CRS will appear here after you press Calculate")

#   For testing only
        # self.setDefaultValues(0, [378729.096, 5375519.708, 212.78, -21.64, 1182.62, 3262.27])
        # self.setDefaultValues(1, [379103.8064, 5374674.296, 17.41, 180.14, 279.96, 3066.9])
        # self.setDefaultValues(2, [379307.5922, 5374865.902, 18.32, 417.58, 427.94, 3067.81])
        # self.setDefaultValues(3, [379985.7184, 5375800.327, -1054.638, 1265.888, 1211.501, 1994.852])
        # self.setDefaultValues(4, [379869.8227, 5376563.518, -1044.573, 1301.838, 1982.777, 2004.917])
        # self.setDefaultValues(5, [378874.5836, 5374432.606, 219.49, -92.068, 87.843, 3268.98])
        
        self.pbCalculate.pressed.connect(self.onCalculatePressed)  
        self.pbCopy.pressed.connect(self.onCopyPressed)  

# Copy text from the text box into the clipboard        
    def onCopyPressed(self):
        cb = QtWidgets.QApplication.clipboard()
        cb.clear(mode=cb.Clipboard )
        cb.setText(self.pteWkt.toPlainText(), mode=cb.Clipboard)

# Retrieve input data, calcualte affine parameters, prepare WKT and write results into text box
    def onCalculatePressed(self):
        name = self.leName.text()
        crs = self.crsBase.crs()
        # Only works with projected CRS
        if crs.isGeographic():
            iface.messageBar().pushMessage("Base CRS", "You must choose a PROJECTED CRS as the base (ie not latitude, longitude)", level=Qgis.Warning)
            return
        
        # Get WKT for the base CRS. The variant is important as only later versions allow for affine parameters
        wktBase = crs.toWkt(variant=QgsCoordinateReferenceSystem.WktVariant.WKT2_2018, multiline=False)
        
        # Loop through table and get coords
        base = []
        local = []
        for row in range(0, self.tblCoords.rowCount()):
            bx = self.getNumberFromTable(row, 0)
            by = self.getNumberFromTable(row, 1)
            bz = self.getNumberFromTable(row, 2)
            lx = self.getNumberFromTable(row, 3)
            ly = self.getNumberFromTable(row, 4)
            lz = self.getNumberFromTable(row, 5)
            # All values must be valid for the row to be valid
            if bx is not None and by is not None and bz is not None and lx is not None and ly is not None and lz is not None:
                base.append([bx, by, bz])
                local.append([lx, ly, lz])

        # We need at least 2 sets of valid points
        if len(base) < 2:
            iface.messageBar().pushMessage("Valid Rows", "You must have 2 or more sets of points with valid coordinates", level=Qgis.Warning)
            return

        a0, a1, a2, b0, b1, b2 = calcAffine(base, local)
        
        wktAffine = createAffineWkt(a0, a1, a2, b0, b1, b2)
        pos = wktBase.find(',CS[Cartesian')
        wkt = 'DERIVEDPROJCRS["' + name + '",BASE' + wktBase[:pos] + '],' + wktAffine + wktBase[pos:]
        # Trim the Usage paramter if it exists
        pos = wkt.find(',USAGE[')
        if pos >=0:
            wkt = wkt[:pos] + ']'
        #Trim the BASEPROJCRS ID parameter fro mthe end of the string if it exists
        pos = wkt.find(',ID[', -25)
        if pos >=0:
            wkt = wkt[:pos] + ']'
        self.pteWkt.setPlainText(wkt)


    def getNumberFromTable(self, row, col):
        # return a valid float (double) or None
        val = None
        item = self.tblCoords.item(row, col)
        if item is not None:
            strval = item.data(0)
            if strval is not None:
                try:
                    # float() is reported to have issues with long strings so use Decimal
                    val = float(Decimal(strval))
                except:
                    pass
        return val
            
        
# Utility method for testing        
    def setDefaultValues(self, row, vals):
        col = 0
        for val in vals:
            self.tblCoords.setItem(row, col, QtWidgets.QTableWidgetItem(str(val), 0))
            col += 1

