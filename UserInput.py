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
Keana Kief (OSU)
April 16th, 2024
"""


class UserInput: 
    
    def __init__(self, controller_configuration):
        self.wind_ind = controller_configuration["wind_ind"]
        self.wind_selection = controller_configuration["wind_selection"]
        self.wind_vals = controller_configuration["wind_vals"]
        self.kd_ind = controller_configuration["kd_ind"]
        self.kd_selection = controller_configuration["kd_selection"]
        kd_vals_tuple = controller_configuration["kd_vals"]
        self.kd_vals = range(kd_vals_tuple[0], kd_vals_tuple[-1])
        self.vdatum_region = controller_configuration["vdatum_region"]
        self.mcu = controller_configuration["mcu"]
        self.output_directory = controller_configuration["directories"]["tpu"]
        self.csv_option = controller_configuration["csv_option"]

        #Get the current cblue version and subaqueous version from the cblue_configuration.json
        self.cblue_version = controller_configuration["cBLUE_version"]
        self.subaqueous_version = controller_configuration["subaqueous_version"]

        #Get what multiprocess is set to from the cblue_configuration.json
        #Should be "True" or "False" held in a string
        #TODO: Make multiprocess a GUI selection? Currently the user edits the cblue_configuration.json to change this value.
        self.multiprocess = controller_configuration["multiprocess"]

        #If multiprocess is "True", save cpu information about number of cores to multiprocess with
        if self.multiprocess:
            #Get the number of cores to run multiprocessing on from the cblue_configuration.json
            #TODO: Make number of cores a GUI selection? Currently the user edits the cblue_configuration.json to change this value.
            num_cores = controller_configuration["number_cores"]
            self.cpu_process_info = ("multiprocess", num_cores)
        #otherwise if multiprocess is "False", save cpu information as singleprocess
        else:
            self.cpu_process_info = ("singleprocess",)

        #Get the float value for water surface ellipsoid height. In meters, positive up. 
        self.water_surface_ellipsoid_height = controller_configuration["water_surface_ellipsoid_height"]

        #A string holding the error type requested by the user. Either "1-\u03c3" or "95% confidence".
        self.error_type = controller_configuration["error_type"]
