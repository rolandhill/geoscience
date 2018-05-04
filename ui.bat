sed -i.bak "s/<header>.*</<header>qgis.gui</g" %1.ui
rem pyuic5 -o %1.py %1.ui
