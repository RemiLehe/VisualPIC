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


import numpy as np
import vtk
from vtk.qt4.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

class VolumeVTK():
    def __init__(self, field3D):
        self.actorType = "Volume"
        self.name = field3D.GetName()
        self.speciesName = field3D.GetSpeciesName()
        self.field = field3D
        self.opacity = vtk.vtkPiecewiseFunction()
        self.color = vtk.vtkColorTransferFunction()
        self.customCMapRange = False
        self._SetDefaultStyle()

    def _SetDefaultStyle(self):
        self.opacity.AddPoint(0, 0)
        self.opacity.AddPoint(255/10, 0.1)
        self.opacity.AddPoint(255/10*2, 0.2)
        self.opacity.AddPoint(255/10*3, 0.3)
        self.opacity.AddPoint(255/10*4, 0.4)
        self.opacity.AddPoint(255/10*5, 0.5)
        self.opacity.AddPoint(255/10*6, 0.6)
        self.opacity.AddPoint(255/10*7, 0.7)
        self.opacity.AddPoint(255/10*8, 0.8)
        self.opacity.AddPoint(255/10*9, 0.9)
        self.opacity.AddPoint(255, 1)
        
        self.color.AddRGBPoint(0.0,0, 0, 1)
        self.color.AddRGBPoint(100, 1.000,0, 0)
        self.color.AddRGBPoint(255, 0, 1.0, 0)

    def GetFieldName(self):
        return self.field.GetName()

    def GetSpeciesName(self):
        return self.field.GetSpeciesName()

    def GetTimeSteps(self):
        return self.field.GetTimeSteps()

    def SetColorPoints(self, points):
        # points = [x0, r0, g0, b0, x1, r1, g1, b1, ..., xN, rN, gN, bN]
        self.color.RemoveAllPoints()
        self.color.FillFromDataPointer(int(len(points)/4), points)
        
    def SetOpacityPoints(self, points):
        self.opacity.RemoveAllPoints()
        self.opacity.FillFromDataPointer(int(len(points)/2), points)

    def SetOpacityValue(self, index, valueX, valueY):
        self.opacity.SetNodeValue(index, [valueX, valueY, 0.5, 0.0])

    def SetOpacityValues(self, values):
        self.opacity.RemoveAllPoints()
        for point in values:
            self.opacity.AddPoint(point[0], point[1])
            #self.SetOpacityValue(i, point[0], point[1])

    def SetCMapRangeFromCurrentTimeStep(self, timeStep):
        fieldData = np.absolute(self.field.GetAllFieldDataInOriginalUnits(timeStep))
        self.maxRange = np.amax(fieldData)
        self.minRange = np.amin(fieldData)
        self.customCMapRange = True

    def SetCMapRange(self, min, max):
        self.maxRange = max
        self.minRange = min
        self.customCMapRange = True

    def GetOpacityValues(self):
        values = list()
        size = self.opacity.GetSize()
        for i in range(size):
            val = [1,1,1,1]
            self.opacity.GetNodeValue(i, val)
            values.append([val[0], val[1]])
        return values

    def GetData(self, timeStep, transvEl = None, longEl = None, fraction = 1):
        if self.field.GetFieldDimension() == "3D":
            fieldData = np.absolute(self.field.GetAllFieldDataInOriginalUnits(timeStep))
        if self.field.GetFieldDimension() == "2D":
            fieldData = np.absolute(self.field.Get3DFieldFrom2DSliceInOriginalUnits(timeStep, transvEl, longEl, fraction))
        if self.customCMapRange:
            maxvalue = self.maxRange
            minvalue = self.minRange
        else:
            maxvalue = np.amax(fieldData)
            minvalue = np.amin(fieldData)
        fieldData = np.round(255 * (fieldData-minvalue)/(maxvalue-minvalue))
        fieldData[fieldData < 0] = 0
        fieldData[fieldData > 255] = 255
        # Change data from float to unsigned char
        npdatauchar = np.array(fieldData, dtype=np.uint8)
        return npdatauchar

    def GetAxes(self, timeStep):
        axes = {}
        if self.field.GetFieldDimension() == "3D":
            axes["z"] = self.field.GetAxisDataInOriginalUnits("z", timeStep)
        if self.field.GetFieldDimension() == "2D":
            axes["z"] = self.field.GetAxisDataInOriginalUnits("y", timeStep)
        axes["y"] = self.field.GetAxisDataInOriginalUnits("y", timeStep)
        axes["x"] = self.field.GetAxisDataInOriginalUnits("x", timeStep)
        return axes

    def GetAxesSpacing(self, timeStep, transvEl = None, longEl = None, fraction = 1):
        spacing = {}
        axesx = self.field.GetAxisDataInOriginalUnits("x", timeStep)
        axesy = self.field.GetAxisDataInOriginalUnits("y", timeStep)
        if self.field.GetFieldDimension() == "3D":
            axesz = self.field.GetAxisDataInOriginalUnits("z", timeStep)
            spacing["x"] = np.abs(axesx[1]-axesx[0])
            spacing["y"] = np.abs(axesy[1]-axesy[0])
            spacing["z"] = np.abs(axesz[1]-axesz[0])
        if self.field.GetFieldDimension() == "2D":
            axesz = self.field.GetAxisDataInOriginalUnits("y", timeStep)
            spacing["x"] = np.abs(axesx[-1]-axesx[0])/longEl
            spacing["y"] = np.abs(axesy[-1]-axesy[0])/transvEl*fraction
            spacing["z"] = np.abs(axesz[-1]-axesz[0])/transvEl*fraction
        return spacing

class Visualizer3Dvtk():
    def __init__(self, dataContainer):
        self.dataContainer = dataContainer
        self._GetAvailable3DFields()
        self.volumeList = list()
        self.volume = None
        self.volumeMapper = None

    def _GetAvailable3DFields(self):
        self.availableFields = list()
        speciesList = self.dataContainer.GetAvailableSpecies()
        domainFields = self.dataContainer.GetAvailableDomainFields()
        for species in speciesList:
            for field in species.GetAvailableFields():
                #if field.GetFieldDimension() == "3D":
                self.availableFields.append(field)
        for field in domainFields:
            #if field.GetFieldDimension() == "3D":
            self.availableFields.append(field)

    def GetListOfAvailable3DFields(self):
        namesList = list()
        for field in self.availableFields:
            namesList.append({"fieldName":field.GetName(), "speciesName":field.GetSpeciesName()})
        return namesList

    def GetTimeSteps(self):
        i = 0
        timeSteps = np.array([0])
        for volume in self.volumeList:
            if i == 0:
                timeSteps = volume.GetTimeSteps()
            else :
                timeSteps = np.intersect1d(timeSteps, volume.GetTimeSteps())
            i+=1
        return timeSteps

    def GetVTKWidget(self, parentWidget):
        self.vtkWidget = QVTKRenderWindowInteractor(parentWidget)
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0,0,0)
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactor.Initialize()
        self.vtkCamera = self.renderer.GetActiveCamera()
        return self.vtkWidget

    def AddVolumeField(self, fieldName, speciesName):
        if speciesName == "":
            for volume in self.volumeList:
                if (volume.GetFieldName() == fieldName):
                    return False
            self.volumeList.append(VolumeVTK(self.dataContainer.GetDomainField(fieldName)))
            return True
        else:
            for volume in self.volumeList:
                if (volume.GetFieldName() == fieldName) and (volume.GetSpeciesName() == speciesName):
                    return False
            self.volumeList.append(VolumeVTK(self.dataContainer.GetSpeciesField(speciesName, fieldName)))
            return True

    def RemoveVolumeFromName(self, fieldName, speciesName):
        for volumeField in self.volumeList:
            if (volumeField.GetFieldName() == fieldName) and (volumeField.GetSpeciesName() == speciesName):
                self.volumeList.remove(volumeField)
                return

    def RemoveVolume(self, volume):
        self.volumeList.remove(volume)

    def GetVolumeField(self, fieldName, speciesName):
        for volume in self.volumeList:
            if (volume.name == fieldName) and (volume.speciesName == speciesName):
                return volume

    def CreateVolume(self, timeStep):
        firstTime = False
        # Get data
        npdatauchar = list()
        volumeprop = vtk.vtkVolumeProperty()
        volumeprop.IndependentComponentsOn()
        volumeprop.SetInterpolationTypeToLinear()
        for i, volume in enumerate(self.volumeList):
            npdatauchar.append(volume.GetData(timeStep, 200, 300, 0.5)) # limit on elements only applies for 2d case
            volumeprop.SetColor(i,volume.color)
            volumeprop.SetScalarOpacity(i,volume.opacity)
            volumeprop.ShadeOff(i)
        npdatamulti = np.concatenate([aux[...,np.newaxis] for aux in npdatauchar], axis=3)
        axes = self.volumeList[0].GetAxes(timeStep)
        axesSpacing = self.volumeList[0].GetAxesSpacing(timeStep, 200, 300, 0.5) # limit on elements only applies for 2d case
        # Put data in VTK format
        dataImport = vtk.vtkImageImport()
        dataImport.SetImportVoidPointer(npdatamulti)
        dataImport.SetDataScalarTypeToUnsignedChar()
        dataImport.SetNumberOfScalarComponents(len(self.volumeList))
        dataImport.SetDataExtent(0, npdatamulti.shape[2]-1, 0, npdatamulti.shape[1]-1, 0, npdatamulti.shape[0]-1)
        dataImport.SetWholeExtent(0, npdatamulti.shape[2]-1, 0, npdatamulti.shape[1]-1, 0, npdatamulti.shape[0]-1)
        dataImport.SetDataSpacing(axesSpacing["x"],axesSpacing["y"],axesSpacing["z"])
        dataImport.SetDataOrigin(axes["x"][0],axes["y"][0],axes["z"][0])
        dataImport.Update()
        # Set the mapper
        if self.volumeMapper == None:
            self.volumeMapper = vtk.vtkGPUVolumeRayCastMapper()
        self.volumeMapper.SetAutoAdjustSampleDistances(1)
        self.volumeMapper.SetInputConnection(dataImport.GetOutputPort())
        self.volumeMapper.Update()
        # Create volume
        if self.volume == None:
            self.volume = vtk.vtkVolume()
            firstTime = True
            self.volume.SetMapper(self.volumeMapper)
            self.volume.SetProperty(volumeprop)
        # Add to render
        if firstTime:
            self.renderer.AddVolume(self.volume)
        else:
            self.volume.Modified()
        if firstTime:
            self.renderer.ResetCamera()
            self.renderer.GetRenderWindow().Render()
        else:
            #currentCameraPosition = np.array(self.renderer.GetActiveCamera().GetPosition())
            #newDataOrigin = np.array((axes["x"][0],axes["y"][0],axes["z"][0]))
            #newCameraPosition = newDataOrigin - self.pastDataOrigin + currentCameraPosition
            self.renderer.ResetCamera()
            #self.renderer.GetActiveCamera().SetPosition(newCameraPosition[0],newCameraPosition[1],newCameraPosition[2])
            self.vtkWidget.GetRenderWindow().Render()
        #self.pastDataOrigin = np.array((axes["x"][0],axes["y"][0],axes["z"][0]))
        self.interactor.Initialize()

    def MakeRender(self, timeStep):
        self.CreateVolume(timeStep)

    def UpdateRender(self):
        self.interactor.Render()

    def SaveScreenshot(self, path):
        w2if = vtk.vtkWindowToImageFilter()
        w2if.SetInput(self.vtkWidget.GetRenderWindow())
        w2if.Update()
 
        writer = vtk.vtkPNGWriter()
        writer.SetFileName(path + ".png")
        writer.SetInputData(w2if.GetOutput())
        writer.Write()

