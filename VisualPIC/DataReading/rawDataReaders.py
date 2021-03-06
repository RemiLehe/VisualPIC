# -*- coding: utf-8 -*-

#Copyright 2016-2017 Angel Ferran Pousa, DESY
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


import abc
from h5py import File as H5File
import numpy as np

from VisualPIC.DataReading.dataReader import DataReader

# TODO: Add try/except statement for openPMD-viewer
from opmd_viewer import OpenPMDTimeSeries


class RawDataReaderBase(DataReader):
    """Parent class for all rawDataReaders"""
    __metaclass__  = abc.ABCMeta
    def __init__(self, location, speciesName, dataName, internalName, firstTimeStep):
        DataReader.__init__(self, location, speciesName, dataName, internalName)
        self.internalName = dataName
        self.firstTimeStep = firstTimeStep

    def GetData(self, timeStep):
        if timeStep != self.currentTimeStep:
            self.currentTimeStep = timeStep
            self.data = self._ReadData(timeStep)
        return self.data

    def GetDataUnits(self):
        if self.dataUnits == "":
            self._ReadUnits()
        return self.dataUnits

    def GetTime(self, timeStep):
        if timeStep != self.currentTimeStep:
            self.currentTimeStep = timeStep
            self._ReadTime(timeStep)
        return self.currentTime

    def GetTimeUnits(self):
        if self.timeUnits == "":
            self._ReadUnits()
        return self.timeUnits


class OsirisRawDataReader(RawDataReaderBase):
    def __init__(self, location, speciesName, dataName, internalName, firstTimeStep):
        RawDataReaderBase.__init__(self, location, speciesName, dataName, internalName, firstTimeStep)

    def _ReadData(self, timeStep):
        file_content = self._OpenFile(timeStep)
        if self.internalName == "tag":
            tags = np.array(file_content.get(self.internalName))
            a = tags[:,0]
            b = tags[:,1]
            data = 1/2*(a+b)*(a+b+1)+b # Cantor pairing function
        else:
            data = np.array(file_content.get(self.internalName))
        self.currentTime = file_content.attrs["TIME"][0]
        file_content.close()
        return data

    def _ReadTime(self, timeStep):
        file_content = self._OpenFile(timeStep)
        self.currentTime = file_content.attrs["TIME"][0]
        file_content.close()

    def _ReadUnits(self):
        file_content = self._OpenFile(self.firstTimeStep)
        self.dataUnits = str(list(file_content[self.internalName].attrs["UNITS"])[0])[2:-1].replace("\\\\","\\")
        self.timeUnits = str(file_content.attrs["TIME UNITS"][0])[2:-1].replace("\\\\","\\")
        file_content.close()

    def _OpenFile(self, timeStep):
        fileName = "RAW-" + self.speciesName + "-" + str(timeStep).zfill(6)
        ending = ".h5"
        file_path = self.location + "/" + fileName + ending
        file_content = H5File(file_path, 'r')
        return file_content


class OpenPMDRawDataReader(RawDataReaderBase):
    def __init__(self, location, speciesName, dataName, internalName, firstTimeStep):
        # Store an openPMD timeseries object
        # (Its API is used in order to conveniently extract data from the file)
        self.openpmd_ts = OpenPMDTimeSeries( location, check_all_files=False )
        # Initialize the instance
        RawDataReaderBase.__init__(self, location, speciesName, dataName, internalName, firstTimeStep)

    def _ReadData(self, timeStep):
        data, = self.openpmd_ts.get_particle( [self.internalName],
                    species=self.speciesName, iteration=timeStep )
        self.currentTime = self._ReadTime(timeStep)
        return data

    def _ReadTime(self, timeStep):
        # The line below sets the attribute `_current_i` of openpmd_ts
        self.openpmd_ts._find_output( None, timeStep )
        # This sets the corresponding time
        self.currentTime = self.openpmd_ts.t[ self.openpmd_ts._current_i ]

    def _ReadUnits(self):
        # OpenPMD data always provide conversion to SI units
        self.dataUnits = "" # TODO:
        self.timeUnits = "s"

    def _OpenFile(self, timeStep):
        # The line below sets the attribute `_current_i` of openpmd_ts
        self.openpmd_ts._find_output( None, timeStep )
        # This finds the full path to the corresponding file
        fileName = self.openpmd_ts.h5_files[ self.openpmd_ts._current_i ]
        file_content = H5File(fileName, 'r')
        return file_content
