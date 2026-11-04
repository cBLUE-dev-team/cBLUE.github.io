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
204 Owen Hall
Oregon State University
Corvallis, OR  97331
(541) 737-5688
christopher.parrish@oregonstate.edu

Last Edited By:
Keana Kief (OSU)
August 4th, 2025
"""

import logging
import os
import json

logger = logging.getLogger(__name__)

class Sensor: 

    NO_DATA_VALUE = -9999.0

    def __init__(self, sensor_name):
        #Initalizes the sensor object based on the sensor name selected in CBlueApp.py.

        #:param sensor_name: The name of the sensor model selected by the user in the GUI in CBlueApp.py

        #:return: None
        #:rtype: None
       
        #Assign the sensor name given to the sensor object
        self.name = sensor_name

        #JSON file containing lidar sensor configurations for cBLUE
        self.sensor_file = "lidar_sensors.json"

        #Check if the lidar sensor config file exists
        if os.path.isfile(self.sensor_file):
            with open(self.sensor_file) as sf:
                #If the file exists load the information into self.sensor_config
                self.sensor_config = json.load(sf)
        else:
            logger.sensor("Sensor file doesn't exist")

        #The type of sensor: "single", "single_hawkeye", or "multi" beam
        self.type = self.sensor_config[self.name]["sensor_model"]["type"]

        #Scan angle and range uncertainties
        self.a_std_dev = self.sensor_config[self.name]["sensor_model"]["a_std_dev"]
        self.b_std_dev = self.sensor_config[self.name]["sensor_model"]["b_std_dev"]
        self.std_rho = self.sensor_config[self.name]["sensor_model"]["std_rho"]
        self.flying_height = None

    def set_luts(self, flying_height):

        #If this is a Leica HawkEye sensor, get the path of the deep narrow, deep wide, and shallow subaqueous lookup tables
        if self.type == "single_hawkeye":
            if flying_height == self.NO_DATA_VALUE:
                #There was no valid ground or water-surface point found in the LAS data, so the flying height cannot be calculated.
                print("\nNo valid ground or water-surface point found in the LAS data. "
                            "Flying height cannot be calculated, and this LAS file will not be processed.")
                raise ValueError(
                "No valid ground or water-surface point found in the LAS data. "
                "Flying height cannot be calculated."
            )
            elif flying_height <= 450:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["400m"]
            elif flying_height <= 550:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["500m"]
            else:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["600m"]
            #The path of the vertical deep narrow look up table used for modeling
            self.vert_lut_deep_narrow = self.subaqueous_LUTs["vertical_deep_narrow"]
            #The path of the horizontal deep narrow look up table used for modeling
            self.horz_lut_deep_narrow = self.subaqueous_LUTs["horizontal_deep_narrow"]
            # The path of the range bias deep narrow uncertainty look up table used for modeling
            self.range_bias_lut_narrow = self.subaqueous_LUTs["range_bias_deep_narrow"]
            #The path of the vertical deep wide look up table used for modeling
            self.vert_lut_deep_wide = self.subaqueous_LUTs["vertical_deep_wide"]
            #The path of the horizontal deep wide look up table used for modeling
            self.horz_lut_deep_wide = self.subaqueous_LUTs["horizontal_deep_wide"]
            # The path of the range bias deep wide uncertainty look up table used for modeling
            self.range_bias_lut_wide = self.subaqueous_LUTs["range_bias_deep_wide"]
            #The path of the vertical wide look up table used for modeling
            self.vert_lut_shallow = self.subaqueous_LUTs["vertical_shallow"]
            #The path of the horizontal wide look up table used for modeling
            self.horz_lut_shallow = self.subaqueous_LUTs["horizontal_shallow"]
            # The path of the range bias shallow uncertainty look up table used for modeling
            self.range_bias_lut_shallow = self.subaqueous_LUTs["range_bias_shallow"]

        # If this is the CoastalMapper    
        elif self.type == "single_cm":
            if flying_height == self.NO_DATA_VALUE:
                #There was no valid ground or water-surface point found in the LAS data, so the flying height cannot be calculated.
                print("\nNo valid ground or water-surface point found in the LAS data. "
                            "Flying height cannot be calculated, and this LAS file will not be processed.")
                raise ValueError(
                "No valid ground or water-surface point found in the LAS data. "
                "Flying height cannot be calculated."
            )
            elif flying_height <= 637.5:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["400m"]
            else:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["875m"]
            #The path of the vertical deep look up table used for modeling
            self.vert_lut_deep = self.subaqueous_LUTs["vertical_deep"]
            #The path of the horizontal deep look up table used for modeling
            self.horz_lut_deep = self.subaqueous_LUTs["horizontal_deep"]
            # The path of the range bias deep uncertainty look up table used for modeling
            self.range_bias_lut_deep = self.subaqueous_LUTs["range_bias_deep"]
            #The path of the vertical wide look up table used for modeling
            self.vert_lut_shallow = self.subaqueous_LUTs["vertical_shallow"]
            #The path of the horizontal wide look up table used for modeling
            self.horz_lut_shallow = self.subaqueous_LUTs["horizontal_shallow"]
            # The path of the range bias shallow uncertainty look up table used for modeling
            self.range_bias_lut_shallow = self.subaqueous_LUTs["range_bias_shallow"]
        
        #Otherwise if this is the Chiroptera-5 sensor
        elif self.type == "chiroptera_5":
            if flying_height == self.NO_DATA_VALUE:
                #There was no valid ground or water-surface point found in the LAS data, so the flying height cannot be calculated.
                print("\nNo valid ground or water-surface point found in the LAS data. "
                            "Flying height cannot be calculated, and this LAS file will not be processed.")
                raise ValueError(
                "No valid ground or water-surface point found in the LAS data. "
                "Flying height cannot be calculated."
            )
            elif flying_height <= 450:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["400m"]
            elif flying_height <= 550:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["500m"]
            else:
                self.subaqueous_LUTs = self.sensor_config[self.name]["subaqueous_LUTs"]["600m"]

            #The path of the vertical look up table used for modeling
            self.vert_lut = self.subaqueous_LUTs["vertical"]
            #The path of the horizontal look up table used for modeling
            self.horz_lut = self.subaqueous_LUTs["horizontal"]
            # The path of the range bias uncertainty look up table used for modeling
            self.range_bias_lut = self.subaqueous_LUTs["range_bias"]

        #Any other sensor
        else:
            #The path of the vertical look up table used for modeling
            self.vert_lut = self.sensor_config[self.name]["subaqueous_LUTs"]["vertical"]
            #The path of the horizontal look up table used for modeling
            self.horz_lut = self.sensor_config[self.name]["subaqueous_LUTs"]["horizontal"]
            # The path of the range bias uncertainty look up table used for modeling
            self.range_bias_lut = self.sensor_config[self.name]["subaqueous_LUTs"]["range_bias"]