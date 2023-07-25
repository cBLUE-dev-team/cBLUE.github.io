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

Last Edited By:
Keana Kief (OSU)
July 25th, 2023


"""
import os
import pandas as pd
import logging
import numpy as np
import numexpr as ne
import laspy

logger = logging.getLogger(__name__)

"""
This class provides the functionality to load las files into cBLUE.  One Las object
is created for each loaded las file.
"""


class Las:
    def __init__(self, las):
        self.las = las
        self.las_short_name = os.path.split(las)[-1]
        self.las_base_name = self.las_short_name.replace(".las", "")
        self.inFile = laspy.read(self.las)
        self.points_to_process = self.inFile.points
        self.unq_flight_lines = self.get_flight_line_ids()
        self.num_file_points = self.points_to_process.array.shape[0]

        """index list that would sort gps_time (to be used to
        later when exporting las data and calculated tpu to a las
        file
        """
        self.t_argsort = None

    def get_bathy_points(self):
        class_codes = {"BATHYMETRY": 26}
        bathy_inds = self.inFile.raw_classification == class_codes["BATHYMETRY"]
        return self.inFile.points.array[bathy_inds]["point"]

    def get_flight_line_ids(self):
        """generates a list of unique flight line ids

        This method returns a list of unique flight line ids.

        :return: ndarray
        """

        # pandas' unique faster than numpy's ?
        return pd.unique(self.points_to_process["pt_src_id"])

    def get_flight_line(self, sensor_type):
        """retrieves the x, y, z, and timestamp data from the las data points

        The x, y, and z values in the las file are stored as integers.  The
        scale and offset values in the las file header are used to convert
        the integer values to decimal values with centimeter precision.

        :param ? fl:
        :return: np.array, np.array, np.array, np.array
        """

        #xyz_to_coordinate converts the x, y, z integer values to coordinate values
        x, y, z = self.xyz_to_coordinate()

        t = self.points_to_process["gps_time"]

        if "classification" in self.points_to_process.array.dtype.names:
            c = self.points_to_process["classification"]
        elif "classification_flags" in self.points_to_process.array.dtype.names:
            c = self.points_to_process["classification_flags"]
        else:
            raise Exception("Unknown las version or missing classification attribute.")

        self.t_argsort = t.argsort()

        # Check if this is a multi beam sensor
        if(sensor_type == "multi"):
            #Get the fan angle and multiply it by 0.006 to convert to degrees
            fan_angle = self.inFile.scan_angle*0.006
            #Add xyztcf to an array together
            xyztcf = np.vstack([x, y, z, t, c, fan_angle]).T
            # logger.las(f"{sensor_type} Fan Angle: {fan_angle}")
        else:
            #Fan angle is not used by the other sensors
            #Add xyztc to an array together
            xyztcf = np.vstack([x, y, z, t, c]).T

        flight_lines = self.points_to_process["pt_src_id"]

        return xyztcf, self.t_argsort, flight_lines

    
    def xyz_to_coordinate(self):
        """The x, y, and z values in the las file are stored as integers.  The
        scale and offset values in the las file header are used to convert
        the integer values to decimal values with centimeter precision."""

        scale_x = np.asarray(self.inFile.header.scales[0])
        scale_y = np.asarray(self.inFile.header.scales[1])
        scale_z = np.asarray(self.inFile.header.scales[2])

        offset_x = np.asarray(self.inFile.header.offsets[0])
        offset_y = np.asarray(self.inFile.header.offsets[1])
        offset_z = np.asarray(self.inFile.header.offsets[2])

        X = self.points_to_process["X"]
        Y = self.points_to_process["Y"]
        Z = self.points_to_process["Z"]


        x = ne.evaluate("X * scale_x + offset_x")
        y = ne.evaluate("Y * scale_y + offset_y")
        z = ne.evaluate("Z * scale_z + offset_z")

        return x, y, z
