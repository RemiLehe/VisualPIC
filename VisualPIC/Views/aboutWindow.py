# -*- coding: utf-8 -*-

#Copyright 2016-2018 Angel Ferran Pousa, DESY
#
#This file is part of VisualPIC.
#
#VisualPIC is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#VisualPIC is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with VisualPIC.  If not, see <http://www.gnu.org/licenses/>.

import sys
import os
from pkg_resources import resource_filename

from PyQt5.uic import loadUiType
from PyQt5.QtGui import QPixmap

from VisualPIC.__version__ import __version__


if getattr(sys, 'frozen', False):
    # we are running in a bundle
    bundle_dir = sys._MEIPASS
else:
    # we are running in a normal Python environment
    bundle_dir = os.path.dirname(os.path.abspath(__file__))
guipath = os.path.join( bundle_dir, 'aboutWindow.ui' )
Ui_AboutWindow, QAboutWindow = loadUiType(guipath)


class AboutWindow(QAboutWindow, Ui_AboutWindow):
    def __init__(self, parent=None):
        super(AboutWindow, self).__init__(parent)
        self.setupUi(self)
        self.set_ui_icons()
        self.set_version_number()

    def set_ui_icons(self):
        logo_path = resource_filename(
                'VisualPIC.Icons', 'logo_horiz_transp.png')
        pixmap = QPixmap(logo_path)
        self.label.setPixmap(pixmap)

    def set_version_number(self):
        self.version_label.setText("Version: " + __version__)
