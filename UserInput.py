"""
cBLUE (comprehensive Bathymetric Lidar Uncertainty Estimator)
Copyright (C) 2019
Oregon State University (OSU)
Center for Coastal and Ocean Mapping/Joint Hydrographic Center, University of New Hampshire (CCOM/JHC, UNH)
NOAA Remote Sensing Division (NOAA RSD)

This library is free software; you can redistribute it and/or
modify it under the terms of the GNU Lesser General Public
License as published by the Free Software Foundation; either
version 2.1 of the License, or (at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public
License along with this library; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

Contact:
Christopher Parrish, PhD
School of Construction and Civil Engineering
101 Kearney Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

Last Edited:
Keana Kief
April 25th, 2023
"""

class UserInput: 
    
    def __init__(self, controller_panel):

        #Get the index of the wind selection from the controller panel
        self.wind_ind = controller_panel.windRadio.selection.get()
        #Use the wind index to get the string name describing the wind selection
        self.wind_selection = controller_panel.wind_vals[wind_ind][0]
        #Use the wind index get the array holding integer values representing the wind selection
        self.wind_vals = controller_panel.wind_vals[wind_ind][1]

        #Get the index of the turbidity selection from the controller panel
        self.kd_ind = controller_panel.turbidityRadio.selection.get()
        #Use the kd index to get the string name describing the turbidity selection
        self.kd_selection = controller_panel.kd_vals[kd_ind][0]
        #Use the kd index get the array holding integer values representing the turbidity selection
        self.kd_vals = controller_panel.kd_vals[kd_ind][1]
        
        #Get the string name of the vdatum region
        self.vdatum_region = controller_panel.vdatum_region.get()
        #Get the float value for the maximum cumulative error related to the vdatum region
        self.mcu = controller_panel.mcu

        #Get the file path of the TPU output directory
        self.output_directory = controller_panel.tpuOutput.directoryName

        #Get the current cblue version from the cblue_configuration.json
        self.cblue_version = controller_panel.controller.controller_configuration["cBLUE_version"]

        #Get what multiprocess is set to from the cblue_configuration.json
        #Should be "True" or "False" held in a string
        #TODO: Make multiprocess a GUI selection? Currently the user edits the cblue_configuration.json to change this value.
        self.multiprocess = controller_panel.controller.controller_configuration["multiprocess"]

        #If multiprocess is "True", save cpu information about number of cores to multiprocess with
        if self.multiprocess:
            #Get the number of cores to run multiprocessing on from the cblue_configuration.json
            #TODO: Make number of cores a GUI selection? Currently the user edits the cblue_configuration.json to change this value.
            num_cores = controller_panel.controller.controller_configuration["number_cores"]
            self.cpu_process_info = ("multiprocess", num_cores)
        #otherwise if multiprocess is "False", save cpu information as singleprocess
        else:
            self.cpu_process_info = ("singleprocess",)

        #Get the float value for water surface ellipsoid height. In meters, positive up. 
        self.water_surface_ellipsoid_height = controller_panel.controller.controller_configuration["water_surface_ellipsoid_height"]

        #A string holding the error type requested by the user. Either "1-\u03c3" or "95% confidence".
        self.error_type = controller_panel.controller.controller_configuration["error_type"]

        #Get if the user wants a csv output file. True or False boolean value.
        self.csv_option = controller_panel.csv_option.get()
