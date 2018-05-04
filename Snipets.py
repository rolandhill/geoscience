# -*- coding: utf-8 -*-
"""
Created on Thu May 03 16:41:00 2018

@author: hillr
"""


Writing and Reading Python Plugin Settings to/from QGIS Project File
For some plugins it’s necessary to save the settings inside the QGIS project file. Saving is done with this simple one-liner:

1
QgsProject.instance().writeEntry(pluginName, setting, value)
Then you just need to save the project.

Reading is performed with one of the following functions:

QgsProject.instance().readEntry (pluginName, setting) # for strings
QgsProject.instance().readNumEntry (pluginName, setting)
QgsProject.instance().readDoubleEntry (pluginName, setting)
QgsProject.instance().readBoolEntry (pluginName, setting)
QgsProject.instance().readListEntry (pluginName, setting)
You’ll find the corresponding API documentation at: http://doc.qgis.org/stable/classQgsProject.html. As you can see, you can only read/write simple data types. To allow the plugin developer to save more complex plugin settings, I filed an enhancement request.

To handle all those different read functions in a convenient way, I created the following functions:


def readSetting(self,func,setting):
    """read a plugin setting from QgsProject instance"""
    value,ok = func('pluginName',setting)
    if ok:
        return value
    else:
        return None
             
def readSettings(self,setting,value):
    """read plugin settings from QgsProject instance"""
    # map data types to function names
    prj = QgsProject.instance()
    functions = { 'str' : prj.readEntry,
                  'int' : prj.readNumEntry,
                  'float' : prj.readDoubleEntry,
                  'bool' : prj.readBoolEntry,
                  'pyqtWrapperType' : prj.readListEntry # QStringList
                }
         
    dataType = type(value).__name__
    return = self.readSetting(functions[dataType],setting)
readSettings() has to be supplied with the name of the setting and an example or default value for the setting (from which we can determine the data type of the setting). Of course this can be done in many different ways. In Time Manager plugin, readSettings() receives a dictionary of all settings that have to be read. The function then loops through the dictionary and reads the available settings.





# -*- coding: utf-8 -*-
"""
Created on Thu May 03 16:43:53 2018

@author: hillr
"""

from scipy import interpolate

def f(x):
    x_points = [ 0, 1, 2, 3, 4, 5]
    y_points = [12,14,22,39,58,77]

    tck = interpolate.splrep(x_points, y_points)
    return interpolate.splev(x, tck)

print f(1.25)