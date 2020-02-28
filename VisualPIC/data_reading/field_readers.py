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

import os

from h5py import File as H5F
import numpy as np
from scipy.interpolate import interp2d
from scipy.ndimage import zoom
from openpmd_viewer.openpmd_timeseries.data_reader.params_reader import (
    read_openPMD_params)
import openpmd_viewer.openpmd_timeseries.data_reader.field_reader as opmd_fr


class FieldReader():
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def read_field(self, file_path, field_path, slice_i=0.5, slice_j=0.5,
                   slice_dir_i=None, slice_dir_j=None, m='all', theta=0,
                   max_resolution_3d_tm=None, only_metadata=False):
        fld_metadata = self._read_field_metadata(file_path, field_path)
        self._readjust_metadata(fld_metadata, slice_dir_i, slice_dir_j, theta,
                                max_resolution_3d_tm)
        if only_metadata:
            return np.array([]), fld_metadata
        geom = fld_metadata['field']['geometry']
        if geom == "1d":
            fld = self._read_field_1d(file_path, field_path)
        elif geom == "2dcartesian":
            fld = self._read_field_2d_cart(file_path, field_path, slice_i,
                                           slice_dir_i)
        elif geom == "3dcartesian":
            fld = self._read_field_3d_cart(file_path, field_path, slice_i,
                                           slice_j, slice_dir_i, slice_dir_j)
        elif geom == "2dcylindrical":
            fld = self._read_field_2d_cyl(file_path, field_path, slice_i,
                                          slice_dir_i)
        elif geom == "thetaMode":
            fld = self._read_field_theta(file_path, field_path, m, theta,
                                         slice_i, slice_dir_i,
                                         max_resolution_3d_tm)
        return fld, fld_metadata

    def _readjust_metadata(self, field_metadata, slice_dir_i, slice_dir_j,
                           theta, max_resolution_3d_tm):
        if (field_metadata['field']['geometry'] == 'thetaMode' and
            theta is None):
            r_md = field_metadata['axis']['r']
            # Check if resolution should be reduced
            if max_resolution_3d_tm is not None:
                z = field_metadata['axis']['z']['array']
                r = r_md['array']
                nr = len(r)
                nz = len(z)
                max_res_lon, max_res_transv = max_resolution_3d_tm
                #if nz > max_res_lon:
                #    excess_z = int(np.round(nz/max_res_lon))
                #    field_metadata['axis']['z']['array'] = z[::excess_z]
                #if nr > max_res_transv/2:
                #    excess_r = int(np.round(Nr/max_res_transv/2))
                #    r_md['array'] = r[::excess_r]
                if nr > max_res_transv:
                    r = zoom(r, max_res_transv/nr, order=1)
                    r_md['array'] = r
                if nz > max_res_lon:
                    z = zoom(z, max_res_lon/nz, order=1)
                    field_metadata['axis']['z']['array'] = z
            # Create x and y axes and remove r
            field_metadata['axis']['x'] = r_md
            field_metadata['axis']['y'] = r_md
            del field_metadata['axis']['r']
        if slice_dir_i is not None:
            del field_metadata['axis'][slice_dir_i]
        if slice_dir_j is not None:
            del field_metadata['axis'][slice_dir_j]

    def _read_field_1d(self, file_path, field_path):
        raise NotImplementedError

    def _read_field_2d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_dir_i='z'):
        raise NotImplementedError

    def _read_field_3d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_j=0.5, slice_dir_i=None, slice_dir_j=None):
        raise NotImplementedError

    def _read_field_2d_cyl(self, file_path, field_path, slice_i=0.5,
                           slice_dir_i=None):
        raise NotImplementedError

    def _read_field_theta(self, file_path, field_path, m='all', theta=0,
                          slice_i=0.5, slice_dir_i=None,
                          max_resolution_3d_tm=None):
        raise NotImplementedError

    def _read_field_metadata(self, file_path, field_path):
        raise NotImplementedError


class OsirisFieldReader(FieldReader):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def _read_field_1d(self, file_path, field_path):
        file = H5F(file_path, 'r')
        return file[field_path]
    
    def _read_field_2d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_dir_i=None):
        file = H5F(file_path, 'r')
        fld = file[field_path]
        if slice_dir_i is not None:
            fld_shape = fld.shape
            axis_order = ['z', 'x']
            slice_list = [slice(None)] * fld.ndim
            axis_idx_i = axis_order.index(slice_dir_i)
            axis_elements_i = fld_shape[axis_idx_i] 
            slice_idx_i = int(round(axis_elements_i * slice_i))
            slice_list[axis_idx_i] = slice_idx_i
            fld = fld[tuple(slice_list)]
        return fld

    def _read_field_3d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_j=0.5, slice_dir_i=None, slice_dir_j=None):
        file = H5F(file_path, 'r')
        fld = file[field_path]
        if slice_dir_i is not None:
            fld_shape = fld.shape
            axis_order = ['x', 'y', 'z']
            slice_list = [slice(None)] * fld.ndim
            axis_idx_i = axis_order.index(slice_dir_i)
            axis_elements_i = fld_shape[axis_idx_i] 
            slice_idx_i = int(round(axis_elements_i * slice_i))
            slice_list[axis_idx_i] = slice_idx_i
            if slice_dir_j is not None:
                axis_idx_j = axis_order.index(slice_dir_j)
                axis_elements_j = fld_shape[axis_idx_j] 
                slice_idx_j = int(round(axis_elements_j * slice_j))
                slice_list[axis_idx_j] = slice_idx_j
            fld = fld[tuple(slice_list)]
        else:
            fld = fld[:]
        return fld

    def _read_field_metadata(self, file_path, field_path):
        file = H5F(file_path, 'r')
        md = {}
        field_units = self._get_field_units(file, field_path)
        field_shape = self._get_field_shape(file, field_path)
        field_geometry = self._determine_geometry(file)
        md['field'] = {}
        md['field']['units'] = field_units
        md['field']['geometry'] = field_geometry
        md['axis'] = self._get_axis_data(file, field_path, field_geometry,
                                       field_shape)
        md['time'] = self._get_time_data(file)
        file.close()
        return md
        
    def _get_field_units(self, file, field_path):
        """ Returns the field units"""
        return self._numpy_bytes_to_string(file[field_path].attrs["UNITS"][0])

    def _get_field_shape(self, file, field_path):
        """ Returns shape of field array"""
        return file[field_path].shape

    def _determine_geometry(self, file):
        """ Determines the field geometry """
        if '/AXIS/AXIS3' in file:
            return "3dcartesian"
        elif '/AXIS/AXIS2' in file:
            return "2dcartesian"
        else:
            return "1d"

    def _get_axis_data(self, file, field_path, field_geometry, field_shape):
        """ Returns dictionary with the array and units of each field axis """
        axis_data = {}
        axis_data['z'] = {}
        axis_data["z"]["units"] = self._numpy_bytes_to_string(
                file['/AXIS/AXIS1'].attrs["UNITS"][0])
        axis_data["z"]["array"] = np.linspace(file.attrs['XMIN'][0],
                                              file.attrs['XMAX'][0],
                                              field_shape[-1]+1)
        if field_geometry in ["2dcartesian", "3dcartesian"]:
            axis_data['x'] = {}
            axis_data["x"]["units"] = self._numpy_bytes_to_string(
                file['/AXIS/AXIS2'].attrs["UNITS"][0])
            axis_data["x"]["array"] = np.linspace(file.attrs['XMIN'][1],
                                                  file.attrs['XMAX'][1],
                                                  field_shape[0]+1)
        if field_geometry == "3dcartesian":
            axis_data['y'] = {}
            axis_data["y"]["units"] = self._numpy_bytes_to_string(
                file['/AXIS/AXIS3'].attrs["UNITS"][0])
            axis_data["y"]["array"] = np.linspace(file.attrs['XMIN'][2],
                                                  file.attrs['XMAX'][2],
                                                  field_shape[1]+1)
        return axis_data

    def _get_time_data(self, file):
        """ Returns dictionary with value and units of the simulation time """
        time_data = {}
        time_data["value"] = file.attrs["TIME"][0]
        time_data["units"] = self._numpy_bytes_to_string(
            file.attrs["TIME UNITS"][0])
        return time_data

    def _numpy_bytes_to_string(self, npbytes):
        return str(npbytes)[2:-1].replace("\\\\","\\").replace(' ', '')


class HiPACEFieldReader(FieldReader):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def _read_field_3d_cart(self, file_path, field_path, slice_i=0.5,
                           slice_j=0.5, slice_dir_i=None, slice_dir_j=None):
        file = H5F(file_path, 'r')
        fld = file[field_path]
        if slice_dir_i is not None:
            fld_shape = fld.shape
            axis_order = ['z', 'x', 'y']
            slice_list = [slice(None)] * fld.ndim
            axis_idx_i = axis_order.index(slice_dir_i)
            axis_elements_i = fld_shape[axis_idx_i] 
            slice_idx_i = int(round(axis_elements_i * slice_i))
            slice_list[axis_idx_i] = slice_idx_i
            if slice_dir_j is not None:
                axis_idx_j = axis_order.index(slice_dir_j)
                axis_elements_j = fld_shape[axis_idx_j] 
                slice_idx_j = int(round(axis_elements_j * slice_j))
                slice_list[axis_idx_j] = slice_idx_j
            fld = fld[tuple(slice_list)]
        return fld

    def _read_field_metadata(self, file_path, field_path):
        file = H5F(file_path, 'r')
        md = {}
        field_units = self._get_field_units(file_path)
        field_shape = self._get_field_shape(file, field_path)
        md['field'] = {}
        md['field']['units'] = field_units
        md['field']['geometry'] = '3dcartesian'
        md['axis'] = self._get_axis_data(file, field_shape)
        md['time'] = self._get_time_data(file)
        file.close()
        return md
        
    def _get_field_units(self, file_path):
        """ Returns the field units"""
        # HiPACE does not store unit information in data files
        file = os.path.split(file_path)[-1]
        if 'field' in file:
            return 'm_e c \\omega_p e^{-1}'
        elif 'density' in file:
            'e \\omega_p^3/ c^3'
        else:
            return ''

    def _get_field_shape(self, file, field_path):
        """ Returns shape of field array"""
        return file[field_path].shape

    def _get_axis_data(self, file, field_shape):
        """ Returns dictionary with the array and units of each field axis """
        axis_data = {}
        axis_data['z'] = {}
        axis_data["z"]["units"] = 'c/ \\omega_p'
        axis_data["z"]["array"] = np.linspace(file.attrs['XMIN'][0],
                                              file.attrs['XMAX'][0],
                                              field_shape[0]+1)
        axis_data['x'] = {}
        axis_data["x"]["units"] = 'c/ \\omega_p'
        axis_data["x"]["array"] = np.linspace(file.attrs['XMIN'][1],
                                              file.attrs['XMAX'][1],
                                              field_shape[1]+1)
        axis_data['y'] = {}
        axis_data["y"]["units"] = 'c/ \\omega_p'
        axis_data["y"]["array"] = np.linspace(file.attrs['XMIN'][2],
                                              file.attrs['XMAX'][2],
                                              field_shape[2]+1)
        return axis_data

    def _get_time_data(self, file):
        """ Returns dictionary with value and units of the simulation time """
        time_data = {}
        time_data["value"] = file.attrs["TIME"][0]
        time_data["units"] = '1/ \\omega_p'
        return time_data


class OpenPMDFieldReader(FieldReader):
    def __init__(self, *args, **kwargs):
        return super().__init__(*args, **kwargs)

    def _read_field_1d(self, file_path, field_path):
        fld, _ = opmd_fr.read_field_cartesian(file_path, field_path, ['z'],
                                              None, None)
        return fld

    def _read_field_2d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_dir_i=None):
        fld, _ = opmd_fr.read_field_cartesian(file_path, field_path,
                                              ['z', 'x'], None, None)
        if slice_dir_i is not None:
            fld_shape = fld.shape
            axis_order = ['x', 'z']
            slice_list = [slice(None)] * fld.ndim
            axis_idx_i = axis_order.index(slice_dir_i)
            axis_elements_i = fld_shape[axis_idx_i] 
            slice_idx_i = int(round(axis_elements_i * slice_i))
            slice_list[axis_idx_i] = slice_idx_i
            fld = fld[tuple(slice_list)]
        return fld

    def _read_field_3d_cart(self, file_path, field_path, slice_i=0.5,
                            slice_j=0.5, slice_dir_i=None, slice_dir_j=None):
        if slice_dir_i is not None:
            slicing = -1. + 2*slice_i
        else:
            slicing = None
        fld, _ = opmd_fr.read_field_cartesian(file_path, field_path,
                                              ['z', 'x', 'y'], slicing,
                                              slice_dir_i)
        if slice_dir_i is not None and slice_dir_j is not None:
            fld_shape = fld.shape
            axis_order = ['x', 'y', 'z']
            axis_order.remove(slice_dir_i)
            slice_list = [slice(None)] * fld.ndim
            axis_idx_j = axis_order.index(slice_dir_j)
            axis_elements_j = fld_shape[axis_idx_j] 
            slice_idx_j = int(round(axis_elements_j * slice_j))
            slice_list[axis_idx_j] = slice_idx_j
            fld = fld[tuple(slice_list)]
        return fld


    def _read_field_theta(self, file_path, field_path, m='all', theta=0,
                          slice_i=0.5, slice_dir_i=None,
                          max_resolution_3d_tm=None):
        field, *comp = field_path.split('/')
        if len(comp) > 0:
            comp = comp[0]
        if comp in ['x', 'y']:
            #fld_r, _ = opmd_fr.read_field_circ(file_path, field + '/r', None,
            #                                   None, m, theta)
            #fld_t, _ = opmd_fr.read_field_circ(file_path, field + '/t', None,
            #                                   None, m, theta)
            fld_r, _ = self.read_field_circ(file_path, field + '/r', None,
                                            None, m, theta,
                                            max_resolution_3d_tm)
            fld_t, _ = self.read_field_circ(file_path, field + '/t', None,
                                            None, m, theta,
                                            max_resolution_3d_tm)
            if comp == 'x':
                fld = np.cos(theta) * fld_r - np.sin(theta) * fld_t
            elif comp == 'y':
                fld = np.sin(theta) * fld_r + np.cos(theta) * fld_t
            # Revert the sign below the axis
            fld[: int(fld.shape[0] / 2)] *= -1
        else:
            #fld, _ = opmd_fr.read_field_circ(file_path, field_path, None,
            #                                 None, m, theta)
            fld, _ = self.read_field_circ(file_path, field_path, None, None, m,
                                          theta, max_resolution_3d_tm)
        if slice_dir_i is not None:
            fld_shape = fld.shape
            axis_order = ['r', 'z']
            slice_list = [slice(None)] * fld.ndim
            axis_idx_i = axis_order.index(slice_dir_i)
            axis_elements_i = fld_shape[axis_idx_i] 
            slice_idx_i = int(round(axis_elements_i * slice_i))
            slice_list[axis_idx_i] = slice_idx_i
            fld = fld[tuple(slice_list)]
        return fld

    def read_field_circ(self, filename, field_path, slice_relative_position,
                        slice_across, m=0, theta=0.,
                        max_resolution_3d_tm=None):
        """
        Adapted from openpmd_viewer to test reduded resolution in reconstructed
        3d fields from thetaMode data.
        """
        # Open the HDF5 file
        dfile = opmd_fr.h5py.File( filename, 'r' )
        # Extract the dataset and and corresponding group
        group, dset = opmd_fr.find_dataset( dfile, field_path )

        # Extract the metainformation
        Nm, Nr, Nz = opmd_fr.get_shape( dset )
        info = opmd_fr.FieldMetaInformation( { 0: 'r', 1: 'z' }, (Nr, Nz),
            group.attrs['gridSpacing'], group.attrs['gridGlobalOffset'],
            group.attrs['gridUnitSI'], dset.attrs['position'], thetaMode=True )

        # Convert to a 3D Cartesian array if theta is None
        if theta is None:

            # Get cylindrical info
            rmax = info.rmax
            inv_dr = 1./info.dr
            Fcirc = opmd_fr.get_data( dset )  # (Extracts all modes)
            nr = Fcirc.shape[1]
            if m == 'all':
                modes = [ mode for mode in range(0, int(Nm / 2) + 1) ]
            else:
                modes = [ m ]
            modes = np.array( modes, dtype='int' )
            nmodes = len(modes)

            # If necessary, reduce resolution for 3D reconstruction
            if max_resolution_3d_tm is not None:
                max_res_lon, max_res_transv = max_resolution_3d_tm
                nz = Fcirc.shape[2]
                #if nz > max_res_lon:
                #    excess_z = int(np.round(nz/max_res_lon))
                #    Fcirc = Fcirc[:, :, ::excess_z]
                #    info.z = info.z[::excess_z]
                #if nr > max_res_transv/2:
                #    excess_r = int(np.round(nr/max_res_transv/2))
                #    Fcirc = Fcirc[:, ::excess_r, :]
                #    info.r = info.r[::excess_r]
                fld_zoom = np.array([1., 1., 1.])
                if nr > max_res_transv:
                    fld_zoom[1] = max_res_transv/nr
                    info.r = zoom(info.r, fld_zoom[1], order=1)
                if nz > max_res_lon:
                    fld_zoom[2] = max_res_lon/nz
                    info.z = zoom(info.z, fld_zoom[2], order=1)
                if any(fld_zoom != 1):
                    Fcirc = zoom(Fcirc, fld_zoom, order=1)

            # Convert cylindrical data to Cartesian data
            info._convert_cylindrical_to_3Dcartesian()
            nx, ny, nz = len(info.x), len(info.y), len(info.z)
            F_total = np.zeros( (nx, ny, nz) )
            opmd_fr.construct_3d_from_circ(
                F_total, Fcirc, info.x, info.y, modes, nx, ny, nz, nr, nmodes,
                inv_dr, rmax )

        else:

            # Extract the modes and recombine them properly
            F_total = np.zeros( (2 * Nr, Nz ) )
            if m == 'all':
                # Sum of all the modes
                # - Prepare the multiplier arrays
                mult_above_axis = [1]
                mult_below_axis = [1]
                for mode in range(1, int(Nm / 2) + 1):
                    cos = np.cos( mode * theta )
                    sin = np.sin( mode * theta )
                    mult_above_axis += [cos, sin]
                    mult_below_axis += [ (-1) ** mode * cos, (-1) ** mode * sin ]
                mult_above_axis = np.array( mult_above_axis )
                mult_below_axis = np.array( mult_below_axis )
                # - Sum the modes
                F = opmd_fr.get_data( dset )  # (Extracts all modes)
                F_total[Nr:, :] = np.tensordot( mult_above_axis,
                                                F, axes=(0, 0) )[:, :]
                F_total[:Nr, :] = np.tensordot( mult_below_axis,
                                                F, axes=(0, 0) )[::-1, :]
            elif m == 0:
                # Extract mode 0
                F = get_data( dset, 0, 0 )
                F_total[Nr:, :] = F[:, :]
                F_total[:Nr, :] = F[::-1, :]
            else:
                # Extract higher mode
                cos = np.cos( m * theta )
                sin = np.sin( m * theta )
                F_cos = opmd_fr.get_data( dset, 2 * m - 1, 0 )
                F_sin = opmd_fr.get_data( dset, 2 * m, 0 )
                F = cos * F_cos + sin * F_sin
                F_total[Nr:, :] = F[:, :]
                F_total[:Nr, :] = (-1) ** m * F[::-1, :]

        # Perform slicing if needed
        if slice_across is not None:
            # Slice field and clear metadata
            inverted_axes_dict = {info.axes[key]: key for key in info.axes.keys()}
            for count, slice_across_item in enumerate(slice_across):
                slicing_index = inverted_axes_dict[slice_across_item]
                coord_array = getattr( info, slice_across_item )
                # Number of cells along the slicing direction
                n_cells = len(coord_array)
                # Index of the slice (prevent stepping out of the array)
                i_cell = int( 0.5 * (slice_relative_position[count] + 1.) * n_cells )
                i_cell = max( i_cell, 0 )
                i_cell = min( i_cell, n_cells - 1)
                F_total = np.take( F_total, [i_cell], axis=slicing_index )
            F_total = np.squeeze(F_total)
            # Remove the sliced labels from the FieldMetaInformation
            for slice_across_item in slice_across:
                info._remove_axis(slice_across_item)

        # Close the file
        dfile.close()

        return( F_total, info )

    def _read_field_metadata(self, file_path, field_path):
        file = H5F(file_path, 'r')
        field, *comp = field_path.split('/')
        if len(comp) > 0:
            comp = comp[0]
        md = {}
        t, params = read_openPMD_params(file_path)
        md['time'] = {}
        md['time']['value'] = t
        md['time']['units'] = 's'
        field_geometry = params['fields_metadata'][field]['geometry']
        field_units = self._determine_field_units(field)
        md['field'] = {}
        md['field']['units'] = field_units
        md['field']['geometry'] = field_geometry
        ax_el, ax_lims = opmd_fr.get_grid_parameters(file, [field],
                                                     params['fields_metadata'])
        axes = ax_el.keys()
        md['axis'] = {}
        for axis in axes:
            md['axis'][axis] = {}
            md['axis'][axis]['units'] = 'm'
            ax_min = ax_lims[axis][0]
            ax_max = ax_lims[axis][1]
            ax_els = ax_el[axis]+1
            if field_geometry == 'thetaMode' and axis == 'r':
                ax_min = -ax_max
                ax_els += ax_el[axis]
            md['axis'][axis]['array'] = np.linspace(ax_min, ax_max, ax_els)
        return md

    def _determine_field_units(self, field):
        if field == 'E':
            return 'V/m'
        if field == 'B':
            return 'T'
        if field == 'rho':
            return 'C/m^3'
