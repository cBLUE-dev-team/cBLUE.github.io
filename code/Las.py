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

"""
import os
import logging
from time import time
import numpy as np
import laspy

logger = logging.getLogger(__name__)


class Las:
    """
    This class provides the functionality to load las files into cBLUE.  One Las object
    is created for each loaded las file.
    """

    def __init__(self, las):

        # Get file name parts from las file
        self.las_short_name = os.path.split(las)[-1]
        self.las_base_name = self.las_short_name.replace(".las", "")

        # Read LAS file
        self.inFile = laspy.read(las)
        # Get point information
        self.points_to_process = self.inFile.points
        # Identify unique flight lines
        self.unq_flight_lines = np.unique(self.points_to_process["pt_src_id"])
        # Compute number of points
        self.num_file_points = self.points_to_process.array.shape[0]

    def get_flight_line_txyz(self):
        """retrieves the x, y, z, and timestamp data from the las data points

        The x, y, and z values in the las file are stored as integers.  The
        scale and offset values in the las file header are used to convert
        the integer values to decimal values with centimeter precision.

        :param ? fl:
        :return: np.array, np.array, np.array, np.array
        """

        # Get scale and offset of xyz points
        (scale_x, scale_y, scale_z) = self.inFile.header.scales
        (offset_x, offset_y, offset_z) = self.inFile.header.offsets

        t = self.points_to_process["gps_time"]

        # Apply scaling and offset
        x = scale_x * self.points_to_process["X"] + offset_x
        y = scale_y * self.points_to_process["Y"] + offset_y
        z = scale_z * self.points_to_process["Z"] + offset_z

        logger.las(f" X min: {x.min()},\t X max: {x.max()}")
        logger.las(f" Y min: {y.min()},\t Y max: {y.max()}")
        logger.las(f" Z min: {z.min()},\t Z max: {z.max()}")

        # Get point classification
        if "classification" in self.points_to_process.array.dtype.names:
            c = self.points_to_process["classification"]
        elif "classification_flags" in self.points_to_process.array.dtype.names:
            c = self.points_to_process["classification_flags"]
        else:
            raise Exception("Unknown las version or missing classification attribute.")

        xyztc = np.vstack([x, y, z, t, c]).T

        flight_lines = self.points_to_process["pt_src_id"]

        self.t_argsort = t.argsort()

        return xyztc, self.t_argsort, flight_lines


if __name__ == "__main__":
    pass
