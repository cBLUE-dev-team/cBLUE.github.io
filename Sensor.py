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
April 11th, 2023
"""

import logging

logger = logging.getLogger(__name__)

#Current Sensors
"""
"Riegl VQ-880-G (0.7 mrad)": "RIEGL 0.7 mrad",
"Riegl VQ-880-G (1.0 mrad)": "RIEGL 1.0 mrad",
"Riegl VQ-880-G (1.5 mrad)": "RIEGL 1.5 mrad",
"Riegl VQ-880-G (2.0 mrad)": "RIEGL 2.0 mrad",
"Leica Chiroptera 4X (HawkEye 4X Shallow)": "CHIRO",
"HawkEye 4X 400m AGL": "HAWK400",
"HawkEye 4X 500m AGL": "HAWK500",
"HawkEye 4X 600m AGL": "HAWK600",
"""

#TODO: Add PILLS TPU Model
#TODO: Add sensor scan angle and range uncertainties

class Sensor: 

    def __init__(self, sensor_name):
        """ Initalizes the sensor object based on the sensor name selected in CBlueApp.py.

        :param sensor_name: The name of the sensor model selected by the user in the GUI in CBlueApp.py

        :return: None
        :rtype: None
        """

        #Assign the sensor name given to the sensor object
        self.name = sensor_name
        
        #Use the sensor name to initalize sensor values:

        #If the sensor is Riegl VQ-880-G (0.7 mrad)
        if (sensor_name=="Riegl VQ-880-G (0.7 mrad)"):
            self.riegl_07_mrad()
            logger.sensor(f"Initalized for Riegl VQ-880-G (0.7 mrad)")

        #If the sensor is Riegl VQ-880-G (1.0 mrad)
        elif (sensor_name=="Riegl VQ-880-G (1.0 mrad)"):
            self.riegl_10_mrad()
            logger.sensor(f"Initalized for Riegl VQ-880-G (1.0 mrad)")

        #If the sensor is Riegl VQ-880-G (1.5 mrad)
        elif (sensor_name=="Riegl VQ-880-G (1.5 mrad)"):
            self.riegl_15_mrad()
            logger.sensor(f"Initalized for Riegl VQ-880-G (1.5 mrad)")

        #If the sensor is Riegl VQ-880-G (2.0 mrad)
        elif (sensor_name=="Riegl VQ-880-G (2.0 mrad)"):
            self.riegl_20_mrad()
            logger.sensor(f"Initalized for Riegl VQ-880-G (2.0 mrad)")

        #If the sensor is Leica Chiroptera 4X (HawkEye 4X Shallow)
        elif (sensor_name=="Leica Chiroptera 4X (HawkEye 4X Shallow)"):
            self.leica_chiroptera()
            logger.sensor(f"Initalized for Leica Chiroptera 4X (HawkEye 4X Shallow)")

        #If the sensor is HawkEye 4X 400m AGL
        elif (sensor_name=="HawkEye 4X 400m AGL"):
            self.hawkeye_400m()
            logger.sensor(f"Initalized for HawkEye 4X 400m AGL")

        #If the sensor is HawkEye 4X 500m AGL
        elif (sensor_name=="HawkEye 4X 500m AGL"):
            self.hawkeye_500m()
            logger.sensor(f"Initalized for HawkEye 4X 500m AGL")

        #If the sensor is HawkEye 4X 600m AGL
        elif (sensor_name=="HawkEye 4X 600m AGL"):
            self.hawkeye_600m()
            logger.sensor(f"Initalized for HawkEye 4X 600m AGL")

    
    def riegl_07_mrad(self):
        """ Initalizes the sensor object for Riegl VQ-880-G (0.7 mrad).
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_0.7_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_0.7_mrad_hz.csv"


    def riegl_10_mrad(self):
        """ Initalizes the sensor object for Riegl VQ-880-G (1.0 mrad).
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_1_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_1_mrad_hz.csv"


    def riegl_15_mrad(self):
        """ Initalizes the sensor object for Riegl VQ-880-G (1.5 mrad).
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_1.5_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_1.5_mrad_hz.csv"


    def riegl_20_mrad(self):
        """ Initalizes the sensor object for Riegl VQ-880-G (2.0 mrad).
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_2_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/RieglVQ880_LUTs/ReiglVQ880G_600_AGL_2_mrad_hz.csv"


    def leica_chiroptera(self):
        """ Initalizes the sensor object for Leica Chiroptera 4X (HawkEye 4X Shallow). 
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/Chiroptera_4X_400_AGL_4pt75_mrad_LUT_linear.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/Chiroptera_4X_400_AGL_4pt75_mrad_hz.csv"


    def hawkeye_400m(self):
        """ Initalizes the sensor object for HawkEye 4X 400m AGL. 
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_400_AGL_8_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_400_AGL_8_mrad_hz.csv"


    def hawkeye_500m(self):
        """ Initalizes the sensor object for HawkEye 4X 500m AGL. 
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_500_AGL_8_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_500_AGL_8_mrad_hz.csv"

    def hawkeye_600m(self):
        """ Initalizes the sensor object for HawkEye 4X 600m AGL. 
        Sets the paths for the vertical (vert_lut) and horizontal (horz_lut) look up tables.

        :return: None
        :rtype: None
        """
        #The vertical Look Up Table used for modeling
        self.vert_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_600_AGL_8_mrad.csv"
        #The horizontal Look Up Table used for modeling
        self.horz_lut = "./lookup_tables/Hawkeye_LUTs/HawkEye4X_Deep_600_AGL_8_mrad_hz.csv"
